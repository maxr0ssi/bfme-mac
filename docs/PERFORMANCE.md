# Performance: big battles on Apple Silicon — measurements and fixes

Record of every measurement behind the rendering-performance work. Machine: MacBook Pro, Apple M3
Max (12P+4E cores, 40-core GPU), 64 GB unified memory, macOS 26.3, `powermode 0`. Engine
`engines/w10` (Sikarugir wine-staging 10.0, new-style WoW64, x86_64 under Rosetta), D3D9 → wined3d →
Apple OpenGL 4.1 ("4.1 Metal - 90.5"). Game: RotWK 2.02 + HD Edition, 3024x1964, Options.ini
UltraHigh except Shader/Shadow/Water Medium. Another session ran Blender renders during the
2026-09-24 micro-benchmarks (load average 7–15), so single-run numbers there carry that noise.

Rule used throughout: a change counts only when its effect is outside the run-to-run spread, and
anything the player sees is checked by eye as well (Open-BFME-1's `docs/fps60.md` lesson).

## 1. Where a frame goes (the pipeline)

```
game thread:   game code (~20 ms in a small fight) | wined3d client work | buffer Lock
                                   ▼ wined3d command queue (CS)
render thread: GL calls → opengl32.dll (32-bit) → unix call → opengl32.so → Apple GL → Metal → GPU
```

Two threads do all the work; the other 14 cores idle. Before the fixes below, every dynamic-buffer
Lock made the game thread wait for the render thread (`wined3d_resource_wait_idle` +
`wined3d_cs_mt_finish` in `emit_map`, cs.c), so the two threads took turns: frame time was the
**sum** of both, not the larger.

## 2. In-game measurements

Tools: `tools/perfprobe.py` (frame times from `WINEDEBUG=-all,+fps,+frametime`, per-thread CPU from
`ps -M`, optional `build/eipsample.exe` guest profile), `scripts/bench-matchstart.sh` (hands-free,
same map and camera each run).

| when (2026-09-24) | build | scene | FPS | frame p50 / p95 / p99 ms |
|---|---|---|---|---|
| 09:27 | pin fix on (first fix) | Edoras, match start | 20.2 | 46 / 70 / 82 |
| 09:29 | pin fix on | Edoras, small fight (15 s before a crash) | 10.9 | 91 / 103 / 106 |
| 09:31–09:34 | pin fix off (stock buffer path) | Edoras, own base, no fight, 13 windows of 15 s | 8.2–11.5 | 87–127 / 98–162 / 106–174 |

| 11:33–11:35 | **fixes 0001–0011 + SSE2** | Edoras, own base, no fight (same view as 09:31) | **29.3–30.3** (capped) | 33.0–33.2 / 34–39 / 35–72 |
| 11:35–11:37 | fixes 0001–0011 + SSE2 | Edoras, small battle (same kind as 09:29) | **22.1–29.7** | 33–44 / 39–57 / 43–64 |

Fixed build, per-thread CPU in the small battle: game thread 81–84 % of a core, the two render-side
threads 18–29 % each, process 135–142 %; thread priority 46–47 (game) / 31 (others), i.e. not
background QoS. GPU utilisation (`ioreg` IOAccelerator "Device Utilization %", 1 s samples) 11–16 %:
the GPU is not the limit at 3024x1964. With no thread saturated, the dips below 30 are waiting
(suspected: texture locks and other maps that still take the synchronous CS path; to be checked
with `+d3d_perf`). One-off hitches of 80–170 ms appear (likely first-use shader compiles).
The player's verdict: "This feels so much better."

Scenes differ between the first rows, so pin-on vs pin-off is not a clean A/B; both are ~10 FPS in a fight
and the pin fix is not the answer. Pin-off per-thread CPU: host thread #2 93–94 % of a core, #15
68–75 %, process 178–196 %.

Game-thread profile, pin fix on, match start (eipsample, 3,331 samples, tid 36 = game main thread):
`ntdll` 42.9 % (waits), `wined3d` 27.7 %, game exe 21.4 %, `d3dx9_27` 4.0 %. Call sites:
`wined3d_resource_wait_idle` from `emit_map` 15.9 %, `wined3d_cs_mt_finish` 13.5 % (together
~30 %: the lock wait); `invert_matrix`/`transpose_matrix`/`multiply_matrix` ~17 %. Small fight:
wait_idle 17.4 %, finish 9.6 %, same module split.

The earlier render-thread profile (pin off, before this record) put ~38 % at the return of the
`glMapBufferRange` unix call, ~24 % at `glUnmapBuffer`'s, ~25 % at `ntdll+0xcc6c`. **Correction:**
`ntdll+0xcc6c` is where the guest EIP sits while the thread runs *host* code inside a unix call, so
that 25 % is driver/host time, not WoW64 transition cost (§3: a transition is 0.05 µs).

macOS `sample` is useless here: under Rosetta every frame of every thread is "unknown binary".

## 3. Micro-benchmarks without the game (`tools/glcallcost.c`)

32-bit program on the same engine, OpenGL 4.1 core forward-compatible context like wined3d's; a
64-bit build of the same source for the native comparison. µs per call or per upload+draw; ranges
are across 2–4 runs.

| operation | 32-bit (WoW64) | 64-bit native |
|---|---|---|
| glGetError / glEnable / glUniform4fv (the transition itself) | 0.05–0.06 | 0.014–0.019 |
| glBufferSubData, 64 B … 64 KB, no draws | 22–41 (fixed cost, size-independent) | 147–189 |
| glBufferData(NULL) orphan, 1 MB | 0.11–0.13 | 0.16 |
| glMapBufferRange+Unmap, 64 B, WRITE\|UNSYNC | 56–82 | 0.20 |
| glMapBufferRange+Unmap, whole 1 MB (stock wined3d, per lock) | 292–391 | 0.07 |
| **WW3D pattern** (append 256 B–16 KB, draw it, repeat; 5000-vertex VB): glBufferSubData | 21–56 | 51–114 |
| same, orphan the VB before each upload | 3–15 | 5–13 |
| same, pool of 256 buffers round robin | 2–6 | 5–13 |
| same, unsynchronized range map + memcpy + unmap | 73–143 (unmap ~90 of it) | **0.30–0.54** |
| draws only, data already uploaded | 0.08–0.12 | 0.04 |

Findings:
1. The WoW64 transition is cheap (0.05 µs). Batching GL calls is not worth doing.
2. Apple's driver is fast when written through an unsynchronized mapping: 0.3 µs per upload+draw
   natively. That is unified memory working: the CPU writes GPU-visible memory directly.
3. Wine's 32-bit map bridge (`dlls/opengl32/wgl.c` + `unix_wgl.c`: map, second call with a
   malloc'd 32-bit copy, copy back and free on unmap) turns that into 73–143 µs; the unmap
   dominates. Replaying the bridge's extra GL queries natively costs nothing (0.19–0.23 µs), so the
   cost is in the bridge itself. (Unexplained: after a loop that also queried the map pointer and
   length between map and unmap, later 32-bit unsync maps ran at 0.6–1.7 µs.)
4. `glBufferSubData` interleaved with draws is 20–60 µs per call: Apple has to split the GPU
   command stream for each upload into an in-flight buffer. Wrong tool for per-draw streaming.

## 4. Synthetic BFME frame (`tools/d3d9bench.c`, `scripts/bench-d3d9.sh`)

A 32-bit D3D9 program that issues EA's WW3D2 per-frame pattern (shared 5,000-vertex dynamic VB with
exact-range NOOVERWRITE/DISCARD locks, a world matrix per object, redundant state, fixed-function
and vs_1_1/vs_2_0 draws). Each build installed in the engine in turn (so `wined3d.so` loads as it
will in the game); median of 3 runs of 10 s after a 2 s warm-up; 2026-09-24 ~10:20, with another
session's Blender builds running.

| build | default scene (2000 objects, 300 dynamic draws) | heavy scene (3000 objects, 900 dynamic) |
|---|---|---|
| stock (`wined3d.dll.orig-w10`) | 73.6 ms, 13.6 FPS | 183.9 ms, 5.4 FPS |
| stream + clip planes + state + SSE2 (fixes 2–5) | 42.1 ms, 23.8 FPS | 88.8 ms, 11.3 FPS |
| **+ direct host-buffer writes (fix 6)** | **21.9 ms, 45.7 FPS** | **34.2 ms, 29.3 FPS** |
| same, installed by `scripts/wine-fixes.sh` | — | 34.0 ms, 29.4 FPS |

App-thread split, default scene: stock spends 22 ms in Lock + 41 ms in Unlock per frame (the wait
for the render thread); with fixes 2–6 Lock + Unlock is 0.14 ms and the remaining time is the
render thread (seen as the wait in Present: 32 ms without fix 6, 13 ms with it).
Image checksums (`--crc`) are identical between stock and the fixed build in all three scenes
tried (grouped, grouped heavy, default interleaved): `64abfac0`, `5eb28a61`, `68fe2221`.
Stock itself is occasionally non-deterministic in the interleaved scene (stray triangles; agent
calibration run), the NOOVERWRITE race that Wine's test 26868 below also catches.

UI-side scenes (2026-09-24 15:00–15:30, fixes 0012–0019 as `direct4` vs `direct3`, median of 3,
`WINEMSYNC=1`, `--objects 800 --cpu-ms 20` = 20 ms of stand-in game work per frame; a Zoom call
was loading the machine, builds were run interleaved):

| scene | direct3 | direct4 |
|---|---|---|
| base, no UI | 25.0 ms | 24.7 ms |
| `--radar 400` (one-pixel radar locks) | 31.1 ms (UI 7 ms) | 24.2 ms (UI 0.1 ms) |
| `--text 30` (text-surface locks) | 43.1 ms (UI 19 ms) | 24.8 ms (UI 0.17 ms) |
| `--relock 20` (managed buffer relocks) | 24.5 ms | 24.2 ms |
| `--dyntex 8` (dynamic texture DISCARD) | 43.3 ms (UI 19 ms) | 24.4 ms (UI 0.25 ms) |
| all UI work, engine swap | 33.5–34.4 ms | 24.3–24.7 ms |
| heavy scene, engine swap | 33.2–35.0 ms | 33.9–34.1 ms |
| new GLSL program at first draw (`--programs 200`, p50) | 3.2–3.8 ms | 0.73–0.81 ms (cache warm) |

The game's in-game round trips were cheaper than the bench's (~426 per frame, 0.77 ms total), so in
the game expect ~0.8 ms/frame back plus no 7–50 ms text-lock hitches, not the bench's full gap.
Image checksums match direct3 for every patch (`64abfac0`, `5eb28a61`, `d28e1dc8`, UI scenes
`da294342`, `5ad3a6e9`; dynamic-texture scene `720f8579` on all builds). `tools/d3d9lockcheck.c`
(radar locks between draws, UpdateTexture/UpdateSurface, relocks with read-back, DISCARD
sub-rectangles, two levels locked at once) passes on direct3 and every patch.

## 5. Correctness: Wine's d3d9 visual test suite

`wine/build-11.0/dlls/d3d9/tests/i386-windows/d3d9_test.exe visual` on the w10 engine (211,245
checks), one run per build:

| build | result |
|---|---|
| stock | completes, 267 failures |
| fixes 2–5, `WINED3D_WOW64_BUFFERS=off` / `=pin` | completes, 266 / 265 |
| fixes 2–5, stream (first version) | **crash** after `test_dynamic_map_synchronization` |
| fixes 2–6 + flush fix (installed) | completes, **262 failures: 5 fewer than stock, none new** |
| + 0011–0019 (each patch separately; 0019 cold and warm) | 262, identical failure list |

The crash was a use-after-free: an application may draw from a buffer it still has mapped
(Castlevania 2's pattern; wined3d uploads the mapped data before each such draw), and each of those
uploads freed the streamed system memory the application was still writing. Reproduced in a
standalone copy of the test under `WINEDEBUG=warn+heap` ("delayed freed block"), fixed in patch
0010, reproducer clean afterwards. The checks the fixed build passes and stock fails: 17476 (x2),
26276, 26868 (NOOVERWRITE synchronisation), 27016 (size-0 lock, BFME2's pattern).

## 6. Fixes (patches/wined3d-wow64-buffers/, installed by scripts/wine-fixes.sh)

| patch | change | effect |
|---|---|---|
| 0001 | pin dynamic buffers in sysmem (`WINED3D_WOW64_BUFFERS=pin`); size-0 lock dirty range | superseded as default; the size-0 part fixes test 27016 |
| 0002 | clip planes recomputed only when enabled (upstream 2dad2e74764) | ~17 % of the game thread in the in-game profile |
| 0003 | DISCARD/NOOVERWRITE maps get fresh sysmem, uploaded on unmap: no wait (`=stream`, default; `=off` for stock) | Lock+Unlock 64 ms → 0.14 ms per frame (bench) |
| 0004–0007 | redundant vertex declaration / viewport / texture-stage / render-state sets ignored (upstream 7f5c2105964, 95bb04efb00, 7be265ec89a, 8dcbf5d8235) | fewer CS commands per draw |
| 0008 | every default state pushed once from a fresh primary stateblock (what upstream c42d364fa4d covers) | keeps 0004–0007 correct |
| 0009 | `wined3d.so`: write streamed ranges straight into host buffer memory (orphan on DISCARD, unsynchronized map + memcpy + unmap, one transition) | 42 → 22 ms and 89 → 34 ms per frame (bench) |
| 0010 | don't free streamed memory when flushing a still-mapped buffer | fixes the test-suite crash |
| 0011 | pixel format queried once per present, not per draw; vertex attribute divisors cached | heavy scene 34.0 → 30.6 ms (§8) |
| 0012–0013 | CPU-only textures (managed/systemmem/scratch) and sysmem-only buffer maps done on the game thread when no queued command uses them (`WINED3D_CLIENT_MAPS=0` = off) | radar 400 px locks: UI 7 → 0.1 ms/frame; text locks 19 → 0.17 ms (bench) |
| 0014 | sysmem texture uploads ≤ 256 KiB copied on the game thread (no render-thread blit holding the source) | part of the above |
| 0015 | one pending upload per resource; an unmap only takes its own sub-resource's upload | fixes lost data / leak / wrong-target upload on a second map |
| 0016 | stream mode: DISCARD locks of dynamic textures get sysmem for the box, uploaded on unlock | `--dyntex 8`: 43.3 → 24.4 ms (bench) |
| 0017–0018 | rasterizer-setup shader compiled once per source; only active uniforms looked up at link (first 16 links cross-checked) | new program at first draw 3.2–3.8 → 2.9 ms |
| 0019 | linked GLSL programs recorded to `AppData/Local/wined3d/<exe>.glslprograms`, rebuilt in idle CS time next session (`WINED3D_PROGRAM_CACHE=0` = off) | first-draw program build 3.4 → 0.8 ms (warm) |
| 0020 | float shader constants pushed to the CS only where their bits changed since the last push (`WINED3D_CONST_FILTER=0` = off) | effects bench: render thread 8.2 → 6.1 ms/frame; §12 |
| 0021 | a constant push carries its data in the PUSH_CONSTANTS op instead of a heap copy + upload op (`WINED3D_INLINE_PUSH_CONSTANTS=0` = off) | DrawIndexedPrimitive 0.77 → 0.65 µs per draw; §12 |
| build | 32-bit DLLs compiled with `-msse2 -mfpmath=sse` | x87 instructions: wined3d 6,684 → 801, d3dx9_27 11,486 → 138 |

Revert everything: `scripts/wine-fixes.sh --revert` (restores `.orig-w10` DLLs, removes `wined3d.so`).

Game-side facts from EA's released WW3D2 source (`dx8vertexbuffer.cpp`): dynamic geometry goes
through one shared 5,000-vertex dynamic VB; each lock is exactly the drawn range with
`NOSYSLOCK | (offset ? NOOVERWRITE : DISCARD)`; the whole-buffer `Lock(0,0)` path is for fills.

## 7. Vulkan (wined3d `renderer=vulkan` → MoltenVK → Metal): studied, not adopted

- Zero-copy is real there: winevulkan imports memory it reserves below 4 GiB through
  `VK_EXT_external_memory_host` (pointers at 0x00A10000), MoltenVK wraps the same pages as a Metal
  buffer; dynamic-VB draws 1.9 µs vs 61 µs on stock GL.
- But wined3d 10.0's Vulkan backend renders this content wrongly (clears read back black, no DXT,
  alpha test / fog ignored, cube textures abort Metal; d3d9 visual: 150 failures then a Metal abort),
  ps_1_1 `tex` crashes vkd3d-shader in the bench, and every shader-constant update ends and restarts
  the render pass: 71 µs per draw vs 2.4 µs on GL. Wine 11.0 fixes most correctness items (not fog,
  L8/A8L8/D24X8), not the constant cost.
- To make it win: take 11.0's wined3d + d3d9 + vkd3d 1.18 as a unit, stream constants through
  host-visible memory, treat the renderer as persistently mapped on 32-bit, add fog and formats.
  Weeks of work; the GL path with patch 0009 gets the buffer benefit now.

## 8. Other levers checked (2026-09-24, after the fixes)

- **Core placement.** Heavy bench scene, fixed build: launched normally 29.0 FPS (34.5 ms);
  under `taskpolicy -b` (background QoS, efficiency cores) 0.95 FPS. A normal launch lands on
  performance cores; whether the game started from its applet does too is recorded by
  `tools/perfprobe.py` (per-thread `ps` priority: 31 default, 4 background) in the next game run.
  Power mode was `powermode 0` (Automatic) on AC; High Power needs `sudo pmset` or System Settings.
- **msync (`WINEMSYNC=1`).** Works in this engine ("msync: up and running"). A first A/B ran while
  another session's Blender renders held the load average at ~36 and is void (both arms 13–21 FPS
  vs 29 on a quiet machine). Repeated quiet (load 4–5), interleaved 0/1/0/1, 3 runs each: off
  33.8–34.6 ms, on 33.5–34.0 ms. ~1.5 %, ranges overlap: not a lever; left off.
- **msync in a real battle (the lever that mattered).** The earlier bench A/B could not show it: the
  bench never takes the game's DirectX lock, a critical section plus a Win32 kernel mutex taken around
  all rendering. Hands-free AI battle (`scripts/bench-battle.sh`), game main thread only
  (`eipsample … main`), battle windows: without msync (run ai1, 18.9 FPS, 50.7 ms p50) ntdll 37.8 %
  of the thread — NtWaitForMultipleObjects 20.8 %, NtReleaseMutant 13.6 %: ~19 ms a frame of
  wineserver round trips; with `WINEMSYNC=1` (run msync2, 21.7 FPS, 42.0 ms p50, a heavier battle:
  game code 32 vs 25 ms a frame) ntdll 5.9 % (~2.5 ms): NtReleaseMutant gone, the wait 2.4 %. The
  memory probe (build/rotwk-re/memprobe.exe; analyze_probe.py) showed the lock held only by the main
  thread in every sample of both runs (11,014 / 12,420), so the mutex was pure overhead. Split of
  the main thread's frame: without msync render 57 % / other 32 % / logic 11 %; with msync render
  65 % / other 18 % / logic 17 %. Logic ran 3.84 steps/s instead of 5 in the first run (the game
  slows down in big battles, not just the frame rate). Made the default in the play scripts.
- **What is left on the render thread** (eipsample on the bench, heavy scene, fixes 0001–0010,
  6,771 samples of the CS thread): opengl32 65 % (i.e. host driver time), wined3d 25 % (spread
  thin, top function 2 %), the 32→64 stub 7 %. By GL call: glDrawElementsInstancedBaseVertex
  27.7 % (Apple's per-draw validation/encoding, ~3 µs a draw), wglGetPixelFormat 5.6 %,
  glUniformMatrix4fv 4.8 %, glBindBufferBase 4.1 %, glUniform4fv 3.1 %, glVertexAttribPointer 2.2 %,
  glVertexAttribDivisor 2.2 %, glUseProgram 1.8 %. The pixel-format query ran on every context
  acquire (per draw) and the divisor was re-sent for every attribute on every stream load; patch
  0011 checks the format once per present and caches divisors per VAO:
  heavy scene 34.0 → 30.4–30.8 ms (29.4 → 32.4–32.8 FPS, two interleaved rounds); d3d9 visual
  262 failures, identical list; image checksums unchanged.

## 9. Crashes seen during measurement

13 of 15 RotWK dumps since 2026-09-23 fault at `lotrbfme2ep1.exe+0x1385BD` (read of an unmapped
`0x7xxxF708`), on the main thread: a long-standing game crash, not caused by the tools. One dump
(09:29:33) faulted at `+0x76D9E2` (write of 0) in the same second eipsample started suspending
threads; the thread-suspending profiler is no longer used during play.

## 10. Game-side patch (`gamepatch/`, 2026-09-24): built and tested standalone, not yet run in the game

A proxy `dinput8.dll` in the RotWK folder (the exe imports `DirectInput8Create` statically, so it
loads before WinMain; `play-rotwk.sh` adds `dinput8=n,b` because Wine prefers its builtin) patches
the running game in memory; the exe on disk is untouched, so `exeCRC` (computed from the file) and
unpatched peers are unaffected. Each patch checks the exact original bytes (or an FNV-1a hash of a
whole function it replaces) and is skipped if they differ; `gamepatch.ini` / `GAMEPATCH_<NAME>=0`
switch patches on/off (all on except `limiter`); the log (`logs/gamepatch.log`) lists every site with its old and new bytes.
Install / revert / tests: `scripts/game-patch.sh [--revert|--test]`.

The exe was built with whole-program optimisation, so callers may keep values in registers a
callee is known not to touch; every replacement preserves exactly the registers its original
preserves (`t_regs`). "Bit-exact" below is against the game's FPU mode: `0x440809` does
`_fpreset(); _controlfp(_PC_24 | _RC_NEAR, _MCW_PC | _MCW_RC)`. At 24-bit precision every x87
operation rounds its exact result to a 24-bit significand with an extended exponent, i.e. IEEE
single rounding whenever the result is a normal float, so the same operations in SSE single give
the same bits unless a result overflows or is an inexact denormal. The SSE paths run only in that
mode (x87 CW & 0xf3f == 0x3f, MXCSR default) and fall back to the original x87 code otherwise.

| patch | site(s) | what | proof (logs/gamepatch/) |
|---|---|---|---|
| dxlock | 4 calls at 0x51eecb, 0x51ef5c, 0x520920, 0x525291 (`call [WaitForSingleObject]` / `[ReleaseMutex]` → `call stub; nop`) | the DX lock's recursive Win32 mutex (0xdd1fd8) becomes a process-local CRITICAL_SECTION; the game's own CS 0xdd1f80 and owner/count words work as before. Waits with a timeout poll TryEnter (20 s acquire, the movie thread's 1 ms try at 0x65cd0c); release by a non-owner returns FALSE like ReleaseMutex | `t_dxlock`: the game's own lock functions run at their addresses before/after patching; 9 scenarios (recursion, 8-thread exclusion stress, try while held, try waiting for a release, non-owner release, release without acquire, the 20 s timeout path, no handle yet) give identical transcripts, with and without `WINEMSYNC=1`. One known difference: a thread that exits holding the lock (never happens in the code) abandons a mutex but not a CS |
| invsqrt | 0x441c56 `mov eax,imm` → `jmp` | fast inverse sqrt (3 Newton steps, 219 callers) in SSE for x in [2^-126, 2^124] | `t_invsqrt`: all 2^32 inputs, 80-bit st0 compared: 0 mismatches (unguarded SSE differs only for negative, NaN and x ≥ 0x7e6ecbbc); 7 other FPU modes fall back, 0 mismatches. 361 → 29 ns per call |
| normtail | 0x4f1710 (32 B), 0xb2b875 (34 B) | the x87 `v[i] *= invsqrt(len²)` after the two hottest callers (triangle normal 0x4f1613, quaternion nlerp 0xb2b720) | `t_invsqrt` [4]: 8 M random vectors incl. specials, 0 mismatches, no x87 stack leak |
| hittest | 0xb0dfe0 → `jmp` | APT button hit test (every triangle of every button shape every frame) in SSE + exact per-triangle Y reject + conservative shape bounding box (2^-12 margin vs a < 2^-19 rounding error) | `t_hittest`: 30 M synthetic shapes (UI-like transforms, points on vertices and edges, degenerate triangles, wide and special floats), 9.7 M hits, 0 mismatches; 20-triangle button 18.5 µs → 0.18 µs per call |
| quatmat | 0xb26100 → `jmp` | quaternion → matrix (animation) in SSE | `t_quat`: 20 M quaternions (unit, wide, specials), 12 floats compared, 0 mismatches; 1132 → 51 ns |
| shutdown | 0x5385b5 `call [ecx+8]` → `call safe_release` | the exit crash (13 of 15 dumps, §9): static texture wrappers Release after `DX8Wrapper::Shutdown` FreeLibrary'd D3D9.DLL. While the game's D3D9 handle (0xdd3610) is set this is exactly `p->Release()`; afterwards the Release is skipped if the vtable is in no loaded module | `t_misc` [3] with a really unloaded DLL; to be seen on a real exit |
| limiter (**off by default**) | 0x63a1dc-0x63a1f4 | the `Sleep(0)`+`timeGetTime` spin: Sleep(1) while > 2 ms remain (the margin widens after a slow Sleep), the same exit test on `timeGetTime` | `t_misc` [4]: waiting CPU ~95 % → 8-45 %, exit at target+0 in almost every frame, but in one run 2 of 1050 frames ended 5 and 22 ms late (a Sleep(1) woke up late; the original, never sleeping, had none). Standalone console process on a loaded machine, so possibly worse than in game; enable with `limiter=1` and judge in game |
| floor | IAT 0xbd0580/0xbd0588 | msvcr71 floor/ceil (417 + 145 call sites) → SSE4.1 `roundsd` for normal finite inputs | `t_misc` [2]: 6 M inputs, 0 mismatches (floor is exact, so any correct CRT agrees) |

Where the main-thread time of `logs/battle-msync2` sits, and what was not replaced:
- exe+0x41c00 (21 %) is the inverse sqrt itself (hot IPs 0x441c7b..0x441ca5, no loop around it).
- 0xf1700 (6.4 %) is the x87 tail of 0x4f1613 (face normal), called per face by
  buildPolygonNormals 0x4f21b2 from the shadow-volume code updateMeshVolume 0x4f28e9 (also
  buildSilhouette 0x4f2614, 0xf2600); 0xef800 (2.9 %) is 0x4ef790 = constructVolume (only caller
  0x4f33f2 in updateMeshVolume), whose silhouette edge chaining is a linear search over a 16-bit
  index list. (An earlier version of this line called 0x4f28e9 "projected-decal code" and
  0x4ef790 a "polygon clip"; both are stencil shadow volume code, see §10.2. Replaced by edgemap.)
- 0x72b800 (0xb2b720, quaternion nlerp: tail patched), 0x726100 (quatmat), 0x72bd00 (0xb2bd10,
  matrix → quaternion: x87 `fsqrt` with double constants, branchy; not replaced).
- 0x63ae00 (0xa3ae50: distance to a circle via two virtual calls + x87 `fsqrt`), 0x1b1c00
  (0x5b1c00: animation channel decompression, integer/SSE), 0x2e8d00 / 0x2f9e00 / 0x6a600
  (pathfinding and terrain lookups around `floor`: floor patched), 0x19bc00 (bounding sphere via a
  virtual call + `fsqrt`), 0x6d1900 (APT keyframe scans), 0x63cf00 (`_ftol2`): mixed or not pure
  math; listed only.
- msvcr71.dll+0x7054 (1.4 %) is the `fsqrt` inside Wine's builtin `sqrt`. Not replaced: Wine's
  builtin msvcr71 (loaded instead of the game's own copy) rounds `sqrt` to the x87 precision
  (24-bit), Microsoft's msvcr71 on Windows may use SSE2 there, so matching "the unpatched game"
  would mean different code per platform. (Same observation for Mac ↔ PC multiplayer: if Microsoft's
  CRT math differs from Wine's, sqrt/sin/cos results can differ between a Mac and a PC; unverified.)

### 10.1 Render-side patches (second batch, 2026-09-24): standalone-tested, not yet run in the game

Code: `gamepatch/src/p_perf.c/.S`, `p_particle.c/.S`, `p_anim.c/.S` (declarations `gp_render.h`);
tests `t_perf`, `t_particle`, `t_anim`, `t_adecode` (run by `scripts/game-patch.sh --test`). The
animation tests run the game's own `.text` at its address + offset with `.rdata`/`.data` at their
own addresses, original bytes in one copy and patched bytes (applied by the same installer as in
the game) in another.

| patch | site(s) | what | proof (logs/gamepatch/) |
|---|---|---|---|
| perfmarker | 0x517690 head → `jmp`; name-building blocks at 0x543170, 0x5432b0 (MeshDX8Render), 0x573d3a, 0x573dc6 (MeshFXShader) → `jmp` | while the D3DPERF pointer 0xdd361c is null (always, unless PIX or passtimers), PerfTimer begin returns `this` at once and the four per-draw callers skip building the marker name (string copies; `sprintf` per multi-pass FX batch). Nothing reads those stack buffers then; registers the blocks change are dead at the resume points | `t_perf` [1]: begin with every name/suffix/pointer combination: with a pointer identical (registers, object bytes, events), without it returns `this`, keeps every register the original keeps; [3]: each block run from entry to resume point: with a pointer identical (registers, stack, events), without it writes nothing and leaves esp as the original. Per draw 60-70 ns (DX8, FX single pass) and 160 ns (FX multi-pass, sprintf) → 6-8 ns, the begin marker alone 37 → 2 ns |
| passtimers (**off**, diagnostic) | data 0xdd361c/0xdd3620 | D3DPERF-compatible Begin/End: inclusive/self ms and calls per pass per frame (frame = top-level "RenderViews"; mesh draws bucketed by the text before the last tab), logged every 5 s. Markers run while it is on (perfmarker's early return is then inactive) | `t_perf` [2]: 10 scripted frames through the game's marker code: frames, calls, one bucket for 20 per-mesh names, incl ≥ self ≥ sleeps, other threads ignored |
| animdedup | 0x5a4dfc (Render → progress), 0x59cd79 (HLod USOT → Animatable USOT), 0x5a512c (→ single-anim update) | skip re-evaluating a unit's pose (HTree Anim_Update) when it was evaluated at this sync time and nothing it depends on changed: valid, not dirty, no master, last sync = SyncTime, Compute_Current_Frame returns the stored frame/direction bit for bit, a snapshot of transform/anim/frame/HTree header equals the current one, compressed anim with the integer frame below every channel's count. The pose is still copied to all sub-meshes as before | `t_anim`: 5 scripts × 3000 frames of 8 units (moves, animation changes in every mode, bone queries, 1-3 Render passes, direct writes that bypass the valid flag, channels shorter than their animation): arena hashed after every frame, original vs patched identical; ~32 % of Render evaluations skipped (world time 3.2 → 2.7 s). Removing any one condition (count guard, CCF, transform, frame, last sync) makes the test fail |
| animdecode | the 6 from-frame-0 decoder calls 0x5b2131 0x5b2218 0x5b22eb 0x5b2396 0x5b247d 0x5b2550; channel destructor 0x5b18fe (evict) | channel queries without a cache stream (second animation of a blend, HAnim Get_Translation/Get_Orientation) continue from a per-channel cache, exactly as the game's own per-HTree stream does, but only from a cached frame below the channel's frame count and never for frame -1 | `t_adecode` [1]: the premise on the original code (stream vs from-0: 0 differences below the count; past it the game's own stream is path-dependent, 31 k of 87 k differ); [2] 1 M interleaved queries over 600 channels of all six kinds: 0 mismatches, 56 % continued; [3] registers per site and the destructor entry |
| particlevtx | 0x579da0 (5 B) → `jmp` | per-vertex ARGB pack of the point-group vertex loop: `trunc(double(x)·255)` instead of fstcw/fldcw(chop)/4×fmul/fistp/fldcw; exact for |x| ≤ 1 and NaN in every FPU mode (products below 2^24 cannot be rounded across an integer); anything else falls back to the original | `t_particle`: all 2^32 inputs, 136 M random tuples in 48 FPU/MXCSR modes, fallback path: 0 mismatches, every register/xmm/x87 CW compared. 181 → 8.5 ns per vertex |

Not built: R4's per-frame bounding-sphere cache (the second Get_Bounding_Sphere in
renderOneObject never evaluates animation, since the first call left the pose valid; an exact cache
would have to snapshot transform, bone pivots and box, about what recomputing costs).

### 10.2 Shadow volumes: edgemap and shadowpar (2026-09-24): standalone-tested, not yet run in the game

Code: `gamepatch/src/p_edgemap.c`, `par_shadow.c/.h`, `par_shjob.c`, `p_shadow.S`, with the worker
pool `parallel/pool/parallel.c` built into the DLL unchanged; test `t_shadow` (+ `t_shadow_world.c`).
0x4ef790 (§10 "polygon clip", 2.9 % of the main thread in `battle-msync2`) is `constructVolume`,
the shadow-volume builder; the whole stencil-shadow pass is 18–25 % (research R2/R5).

| patch | site(s) | what | proof |
|---|---|---|---|
| edgemap (on) | hash of 0x4ef790+0x45b; entry 0x4ef790 → `jmp`; search 0x4ef8db (13 B) | silhouette edges chained through an index (O(E·k)) into exactly the order the original linear search leaves them in; the original's search then hits on its first compare. Per-thread index buffers; other threads use a linear version with the same result | `t_shadow` [1]: 800 silhouettes from the game's own `buildSilhouette` on 8 RotWK meshes + 3,200 random edge sets: 0 mismatches (volume vertices, indices, silhouette order). Per volume: orc warrior 382 tris 11.9 → 3.6 µs, dire wolf 594 tris 42 → 5.3 µs, CHEST_02 1,794 tris 143 → 10 µs |
| shadowpar (**off**) | hashes of the caster loop, `updateMeshVolume` heavy block, skinning part of `updateVolumes`, `buildPolygonNormals`, `buildSilhouette`, `allocateShadowVolume`, `resetShadowVolume`; writes 0x4f4fe8 (caster loop), 0x4f3301 (heavy block), 0x4f2221 (triangle normals ≥ 1024 tris) | skinning, scratch resizes and volume allocation stay serial in the original order; face normals + silhouette + `constructVolume` become jobs on 7 workers + main (one shadow per chunk, per-thread copies of the skinned vertices, mesh descriptor and neighbour array); shared state (0xdd1868, neighbour flags) set after the join to what the serial game leaves; `RenderVolume` in the original order (caster N now drawn after caster N+1's `Update`, which draws nothing and writes nothing a draw reads). First-appearance meshes and static-VB volumes run inline | `t_shadow` [2]: 160 casters / 10 models / 24 frames through the game's own `updateMeshVolume` and caster-loop bytes: full state and ordered draw record identical to unpatched for edgemap, shadowpar, both, both + verify (7,517 volumes, 0 mismatches), and both with deliberately corrupted workers (verify catches it, restores, switches off). [3] A1: 25 meshes, 18,328 tris, 0 differences. Caster loop incl. serial skinning stand-in 43.6 → 30.4 ms/frame (1.44× vs invsqrt alone, 1.3× vs edgemap alone) |

**First in-game session (2026-09-24 17:06–17:29, UltraHigh, big skirmish): the caster loop
practically never ran** (one `pool of 7 workers` line at 17:07:03, then no verify line and no
900-frame summary in ~22 min). Static analysis of why:
- The per-frame path is the one hooked: RTS3DScene::Flush 0x470f44 ("RenderVolumeShadows", pass mode
  0, scene+0x18 == 0) → W3DShadowManager::renderShadows 0x499d6d (needs TheW3DVolumetricShadowManager
  0xdd1718 and the shadow-scene byte set at 0x47014b) → 0x4f43a6, which reaches the caster loop
  (jmp 0x4f4fe8 at 0x4f4fa3) unless the caster list is empty (0x4f4451), TheGlobalData+0x60
  `UseShadowVolumes` is 0 (0x4f445e) or there is no device (0x4f4467). Update 0x4f3906 has no other
  caller but a vtable thunk (0x4f3be6, `Update(true)`, vtable 0xbe4fa0 slot 1); updateVolumes,
  updateMeshVolume, buildSilhouette and constructVolume each have exactly one caller in that chain.
  So there is no other place for the hook.
- GameLOD's static-level apply (0x601c62, at 0x601d4f) clears `UseShadowVolumes` and
  `UseShadowDecals` whenever `UseShadowMapping` is set, and EA's UltraHigh level sets all three. With
  volumes off, volumetric addShadow returns NULL (0x4f24d2) and renderShadows returns before the loop;
  the frame's shadows come from UpdateShadowMap 0x47d5c9 (called every frame from 0x449df5, works only
  with TheGlobalData+0x62), i.e. two more scene submissions (R4). A display switch (0x6bff7b, via
  W3DDisplay vtable +0x28 = 0x49d565, flag display+0x18) turns mapping off and volumes on while set;
  it is set from menu / game-start transitions (0x91b89c, 0x6b5d59, 0x648ee2, 0x800520, 0x9287aa, a
  script action at 0x7bd775) and cleared by 0x7792bc, 0x6bd0bd, 0x975417. Which game states have it
  set is not determined; `battle-msync2` (also UltraHigh) did build volumes (44 samples at 0x4ef8d5),
  so some path turns volumes on in battle.
- `shadowstats` (on, counters only) logs every 60 s: the three flags, the display switch, shadow-map
  pass calls, renderShadows calls by outcome (reached the loop / no casters / volumes off / no
  device), the caster count, edgemap constructVolume calls and shadowpar loops. `t_shadow` [4] runs
  worlds through the real entry 0x499d6d → 0x4f43a6 (only its camera/terrain calls and D3D
  render-state blocks stubbed): identical to the direct loop with and without edgemap + shadowpar,
  one loop per frame, and no loop for each of the three early-outs.

In-game self-check: for the first `shadowpar_verify` (300) frames with volumes every block is built
the original way and by its job, compared byte for byte; a mismatch or worker fault restores the
reference and switches shadowpar off for the session (logged). Summary every 900 frames with a
serial sample frame every 150. Expected: edgemap removes most of the 2.9 %; shadowpar a plausible
5–10 % of main-thread time in battles. Costs: 7 spinning workers compete with Wine's render thread;
~10 MB job queue; verify frames ~2× shadow time.

## 11. d3dx9 effects (main thread): preshaders

**Where.** In the big-battle main-thread profile (`logs/battle-msync2/eipsample-main.txt`)
`d3dx9_27.dll` is 7.9 % of the leaf samples. The biggest listed regions are the preshader
interpreter: `execute_preshader`/`exec_get_arg` 1.55 %, `regstore_get_double`/`regstore_set_data`
1.36 %. Two smaller regions (+0x5f200 1.06 %, +0x61200 0.49 %) hold `get_relevant_argb_components` /
`make_argb_color`: runtime pixel-format conversion (`D3DXLoadSurface*`), not effects. At UltraHigh
every FX batch runs twice a frame (shadow-map pass `UpdateShadowMap` 0x47d5c9, then the main view).

**How the game drives effects** (static analysis of lotrbfme2ep1.exe 2.02, `build/rotwk-re`):
- Load: `D3DXCreateEffect` (flags 0, no pool) at 0x551356 / 0x5513a3. The game walks every parameter
  (`GetParameter(NULL, i)` + `GetParameterDesc`, 0x55143f). 0x54f406 matches SAS bind names (Camera,
  Time, lights, Shadow, Skeleton, WorldToView, Projection, ...) to setter functors that keep the
  *handle*. Material constants are recorded once into a parameter block (`BeginParameterBlock`,
  `GetParameterByName`, `IsParameterUsed`, `Set*`, `EndParameterBlock`, 0x551f8f). The shadow
  technique comes from `GetTechniqueByName("_CreateShadowMap")`. Names are used at load only.
- Per batch (FX flush 0x573beb, shader wrapper vtable 0xbe9b84, Begin wrapper 0x5517e6):
  `SetTechnique(handle)`, `ApplyParameterBlock`, `SetTexture` per material texture, every setter of
  all six update lists (0x552bd0 with 0xffff: `SetMatrix`/`SetMatrixTranspose` 0x54ce79/0x54cdca,
  `SetVector`, `SetFloat`, `SetInt`, `SetRawValue` for bones and lights), then `Begin(&passes, 6)`.
- Per pass: `BeginPass(i)` (0x551654). Per mesh: the per-object list again (0x55165e, list 1 from
  0x54aae7), then `CommitChanges()` (0x551698), then the draw. Then `EndPass`, `End` (0x5516c1/0x5516e7).

Wine marks a parameter dirty on every set, even to the value it already has, so every `BeginPass`
and every `CommitChanges` ran the vertex-shader preshaders again (defaultw3d.fxo: ~70 instructions
over camera, light, fog, material and per-object inputs). Each component of each instruction went
through a generic interpreter (`exec_get_arg` → `regstore_get_double` → function pointer →
`regstore_set_double`). In `tools/d3dx9fxbench.c`, which replays the pattern above on the real `.fxo`
files, that interpreter was ~70 % of d3dx9's time.

**Fixes** (`patches/d3dx9-setrawvalue/0005–0007`, Wine branch `d3dx9-perf` = perf-try + 3):

| patch | what | exact because |
|---|---|---|
| 0005 | preshader instructions with directly addressed float/double operands get register pointers once; loop with add/mul/neg/rcp/lt/ge/cmp/mov inlined | same registers, same order, same double operations |
| 0006 | each preshader keeps a copy of its input registers: no change, no run; otherwise only the instructions depending on changed registers run, plus the writers of the values they read and the last writer of each output they write | only used when a preshader never reads a temp or output before writing it (it is then a pure function of its inputs); not for relative addressing outside the constant table, tx_1 inputs, failing instructions, or outputs sharing registers with parameter constants |
| 0007 | handle checks compare the 4 magic bytes inline instead of calling `strncmp()` | same bytes read, stopping at the first difference |

`WINE_D3DX9_FXOPT` (bit mask, default all): `0` = old code paths, `1` = only 0005, `2` = only 0006, `4` = only 0008 (CommitChanges skips constant states that cannot set anything; exact because without update_all those states are reported clean and return D3D_OK without a device call).

**Results** (bench: defaultw3d + normalmapped + terrain, 300 batches × up to 3 meshes, shadow pass +
main view, `--mode dev`, median of 5 × 4 s):

| | frame | BeginPass | CommitChanges | per-batch setters |
|---|---|---|---|---|
| before | 10.93 ms | 9.52 µs | 2.94 µs | 0.51 µs |
| `FXOPT=1` (0005 + 0007) | 3.57 ms | 2.24 µs | 0.80 µs | |
| `FXOPT=2` (0006 + 0007) | 5.40 ms | 4.30 µs | 1.24 µs | |
| 0005–0007 | 3.28 ms | 2.04 µs | 0.69 µs | 0.45 µs |

**Gates.** The device calls the effects issue (every render/sampler/texture-stage state,
texture, shader, shader constant with its data, transform, light, material, FVF, plus every
BeginPass/CommitChanges result), hashed through an `ID3DXEffectStateManager`, are identical to the
unpatched build for 5 scenes including all 13 game effects with all techniques, and for
`WINE_D3DX9_FXOPT` 1, 2 and 3. A deliberately broken build changes the hash. Wine's d3dx9_36
`effect` tests: 233,887 tests, 0 failures, 26 todo, the same as before (also with FXOPT 1 and 2).

**Not done: these would change the device call stream.** Skipping re-uploads of unchanged
constants and states on BeginPass/CommitChanges, and honouring `D3DXFX_DONOTSAVESHADERSTATE |
D3DXFX_DONOTSAVESAMPLERSTATE` (the game's `Begin` flags). Wine captures and restores a full state
block per batch anyway, but it costs only ~0.35 µs per batch in the bench.

### 10.3 The shadow-map pass (UltraHigh): what it does per object, and what can be cut exactly (2026-09-24, static)

UpdateShadowMap 0x47d5c9 (render helper 0x449df5, before RenderViews) pushes a material pass
(vtable 0xbdcb44: at Begin it swaps the mesh effect's technique for its `_CreateShadowMap` one,
0x47b1bb → 0x550e14) onto a RenderInfo, sets byte 0xdd1e44 and calls WW3D::Render 0x517c60
(0x47d70c) with the light camera; scene pass mode (+0x7ec) stays 0. Per object:

- **Visibility_Check** 0x470b83 (via 0x46fee3): grid query 0x541f90, per candidate Get_Bounding_Sphere
  vt+0x104 (HLod 0x59ac20: BOUNDINGBOX bone → Get_Bone_Transform 0x5a51b0 → USOT vt+0xa8 when the pose
  is invalid), Cull_Sphere 0x535420, Set_Visible, occluder/translucent classification. The shadow pass
  is the first render of the frame, so it evaluates the pose of every moved unit in its grid cells
  (animation that RenderViews would otherwise pay; inferred, counted now).
- Customized_Render 0x46fe84: the UpdateList loop is skipped (0x46ff40), terrain renders, then
  **renderOneObject** 0x46f48e for every visible object: LightEnvironment ctor 0x53eef0 on the stack,
  Get_Bounding_Sphere again, drawable state (0x67055a, shroud 0x68d8f7, tint 0x670a06/0x672f9a/0x672faf,
  0x67ddd3), Reset 0x53f100, global lights with a temporarily changed diffuse (writes light+0xe0 and
  restores it, 0x46f93d/0x46f979), scene point lights (sphere test 0x46e93d) and dynamic lights via
  Add_Light 0x540250, Pre_Render_Update 0x540500 with the light camera, material passes, then
  robj->Render → HLod 0x59c080 → Mesh::Render 0x54b500: frustum test, Set_Lighting_Environment
  0x54b490 (copy into mesh+0xcc), FX list insert 0x57430d. Non-FX meshes return at 0x54b773.
- Flush 0x470f44 (mode-0 blocks): DX8 + FX flush 0x516d80, occluded objects into stencil 0x470176,
  water, decal shadows (0x50d92c returns at 0x50d958 in this pass), tree light environment + trees,
  volume shadows (off at UltraHigh), static sort lists, translucent 0x4708b5/0x470a0b, particles
  (manager armed again at 0x47016c; every draw module except RenderObject returns 0 when 0xdd1e44 is
  set: 0x961e09 0x9624c9 0x962a41 0x963491 0x963db0 0x9658c7), smudges. Then WW3D::Render's FX flush
  0x574406: 0x524de0(1) (lights to D3D suspended), rigid / CPU-skinned / GPU-skinned lists, per batch
  0x54a080 → Set_Light_Environment 0x5228a0 (stores the environment pointer 0xdd3454), effect
  parameter binders per mesh (registered by parameter name at 0x54f406: NumAmbientLights 0x54cef6,
  NumDirectionalLights 0x54cfad, NumPointLights 0x54d112, AmbientLight, DirectionalLight, PointLight,
  Shadow...), draws; at the end 0x524de0(0) applies the last environment to D3D (AMBIENT render state
  0x8b and the lights, 0x5228a0 with 0xdd3460 clear).

What is dead or redundant (verified statically unless marked):
- The light environment is **not** dead in this pass: it is copied into every FX mesh, read by the
  light-parameter binders (effect calls in this pass) and, for the last batch, applied to D3D at the
  end of the flush (0x574440 → 0x524ded → 0x5228a0), which also primes the render-state cache the
  main pass filters against. Skipping or approximating it changes the effect call stream and the D3D
  stream. Rejected.
- Decal shadows, terrain extras and volume shadows skip themselves in this pass (the checks above).
  Particles do **not** reduce to "one virtual call per system": the RenderObject draw module and the
  sorting-renderer flush under the same marker do real work here, and neither is dead (§10.4; an
  earlier version of this line said "nothing worth cutting").
- CPU skinning twice (shadow + main) could be reused exactly (full input snapshot), but FX meshes are
  skinned on the CPU only when the effect has no `MaxSkinningBones` or the mesh uses more bones
  (0x58c05a at 0x58c118/0x58c1a6); RotWK's Shaders.big gives defaultw3d.fxo 90 and normalmapped.fxo 32,
  so such meshes should be rare (confirm: renderstats "CPU skinning per frame" line). Not built.
- Bounding spheres (4 per object per frame) and light environments (2) are recomputed from the same
  inputs, but an exact validity check costs about what the recomputation costs (§10.1), and the light
  environment has ~15 inputs behind virtual calls. Not built.
- Parallel light environments (R4 design B): the common "tint" path writes the shared global lights
  (above), Get_Position may validate containers, the tint getters write drawable caches (0x671c0c);
  it needs a rewritten tint path plus an audit of every call; its gain is bounded by the
  renderOneObject time now logged. Parallel pose evaluation before UpdateShadowMap is the larger
  lever if the shadow pass's Visibility_Check time is mostly animation.

Measurement (renderstats, on): every 60 s, per frame, main passes | shadow-map pass: ms in
WW3D::Render, Customized_Render, Visibility_Check, renderOneObject (and objects), Flush and the FX
flushes (time stamp counter at 0x47d70c/0x518065, vtable slots 0xbdc3c4/0xbdc3d4, 0x47009f/0x47010c,
0x471a3b, 0x517db2/0x516d91; ticks converted with QueryPerformanceCounter per window), and the HLod
pose evaluations / animdedup skips of each pass (p_anim gp_ad_pass). `t_rstats` [4]: every timed stub
hands the original its registers, xmm0-7 and arguments in order, returns the original's eax, ecx,
edx, xmm0-7 and stack, keeps ebx esi edi ebp, counts one call and a positive time for its kind in the
pass of 0xdd1e44; [5] the extra cost per timed call: 19 ns (~830 a frame, ~0.02 ms).

### 10.4 The RenderParticles pass, main view and shadow map (2026-09-25, static; particlestats)

Measured (passtimers, 09:31:43, 57.6 ms/frame): `UpdateShadowMap/RenderParticles` 5.27 ms self,
`RenderParticles` (main view) 4.63 ms self. What the marker covers (RTS3DScene::Flush,
0x4716c7..0x471708):

- **0x4716ee → 0x44c3ea → W3DFXParticleSystemManager::render 0x44c84a**, called only in scene mode 0
  with scene+0x18 clear, working only when armed (mgr+0xa8, set by Customized_Render at 0x47016c in
  both passes, cleared at 0x44c86e). Simulation is not here: the manager update (0x5f5123, emission,
  per-particle modules, deaths) runs once per frame at 0x449d48, before UpdateShadowMap (0x449df5).
  Per system (std::list mgr+0x4c): a temporary handle (0x44c4be/0x44c4e2), type 6 (terrain) skipped,
  sort-level systems (0xdd1e19) bucketed and drawn after the loop, "SMUD" heat-smudge systems (client
  RNG 0x6d33ab per particle; only with TheGlobalData+0x25 set, inferred to be UseHeatEffects, which the
  group pack turns off),
  else the CAT_DRAW module's vt+0x10, whose return is added to mgr+0x5c. Six modules (default,
  streak, quad, butterfly, lightning, gpu) return 0 at their first test when 0xdd1e44 is set
  (0x961e09 0x9624c9 0x962a41 0x963491 0x963db0 0x9658c7, verified): in the shadow pass no gather, no
  point-group expansion, no vertex loop (0x579da0, particlevtx), no VB lock, no sort insert, no draw.
  The **RenderObject module 0x964c00 has no such test**. For every particle inside the pass camera's
  box (the light camera's in the shadow pass) it builds the transform and calls the particle's render
  object Set_Transform (vt+0x54), sets colour/opacity with 0x50e040 / 0x50e244 / 0x50e413 (per
  sub-mesh: DX lock 0x51eec0, an FX parameter found by name, e.g. "ColorEmissive", and the material
  parameter block recorded again, 0x551f8f; fixed-function meshes: the vertex material 0x53c800) and
  un-hides it (vt+0x194). The tail: mgr vt+0x3c, 0x494117 (returns at once in the shadow pass).
- **0x4716f4 → 0x52ec60 SortingRendererClass::Flush**, unconditional: it draws every sorted
  (alpha-blended) polygon inserted since the pass began (0x52fee0 inserts when sorting 0xd9b034 is on,
  which it always is), not only particles: in the main view also translucent meshes and W3D emitters.
  With nothing queued it still unbinds VB/IB (0x51ce40/0x51ced0) and restores the saved transforms.

Shadow pass, what reaches what:
- Render-object particles are ordinary scene objects (created hidden and added to the scene at
  0x5fbd62/0x5fbd86). The main view culls them (Visibility_Check) and draws them (renderOneObject, FX
  flush 0x516d80) *before* its own RenderParticles, so it uses the transform, colour and visibility
  the shadow pass's RenderParticles wrote (a new particle is un-hidden there first). Skipping the
  module in the shadow pass would draw those particles one frame late or not at all: **not exact**.
- W3D model emitters (ParticleBufferClass::Render 0x5aed50, vtable slot 0xbed2a0) have no shadow
  test; the object loop renders them in the shadow pass too, and their blended point groups
  (0x5798f4) go to the sorting renderer, which the flush above draws into the shadow map (R32F colour
  target 0x47d421 + D24S8, cleared to 1.0) with the particles' own shader: colour writes on, so they
  can change shadow-map texels (inferred; how many there are is what particlestats counts).
- Other state: mgr+0x5c (on-screen count) also gets the shadow pass's RenderObject counts but is
  reset by the main view's RenderTerrainParticles (0x44cd44) before it adds its own and is read only
  by debug displays (0x448659, 0x5f984b); the temporary handles net out; 0xd9b035 is restored.

So no part of the shadow pass's particle work that costs anything is dead. Nothing is patched.
`particlestats` (on, counters only; p_pstats.c/.S, `t_pstats`) times, per pass: the manager render,
the RenderObject module (systems, particles) and its colour setters, the sorting flush (with the
nodes it draws) and emitter renders, and every 16th frame counts systems by draw module kind. Its 60 s
lines say which of the two is the ~5 ms. If it is the colour setters (a parameter block recorded again
per particle mesh per pass with unchanged values), an exact cache there is the next candidate; it
would help both passes and is not a shadow-pass skip.

### 10.5 Game-logic x87 code (2026-09-25, static + standalone tests; not yet run in the game)

What of `logs/battle-msync2` (46 ms frames, 21.7 FPS; `battle-ai1` as a second opinion) is left
outside rendering, shadow volumes and the patches above, by leaf samples of 3297 (256-byte regions;
functions from `build/rotwk-re/funcs.txt`). "Calls/frame" = region time / measured per-call cost of
the original (both standalone under Rosetta), i.e. inferred, and an upper bound where the region
holds other code too.

| rank | region (m2 / ai1 samples) | function | x87 | calls/frame | done |
|---|---|---|---|---|---|
| 1 | 0x1b1c00 (32 / 30) | 0x5b1c00 animation channel decode | 4 of 126 insns, integer | - | not x87; animdecode already cuts calls |
| 2 | 0x72bd00 (28 / 29) | 0xb2bd10 Matrix3D -> quaternion, 21 call sites in 12 functions (HAnim/HTree blending, 0xb27c80) | fsqrt, fdivr, double consts | ~800 | **mat2quat** |
| 3 | 0x2e8d00 (28 / 25) | 0x6e8ce6 world -> pathfinder cell (81 call sites), + its integer wrappers 0x6e8d88/0x6e8dd5 | 24 (<= 14 per call) + 2 floor calls | ~1,800 | **worldcell** |
| 4 | 0x63ae00 (22 / 38) | 0xa3ae50 distance to a bounding circle, 2D (distance-proc table 0xdbdaf8, per candidate of iterateObjects 0xa3bdb0; hot IP right after its fsqrt in ai1) | 21, fsqrt | ~800 | **distcalc** (+ centre 2D 0xa3a7a0) |
| 5 | 0x365900 (19 / -) | 0x7658c3 / 0x765945 path length (octile via CRT fabs; Euclid via CRT sqrt) | 30 + CRT | - | next candidate (fabs part only: CRT sqrt stays, see above) |
| 6 | 0x6d1900 (18 / 11) | 0xad1920 GeometryInfo::getMaxHeightAbovePosition (56 callers), 0xad17e0 calcPointToLineDistSquared tail | 14 / 89 | - | next candidate |
| 7 | 0x06a600 (- / 23) | 0x46a575 terrain height (virtual, 4 floor calls, invsqrt) | 70 | - | next candidate (floor already SSE) |
| 8 | 0x19bc00 (- / 14) | 0x59bc50 bounding sphere from box (virtual) | fsqrt only | <1,000 | **bsphere** |
| 9 | 0x63cf00 (- / 13) | 0xa3cfa4 `_ftol2` (~580 call sites; region shared with the EH prolog 0xa3cef0) | 6 | <3,000 | **ftol2** |
| 10 | 0x2f9e00 (- / 11) | 0x6f9850 pathfinder search step | 43 of 611 | - | mixed, not pure math |

The static scan (x87 instructions per function, direct-call closure of GameLogic::update 0x62e4e8:
8,086 functions) finds denser functions (0xad1d60 117 x87, 0x466c4c 106, 0xad30e0 96, 0x82dfb7 96,
0xad4660/0xad2040/0xad2770 geometry 82-91), but none reaches the top-25 regions of either profile
(so each < ~0.4 %). The logic's remaining time is spread thin: a leaf profile cannot show it better;
an inclusive profile (eipsample stack scan + `tools/callstacks.py --root 0x62e4e8`) of today's battle
is the next measurement.

Patches (code `gamepatch/src/p_logic.c/.S`, `p_ftol2.S`, `gp_logic.h`; tests `t_logic`, `t_ftol2`
with a full-state harness `tests/lm_harness.h`: every general register, xmm0-7 (128 bits), x87 control
word / stack top / tags / all non-empty 80-bit registers, MXCSR control bits, argument slots + two
canaries, output memory with guards, and the order of virtual getter calls; originals read from the
exe at run time; the installers patch a relocated copy with their byte/hash checks). Same scheme as
quatmat: SSE only in the game's FPU mode, MXCSR flags cleared, OE/UE/IE/ZE or a NaN result -> the
original x87 instructions on the same inputs; all on by default.

| patch | site | what | proof | per call |
|---|---|---|---|---|
| mat2quat | hash 0xb2bd10+0x168, `jmp` at 0xb2bd10 | both branches (trace > 0; largest diagonal via the game's own next[] table) in SSE; leaves eax/ecx/edx/xmm0/xmm1 and the float in its matrix-pointer slot exactly as the original | 10 M matrices (rotations, scaled, random, wide, bit patterns, specials, trace near 0/-1, output aliasing the matrix): 0 mismatches, 5.8 % ran x87 | 468/394 -> 49/52 ns |
| distcalc | hashes 0xa3a7a0+0x26, 0xa3ae50+0x53; `jmp` at both | centre 2D and bounding circle 2D in SSE after the same getter calls (same order, same ecx); ecx/edx/xmm left as the last getter leaves them, d2 in the object slot; x87 fallback: the original's d2 instructions, then a jump into its own tail | 10 M inputs each through a mock Object whose getters change ecx/edx/xmm0-1: 0 mismatches (except eax of 0xa3ae50: the FPU status word the original's sign test leaves; only reachable through the table, so no caller reads it) | 144 -> 63, 391 -> 75 ns |
| bsphere | hash 0x59bc50+0x82; 0x59bcb9 `flds/fsqrt/fstps` -> `call` + 4-byte nop | sqrtss | all 2^32 inputs: 0 mismatches; 10 M whole-function calls with a mock box | 175 -> 19 ns (function) |
| worldcell | hash 0x6e8ce6+0xa2; `jmp` at 0x6e8ce6 (8 B) | x*0.1f [+0.5f] -> roundss floor -> cvtss2si; floor(y) float left in the `exact` slot | all 2^32 coordinate values x both flags; 10 M random (cell edges, tiny, huge, specials) with msvcr71 floor and with gp_floor in the IAT: 0 mismatches (edx, and xmm when msvcr71's floor runs, are what that external function leaves) | 168 -> 46 ns |
| ftol2 | hash 0xa3cfa4+0x75; `jmp` at 0xa3cfa4 | `fstp tbyte` + integer emulation of fistp / diff-at-24-bit / correction, ecx included (untouched on the n = 0 / indefinite path, as the original) | all 2^32 floats, 50 M doubles, 50 M 80-bit values (int64s, halves, around 2^63, unnormals, pseudo-denormals, inf/NaN): 0 mismatches; 3 deliberate rounding bugs are each caught by 1 M randoms | 54 -> 3.7 ns |

Other x87 modes (PC_53, PC_64, RC down/up/chop, MXCSR RC down, FTZ+DAZ): every call runs the
original, 0 mismatches. Expected saving from the regions above: mat2quat ~0.35, distcalc ~0.25,
worldcell ~0.2, bsphere and ftol2 up to ~0.15 each: about 1 ms of a 46 ms frame. In-game proof that
they run: the `logicmath:` line every 60 s (calls and x87 runs per entry) and the exit line.

## 12. Per-draw cost of the FX path, and what Flush does besides the FX flush (2026-09-25)

**Scene.** `tools/d3dx9fxbench.c --mode dev --draw 1` now draws: every mesh binds one of 32 vertex/index
buffer pairs (only when it changes, like DX8Wrapper) and draws, the frame ends with Present (no vsync).
`--bones 20,60` sets 20–60 bones per skinned object (SetRawValue of nbones × 32 bytes, as the game's
skeleton setter 0x54d926 does), `--batch-ints 1` keeps the per-object ints (NumJointsPerVertex, ...) the same
within a batch (the game flushes rigid and GPU-skinned meshes as separate lists). defaultw3d + normalmapped +
terrain, 350 batches × 1–8 meshes, shadow pass + main view: 730 BeginPass and 3,237 draws a frame, about the
game's ~700 batches and ~3,000 draws (renderstats). Timed per API call (rdtsc), frame time, and the wait in
Present (= render thread); "busy" = frame − Present = the application thread.

**What one mesh costs on the application thread** (bench, 13:50, load ~5, per-call timers and the share
of each function in a frame-pointer profile, `tools/fpsample.c` + `tools/fpsym.py`; the sampler itself
slows the thread by ~10 %):

| layer | bfme-fixes µs/mesh | + 0008/0020/0021 | what |
|---|---|---|---|
| d3dx9, per-object setters | 0.32 | 0.30 | ~10 Set* calls (world, bones by SetRawValue, point light, ints) |
| d3dx9, CommitChanges itself | 0.43 | 0.37 | walks all ~22 states of the pass (12 constant, 7 FXLC, 2 array selectors, 1 parameter), reruns dirty preshaders; `set_constants` copies each dirty parameter into the register store and uploads it |
| d3d9 + wined3d inside CommitChanges | 0.06 | 0.06 | SetVertexShaderConstantF (mutex, memcpy into the stateblock, changed bits), a few SetRenderState |
| DrawIndexedPrimitive: float-constant push | 0.27 | 0.11 | before: malloc + copy + UPDATE_SUB_RESOURCE op + PUSH_CONSTANTS op per changed range; after: compare with the last push, one op with the changed registers |
| DrawIndexedPrimitive: rest of apply_stateblock | 0.26 | 0.27 | stream source / index buffer, recursive mutex per set call, bitmap scans |
| DrawIndexedPrimitive: CS draw op | 0.13 | 0.12 | queue space + referencing every bound resource |
| DrawIndexedPrimitive: managed textures | 0.07 | 0.07 | `wined3d_device_update_texture()` checks per bound managed texture |
| DrawIndexedPrimitive: mutex, bitmaps, misc | 0.19 | 0.18 | |
| bind VB/IB | 0.09 | 0.08 | SetStreamSource + SetIndices when they change |
| **total** | **1.83** | **1.56** | the game's "Rendering mesh FXShader" self time is 1.8–2.5 µs incl. its own setter code |

Per batch another ~3.3 µs (BeginPass 2.2: every state and every constant of both shaders set again;
batch parameters 0.5; End 0.25 with the stateblock restore; ApplyParameterBlock 0.2; Begin 0.1).
No WoW64/unix call is on this path on the application thread (only the CS thread calls into GL).

CommitChanges uploads a whole constant table entry whenever its parameter was set: a GPU-skinned mesh sends
the 90-bone palette (180 registers, 2.9 KB) however many bones it has (d3dx9fxbench: 215,000 VS constant
registers a frame, 3.4 MB). wined3d then pushed every one of them to the CS, which copied them into the push
constant buffer, re-versioned each in the GLSL constant heap and re-sent them with glUniform4fv.

**Render thread** (same scene): 60–66 % inside opengl32 (driver), `walk_constant_heap` 4.7 % +
`update_heap_entry` 3.4 % before the fixes, 2.0 % + 1.5 % after.

**Fixes**

| patch | what | exact because |
|---|---|---|
| wined3d 0020 | `wined3d_device_apply_stateblock()` keeps a copy of the float constants it last pushed and pushes only registers whose bits changed (runs closer than 5 registers merged). `WINED3D_CONST_FILTER=0` = off | the push constant buffer already holds the skipped bits, and each register it holds was marked changed in the GLSL constant heap when those bits were written, so every program either loaded them since or reloads them (version > program version); the copy is invalidated whenever the push constant buffers are released (device reset / uninit). The D3D call stream is untouched |
| wined3d 0021 | a push of constants carries its data inside the PUSH_CONSTANTS op (one op, no heap copy, no upload bookkeeping, no free() on the CS thread) when the push constant buffer is CPU memory. `WINED3D_INLINE_PUSH_CONSTANTS=0` = off | the CS writes the same bytes to the same buffer with the same function, in the same queue order, before marking the same registers |
| d3dx9 0008 | CommitChanges leaves out constant states that are not shaders or samplers; `d3dx_fxopt()` reads `WINE_D3DX9_FXOPT` once (the default, all bits set, used to look like "not read yet" and cost a getenv() per call; only load-time callers existed so far). `WINE_D3DX9_FXOPT` bit 0x4 | without update_all such a state is reported clean by `d3dx9_get_param_value_ptr()` and `d3dx9_apply_state()` returns D3D_OK for it without a device call |

**Gates.** d3dx9fxbench `--hash` (every device call the effects make, through a state manager): identical to
the bfme-fixes build in 6 scenes (incl. all 13 game effects with all techniques, 1–90 bones, shared
palettes) and with `WINE_D3DX9_FXOPT` 0, 3, 4 and unset; the new bench gives the old bench's hash for the old
arguments. Image checksums (d3dx9fxbench `--crc`, the effect scene actually drawn and read back every
frame, 6 scenes, 4 frames each): identical to the bfme-fixes build, also with each switch off. Wine's
d3dx9_36 `effect` tests: 233,887 tests, 0 failures, 26 todo, unchanged (FXOPT unset and 0). d3d9 `visual`: 262
failures, identical list; `stateblock`: 14,738 tests, 0 failures. d3d9bench `--crc`: 68fe2221, 64abfac0,
5eb28a61 and five more scenes unchanged.

One trap met on the way, kept in the bench: with bone indices ≥ 2 the skinning shaders read past their
constant array. That is undefined, and on this driver the pixels then depend on which uniforms were
re-sent before the draw (a bfme-fixes build, a build with every uniform re-sent before every draw, and one
with 0020 gave three different images; glGetUniformfv showed the right values in all of them). `--crc`
uses indices 0 and 1, where all builds agree. The game's meshes index bones they have, inside the palette
d3dx9 uploads (inferred).

**Results** (bench, `--batch-ints 1`; other sessions' 12–14-core tests came and went, so each line is a
median of interleaved runs and the rounds with load > 10 are the noisy ones):

| run | build | frame | render thread (Present wait) | application thread | CommitChanges | DrawIndexed |
|---|---|---|---|---|---|---|
| 13:20, 5 rounds, load 7 | bfme-fixes | 16.92 ms | 8.16 ms | 8.63 ms | | |
| | + 0008, 0020, 0021 | 13.96 ms | 6.14 ms | 7.88 ms | | |
| | same, all three switched off | 16.91 ms | 8.15 ms | 8.74 ms | | |
| 13:50, profiler attached, load 5 | bfme-fixes (2 runs) | 15.86 / 15.90 ms | 7.00 / 7.07 ms | 8.86 / 8.83 ms | 0.49 / 0.50 µs | 0.93 / 0.92 µs |
| | + 0008, 0020, 0021 | 12.97 ms | 5.10 ms | 7.87 ms | 0.43 µs | 0.75 µs |
| 11:55–12:10, one patch at a time, load ~5 | 0020 alone | 14.44 → 12.02 ms | −2.4 ms | ±0 (7.74 → 7.78) | | |
| | + 0021 | | | 7.65 → 7.25 ms | 0.45 µs | 0.77 → 0.65 µs |
| | + 0008 | | | 7.38 → 7.15 ms | 0.46 → 0.39 µs | |

d3d9bench (WW3D's own vs_1_1 path, which re-sets changed matrices for every object): default scene
23.0 → 21.9 ms, heavy scene unchanged within the noise (35.0 / 35.2 ms).

**Expected in the game:** 0.2–0.27 µs less per FX mesh on the game thread (DrawIndexedPrimitive −0.12
to −0.18, CommitChanges −0.06) and ~0.1 µs per BeginPass: with ~3,000 meshes and ~700 batches a frame,
~0.6–0.8 ms of a 55–63 ms battle frame (inferred from the bench; the game's own per-mesh setter code is
not touched). The render thread saves ~2–3 ms a frame (constant heap, uploads, the second copy), which
shows only while the render thread is the limit.

**The ~5 ms per pass of Flush outside the FX flush** (static analysis): Visibility_Check 0x470b83 puts every
visible object with a drawable into one of three scene lists (occluders +0x7fc/+0x808 flag 0x2, potential
occludees by player +0x800/+0x80c flag 0x4, the rest +0x804/+0x810 flag 0x10; caps from TheGlobalData+0x978..
+0x980), and Customized_Render's object loop skips everything with those flags (0x47008a, `test $0x1e`).
Those objects are rendered by 0x470176, called from RTS3DScene::Flush at 0x470f7c whenever the scene pass mode
is 0 (the shadow-map pass included): per player bucket stencil render states, then renderOneObject for each
object (0x4704cb/0x4704f3 occludees, 0x4705c4/0x4705eb occluders, 0x4706c7/0x4706f0 the rest), with an FX
flush around each object that carries per-player stencil bits and after each list. So nearly every unit and
building's renderOneObject (light environment, bounding sphere, drawable state, HLod → Mesh::Render queuing)
runs inside Flush, and renderstats' renderOneObject timers (0x47009f/0x47010c) see only the 20–100 objects
without drawable flags. At the 6–7 µs per object those timers measure, 5 ms is ~750–850 objects per pass.
It is game code per object, not per draw; the draws it queues are the FX flush's. To confirm in the game:
time the call at 0x470f7c and count renderOneObject from its six call sites (renderstats).


## Selectable Dwarven builder art prototype — 2026-09-26

Build: `26bf6c1` plus uncommitted `assets/dwarves/porter/` recipe, original helmet retained.
Scene: static complete `DUPorter_SKN`, all mesh parts counted, HD Edition source versus
review prototype; no game session, timing or FPS measurement. Source model SHA-256:
`af7b8eeb0ab43b7447e3238208474fef4bc583aac005bae99b740858e212e62b`.

| Static asset cost | HD source | Review prototype |
|---|---:|---:|
| Vertices | 2,496 | 17,939 |
| Triangles | 2,362 | 8,980 |
| Model file bytes | 221,497 | 1,079,349 |
| Three body/cart diffuse DDS files, bytes | 262,608 | 4,194,744 |

The private DDS atlases duplicate material pixels under separate texture names and retain
original shared sheets for the unchanged helmet and bucket; the texture row excludes those
retained sheets. This prototype adds geometry and texture cost. Runtime cost is unmeasured
and must be checked before shipping; these counts are not a performance improvement claim.


## Elven citadel-style rollout completion — 2026-09-26

Build: `1385bd4` plus the uncommitted completion pass. Scene: offline EA-versus-redesign
Blender views, including construction, damage, rubble and available night states. No game run,
FPS measurement or runtime improvement claim. Older prototype measurements above remain historical.

The final recipes retain EA bodies and add the approved ivory/mithril/mallorn-gold details.
The palette pass rebuilt 63 ownership-approved shared sheets. The recipe texture-budget
estimate is 216.7 MB against its 256 MB limit (`sagekit budget elves`); this counts own recipe
textures and alpha allowances, not total installed textures, geometry or measured GPU memory.

| Group | Final offline checks passed / total |
|---|---|
| Approved citadel | Citadel: 114/114 |
| Citadel additions | Eagle’s Nest: 86/86; Enchanted Anvil: 90/90; Mystic Fountains: 97/97; Crystal Moat: 43/43 |
| Fortress expansions | Floodgate: 113/113; Floodgate doors: 74/74; Vigilant Ent: 92/92; Watchtower: 92/92 |
| Walls | Wall segment: 84/84; Wall hub: 86/86; Wall gate: 115/115; Wall end: 79/79; Fortress wall hub: 88/88 |
| Production | Barracks: 169/169; Forge: 130/130; Green Pasture: 163/163; Green Pasture with fence: 159/159 |
| Special buildings | Battle tower: 111/111; Mallorn tree: 105/105; Mirror of Galadriel: 63/63; Statue: 60/60; Ent moot: 75/75 |

Total: **2288/2288 passing checks across 23 recipes**, including the approved citadel.
These gates cover the actual shipped model set, not a claim that every EA state was replaced.

Construction/collapse corrections preserve existing gate thresholds: rest-pose matching for
the wall hubs, internal-cap classification for the floodgate, the doors’ original model-space
offset, closed added surfaces for the pasture, fountains and Eagle’s Nest, and optional-source
colour-channel mapping for forge construction. The door-offset regression and W3D layout
regression pass. No rejected lifecycle model is forced into the package.

Retained EA bodies: barracks D2/D3; forge D1/D2/D3; crystal moat D1/D2/D3; Mallorn D2;
mirror D1/D2/D3; statue construction. Mallorn lacks a required non-neutral vertex-colour channel.
Statue matching probes still failed the unchanged open-back gate, so the previous fallback
remains. The fortress hub uses the regular wall hub’s completed construction output.

Integration evidence: installer synthetic checks cover duplicate cache records, preservation of
unrelated art, repeat installation, guarded revert, interrupted-write rollback and stale staging.
The real Elven archive/cache preparation is staged only; installed Dwarven building/builder
archives and both live asset caches remain byte-identical to their pre-completion snapshots.
Current review artifacts: `build/assets/elves/review/`; state details: `assets/elves/ROLLOUT.md`.


## Selectable Elven builder review — 2026-09-26

Build: `1385bd4` plus uncommitted `assets/elves/porter/`. Scene: original HD Edition
`EUPorter_SKN` versus the Elven craftsman, offline paired diffuse-material renders.
The original face/hair/anatomy, held tools, skeleton and shared animation bytes are retained.
No game session, timing or FPS measurement. Source model SHA-256:
`aa03bb943f1c2de458b2adac765b71ef237fc0086bd22bb5cfae24c11fba869b`.

| Static asset cost | Source | Review model |
|---|---:|---:|
| Vertices | 1,849 | 16,186 |
| Triangles | 1,722 | 7,544 |
| Model bytes | 138,257 | 955,389 |

The private diffuse DDS adds 1,398,248 file bytes; the private RGBA house-mask TGA adds
8,388,626 file bytes. These are disk sizes, not measured GPU memory. Retained shared
textures remain unchanged and are excluded from those additional-file counts. Geometry and
texture cost increase; runtime cost is unmeasured.

The atlas is 2048×1024. Its left half repeats the original 256×256 body/mask four times
each way, matching the affine UV remap; new material swatches occupy the right half.
An initial ImageMagick tile composite erased RGB beneath transparent mask pixels. It was
replaced with raw RGBA row repetition, and the check now verifies exact source-mask bytes
and transparent-white neutral pixels throughout the added-material region.

Eight paired views cover portrait, RTS, run, walk, water, fidget and both deaths; the seven
actual INI animation files are decoded with OpenSAGE, with finite transforms checked at every
frame. A header-only audit wrongly inferred that crushed death hides the cart; the actual
motion visibility channels override legacy keys and show it. No game-animation data changed.

Structural checks, exact mask mapping, deterministic cache staging, archive read-back, active
rig-change rejection and per-file harness checks pass. The Elven builder and its new
house-colour mapping are staged only. Existing Dwarven archives and both live asset caches
remain byte-identical to the earlier rollout snapshot.

Related existing issue found during this audit: the installed Dwarven builder's private
`ducrafts*` textures lack house-colour mappings/masks. It was not repaired or reinstalled
in the Elven builder task; the earlier builder entry's unverified player-colour limitation
therefore remains open.


## Reviewed faction pair installation — 2026-09-26

Build: `1385bd4` plus the uncommitted Elven completion, builder recipes and Dwarven colour
repair. Scene: installed-file and cache inspection only; the player requested installation
after reviewing the art. No game session, timings, GPU-memory measurement or FPS claim.

Installed the Elven buildings, then the Elven selectable builder, then repaired the installed
Dwarven builder's private player-colour mapping. This closes the missing-mapping issue noted
in the preceding review entry; runtime player-colour appearance is still unverified.
The Dwarven building archive remains byte-identical to the pre-install snapshot. The repaired
Dwarven model and all diffuse DDS files also remain byte-identical to their reviewed install.

The new Dwarven mask is a 2048×1024 RGBA TGA, 8,388,626 file bytes. Its character region
repeats the original mask exactly; the added-prop region stays transparent white. All three
private diffuse aliases share this mask. The builder archive grows from 5,274,291 to
13,712,576 bytes (+8,438,285), including the composed house-colour INI. The model remains
1,079,349 bytes, SHA-256 `243ce51959dbcac531269c65919d26df78ba448b63443f0d4ec0033c54eaa22b`.

Final read-back verified the effective load-order bytes of the Elven building archive
(274 members, 101 models), Elven builder (4 members, 1 model) and repaired Dwarven builder
(6 members, 1 model). Every applicable effective cache record matches its model; all four
private builder colour mappings appear exactly once in the effective INI. An initial audit
also inspected the lower-priority BFME2 forge record and found its original layout; that is
not the RotWK-selected record. The final audit follows the same first-provider cache order
as the installer. No secondary-cache rewrite was needed.

Installer self-checks, exact mask-row checks, unrelated-record preservation, file harness and
repository invariants pass. A simulated reverse-order restore validates every backup/hash
without live writes and returns exactly to the pre-install snapshot. Restore order is Dwarven
colour repair, Elven builder, then Elven buildings; each installer retains `--revert` and refuses
later conflicting changes. Evidence: `build/assets/install-pair/{before,after,verification}.json`.


## Dwarven troop source survey — 2026-09-26

Build: `1385bd4` plus the uncommitted source-review tool. Scene: offline current installed
HD troop models in decoded idle poses; no game run or performance claim. The active barracks,
archery range and forge recruitment lists resolve to 8 core troop types. The review sheet has
9 portraits because the Zealot's 2 complete source models are shown separately; this is not a
claim about runtime selection of its `ExtraMesh` variation. Upgrade scope includes 4 troop
banner models and the Battlewagon's 4 role choices, with armour available after role selection.

Every decoded idle frame has finite transforms and a matching skeleton hierarchy. Source
hashes/providers are recorded in `build/assets/dwarves/troops/sources.json`. Initial Zealot
previews incorrectly exposed the forged-blade effect cards; active creation scripts hide them,
so the final source previews apply that hide. These are material/shape review images, not
simulations of player-colour blending, additive effects or game lighting. No models, textures,
gameplay data, installed archives or live caches were changed by the survey.


## Dwarven troop redesign and animation audit — 2026-09-26

Build: `1385bd4` plus uncommitted `assets/dwarves/troops/`. Scene: offline paired model/texture
and decoded-animation review. No game session, frame-time, FPS or measured GPU-memory claim.
The reviewed building palette is reused: Erebor blue, warm bronze/gold, iron and timber.

Scope: 8 core troop types, both Zealot source appearances, 4 banner designs, Battlewagon crews
and role/armour combinations, and siege construction/destruction/deployment. The staged set
contains 42 private models: 19 enhanced models and 23 existing lower-detail variants retaining
their original geometry with the same private palette. All original body positions, triangles,
UVs and bone assignments are retained; new surface-fitted details use existing bones only.

| Static sum across the staged model set | Source | Redesign before private renaming |
|---|---:|---:|
| Vertices | 104,945 | 118,937 |
| Triangles | 111,032 | 116,816 |
| W3D file bytes | 10,575,828 | 11,007,300 |
| Corresponding diffuse file bytes | 8,523,320 | 8,960,336 |

These sums include mutually exclusive LOD/state models; they are not simultaneous scene costs.
The 24 private diffuse sheets retain source dimensions. Fourteen private house-colour masks
add 7,334,226 file bytes, copied unchanged. The staged archive has 93 members. Private models
use the established uncached own-copy path; private textures/masks are registered in staged
current-cache copies, with unrelated records byte-identical. Original assets are not replaced.

The first DDS export lost the Zealot sheet's mip chain: its 768×384 source has 10 levels but
ImageMagick emitted 1 for this non-power-of-two size. The final writer compresses each required
level explicitly and preserves the original count/dimensions. It also copies original DXT3/DXT5
alpha blocks at every level; the initial banner alpha deviations (up to 19/255 and 9/255) are
now zero. Protected face/hair pixels and alpha are byte-exact in the lossless painted PNGs;
RGB DDS compression is still lossy. No resolution reduction was used.

The full motion audit passes for 42 models, 15 rigs and 257 matching source clips: 17,663 decoded
frames, 814 model/clip pairs, 663,490 finite bone transforms and 20,008,557 finite added vertex
positions. Exact local geometry/rig preservation proves original motion is unchanged for all
frames; 126 first/middle/last model-pose comparisons independently check that equality. All
lower-detail, construction and embedded death rigs are included.

Inherited source exceptions are explicit: 3 absent authored references; 10 clips without a
staged troop rig (auxiliary fortress/cinematic families); empty `RUGimli_IDLG`; and 2 passenger
Phalanx death routes pointing at the incompatible ground rig. They remain unchanged. These
are excluded cases, not silently passing animations. Source provenance covers 376 hashes.

The package audit passes visual-only INI changes, private names, geometry/hierarchy preservation,
texture size/mips/alpha, unchanged house masks and live installation hashes. No troop archive
or staged cache was installed. Reports are in `build/assets/dwarves/troops/redesign/`:
`build.json`, `paint-checks.json`, `audit.json` and `motion-checks.json`.

Review output: 41 paired equipment stills and 143 representative motion GIFs, each sampled
at 12 poses across its full source clip. Playback delays follow nominal source frame rates;
game speed modifiers are not simulated. Both sides use identical framing/lighting, with camera
bounds covering the full clip. The gallery and after-only roster poster are `review.html` and
`poster.jpg`. The offline previews omit player-colour blending, particle simulation and launched
projectiles; their absence in the previews does not remove the original game effects.


## Dwarven troop warm-palette revision — 2026-09-26

Build: `1385bd4` plus uncommitted troop sources. Scene: offline paired troop renders and
source/staged-package audit; no game run or runtime performance claim. The earlier fixed-blue
cloth/enamel direction was rejected by Max. This revision uses warm neutral wool, bronze/gold
and dark iron; the earlier geometry and animation results above remain valid. Rejected sample
images/manifests are retained under `build/assets/dwarves/troops/redesign/rejected-blue/`.

The 42 models have identical geometry to the earlier staged redesign. All 24 private diffuse
sheets were rebuilt with original dimensions/mip counts; the 14 house-colour masks remain
byte-identical, preserving the player's choice of team colour. Protected skin/hair pixels and
PNG alpha remain exact; decoded DDS alpha maximum error is 0. Source and live installation
hashes still match. Full matching-clip motion validation passes again with the same 257 clips
and 17,663 decoded frames; inherited missing/incompatible references remain documented.


## Troop skin preservation and final warm/Elven revisions — 2026-09-26

Build: `1385bd4` plus uncommitted troop recipes, secondary-skin guards and troop-local posing.
Scene: offline native-model staging, protected-texture checks and decoded source animation.
Nothing installed; no game session or runtime performance measurement.

Follow-up visual inspection removed a gold tint from the Dwarven mount's foreleg by retaining
the complete original mount sheet. The Guardian's protected beard rectangle overlapped blue
shoulder cloth; only the known blue cloth pixels in that island are now repainted. Final
Dwarven scope is 23 painted sheets, 14 original house-colour masks and 42 private models.
Corresponding diffuse bytes are 8,435,784 source and 8,872,800 painted; mask bytes remain
7,334,226. Earlier 24-sheet warm revision above records the intermediate version.

A deeper chunk audit found that the shared mesh writer removed secondary skin positions
(`0xC00`) and normals (`0xC01`). The earlier primary-bone-only motion audit did not catch this;
its previous original-motion certification is superseded by the full skin-channel checks here.
The discarded Elven staging build lost 137,732 bytes from each secondary channel and added
149,112 ordinary array bytes, explaining its misleading 126,352-byte net size reduction.
No package from this intermediate revision was installed.

The final recipes leave every mesh carrying secondary channels wholly intact, preserving both
bone indices, both weights and both coordinate/normal arrays. Only supported meshes receive
fitted additions. A troop-local posing helper evaluates the weighted sum in the respective
bone spaces; the shared building lifecycle poser is unchanged. A synthetic rotation/translation
blend check passes. Both source manifests load successfully: 95 models and 166 blended meshes,
with valid secondary counts, indices, active weights summing to 100 and finite rest positions.

| Final model-set static sum | Dwarven source | Dwarven staged | Elven source | Elven staged |
|---|---:|---:|---:|---:|
| Vertices | 104,945 | 115,905 | 82,960 | 85,360 |
| Triangles | 111,032 | 115,464 | 95,313 | 96,273 |
| W3D bytes before private renaming | 10,575,828 | 11,203,412 | 7,870,003 | 8,006,323 |

These sums include mutually exclusive detail/state models, not simultaneous scene costs.
The final Dwarven set has 14 models with fitted geometry; the final Elven set has 9. All
remaining models retain their original geometry, with private palette sheets where applicable.

Elven scope: 53 private models, 17 painted sheets and 9 original house-colour masks. The staged
archive contains 92 members; provenance covers 512 source hashes. Corresponding diffuse bytes
are 3,792,760 source and 4,349,856 painted; masks add 4,456,844 bytes. Ent/Eagle/horse natural
sheets retain their original appearance. The source Mirkwood shield's single-level mip chain
is retained and recorded as an inherited limitation. Original PNG alpha/protected pixels and
compressed DXT3/DXT5 alpha blocks remain exact; decoded DDS alpha maximum error is 0.

Independent scoped-INI verification allows 15 troop object blocks. Hero parents, the generic
Ent base and the fortress's Vigilant Ent remain exact. Recruited Fir and Eagle children get
private copies of their inherited visual draw only; original recruitment, gameplay and
animation routing are unchanged. Both packages still require review before installation.

Final weighted-motion audit: Dwarves validate 257 matching clips / 17,663 decoded frames across
15 rigs and 814 model/clip pairs, with 663,490 finite bone transforms, 17,627,920 added vertex
positions and 126 original/new model-pose comparisons. The 3 missing source references,
11 skipped available auxiliary/empty clips and 2 incompatible passenger death routes remain
explicit. The final Dwarven archive contains 92 members.

Elves validate all 381 available clips / 25,590 decoded frames across 11 rigs, with 874,792
finite bone transforms and 5,655,840 added vertex positions. Seven absent authored references
remain recorded; no available clip was skipped. Both factions now evaluate original two-bone
blending in their numerical pose comparisons and rendered previews. The Elf intermediate
6,202,500 added-position count is superseded after blended-body additions were removed.

Elven weighted-pose numerical confirmation covers 1,861 model/clip pairs and 159
original/new model-pose comparisons. `cleanup-equivalence.json` records byte-identical Elven
geometry output after deleting the now-unused body-clasp path; no art rebuild was necessary.

Final regenerated review coverage: Dwarves have 41 paired stills and 143 motion GIFs; Elves
have 42 paired stills and 159 motion GIFs. Every GIF contains 12 sampled frames with delays
derived from its original clip's nominal frame rate. Media inventory, decoding, timing and
freshness checks pass; every current review file is newer than its final model work, painted
DDS inputs and two-bone poser. Reports: each faction's `redesign/preview-checks.json`.
No superseded blue-palette or primary-only-pose media remains in the current galleries.
Package, source/skin preservation, live-file, scope and harness checks pass.

## Men of the West troop staging — 2026-09-27

Build: `1385bd4` plus uncommitted Men troop catalog/art and shared staging/audit reuse.
Scene: offline source extraction, staged assets, weighted animation decoding and paired Blender
review renders. Nothing installed; no game session or runtime performance claim.

The source manifest covers 594 hashes. The staged archive has 115 members: 52 private models,
29 painted sheets, 21 copied original house-colour masks, 12 scoped object INIs and the composed
house-colour table. Two banner sheets retain their original shared HC_GUBanner mask lookup;
its existing JPEG/PNG resources are recorded without conversion or new cache registration.
Corresponding diffuse bytes are 7,371,896 both before and after; copied masks total 13,241,220.
These include alternative source sheets, not simultaneous runtime residency.

| Whole model-set static sum | Source | Staged before private renaming |
|---|---:|---:|
| Vertices | 85,207 | 91,447 |
| Triangles | 91,167 | 93,663 |
| W3D bytes | 8,092,644 | 8,449,380 |

Fourteen models have fitted additions, totalling 2,496 added triangles. Detail/state models are
mutually exclusive; these sums are not a scene cost. Original position/normal/UV/triangle and
full influence prefixes remain exact. Secondary-skin meshes retain their complete source bytes.
All source mip counts, PNG alpha/protected regions and DXT3/DXT5 alpha blocks are retained.
The CE sheet retains DXT1, avoiding a decoded face-color change from BC1 interpolation.

Scope verification covers 15 changed object blocks. Three are visual-isolation copies: campaign
Royal Guard, Lone Tower archer and enemy Morgul Trebuchet retain original Draw and SubObjectsUpgrade
modules. Other original non-troop blocks and all gameplay/animation directives remain unchanged.
An independent synthetic-alias reverse check also covers original RandomTexture/UpgradeTexture
routes. Existing Dwarf and Elf package audits still pass after the shared-mask staging addition.

Weighted motion audit passes 440 matching clips / 29,422 decoded frames, across 14 rigs and
1,823 model/clip pairs. It checks 999,770 finite bone transforms, 13,159,440 added vertex positions
and 156 original/new model-pose comparisons. Five authored references are absent. Nine available
clips belong to untouched debris, fortress siege or the unrelated Isengard banner hierarchy;
those lack a staged Men troop rig and are explicitly skipped. All are recorded in
`build/assets/men/troops/redesign/motion-checks.json`. No animation files or routes are repaired.

Final Men review coverage: 50 paired equipment stills and 132 motion GIFs, each with 12 samples
and original source nominal clip timing. All 182 gallery records are unique and present; the
media audit verifies decoding, frame counts, delays and freshness against final model/texture
inputs and the weighted poser. A final Dol Amroth hood-cloth correction preserves protected
horse eye/muzzle/mane pixels. Decoded DDS protected regions and alpha pass exact source checks.
Forged-blade glow has offline speckling in both original and proposed renders; unchanged source
materials and this preview limitation are documented in the gallery. Package/source/scope,
weighted-motion, complete-media and harness checks pass. Live installation is unchanged.


## Men citadel pilot — 2026-09-27

Build: `1385bd4` plus uncommitted Men citadel recipe and palette. Scene: offline player fortress
asset build and paired Blender review, with separate source-upgrade fit composite. Staged only;
no game run, runtime timing or frame-rate claim. No live installation changes.

`GBFORTRESS` retains its original surface and gains 3,544 triangles (1,458 → 5,002), with
vertices 2,004 → 10,142 after layout. Added triangle tags: trim 1,956, gilt 1,216, top 80,
stoneB 152, stoneA 64, enamel 76. The XY bounds stay unchanged; height rises from 116.6455 to
137.2 (+17.6%, below the recipe's 20% ceiling). Texel density median 8.8 px/unit, p10 5.2,
p90 13.1. Framework texture residency estimate: 22.7 MiB against the Men 256 MiB budget;
this is an asset estimate, not measured game residency.

Healthy W3D grows from 295,896 to 1,004,880 bytes. Private healthy/construction/D2/D3 files are
1,004,880 / 1,064,106 / 886,376 / 1,230,181 bytes. The staged output totals 36,401,030 bytes,
including INI and texture variants. Healthy diffuse is 4096 DXT1, 13 mip levels, 11,184,952
bytes. Damage, snow and stonework variants are 2048 DXT1, 12 mip levels, 2,796,344 bytes each;
the 2048 normal TGA is 12,582,956 bytes. Alternatives are not simultaneous scene costs.

Lifecycle models all build without a source-only fallback: construction keeps 6,525/6,525
candidate faces, D2 6,877/6,877, D3 7,549/8,229 after break clipping. The contact sheets show
new roof frames appearing before slate infill in construction and exposed metal in damaged
roofs. Original animation routes and bones remain; these previews are not a live-game test.

Final pipeline checks pass 109/109. Review has 6 paired healthy/composite views and 3 lifecycle
contact sheets. A reverse-alias audit restores the original Men INI by removing private texture
routes, reversing the model names and restoring static LOD selection on the 2 main draws.
Private models leave Arnor and neutral shared-model users on EA assets. Original flag/upgrade
meshes are retained; live asset/cache/archive hashes match the earlier install snapshot.

Rejected first pass: 1,458 → 4,758 triangles (+3,300), height 124.6, 108/109 checks passed.
The open-back check found 50/2,272 newly visible faces; closing the arch and cornice backs fixes
it. Initial gate piers at Y ±21 overlapped the oil outlets and were moved to ±17. Crowns at
Z 104–117 crossed the original flag planes, so their bodies now start above Z 121, on narrow
masts. Neither pass was installed. Final upgrade fit preview retains the original central
Ivory Tower, healing house, oil hardware, closed door and flags; oil crew and particles are not
simulated. No extra banners or night lights were added.


## Men citadel architectural revision — 2026-09-27

Build: `1385bd4` plus uncommitted revised Men citadel recipe/palette. Scene: offline construction,
paired Blender previews and original door animation posing. The player rejected the preceding
trim/crown pilot as insufficiently detailed and too Elven in colour; its measurements above
remain historical, not the current design. The rejected images are preserved under
`build/assets/men/fortress/rejected-trim-pilot/`. Nothing installed; no game run or runtime claim.

The revised body has 11,606 triangles (EA 1,458; +10,148), within the 15,000 hero-building limit,
and 22,774 vertices (EA 2,004) after layout. Added tags: stoneB 2,868, course 1,024, top 892,
stoneA 1,688, trim 1,461, enamel 27, relief 1,404 and gilt 784. There are 16 paired-face
buttresses, 40 small corbels, 8 tower White Tree shields and the gate shield with 7 stars.
Original XY and height bounds are unchanged (top 116.6455); the rejected added gold masts are
removed. Density median 8.5 px/unit, p10 5.1, p90 12.0. Texture dimensions/mips/formats and the
22.7 MiB framework estimate are unchanged from the prior pilot; no game residency measurement.

Healthy/construction/D2/D3 W3D sizes are 2,139,168 / 2,135,354 / 1,654,168 / 2,267,661 bytes;
complete staged output is 40,411,838 bytes. Lifecycle retains 13,133/13,133 construction faces,
13,485/13,485 D2 faces and 13,939/14,837 D3 candidates after clipping. All states built without
fallback. Pipeline checks pass 109/109; all 6 paired views and 3 state contact sheets decode
and are newer than final outputs. Original live-install snapshot hashes remain unchanged.

Door clearance correction: the first architectural iteration used a 13.9 half-opening and
pier belts reaching inward to |Y|14.5, intersecting original outward door motion. Widening the
jamb alone did not fix the low curved arch. Final half-opening 15.6, spring 40, apex 44 and
piers centred at ±17.5 (maximum half-width 1.9 below the door top) clear both original door
animations across 798 quarter-frame poses. Inner curve/jamb minimum clearance is
0.635122 / 0.383812; outer curve/jamb is 1.843204 / 1.442506. This is sampled triangle-surface
and conservative pier-volume evidence, not a continuous-time proof. Source hashes, final recipe
hash and detailed measurements: `work/door-clearance.json` under the build. Earlier static
asset check passes did not establish animated door clearance.

Door half-envelope at X53.8/54.8/55.8/56.8/57.5 is respectively
14.722472 / 14.898799 / 15.075127 / 15.251454 / 15.374883 for Z0..43. Pier outer extent19.4
stays inside oil outlet start19.507; wider capitals begin above42.4, clear of door top40.91
and oil top38.857. Pier back49.2 clears healing-house front48.75. Tower shields occupy
Z44.5..55.5 between window tiers ending40.65 and starting60.08; corbels74..76 clear upper
windows73.44 and flame hardware73.47. Gate shield origin55.6 embeds its rear55.48 in the
original arch front55.638, and its tree/stars embed in their field. An intermediate missing
foliage ramp stopped painting and was corrected before final output; no fallback was used.

The intermediate architectural meshes had 11,582 triangles; the widened shallow arch produces
the final 11,606. Private model/texture scope and original upgrade routes remain unchanged.
The upgrade composite keeps original flag colours; palette changes apply to this citadel body.

## 32-bit address space per texture byte — 2026-09-27

Build: installed `engines/w10` wined3d (0001–0021) vs the same + unbuilt
`patches/wined3d-wow64-buffers/0022` in a scratch engine copy. Scene: `tools/texmem32.c` in a
throwaway prefix, no game. A managed texture costs 1.031 bytes of the 2 GB per byte, kept until
release (1024² DXT5 and 512² A8R8G8B8); an empty process fails CreateTexture after 1.87 GB of
them. With 0022: 0.000 after the fill/draw; 3 GB loaded in 14 MB; +0.25 ms per MB at the first
draw. Fix 0014 adds up to 0.6× transiently for bursts of small first draws. Details, method and
risks: `docs/MEMORY-2GB.md`.
