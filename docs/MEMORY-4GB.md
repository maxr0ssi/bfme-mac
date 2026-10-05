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
