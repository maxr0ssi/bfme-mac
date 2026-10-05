# Performance record

Every measurement behind the performance work, with date, build and scene.

**Where it stands.** Installed: the wined3d patches 0001–0021 (§6), the d3dx9 series
(§11, [LOAD-TIME.md](LOAD-TIME.md)) and the game patch (§10), which has loaded in every game
session since 2026-09-24 (`logs/gamepatch.log`). Own base with no fighting: 8–11 → 30 FPS (the
engine cap). Small battle: ~11 → 22–30 FPS (§2). AI battles: 18.9 FPS without msync, 21.7 FPS
with it (§8). Large battles are the open problem: the game's own code takes 25–32 ms of a
42–51 ms frame (§8, §10.5). Texture memory and the 32-bit address space: [MEMORY-2GB.md](MEMORY-2GB.md).

Contents: 1 pipeline · 2 in-game measurements · 3 GL call costs · 4 synthetic frame ·
5 d3d9 test suite · 6 Wine fixes · 7 Vulkan · 8 other levers · 9 crashes · 10 game patch
(10.1 render side, 10.2 shadow volumes, 10.3 shadow-map pass, 10.4 particles, 10.5 game logic) ·
11 d3dx9 effects · 12 per-draw FX cost · 13 first-use texture loads · 14 eight-player games ·
15 our art's draw cost against EA's · 16 session monitor · 17 logic phase 5 · 18 spell-cast freezes ·
19 unit-count scaling · 20 the pathfinder · 21 path searches split over logic phases.

Machine: MacBook Pro, Apple M3 Max (12P+4E cores, 40-core GPU), 64 GB unified memory, macOS 26.3,
`powermode 0`. Engine `engines/w10` (Sikarugir wine-staging 10.0, new-style WoW64, x86_64 under
Rosetta), D3D9 → wined3d → Apple OpenGL 4.1 ("4.1 Metal - 90.5"). Game: RotWK 2.02 + HD Edition,
3024x1964. The §2 runs used Options.ini UltraHigh with Shader, Shadow and Water at Medium; the §8
and §10 sessions are recorded at UltraHigh. Another session ran Blender renders during the
2026-09-24 micro-benchmarks (load average 7–15), so single-run numbers there carry that noise.

Rule used throughout: a change counts only when its effect is outside the run-to-run spread, and
anything the player sees is checked by eye as well.

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
| stream + clip planes + state + SSE2 (0002–0008) | 42.1 ms, 23.8 FPS | 88.8 ms, 11.3 FPS |
| **+ direct host-buffer writes (0009)** | **21.9 ms, 45.7 FPS** | **34.2 ms, 29.3 FPS** |
| same, installed by `scripts/wine-fixes.sh` | — | 34.0 ms, 29.4 FPS |

App-thread split, default scene: stock spends 22 ms in Lock + 41 ms in Unlock per frame (the wait
for the render thread); with 0002–0009 Lock + Unlock is 0.14 ms and the remaining time is the
render thread (seen as the wait in Present: 32 ms without 0009, 13 ms with it).
Image checksums (`--crc`) are identical between stock and the fixed build in all three scenes
tried (grouped, grouped heavy, default interleaved): `64abfac0`, `5eb28a61`, `68fe2221`.
Stock itself is occasionally non-deterministic in the interleaved scene (stray triangles), the NOOVERWRITE race that Wine's test 26868 below also catches.

UI-side scenes (2026-09-24 15:00–15:30, `direct3` = 0001–0011, `direct4` = 0001–0019, median of 3,
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
| 0002–0008, `WINED3D_WOW64_BUFFERS=off` / `=pin` | completes, 266 / 265 |
| 0002–0008, stream (first version) | **crash** after `test_dynamic_map_synchronization` |
| 0002–0010 | completes, **262 failures: 5 fewer than stock, none new** |
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
  performance cores. `tools/perfprobe.py` records per-thread `ps` priority (31 default, 4
  background); the §2 small battle showed 46–47 / 31, so the game does not run as background.
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
threads; the thread-suspending profiler is no longer used during play. The same site faulted again
at the exit of the 2026-09-28 session with no profiler running (`highmem=1`, [MEMORY-4GB.md](MEMORY-4GB.md)),
so the profiler is not its only trigger.

## 10. Game-side patch (`gamepatch/`, 2026-09-24)

In the game since 2026-09-24: `logs/gamepatch.log` has six sessions (2026-09-24 to 09-28), each
listing every patched site. The 2026-09-28 exit line: hittest 218,617 calls with 3 x87 fallbacks,
quatmat 2 fallbacks, no shutdown Release skipped.

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
| shutdown | 0x5385b5 `call [ecx+8]` → `call safe_release` | the exit crash (13 of 15 dumps, §9): static texture wrappers Release after `DX8Wrapper::Shutdown` FreeLibrary'd D3D9.DLL. While the game's D3D9 handle (0xdd3610) is set this is exactly `p->Release()`; afterwards the Release is skipped if the vtable is in no loaded module | `t_misc` [3] with a really unloaded DLL; in game, 0 Releases skipped at the 2026-09-28 exit |
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

### 10.1 Render-side patches (second batch, 2026-09-24)

In the game, animdedup has skipped 0 % of Render evaluations in every session logged (for example
0 of 2,955 on 2026-09-28). Why is not known: the log's detail line attributes none of the calls to
any of its reasons. The other patches here log no counters.

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

Not built: a per-frame bounding-sphere cache (the second Get_Bounding_Sphere in
renderOneObject never evaluates animation, since the first call left the pose valid; an exact cache
would have to snapshot transform, bone pivots and box, about what recomputing costs).

### 10.2 Shadow volumes: edgemap and shadowpar (2026-09-24)

In the game at UltraHigh the volume pass barely runs (shadow maps turn volumes off); see the first
session below.

Code: `gamepatch/src/p_edgemap.c`, `par_shadow.c/.h`, `par_shjob.c`, `p_shadow.S`, with the worker
pool `parallel/pool/parallel.c` built into the DLL unchanged; test `t_shadow` (+ `t_shadow_world.c`).
0x4ef790 (§10 "polygon clip", 2.9 % of the main thread in `battle-msync2`) is `constructVolume`,
the shadow-volume builder; the whole stencil-shadow pass is 18–25 %.

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
  with TheGlobalData+0x62), i.e. two more scene submissions. A display switch (0x6bff7b, via
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
- Parallel light environments: the common "tint" path writes the shared global lights
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

### 10.5 Game-logic x87 code (2026-09-25, static + standalone tests)

In the game on 2026-09-28 (exit line of a ~7 min session): mat2quat 5.57 M calls (12,961 x87
fallbacks), distcalc 1.54 M (3), bsphere 2.97 M (0), worldcell 6.93 M (52,560), ftol2 33.3 M (6).

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

## 13. First-use texture loads: what a click costs (2026-10-04)

Max: "clicking buildings can cause the frames to drop", "clicking places on the HUD can cause frame
issues", "frames are all jumpy". A texture is loaded on the game thread the first time something that
uses it is created or drawn. All of them go through one call, game.dat 0x53117e:
`D3DXCreateTextureFromFileInMemoryEx(dev, bytes, size, 0, 0, mips, 0, UNKNOWN, MANAGED, D3DX_DEFAULT,
D3DX_FILTER_BOX | skip << 26, ...)`, d3dx9_27 being Wine's builtin since LOAD-TIME.md. The file opener
0x530d29 tries `name.dds`, then `.tga`, `.jpg`, `.png` for every texture, APT ones included (0x477d1c
routes `apt_*` to Art/Textures/, everything else to Art/CompiledTextures/xx/).

**Measured without the game** (`tools/texupload.c`: our real files through that call on the w10
engine, `d3dx9_27=b`, median of 11 new textures each, three runs at load 7-16 on the shared Mac; the
cleanest run shown; `game` = the game thread's load + create + fill, `extra` = that frame against the
same frame without the new texture):

| texture | file | game ms | extra ms |
|---|---|---|---|
| unit portrait / button page, EA 64² / ours 128² DXT5 | 6 / 22 KB | 0.2 / 0.2 | 0.7 / 0.7 |
| button / icon page, EA 256² / ours 512² DXT5 | 88 / 350 KB | 0.2 / 0.2-0.3 | 0.6-0.9 / 0.8-1.3 |
| HUD atlas apt_palantir_1 (1 level), EA 1024x512 / ours 2048x1024 TGA32 | 2 / 8 MB | 1.3 / 4.7 | 2.7 / 8.9 |
| the same as DXT5 / as uncompressed DDS | 2 / 8 MB | 0.7 / 2.9 | 1.9 / 9.0 |
| HUD frame, EA 512x256 / ours 1024x512 TGA32 | 0.5 / 2 MB | 0.5 / 1.3 | 1.2 / 2.7 |
| house-colour mask, EA porter 256² / our worker 2048x1024 TGA32 | 0.25 / 8 MB | 0.9 / 23.0 | 1.6 / 28.3 |
| normal map 1024² TGA24 (EA's and ours alike) | 3 MB | 33.5-44.4 | 36.2-44.7 |
| normal map 2048² TGA24 (ours) | 12 MB | 132.6 | 136.0 |
| normal map 1024² TGA32 (ours) | 4 MB | 12.6-13.0 | 15.3-16.0 |
| building sheet DXT5 2048² / 4096² | 5.3 / 21.3 MB | 1.7 / 5.4 | 4.3 / 10.9 |
| **the TGA textures above, baked** (`tools/texbake.c`): mask / normal 1024² TGA24 / TGA32 | 10.7 / 5.3 / 5.3 MB | 3.0 / 1.7 / 1.6 | 7.9 / 4.8 / 4.8 |

What it means:
- The 2x portrait, button and icon pages (`sagekit ui2x`, `sagekit icons`) cost 0.1-0.4 ms more than
  EA's on their first use: not a hitch. They are all DXT already (EA's two uncompressed pages became
  DXT5).
- The HUD's 2x TGAs cost 9 ms per atlas and 3 ms per frame once. EA ships every APT texture as an
  uncompressed TGA; the palantir movie's .dat loop (0x4aacdd) creates all of them when the movie
  loads. DXT5 would save ~7 ms per atlas but changes the picture (Max's call, not shipped).
- A TGA with a mip chain is the expensive kind: d3dx9 converts and box-filters the chain on the game
  thread, 12 ms per million pixels for 32-bit, 31-42 for 24-bit. Our packs ship 214 of them (normal
  maps, house-colour masks): 0.7-1.8 s of game thread per faction pack. A building's first
  appearance pays for its own: 40-50 ms per 1024² normal map, 130-170 ms per 2048² one. Objects
  whose INI has no `KindOf PRELOAD` are created in the match, on a click: the fortress expansions
  (moats, spikes), the Men's base defences, the Dwarven mine, the Mordor barricade, the neutral
  inn/outpost/shipwright/signal-fire foundations, all carry 1024²-2048² TGA normal maps.
- No eviction: RotWK has no time-based texture invalidation (WW3D's 20,000 ms `InactivationTime`
  constant is absent from game.dat), every texture is `D3DPOOL_MANAGED`, and the only purge path in
  WW3D is the out-of-video-memory retry. A loaded texture stays; no texture loads twice per match.
- Frame logs (gamepatch passtimers, 5 s windows, matches only): frames lost to the 30 FPS cap
  1.8-6.3 % on 2026-09-28..30 (one session 32 %), 6.2 % on 10-03, 4.2 / 5.8 % on 10-04; render passes, particles and
  WW3D::Render per frame unchanged by the 10-04 installs (FX archive included): particle manager
  0.1-0.6 ms, live particles 180-920. The windows that drop frames have no render pass to match, which
  is what load stalls between frames look like; the logs cannot show single frames.

**The fix** (`sagekit/texbake.py`, called by `sagekit install <faction>` and `sagekit unit <id>
--stage`): each such TGA ships as the DDS d3dx9 would have built from it. `tools/texbake.c` makes the
game's call on the TGA with the game's d3dx9, writes every level in the format it chose (X8R8G8B8
for 24-bit, A8R8G8B8 for 32-bit; EA's HD edition ships 68 uncompressed DDS too), loads the DDS with the
same call and compares every byte of every level: only identical bakes ship, so the texels on screen
are the same. asset.dat keeps filing the `.tga` name. Cost: ~0.04 s instead of 0.7-1.8 s of game
thread per faction; the archives grow by a third of each TGA (the stored mips; memory is unchanged,
as d3dx9 built the same chain). Identical at texture reduction 0; with a reduction both versions
drop whole top levels, d3dx9 resizing the TGA with its default filter instead (near-identical).
`sagekit validate` fails a staged archive that still ships one, and UI pages that are not DXT or over
1024 (APT textures over 2048x1024).

**Memory (a):** our archives hold 3.55 GB of texture as loaded (DXT at file size, TGAs at 4/3 of
32 bits a pixel): Men 625 MB, Angmar 507, Isengard 453, Elves 448, Dwarves 385, Mordor 374, Goblins
262, neutral 101, UI 158 (ui2x 71, icons 44, HUD 43). A match loads only what it creates; Men and
Angmar are at or over the 512 MB per-faction budget (`budget_mb`, MEMORY-2GB.md: 1.03 bytes of
32-bit address space per texture byte with today's wined3d). Not a thrash risk (nothing is evicted);
an address-space risk in a four-faction game, which patch 0022 (MEMORY-2GB.md) would remove.
Update 2026-10-04 (static count, MEMORY-2GB.md "Texture memory of our archives"): every structure,
state and unit of all 7 factions is 3.2 GB of texture and 0.92 GB of W3D against EA's 0.45 / 0.29 GB;
a full 8-player build would need ~5 GB of the 4 GB (the 09-28 memwatch: 1.3-1.5 GB used in a match
before most art loads). No eviction or hitch from pressure before that wall. Opaque DXT5 sheets now
ship as the DXT1 that draws the same texels: 3554 → 3287 MB staged over all packs; no texture has a
top mip level the closest camera never samples at 3024x1964 (`sagekit/texreach.py`).
wined3d 0022 offline (MEMORY-4GB.md): 4.09 GB of our textures in 85 MB of address space instead of
3660 MB; frames unchanged within the spread; a texture's first draw 0.3-0.7 ms per MB slower.

Still to see in game (needs the game): which of these loads land on a click at Max's settings, i.e.
whether RotWK preloads a structure's assets at match load (Generals only does with `-preload`; RotWK
has no such switch string, and no direct test of `PRELOAD`, KindOf bit 26, was found in game.dat). The fix
helps either way: at match load it shortens the loading screen, on a click it removes the stall.

## 14. Eight-player games: the logic phases (2026-10-04)

Max: "frames are dropping when I test 8 players, it struggles".

**What is installed** (md5 of the engine against `wine/build-d3dx10`, 2026-10-04 21:45): wined3d.dll,
wined3d.so and d3dx9_27.dll are the current builds (0001-0021, d3dx9 0001-0008). The game patch in
the RotWK folder is the 2026-09-27 build; the only later change is a comment. Every speed patch is on
(the log of each session lists them). Not installed: wined3d 0022 (memory, `unbuilt/`), and
shadowpar and limiter, which are off by design. The RotWK folder's gamepatch.ini still has the
measuring set on (passtimers, renderstats, particlestats, from `measure-session.sh on`). passtimers
turns perfmarker's early return off, so every draw builds its marker name again (40-160 ns each, §10.1,
400-1,500 markers a frame). That is an estimated 0.1-0.5 ms a frame, not measured in the game.

**Rendering is not what drops the frames.** passtimers 5 s windows of the 10-03 and 10-04 matches
(`logs/gamepatch.log`), frame time against the sum of the top-level passes (RenderViews +
UpdateShadowMap + RenderUI):

| session | windows ≥ 60 frames | median frame | median render | slow windows (> 36 ms) |
|---|---|---|---|---|
| 10-03 17:30-17:45 | 121 | 33.2 ms | 6.7 ms | 29; render 3.9-20.2 ms, outside rendering 20.1-64.1 ms |
| 10-04 20:34-20:42 | 86 | 33.2 ms | 5.2 ms | 19; render 2.4-14.1 ms, outside 25.8-42.1 ms |
| 10-04 21:37-21:41 | 40 | 33.8 ms | 8.9 ms | 16; render 5.8-27.3 ms, outside 13.1-41.8 ms |

renderstats in the same minutes: 120-230 FX draws per pass, 660-920 live particles, particle
manager 0.5-0.8 ms a frame. The particle cap (4000) is never reached, and the shadow-map pass is
2-5 ms. Most of a slow window's time is spent outside the render passes (that time also holds the limiter's wait in the window's fast frames), which on the main thread means the
game logic, the client update and stalls (§13).

**The logic runs in uneven phases.** GameLogic::update 0x62e4e8 runs once per drawn frame with a phase
1-6 (5 steps a second x 6). Phase 2 runs two subsystems (0xde4354, 0xde4360) and a per-object loop
(0x6260e1). Phases 3 and 4 update the first and second half of update list 0. Phase 5 runs lists 1 and 2
and twelve subsystems; phase 6 runs list 3. From the memory probe of the 2026-09-24 AI battles
(`build/rotwk-re/probe-*/samples.csv`, `logic_phase`, ms per logic step):

| run | phase 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| probe-msync2 | 1.5 | 5.3 | 11.2 | 16.1 | **29.7** | 0.3 |
| probe-ai1 | 1.2 | 2.5 | 6.3 | 4.9 | **12.5** | 0.5 |

So one frame in six carries most of the logic. With 8 players that frame is the one that drops.
Which subsystem or module class owns phase 5 is not known. A leaf profile spreads it thin (§10.5).
(2026-10-05: what phase 5 runs is now known from the code, §17; its time split still needs logicstats.)

**Synthetic frame at large counts** (`scripts/bench-d3d9.sh engine`, 2026-10-04 21:45, load 5-8,
median of 3 x 5 s):

| scene | frame | where the app thread waits |
|---|---|---|
| 3,000 objects, 900 dynamic | 35.9 ms (27.9 FPS) | draw 17.7, Present 5.1 |
| 4,500 objects, 1,350 dynamic | 53.3 ms (18.8 FPS) | draw 33.8, Present 0.04: the command queue is full |
| same + `--cpu-ms 20` | 58.3 ms | draw 19.0 |

At about 4,500 draws the render thread is the limit, at ~8 µs a draw (Apple's driver, §8). Max's
matches draw far fewer, and the 2026-09-25 big battle drew ~3,000.

**logicstats** (diagnostic, off by default; `gamepatch/src/p_lstats.c/.S`, test `t_lstats`). Every 30 s
it logs:
- ms per logic step in each phase, and the frame interval after each phase (mean, max, frames over
  40 and 50 ms);
- ms per step of each of the 19 subsystems GameLogic::update calls through vt+0x28 (hooked at the
  first step that finds the object) and of six direct calls;
- the 12 update-module classes (update function, vtable) that took the most time, from the list
  call at 0x62ea97.

It changes no game behaviour. The test checks that every stub hands the original the caller's
registers, xmm0-7, arguments and stack, and gives back the original's (logic stub, 19 subsystem stubs,
6 direct calls, module stub). A timed module call costs 17-22 ns more than the original sequence.
`scripts/measure-session.sh on` turns it on along with the other diagnostics.

**Next, ranked by gain against risk:**
1. Play normally with the diagnostics off (`scripts/measure-session.sh off`). No risk; an estimated
   0.1-0.5 ms a frame.
2. One 8-player session with `measure-session.sh on` and the new game patch. logicstats names the
   owner of phase 5, and `measure-session.sh sample` adds an inclusive call tree (with Max's OK).
   Then do exact SSE or integer versions of its hot functions (the logicmath pattern, §10.5).
   Estimated 1-5 ms on the spike frame. Low risk: proven by bit-exact tests.
3. Even out the phases: run the tail of phase 5 (its subsystems after lists 1-2) at the start of
   phase 6, which takes 0.3-0.5 ms now. The logic's own order stays the same; only the client
   update and render in between see the state earlier. That could halve the spike frame. LAN risk:
   it needs proof that nothing between the two phases reads or writes state those calls touch.
   Decide after the logicstats numbers.
4. Late-game rendering: renderOneObject from Flush (~5 ms a pass, §12) and pose evaluation in
   parallel before UpdateShadowMap (§10.3). This only matters in big fights with ~3,000 draws.
5. A setting, and Max's choice only because it changes the picture: shadow maps lower or off save
   the shadow-map pass, 2-5 ms now and 15-18 ms in the 09-25 battle. A lower particle cap gains
   nothing, because the cap is never reached.

## 15. Our art's draw cost against EA's (2026-10-04, static)

Question: does the redesigned art cost the main thread more per object than EA's, and how much in an
8-player late game? `python3 -m sagekit.drawcost_report --rows --scene` (sagekit/drawcost*.py) reads
every staged archive (2026-10-04 22:00: 7 faction packs, neutral, builders, workers, heroes) and EA's
pristine archives, resolves each object's Draw modules per state (healthy, construction, damaged,
really damaged, rubble, night; a ChildObject draws its parent's) and counts what the engine draws.
Report: `build/assets/_review_finish/drawcost/report.txt`.

**Cost model** (main thread, UltraHigh, both passes): a render object (one Draw module showing a model,
meshless rigs included) 2 x 6.5 µs (Visibility_Check + renderOneObject, §12); an FX mesh 2.5 µs in
the main view + 1.8 µs in the shadow-map pass, a DX8 mesh 1.4 µs (main view only), a material in view
~11.5 µs (passtimers "Rendering mesh FXShader", "RenderFXShaderBatch" self, 2026-09-25 09:50 battle:
2,261 / 3,174 meshes, 341 / 413 batches; every session since within 0.3 µs a mesh). Particle manager
render, map-wide: 1.6 µs per system + 0.5 µs per live particle (least squares over the 114 particlestats
minutes of 2026-09-28..10-04, r² 0.5). Particle simulation is not timed and not counted. Triangles cost
only the GPU (11-16 % busy, §2).

**Per object** (326 objects whose art we changed, healthy state, EA → ours):

| | EA | ours |
|---|---|---|
| render objects | 449 | 560 (+64 fire rigs, +39 house-colour models, capture dress) |
| main-view draws / shadow-pass draws | 1,770 / 516 | 1,820 / 521 |
| meshes per body, materials, passes, HLOD levels | | the same: our bodies keep EA's meshes one for one (one FX material, one sheet each) |
| triangles | 0.72 M | 1.85 M |
| particle systems / live particles | 42 / 1,469 | 444 / 7,396 |

Other states: construction, really damaged and rubble draw fewer objects than EA's (fire and house
models are off there); damaged and night as healthy. Night windows are EA's names, shown at night only.
LOD: EA's buildings carry one HLOD level, ours too. `StaticModelLODMode` is off on 119 of our Draws (111
where EA has `<model>M` / `L` copies, the Angmar mill included): no effect at High or UltraHigh, where
EA draws the full model too; at Medium and Low those players draw our full model instead of EA's lighter one.

Top offenders by added µs a frame (fire, map-wide, plus the rig): Isengard citadel 33 → 383 (42 systems,
538 particles), Mordor citadel 39 → 309 (29, 421), Isengard furnace 125 → 302, Mordor mumakil pen
59 → 226, Isengard siege works 109 → 275, uruk pit 40 → 185, Angmar citadel 70 → 202. Walls and
expansions add a house model each (Dwarven wall pieces 14 → 29 µs), and 10-46x EA's triangles.

**8-player late game** (`--scene`; a base = citadel + 3 expansions, ~15 buildings, 6 wall pieces,
2 builders, 4 workers; 7 factions + a second Men base; soldiers are EA's art and the same either way):

| | EA | ours |
|---|---|---|
| render objects / draws (8 bases) | 332 / 1,773 | 421 / 1,845 |
| materials per base | 80-100 | 80-105 |
| triangles (8 bases) | 0.44 M | 1.48 M |
| particle systems / live particles (8 bases) | 35 / 809 | 499 / 7,561 (cap 4,000) |
| a base in view (objects, draws, materials) | 2.10 ms | 2.33 ms |
| particle render, map-wide | 0.46 ms | 2.80 ms (at the cap) |

So the buildings in view cost +0.1-0.5 ms a frame (+11 %), all of it the extra render objects; the
draw calls are within 4 % of EA's. The fire costs +2.3 ms of particle render once every base burns,
plus its untimed simulation, and fills the 4,000-particle cap, which then removes the oldest particles of
everything, combat effects included. Max's measured matches so far (10-03, 10-04, §14) ran 660-1,170
live particles and 0.5-0.8 ms of particle render: their bases had not reached this.

**What can be cut without changing the picture: almost nothing.**
- Merging meshes that share a material: 12 meshes in all packs share bone and material and no INI
  name (by bone, material chunk bytes and flags); EA splits by bone and sheet. Not worth a model change.
- Welding identical vertices: 2 % (the fortress body 16,700 → 16,423); our hard-edged solids need the rest.
- House colour inside the body: EA never mixes `HC_` and other meshes in a Draw with
  `OkToChangeModelColor` (0 of 2,784 models), so the cloth keeps its own render object.
- The fire rig needs its own Draw (a default state copies its particles into every state, docs/ART.md "Fire").
  It could ride our own house model's Draw where both burn and show in the same states (35 objects,
  -13 µs each in view): same picture, but needs an in-game check. Not built.
- No two fire points of one building share a system within 3 units.

**Max's choices (they change the picture, so nothing is built):** a fire budget per building, e.g. at
most 120 live particles (EA's own furnace has 111): 8 bases 499 → 342 systems, 7,561 → 5,223 particles;
at most 60: 230 systems, 3,585 particles, under the cap.

**Built (2026-10-04 late, Max chose 60; docs/ART.md "Fire budget"):** lean copies of EA's fire systems
(`sagekit/fire_lean.py`) and six recipes consolidated. Our fire over all 64 burning recipes 6,480 →
1,537 live particles; the worst building 538 → 59.5 (Mumakil pen; Isengard citadel 57.8, Mordor
citadel 56.2). Same staged packs, same scene (`build/assets/_review_finish/fire_budget/drawcost_after.txt`):

| 8 bases | EA | ours before | ours after |
|---|---|---|---|
| particle systems / live particles | 35 / 809 | 499 / 7,561 | 433 / 2,428 |
| particle render, map-wide (model) | 0.46 ms | 2.80 ms (at the cap) | 1.91 ms |

The rest (render objects, draws, materials) is unchanged. 2,428 includes EA's own effects on our
objects (the Elven bases' 425). A citadel with every add-on burns more than one recipe's fire (Isengard
209, Mordor 104, Angmar 92, damaged state); the scene counts the healthy citadels. Not measured in
game yet.

**Built (2026-10-05, Max: "I think fires we should reduce on most buildings"; docs/ART.md "Fire budget"):**
a budget per building, 20 live particles where the fire is the building's identity (forges, furnaces,
lava, the citadel crowns, Angmar's key buildings; `sagekit/fire_budget.py` IDENTITY), 6 elsewhere, most
of them none; two small coloured torch systems (SagekitWitchTorch, SagekitColdTorch, 3.0 live each). Our
fire over all recipes 1,534 -> 324 live particles, burning recipes 64 -> 38. Same scene, packs restaged
2026-10-05 (`build/assets/_review_finish/fire_reduce/drawcost_after.txt`):

| 8 bases | EA | 2026-10-04 (budget 60) | 2026-10-05 (20 / 6) |
|---|---|---|---|
| render objects | 332 | 421 | 388 (33 fire rigs fewer) |
| particle systems / live particles | 35 / 809 | 433 / 2,428 | 114 / 1,094 |
| particle render, map-wide (model) | 0.46 ms | 1.91 ms | 0.73 ms |
| a base in view | 2.10 ms | 2.33 ms | 2.27 ms |

1,094 includes EA's own effects on our objects (the Elven bases' 425). Not measured in game yet.

**The check.** `sagekit validate` holds every staged object's healthy state to EA's main-view draws
x 1.10 + 2 and EA's render objects + 2 (a house model and a fire rig). It warned where a building's
fire passed EA's heaviest standing one (330 live particles: Isengard citadel 538, Mordor citadel 421,
Isengard furnace 368); since the fire budget it fails any recipe, and any staged object's fire rig in
any state, over 60 (`sagekit/fire_budget.py`); since 2026-10-05 over its building's budget (20 or 6). All 326 objects pass.

## 16. Session monitor: hard data from every game (2026-10-04)

Max: "frames are dropping when I test 8 players". Until now the logs had 5 s and 60 s windows
(passtimers, renderstats), so a single slow frame could not be seen or explained (§13). Now every
game started with `scripts/play-rotwk.sh` is recorded, and gets a report when it exits:

```sh
scripts/play-rotwk.sh            # play as usual; BFME_MONITOR=0 scripts/play-rotwk.sh turns it off
scripts/monitor.sh last          # afterwards: the summary, and logs/sessions/<date-time>/report.html opens
```

What is recorded (`logs/sessions/<date-time>/`):

| signal | source | rate |
|---|---|---|
| frame time, every frame | wined3d's `+frametime` trace (time between two presents, QPC) with `+timestamp`, in `logs/rotwk-*.log` | per frame |
| CPU of the main thread, the render thread (`wined3d_cs`) and the process | macOS libproc per-thread times, read from outside (`tools/monitor_rec.py`) | 4 Hz |
| resident memory, physical footprint | libproc | 4 Hz |
| GPU device / renderer utilisation (whole Mac) | `ioreg` IOAccelerator | 1 Hz |
| D3DX texture loads, texture creations, effect creations, and the game-thread ms in them | game patch `monitor`: the 12 call sites of the 8 D3DX imports | per frame |
| logic frame (match time), objects in the logic, game mode | game patch: TheGameLogic 0xde412c +0x40, list +0xac / Object +0x8c, +0x110 | 1 Hz |
| 32-bit address space: committed, reserved, largest free block, of 2 or 4 GB | game patch: VirtualQuery walk on its own thread | 0.5 Hz |
| map and players | the game's `Skirmish.ini`, if written during the session | once |
| game-patch log events (display switch, LOD change, faults) | `logs/gamepatch.log` | as logged |

The report lines every slow frame (over 50 ms) up against the other signals and names a cause by a
fixed rule, in this order: **loads** (D3DX time in the frame is at least half of its time over
33 ms), **game thread** (main thread at least 90 % of a core in its 0.25 s sample), **render thread**,
**GPU** (at least 90 %), **memory** (resident +50 MB within 1 s), else **waiting**. It also lists the
five slowest 10 s stretches with both threads' CPU, which is what tells a CPU-bound game thread
from a render-side limit in a long 8-player fight. Example line:
`22:06:34 (match minute 3), 171 ms, main thread 100 %, render thread 57 %, +0 MB resident, ... -> game thread`.

The game-side rows need the rebuilt game patch (`scripts/game-patch.sh`, which installs the DLL into
the game folder: Max's step); until then the report has frames, threads, memory and GPU, and picks
the main thread as the busiest unnamed thread (the new patch names it `bfme_main`).

**Proven without the game** (2026-10-04, engine w10, `tools/d3d9bench.c` at 640x480, msync,
`scripts/monitor.sh bench --secs 20 --objects 2000 --cpu-ms 15 --hitch 90:150[:sleep]`):
9 slow frames injected, 9 found, each 158-171 ms after its hitch began (150 ms of hitch plus the
frame), so the clocks line up within ~20 ms; spinning hitches were classed "game thread" (main
98-100 %), sleeping ones "waiting" (main 41-66 %). Report frame stats against the bench's own:
41.7 vs 41.67 FPS. The game patch's part: `gamepatch/tests/t_monitor.c` (sites, the wrappers'
arguments / stack / registers, frame and object records, a bad list pointer ends the walk at -2).

**Overhead** (A/B on the bench, 6 interleaved rounds of 10 s each, mean app-thread frame ms,
median of the 6; spread in brackets):

| bench | off | trace only | trace + sampler | cost |
|---|---|---|---|---|
| `--objects 1500` (~62 FPS) | 16.25 (16.0-16.4) | 16.21 (15.8-16.7) | 16.16 (15.9-16.4) | none outside the spread |
| `--objects 2500 --cpu-ms 20` (~33 FPS) | 30.68 (30.66-30.83) | 30.73 (30.68-30.85) | 30.71 (30.63-31.01) | +0.1 % (within the spread) |

The sampler itself uses ~2 % of one *other* core (mostly `ioreg`). Game patch `monitor`
(t_monitor, w10): 1.0 us per drawn frame, the object walk 0.16 ms per 3000 objects once a second,
the address-space walk 0.15 ms per 200 regions every 2 s on its own thread: ~0.02 % of the main
thread. All under the 1 % budget.

Limits: GPU utilisation is the whole Mac's (other programs count); a thread's CPU is averaged over
its 0.25 s sample, so a lone 60 ms stall shows diluted (the cause rule then says "waiting");
the map and players come from `Skirmish.ini` (skirmish only); the frame line costs ~45 bytes, so a
game log grows ~5 MB an hour.


### 16.1 Stall sampler: the code of every long frame (2026-10-05)

The 2026-10-05 session (8 players, Mordor spells) had 13 freezes of 472-1362 ms with the main thread at
100 %, the render thread idle and no texture loads, creations or effect compiles in the frame
(`logs/sessions/20261005-084422`). Nothing logged could name the code. Now the game patch's monitor
has a stall sampler (`gamepatch/src/p_stall.c`, `[patches] stalls=1`, on with the monitor): when no
frame has come for 150 ms (`GAMEPATCH_STALL_MS`), a watchdog thread samples the main thread every
2 ms until the frame ends, for at most 4 s. Each sample is SuspendThread, GetThreadContext, a copy
of the top 32 KB of the stack and ResumeThread. After that, the watchdog keeps the return addresses
into the exe. The report (`tools/monitor_stalls.py`) groups the samples by stall and names, for each
stall, the innermost exe function, the call chain (`tools/callstacks.py` Chainer with
`build/rotwk-re/funcs.txt` and the names files), the leaf and the logic phase. `play-rotwk.sh` now
turns logicstats on in monitored sessions, so each sample also carries the GameLogic::update phase.
That costs 16-22 ns per update-module call (t_lstats), an estimated 0.3 % of a core at 1,500
objects. This is logicstats' first use in the game; `GAMEPATCH_LOGICSTATS=0` turns it off.

Measured without the game (engine w10):

| test | result |
|---|---|
| `t_stall`, frames every 5 ms for 0.6 s | 0 samples |
| `t_stall`, a 600 ms spin | 177 samples (one per ~2.5 ms after the first 150 ms), all with EIP in the spinning function and its return address in the stack scan |
| `t_stall`, a 600 ms Sleep | 176 samples in ntdll.dll (an M line), the caller's return address in every one |
| main thread held per sample | 69 us mean, 278 max (t_stall); 62 / 336 (t_monitor); 81-95 (bench) |
| `scripts/monitor.sh stalltest` (d3d9bench, 400 objects, a 400 ms spin in `bench_hitch()` every 90th frame) | 16 hitches, 16 stalls, 1557 samples; innermost exe function 99 % `bench_hitch`, chain `__tmainCRTStartup` > `main` > `begin_frame` > `bench_hitch` |

Cost: while frames come, the watchdog wakes every 10 ms to compare two clocks. During a stall,
each sample stretches it by the hold time, about 3-4 % at ~2.5 ms a sample.

## 17. Logic phase 5: what it runs, and two exact speed-ups (2026-10-05, static + standalone tests)

No logicstats data yet: it was off in the 2026-10-05 08:44 session (`logs/sessions/20261005-084422`,
`logicstats: off` in `logs/gamepatch.log`), so the split below is from the code, not measured.

**What phase 5 is** (GameLogic::update 0x62e4e8, the phase-5 branch 0x62e98b-0x62ec0d; list index =
the module's `getUpdatePhase()`, vtable slot 0x30, the BFME/Zero Hour SleepyUpdatePhase, confirmed by
Open-BFME-2's UpdateModule::getUpdatePhase):
- update list 1 = PHASE_PHYSICS (HordeContain, HorseHordeContain) and list 2 = PHASE_NORMAL, the
  default: ~180 module classes, among them PhysicsBehavior (update 0x79350e), the weapon, spawn,
  stealth, contain and slow-death modules. List 0 (PHASE_INITIAL, phases 3-4) holds the AI update
  modules (AIUpdateInterface 0x66e58f and its subclasses); list 3 (PHASE_FINAL) is phase 6.
- TheAI (0xde4b40) update 0x6fec63: the pathfinder queue 0x6f2364 (a cell budget per step from
  GlobalData+0x11e8, so its work per step is fixed and its speed-up deterministic), then 0xde4928's update.
- 0x629da6 (every phase), TheShroudManager, 0xde435c, TheBuildAssistant, TheLargeGroupAudio, 0x62a2c9,
  TheWeaponStore, TheLocomotorStore, TheVictoryConditions, TheDelayedExperienceLevelGrantSystem,
  0x80f4d3, TheSkirmishAIManager, TheMineshaftPortalNetworkManager, TheTeamFactory
  (names from the subsystem-init strings next to each global).
So phase 5 runs most of the per-object module updates of every object, which is why it is the big one.

**Ranking, Rosetta cost** (leaf profiles `logs/battle-msync2`, `battle-ai1`; standalone per-call cost):
the remaining logic leaves in both profiles are Wine's CRT `sqrt` (the `fsqrt` at msvcr71+0x7054:
1.4 % / 1.3 % of the main thread; 104 call sites incl. pathfinder, HordeContain, physics and AI),
the path-segment cost 0x7658c3 (region 0x765900: 0.6 %; summed per path by 0x765972 for the AI
modules and HordeContain), then the already patched worldcell / distcalc / mat2quat. The x87
fallbacks of the logicmath patches do not matter: in the 10-05 session 0.08 % of mat2quat calls and
0.7 % of worldcell calls ran x87 (1,121 of 1.44 M and 16,536 of 2.30 M in a minute), ~4 ms a minute.
CRT `fabs` costs the same as an inline equivalent (21.9 ns both), so it is not worth replacing.

**Implemented** (`gamepatch/src/p_lmath2.c/.S`, test `t_lmath2`, switches `crtsqrt`, `octile`;
`lmath2:` log line every 60 s and at exit). Only under Wine (msvcr71 must be Wine's builtin: its
results and registers are what is reproduced), else skipped; the game's FPU mode only, else the original.

| patch | site | what | proof (t_lmath2, w10) | per call |
|---|---|---|---|---|
| crtsqrt | IAT 0xbd06a0 (thunk 0xa3cf96 and the direct calls) | Wine's sqrt (fsqrt at 24 bits) as sqrtsd + integer round-to-nearest-even to 24 bits; a 53-bit result exactly on a 24-bit midpoint (where rounding twice can differ: a first version without this check failed 139 k of 2 M test doubles, half of them built near midpoints) runs Wine's sqrt. eax/ecx/edx/xmm0 as Wine's code leaves them. Install-time self-test, 4096 inputs | all 2^32 floats as arguments; 20 M doubles (any exponent, subnormals, exact 24-bit ties and their neighbours, specials); 1 M with the full machine state; 7 other FPU modes all fall back: 0 mismatches | 241 -> 31 ns |
| octile | hash 0x7658c3+0x82; `jmp` at 0x7658c3 (7 B) | max + 0.25 * min of the float \|dx\|, \|dy\| in SSE; argument slots, ecx and Wine-fabs's eax/edx as the original leaves them; overflow, underflow or NaN -> the original | 20 M segments (map positions, cell centres, \|dx\| = \|dy\|, any bits, wide exponents, specials) with the full machine state and both points: 0 mismatches; a deliberate tie-branch bug is caught at once | 402 -> 62 ns |

Expected gain, from the profiles (no phase split yet): sqrt ~2,800 calls per drawn frame (0.67 ms /
241 ns in `battle-msync2`), so ~0.6 ms a frame or ~3.5 ms per logic step across all phases; octile
~700-1,200 calls a frame, ~0.3 ms a frame or ~2 ms per logic step. The AI callers run in phases 3-4,
HordeContain and the pathfinder in phase 5. The next session's `lmath2:` line gives the real call counts,
and logicstats (`scripts/measure-session.sh on`) the per-phase time.


## 18. Spell-cast freezes: the Eye of Sauron, read from the code (2026-10-05, static)

Max: casting spell-book powers (the Eye of Sauron, for one) freezes big games for 0.5–1.4 s. The
2026-10-05 session had 13 such freezes (472–1362 ms, main thread 100 %, render thread idle, no
loads; §16.1), all in logic phases 3–4 by the earlier analysis. New rule from Max: results need not
match EA's, only be the same on every machine running our build (no clocks, thread order or
uninitialised data). Everything below is from the INI (`__patch202.big`, the files the game loads)
and the disassembly; the per-cell costs are estimates, marked as such.

### 18.1 What the cast does

`OCLSpecialPower` (system.ini) runs `SUPERWEAPON_SpawnEyeOfSauron`: one `EyeOfSauron` object at the
target (object/evilfaction/units/mordor/eyeofsauron.ini). Its modules:

| module | effect | update list / phase | changes an AI state? |
|---|---|---|---|
| AttributeModifierAuraUpdate `ModuleTag_FearMe` | every 1 s, enemy `INFANTRY`/`CAVALRY` of rank 1 within 150 get `EyeOfSauronFear` (2 s): ModelCondition `EMOTION_AFRAID`, nothing else | 2 (phase 5) | no (below) |
| AttributeModifierAuraUpdate `ModuleTag_OrcTroopBonus` | every 2 s, allies within 150 get `GenericHeroLeadership` (armour, damage, XP, FX) | 2 (phase 5) | no |
| vision 200, StealthDetectorUpdate (500 ms) | reveals the area to the caster's team, unstealths | 2 | indirectly (18.4) |
| AIUpdateInterface, PhysicsBehavior, LifetimeUpdate 60 s | the Eye itself (NO_COLLIDE aircraft, moves only when ordered) | 0 / 2 | no |
| SpecialPowerModule `ModuleTag_EyeStarter` | nothing triggers it (its AntiCategory line is commented out) | - | no |

**The fear is cosmetic in the logic.** `EMOTION_AFRAID` is model-condition bit 64 (Object+0x10C
bitset). Setting it calls the change notifier 0x68b53c: the Drawable picks a new animation and
AIUpdateInterface::wakeUpNow (0x662552) schedules the unit's AI for the next AI update. Nothing in
the logic reads the bit to change behaviour: the only constant tests of it (Object+0x114 bit 0, at
0x749810 and 0x7568cf) are in cower states that set and clear it on themselves, and the Lua uses it
only to pick a sound (`MordorFighterBecomeUncontrollablyAfraid`). The fear emotions (FearIdle →
`BACK_AWAY`, FearBusy → `AVOID_SCARER`, Terror → `RUN_AWAY_PANIC`; emotions.ini) start only for
objects in `EMOTION_AFRAIDOF_OBJECTFILTER` or from Lua broadcasts (Balrog, Phial, gate damage); the
Eye is in neither. So with ~200 units in the area, no unit changes state and none asks for a path.

**Its cost** (estimate): the cast frame (phase 5) has one object creation, two partition scans of
radius 150, ~200 modifier applications with model-condition changes, the leadership FX on the allies
and a radius-200 shroud reveal: about 5–15 ms. The next phase 3 or 4 runs the ~200 woken AI updates
once: 1–6 ms, or up to ~120 ms if all of them are due a target scan (iterateObjects 0xa3bdb0, about
0.1–0.6 ms each in a crowd) in the same phase. **That is one to two orders below 0.5–1.4 s: the Eye
alone does not add up.**

### 18.2 What else runs in phases 3–4: the pathfind queue

§14 and §17 said phases 3–4 run only update list 0. They also run the pathfind queue:
GameLogic::update calls it (0x6f2364, call at 0x62e69f) at the top of every phase, before the
phase's lists, and TheAI's update calls it again in phase 5. Each call resets its counter and serves
requests (AIUpdateInterface::doPathfind 0x668e94, vt+0x230) while the counter is below
`MaxPathfindCellsPerFrame` = 4000 (gamedata.ini; x100 in a match's first 25 logic frames). The cells
are charged only when a search ends (cleanOpenAndClosedLists 0x6f5519), so the budget is checked
between requests: one request runs to its own end, however long.

### 18.3 The searches and their limits

| search | limit (gamedata.ini, GlobalData offset) | reached from |
|---|---|---|
| findPath (vt+0, 0x6fe7cb): zone check, hierarchical pass, cell search 0x6fd06f | `MaxCellsFindPathLimit` 15000 (+0x1210); after 2000 cells only cells within twice the best distance to the goal expand | queue only |
| findClosestPath 0x6fb869, slot 5 0x6fce1a | soft 2000 | queue only |
| findAttackPath 0x6fc18e / sideways 0x6fde38 | 2500 / 2500 (+0x1214 / +0x1218) | queue only |
| path patch 0x6fc9da | `MaxCellsPatchPath` 2000 (+0x120c) | queue only |
| **getMoveAwayFromPath 0x6fb231** | **none** | privateMoveAwayFromUnit 0x66da5f (AI command 0x34) |
| adjustDestination 0x6fe456 | 400 candidate cells (+0x11f0) + one checkPathCost 0x6f70d5 of ≤500 cells | AI states (phases 3–4) |
| 0x6f74d0, adjustToPossibleDestination 0x6f3c87, melee spots 0x6f37b3 / 0x6fb67a | 200, 400, 50, 200 | AI update (phases 3–4) |

- The PathfindServicesInterface searches are reached only through doPathfind, which only the queue
  calls. No AI state calls them directly; the searches inside AI updates are the small bounded ones
  in the last two rows (worst case a few ms each).
- getMoveAwayFromPath is a goal-less flood (Dijkstra) from the unit until a cell is free of other
  units' goals (checkDestination 0x6f3082) and its box, unit radius plus the other unit's, misses
  every segment of the other unit's path, and of a second unit's (LineInRegion per segment, per
  popped cell). If it finds nothing, privateMoveAwayFromUnit runs it a second time with
  canPathThroughUnits. A horde member forwards the order to its horde (0x66dad7), which then searches
  with the horde's footprint. Issuers of command 0x34: Pathfinder::moveAllies 0x6f503b (inside
  doPathfind, computePath 0x6668ca and computeAttackPath 0x665c33, when the new path is blocked by
  allies: every idle, not-attacking ally on the path's cells gets the order), the exit-production
  line callback 0x6f53af and gates (GateOpenAndCloseBehavior). moveAllies' depth limit is 1
  (0x6f50b4), so the cascade is one level wide: one path, K allies, K floods.
- The open list is a binary heap (push 0x6f4b45 = vector push_back + push_heap, pop 0x6f4af2), each
  cell is tested for open/closed (0x6e7f98, 0x6e7f85) before any work, so a cell is examined at most
  once: no O(n²) list. The cell-info pool grows 256 at a time (0x934538) and never refuses.

### 18.4 Cost per examined cell (estimate from the code)

examineNeighboringCells 0x6f9850 does for each of the 8 neighbours: the open/closed tests, cost
terms, the hierarchical-corridor bitset (+1000 cost outside it), two CRT floor calls, a heap push,
the footprint check 0x6ebaa0 over d x d cells and the crowd scan 0x6ed21e over 1, 9 or 25 cells.
d is the pathfind diameter in cells (0x6eaf79: geometry diameter / 10, capped at 5, or 9 for
HORDE, MONSTER and SHIP): infantry 2 (4 cells), a 30x45 horde box 9 (81 cells). Every unit listed in
a footprint cell costs a relationship test; every unit in the crowd-scan cells costs a relationship
test, two AI-priority calls and a heading test. At ~0.3–0.5 ns per simple instruction under Rosetta
and ~50–150 ns per unit test:

| mover | open ground | in a packed group |
|---|---|---|
| infantry | 3–5 µs per popped cell | 6–12 µs |
| horde (81-cell footprint) | 10–15 µs | 20–45 µs |

### 18.5 Does a queue request add up?

| request | cells | time (estimate) |
|---|---|---|
| ordinary findPath | 100–1,000 | 1–15 ms |
| findPath that fails for a horde (the cell search cannot fit the 9-cell footprint where the zone check said yes, or the goal is walled in by units) | 2,000–4,000 typical, 15,000 at most, + closest-path fallback ~2,000 | 0.06–0.25 s typical, up to ~0.8 s |
| one move-away by a horde in a packed group (no free cell until the group's edge) | 1,000–3,000 | 20–135 ms; twice if the first finds nothing |
| move-away with no free cell anywhere reachable (boxed in, or the other path's corridor covers it) | the whole connected area, 10^4–10^5 | 0.2–4 s, twice |
| one path blocked by K idle allies (moveAllies) | K move-aways | K = 5–20: 0.1–2.7 s |

So a single request, served at the top of whichever phase comes next, can take 0.5–1.4 s, and the
Eye cannot. Its link is indirect at most: the reveal and the leadership let the caster's idle
hordes pick targets, their approach paths run through their own packed army, and moveAllies sends
every idle horde on each path into a move-away flood. The same happens without any spell wherever
idle groups stand packed, such as rally points that new units leave production through. That fits
the timing better than battle size does: all 13 freezes came between minutes 1 and 4.6 of the first
match (logic frames 295–1374, 680–1150 objects), none in its last ~45 s or in the 4-minute second match. The
one thing this reading does not settle is which of the two (failed horde findPath, move-away
cascade) dominates; the installed stall sampler names it from the next game's samples without extra
steps (chain 0x62e69f > 0x6f2364 > 0x668e94 > 0x6fd06f or > 0x66da5f > 0x6fb231).

### 18.6 Fix design, ranked by gain

All of these count cells, units and queue entries, never time, so every machine running our build
does the same thing: the queue runs once per logic phase (six per logic frame, in lockstep), its
requests come in the order the AI updates queue them, and the caps and orders below depend only on
game state. No change is visible in the picture; the gameplay effects are listed.

1. **Cap getMoveAwayFromPath** (0x6fb231) at N popped cells, N = `MaxCellsAdjustDestination` (400,
   GlobalData+0x11f0) or a constant; at the cap it returns no path, and the second attempt is capped
   the same way. Removes the only search with no limit: worst case per move-away from seconds to
   ~20 ms (400 x 45 µs). Gameplay: a unit deep inside a packed group does not step aside; the mover
   keeps its path and waits or squeezes past as it does now when a move-away finds nothing.
2. **Queue the move-aways.** moveAllies sends at most M orders per request (M = 2, say) and queues
   the rest in the order it finds them on the path; later queue runs serve them inside the 4000-cell
   budget. Gameplay: allies step aside one to a few phases later (up to ~0.1 s). Together with 1,
   the cascade term (K x flood) becomes a few ms per phase.
3. **Lower `MaxCellsFindPathLimit`** 15000 → 5000 (gamedata.ini, an INI change that ships in our
   archive; nothing to patch). The worst failing horde findPath falls from ~0.7 s to ~0.23 s.
   Gameplay: a route needing more than 5000 cells (rare with the hierarchical corridor; long mazes
   on big maps) gets the closest-path fallback and re-paths on arrival.
4. **Exact per-cell speed-ups**, bit-for-bit the same results (the logicmath pattern, §10.5):
   Object::getRelationship once per (player pair) per search instead of per unit test, the two CRT
   floor calls as SSE (as worldcell), and the footprint loop skipping cells with no units. Expected
   1.5–3x on every search, queued or not. No gameplay change.
5. A per-phase cap on move-away searches ordered by object ID is covered by 2. "One search per
   horde" already holds: members forward move-away orders to their horde, and hordes path as one.

Not chosen: a time budget (differs between machines, so it would desync), and resumable A* across
phases (a large patch; 1–3 bound the single request, which is what freezes).

## 19. Logic that grows with the unit count: ranking, and two exact speed-ups (2026-10-05, static + standalone tests)

Big 8-player games: what on the main thread scales badly with n units, read from the exe, Open-BFME-1/2
and the Zero Hour source. Big battle = 1,500 units, ~1,000 of them moving, ~60 hordes of 25; logic
5 steps/s. Measured per-call costs come from standalone tests under Wine (engine w10) running the
exe's own code; per-step totals are **estimates** from those costs and the counts in brackets.

| rank | system | shape in n | per logic step at n = 1,500 (estimate) | evidence |
|---|---|---|---|---|
| 1 | shroud redraw on cell crossings | O(crossings x R²): every 40-unit cell crossing redraws the unit's vision circle (R = 8-15 cells, 200-700 cells) plus up to 3 counter-layer circles and one queued undo | 3-20 ms (~300 crossings x 2-5 circles x 2-15 µs) | circle r=10, 1 vision bit 1.95 µs; r=15, 4 bits 15.5 µs (t_shroud); per cell and player bit a virtual predicate call and a call to 0xb52e10/0xb52ec0/0xb52bf0 |
| 2 | range scans (AI mood targets, auras, fear, emotion tracker, stealth detection, hunts) | O(n·k), k = units in the scan radius, so O(n²) in a clump; RotWK sets AttackPriority on nearly every unit, so mood scans take the full-radius, sorted path | 3-10 ms (~300-700 queries of ~20 µs; distance calls 3,800 per step at 1,100 objects in the 10-05 session, ~2-4x that in a 1,500-unit battle) | query in a 1,000-unit battle, r=300: 19.7 µs as installed (t_scan); 0xa3c4e0 walks 21 per-player quadtrees, 1 result alloc + log2(k) vector growths per query |
| 3 | HordeContain formation | O(m) per horde every ~15 frames (slot position: sqrt, CRT acos, fsin, fcos, terrain query; updateGoal per member); an O(m²) member-slot swap (0x2435F0 in BFME1) of unknown frequency | 1-3 ms | Open-BFME-1 HordeContain; rate unconfirmed |
| 4 | PhysicsBehavior | O(n): ~2 terrain-height queries, integration, pitch/roll atan2 for some | 1-2 ms | ZH PhysicsUpdate.cpp:627-924; RotWK update not mapped |
| 5 | attribute modifiers and auras (beyond their scans) | O(hits) per pulse: name hash, linear search of the target's modifiers, one AsciiString per hit; fortress auras with Range 99999 hit every unit every ~2 s | 0.5-2 ms | Open-BFME-1 AttributeModifierAuraUpdate.cpp:198-272 |

Stealth: StealthUpdate is O(1) per stealthed object per frame, detectors (~10 at DetectionRange 800,
every 3 frames) ~2k candidates a step: under 0.5 ms. ZH's per-cell collision pairs (O(Σk²))
are absent from BFME1's binary by Open-BFME-1's reading; not verified in RotWK. Spell reveals: one circle when the reveal
appears and one undo when it goes; a growing reveal redraws on every change (~530 cells at r=500).

**Implemented** (code `gamepatch/src/p_shroud.c`, `p_scan.c`, `gp_scale.h`; tests `t_shroud`, `t_scan`;
switches `shroudspan`, `scantree`, on by default; log lines `shroudspan:` / `scantree:` every 60 s and
at exit with their counts). Both give the original's results bit for bit, so they are deterministic
across machines and LAN-safe even if only one player has them on.

| patch | site | what | proof | measured |
|---|---|---|---|---|
| shroudspan | `jmp` at 0xb4fc80, 0xb4fd20, 0xb4fdc0 (hash-checked with their helpers 0xb4e460, 0xb52e10, 0xb52ec0, 0xb52bf0 and the constant-true predicate 0x5879b0) | the span's per-cell, per-player-bit counter update inline; the original per-cell function still runs where the cell's visible status changes (counts 0, 1, 0xfffe, 0xffff: object status caches, the client refresh callback), in the same order; any other predicate is called as before | 400 k random spans (clipped, empty, reversed, any 20-bit mask, a recording predicate, amounts past both clamps) and 20 k whole circles through the original raster 0xb50100, each against an untouched copy on an identical grid: 0 mismatches in grid, object caches and callback/predicate call logs | span of 21 cells 108 -> 38 ns; circle r=10, 1 bit 1.95 -> 0.65 µs; r=15, 4 bits 15.5 -> 4.45 µs |
| scantree | the walk's call at 0xa3c659 (0xa3c4e0, 0xa3a860, append, filter chain, both 2D distance tails hash-checked) | the quadtree walk iterative and in the original's order; the centre and bounding-circle 2D distances inline in SSE after the same getter calls (x87 replica of the original arithmetic outside the safe range or in another FPU mode); filter chain and append fast path inline; region queries run the original walk | 200 k random queries (distance types 0-3, 0-3 filters, sorts, regions, clustered worlds, huge/tiny/denormal/inf/NaN values) and 70 k in 7 other x87 modes, against the untouched copy through the game's own 0xa3c4e0 and linkNode-built trees: identical result vectors and getter/filter call logs | per query (1,000-unit battle, r=300, circle, 2 filters, sorted, 119 candidates): 71.6 µs unpatched, 19.7 µs with distcalc (as installed), **8.6 µs** |

A finding on the way: with a NaN distance in a sorted result, EA's sort (0xa3a6b0/0xa3a700) runs
past the vector and its output depends on the memory around it, original against original. It needs
NaN positions, so it should not occur in play; t_scan compares those results unsorted.

Expected in game (estimate, from the shares above): shroudspan saves ~65-70 % of rank 1, 2-14 ms a
logic step; scantree ~55 % of a query, 1.5-5 ms. The next session's `shroudspan:` and `scantree:`
lines give the real span, cell, walk and candidate counts per minute to replace these estimates.
Next candidates: getClosestObject 0xa3bdb0 (102 call sites: a best-first search with a static heap
vector, CRT floor/ceil per improvement), the 3D distance functions 0xa3a7d0/0xa3aeb0 if the
`scantree:` line shows many table calls, and the horde slot swap once logicstats names its rate.

## 20. The pathfinder: how a search works, a benchmark on the game's own code, and four fixes (2026-10-05, standalone tests)

Follows §18. Max's rule for this work: results need only be the same on every machine running our
build (no time, thread order, addresses or uninitialised data); they may differ from EA's.

### 20.1 The algorithm, from the code

- **Grid.** One `PathfindCell` (16 bytes: info pointer, flags with type, layer, pinched and road
  bits) per 10x10 world units, stored as columns (`pf+0x10[x] + 16*y`); bridges are extra layers.
  A 4800-unit 8-player map is 480x480 = 230 k cells. Per-search state lives in a 60-byte
  `PathfindCellInfo` taken from a pool (0xdea438, grows 256 at a time) when a cell is first touched.
- **Open list: already a binary heap** (STL `push_heap`/`pop_heap` on a vector of cell pointers,
  0x6f57a1 / 0x6f4af2, O(log n)), keyed by the info's 16-bit total cost. A cell is skipped once it is
  open or closed (no decrease-key), so each cell is pushed at most once. No sorted-list problem to fix.
  The compare reads cell -> info -> cost (two dependent loads per compare, infos scattered over the
  pool: the heap is cache-unfriendly, but it is not where the time goes, below).
- **Costs.** Integers: 10 orthogonal / 14 diagonal, +14 pinched, turn penalties, +10 per blocked
  footprint cell, +1000 outside the hierarchical corridor, +10 in the AI danger grid, plus the crowd
  cost. Heuristic 10·max + 5·min of |dx|, |dy| (it overestimates diagonals, so the search is greedy
  rather than optimal). Every 16th expanded cell a jump-ahead step (0x6f6d57) tries a straight run
  toward the goal (its own counter 0xde4b14, limit MaxCellsToExamineTowardsGoal 25000).
- **Per expanded cell**, the search step 0x6f9850 does for each of 8 neighbours: getCell (a call),
  the open/closed tests, a passability test, **checkForMovement 0x6ebaa0 over the unit's
  (2r+c)² footprint** (a getCell call per footprint cell; per unit standing there a relationship
  call and up to four more game calls), cost terms, two CRT floor calls for the danger grid, and
  **the crowd cost 0x6ed21e over the same window** (per unit heading there a relationship call, two
  AI-priority calls, a "moving" call, and for movers two x87 distances with CRT sqrt, two x87
  divides by locomotor speeds and a terrain height through two virtual calls). Footprints: 1 cell
  for small infantry, up to 9x9 = 81 for hordes, monsters and ships (§18.4).
- **x87 under Rosetta:** the crowd maths (fsub/fmul/fadd, sqrt, fdivr), the cliff height test
  (fabs) and the floor calls; the rest is integer code and calls. Memory: the cell columns are read
  9-81 times per neighbour (once per footprint window that covers them), infos are scattered.
- **Worst case per search** (gamedata.ini): findPath gives up after MaxCellsFindPathLimit = 15000
  new cells; findAttackPath 2500, path patch 2000, adjustDestination 400; the move-away flood
  getMoveAwayFromPath 0x6fb231 has **no limit**. Found on the way: the jump-ahead counter 0xde4b14
  and the infos that stay on cells (units', obstacles') carry state from one search into the next,
  so a search depends on the searches before it; that is the same on every machine (same history),
  so it is not a desync source, but a test must reset it (t_path does).

### 20.2 The benchmark: `gamepatch/tests/t_path.c` (+ `t_path_world.c`)

It runs the exe's own pathfinder code under Wine (engine w10, the game patch's floor and sqrt in the
imports as installed): the search loop of findPath 0x6fd06f around the game's pop, closed list,
layer check, search step, info pool and clean-up, on a synthetic 480x480 map (lakes, cliffs, 260
buildings with obstacle infos, 8 walled bases, one closed) with 6400 units in four battle clusters,
one of them a packed block of 1600 standing units. Only what lies outside the pathfinder is stood in
for: relationship, "is moving", AI priority, locomotor speed, three blocker lookups, footprint
parity, three terrain height methods. Movers have footprints of 1, 3, 4 and 9 cells. Those
stand-ins cost a few ns, the game's own versions far more, so the numbers below understate the
original's per-unit cost and the gain of 20.3.

Results (24 searches, median of 3 runs each, ms per search, original -> pathfind patch; the machine
was shared with five other jobs, so the spread is about ±30 %):

| searches | cells expanded (mean) | mean | slowest | per expanded cell |
|---|---|---|---|---|
| across the map | 2,501 | 5.84 -> 3.75 | 18.8 -> 9.6 | 2.3 -> 1.5 µs |
| into a battle | 11,039 | 13.6 -> 12.4 | 27.8 -> 20.7 | 1.2 -> 1.1 µs |
| unreachable goal (runs to 15000 cells) | 12,102 | 15.2 -> 12.8 | 28.0 -> 20.8 | 1.3 -> 1.1 µs |
| unreachable goal, limit 5000 (20.5) | | 12.8 -> 6.7 | | |

### 20.3 pathfind (exact, on): the two footprint scans memoised per search

`gamepatch/src/p_path.c`. checkForMovement and the crowd cost rewritten with the original's control
flow and writes, called from the search step and the jump-ahead step only (4 call sites), with: the
ground getCell inline; every per-unit and per-mover answer (relationship, moving, priority, speed,
parity) asked once per search, kept in a memo indexed by object ID (verified by pointer equality,
never dereferenced); the crowd distances and divides in SSE single precision, which is what the x87
code gives in the game's FPU mode (other modes run the original); the terrain height the original
computes and never reads is skipped. The memo ends at the clean-up every search ends with (0x6f5519)
and when a search step starts with at most one closed cell or another mover. Proof (t_path [2]-[4]):
200 k direct calls of each function, original vs patched, same results and the same bytes in the
movement-info struct; 24 whole searches give the same popped-cell sequence, path, cost, cell count
and final lists; again in a second world with another memory layout and pool order: identical. Gain
in the bench x1.1-1.6, more in the game (the real per-unit calls are dearer than the stand-ins).
No gameplay change.

### 20.4 moveawaycap (changes logic, on): the move-away flood stops after 400 popped cells

The flood's pops (call 0x6fb626) go through a counter; a new flood is one whose closed list is
empty at a pop. At 400 it ends with no spot, as when the game finds none; privateMoveAwayFromUnit's
second attempt is capped the same way. t_path [6] runs the flood (goal-less search to the first
cell whose footprint no other unit stands in or heads for, off the blocked path's row) from inside
and at the edge of the packed block: from the edge every footprint found a spot within 63 cells;
from deep inside, 16-843 cells. Caps 200 / 400 / 800 / 1600: 41 / 43 / 47 / 48 of 48 found one,
exactly the ones the uncapped runs predicted, repeated runs identical. At ~45 µs per cell for a
horde in a crowd in the game (§18.4) 400 cells is ~18 ms, against seconds uncapped.
**Gameplay:** a unit deep inside a packed army no longer steps aside for a path through it (the
mover waits or squeezes past, as when no spot exists); units at the edge still do.

### 20.5 moveawayqueue (changes logic, on) and the INI limit

- `gamepatch/src/p_path2.c`: moveAllies' order call (0x6f550b) gives at most 2 move-away orders per
  mover per pathfinder-queue run; the rest wait in a FIFO of object IDs and 2 are given at the start
  of each later queue run (hook at the queue's entry 0x6f2364, which runs at the top of every logic
  phase); an ally or mover that has gone is dropped. t_path [7] checks the order log (who, for whom,
  where, which run) against the expected one, twice. **Gameplay:** with K allies on a new path, the
  3rd and later step aside 1-K/2 phases later (~0.03 s each); a saved game drops waiting orders.
- `MaxCellsFindPathLimit` 15000 -> 5000 in the group pack (`tools/make_group_pack.py` EDITS; built
  in `build/group-pack/rotwk/install/`, not installed). The worst failing findPath halves in the
  bench (above). **Gameplay:** a route needing more than 5000 new cells (long mazes on big maps;
  rare with the hierarchical corridor) gets the closest-path fallback and re-paths on arrival.

### 20.6 Not done

- **Budget inside a queue request** (§18 fix 2; **done 2026-10-05, §21**: the search is parked on a
  fiber with its state saved by cell, so nothing is repeated): the 4000-cell queue budget is checked between
  requests. Cutting a request and re-queueing it repeats its work from scratch, and a request bigger
  than the budget would never finish unless it runs uncapped when first in a run, which brings back
  the same worst case; real suspend/resume needs the open/closed lists kept across phases while the
  synchronous searches in AI updates use the same lists. With the 5000 limit, one queue run is at most
  ~4000 + 5000 cells. Left for later.
- Per-horde path sharing: already the case (members forward move-away orders to their horde, and a
  horde paths as one, §18.3). A precomputed static cost grid would only replace the cheap static
  part of the footprint test; the memo removes the dear part.

Install: `scripts/game-patch.sh` (the three switches `pathfind`, `moveawaycap`, `moveawayqueue` in
`gamepatch.ini`), group pack `scripts/install-mod.sh rotwk build/group-pack/rotwk/install`; revert
with `scripts/game-patch.sh --revert` and `scripts/install-mod.sh rotwk --revert` (puts the previous
pack back from its `.premod.bak`). The exit log gives
the counts (`pathfind`, `moveawaycap`, `moveawayqueue` lines).

## 21. Path searches split over logic phases: pathsplit (2026-10-05, standalone tests)

Follows §18 and §20. With the move-away cap and the 5000-cell limit, the worst single frame left is
one long queued search: a failing horde search from inside a packed army (5000 cells, ~4,400
popped) runs to its end in one logic phase, and two can share a phase. Rule as in §20: the results
need only be the same on every machine running our build.

### 21.1 What the sources show

EA's *Zero Hour* source (`AIPathfind.cpp`, read for understanding, nothing copied): the queue
(`processPathfindQueue`) checks its cell budget between requests, and the cells are charged in
`cleanOpenAndClosedLists` when a search ends; every search uses the pathfinder's one open list and
one closed list and the per-cell `PathfindCellInfo` that also holds the units standing on or
heading for the cell; a search also keeps state on the pathfinder (`m_isTunneling`,
`m_ignoreObstacleID` set by `doPathfind`, the zone blocks' corridor flags from the hierarchical
pass). RotWK 2.02 (the exe, with Open-BFME-2 for names) is the same with these differences:

| state a search keeps | where | who else writes it |
|---|---|---|
| open list: a binary heap of cell pointers | vector pf+0x1d1f0 | every search |
| closed list, linked through info+0x34/+0x38 | pf+0x34 | every search; clean-up releases the infos |
| per cell: parent (+0x8, an info), +0xc (a cell), costs (+0x10, +0x12), flags bit 0, open 0x8, closed 0x10 (+0x2c) | the cell's info | every search on that cell |
| start-blocked flag / ignored obstacle | pf+0x38 / pf+0x48 | each search sets its own; doPathfind sets pf+0x48 for its request |
| via points (12-byte entries; the heuristic and the search step read them) | vector pf+0x1c1cc | findPath's hierarchical pass fills it; move-away and others clear it |
| corridor flags of the zone blocks | pf+0x460+0x1ba38, byte +0x34 of each 0x44-byte block | findPath / closest / attack paths set them, move-away sets all (0x6fb287) |
| jump-ahead counter | 0xde4b14 | every search with a goal |

- The info release (0x9347c6) skips an info that is flagged open or closed or linked in a list, so
  a running search's infos are safe from units moving; an info with no flags is released when its
  last unit leaves. The goal cell's info is read on every iteration (its x, y) but has no flags
  until the search reaches it.
- Two queues: a priority list (pf+0x1c9e8, vt+0x234, served first up to half the budget) and the
  requests (pf+0x1c1e0, `doPathfind` vt+0x230 at 0x6f2570). The queue runs at the top of every
  phase (0x62e69f) and a second time in phase 5 from TheAI's update (0x6fec66).
- Who searches while a queued search could be in flight: the AI updates' synchronous searches
  (adjustDestination 0x6fe456, checkPathCost 0x6f70d5, 0x6f74d0, adjustToPossibleDestination
  0x6f3c87, melee spots), move-away floods (gates, production exits, the moveawayqueue FIFO at the
  queue's start), and inside `doPathfind` itself: patchPath, attack paths, moveAllies' floods for
  other units. findPath (vt+0) and findClosestPath (vt+4) are reached only from `doPathfind`.

### 21.2 Design

`gamepatch/src/p_path3.c`, switch `pathsplit` (on), `pathsplit_cells` = 1000.

- **One request on a fiber.** The queue's call of `doPathfind` (0x6f2570) runs it on a fiber
  (`CreateFiberEx`, 1 MB). findPath's cell search (0x6fd06f) and findClosestPath (0x6fb869) take
  their pops from the patch (0x6fd9a1, 0x6fdc0c, 0x6fbdb3, 0x6fc060). Every pop of every search is
  counted (0x6f4af2 entry). When the fiber has popped `pathsplit_cells` cells in this phase, the
  search is **parked** and the queue run ends; the next phase resumes it before serving anything
  else (0x6f24de, after the priority list). Phase 5's second run shares the phase's count, so no
  drawn frame pops more than the budget on the fiber. One request is in flight at most.
- **Parked = clean pathfinder** (chosen over routing the AI's synchronous searches through the
  queue, which would change what dozens of AI states see at once, and over a second set of lists,
  which the per-cell infos shared with the units rule out): the open heap and the closed list are
  emptied and every cell's search fields saved by cell (parent as a cell); closed infos are
  released as the game's clean-up does (0x934806), open ones stay on their cells as the game leaves
  them. Saved too: pf+0x38, pf+0x48 (left at 0, as `doPathfind` leaves it), 0xde4b14, the via
  points and the corridor flags. Everything that runs between phases sees what it would see
  between two requests. **Resuming** puts the state back by cell, in the same heap and list order
  (a cell whose info was released meanwhile gets a new one, the goal's included), and restarts the
  pathfind patch's memo (units have moved).
- **Only the unit's own search parks, and only where every object the fiber holds is the unit**:
  not inside `doPathfind`'s approach/attack branch (0x6668ca keeps the victim; a marker around its
  call at 0x6690c3), never in searches for other units (move-away floods), attack paths, path
  patches or the hierarchical pass: those run to their end and count against the phase.
- **The unit while parked**: its waiting-for-path flag (ai+0x3b1, cleared by `doPathfind`) is set
  again and its ID put back at the queue's head, so its AI, and the pathfinder's snapshot
  (0x6f3606, which covers both queues), see a queued request.
  Before resuming: the unit gone (its ID no longer gives the same object) or its request cancelled
  (flag cleared, as `destroyPath` does) → the search is dropped, as the game drops a queued request
  whose unit no longer waits (fiber deleted, its hierarchical path freed, lists already clean).
  Request fields changed (a new order) → the old request finishes, the new one is served by the
  queue entry. Otherwise the flag is cleared again. A map reset (0x6f5a5e) drops a parked search.
  Once the request is done, its queue entry finds the flag cleared and costs nothing.
- Counts only (popped cells, phases), so every machine parks and resumes at the same cell, and
  the pathfinder's snapshot (pf+0x38, pf+0x48, the queues) is the same between players with the same
  setting. The stall sampler (p_stall.c) reads the fiber's stack when the main thread is on it.

### 21.3 Proof: `t_path` [8] (`gamepatch/tests/t_path_split.c`)

Requests served the way the patched queue serves them on the §20.2 world (480², 3,200 units, a packed
block of 800): 24 searches (across the map, into battles, unreachable, limit 5000) and 8 horde
searches (9-cell footprint) from inside the packed block to the closed base. Between phases: a
short search or a move-away flood on the main stack, then the corridor flags, via points, jump
counter, pf+0x38 and pf+0x48 scrambled.

| check | result |
|---|---|
| every request against the same request whole (popped-cell sequence, path, cost, cells, final lists); budgets 500 / 1000 / 2000, via points none / 2, two memory layouts | 0 of 32 differ in all 12 cases (95 parks at budget 1000) |
| most pops on the fiber in one phase | exactly the budget |
| results and per-phase pop counts, layout 0 against layout 1 | identical |
| test sensitivity: the patch with one restore left out | corridor, via points, start-blocked flag, jump counter, list order: results differ; goal info: crash. Flag bit 0 left out: no difference (the search step clears it before use) |
| unit gone / request cancelled / map reset while parked | dropped, lists clean, the unit back at the queue's head while parked, the next request identical |
| request fields changed while parked | finished, identical, the unit stays waiting |
| inside the approach marker; another unit's search on the fiber first | not split (the other unit's 3,771 pops run whole), results identical |
| the game-side entries (both pop stubs with stand-in frames, run start, resume point, reset, approach marker, request call) | the right frame fields and registers (xmm0-7 kept across parks too: the pop's call tree never touches them), same pops whole and parked |

### 21.4 Time per frame, and the budget

Same 32 requests, ms per queue run (searches only, least disturbed of 3), test machine shared:

| | runs | pops per run, mean / most | slowest run | a path ready after (runs, mean) |
|---|---|---|---|---|
| whole (as EA) | 25 | 4,315 / 6,141 | 6.88 ms | 11.3 |
| split, 500 | 229 | 471 / 500 | 1.24 ms | 100.9 |
| split, 1000 | 120 | 899 / 1,000 | 2.19 ms | 52.8 |
| split, 2000 | 70 | 1,541 / 2,000 | 3.76 ms | 30.3 |

The bench's stand-ins cost ~1.1 µs per pop. In the game a pop of a horde in a packed army costs
more: §18.4 estimated 20–45 µs (before the §20.3 memo, so an upper bound). **Worst frame, estimate:
whole 6,141 pops = 0.12–0.28 s; split at 1000 = 20–45 ms, at 2000 = 40–90 ms.** Parking and
resuming cost ~5 % of a run in the bench. The budget is 1000: at the upper per-pop estimate one
phase stays near one 30 FPS frame. The price is throughput when the queue is saturated: this
test queues 32 long searches at once and a path then takes 4.7× as many phases (2.7× at 2000);
an ordinary request (under 1,000 pops) is never split. `pathsplit_cells` sets it (every LAN player
alike).

### 21.5 Gameplay effect

- A search longer than the budget arrives 1–5 phases later (5000 cells of a horde: ~5 phases,
  ~0.15 s at 30 FPS); requests queued behind it wait as long. The unit stands still meanwhile:
  `computePath` drops the old path before searching, as before, only now for longer.
- The path starts where the unit was when its search started.
- A unit that dies, is stopped or gets a new order while its search is parked: as in 21.2.
- LAN: changes the game logic; every player needs the same `pathsplit` and `pathsplit_cells`
  (the shared bundle has them). Replays recorded with it need it on.

Install: `scripts/game-patch.sh` (with `pathsplit=1`, `pathsplit_cells=1000` in `gamepatch.ini`);
off: `pathsplit=0`; revert all: `scripts/game-patch.sh --revert`. Exit log line `pathsplit`:
requests, parks, resumes, drops by cause, most phases for one request, most pops in one phase,
restore anomalies (expected 0).
