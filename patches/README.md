# Local Wine patches for BFME under Wine on macOS

## 1. `Lock(offset, 0)` on D3D9 buffers (correctness fix, upstream patches in `lock-whole-buffer/`)

**History.** Early on, BFME2's "random" access violations were blamed on this: `warn+d3d` logs end
with many `wined3d_resource_check_box_dimensions Box (0, 0, 0)-(0, 1, 1) is invalid` lines, each
preceded by `d3d9_vertexbuffer_Lock(..., offset 0, size 0, ...)`, and the theory was that the lock
failed and the game wrote through a stale pointer. A 2-byte binary patch (`jae`→`ja` on the two
range checks in `wined3d_resource_check_box_dimensions`) was applied to make the box pass.
**That diagnosis was wrong.** Since wine 6.x (commit 08c96a4888, "wined3d: Move box validation to
wined3d_device_context_map"), an invalid box on a *buffer* only produces the WARN; the map goes
ahead and returns a valid pointer (`dlls/wined3d/device.c`, `wined3d_device_context_map`, the
`resource->type != WINED3D_RTYPE_BUFFER` test). Wine's own d3d9 tests lock buffers with
`(0, 0)` and require `D3D_OK`. So the binary patch only silenced the warnings; the crashes were
§2 all along, which is why they stopped when the games moved to the Wine 10.0 engine.

**What is actually wrong.** Per the D3D9 docs a size of 0 means "from offset to the end of the
buffer". `dlls/d3d9/buffer.c` (and d3d8) pass `wined3d_box_set(&box, offset, 0, offset + 0, ...)`
straight through, and wined3d's `buffer_invalidate_bo_range()` (`dlls/wined3d/buffer.c`) then
records a **zero-length dirty range** whenever `offset > 0`, so data the application writes after
such a lock never reaches the GPU copy. `offset == 0` only works because of that function's
`!offset && !size` special case. Present on current master.

**Fix.** `patches/lock-whole-buffer/` holds three Wine-style patches against wine-11.0 (d3d9,
d3d8, and a d3d9 test `test_buffer_zero_lock_size` covering vertex and index buffers, offset 0 and
offset 256, and the game's exact dynamic/write-only/DISCARD pattern), plus a README with the
upstream submission steps. Not yet compiled: the Wine build under `wine/` is what will run the test.

**Binary patch status.** `patches/wined3d/*.emptyrect-patched` is installed in both `engines/stable`
and `engines/w10` (originals kept as `patches/wined3d/wined3d.dll.orig-11.0` and, for w10, next to
the DLL as `wined3d.dll.orig-w10`). It is harmless and pointless; keep or revert as you like.

## 2. WoW64 `syscall_32to64` executed in 32-bit mode (the real cause of every "random" crash)

**Symptom.** A thread dies with `EXCEPTION_ACCESS_VIOLATION` at `0x7BF2113x`/`0x7BF2123D` reading
a tiny address (`0x4ECD`/`0x4DC9`); the game's crash handler recurses until `stack overflow` and
Wine aborts only that thread. Main thread: the process exits with no dump (RotWK at the end of
loading). Worker thread: the game lingers "frozen" at ~25% CPU (BFME2 minutes into a match,
BFME2 at startup when a second Wine process, e.g. the AutoHotkey helper, starts in its first ~8 s).

**Cause.** `0x7BF20000` is the 64-bit `wow64cpu.dll` mapped below 4 GB. The faulting bytes are
`syscall_32to64`, the 32→64 transition stub, being executed **as 32-bit code**: decoded that way
they reproduce every register in the dumps, and the "fault address" is the displacement of its
`mov edx,[rip+cs32_sel]`. It happens right after bursts of 64→32 window-message callbacks. Full
write-up with the disassembly and evidence: `WINE-BUG-REPORT.md`.

**Status.** Reproduces on wine-11.0 and wine-11.17 (Gcenx builds), does not on the Sikarugir Wine
10.0 engine, so it is a 10.0→11.0 regression on macOS/Rosetta. Both games now play on that engine
(`WINE_BUILD=w10`, the play scripts' default). Ruled out: NX_COMPAT on all 47 modules (`patches/nxcompat/`,
reverted), LARGEADDRESSAWARE, Windows version, threaded loading, Retina, shader logging,
`WINE_CPU_TOPOLOGY`, DXVK. Next: bisect with the from-source builds under `wine/` and report
upstream.

## Other engine-side fixes (not Wine bugs)

- `ini.big` → `data\ini\gamelodpresets.ini`: all `LODPreset` rows removed, otherwise the CPU
  benchmark under Rosetta picks a preset that overruns a buffer and crashes before the menu
  (DrewHoo's finding). Backup: `ini.big.preLODfix.bak`.
- `ini.big` → `data\ini\gamedata.ini`: camera `DefaultCameraMinHeight 120→150`,
  `DefaultCameraMaxHeight 300→400`, `DefaultCameraPitchAngle 37.5→35` (widescreen zoom).
  Backup: `ini.big.preCameraFix.bak`. Multiplayer peers need identical INIs.
- `game.dat` LARGEADDRESSAWARE must stay **off** under Wine (crashes otherwise; backup
  `game.dat.preLAA.bak`).
