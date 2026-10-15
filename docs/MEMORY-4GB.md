# 4 GB address space (LARGEADDRESSAWARE)

RotWK runs with the LARGEADDRESSAWARE flag on, as it ships, since 2026-09-27: the 32-bit game gets
4 GB of address space instead of 2 GB. BFME2 1.06 ships with the flag off and stays off.
`scripts/install.sh` sets the flag the way each game ships it. `tools/pe_laa.py --on|--off <file>`
changes it on `lotrbfme2ep1.exe` and `game.dat` (the previous files are kept as `*.preLAAon.bak`).

The old rule "LAA crashes under Wine" came from Wine 11.0: every recorded LAA crash was the Wine 11
WoW64 bug ([patches/WINE-BUG-REPORT.md](../patches/WINE-BUG-REPORT.md)). No run with the flag on
existed on the w10 engine before 2026-09-27. The crash table and the full probe output are in
[history/LAA-W10-2026-09-27.md](history/LAA-W10-2026-09-27.md); outside sources in
[history/RESEARCH-4GB-2026-09-27.md](history/RESEARCH-4GB-2026-09-27.md).

## Evidence

- **Wine 10.0 source.** `virtual_set_large_address_space()` sets the WoW64 user limit to 4 GB − 1
  for a flagged exe; `wow64` and `win32u` derive `zero_bits` from `HighestUserAddress`; the 32→64
  thunks (opengl32, winemac) and our `wined3d.so` zero-extend pointers. No sign extension or 2 GB
  assumption was found on the paths the game uses.
- **Probe, no game** (`tools/laaprobe.c` via `scripts/laa-probe.sh`, 2026-09-27). 4044 MB reserved,
  2032 MB of it above 2 GB, all written and read. With the low 2 GB and the heap's low free space
  used up: SEH, RtlUnwind, vectored handlers and 20,000 window callbacks on a stack above 2 GB;
  d3d9 managed, system-memory and dynamic textures and vertex buffers locked above 2 GB, drawn and
  checked pixel by pixel; the game's 13 DLLs load; D3DX decodes into a managed texture; a dsound
  buffer locks above 2 GB. `--fill-low --mb 1500 d3d9`: 1500 MB of managed textures above 2 GB,
  all drawn correctly. 0 failures.
- **The game patch.** `gamepatch/src` and the worker pool were audited for address assumptions:
  signed jumps and 0x80000000 compares test float bits, pointers only convert to
  `uint32_t`/`uintptr_t`, hashes and pointer differences are unsigned.
- **The game.** RotWK 2.02 runs with the flag on Windows, so its own code is exercised above 2 GB
  there.
- **In game, 2026-09-28** (one ~7 min session with `highmem=1`): 1705 MB below 2 GB reserved at
  start-up, the process heap then allocating at `0x80000020`. The session ended with a dump at exit:
  `lotrbfme2ep1.exe+0x76D9E2`, a write to address 0, the same site as a 2026-09-24 dump taken
  without the flag ([PERFORMANCE.md](PERFORMANCE.md) §9). Not analysed further.

## Testing it in game

Memory above 2 GB is only used once the first 2 GB is full, so a normal short game proves little.
To force it: `GAMEPATCH_HIGHMEM=1 scripts/play-rotwk.sh` (or `highmem=1` in the game folder's
`gamepatch.ini`). The game patch then reserves the free space below 2 GB at start-up, except
`highmem_slack` (256 MB), and `logs/gamepatch.log` gets a `highmem: reserved … MB` line. Play a
skirmish with `scripts/memwatch.sh` running and look for crashes, missing textures or sound, and new
`DUMP_*.dmp` files in the game folder (`tools/parse_minidump.py`). Starting without the variable
turns it off. `gamepatch/tests/t_highmem.c` checks the reservation without the game.

## Open risks

Wine code off the tested paths (winecoreaudio, mss32's own threads), and the game's own code under
Wine rather than Windows.

## Patch 0022: textures out of the 32-bit address space (offline, 2026-10-04)

Built, not installed: `scripts/wine-0022.sh --stage` puts patch 0022 (MEMORY-2GB.md) on top of the
series the game plays on (bfme-fixes-10.0, wined3d 0001–0021) in wine/src-0022, builds wined3d.dll and
wined3d.so with wine-fixes.sh's flags, and stages them in build/wine-0022/ plus an engine clone in
build/engine-0022. Install with `scripts/wine-0022.sh --install`, undo with `--revert`. Switch it off
without reinstalling with `WINED3D_STASH_MANAGED=0`.

**Test** (`scripts/texstash.sh`, `tools/texstash.c`). A large-address-aware 32-bit process loads
textures the game's way (managed, full chain, every level locked and filled once) in our formats and
sizes: X8R8G8B8 normal maps, DXT5/DXT1 sheets from 1024 to 4096, A8R8G8B8 masks, 10 % in DEFAULT pool.
It loads up to 4.5 GB, then draws each texture, runs 300 frames, evicts, relocks 29, calls GetDC on 4,
resets the device, and checks a CRC of every draw against the other engine.

| (Apple M3 Max, throwaway prefix) | engine as installed | + 0022 |
|---|---|---|
| address space used at 4.09 GB of textures | 3660 MB (largest free 431) | 85 MB, 63 after the draws |
| peak (after relocks and Reset) | 3660 MB | 282 MB (relocked textures stay in 32-bit memory) |
| with 1.3 GB taken first, as the game does in a match (`--reserve 1300`) | the fill fails at 3064 MB (address space), then the process crashes | loads to 4094 MB |
| where loading stops | 4094 MB: `D3DERR_OUTOFVIDEOMEMORY` | the same |
| CRC of 1518 draws (first, after evict, relock, GetDC, Reset) | | all identical; `WINED3D_STASH_MANAGED=0` gives the installed engine's CRCs and numbers |

**Speed.** Three alternating pairs. Other agents kept the machine's load at 21–48 on 16 cores, so the
spread is wide.

| | installed | + 0022 |
|---|---|---|
| frame, 256 textures, application thread (median) | 1.76 / 3.44 / 2.97 ms | 1.50 / 3.19 / 2.58 ms |
| fill (application thread) | 0.90 / 1.89 / 1.74 ms per MB | 1.02 / 1.79 / 2.32 ms per MB |
| first draw of a texture (the upload, waited for) | 0.39 / 1.35 / 0.98 ms per MB | 0.73 / 1.88 / 1.66 ms per MB |
| redraw after EvictManagedResources | 0.36 / 1.54 / 1.16 ms per MB | 1.08 / 2.44 / 0.76 ms per MB |

Frames and the fill are within the spread. Every pair shows a slower first draw, by 0.3–0.7 ms per
MB: the texture is copied back below 4 GB for the upload and stashed again. That work runs on the
render thread. For a 2048² DXT5 sheet (5.3 MB, a 4.3 ms first use in PERFORMANCE.md §13), it adds about
2–4 ms.

**Risks found**
- The next ceiling is wined3d's video-memory accounting. GPU copies of textures and buffers are
  capped at 4 GB whatever `VideoMemorySize` says, because `wined3d_device_get_available_texture_mem`
  clamps to `UINT_MAX`. Past that, `D3DERR_OUTOFVIDEOMEMORY` reaches WW3D's free-and-retry path, which
  means hitches, not a crash. The full 8-player build (about 2.9 GB of texture) is under it.
- With 1.3 GB taken first, redrawing every texture after a device Reset hit an Apple Metal assertion
  ("commit command buffer with uncommitted encoder") at 3.6 and 4.1 GB of textures. It did not happen
  at 3.1 GB, or at 4.1 GB without the 1.3 GB. The installed engine cannot get that far, so it can't
  be compared there. In the game, Reset means alt-tab or a mode change.
- The host keeps a copy of every texture (+1× texture bytes of host RAM). That is fine on 64 GB;
  check the LAN Mac's RAM.
- A texture locked again after its upload stays in 32-bit memory (the radar and text pages: small).
  Under wined3d 0012 a stashed texture is not client-mappable (no SYSMEM location), so the map goes
  through the render thread, which restores it first. The relock test covers this. The 0003/0009
  dynamic-buffer paths draw every quad of the test.
- Not covered: cube and volume textures, and the game itself. A play session with
  `scripts/memwatch.sh` is the next step.

## Growth over a match: 0022's copies in macOS's medium malloc zone (2026-10-15, session + standalone tests)

**The session.** `logs/sessions/20261015-160144` (8 players, mp woody end, 98 min; 0022 installed,
terrain32 and terrainbox on). The macOS footprint rose from ~3.0 GB when the match got going to 5.9 GB
after 78 min (peak 6.5 GB). The game's 32-bit committed memory rose 837 -> 1369 MB over the same time,
so ~2.3 GB of the growth was outside the 4 GB. 131,375 D3DX texture creations (53,358 terrain32 near-tile
bakes: 512² X8R8G8B8, 3 levels, 1.31 MB each) and 2,213 file loads. Per 60 s window the footprint grew
with the window's loads and creations; in the 23 windows without a load it barely moved (+120 MB with
28,429 creations). The recorder had no per-region numbers, so the split inside those 2.3 GB is not known.

**Mechanism** (`scripts/texchurn.sh` + `tools/texchurn.c`, engine w10 + 0022 as installed, M3 Max 64 GB,
the near tiles' create / fill / D3DXFilterTexture / draw / release; vmmap of the test). wined3d.so took
each stashed copy from `malloc()`. A 1.31 MB block goes to libmalloc's medium zone (32 KiB-8 MiB), which
is only engaged on Macs with 32 GiB or more (`MEDIUM_ACTIVATION_THRESHOLD`, libmalloc `thresholds.h`).
It returns free memory only in runs of its madvise window, which grows with the bytes the zone holds
(1.5 MiB minimum; with ~2 GiB of copies, 256 MiB), and it has a magazine per CPU. vmmap after 45,000
textures with 120 alive: DefaultMallocZone 1.2 GB dirty, 158.7 MB allocated, 87 % fragmentation. Not a
leak: every copy is freed, but the zone keeps the pages.

| (texchurn, 30 created and released per cycle) | stash off | 0022 installed | 0022 + fix |
|---|---|---|---|
| 120 alive, 21,000 textures: footprint end (MB) | 620 | 1,588 (+30 per 1000 in the second half) | 613 (0) |
| 120 alive, 45,000 textures | | 1,850 (1,669 at 15,000) | |
| 1,500 alive (2 GB of copies), 15,000 textures | | 5,572 (+60 per 1000) | 4,313 (0) |
| same, cached fix, second pair | | 5,116 | 4,331 |
| 300 alive + one texture kept per cycle (1.1 GB kept), 18,000 | | 4,285 | 3,304 |
| installed engine with `MallocMediumZone=0` (as on a Mac under 32 GiB), 120 alive | | 626 (flat) | |
| 32-bit committed | 232 | 108 | 108 |

**Fix** (in patch 0022, `unix_gl.c`): copies of 32 KiB and more get their own anonymous mapping
(VM tag 247, so vmmap and the recorder name them), unmapped when freed; up to 64 MiB of freed mappings
are kept for reuse by size (a fresh mapping costs a page fault per page; every upload frees a copy and
makes another of the same size). What the zone could keep is now bounded at 64 MiB. Built with
`make dlls/wined3d/wined3d.so` in wine/build-0022 (wined3d.dll unchanged), staged in build/wine-0022
(the previous `.so` kept as `build/wine-0022s/wined3d.so.prev-0022`) and build/engine-0022; not
installed. Install: `scripts/wine-0022.sh --install`; undo: `--revert` (the series without 0022).
- `scripts/texstash.sh`-style CRC check (2 GB, every draw after load, evict, relock, GetDC, Reset):
  779 of 779 draws identical to `WINED3D_STASH_MANAGED=0`.
- Speed: texchurn's wall time unchanged (43.1 vs 43.1 s, 60.9 vs 60.5 s per 15,000 textures). In texstash's
  bulk load of large textures (4-22 MB each, mostly past the reuse cache), first draws 1.03 / 1.07 vs
  0.93 / 0.91 ms per MB and evict redraws 0.98 / 1.03 vs 0.83 / 0.88 (two alternating pairs, machine load
  ~5): ~0.1-0.15 ms per MB more on the render thread, from the page faults of fresh mappings.

**What stays.** Every managed texture still costs its bytes twice on the host: the stashed copy and the
GPU's (IOAccelerator) copy, as it did in 32-bit memory before 0022. On a Mac under 32 GiB (the 8 GB M1)
the medium zone is off, so this retention never happened there; that Mac's risk is the match's real
working set (textures x2 + the game's ~1.4 GB), around 5 GB late in an 8-player match. The copies are
cold after their upload, so macOS compresses or swaps them without slowing the game; the GPU copies and
the game's heap are hot. Next session: the summary's "Memory by VM tag" lines (MALLOC_MEDIUM should stay
small, "wined3d stash" = the copies, IOAccelerator = the GPU's) split the growth for real.
