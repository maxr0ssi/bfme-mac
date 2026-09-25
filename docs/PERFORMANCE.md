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

`WINE_D3DX9_FXOPT` (bit mask, default all): `0` = old code paths, `1` = only 0005, `2` = only 0006.

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
- Particles, decal shadows, terrain extras and volume shadows already skip themselves in this pass
  (the checks above); what is left is a loop over the particle systems with one virtual call each.
  Nothing worth cutting.
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
