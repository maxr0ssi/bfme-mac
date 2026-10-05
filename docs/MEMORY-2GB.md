# Texture memory in the 32-bit address space

BFME2 runs with LARGEADDRESSAWARE off (2 GB of address space), RotWK with it on (4 GB;
[MEMORY-4GB.md](MEMORY-4GB.md)). That space holds the game, its DLLs, Wine's PE side (d3d9,
wined3d, opengl32 thunks) and every heap. The art packs add higher-resolution textures (sagekit
budget 512 MB per faction, `budget_mb` in `sagekit/style.py`). This page is what a texture byte
costs in that space under the w10 engine (wined3d with `patches/wined3d-wow64-buffers/`
0001–0021), and how to make it cost almost nothing. The per-byte costs apply to both games; only
the ceiling differs. The measurements below were taken in the 2 GB case.

1.03 bytes per texture byte today, kept for as long as the texture is loaded. With 0022 (below):
0.002 bytes per byte for textures of 0.5 MB and up, about 2.7 KB per texture for the objects. The
GPU copy never costs 32-bit space: the macOS GL driver keeps it above 4 GB.

## Where the memory goes (static analysis)

| What | Where it lives | 32-bit bytes per byte |
|---|---|---|
| Game textures: all `D3DPOOL_MANAGED`, full mip chain, each level `LockRect(NULL, NOSYSLOCK)`-filled once (d3d trace `logs/bfme2-20260922-121845.log`; WW3D2 `TextureLoadTaskClass`, the DDS file buffer is freed after the copy) | — | — |
| d3d9 managed texture = **two** wined3d textures (`dlls/d3d9/texture.c`, `d3d9_texture_init`): a CPU-only one the game locks, a GPU-only one draws use | | |
| CPU-only half: `calloc` of every level in the PE heap (`wined3d_resource_allocate_sysmem`). It has no other location, so `wined3d_texture_evict_sysmem()` never runs for it: kept until Release | 32-bit PE heap | 1.0 + 64 KB rounding (large blocks) |
| GPU-only half: uploaded from the CPU half on the CS thread (`wined3d_device_update_texture` → `texture2d_blt` → `glCompressedTexSubImage2D` with the 32-bit pointer, no PBO); DXT stays compressed, mips as in the file | host GL driver, above 4 GB | 0 |
| `EvictManagedResources()` (the game calls it): drops the GPU half and marks the CPU half dirty; no download | — | 0 |
| Upload copies of fix 0014 (regions ≤256 KB copied into a heap buffer at draw time, freed when the CS runs them) | 32-bit PE heap, transient | up to +0.6 during a burst of first draws, retained by the heap afterwards |
| Managed VB/IB (pinned in sysmem upstream) / static DEFAULT VB / dynamic VB (pinned by fix 0001) | 32-bit PE heap | 1.06 / 0 after upload / 1.0 |
| GL buffer maps under WoW64 (opengl32 copies the mapping below 4 GB) | 32-bit, transient per map | 0 at rest |

Formats: DXT1/DXT5 cost their file size (minus the 128-byte header). A 24-bit TGA (the art mod's
normal maps) becomes X8R8G8B8 (wined3d offers no R8G8B8 textures; the game creates none) with the
full mip chain that WW3D2's TGA loader builds: 5.33 bytes per pixel in memory against 3 in the
file, **1.78× what `sagekit/formats/textures.py` `tga24_size()` counts**. A 2048² normal map is
21.3 MB in memory, not 12.

## Measurements (2026-09-27, `tools/texmem32.c`, throwaway prefix, no game)

Build: installed `engines/w10` wined3d (bfme-fixes-10.0 + 0001–0021) and the same plus 0022 in a
scratch copy of the engine. Delta of the 2 GB range against the process after device creation
(VirtualQuery walk; "addr" = committed + reserved).

| Case | installed | + 0022 |
|---|---|---|
| 256 MB managed 1024² DXT5 (192 textures), filled | 1.031 | 0.005 |
| … drawn (uploaded) | 1.031 | 0.000 |
| … after `EvictManagedResources` + draw | 1.031 | 0.000 |
| … after the game relocks them (`--relock`, bytes checked: 0 differ) | 1.031 | 1.031 (pinned, see risks) |
| 128 MB managed 512² A8R8G8B8 | 1.031 | 0.000 |
| 256 MB managed 256² DXT1 (6142 textures), drawn | 1.66–1.72 (0014 burst) | 0.124 (2.7 KB/texture objects) |
| same with `WINED3D_CLIENT_MAPS=0` / stock wined3d | 1.105 / 1.103 | — |
| 256 MB DEFAULT-pool DXT5 via UpdateTexture (the floor) | 0.000 | — |
| 128 MB managed / DEFAULT / dynamic VB | 1.062 / 0 / 1.062 (stock 0) | 1.062 / — / — |
| Load 1024² DXT5 until CreateTexture fails (`--batches 12`) | fails after **1.87 GB** (1437 textures; largest free block 0.2 MB) | 3 GB loaded, 14 MB used |
| Time, 512 MB 1024² DXT5: fill / first draw / draw after evict | 0.90 / 0.18 / 0.18–0.25 s | 0.47 / 0.31 / 0.33–0.38 s |

Rendered checksums (`CRC` lines, 15 textures point-sampled) are identical between the builds and
before/after eviction and relock. `tools/d3d9lockcheck.c`: 0 failures on both.

## Patch 0022 — managed textures' system memory in host memory

`patches/wined3d-wow64-buffers/unbuilt/0022-wined3d-Keep-managed-textures-system-memory-in-host-memory-under-WoW64.patch`
(against bfme-fixes-10.0; applies with `git apply --check`). Written, not built into the
engine and not played; `scripts/wine-fixes.sh` does not apply `unbuilt/`.

- When the game has filled a managed texture (unmap of its last mip) and after every upload, the
  CS thread copies the CPU half's memory into a `malloc` in `wined3d.so` (64-bit, above 4 GB; the
  call fails rather than land below 4 GB), frees the 32-bit copy and marks the sub-resources
  DISCARDED with a stash handle.
- Anything that needs the system memory again copies it back first: `wined3d_texture_load_location`
  / `prepare_location` (the first-draw upload, uploads after `EvictManagedResources`, maps,
  `GetDC`, volume uploads through a PBO). `texture2d_blt` treats a stashed source as on the CPU;
  the dirty-region op skips stashed textures so an eviction does not restore everything at once.
- A texture locked again after a stash stays in 32-bit memory for good (radar, dynamic UI).
- Switch: `WINED3D_STASH_MANAGED=0`; off automatically without `wined3d.so` or outside WoW64.

Checks: Wine's d3d9 tests, installed vs patched: `visual` 86 = 86 failures, identical lines; `device`
34 vs 32 failures (two flaky ones gone; the patched run skipped the large-query test on time),
`stateblock` 0 vs 0, `d3d9ex` 24 vs 24.

Risks: (1) one extra 32→64→32-bit copy of each texture at its first draw and after each
`EvictManagedResources`: +0.25 ms per MB, so ~0.1–0.2 s once at the first frame of a match with
500 MB of new textures; (2) the stash uses host RAM equal to the textures (64 GB machine);
(3) a texture that is only ever DISCARDED-and-stashed relies on every system-memory reader going
through load/prepare — the covered paths are listed above, a missed one would read zeros (the d3d9
suite and the checksums found none after the PBO fix); (4) textures the game relocks keep costing
1.03. Correctness of Lock readback does not depend on GL: the bytes come back from the copy.
Device Reset does not unload managed resources in wined3d, so it is not a trigger.

Side finding, independent of 0022: fix 0014 copies every mip ≤256 KB of a texture drawn for the
first time into a heap buffer; with many new small textures in one frame the heap grows by up to
0.6× their size and keeps that address space (stock: none). 0022 avoids it for stashed textures.
Capping 0014 by bytes in flight would fix it for the rest.

## What it means for the art budget

- **Today:** every MB of loaded texture takes 1.03 MB of the address space, from load until
  release, and nothing else in the address space shrinks to make room. What the game already uses
  in a battle has not been measured (no VirtualQuery walk of the game yet); in a 2 GB process the
  empty-process wall is 1.87 GB of textures. Count normal-map TGAs at 5.33 B/px: STANDARD tier = 2.7 + 5.3 = 8.0 MB,
  HERO = 10.7 + 21.3 = 32 MB per building, against 5.7 / 22.7 in `sagekit budget`.
- **With 0022:** textures stop costing 32-bit space once filled (2.7 KB per texture object). The
  budget would then follow host RAM and load time, but only once 0022 has been played with (load a
  map, a long battle with an eviction, alt-tab; compare memory with `scripts/memwatch.sh`).
  Until then the budget stays at 512 MB per faction.

## Texture memory of our archives (2026-10-04)

Counted from the installed archives (`python3 -m sagekit.texslim`; a texture's texel data with its
full mip chain, APT textures one level; ×1.03 for the 32-bit address space, as above). The faction
packs: Men 625 MB, Angmar 507, Isengard 453, Elves 448, Dwarves 385, Mordor 374, Goblins 262;
neutral 101, scenery 58, UI 158 (ui2x 71, icons 44, HUD 43), each builder or worker 12-15. Every
structure of a faction loads 6-11× EA's texture memory for the same objects (Men 599 against 73 MB,
Isengard 449 against 44) and 2-5× EA's model bytes. Uncompressed normal maps (X8R8G8B8, 4 bytes a
pixel) are 1.36 GB of the 3.2 GB; DXT5 sheets 1.1 GB; snow variants 0.38 GB (snowy maps only).

**An 8-player match with all 7 factions.** If every structure, damage state and unit of the 7
factions appears: our art 3.2 GB of textures and 0.92 GB of W3D against EA's 0.45 and 0.29 GB.
Calibration (`logs/memwatch-20260928-153726.csv`, a 5.5 min skirmish, no `highmem`): 0.88 GB
committed at the first in-match sample, 1.17 GB at the end, 0.35-0.39 GB reserved (Wine and the
game's reservations), 2.6 GB free of 4 GB. Without snow that full build needs ~1.3 + 2.9 + ~0.9 ≈
5 GB: over the 4 GB wall, where EA's is ~1.9 GB. A match loads only what appears, so a shorter game
stays under it; the real figure for an 8-player game needs `scripts/memwatch.sh` in that game.

**Eviction.** None before the wall: the game never evicts (PERFORMANCE.md §13), and wined3d's
video-memory accounting (`VideoMemorySize` 4096) is above what the 32-bit side can hold, so
`D3DERR_OUTOFVIDEOMEMORY` (WW3D's free-and-retry path) is not reached first; the system-memory half
fails to allocate instead (a crash or a missing texture, not a hitch). At UltraHigh
`TextureReductionFactor` is 0 and nothing else sizes textures. Memory costs frame time only through
first-use loads, which scale with bytes (PERFORMANCE.md §13).

**DXT1 for opaque DXT5 (applied).** A DXT5 sheet whose alpha is 255 at every texel of every level
ships as DXT1 at half the memory: same colour blocks, endpoints swapped (indices XOR 1) where
colour0 < colour1, index 0 where they are equal. `tools/dxtslim.c` keeps a rewrite only when the
game's d3dx9 call loads both and every level draws byte-identically on this Mac (point-sampled into a
render target; at start-up a one-colour-per-level texture checks the level choice; without the swap,
or with one block changed in level 1 or 6, the check fails). One Isengard snow sheet's 2x2 level
drew differently and stays DXT5. `sagekit install <faction>` applies it (`sagekit/texslim.py`).
Isengard pilot: 65 sheets, 453.5 → 360.1 MB in memory, archive 586 → 488 MB, every other member
byte-identical. All packs: about 290 MB (Isengard 94, Mordor 79, Angmar 50, Elves 48, Men 11).

`sagekit validate` fails a staged archive over its cap (`CAP_MB` in `sagekit/texslim.py`: 640 MB
for faction packs, 96 for the rest; lower it as packs slim).

**Rollout (2026-10-04, staged, not installed).** Every faction pack, neutral, the 14 builders and
workers and the heroes restaged with the DXT1 rewrite: 3554 → 3287 MB in all (Isengard −93, Mordor
−78, Angmar −47, Elves −31, Men −8, Dwarves −5, Goblins −3, heroes −0.7); 25 sheets kept DXT5 because
a small level (2x2) drew differently. A full 8-player build is now ~2.9 GB of texture against EA's
0.45, about 4.8 GB of address space: still over the wall.

**Mip levels the camera never samples: none.** `sagekit/texreach.py` bounds the lowest mip level each
texture can reach at the closest camera (eye 120 units up, 50° horizontal field of view from game.dat,
3024 pixels, trilinear, facing the triangle, flat ground). Every one of the 724 model textures in the
staged packs reaches its top level (highest bound LOD 0.66, Men's market; median about −5): towers
come within a few units of the closest camera, and nearly every sheet has magnified UV islands. With
the camera 4x farther and a 60° view, 4 MB could go. So dropping top levels is not exact at Max's
resolution. `sagekit validate` fails a texture whose top level is never reached (cached in
build/texreach/).

**Normal maps have a visible effect.** Lit with a sun 50° up on a mid-grey face, 69-91 % of every
normal map's texels (median 88 %, 193 maps) move more than one 8-bit step against a flat normal;
the median texel is tilted 10°. None can go without a visible change
(`build/assets/_review_finish/memory/normal-maps-effect.jpg`).

**What would get under 3 GB without a visible change:** patch 0022 (above) moves each texture's
system-memory copy out of the 32-bit space, leaving ~1.3 GB of game + ~0.9 GB of models + 2.7 KB per
texture ≈ 2.3 GB for the same full build. It is written, not built or played. Exact but small:
sharing byte-identical textures under one name (103 MB, 90 % Angmar's damage-state normals; needs W3D
and asset.dat renames). Everything else (normal maps as DXT, −1 GB; smaller sheets) changes the
picture and is Max's call.
