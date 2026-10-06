# Above 30 FPS and more cores: a roadmap

Max's two goals: more than 30 FPS ("the big one"), and using more than one core. This is the
design, written 2026-10-06 from the exe (RotWK 2.02, `build/rotwk-re`), the logicstats data of the
10-05 8-player match and the existing patches. Nothing here is built or installed. Open-BFME-1/2 and
EA's Zero Hour source were read for understanding only; nothing of theirs is copied.

**In short**
- The game draws one frame per logic *phase*: 6 phases per logic step, 5 steps a second, hence 30
  FPS, and below 30 the game itself slows. Units move 5 times a second; the picture is smooth
  because drawables already blend between logic steps by `phase / 6` (engine+0x3c, §2.2).
- So **more than 30 FPS needs no change to the logic**: draw extra frames between phases with that
  blend driven by the clock instead of the phase count (§2.4). Client-only and LAN-safe.
- In 8-player battles the logic costs 32.5 ms per step, but **unevenly**: phase 5 alone 12 ms (up
  to 26), phases 1, 2 and 6 under 2.5. Evening that out costs no thread and removes most drops
  below 30 (§4 step 1).
- **Running the logic on worker threads deterministically is mostly not realistic** for the big
  per-object updates (AI, animals, hordes, weapons): every one writes shared state (one logic RNG,
  update lists, object creation, the pathfinder, drawables). A few pieces can (§3.3); client-side
  work can (§3.2). Exact single-thread speed-ups stay the main lever for the logic.
- C++ in our DLL works with mingw g++ if game classes are only ever plain structs to us (§5).

Contents: 1 measured split · 2 frame loop and fps60 (A) · 3 threads (B) · 4 roadmap (D) ·
5 hybrid C++ (C) · 6 decisions for Max.

## 1. Where the main thread goes in an 8-player battle (measured)

Session `logs/sessions/20261005-182416` (2026-10-05 18:24, 81 min, mp eastfarthing hills, 1 human
+ 7 AI, up to 1,328 objects; game patch with logicstats, passtimers, renderstats, particlestats
on; machine: the M3 Max of PERFORMANCE.md). Aggregated from `logs/gamepatch.log` over the match
windows (logicstats: 124 windows of 30 s with ≥ 100 logic steps; passtimers: 862 windows of 5 s
with ≥ 100 frames) by a scratch script, steps-weighted.

| | per logic step (6 drawn frames) | per drawn frame |
|---|---|---|
| frame time (passtimers windows) | | p50 33.7, p90 35.7 ms: the 30 FPS cap holds in most 5-s windows |
| render passes (RenderViews + UpdateShadowMap + RenderUI, inclusive) | | p50 9.0, p90 14.0 ms |
| game logic, all six phases | 32.5 ms (heaviest quarter of windows 38-56 ms) | 5.4 ms on average, but uneven (below) |
| everything else: GameClient::update outside the draw, input, audio, network, Present, passtimers' own ~2 ms, and the limiter's wait | | not measured per frame (the limiter spins with `Sleep(0)`, so "main thread 97 % busy" includes the wait) |

The logic per phase (ms per logic step, i.e. the extra time of the one frame that runs it):

| phase | what runs (§14, §17; GameLogic::update 0x62e4e8, list loop 0x62e9d4) | mean | heaviest quarter |
|---|---|---|---|
| 1 | logic frame +1, script engine (0xde3bac, 0.69), 0xde46a8 | 2.1 | 2.7 |
| 2 | ThePartitionManager 0xde4354 (0.25), TheCollisionManager 0xde4360 (0.88), the per-object loop 0x6260e1 | 1.9 | 2.8 |
| 3 | update list 0, first half by index (AI) | 6.6 | 7.9 |
| 4 | update list 0, second half | 8.6 | 11.1 |
| 5 | lists 1 and 2 (6.0 ms of modules), then 12 subsystems: TheShroudManager 0xde4358 1.88, 0xde4938 0.90, TheAI 0xde4b40 0.86, 0xde3be8 0.36 ... | **12.0** | **17.0** (single windows up to 26) |
| 6 | list 3 | 1.4 | 2.2 |

Every phase starts with the pathfind queue (0x6f2364 at 0x62e69f), included above.

Update-module classes that took the most time (logicstats keeps each window's top 12, so the tail
is cut; class names from the INI module name each vtable's factory registers, §3.3):

| update fn (vtable) | class | ms per step | calls per step | µs per call |
|---|---|---|---|---|
| 0x66e58f (0xc6a5a8) | AIUpdateInterface::update | 5.31 | 303 | 17.5 |
| 0x882058 (0xc5e378) | **AnimalAIUpdate** | 3.61 | 321 | 11.2 |
| 0x872efc (0xc5d3e0) | HordeContain | 2.26 | 26 | 85 |
| 0x89e2d0 (0xc66d3c) | HordeAIUpdate | 1.86 | 20 | 92 |
| 0x88f554 (0xc629bc) | FireWeaponUpdate | 1.49 | **1.0** | **1,460** |
| 0x8ae020 (0xc6ac9c) | WorkerAIUpdate | 1.05 | 32 | 33 |
| 0x8b73b7, 0x8af246, 0x88caf5, 0x8b5738, 0x8a1b9f, 0x85f28a | AISpecialPowerUpdate, LargeGroupAudioUpdate, DozerAIUpdate, EmotionTrackerUpdate, ProductionUpdate (by address range), BezierProjectileBehavior (by address range) | 0.27-0.46 each | 4-147 | 2-60 |

So in a big battle the frame budget is roughly: render 9-14 ms, logic 1.4-12 ms depending on the
phase (17-26 ms in the worst windows), and an unmeasured "other". A frame drops below 30 FPS when
a heavy phase meets a heavy render: phases 3-5 carry 83 % of the logic. Earlier
profiles put the rest of the frame (client update, Present, d3dx9 outside the passes) at about
7 ms in the 09-24 AI battle (§8: 18 % of a 42 ms frame); that needs a per-frame measurement now
(roadmap step 0).

Two consequences for everything below:
- **The 30 FPS frames already have slack on average** (9 + 5.4 + ~7 ≈ 21 ms of 33), but not on
  the phase-3/4/5 frames. Spreading the logic evenly over the six phases is worth more than any
  thread for the drops, and is the precondition for drawing more than 30 frames.
- **In a LAN game the slowest machine sets the speed.** On the brother's 13" M1 (4 P + 4 E
  cores, ~1.3-1.4x slower per core than the M3 Max under Rosetta, estimated from public
  single-core scores) the same battle is ~45 ms of logic per step and ~12-19 ms of render. Single-
  thread speed-ups help both machines; thread-level parallelism helps the M1 less (2 free P-cores
  after the game thread and Wine's render thread).
## 2. The frame loop, and what is tied to the drawn frame (part A)

Static analysis of the RotWK 2.02 exe (`build/rotwk-re/text.asm`, vtables in the PE file), with
Open-BFME-1/2 and EA's Zero Hour source read for names. Globals: TheGameEngine 0xde4324,
TheGameLogic 0xde412c, TheGameClient 0xde4388, TheNetwork 0xde4468, TheDisplay 0xde4418,
TheInGameUI 0xde4830, TheFXParticleSystemManager 0xde3744, TheAudio 0xde42fc. FramesPerSecond
0xd9f60c = 30 and LogicFramesPerSecond 0xd9f608 = 5, both set only at 0x644fa6/0x644fb0 (frames
forced to logic x 6).

### 2.1 One drawn frame

1. **GameEngine::execute** loop (0x639cf8) calls Win32GameEngine::update 0x44181f, then the
   **limiter** 0x63a196-0x63a1f8: target ms = 1000 / (GameEngine+0x0c max FPS x LogicTimeScale
   0xd9f498), spun with `Sleep(0)` + `timeGetTime` (last time 0xde4318). In network games the
   scale is recomputed at phase 1 from the network's pacing (net vt+0x5c / vt+0x58). The limit is
   skipped for 6 client frames after a skipped one (0xde4308 + 6). `limiter=1` (§10) replaces the
   spin with `Sleep(1)`.
2. **Win32GameEngine::update** 0x44181f: GameEngine::update, then Windows messages (a `Sleep(5)`
   loop while minimised).
3. **GameEngine::update** 0x6325a0:
   - 0xdef548 vt+0x28, ScriptEngine 0x604189, the script freeze test 0x603452;
   - **client pass** vt+0x9c = 0x632409: if GameClient+0xc8 ("logic advanced") the client frame
     +1 (GameClient vt+0x7c / vt+0x38); APT player; `shouldSkipClientFrame` 0x63239d (network:
     we are ahead, skip the whole client pass including the draw); else Radar,
     **GameClient::update 0x64849e** (drawable updates, particles, UI, then W3DDisplay::draw),
     MessageStream 0x7128c3, keyboard, audio, network vt+0x3c;
   - then the **phase**: engine+0x34 += 1; past 6 it becomes 1. engine+0x38 = 30 / 5 = 6;
     **engine+0x3c = phase / 6** (0x63256f, clamped 0..1);
   - **engine step** vt+0x98 = 0x6329b0(phase): only phase 1 asks the network (and the pause
     flag GameLogic+0x124); if logic is refused, GameClient+0xc8 = 0 and GameEngine::update puts
     the old phase back, so the next frame tries phase 1 again. Otherwise **GameLogic::update
     0x62e4e8(phase)** (GameLogic vt+0x34; phase stored at GameLogic+0x17c; the logic frame
     GameLogic+0x40 +1 in phase 1 only, 0x62e577).

So a drawn frame is *client pass with draw, then one logic phase*. Game speed = drawn frames / 6
in skirmish; in network games phase 1 waits for the network, phases 2-6 always run, so the
6-phase split is the same in LAN play.

### 2.2 Drawables are already interpolated

Objects move once per logic step (5 Hz): AI and locomotors in list 0 (phases 3-4), PhysicsBehavior
in list 2 (phase 5). The 30 FPS picture is smooth because of a keyframe blend:
- in phase 1 GameLogic::update walks every object (0x62e908-0x62e933) and calls **0x674b1f(0)**
  on its drawable: previous and current matrices (drawable+0x3ac, +0x3dc) shift, and four
  positions (+0x40c..+0x430) are stored from the object's previous / current / next positions
  (Object::setTransformMatrix 0x68da67 calls it too);
- **Drawable::getTransformMatrix 0x6765b9**, once per client frame (cache key drawable+0x244 =
  client frame): Matrix3D::Lerp 0xb27c80 of the two matrices by engine+0x3c, and a Catmull-Rom
  (D3DXVec3CatmullRom 0xa3ed38) over the four positions by the same ratio; a keyframe older than
  logic frame - 2 snaps to the object's own transform.
- other readers of engine+0x3c: a second drawable lerp 0x67171d (cache key +0x204), the rope
  drawable 0x676711, W3DModelDraw 0x4b51b5 / 0x4b686d / 0x4b6f12 (a per-step percentage from
  0x68bd71, not identified), 0x48e0ee, 0x8a0365.

The client pass runs *before* the phase advances, so frames draw at ratios 1/6 ... 6/6: the
picture is up to one logic step (200 ms) behind the logic. That lag is the game's own and stays.

### 2.3 Per drawn frame or per time

Most client "time" is the **client frame counter**, +1 per drawn frame while GameClient+0xc8 is set.

| system | driven by | where |
|---|---|---|
| W3D animation, texture mappers, W3D particle buffers, streaks, snow, terrain tracks, shader time | WW3D sync time: W3DDisplay::draw adds frameLen (0xdc7a8c, set at 0x44bf5c) x client frames since the last draw | 0x44b788 → WW3D::Sync 0x516e20 (0xdd1e0c/0xdd1e10); tracks every draw at 0x483870 |
| FX particle systems | one step per call while GameClient+0xc8 is set; INI durations converted with FramesPerSecond = 30 | manager update 0x5f5123 from the render helper 0x449d48 |
| drawable client updates, animation sounds | once per new client frame (guard 0xd9f6f8) | 0x675996 from GameClient::update 0x648741 |
| shroud on drawables | only at engine phase 1 | 0x63252f |
| floating text ("+15") | rises speed/6 per client frame, fade per client frame | 0x69db40, draw 0x69dc5b |
| tread scroll | rate/6 per call | 0x4cbffb |
| other engine+0x38 readers | per frame | 0x6714c0, 0x85ebee, 0x860b39, 0x8cd55f |
| input, audio, radar, APT, message stream | every engine iteration | |
| camera scrolling | not checked in RotWK (per message-stream pass in Zero Hour) | |

### 2.4 Design: more than 30 drawn frames, same game speed, same logic

**Rule: logic phases stay at 30 a second; extra frames are client-only.** Changing FramesPerSecond
(0xd9f60c) or engine+0x38 is ruled out: logic reads engine+0x38 (0x62c159) and every INI duration
is converted with 0xd9f60c, so that route is the "frames to seconds" project rejected on 09-24 and
the 2x-speed animations Open-BFME-1 hit (`037-fps60`).

**Scheduler** (a replacement for GameEngine::update 0x6325a0, 361 bytes, hash-checked, switch
`fps60`, plus the limiter):
- keep a phase clock: the next phase is due every 1000/30 ms (x LogicTimeScale), measured with
  QueryPerformanceCounter;
- each engine iteration is either a **real frame** (the original: client pass, phase +1, step) or
  an **extra frame** (client pass only, below);
- an extra frame is drawn only if the time to the next phase due is more than the predicted cost
  of a draw (a running mean of the last real frames' client-pass time, x 1.2). So extra frames
  never delay a phase: on a slow machine (the brother's M1 in a big battle) they simply stop, and
  the game runs exactly as now. That matters in LAN, where the slowest machine sets the pace;
- the limiter targets the display (60 or 120 Hz, a setting `fps60_hz`), with `Sleep(1)` for long
  waits and a short spin at the end (as `limiter`).

**The extra frame** (client pass 0x632409 with these changes, all restored after it):
- engine+0x3c = (p - 1 + a) / 6, where p is engine+0x34 after the last real frame's phase and
  a = time since that frame / phase period, clamped 0..1. The real frame before it drew (p - 1)/6
  and the next one draws p/6, so the blend now runs on time between them. This holds across the
  wrap too: an extra frame after phase 1 (which records the new keyframe) gets a/6 of the new
  segment, the frame before it drew the old segment's end;
- the drawable transform caches are keyed by the client frame (drawable+0x244, +0x204): give them a
  separate "render frame" key (hook the two cache tests) so the extra frame recomputes the blend;
- GameClient+0xc8 = 0 for the pass, so the client frame does not advance and every system in the
  table that counts client frames (particles, drawable updates, floating text, shroud, tread
  scroll, engine+0x38 readers) holds for that frame: they keep their speed and move at 30 Hz;
- WW3D sync: advance by the real elapsed time (frameLen x a) instead of whole frameLen steps, so
  W3D animations, texture scrolls and shader time play smoothly at the right speed. Hook the add at
  0x44b788;
- skip MessageStream, keyboard, network and radar on extra frames (input still lands on the next
  real frame, ≤ 33 ms later; or keep the mouse cursor update for feel, to decide when building);
- W3DDisplay::draw runs whole: it reads the client's state and writes nothing the logic reads.

**What stays 30 Hz in the first version** (correct speed, less smooth): particles, floating text,
tread scroll, fades counted in client frames. Second version, if Max sees it: interpolate their
draw by a (particles: position + velocity x a at draw time, the RenderObject/point-group vertex
loops; floating text: offset by speed/6 x a). Max's 09-24 note already lists Open-BFME's
pitfalls: the sawtooth of floating text (it rises in the extra frame and snaps back if the
offset is applied twice), and Set_Transform not being called between steps (the cache keys above).

**Determinism**: the logic sees the same phases in the same order with the same inputs; nothing
it reads is touched (engine+0x34/+0x38, GameLogic, FramesPerSecond). Client-only, so it is LAN
safe even if only one player has it on. The network calls stay once per real frame.

**Expected gain** (estimates from §1): an extra frame costs the client pass without logic, ~9-14
ms of render plus a few ms of drawable work in a big battle, ~4-8 ms in a small one. Small fights
and own base: 60 FPS (120 on the 120 Hz screen only with < 8 ms frames). 8-player late game: the
real frames already use ~21-33 ms of the 33 ms, so extra frames fit only between light phases:
~35-45 FPS shown, more after the logic is evened out (§4 step 1). The picture lag stays 0-200 ms as
now.
## 3. Multi-threading (part B)

### 3.1 Why the logic cannot simply run beside the draw

The obvious design is a logic thread running phase k while the main thread draws frame k. It
would need the two to share nothing, and they share a lot (static reading, direct calls only):
- **logic → client, synchronously:** a model-condition change (0x68b53c) goes straight to the
  Drawable (0x679512), which swaps W3D render objects in the scene the draw is walking; object
  creation and destruction create and delete Drawables; FX lists, particle systems, audio events,
  floating text, terrain edits (flattenTerrain → setRawMapHeight → road relight, §22), shroud
  changes, radar. Some return values the logic keeps (a Drawable pointer stored in the Object).
- **logic reads the client:** weapon launch points and bone positions come from the Drawable's
  render object, whose pose the draw evaluates.
- **client reads the logic:** the drawable blend reads the object's positions (§2.2), health bars,
  shroud status, selection, player colours.

Making that safe means deferring every logic → client call into a log replayed in order at a join,
plus locks for the few with return values. The logic calls the client within the first fraction of
a millisecond of almost every phase, so a lock-based version overlaps almost nothing, and a deferred
version is a rewrite of the client boundary (hundreds of call sites). **Not recommended.** The
extra frames of §2.4 already give the "draw more often than the logic" half of that design without
any of it.

### 3.2 Parallel work inside the client pass and the draw (client-only, LAN-safe)

Nothing here affects lockstep: the client RNG (0xda1c74) and audio RNG (0xda1c8c) are client-only.
Each region uses `parallel/pool` (`par_for`, the recorder, the first-300-calls serial/parallel
compare, parallel/DESIGN.md) and copies the main thread's x87 control word and MXCSR into every
worker (`fpu_capture`/`fpu_load`, already done).

| region | where | parallel unit | hazards | estimate |
|---|---|---|---|---|
| particle simulation | FX particle manager update 0x5f5123 (render helper 0x449d48) | one system per item; deaths, emitter spawns and new systems deferred in system order | client RNG draws per particle (give each system its own stream seeded from the shared one in system order: visually equivalent, not identical), the manager's lists | 0.5-2 ms a frame in big fights (simulation is untimed today: measure first) |
| pose evaluation before the shadow pass | HLod Anim_Update for every object the shadow pass will cull (§10.3; 49-67 evaluations a frame in the 10-05 renderstats) | one HLod per item | animdecode's per-channel cache must be per thread; shared HTree/anim data is read-only | 0.3-1 ms (small now that animdedup/animdecode run) |
| drawable client updates | 0x675996 from GameClient::update 0x648741 | one drawable per item | module updates may create FX / sound (defer), share render objects | unknown: needs the framesplit numbers |
| Visibility_Check bounding spheres | 0x470b83 per candidate | per object | none beyond the pose | < 0.5 ms |
| light environments in renderOneObject | 0x46f48e | per object | writes the shared global lights temporarily (§10.3); needs a rewritten tint path | 1-2 ms, high effort |

**D3D stays on one thread at a time.** Wine's d3d9 takes `wined3d_mutex` around every call and the
device is not created MULTITHREADED; the game wraps rendering in its own DX lock (critical section
0xdd1f80 plus the mutex our `dxlock` patch replaced). A second thread can issue D3D calls only while
holding that lock. GL lives on wined3d's command-stream thread (19 % of a core in the 10-05 match),
so which game thread calls d3d9 does not matter to GL.

**A D3D/d3dx9 submission thread** (a recording proxy for the device and the effects, replayed on
another thread) would move the per-draw d3dx9 and wined3d client cost off the main thread: about
1.5-2.5 µs a mesh plus 3.3 µs a batch (§12), i.e. ~1.5-2.5 ms a frame at the 10-05 match's
~600-700 draws and ~150 batches. Lock returns need staging buffers (wined3d patch 0003's pattern),
every Get needs shadow state, and errors arrive late. Large and risky for that gain; last on the list.

### 3.3 Deterministic parallel logic

Rule (Max, 2026-10-05): results must be the same on every machine running our build, not the same
as EA's. So thread order, timing and addresses must never reach the logic; the merge order must be
fixed (object ID or list index).

**What every update touches** (survey of direct calls from each hot update; the ~200 virtual call
sites per update were not followed, so this is a lower bound):

| shared state | where | written by | parallel option |
|---|---|---|---|
| logic RNG, one LCG word | 0xda1ca4 (randomValue 0x6d315d; 333 call sites: AI states, HordeContain, weapons, slow death, emotion tracker, partition manager ...) | most module classes | per-object streams seeded from (phase-start seed, object ID, frame, draw index) — a gameplay-visible change of which random numbers come out; or keep serial |
| update lists | TheGameLogic +0xc8 + 12·list (4 vectors), sleep-forever +0xf8, current module +0x104 | `setWakeFrame` 0x850c32 (156 sites, e.g. AIUpdateInterface::wakeUpNow 0x662552) → 0x62b921 push_back / swap-remove; the loop re-reads the end, so a module woken in a pass runs in it | command buffer applied in list-index order; +0x104 per thread |
| object create / destroy / damage / IDs | object list +0xac (next at Object+0x8c), destroy list +0x108, ThingFactory | weapons, death, hordes, castle | serial, or a deferred buffer in ID order (changes when things appear) |
| partition dirty list | PartitionData::makeDirty 0xb4e2a0 → 0xb4f460 (prepend) | every move | record and replay in item order (idempotent per object) |
| getClosestObject scratch | function-static heap vector 0xdef90c-0xdef918 | every closest-object scan (0xa3bdb0) | per-thread copy (the cloner's redirect) |
| pathfinder | cell-info pool 0xdea438, jump counter 0xde4b14, open pf+0x1d1f0, closed pf+0x34, via points pf+0x1c1cc, queues pf+0x1c1e0 / +0x1c9e8 | AI, physics, the queue | serial (§20-§21); parallel searches need per-search cell info |
| allocator | operator new 0x42f6e0 / 0x42f720 → MemoryPool::_Allocate 0x42fe60, GeneralAllocator 0xdc61d8, a CRITICAL_SECTION at +0x4e4 | everything | already thread-safe, but one lock: contention. Addresses already differ between machines (client allocations share heap 0), so the lockstep must already be address-independent (inferred) |
| strings | AsciiString copy/release 0x435f30 / 0x435d50 under one global CS (0xdc6268), PooledString CS 0xdfd400 | everything | thread-safe, contended |
| players, money, experience | ThePlayerList 0xde4928 | kills, income | serial |
| client calls from logic | model conditions → Drawable, FX, audio | most | defer to main in order |
| Lua `math_random` | CRT `rand`, per thread | scripts | keep Lua on main |

**x87.** setFPMode 0x440809 (`_fpreset`, `_controlfp(PC_24 | RC_NEAR)`, control word 0x007f) runs
at the top of every logic phase (0x62e6a4) and from 19 other callers; `_ftol2` 0xa3cfa4 (584
sites) rounds at that precision. A worker at the Windows default (0x27f) gives different results,
so workers load the main thread's words before every job (parallel/pool does). Game code changes
the control word only in ~296 save/restore pairs in W3D render code.

**Free desync detector.** GameLogic::getCRC 0x625886 (called at 0x62e7e8 every
TheWritableGlobalData+0xc18 frames, posted as message 0x44a) covers every object's xfer, the logic
seed, the partition, collision and shroud managers, ThePlayerList and TheAI. A parallel build can
compute it every frame in a check mode and compare a serial run; in LAN two machines on the
parallel build already compare it.

**Module classes** (no RTTI in the exe; classes from the INI module name each vtable's factory
registers): 0xc6a5a8 AIUpdateInterface (also Siege/Transport AI), **0xc5e378 AnimalAIUpdate**,
0xc5d3e0 HordeContain (AOD, horse), 0xc66d3c HordeAIUpdate, 0xc6ac9c WorkerAIUpdate, 0xc629bc
FireWeaponUpdate, 0xc6d948 AISpecialPowerUpdate, 0xc6d1a0 EmotionTrackerUpdate, 0xc61fa4
DozerAIUpdate, 0xc6b408 LargeGroupAudioUpdate, 0xc30e08 CastleBehavior. None writes only itself:

| class | reaches (direct calls, depth ≤ 5) |
|---|---|
| AIUpdateInterface | partition dirty list, allocator, strings, client RNG, path requests, destroyObject, damage, kill, FX |
| AnimalAIUpdate | getClosestObject, logic RNG, AI commands |
| HordeContain | its members' AI, destroyObject, logic RNG |
| FireWeaponUpdate, CastleBehavior | range scans, damage, kill, destroy, logic RNG |
| EmotionTrackerUpdate | getClosestObject, FX, client RNG |
| PhysicsBehavior 0x79350e | setPosition / setTransformMatrix (partition dirty), the pathfinder (0x6f0741), model condition → Drawable, wakeUpNow |

**Realistic candidates, ranked:**
1. **Shroud update split by map rows** (TheShroudManager 0xde4358, update 0xb51970 → per-entry
   0xb4ef50 and the span functions 0xb4fc80.. that shroudspan already rewrote). Each worker owns a
   band of rows and applies every entry in the original order, so each cell sees the same sequence
   of adds and clamps; the visible-status callbacks are recorded per band and replayed by (entry,
   row). Exact, even against EA, if the circle raster 0xb50100 is row-major (to check). TheShroud
   Manager is 1.9 ms per step in phase 5 (§1).
2. **Scans taken at the start of a pass.** Before the list loop, run the range scans
   (iterateObjectsInRange 0xa3c4e0, getClosestObject 0xa3bdb0) of every module due in the pass in
   parallel on the state at the pass start; the modules then read their answer instead of scanning.
   Deterministic, but a gameplay change: a scan can be up to one pass stale (a unit killed earlier
   in the same pass can be returned), so each consumer must re-check its target, as the AI already
   does for targets that die later. Needs to know which modules scan and with what arguments
   before they run, i.e. a C++ rewrite of each consumer's scan step. 1-3 ms a step after scantree.
3. **Parallel path searches** with per-search cell info and a count-based budget: big redesign of
   §20-§21 for what TheAI and the queue now cost (~1-3 ms a step).
4. **HordeContain across hordes** (each horde writes only its members, but RNG, AI commands and
   destroys must be deferred): ~0.3-1 ms a step.
5. **Not realistic:** the per-object AI, animal, worker, dozer, horde-AI, weapon, castle, emotion
   and special-power updates. They need exact single-thread speed-ups instead.

**Expected speed-up.** Of the 32.5 ms of logic per step, candidates 1-4 cover at most ~5-8 ms; on
6 workers (an 8-performance-core Mac: main thread and Wine's render thread take two) that saves
~4-6 ms a step, ~0.7-1 ms a drawn frame, 2-4 ms on the phase-5 frame. On the brother's M1 (4 P + 4
E: two P workers plus E cores at about a third of the speed, ~3.3 effective) about 60 % of that.
The phase balancing of §4 step 1 removes more from the worst frame (≈5 ms on average, ≈12 ms in the
worst windows) with no thread at all. So threads in the logic come after the cheaper work, not
before.
## 4. Roadmap, ranked (part D)

Gains are estimates from §1-§3 unless marked; "8p" = the 10-05 8-player match on the M3 Max,
"small" = own base or a small fight. Every step keeps the project's rules: a switch per patch,
original bytes or a hash checked first, a standalone test that runs the game's own code, nothing
installed before Max's review, Max tests in game.

| # | step | gain | risk | effort | logic / LAN |
|---|---|---|---|---|---|
| 0 | **framesplit**: per-frame timing of the client pass, the draw, the logic phase, Present and the limiter wait | none; tells us the real headroom for 1-3 | none (diagnostic) | S | client only |
| 1 | **phasebalance**: spread the six phases evenly | heaviest phase 12 → ~7.5 ms mean, 17 → ~10-11 heaviest quarter, ~26 → ~14 worst; most 8p drops below 30 go | low | S-M | changes when the pathfind queue runs relative to modules; deterministic; every LAN player needs the same switch |
| 2 | **exact speed-ups of the new top classes**: AnimalAIUpdate, AIUpdateInterface, Horde*, FireWeaponUpdate's 1.5 ms single call, getClosestObject | 2-6 ms a step (0.3-1 ms a frame, more on phase 3-5 frames) | low | M (one per class) | exact: none |
| 3 | **fps60**: extra interpolated frames between phases (§2.4) | small: 30 → 60 FPS; 8p: 30 → ~35-45, more after 1 | medium (visual glitches, never logic) | M | client only, LAN-safe |
| 4 | parallel client work: particle simulation, pose evaluation, drawable updates (§3.2) | 1-3 ms a frame in big fights | medium | M | client only |
| 5 | shroud update split by rows (§3.3 #1) | ~1-1.5 ms a step on the phase-5 frame | low-medium | M | exact if the raster is row-major |
| 6 | scans taken at the pass start (§3.3 #2) | 1-3 ms a step | high | L | deterministic, gameplay-visible staleness |
| 7 | D3D/d3dx9 submission thread (§3.2) | 1.5-2.5 ms a frame | high | L | client only |
| - | not recommended now: logic beside the draw (§3.1), parallel per-object AI, parallel path searches, frames → seconds | | | | |

### Step 0: framesplit (first prototype, a day)

Timers (rdtsc, converted per window as renderstats does) around: the client pass call at 0x6325cf
(vt+0x9c → 0x632409), inside it GameClient::update 0x64849e and W3DDisplay::draw; the engine step
calls at 0x6326c6 / 0x6326f0 (vt+0x98 → 0x6329b0); Present (the DX8Wrapper end-scene path); and the
limiter's wait 0x63a196-0x63a1f8. Per frame into the monitor's frame record (`p_monitor.c`), per
30 s into a `framesplit:` line with p50/p90 per phase. Test `t_fsplit` in the logicstats pattern
(stubs hand the original every register, xmm and stack slot). One 8-player session with it gives
the headroom table that decides how much step 3 can show.

### Step 1: phasebalance

GameLogic::update's dispatch (0x62e97e-0x62e9be) maps phase → lists [first, end): 3-4 → list 0
(split by index at size/2, 0x62e9d4-0x62ea1e), 5 → lists 1-2, 6 → list 3; the twelve phase-5
subsystems follow the lists. New split, keeping every module's and subsystem's relative order:

| phase | now (ms/step, 8p mean) | balanced |
|---|---|---|
| 1 | frame +1, script engine (2.1) | same (2.1) |
| 2 | subsystems, per-object loop (1.9) | same, then list 0 [0, n/3) (~6) |
| 3 | list 0 [0, n/2) (6.6) | list 0 [n/3, 2n/3) (~5) |
| 4 | list 0 [n/2, n) (8.6) | list 0 [2n/3, n) (~6) |
| 5 | lists 1, 2, then 12 subsystems (12.0) | list 1, list 2 [0, 2m/3) (~6) |
| 6 | list 3 (1.4) | list 2 [2m/3, m), the 12 subsystems, list 3 (~7.5) |

Splits by vector index, as EA's own list-0 split; the sleep-forever swap-removal (now from phase 4
on) only in the pass that finishes a list, so indices stay stable across a list's passes. What
changes: the pathfind queue (top of every phase) and the client pass now also fall between list 0's
thirds and between list 2's parts, as they already fall between list 0's halves. Proof: a test that
runs the game's GameLogic::update loop on a scripted world of stand-in modules and logs every
module call, queue run and subsystem call: the patched log is the original's with only phase
boundaries moved; plus the getCRC check in Max's game. Cut points by index (or by a fixed cost
table per class) — never by measured time, which would differ between machines.

### Step 2: exact speed-ups, new targets

- **AnimalAIUpdate 0x882058**: 3.6 ms per step, 321 calls (11 µs each): the third biggest logic
  cost is ambient animals. First find which INI objects carry it and what each update does
  (getClosestObject per call?); an exact speed-up of its scan path, or (Max's call, a gameplay
  change) a longer sleep for idle animals.
- **AIUpdateInterface 0x66e58f** (5.3 ms, 17.5 µs a call), **HordeContain 0x872efc** (85 µs a
  call), **HordeAIUpdate 0x89e2d0** (92 µs): an inclusive sample first (the stall sampler in a
  low-rate always-on mode, `stalls_always`), then the logicmath pattern.
- **FireWeaponUpdate 0x88f554**: one call a step costing 1.46 ms (§25.4 suspects a fortress
  upgrade firing a DamageNugget every 250 ms): the 3D distance through the table (0xa3aeb0) in SSE.
- **getClosestObject 0xa3bdb0**: the next scan after scantree (§19).

### Step 3: fps60 (§2.4)

First prototype: the GameEngine::update replacement with the phase clock, extra frames that only
change engine+0x3c and the two drawable cache keys, nothing else (particles and WW3D time hold).
Offline test: the replacement against the original on stubbed subsystems with a scripted clock:
identical sequence of vt+0x98 phases and network calls, extra frames only when the clock allows,
never a phase late because of one. Then Max's look at a small fight; then the WW3D time and the
particle / floating-text interpolation.

### Effects in frames per second (estimates)

| scene (M3 Max) | now | after 0-2 | after 3 | after 4-5 |
|---|---|---|---|---|
| own base, small fight | 30 (cap) | 30 | **60** | 60 |
| 8p mid game | 30 with drops on phase 3-5 frames | 30 locked in most windows | ~40-50 | ~45-55 |
| 8p late, worst windows | 25-30 | ~30 | ~30-35 | ~35-40 |

On the brother's M1 every row is lower (~1.35x the per-frame cost); in LAN his machine sets the
logic pace, so steps 1-2 matter most for LAN games, and step 3's extra frames switch themselves off
on his side when there is no time.
## 5. Hybrid C++: our own subsystems inside the game (part C)

Yes, it works in principle: the DLL already swaps game functions for our code (crtsqrt,
scantree, pathsplit). C++ does not change how a function gets swapped in. It changes how
comfortably we can write a big replacement, such as a whole module's update or a new scheduler.

**ABI facts** (checked 2026-10-06 with a scratch test compiled both ways, not in the repo):

| item | the exe (MSVC 7.1) | mingw g++ (i686) | clang `-target i686-pc-windows-msvc` (Apple clang 17) |
|---|---|---|---|
| member calls | `thiscall` (`this` in ecx, callee pops) | `thiscall` by default for members since GCC 4.7; `__attribute__((thiscall))` for free functions | `thiscall`, same as MSVC |
| vtable layout | one deleting-destructor slot; overloads grouped in reverse declaration order | **two** destructor slots (Itanium ABI); overloads in declaration order. A test class came out with `f(int)`/`g()` at +0x8/+0xc under MSVC rules and +0x8/+0x10 under g++ | same as MSVC (+0x8/+0xc in the test) |
| class layout | MSVC rules (vfptr first, bases in order, no tail-padding reuse) | same for plain single inheritance; differs for virtual bases and some empty bases | MSVC rules |
| RTTI | the exe has MSVC RTTI (complete object locators before vtables) | incompatible (`typeinfo` is Itanium) | MSVC-compatible |
| exceptions | MSVC C++ EH over SEH frames (`fs:[0]` chain; the EH prolog 0xa3cef0 in nearly every game function) | DWARF/SJLJ unwinding, cannot unwind through MSVC frames | MSVC EH model, but needs the MSVC runtime to throw |
| operator new/delete | the game's own allocators (operator new 0x42f6e0 / 0x42f720, memory pools; parallel/DESIGN.md §2) | its own, from libstdc++/msvcrt | its own |

**Rules that follow:**
- Game classes are never declared as C++ classes with virtual functions in our code. We see them as
  plain structs with offsets checked by `static_assert`, and call their virtuals through a tiny
  helper (`vcall<slot>(obj, args...)`, ecx = object). That works the same in either compiler and
  is what the C code already does.
- Our own classes stay inside the DLL. Nothing with a vtable, an STL container or an exception
  crosses into game code. Hand the game only plain structs and pointers it already understands.
- No exceptions (`-fno-exceptions`), no RTTI (`-fno-rtti`), no static constructors that need
  the C++ runtime before the game starts (or a defined init order in `DllMain` / first use).
  A game exception thrown through our frames would unwind past them without running our
  destructors; guard each entry with the same register/stack rules the asm stubs follow today.
- Memory that the game will free must come from the game's allocator (call 0x42f6e0 / the pool
  for that class); memory we free comes from ours. Never mix.
- The DLL loads before `WinMain`; `__thread` TLS fails under this Wine (parallel/DESIGN.md).
  Keep `TlsAlloc` or per-slot arrays.

**Compiler choice:** mingw `i686-w64-mingw32-g++` 16.2 is installed and fits the existing
build, given the "plain structs only" rule above. Apple's clang can compile MSVC-ABI COFF objects
(checked) but has no `lld-link` to link them; mingw `ld` can link such objects when they need no
C++ runtime. Start with g++ and the rules above; move to clang/lld only if we ever want to subclass
a game class in C++ (not needed for anything in this roadmap).

**Floats and determinism.** Within our own build every machine runs the same code, so the rule is
"same instructions, same inputs, same bits":
- Our code: SSE2 scalar single/double only (`-msse2 -mfpmath=sse -ffp-contract=off`, as the
  Makefile has), no `-ffast-math`, no FMA, no auto-vectorised reductions (they reorder sums),
  explicit `MXCSR` (round to nearest, no FTZ/DAZ unless the original code had it).
- No host math library calls in logic: `sqrt` is `sqrtss/sqrtsd` (exact everywhere);
  `sin/cos/atan2/acos` need our own fixed implementations (or the game's own, under its FPU mode),
  never Wine's or Windows' msvcr71, which differ.
- The game's own x87 code runs at 24-bit precision (0x440809, called again at the top of every
  logic phase, 0x62e6a4). Under Rosetta the x87 is emulated; that is the same code on both Macs
  only if both run the same Rosetta (a macOS update could in principle change it; unverified).
  Every function we move to SSE removes that question for its code.
- Worker threads start with the default x87 control word (0x27f) and MXCSR; each must load the
  main thread's words before running game code (parallel/pool already does: `par_for` snapshots
  them).

**What a GPL-3 relicense would and would not allow** (not legal advice):
- *Would allow:* copying Open-BFME-2's reconstructed C++ (GPL-3) and EA's Generals/Zero Hour
  source (GPL-3 with EA's extra terms: no EA trademarks, keep the notice) into the DLL, which would
  cut the work of rewriting a subsystem from the disassembly to adapting known source. Our MIT code
  can be relicensed by its authors (check third-party files such as `tools/LICENSE-DrewHoo` first).
- *Would not allow:* shipping the game exe or EA data (unchanged: we never do). It would make the
  whole DLL GPL-3 (source must stay available, as it is), and anyone reusing our code would inherit
  GPL. The DLL runs inside a proprietary exe; the Open-BFME projects ship GPL code that patches the
  same exe, so the community's practice is to accept that, but it is a grey area.
- *Without relicensing:* we keep reading their code for understanding and write our own, as now.
  This roadmap assumes that.

**Build and tooling changes for C++:** a `CXX := i686-w64-mingw32-g++` with
`-std=c++17 -O2 -msse2 -mfpmath=sse -ffp-contract=off -fno-exceptions -fno-rtti
-fno-threadsafe-statics -fno-asynchronous-unwind-tables`, linked with the gcc driver (not g++) so
libstdc++ never comes in. Checked with a scratch DLL: a templated `vcall` helper compiles to
`mov ecx,obj; call [eax+slot]`, and the DLL imports only KERNEL32 and UCRT pieces the C build
already imports. The harness's 600-line limit and the `docs/REFERENCE.md` rule apply to `.cpp`
files too. Tests stay the same pattern: the game's code in a relocated copy against ours.

## 6. Decisions for Max

1. **Logic-order changes.** Phase balancing (step 1) and the pass-start scans (step 6) change the
   logic deterministically, not bit for bit against EA. Your 10-05 rule allows that, but AGENTS.md,
   docs/DEVELOPMENT.md ("bit-exact against the original") and parallel/DESIGN.md ("nothing
   lockstep-relevant may be parallelised") still say otherwise, and MULTIPLAYER.md would need a line:
   every LAN player runs the same game patch with the same switches (a Windows player too, with our
   dinput8.dll), and old replays may not play back. Confirm, and we update those files.
2. **fps60 first version**: particles, floating text and tread scroll stay at 30 updates a second
   (right speed, less smooth) until the second version interpolates them. Target 60 Hz or the 120 Hz
   screen?
3. **Ambient animals** (AnimalAIUpdate) cost 3.6 ms per logic step. If no exact speed-up is enough,
   letting idle animals think less often is a gameplay change: your call.
4. **GPL-3 relicense**: not needed for anything above. It would only let us copy Open-BFME-2 / EA
   code instead of rewriting it (§5).
5. **One measuring session** after step 0 is built (framesplit on, otherwise normal play), to get the
   per-frame headroom before step 3.

## Sources

- Data: `logs/gamepatch.log` (logicstats, passtimers, renderstats, 2026-10-05 18:24-19:46),
  `logs/sessions/20261005-182416/summary.txt`; numbers aggregated with throwaway scripts (not kept).
- Code: `build/rotwk-re/text.asm`, `build/ext/rotwk_map.tsv`; GameEngine::update 0x6325a0, client
  pass 0x632409, engine step 0x6329b0, GameLogic::update 0x62e4e8, limiter 0x63a196, drawable blend
  0x674b1f / 0x6765b9.
- Related: docs/PERFORMANCE.md §10-§26, parallel/DESIGN.md, Open-BFME-1 `mods/README.md` (its
  render-only 60 FPS experiment and the retired frame-doubling one).
