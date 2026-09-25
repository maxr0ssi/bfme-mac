# Battle for Middle-earth on Apple Silicon (free, Wine-based)

Everything lives in this folder. No CrossOver, no VM.

## Play

| Game | Command |
|---|---|
| BFME2 (Vanilla 1.06) | `scripts/play-bfme2.sh` (Wine 10.0 engine, `WINE_BUILD=w10`, patched wined3d) |
| Rise of the Witch-king (Patch 2.02 + HD Edition) | `scripts/play-rotwk.sh` (Wine 10.0 engine, `WINE_BUILD=w10`) |

Both games run on the Wine 10.0 engine (`engines/w10`, the Sikarugir build); each launch script
defaults `WINE_BUILD` to `w10`, so `WINE_BUILD=stable` is the override, not the other way round.
Wine 11.0/11.17 kill RotWK's main thread at the load→play transition, and fault the same way in
BFME2 whenever a second Wine process (the AutoHotkey helper) starts during the game's first ~8 s
(WoW64 32→64 syscall entry executed in 32-bit mode; full analysis in `patches/WINE-BUG-REPORT.md`).
Loading a skirmish takes ~12 s once `scripts/d3dx9-fix.sh` has run (~3 min without it: the second
half of the bar is Microsoft's d3dx9_27 converting textures in x87 code that Rosetta emulates
slowly; the script swaps in Wine's own d3dx9_27 with the fixes units need; `docs/LOAD-TIME.md`).

Both start borderless full-screen (windowed mode underneath, so alt-tab and Zoom are safe), with
screen-edge camera scrolling emulated by `ahk/edgescroll.ahk` (Ctrl+Alt+E toggles it).
`Esc` skips the intro. Logs go to `logs/`.

Before playing: turn off Low Power Mode (`sudo pmset -a powermode 2`, or System Settings →
Battery → Energy Mode → High Power). It visibly hurts frame pacing.

## Layout

Code and docs are in git; everything under the runtime directories is ignored and rebuilt by the
scripts (or downloaded), and the harness refuses to commit any of it.

```
env.sh          sourced by every script: WINE_BUILD=<name> selects engines/<name> + prefixes/<name>
scripts/        launch, setup and diagnostic scripts (below)
tools/          Python helpers (.big archives, workshop downloads, dump parsing) + lswin.swift
sagekit/        the art engine: formats, game install, taxonomy, Blender pipeline, painter, checks
assets/         our buildings as recipes (a Style per faction, a Building per building) - assets/README.md
config/         bfme2.reg, rotwk.reg (registry the launcher would write), options-bfme2.ini
ahk/            portable AutoHotkey + the scripts that drive the game window and menus
patches/        Wine bug write-ups, patches/wined3d (binary-patched DLLs), patches/nxcompat (NX_COMPAT experiment)
harness/        repo harness (rule engine); .githooks/ and .claude/settings.json wire it in
engines/        Wine builds, one dir each: w10 (Sikarugir Wine 10.0, patched wined3d — what both
                games play on), stable (Gcenx 11.0, patched wined3d; WoW64 bug, kept for comparison),
                staging (11.17), cx (CrossOver 24 engine); template/ + *.dylib = their support libs
prefixes/       Wine prefixes: stable (the real install; games, saves, Options.ini), w10, cx
                (games symlinked from stable). Options.ini: prefixes/<b>/drive_c/users/<you>/AppData/Roaming/My ... Files/
downloads/      tarballs, winetricks, downloads/dxvk (unused, renders black), downloads/resfix-maps (not installed)
wine/           Wine source + build trees for the upstream bug work (src/ clone, build-<label>/);
                scripts/build-wine.sh <label> installs the result as engines/src-<label> (patches/WINE-BUILD.md)
build/          compiled helpers (lswin); logs/  game logs, harness captures, memory samples
```

## What's in here

- `scripts/play-bfme2.sh`, `scripts/play-rotwk.sh` — launch (see Play). `scripts/play-bfme2-dxvk.sh`
  is the DXVK experiment (`d3d9=n`, renders black on MoltenVK; kept for when DXVK/MoltenVK improves).
- `scripts/test-skirmish.sh [label]` — hands-free: launches, clicks through to a skirmish, classifies the
  outcome (`GAME=bfme2|rotwk`, `WINE_BUILD=`, `KEEP_ON_HANG=1`). Takes over the screen ~8 min for
  RotWK, ~12 min for BFME2 (its map loads slower).
  `tools/classify-capture.py` is its screenshot classifier; `tools/lswin.swift` lists game windows
  (compiled into `build/` on first use). BFME2 needs a player profile in the prefix: with none,
  Skirmish opens a modal "Add New Profile" and the run never reaches a map. `prefixes/w10` has one.
- `scripts/setup-prefix.sh <build>` — build `prefixes/<build>` for `engines/<build>`, symlinking the
  game folders from `prefixes/stable` (idempotent; refuses to touch `stable`).
- `scripts/install-mod.sh <bfme2|rotwk> <workshop-guid|dir|zip>` — install a mod (or any set of
  `.big` files) into a game folder: backs up everything it overwrites as `<file>.premod.bak`,
  logs to `<gamedir>/mods-installed.log`, undone with `--revert`. See `docs/MODDING.md` for the
  art pipeline (Blender → W3D → `asset.dat`).
- `scripts/make-apps.sh` — puts "Battle for Middle-earth II.app" and "Rise of the Witch-king.app"
  in /Applications (Launchpad, Spotlight, Dock). Each is a plain bundle whose launcher execs the
  play script from this checkout, so a `git pull` is live in the app with nothing to rebuild;
  re-run only if the folder moves. Icons are pulled from the games' own executables by
  `tools/exe_icon.py`. `--remove` deletes them. They are AppleScript applets, not bare script
  bundles, because macOS denies a Finder-launched process every read under `~/Documents` unless
  the app can ask; the first launch shows a "access files in your Documents folder" prompt — Allow
  it once per app. Output goes to `logs/app-<game>.log`.
- `scripts/retina.sh on|off` — toggle Wine's Retina mode and both games' `Resolution` together.
- `scripts/inspect-hung.sh`, `scripts/monitor_mem.sh` — diagnostics: lldb/vmmap look at a hung game,
  memory samples every 15 s.
- `tools/fetch_game.py` — downloads any package from the community workshop (the same server the
  All-in-One Launcher uses): `BFME1|BFME2|RotWK` for base games, or a workshop GUID
  (`official-1` = BFME2 Patch 1.09, `official-2` = RotWK Patch 2.02). Verifies MD5s, resumable.
- `tools/prebake_textures.py <gamedir> [--revert]` — converts the ~60 % of texture bytes the games
  ship as uncompressed TGA (no mipmaps) into DDS with precomputed mip chains via `tools/tga2dds.c`
  (`cc -O2 -o build/tga2dds tools/tga2dds.c`), and patches every `.tga` reference in W3D, INI and
  `asset.dat` in place (same length). Each rewritten archive is kept as `.prebake.bak`. Measured
  231 s → 168 s on RotWK with Microsoft's d3dx9; the big win is `scripts/d3dx9-fix.sh`.
- `tools/bigtool.py` (list/extract/replace inside `.big` archives, BIGF and BIG4),
  `tools/neuter_gamelod.py` (the pre-menu crash fix), `tools/parse_minidump.py`.
- `ahk/edgescroll.ahk` — what the play scripts launch: borderless setup (title bar off, window to
  0,0 full size) and then resident, emulating screen-edge camera scrolling and offering the
  Cmd-Tab mouse rescue (see "Settings that matter"). One AutoHotkey process does both jobs because
  a second Wine process in the game's first seconds crashes it.
  `ahk/borderless.ahk` is the same borderless setup as a one-shot, kept for diagnostics;
  `ahk/autoskirmish.ahk` is the menu driver.
- `patches/README.md` — the wined3d empty-rect fix and the game-data edits;
  `patches/WINE-BUG-REPORT.md` — the WoW64 transition bug; `patches/nxcompat/install.sh` — the
  NX_COMPAT experiment (no effect; reverted — the prefixes hold the stock binaries again).
- `scripts/build-wine.sh <label>` — configure, build and install a from-source WoW64 Wine from the
  clone in `wine/src` into `engines/src-<label>` (x86_64 host under Rosetta, mingw-w64 PE side;
  `patches/WINE-BUILD.md` has the toolchain, the two traps, and the 10.0→11.0 bisect recipe).
  `patches/lock-whole-buffer/` — upstream d3d8/d3d9 patches + test for zero-size buffer locks.
- `scripts/wine-fixes.sh [--revert]` — builds our fixes to Wine 10.0 from source and installs them into
  `engines/$WINE_BUILD` (each DLL's engine copy kept as `<dll>.orig-<build>`): `patches/d3dx9-setrawvalue/`
  (the loading-time fix: SetRawValue for the units' bone palette, so Wine's fast d3dx9_27 can replace
  Microsoft's, ~170 s -> ~12 s) and `patches/wined3d-wow64-buffers/` (big battles: dynamic-buffer
  locks stop waiting for the render thread, a new `wined3d.so` writes the locked range straight into
  the GPU buffer, redundant state work removed, SSE2 instead of x87; synthetic battle frame 184 ->
  34 ms, `docs/PERFORMANCE.md`). `--revert` restores the engine's DLLs and removes `wined3d.so`.
  `scripts/d3dx9-fix.sh` is the old name, a wrapper.
- `scripts/perf-install.sh [--revert|--status]` — every performance fix in one step: the Wine fixes
  (`wine-fixes.sh`) and the game patch (`game-patch.sh`); `--revert` removes both, `--status` says
  what is installed (and which wined3d build). Switches that need no reinstall are in its header.
- `scripts/game-patch.sh [--revert|--test|--status|--bundle]` — the game-side performance patch for
  RotWK 2.02 (`gamepatch/`): a proxy `dinput8.dll` in the RotWK folder that patches the running game in
  memory before WinMain (the exe on disk is never changed) — DirectX lock without the Win32 mutex, SSE
  inverse square root / vector scaling / quaternion matrix / UI hit test / floor, the exit crash,
  per-draw debug-marker strings skipped, animation re-evaluation and decode shortcuts, SSE particle
  colours, indexed shadow-volume edge chaining, and (off by default) a frame limiter that sleeps,
  per-pass render timers (`passtimers`) and shadow volumes built on several cores (`shadowpar`,
  which checks itself against the serial result for its first 300 frames). Every patch checks the exact original bytes first, gives bit-identical
  results (so patched and unpatched players can play together) and can be switched off in
  `gamepatch.ini` or with `GAMEPATCH_<NAME>=0`. `play-rotwk.sh` loads it (`dinput8=n,b`) while
  `gamepatch.ini` is in the game folder; log in `logs/gamepatch.log`. `--test` runs the standalone
  bit-exactness tests (`gamepatch/tests/`) in a throwaway prefix; `--bundle` makes the two files a
  friend copies into his RotWK folder. Record: `docs/PERFORMANCE.md` §10–10.2.
- `tools/eipsample.c` — in-guest sampling profiler (`i686-w64-mingw32-gcc -O2 -o build/eipsample.exe
  tools/eipsample.c`, run with `wine build/eipsample.exe [secs] [ms]` while the game runs). Reads the
  guest EIP of the busiest thread, so time lands on the real module and offset, which macOS `sample`
  can't do under Rosetta. Not a debugger attach. It is how the d3dx9 load cost was found. Each
  sample also keeps the return addresses into the exe found on the stack ("R" lines);
  `tools/callstacks.py <output> --exe build/rotwk-re/disk.exe --funcs build/rotwk-re/funcs.txt
  --root 0x449cf8` turns them into inclusive time per function and a call tree
  (`build/rotwk-re/funcs.py` writes the function map, `namematch.py` names from Open-BFME-1).
- `tools/perfprobe.py <label> [secs] [--no-eip]` — measures a running game in one pass: frame times
  (start it with `WINEDEBUG=-all,+fps,+frametime`), per-thread CPU, optional eipsample profile
  (eipsample suspends threads; don't use it mid-fight). `scripts/bench-matchstart.sh <label>` runs a
  hands-free skirmish and probes the match-start view (same map and camera every run).
- `scripts/bench-battle.sh <label> [max_min]` — hands-free big-battle profile: starts the skirmish in
  `build/Skirmish.ini.aibattle` (idle human vs AIs), waits until frames fall under 20 FPS, then runs the
  read-only memory probe (`build/rotwk-re/memprobe.exe`, logic vs render split), perfprobe and
  `eipsample … main` (samples only the game thread). One game session at a time: `logs/.game-session`.
- `parallel/` — the multi-core framework for the game patch (not wired in yet): a fork/join worker
  pool (`pool/parallel.c`: spin-then-park, FPU state copied into jobs, faults retried serially), a
  deferred-call recorder (`pool/recorder.c`) and `parallel/DESIGN.md`. `parallel/pool/build-and-run.sh
  bench|rectest|place` builds and runs its tests under Wine in an isolated prefix, never beside a game.
- `tools/glcallcost.c` — what GL calls and buffer uploads cost a 32-bit program under WoW64 versus a
  64-bit one (build both with mingw; numbers in `docs/PERFORMANCE.md` §3).
- `scripts/bench-d3d9.sh <variant> [args]` + `tools/d3d9bench.c` — compares wined3d builds without the
  game (a 640x480 window for ~15 s per run, 3 runs, median; refuses to run beside a game). The bench
  replays WW3D2's per-frame D3D9 pattern (EA's Generals source, `dx8wrapper.cpp`): per-object state
  changes and `SetTransform(WORLD)`, static-mesh FFP draws, vs_1_1/2_0 skinned draws with the bone
  palette as VS constants, and draws appended to one shared 5000-vertex dynamic VB/IB with
  NOOVERWRITE/DISCARD range locks (defaults ~2000 draws/frame, 300 dynamic). `<variant>`: `stock`
  (the engine's `wined3d.dll.orig-w10`), `engine` (what is installed), `sse2`/`x87`
  (`build/wined3d-variants/wined3d-<v>.dll`) or a path; the DLL is copied next to the exe with its
  "Wine builtin DLL" marker cleared and loaded with `wined3d=n` (Wine otherwise swaps the engine's
  builtin back in), and the bench checks in-process which file it runs. Prints fps, mean/p50/p95/p99
  frame ms and the app thread's split (`lock fill unlock state draw present`; `present` = waiting
  for the render thread); medians go to `logs/bench-d3d9.log`. Knobs: `--objects --dyn-frac
  --ffp-frac --vs 11|20 --bones --dyn-verts --redundant --clip --order mix|grouped --secs`, env
  `WINED3D_WOW64_BUFFERS=off|pin|stream`, `WINE_D3D_CONFIG=renderer=vulkan`, `RUNS=`. `--crc [--bmp f]`
  checksums one deterministic frame: all builds agree with `--order grouped`; in the default
  interleaved order stock wined3d is itself non-deterministic (stray triangles from the dynamic VB).
  Calibration 2026-09-24, defaults, median of 3: stock 75 ms, `sse2` 52 (`off` 73, `pin` 44), `x87` 49
  (+25 ms of app-thread time in DrawIndexedPrimitive, hidden while the render thread is the limit).
  Vulkan crashes compiling ps_1_1 in vkd3d-shader; FFP and vs_2_0 run there, ~7x slower than GL.
  UI-side knobs: `--radar N` (one-pixel radar locks), `--text N` (text-surface locks), `--relock N`
  (managed-buffer relocks), `--dyntex N` (dynamic-texture DISCARD), `--cpu-ms N` (stand-in game work
  per frame), `--programs N` (new GLSL programs at first draw; prints a `PROGRAMS` line).
- `tools/d3d9lockcheck.c` — correctness reproducer for wined3d's app-thread map paths (fixes
  0012–0016): radar locks between draws, systemmem UpdateTexture/UpdateSurface, managed and systemmem
  buffer relocks with read-back, DISCARD sub-rectangles, two mip levels locked at once. Build with
  i686 mingw, run under Wine; prints failures and exits non-zero on any.
- `tools/d3dx9fxbench.c` — replays the game's per-batch / per-mesh `ID3DXEffect` calls (shadow-map
  pass + main view) on the real `.fxo` effects against any `d3dx9_27.dll` build, without the game;
  `--hash` checksums every device call the effects make, so two builds can be proven identical
  (build and run lines in its header).
- `tools/make_group_pack.py <rotwk|bfme2>` — builds the **group pack**, `!!!!!!!!!!group-pack.big`, from
  your own install: INI copies with our tweaks (4000 particles, heat effects off, camera max
  height 700) that override the game's own because the name sorts first. Install with
  `scripts/install-mod.sh rotwk build/group-pack/rotwk/install`; everyone playing together needs the
  same pack (`MULTIPLAYER.md`). The edits are the `EDITS` list at the top of the tool.
- `tools/w3d_fixup.py <original.w3d> <exported.w3d>` — repairs what the OpenSAGE Blender add-on drops or
  changes on re-export (materials and texture references, mesh version 5.0, surface types, pivot
  fixups, and it generates the AABTREE collision trees BFME2 requires). Details in `docs/MODDING.md` §h.
- `tools/asset_dat.py show|check|patch|texture <asset.dat> ...` — `asset.dat`: BFME2 caches every
  model's chunk offsets and sizes and reads them blind, so an edited model must have its record
  patched to match (`check` says whether it does; the first write keeps `asset.dat.orig`); `texture`
  registers a new texture (without a record it renders magenta). Both tools are command lines over
  `sagekit/formats/`.
- `python3 -m sagekit list|validate|inventory|budget|build` — builds new art for a building from
  your install: `inventory dwarves/fortress` lists every part and lifecycle state the game draws,
  `build dwarves/fortress` runs extract → Blender geometry/bake/paint → export → fix-up → asset
  cache → checks → before/after renders into `build/assets/`. Rules and layout: `assets/README.md`.
- `harness/README.md` — what the repo harness enforces and why.

## Settings that matter

- `Options.ini` `Resolution`: must be a real mode. Native points are `1512 982`; with Wine's
  Retina mode (`scripts/retina.sh on`) `3024 1964` renders
  every physical pixel (4× the detail, GPU barely notices, text gets smaller).
- Graphics tiers are all `UltraHigh`. The engine's own ceiling is defined in
  `data\ini\gamelod.ini` inside `ini.big`; it can be raised further (particle cap etc.).
- Frame rate: hard 30 FPS, tied to the simulation. Unlocking it speeds the game up. Don't.
- Mouse: the engine reads the mouse through Windows messages (DirectInput is keyboard-only).
  Wheel zoom needs `HKCU\Software\Wine\Mac Driver\UsePreciseScrolling = n` (set in all
  prefixes). **Screen-edge scrolling is disabled by the engine in windowed mode** (the only mode
  that works here), so `ahk/edgescroll.ahk` emulates it: while the cursor is within 4 points of
  the game window's edge it holds the matching arrow key(s) down (a corner holds two), and it
  keeps out of the way while a mouse button is held, so right-drag rotation is unaffected.
  Toggle it with **Ctrl+Alt+E** (Control+Option+E; Scroll Lock also works on a PC keyboard) — a
  tooltip confirms. Margin: pass it as an argument (`edgescroll.ahk 8`) or edit `margin` at the
  top of the script. Right-drag and the arrow keys still work as before.
- **Mouse after Cmd-Tab.** On the Wine 10 engine, switching to another app and back can leave the
  3D view without mouse (and keyboard) input — Sikarugir issue #237. Cause, from wine-10.0's
  `dlls/winemac.drv`: `macdrv_app_deactivated()` calls `NtUserClipCursor(NULL)` and hands the
  foreground to the desktop window, `applicationDidResignActive` does `invalidateGotFocusEvents` +
  `releaseMouseCapture`, and `macdrv_app_activated()` restores *none* of it — recovery depends
  entirely on a later `WINDOW_GOT_FOCUS` → `WM_MOUSEACTIVATE` → `NtUserSetForegroundWindow`
  round-trip that a busy D3D window can miss. The Cocoa side re-clips the cursor independently,
  which is why the pointer looks confined while nothing responds.
  - There is **no registry fix**. The full set of values winemac.drv 10.0 reads (`setup_options()`
    in `dlls/winemac.drv/macdrv_main.c`) contains only two mouse-clipping knobs, and both change
    *how* clipping is done, not whether focus is restored. They are the only things worth trying,
    and only on a throwaway basis — do not leave them set if they don't help:
    ```sh
    WINE_BUILD=w10 . ./env.sh
    wine reg add 'HKCU\Software\Wine\Mac Driver' /v UseConfinementCursorClipping /t REG_SZ /d N /f
    wine reg add 'HKCU\Software\Wine\Mac Driver' /v CursorClippingLocksWindows  /t REG_SZ /d N /f
    ```
    (`CaptureDisplaysForFullscreen=Y` was already tried in the issue and does nothing here; the
    `UseTakeFocus` / `GrabFullscreen` advice found on forums is X11-only — winemac.drv never
    reads those names.)
  - What we *can* do from here: **Ctrl+Alt+R** in `ahk/edgescroll.ahk` performs the step the driver
    skips — `ClipCursor(NULL)`, then `SetForegroundWindow` on the game window from AutoHotkey's
    separate Wine process (same prefix, so it reaches the game's thread), then a 1-px cursor nudge.
    That hotkey is deliberately *not* window-context-guarded, because when the bug bites Wine's
    foreground is the desktop window. To have it run automatically on every activation, set
    `recaptureOnActivate := true` at the top of the script. Both are unverified — test them.
  - The only confirmed fix upstream is a newer Wine (11.x; the issue reporter verified 11.11, and
    Sikarugir say `WS11WineSikarugir11.0` resolves it). We can't take it: Wine 11 kills the main
    thread at the load→play transition (`patches/WINE-BUG-REPORT.md`). Until then, treat Cmd-Tab
    mid-match as risky: try Ctrl+Alt+R, and if that fails, save and relaunch.
- Retina (`scripts/retina.sh on`) sets RetinaMode and both games' `Resolution` in every prefix
  (w10 and stable), so it does not depend on which engine you launch with. The earlier note that
  Retina "needs the empty-rect wined3d fix" was wrong: that binary patch only silences warnings
  (`patches/README.md` §1); the crashes it was blamed for were the WoW64 bug, which the w10 engine
  does not have. The patched DLL is installed in `engines/w10` anyway (stock copy kept beside it as
  `wined3d.dll.orig-w10`); harmless either way.
- Hands-free runs (`scripts/test-skirmish.sh`) start the AutoHotkey helper with edge scrolling
  off (`EDGESCROLL=off`), so a parked cursor cannot hold arrow keys while the menus are driven.
  **If you pick up a game the harness left running, press Ctrl+Option+E once to turn it on**
  (the harness log says so when it hands over). `ahk/edgescroll.log` records geometry, focus and
  every key press, so a session where edge scrolling "did nothing" is diagnosable afterwards.
- Loading is faster than the docs used to say: with Wine's logging quiet (the play scripts'
  default) RotWK reaches the map in ~3 min from launch, ~190 s of it on the loading bar;
  `WINEMSYNC=1` (CrossOver-style fast sync, present in the w10 engine but off) measured ~7 %
  faster, inside the noise so far — opt in with `WINEMSYNC=1 scripts/play-rotwk.sh`
  (`docs/LOAD-TIME.md`).
- `game.dat` must not have the 4 GB (LARGEADDRESSAWARE) flag under Wine.
- Keep every prefix at Windows 10 (`winecfg -v win10`): Windows XP crashes wined3d at startup.

## Known limits

- 30 FPS ceiling (engine design).
- Exclusive fullscreen is unusable under Wine's Mac driver (minimize + black on focus loss);
  borderless windowed is the equivalent.
- Modified `ini.big` files (camera, LOD table) must match between multiplayer peers.
- Multiplayer (Mac ↔ PC, over the internet): see `MULTIPLAYER.md` — ZeroTier virtual LAN, free up
  to 10 devices, setup, turning it off, privacy.
