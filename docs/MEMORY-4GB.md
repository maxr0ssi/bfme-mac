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
