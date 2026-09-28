# Loading time on the Wine 10.0 (Sikarugir) engine — findings and experiment matrix

## 0. Resolved 2026-09-23 — it was Microsoft's d3dx9_27, fixed by `scripts/d3dx9-fix.sh`

Everything from §1 on predates this and is kept as history; several of its conclusions are wrong
(see the last table). What settled it:

| step | finding |
|---|---|
| bar decoded from harness captures | RotWK: 0→~64 % within ~5 s of Play, then a linear crawl at ~0.17 %/s to 93 % (BFME2: 56 %, then ~0.08 %/s). ~35 % of the bar is ~97 % of the time |
| CPU during the crawl | ~110 %, flat: one thread busy, the rest idle |
| macOS `sample`, phase checked by CPU | main thread ~99 % in translated 32-bit code, 25/3287 samples in `ntdll.so`: no waits, no I/O, no spin. The `cthread_yield` spin in §1.5 is the in-game 30 FPS limiter, not loading |
| detail level | `StaticGameLOD` VeryLow (1/16 texels): 269 s → 16 s. Cost is proportional to texels |
| TGA → DDS pre-bake (`tools/prebake_textures.py`) | 231 s → 168 s. File format and mipmap generation are only a quarter of it |
| in-guest profiler (`tools/eipsample.c`, reads the guest EIP) | **99.2–99.5 % of the loading thread in `d3dx9_27.dll`**, Microsoft's native copy (winetricks, `*d3dx9_27=native`), game 0.4 %, wined3d 0.3 %. The hot loop is x87 (`flds/fmuls/fcomps/fnstsw/fistpl`, 707 x87 ops in the hot 3.8 KB), which Rosetta emulates slowly |
| Wine's builtin d3dx9_27 | **12 s** Play → map. Units invisible: `ID3DXEffect::SetRawValue` is a stub in 10.0 (~96k calls per load), and the games upload their bone palette through it |
| `patches/d3dx9-setrawvalue/` | upstream SetRawValue + struct support: units render, 0 SetRawValue fixmes |

Superseded claims below: msync is not a load lever (§2.1; its ~7 % was noise, nothing waits);
shader compiles are not it (§1.3, right for the wrong reason); the §1.5 profile was taken in-game;
the wined3d map/lock path (179,637 map/unmap pairs, every one on the slow synchronous path) is real
but costs ~0.3 % of the loading thread. `csmt=0` was never measured cleanly and no longer matters.

Scope: the ~3 min second half of the loading bar on `engines/w10` (`WINE_BUILD=w10`), the engine both
games play on. Research only — nothing here has been run. Baselines from the existing harness:

| run | game | loading→MAP |
|---|---|---|
| `logs/skirmish-w10-rotwk-postnx.log` | RotWK | 290 s |
| `logs/skirmish-reorg-rotwk-w10.log` | RotWK | 291 s |
| `logs/skirmish-mouseprobe.log` | RotWK | 394 s |
| `logs/skirmish-w10.log` | RotWK | 374 s |
| `logs/skirmish-w10-bfme2b.log` | BFME2 | 493 s |

**Run-to-run spread on identical settings is 290–394 s (±15 %).** Nothing below is measurable in one
run; every cell in the matrix needs ≥3 runs, and the poll granularity has to come down first (§2.0).

## 1. What the evidence says

**1.1 msync and esync both exist in the w10 engine, and both are OFF by default.**
`engines/w10/wswine.bundle/lib/wine/x86_64-unix/ntdll.so` and `.../bin/wineserver` contain the full
msync/esync symbol sets (`msync_init`, `msync_create_mutex`, `__msync_wait_objects`, `msync: up and
running.`) plus `WINEMSYNC`, `WINEESYNC`, `WINEMSYNC_QLIMIT`. The gate (ntdll `0x22b5c`, wineserver `0x10001e8ec`)
shows the standard `getenv("WINEMSYNC") && atoi(...)` cached test — **no default, no config file**: unset
env var → 0. esync's gate (ntdll `0xb93c`) is `getenv("WINEESYNC") && atoi(...) && !do_msync()`, i.e.
msync wins when both are set. `engines/cx` (WineCX 24.0.7) ships the same code. `engines/stable`
(Gcenx 11.0) and `engines/staging` (11.17) contain **neither** — a strings scan of their `ntdll.so`
and `wineserver` finds no msync/esync symbols at all.
Nothing in the repo sets either var: `env.sh`, `scripts/play-*.sh`, `scripts/test-skirmish.sh` and
`ahk/` have no mention of it. **So every run so far has used wineserver round-trips for every
contended wait.**

**1.2 `WINE_DISABLE_WRITE_WATCH` and `WINE_CPU_TOPOLOGY` are not honoured by this build.**
Neither string exists anywhere in `engines/w10/wswine.bundle` (nor `engines/cx`), so the
`WINE_CPU_TOPOLOGY=1:0` in `scripts/play-rotwk.sh:16` and `scripts/play-bfme2.sh:17` is dead code —
which confirms the README's "no effect". BFME2's comment credits it with taming the startup CPU
benchmark; what actually does that is the neutered `gamelodpresets.ini` in `INI.big`, so don't remove
that on the strength of the env var. `WINE_LARGE_ADDRESS_AWARE` is not in w10's ntdll (it is in `engines/cx`); the exe's own flag is the switch,
and RotWK runs with it on since 2026-09-27 (MEMORY-4GB.md; the crash once blamed on it was Wine 11's).

**1.3 Shader compiles are probably not the 3 minutes.** In `logs/rotwk-20260922-204512.log` (warn+d3d,
the 290 s run) the highest GL shader object is `#250` and only 135 emit an info log; BFME2's 493 s run
reaches `#342`. A few hundred GLSL compile+links is seconds, not minutes — even though wined3d has no
on-disk program cache (no `glGetProgramBinary` anywhere in Wine) so every permutation is recompiled
per launch. The context is a GL 4.1 **core** profile, so `MaxVersionGL` is already saturated. §2.0's
`+timestamp,+d3d_shader` run is what would turn "probably" into a fact.

**1.4 The log volume scales with wall time, not with work.** RotWK 290 s → 49,591 draws / 4,363
callback unwinds; BFME2 493 s → 90,234 / 7,065 — both ≈175 draws/s and ≈15 unwinds/s, i.e. the loading
screen simply redraws at a constant rate. **Nothing in the Wine log accounts for the 3 minutes**: no
exception storm (42 `dispatch_exception` total, 0 in BFME2), no conversion warnings, no shader storm.

**1.5 The one profile we have is dominated by sleeping and by wineserver waits.** A 1 ms `sample`
(864 samples) of a RotWK process, in `scratchpad/load-sample.txt`, taken during `skirmish-mouseprobe`
at the load→play boundary — *not* mid-load: main thread `120262127` **457/864 in `NtDelayExecution` →
`cthread_yield`** (a `Sleep(0)` spin); threads `120262401`/`120262607` 862 and 863 of 864 in
`NtDelayExecution`; threads `120262536`/`120263822`/`120262621`/`120262535` 853/859/720/666 in
`NtWaitForMultipleObjects` with `NtReleaseMutant` + `wine_server_call` alongside; `wined3d_cs` idle
196/849 in `os_sync_wait_on_address` and only ~30 samples in real GL calls. Every contended wait and
every `NtReleaseMutant` there is a wineserver round-trip that msync replaces with an in-process
Mach/`os_sync` wait — the strongest argument for §2.1. Caveat: at the boundary this may be the in-game
30 FPS limiter, so **take a fresh `sample` mid-load before concluding** (§2.0).

**1.6 The work itself is tunable from the game side.** `data\ini\gamelod.ini` (in `INI.big`) sets
`TextureReductionFactor = 0` for `High`/`UltraHigh`, `1` for `Low` (half res → ¼ the texels) and `2`
for `VeryLow` (1/16). Both prefixes run `StaticGameLOD = UltraHigh`, and RotWK additionally loads
~315 MB of HD Edition textures (`!!!!!!!!rotwk_hd_edition_2.02.big` + `___hdrotwk.v.0.9.big`) on top
of `Textures0-4.big` (457 MB) and `W3D.big` (238 MB).

**1.7 wined3d knobs need no prefix edit.** The shipped `wined3d.dll` contains `WINE_D3D_CONFIG`, which
`wined3d_main.c` reads as a `name=value,…` list **taking precedence over the registry**. Names in the
shipped DLL: `csmt` (default 1), `MaxVersionGL` (4.4), `shader_backend`, `renderer`, `ffp_hlsl` (0),
`cb_access_map_w`, `VideoMemorySize` (REG_SZ/atoi), `VideoPciDeviceID`, `VideoPciVendorID`,
`MultisampleTextures`, `SampleCount`, `CheckFloatConstants`, `strict_shader_math`,
`MaxShaderModelVS/HS/DS/GS/PS/CS` (uncapped). `UseGLSL` and `OffscreenRenderingMode` no longer exist.
winemac.drv's `setup_options()` reads, under `HKCU\Software\Wine\Mac Driver` (strings, first char
`y/t/1` = true): `WindowsFloatWhenInactive`, `CaptureDisplaysForFullscreen` (N),
`SkipSingleBufferFlushes` (N), **`AllowVerticalSync` (Y)**, `AllowSetGamma` (Y),
`Left/RightOptionIsAlt`, `Left/RightCommandIsCtrl`, `AllowSoftwareRendering` (N),
`AllowImmovableWindows` (Y), `UseConfinementCursorClipping` (Y), `CursorClippingLocksWindows` (Y),
`UsePreciseScrolling` (Y), `OpenGLSurfaceMode`, `EnableAppNap` (**N** — App Nap is already suppressed),
`RetinaMode`. These have no env form; they need `wine reg add`, which touches the prefix.

**1.8 Rosetta is probably not the cost.** `bin/wine`, `bin/wineserver` and the unix `.so`s are all
`Mach-O x86_64` (`Code Type: X86-64 (translated)`, `com.apple.rosetta.exceptionserver` thread), so
they get AOT-cached in `/var/db/oah` once. The game's 32-bit PE code is mapped by Wine's loader, never
seen by `oahd`, so it takes the in-process JIT path with no persistence — but at the measured ~MB/s
translation rate a 30 MB game is seconds of first-touch cost, not minutes. `pmset -g` already reports
`powermode 2` (High Power), so that lever is spent too.

## 2. Experiment matrix

Ordered by expected payoff. Run from `$BFME_ROOT`; the harness prints `RESULT: MAP_RENDERED after
<n>s` (loading screen → map) into `logs/skirmish-<label>.log`, and does `wineserver -k` before each
launch, so env-var changes take effect cleanly.

### 2.0 First: make the measurement honest (do this before anything else)
- **Change:** `WINEDEBUG=-all POLL=5 GAME=rotwk scripts/test-skirmish.sh base-quiet` — three times.
  The harness default is `WINEDEBUG=warn+d3d,+seh,err+all`, which wrote 87,492 lines / 8.2 MB for
  RotWK and 149,176 lines / 14 MB for BFME2. The play scripts use `-all`, so **every number in the
  table at the top is measured under a debug load the player never has.** `POLL=20` also quantises the
  result to 20 s (+5 s confirm bias); `POLL=5` costs only extra screenshots.
- **Reversal:** none (caller env only). **Expected:** possibly 5–15 %, but the point is the baseline
  and its variance. **Risk:** none, except that a crash in a quiet run can't be diagnosed — rerun it
  with the default `WINEDEBUG` if that happens.
- **Also, two read-only diagnostics that settle §1.3/§1.5 outright.** While a quiet run sits on the
  bar: `sample $(pgrep -f lotrbfme2ep1) 10 -f logs/load-sample-mid.txt`. And one run with
  `WINEDEBUG=+timestamp,+d3d_shader`: `+timestamp` prefixes every line with ms since start, so the
  shader-compile lines carry the timestamps this analysis lacked and "is the second half shader
  compiles?" gets answered in one run instead of argued about.

### 2.1 `WINEMSYNC=1` — highest expected payoff, zero risk
- **Change:** `WINEMSYNC=1 WINEDEBUG=-all POLL=5 GAME=rotwk scripts/test-skirmish.sh msync-on`
- **Reversal:** drop the variable; `wineserver -k` (the harness does it).
- **Expected:** removes the wineserver round-trip from the mutex/event traffic in §1.5. Plausibly
  10–30 % if waits are on the critical path. (CrossOver ships the identical gate — its
  `bin/wineserver` at `0x100018951` is the same `getenv("WINEMSYNC")` test — and exposes it as a
  per-bottle *Synchronization* toggle whose documented default is "neither ESync nor MSync". So the
  common claim that CrossOver "has msync by default" is wrong; it is opt-in there too.)
- **Risk:** low. Game **and** wineserver must agree (`Server is running with WINEMSYNC but this process
  is not` otherwise), so never set it for one process only — the harness's `wineserver -k` handles
  this, a manual `wine` command in a live prefix does not. It changes wait timing, which is exactly
  what the WoW64 bug (`patches/WINE-BUG-REPORT.md`) is sensitive to; w10 does not have that bug, but
  watch for new `CRASHED`/`HANG_AFTER_LOAD` results and be ready to call it off.
- **Fallback:** `WINEESYNC=1` (same binaries, fd-based); only if msync misbehaves.

### 2.2 `StaticGameLOD = Low` — largest reduction in actual work
- **Change:** in `prefixes/w10/drive_c/users/<you>/AppData/Roaming/My Rise of the Witch-king Files/Options.ini`
  set all three of `StaticGameLOD`, `IdealStaticGameLOD`, `FixedStaticGameLOD` to `Low` (then `VeryLow`).
- **Reversal:** set them back to `UltraHigh` (keep a copy of the file first).
- **Expected:** `Low` → `TextureReductionFactor 1` = ¼ the texels decoded and uploaded, plus
  `UseShadowVolumes=No`, `MaxParticleCount 3000→500`; `VeryLow` → 1/16 the texels. If texture upload is
  a real share of the bar, this is the biggest single cut available. It also isolates "is it asset
  work at all?" — if `VeryLow` doesn't move the number, stop looking at assets.
- **Risk:** visual quality only. **Multiplayer-safe**: `Options.ini` is per-machine and is not part of
  the `ini.big` data that peers must match.
- **Finer control:** SAGE applies the *individual* Options.ini graphics keys only when
  `StaticGameLOD = Custom` (`GameLOD.cpp`, `if (userSetDetail == STATIC_GAME_LOD_CUSTOM)`). So to cut
  textures without cutting everything else: `StaticGameLOD = Custom` + `TextureReduction = 2` (a real
  Options.ini key; `TextureReductionFactor` is its gamelod.ini counterpart and is *not* valid here),
  optionally `UsePixelShader = no` to push the game onto the FFP path and cut shader count.
  `IdealStaticGameLOD` is already set explicitly, which skips the RDTSC CPU benchmark — lever spent.

### 2.3 `IsThreadedLoad = no`
- **Change:** same `Options.ini`, `IsThreadedLoad = no`. **Reversal:** `yes`.
- **Expected:** §1.5 shows the main thread burning half its samples in `Sleep(0)` yields and several
  workers parked in `NtWaitForMultipleObjects`. If the threaded loader is a producer/consumer that
  spin-yields, serialising it removes the cross-thread handoff, which under WoW64+Rosetta costs a
  32→64 transition per iteration. Could go either way — measure both, and **together with 2.1**, since
  msync makes the threaded path cheaper and the two interact.
- **Risk:** low. Ruled out for the *crash* in `patches/WINE-BUG-REPORT.md` but never timed. Changes
  thread timing → same WoW64 caveat as 2.1. Every published Options.ini template uses `yes`; no one
  has posted results for `no`, so this is genuinely untested ground.

### 2.4 Vertical sync off
- **Change:** `WINE_BUILD=w10 . ./env.sh; wine reg add 'HKCU\Software\Wine\Mac Driver' /v AllowVerticalSync /t REG_SZ /d N /f`
  **Reversal:** `wine reg delete 'HKCU\Software\Wine\Mac Driver' /v AllowVerticalSync /f`
- **Expected:** the loading screen redraws ~175 draws/s throughout (§1.4). If the loader's progress
  steps are serialised behind `CGLFlushDrawable`/vsync this cuts the bar directly; if the redraw is a
  passenger it does nothing. Cheap either way.
- **Risk:** low. The 30 FPS cap is a simulation lock and is unaffected, so no MP desync; possible
  tearing in game. **This writes to `prefixes/w10`** — unlike 2.1/2.5 there is no env form.

### 2.5 wined3d shader/command-stream knobs (env-only, no prefix edit)
- **Change:** `WINE_D3D_CONFIG=csmt=0 …/test-skirmish.sh csmt-off`; separately
  `WINE_D3D_CONFIG=ffp_hlsl=1 …` ; separately `WINE_D3D_CONFIG=MaxShaderModelPS=1,MaxShaderModelVS=1 …`
  (capping the reported shader model makes the *game* pick simpler material paths, so it changes how
  many programs wined3d ever has to compile — a load knob, not an FPS knob). Also `-- -noshellmap`
  appended to the harness command skips the shell-map load behind the main menu; that is startup, not
  the bar, but it is free and shortens every run.
- **Reversal:** drop the variable. **Expected:** `csmt=0` (default 1) removes the CS thread's queue handoff, and the sample shows
  `wined3d_cs` idle 23 % of the time, so the handoff may cost more than it buys on a load that is
  upload-heavy and draw-light. `ffp_hlsl=1` changes how fixed-function replacement shaders are
  generated. Small effects expected — §1.3 bounds shader work at seconds.
- **Risk:** low; `ffp_hlsl` is off by default in 10.0 and may render wrong — check the MAP screenshot.

### 2.6 `VideoMemorySize` — deliberately *lower* it
- **Change:** `WINE_D3D_CONFIG=VideoMemorySize=512` (currently `4096`, a REG_SZ in
  `prefixes/w10/user.reg` under `[Software\Wine\Direct3D]`). **Reversal:** drop the variable.
- **Expected:** SAGE sizes its texture working set from `GetAvailableTextureMem`, so less reported
  VRAM may mean less preloading. Speculative; test after 2.2, which probes the same thing directly.
- **Risk:** low, reversible; may cause in-game texture thrash — don't leave it set.

### 2.7 Remove the HD Edition assets (RotWK only) — last resort
- **Change:** rename `!!!!!!!!rotwk_hd_edition_2.02.big` and `___hdrotwk.v.0.9.big` to `.bak` in
  `prefixes/stable/…/RotWK/` (the w10 prefix symlinks it). **Reversal:** rename back. **Expected:**
  315 MB fewer high-resolution textures and models to index and upload.
- **Risk:** **highest here.** It edits the real install under `prefixes/stable`, and peers are
  expected to have the HD data — a diagnostic only, restored before any multiplayer game. Do it only
  if 2.2 shows asset volume dominates.

### Dead ends — do not spend runs on these
`WINE_CPU_TOPOLOGY`, `WINE_DISABLE_WRITE_WATCH`, `WINEFSYNC` (§1.2 — absent from these binaries;
the last two are Proton/Linux-only anyway); `MaxVersionGL` (at the macOS ceiling already, §1.3);
`strict_shader_math` (emits an `optionNV` pragma — NVIDIA-only, inert on Apple GL); `UseGLSL` and
`OffscreenRenderingMode` (deleted from Wine in 6.1 / 9.5); `OpenGLSurfaceMode` and
`AllowSoftwareRendering` (compositing/fallback, not load-path); 
`renderer=vulkan` (black, README); Low Power Mode (already off); `ROSETTA_*`
(undocumented, and the game's PE code is JIT-translated per launch at ~MB/s — seconds, not minutes).
**Never delete `asset.dat`** as an experiment: it is a prebuilt W3D/texture catalogue the game only
*reads* (no regeneration path outside EA's AssetCacheBuilder); without it textures come up pink.

## 3. Measured (2026-09-22 late, RotWK on w10, POLL=5, WINEDEBUG=-all on every run)

| run | setting | loading→MAP |
|---|---|---|
| lt-base-1 (first run of the session, cold cache) | default | 283 s |
| lt-base-2, lt-base-3 | default | 187 s, 198 s |
| lt-msync-1 | `WINEMSYNC=1` | 182 s |
| lt-msync-2 | `WINEMSYNC=1` | ~176 s (map up; a stray Esc opened the pause menu, which the classifier reads as UNKNOWN, so the harness logged a false HANG_AFTER_LOAD — captures 33–36 show the rendered map) |
| lt-msync-3 | `WINEMSYNC=1` | run interrupted, no result |

- msync is active when set: the game log opens with `msync: bootstrapped mach port` and
  `msync: up and running.`; no msync errors, game rendered and ran (short watch only, the
  5-minute stability watch was not completed).
- Warm baseline mean 192 s vs msync mean ~179 s: **~7 % in msync's favour, inside the ±15 %
  run-to-run noise.** Not adopted by default yet; `WINEMSYNC=1 scripts/play-rotwk.sh` to opt in.
- **The largest effect measured is Wine's debug logging.** These runs, at `WINEDEBUG=-all`, are
  ~35 % faster than the 290/291 s baselines in §0, which the harness took with its default
  `warn+d3d,+seh,err+all` (87k–149k log lines per load). Normal play through the play scripts
  already runs quiet, so the earlier "3 minutes" figure overstated what a player sees;
  harness timings must only be compared at equal WINEDEBUG.
- Harness note: hang/timeout thresholds are now in seconds (`HANG_SECS`, `IDLE_SECS`,
  `MAX_SECS`) so `POLL=5` no longer makes a hang fire after 20 s of UNKNOWN.

Outstanding: msync run 3 and a 5-minute in-match stability watch, the
`WINEDEBUG=+timestamp,+d3d_shader` attribution run, `WINE_D3D_CONFIG=csmt=0`, BFME2 with msync.
