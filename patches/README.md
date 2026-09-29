# Wine patches

Everything here is LGPL-2.1-or-later ([COPYING.LIB](COPYING.LIB)). The two series in use are applied
on top of `wine-10.0` and built by `scripts/wine-fixes.sh` (worktree `wine/src-d3dx10`, branch
`bfme-fixes-10.0`) with SSE2 maths instead of x87 in the 32-bit DLLs; `scripts/install.sh` installs
the prebuilt DLLs from a release.
`scripts/wine-fixes.sh --revert` restores the engine's own DLLs.

| Folder | What | Record |
|---|---|---|
| [d3dx9-setrawvalue/](d3dx9-setrawvalue/) | Wine's own `d3dx9_27` in place of Microsoft's: the load-time fix, and faster effects | its README, [LOAD-TIME.md](../docs/LOAD-TIME.md), [PERFORMANCE.md](../docs/PERFORMANCE.md) §11 |
| [wined3d-wow64-buffers/](wined3d-wow64-buffers/) | big-battle frame rate: buffer and texture locks, redundant state, GLSL programs, shader constants | [PERFORMANCE.md](../docs/PERFORMANCE.md) §4–§6, §12 |
| [lock-whole-buffer/](lock-whole-buffer/) | `Lock(offset, 0)` on d3d8/d3d9 buffers, written for upstream Wine 11.0 | its README |
| `nxcompat/` | NX_COMPAT-flagged copies of the games' modules; made no difference, not used | `nxcompat/install.sh` |
| [WINE-BUG-REPORT.md](WINE-BUG-REPORT.md) | the Wine 11 WoW64 crash (`syscall_32to64` run as 32-bit code) | |
| [WINE-BUILD.md](WINE-BUILD.md) | building WoW64 Wine from source on macOS | |

## d3dx9-setrawvalue (0001–0008)

| Patch | Change |
|---|---|
| 0001 | `ID3DXEffect::SetRawValue()` for 4-component vectors (upstream, Connor McAdams) |
| 0002 | 4x4 row-major matrices in `SetRawValue()` (upstream, Connor McAdams) |
| 0003 | import `windowscodecs` directly instead of delay-loading it (mingw toolchain workaround) |
| 0004 | struct parameters in `SetRawValue()`: the games' bone palettes and lights |
| 0005 | preshader instructions run through direct register pointers |
| 0006 | only the preshader instructions whose inputs changed are rerun |
| 0007 | parameter handles checked without `strncmp()` |
| 0008 | CommitChanges() skips constant states that cannot set anything |

## wined3d-wow64-buffers (0001–0021 in use, 0022 unbuilt)

| Patch | Change |
|---|---|
| 0001 | dynamic buffers can be pinned in system memory (`WINED3D_WOW64_BUFFERS=pin`); size-0 lock dirty range |
| 0002 | clip planes recomputed only when enabled |
| 0003 | DISCARD/NOOVERWRITE buffer maps get fresh system memory, uploaded on unmap: no wait for the render thread |
| 0004 | redundant vertex declaration sets ignored |
| 0005 | redundant viewport sets ignored |
| 0006 | redundant texture-stage state sets ignored |
| 0007 | redundant render-state sets ignored |
| 0008 | every default state pushed once from a fresh primary stateblock (keeps 0004–0007 correct) |
| 0009 | streamed buffer ranges written straight into host buffer memory (`wined3d.so`) |
| 0010 | streamed memory not freed while a buffer is still mapped (a use-after-free in 0003) |
| 0011 | pixel format queried once per present, not per draw; vertex attribute divisors cached |
| 0012 | CPU-only textures mapped on the game thread |
| 0013 | system-memory buffers mapped on the game thread |
| 0014 | small system-memory texture uploads copied on the game thread |
| 0015 | one pending upload per resource |
| 0016 | DISCARD maps of dynamic textures streamed through system memory |
| 0017 | rasterizer input setup shader reused between programs |
| 0018 | only active uniforms looked up when linking a program |
| 0019 | linked GLSL programs recorded and rebuilt ahead of first use next session |
| 0020 | only the float shader constants that changed are pushed |
| 0021 | push-constant data carried inside the push-constant command |
| `unbuilt/0022` | managed textures' system memory kept in host memory: written, not built, not played ([MEMORY-2GB.md](../docs/MEMORY-2GB.md)) |

Each patch's environment switch and measured effect are in [PERFORMANCE.md](../docs/PERFORMANCE.md) §6.

## The two old crash theories

- **`Lock(offset, 0)`.** BFME2's `warn+d3d` logs are full of `Box (0, 0, 0)-(0, 1, 1) is invalid`
  after `Lock(offset 0, size 0)`. On buffers that is only a warning: the map still succeeds. The
  real defect is smaller: with `offset > 0` wined3d records a zero-length dirty range, so the
  written data never reaches the GPU copy. `lock-whole-buffer/` fixes it for upstream (built and
  tested against wine-11.0, not submitted); wined3d-wow64-buffers 0001 carries the dirty-range part.
  An earlier 2-byte binary patch only silenced the warning; the crashes were the next item.
- **WoW64 `syscall_32to64`.** Every "random" crash on Wine 11.0 and 11.17 was the 32→64 transition
  stub run as 32-bit code ([WINE-BUG-REPORT.md](WINE-BUG-REPORT.md)). It does not reproduce on
  Sikarugir's 10.0 build, which both games use (`WINE_BUILD=w10`, the default). A bisect found no
  good commit to compare against ([docs/history/BISECT-2026-09-23.md](../docs/history/BISECT-2026-09-23.md));
  the report is drafted, not filed.

## Game-data changes (not Wine)

- `ini.big` → `data\ini\gamelodpresets.ini`: every `LODPreset` row removed
  (`tools/neuter_gamelod.py`, applied by `scripts/install.sh`), otherwise the CPU benchmark under
  Rosetta picks a preset that crashes before the menu (DrewHoo's finding).
- Camera height, particle count and heat effects are in the group pack
  (`tools/make_group_pack.py`, [MULTIPLAYER.md](../MULTIPLAYER.md)).
- LARGEADDRESSAWARE: on for RotWK, off for BFME2, as each ships ([MEMORY-4GB.md](../docs/MEMORY-4GB.md)).
