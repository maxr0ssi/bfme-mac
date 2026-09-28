# Reference: every script, tool and directory

The lab notebook's index. The player's view is [PLAYING.md](PLAYING.md); the measured record behind
the performance work is [PERFORMANCE.md](PERFORMANCE.md).

## Layout

Code and docs are in git; everything under the runtime directories is ignored and rebuilt by the
scripts (or downloaded), and the harness refuses to commit any of it.

```
env.sh          sourced by every script: WINE_BUILD=<name> selects engines/<name> + prefixes/<name>
scripts/        launch, setup and diagnostic scripts (below)
tools/          Python helpers (.big archives, PE flags, dump parsing) + lswin.swift
sagekit/        the art engine: formats, game install, taxonomy, Blender pipeline, painter, checks
assets/         our buildings as recipes (a Style per faction, a Building per building) - assets/README.md, map in docs/ART.md
config/         bfme2.reg, rotwk.reg (registry the launcher would write), options-bfme2.ini
ahk/            portable AutoHotkey + the scripts that drive the game window and menus
patches/        Wine bug write-ups, patches/wined3d (binary-patched DLLs), patches/nxcompat (NX_COMPAT experiment)
harness/        repo harness (rule engine); .githooks/ and .claude/settings.json wire it in
engines/        Wine builds, one dir each. w10 (Sikarugir Wine 10.0 with our fixes) is what both games
                play on and what install.sh sets up; template/ + *.dylib are its support libraries.
                The development machine also keeps stable (Gcenx 11.0; WoW64 bug), staging (11.17)
                and cx (CrossOver 24) for comparison.
prefixes/       Wine prefixes. w10 holds the games, saves and Options.ini
                (prefixes/w10/drive_c/users/<you>/AppData/Roaming/My ... Files/). On the development
                machine the games live in stable and w10 symlinks them (scripts/setup-prefix.sh).
downloads/      tarballs (the Wine engine, AutoHotkey), winetricks, downloads/dxvk (unused, renders black), downloads/resfix-maps (not installed)
wine/           Wine source + build trees for the upstream bug work (src/ clone, build-<label>/);
                scripts/build-wine.sh <label> installs the result as engines/src-<label> (patches/WINE-BUILD.md)
build/          compiled helpers (lswin); logs/  game logs, harness captures, memory samples
```

## Install and play

- `scripts/install.sh --bfme2 <dir> [--rotwk <dir>] [--from <release.tar.gz>] [--group-pack] [--no-apps]`
  — a fresh setup from your own game folders: downloads the latest GitHub release of the fixes (or
  uses `--from`, checked against GitHub's SHA-256 and its own `SHA256SUMS`), the Wine engine (Sikarugir
  `WS12WineSikarugir10.0_6` + `Template-1.0.18`) and AutoHotkey 1.1.37.02, each pinned by SHA-256;
  installs the patched Wine DLLs from the release file; creates `prefixes/w10`; copies the games in
  (APFS clones, so no extra space on the same volume) and applies `tools/neuter_gamelod.py` and
  `tools/pe_laa.py` to the copies (4 GB on for RotWK, off for BFME2); writes the registry, the CD key (asked for; Enter
  generates one as the All-in-One Launcher does) and an `Options.ini` at the display's resolution;
  installs the game patch if the RotWK exe matches every patch site. `--status`; `--uninstall`
  moves the engine and prefix to a `.trash-*` folder. No winetricks: the games import only
  `d3dx9_27`, which the patched builtin provides.
- `scripts/make-release.sh` — packages the installed Wine fixes and the game patch as
  `build/release/bfme-mac-fixes-<date>-<commit>.tar.gz` (the `--from` file), with `SOURCES.md`,
  `COPYING.LIB` and `SHA256SUMS`, and prints the `gh release create` line that publishes it.
  Refuses if the engine's DLLs differ from the build tree.
- `scripts/play-bfme2.sh`, `scripts/play-rotwk.sh` — launch ([PLAYING.md](PLAYING.md)). `scripts/play-bfme2-dxvk.sh`
  is the DXVK experiment (`d3d9=n`, renders black on MoltenVK; kept for when DXVK/MoltenVK improves).
- `scripts/make-apps.sh` — puts "Battle for Middle-earth II.app" and "Rise of the Witch-king.app"
  in /Applications (Launchpad, Spotlight, Dock). Each is a plain bundle whose launcher execs the
  play script from this checkout, so a `git pull` is live in the app with nothing to rebuild;
  re-run only if the folder moves. Icons are pulled from the games' own executables by
  `tools/exe_icon.py`. `--remove` removes the ones that launch this checkout. They are AppleScript applets, not bare script
  bundles, because macOS denies a Finder-launched process every read under `~/Documents` unless
  the app can ask; the first launch shows a "access files in your Documents folder" prompt — Allow
  it once per app. Output goes to `logs/app-<game>.log`.
- `scripts/retina.sh on|off` — toggle Wine's Retina mode and both games' `Resolution` together.
- `ahk/edgescroll.ahk` — what the play scripts launch: borderless setup (title bar off, window to
  0,0 full size) and then resident, emulating screen-edge camera scrolling and offering the
  Cmd-Tab mouse rescue ([PLAYING.md](PLAYING.md), "Settings that matter"). One AutoHotkey process does both jobs because
  a second Wine process in the game's first seconds crashes it.
  `ahk/borderless.ahk` is the same borderless setup as a one-shot, kept for diagnostics;
  `ahk/autoskirmish.ahk` is the menu driver.
- `scripts/install-mod.sh <bfme2|rotwk> <dir|zip>` — install a mod (or any set of
  `.big` files) into a game folder: backs up everything it overwrites as `<file>.premod.bak`,
  logs to `<gamedir>/mods-installed.log`, undone with `--revert`. See `docs/MODDING.md` for the
  art pipeline (Blender → W3D → `asset.dat`).
- `tools/make_group_pack.py <rotwk|bfme2>` — builds the **group pack**, `!!!!!!!!!!group-pack.big`, from
  your own install: INI copies with our tweaks (4000 particles, heat effects off, camera max
  height 700) that override the game's own because the name sorts first. Install with
  `scripts/install-mod.sh rotwk build/group-pack/rotwk/install`; everyone playing together needs the
  same pack (`MULTIPLAYER.md`). The edits are the `EDITS` list at the top of the tool.

## Game files and fixes

- `tools/pe_laa.py [--on|--off] <file>...` — shows, sets or clears the large-address-aware (4 GB)
  flag of a Windows executable (RotWK 2.02 ships `lotrbfme2ep1.exe` and `game.dat` with it on and
  plays that way on w10; the crash once blamed on it was Wine 11's, `docs/MEMORY-4GB.md`); keeps
  `<file>.preLAAoff.bak` / `<file>.preLAAon.bak`.
- `scripts/laa-probe.sh [args]` + `tools/laaprobe.c` — does a 4 GB-aware 32-bit program work under
  `engines/$WINE_BUILD`: address space, top-down allocations, exceptions and callbacks on a stack
  above 2 GB, D3D9 locks above 2 GB drawn and read back, the games' DLLs; `--fill-low` first uses
  up the low 2 GB. Throwaway prefix `build/prefix-laa`, no game. Findings: `docs/MEMORY-4GB.md`.
- `tools/bigtool.py` (list/extract/replace inside `.big` archives, BIGF and BIG4),
  `tools/neuter_gamelod.py` (the pre-menu crash fix), `tools/parse_minidump.py`.
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
  friend copies into their RotWK folder. Record: `docs/PERFORMANCE.md` §10–10.2.
- `scripts/perf-install.sh [--revert|--status]` — every performance fix in one step: the Wine fixes
  (`wine-fixes.sh`) and the game patch (`game-patch.sh`); `--revert` removes both, `--status` says
  what is installed (and which wined3d build). Switches that need no reinstall are in its header.
- `scripts/wine-fixes.sh [--revert]` — builds our fixes to Wine 10.0 from source and installs them into
  `engines/$WINE_BUILD` (each DLL's engine copy kept as `<dll>.orig-<build>`): `patches/d3dx9-setrawvalue/`
  (the loading-time fix: SetRawValue for the units' bone palette, so Wine's fast d3dx9_27 can replace
  Microsoft's, ~170 s -> ~12 s) and `patches/wined3d-wow64-buffers/` (big battles: dynamic-buffer
  locks stop waiting for the render thread, a new `wined3d.so` writes the locked range straight into
  the GPU buffer, redundant state work removed, SSE2 instead of x87; synthetic battle frame 184 ->
  34 ms, `docs/PERFORMANCE.md`). `--revert` restores the engine's DLLs and removes `wined3d.so`.
  `scripts/d3dx9-fix.sh` is the old name, a wrapper.
- `scripts/build-wine.sh <label>` — configure, build and install a from-source WoW64 Wine from the
  clone in `wine/src` into `engines/src-<label>` (x86_64 host under Rosetta, mingw-w64 PE side;
  `patches/WINE-BUILD.md` has the toolchain, the two traps, and the 10.0→11.0 bisect recipe).
  `patches/lock-whole-buffer/` — upstream d3d8/d3d9 patches + test for zero-size buffer locks.
- `patches/README.md` — the wined3d empty-rect fix and the game-data edits;
  `patches/WINE-BUG-REPORT.md` — the WoW64 transition bug; `patches/nxcompat/install.sh` — the
  NX_COMPAT experiment (no effect; reverted — the prefixes hold the stock binaries again).
- `parallel/` — the multi-core framework for the game patch (not wired in yet): a fork/join worker
  pool (`pool/parallel.c`: spin-then-park, FPU state copied into jobs, faults retried serially), a
  deferred-call recorder (`pool/recorder.c`) and `parallel/DESIGN.md`. `parallel/pool/build-and-run.sh
  bench|rectest|place` builds and runs its tests under Wine in an isolated prefix, never beside a game.

## Measuring

- `scripts/measure-session.sh on|sample [label]|summary [since]|off` — one measuring session played by
  you: `on` turns the game patch's diagnostics on (passtimers, renderstats, particlestats; ~2 ms/frame),
  `sample` takes a 20 s read-only stack sample of the main thread during a fight and writes the
  inclusive call tree to `logs/incl-<label>-tree.txt`, `summary` prints the frame-time distribution and
  the latest per-pass lines, `off` turns the diagnostics off again.
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
- `tools/fpsample.c` + `tools/fpsym.py` — inclusive profile of one thread of a bench under Wine: the
  sampler walks the frame-pointer chain (Wine's PE DLLs keep frame pointers), the script symbolizes it
  with `i686-w64-mingw32-addr2line` on the `-g` builds and prints inclusive/self time per function and
  the callees (`--children F`) or callers (`--parents F`) of a function.
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
- `tools/texmem32.c` — what a D3D9 texture or buffer byte costs in the 32-bit address space under
  the Wine in use: creates `--mb N` of managed (or `--pool default|sysmem`) textures the way WW3D2
  loads them, draws, relocks (`--relock`, checks the bytes), evicts, releases, and after each step
  walks the 2 GB with VirtualQuery (committed, reserved, largest free block, bytes per payload
  byte, ms per step); `--batches B` loads until CreateTexture fails, `--vb N --vbpool` does buffers;
  `CRC` lines checksum the drawn textures. i686 mingw, run in a throwaway prefix. `docs/MEMORY-2GB.md`.
- `tools/d3dx9fxbench.c` — replays the game's per-batch / per-mesh `ID3DXEffect` calls (shadow-map
  pass + main view) on the real `.fxo` effects against any `d3dx9_27.dll` build, without the game;
  `--hash` checksums every device call the effects make, so two builds can be proven identical.
  `--mode dev --draw 1` also binds buffers and draws every mesh and presents each frame, which times the
  whole per-mesh path down through d3d9 and wined3d (Present = the wait for the render thread);
  `--bones lo,hi`, `--share P` and `--batch-ints 1` make the per-object setters look like the game's;
  `--crc` draws a deterministic scene, reads every frame back and prints an image checksum, the
  pixel-level check for d3d9/wined3d changes on the effect path (build and run lines in its header).
- `tools/glcallcost.c` — what GL calls and buffer uploads cost a 32-bit program under WoW64 versus a
  64-bit one (build both with mingw; numbers in `docs/PERFORMANCE.md` §3).
- `scripts/memwatch.sh [secs]` — how close a match gets to the game's address space (2 GB, 4 GB with
  the large-address flag): start it in a Terminal while the game runs (menu or match); every 2 s `tools/memwatch.c` (built on first
  use) walks the game's address space read-only from a second Wine process and `tools/memwatch.py`
  adds the macOS side (resident, footprint) into `logs/memwatch-<date>.csv`: committed, reserved,
  largest free block (the out-of-memory predictor), free blocks over 16 MB, committed by type. Stops
  with the game or Ctrl-C and prints the summary; `scripts/memwatch.sh summary [csv] [--png]` again
  later. Each query runs on the game's main thread (~50 µs), so it paces itself under 2 % of it.
- `scripts/inspect-hung.sh`, `scripts/monitor_mem.sh` — diagnostics: lldb/vmmap look at a hung game,
  memory samples every 15 s.

## Art

- `sagekit/install.py` — scoped faction installation over the current asset caches; `python3 -m sagekit install elves --check` stages without installing, `install elves --revert` restores the last scoped backup and refuses to erase later changes. `python3 -m sagekit.install` checks multi-pack preservation, duplicate cache records, rollback and revert guards using temporary files.
- `sagekit/formats/w3dmesh.py` — W3D mesh assembly; `python3 -m sagekit.formats.w3dmesh` checks optional colour-slot mapping and required-data guards.
- `sagekit/blender/lifecycle.py` — construction/damage fitting; `check_match_offset()` under Blender checks translated construction coordinates against the built floodgate doors while preserving the zero-offset path.
- `assets/dwarves/porter/install.py` — `python3 -m assets.dwarves.porter.install [--check|--revert|--selfcheck]`: install/repair the reviewed RotWK builder and player-colour mapping; preserves unrelated records, composes active mappings, accepts legacy receipts and guards scoped reverts.
- `assets/dwarves/porter/unit.py` — `python3 -m assets.dwarves.porter.unit --render`: build and check the selectable Dwarven builder prototype and before/after previews; no installation.
- `assets/dwarves/troops/review.py` — Extract the active Dwarven troop source roster and `--render` an offline idle-pose gallery; preserves source hashes, hides upgrade-gated equipment and never installs or launches the game.
- `assets/dwarves/troops/catalog.py` — Explicit troop, upgrade, passenger, LOD and authored-animation manifest; runnable source/condition/hierarchy validation.
- `assets/dwarves/troops/infantry.py` — Fitted infantry, banner and passenger metalwork with original geometry/UV/bone preservation checks.
- `assets/dwarves/troops/siege.py` — Fitted Battlewagon, Demolisher and Catapult joinery, including construction/death fragments; runnable source checks.
- `assets/dwarves/troops/paint.py` — Private original-size palette sheets with protected faces/fur, original mip counts and retained DXT3/DXT5 alpha blocks.
- `assets/dwarves/troops/build.py` — Build private troop models, texture/house-colour aliases and visual-only INI edits; stage archive/caches without installation.
- `assets/dwarves/troops/preview.py` — Paired stills and actual decoded-motion GIFs with upgrade visibility, attached wagon crews and a local review gallery.
- `assets/dwarves/troops/motion_check.py` — All-authored-clip Blender audit of matching rigs, finite poses/additions and exact original geometry motion, recording inherited source defects.
- `assets/dwarves/troops/audit.py` — Verify staged package isolation, visual-only INI edits, cache preservation, original geometry, protected pixels, alpha/mips and unchanged live installation.
- `assets/dwarves/porter/design.py` — builder cart, supplies, outfit and tools bound to the original rig; keeps the original helmet.
- `assets/dwarves/porter/preview.py` — Blender preview worker invoked by the builder recipe; original animation poses decoded with the installed OpenSAGE add-on.
- `python3 -m sagekit list|validate|inventory|budget|build` — builds new art for a building from
  your install: `inventory dwarves/fortress` lists every part and lifecycle state the game draws,
  `build dwarves/fortress` runs extract → Blender geometry/bake/paint → export → night lights
  (`sagekit/nightlights.py`) → fix-up → derive → lifecycle (construction, really damaged and rubble models rebuilt around the new body along EA's
  pieces and animations, `sagekit/lifecycle.py`) → asset cache → checks → before/after renders into
  `build/assets/` (`renders/lifecycle/<model>.png` for the lifecycle models). Rules and layout:
  `assets/README.md`.
  `names dwarves --write` regenerates `assets/dwarves/NAMES.md`, every model and texture name the
  faction ships (pick new names against it).
  `owners elves` lists the models and sheets the faction shares with other factions (scan cached in
  `build/assets/_ownership.json`; `sheets` skips shared sheets, `validate` fails a recipe that would
  change another faction's art). `new elves --write` writes one stub recipe per design unit of EA's
  (never over an existing one). `measure elves/fortress` measures EA's body into `work/measure.json`
  (footprint, planes, levels, setbacks, openings, heads, symmetry; `sagekit/measure.py` for design()).
- `tools/w3d_fixup.py <original.w3d> <exported.w3d>` — repairs what the OpenSAGE Blender add-on drops or
  changes on re-export (materials and texture references, mesh version 5.0, surface types, pivot
  fixups, and it generates the AABTREE collision trees BFME2 requires). Details in `docs/MODDING.md` §h.
- `tools/asset_dat.py show|check|patch|texture <asset.dat> ...` — `asset.dat`: BFME2 caches every
  model's chunk offsets and sizes and reads them blind, so an edited model must have its record
  patched to match (`check` says whether it does; the first write keeps `asset.dat.orig`); `texture`
  registers a new texture (without a record it renders magenta). Both tools are command lines over
  `sagekit/formats/`.

## Development

- `scripts/setup-prefix.sh <build>` — the development setup: build `prefixes/<build>` for
  `engines/<build>`, symlinking the game folders from `prefixes/stable` (idempotent; refuses to
  touch `stable`). New installs use `scripts/install.sh`.
- `harness/README.md` — what the repo harness enforces and why.

## Experiments and dead ends

Kept for the record. The hands-free runs take over the screen and are not used any more: the
player plays, the agents read logs (AGENTS.md). The DXVK and NX_COMPAT experiments are under
`scripts/play-bfme2-dxvk.sh` and `patches/README.md` above; the Wine 11 bisect is in
[BISECT.md](BISECT.md); the old state snapshot is [history/STATE-2026-09-23.md](history/STATE-2026-09-23.md).

- `scripts/test-skirmish.sh [label]` — hands-free: launches, clicks through to a skirmish, classifies the
  outcome (`GAME=bfme2|rotwk`, `WINE_BUILD=`, `KEEP_ON_HANG=1`). Takes over the screen ~8 min for
  RotWK, ~12 min for BFME2 (its map loads slower).
  `tools/classify-capture.py` is its screenshot classifier; `tools/lswin.swift` lists game windows
  (compiled into `build/` on first use). BFME2 needs a player profile in the prefix: with none,
  Skirmish opens a modal "Add New Profile" and the run never reaches a map. `prefixes/w10` has one.
- `scripts/bench-battle.sh <label> [max_min]` — hands-free big-battle profile: starts the skirmish in
  `build/Skirmish.ini.aibattle` (idle human vs AIs), waits until frames fall under 20 FPS, then runs the
  read-only memory probe (`build/rotwk-re/memprobe.exe`, logic vs render split), perfprobe and
  `eipsample … main` (samples only the game thread). One game session at a time: `logs/.game-session`.
- `tools/prebake_textures.py <gamedir> [--revert]` — converts the ~60 % of texture bytes the games
  ship as uncompressed TGA (no mipmaps) into DDS with precomputed mip chains via `tools/tga2dds.c`
  (`cc -O2 -o build/tga2dds tools/tga2dds.c`), and patches every `.tga` reference in W3D, INI and
  `asset.dat` in place (same length). Each rewritten archive is kept as `.prebake.bak`. Measured
  231 s → 168 s on RotWK with Microsoft's d3dx9; the big win is `scripts/d3dx9-fix.sh`.

| `assets/elves/porter/unit.py` | Build/check the selectable Elven craftsman with original rig/anatomy and private diffuse/house-colour atlas; `--render` makes matched motion previews. |
| `assets/elves/porter/design.py` | Curved birch cart, open-spoke wheels, ivory masonry and plans, attached to the original porter bones. |
| `assets/elves/porter/preview.py` | Offline OpenSAGE-decoded Elven builder poses, including source opaque-texture alpha handling. |
| `assets/elves/porter/install.py` | Stage `--check`, reviewed scoped install and guarded `--revert` for the Elven builder; preserves active house-colour mappings and unrelated cache records. |

- `assets/elves/troops/catalog.py` — Active Elven troop, upgrade, banner, natural-creature and animation manifest with offline validation; heroes/builders excluded.
- `assets/elves/troops/art.py` — Fitted leafwork and private neutral-cloth/silver/gold sheets, retaining original bodies, rigs, protected pixels and alpha.
- `assets/elves/troops/build.py` — Reuse the private troop pipeline to stage Elven models, textures and scoped visual INI edits without installation.
- `assets/elves/troops/preview.py` — Paired Elven equipment stills and decoded-motion comparisons in a local review gallery.
- `assets/elves/troops/audit.py` — Read-only Elven staged-package validation and optional full matching-source animation audit.

- `assets/dwarves/troops/posing.py` — Troop preview skinning with original primary/secondary positions and bone weights; shared by Dwarven, Elven and Men motion reviews.

- `assets/men/troops/catalog.py` — Active Men of the West troop, equipment, banner, cavalry mode and siege-state manifest with source validation.
- `assets/men/troops/art.py` — Private silver/steel, neutral-cloth and restrained-gold troop sheets plus supported fitted edging; original blended bodies preserved.
- `assets/men/troops/build.py` — Stage isolated Men troop models, textures, masks and scoped visual INI overrides without installation.
- `assets/men/troops/preview.py` — Paired Men troop equipment and original-animation comparisons using weighted skinning.
- `assets/men/troops/audit.py` — Verify private Men art, complete source skin arrays, object scope, animations and current review media.
- `assets/men/atlas.py` — Measured original Gondor fortress sheet regions for the citadel pilot.
- `assets/men/style.py` — Citadel pilot palette and paint stack: neutral limestone, charcoal slate and forged steel.
- `assets/men/fortress/building.py` — Private Men citadel recipe preserving original body and shared Arnor assets.
