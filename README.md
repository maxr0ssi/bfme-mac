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
- `scripts/d3dx9-fix.sh [--revert]` — the loading-time fix: builds Wine 10.0's d3dx9_27.dll with
  `patches/d3dx9-setrawvalue/` (SetRawValue for the units' bone palette, see its README), installs it
  into `engines/$WINE_BUILD` keeping `d3dx9_27.dll.orig-<build>`, and sets `*d3dx9_27=builtin` in the
  prefix; `--revert` undoes both. `scripts/setup-prefix.sh` keeps the override on new prefixes.
- `tools/eipsample.c` — in-guest sampling profiler (`i686-w64-mingw32-gcc -O2 -o build/eipsample.exe
  tools/eipsample.c`, run with `wine build/eipsample.exe [secs] [ms]` while the game runs). Reads the
  guest EIP of the busiest thread, so time lands on the real module and offset, which macOS `sample`
  can't do under Rosetta. Not a debugger attach. It is how the d3dx9 load cost was found.
- `tools/make_group_pack.py <rotwk|bfme2>` — builds the **group pack**, `!!!!!!!!!!group-pack.big`, from
  your own install: INI copies with our tweaks (4000 particles, heat effects off, camera max
  height 1000) that override the game's own because the name sorts first. Install with
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
