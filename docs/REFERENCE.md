# Reference: every script, tool and directory

The player's view is [PLAYING.md](PLAYING.md); the measured record behind the performance work is
[PERFORMANCE.md](PERFORMANCE.md).

## Layout

Code and docs are in git; everything under the runtime directories is ignored and rebuilt by the
scripts (or downloaded), and the harness refuses to commit any of it.

```
env.sh          sourced by every script: WINE_BUILD=<name> selects engines/<name> + prefixes/<name>
scripts/        launch, setup and diagnostic scripts (below)
tools/          Python helpers (.big archives, PE flags, dump parsing) + lswin.swift
sagekit/        the art engine: formats, game install, taxonomy, Blender pipeline, painter, checks
assets/         our buildings as recipes (a Style per faction, a Building per building) - assets/README.md, map in docs/ART.md
config/         bfme2.reg, rotwk.reg (registry the launcher would write)
ahk/            portable AutoHotkey + the scripts that drive the game window and menus
patches/        Wine patch series, bug write-ups and the NX_COMPAT experiment (patches/README.md)
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

- `scripts/install.sh --bfme2 <dir> [--rotwk <dir>] [--from <release.tar.gz>] [--group-pack] [--buildings [list]] [--no-apps]`
  — a fresh setup from your own game folders: downloads the latest GitHub release of the fixes (or
  uses `--from`, checked against GitHub's SHA-256 and its own `SHA256SUMS`), the Wine engine (Sikarugir
  `WS12WineSikarugir10.0_6` + `Template-1.0.18`) and AutoHotkey 1.1.37.02, each pinned by SHA-256;
  installs the patched Wine DLLs from the release file; creates `prefixes/w10`; copies the games in
  (APFS clones, so no extra space on the same volume) and applies `tools/neuter_gamelod.py` and
  `tools/pe_laa.py` to the copies (4 GB on for RotWK, off for BFME2); writes the registry, the CD key (asked for; Enter
  generates one as the All-in-One Launcher does) and an `Options.ini` at the display's resolution;
  installs the game patch if the RotWK exe matches every patch site; with `--buildings` (asked
  otherwise, default no) the release's building packs (`sagekit/pack.py`), each checked against
  the player's game first. `--buildings`/`--no-buildings` alone add or remove them on an existing
  install. `--status`; `--uninstall` takes the buildings out and moves the engine and prefix to a
  `.trash-*` folder. No winetricks: the games import only `d3dx9_27`, which the patched builtin provides.
- `scripts/make-release.sh [--buildings [list]]` — packages the installed Wine fixes and the game patch as
  `build/release/bfme-mac-fixes-<date>-<commit>.tar.gz` (the `--from` file), with `SOURCES.md`,
  `LICENSE`, `NOTICE` (LGPL terms for the Wine patches), `COPYING.LIB` and `SHA256SUMS`, and prints
  the `gh release create` line that publishes it.
  Refuses if the engine's DLLs differ from the build tree. `--buildings` also stages each finished
  faction (dwarves, elves, men, goblins) and packs it as `bfme-mac-buildings-<faction>-<version>.tar.gz`,
  listed in the fixes file's `BUILDINGS` and in `SHA256SUMS-<version>`.
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
- `scripts/window-watch.sh <pid> [log]` — started by the play scripts: logs the game window's real
  macOS frame and layer, and the screen's menu-bar and notch heights, as `mac` lines in
  `ahk/edgescroll.log` beside the Wine rect, at start and on every change. Read-only.
- `scripts/retina.sh on|off` — toggle Wine's Retina mode and both games' `Resolution` together.
- `ahk/edgescroll.ahk` — what the play scripts launch: borderless setup (title bar off, window to
  0,0 full size) and then resident, emulating screen-edge camera scrolling and offering the
  Cmd-Tab mouse rescue ([PLAYING.md](PLAYING.md), "Keys"); puts the window back at 0,0 when macOS
  moves it ("Picture shifted down"). One AutoHotkey process does both jobs because
  a second Wine process in the game's first seconds crashes it.
  `ahk/borderless.ahk` is the same borderless setup as a one-shot, kept for diagnostics;
  `ahk/autoskirmish.ahk` is the menu driver.
- `scripts/install-mod.sh <bfme2|rotwk> <dir|zip>` — install a mod (or any set of
  `.big` files) into a game folder: backs up everything it overwrites as `<file>.premod.bak`,
  logs to `<gamedir>/mods-installed.log`, undone with `--revert`. See `docs/MODDING.md` for the
  art pipeline (Blender → W3D → `asset.dat`).
- `tools/make_group_pack.py <rotwk|bfme2>` — builds the **group pack**, `!!!!!!!!!!group-pack.big`, from
  your own install: INI copies with our tweaks (4000 particles, heat effects off, camera max
  height 700, path searches give up after 5000 cells instead of 15000) that override the game's own because the name sorts first. Install with
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
- `scripts/cursor-test.sh` + `tools/cursortest.c` — every RotWK cursor (`data/cursors`, 81 .ani/.cur)
  through the engine's Mac driver, set the way the game sets them (WM_SETCURSOR always handled);
  fails on any cursor winemac turns into the macOS arrow. Throwaway prefix `build/prefix-cursor`,
  no game; moves the pointer once and puts it back. 2026-10-04, w10: 81 of 81 convert.
- `tools/cursorprobe.swift` (built by `scripts/cursor-test.sh`) — read-only probe, every 50 ms: the
  pointer macOS shows, whether WindowServer draws it in software, the frontmost app and the window
  under the pointer (winemac's own hit test). `CURSORPROBE=<secs> scripts/play-rotwk.sh` logs it to
  `logs/cursorprobe-*.log`; add `WINEDEBUG=+cursor` to see every cursor the game sets.
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
  `gamepatch.ini` or with `GAMEPATCH_<NAME>=0`. Exceptions: `moveawaycap`, `moveawayqueue` and `pathsplit` change
  the game logic (the same way on every machine), so every LAN player needs them set alike
  (`docs/PERFORMANCE.md` §20, §21). `play-rotwk.sh` loads it (`dinput8=n,b`) while
  `gamepatch.ini` is in the game folder; log in `logs/gamepatch.log`. `--test` runs the standalone
  bit-exactness tests (`gamepatch/tests/`) in a throwaway prefix; `--bundle` makes the two files
  another player copies into their RotWK folder. Record: `docs/PERFORMANCE.md` §10.
- `scripts/perf-install.sh [--revert|--status]` — every performance fix in one step: the Wine fixes
  (`wine-fixes.sh`) and the game patch (`game-patch.sh`); `--revert` removes both, `--status` says
  what is installed (and which wined3d build). Switches that need no reinstall are in its header.
- `scripts/wine-fixes.sh [--revert]` — builds our fixes to Wine 10.0 from source and installs them into
  `engines/$WINE_BUILD` (each DLL's engine copy kept as `<dll>.orig-<build>`): `patches/d3dx9-setrawvalue/`
  (the loading-time fix: SetRawValue for the units' bone palette, so Wine's fast d3dx9_27 can replace
  Microsoft's, ~190 s -> ~12 s) and `patches/wined3d-wow64-buffers/` (big battles: dynamic-buffer
  locks stop waiting for the render thread, a new `wined3d.so` writes the locked range straight into
  the GPU buffer, redundant state work removed, SSE2 instead of x87; synthetic battle frame 184 ->
  34 ms, `docs/PERFORMANCE.md`). `--revert` restores the engine's DLLs and removes `wined3d.so`.
  It applies only the `*.patch` files at the top of each series folder; `unbuilt/` holds patches
  that are written but not played (0022), so they stay out of the build and the release.
- `scripts/build-wine.sh <label>` — configure, build and install a from-source WoW64 Wine from the
  clone in `wine/src` into `engines/src-<label>` (x86_64 host under Rosetta, mingw-w64 PE side;
  `patches/WINE-BUILD.md` has the toolchain and the two traps).
  `patches/lock-whole-buffer/` — upstream d3d8/d3d9 patches + test for zero-size buffer locks.
- `patches/README.md` — index of the patch series, one line per patch, and the game-data edits;
  `patches/WINE-BUG-REPORT.md` — the WoW64 transition bug; `patches/nxcompat/install.sh` — the
  NX_COMPAT experiment (no effect; reverted).
- `parallel/` — the multi-core framework for the game patch (used by the game patch's `shadowpar`,
  off by default): a fork/join worker
  pool (`pool/parallel.c`: spin-then-park, FPU state copied into jobs, faults retried serially), a
  deferred-call recorder (`pool/recorder.c`) and `parallel/DESIGN.md`. `parallel/pool/build-and-run.sh
  bench|rectest|place` builds and runs its tests under Wine in an isolated prefix, never beside a game.

## Measuring

- `scripts/monitor.sh last|report [dir]|list|bench [args]|stalltest|start <pid> <log> <dir>` — the session
  monitor, on in every `play-rotwk.sh` game (`BFME_MONITOR=0` turns it off): per-frame times from
  wined3d (`+timestamp,+frametime`), thread CPU / memory / GPU sampled from outside by
  `tools/monitor_rec.py` (libproc, every 0.25 s), the game patch's frame records (`monitor`: D3DX
  loads per frame, objects, 32-bit address space); when the game exits `tools/monitor_report.py` (+
  `tools/monitor_chart.py`) writes `logs/sessions/<date-time>/report.html` and `summary.txt`. `last`
  prints and opens the newest; `bench` proves the pipeline on `tools/d3d9bench.c` (`--hitch N:MS[:sleep]`
  injects known slow frames); `stalltest` proves the stall sampler: the report must name the bench's
  `bench_hitch()` as the function of its 400 ms frames. PERFORMANCE.md §16.
- `tools/monitor_stalls.py <game.txt> [--top 5]` — the report's stall section: for every frame over
  150 ms the game patch's stall sampler (`gamepatch/src/p_stall.c`) caught, histograms of the main
  thread's functions (innermost exe function, call chain, leaf, logic phase), named from
  `build/rotwk-re/` (or a bench's COFF symbols); chains with `tools/callstacks.py`'s `Chainer`.
- `tools/monitor_rec.py --pid P --dir D --log L [--any] [--no-report]` — the monitor's sampler (above).
- `tools/monitor_report.py <session dir> [--spike-ms 50]` — rebuilds a session's report and summary.
- `tools/obfme_map.py <rotwk addr>... | --name <regex> | build` — names RotWK code from Open-BFME-2
  (byte-exact C++ of BFME2 1.06, GPLv3, read only from its git-ignored clone in `build/ext/`, never
  copied here): their function, source file and line, and match confidence for an address; for an
  unmapped one, its 1.06 address, the mapped functions it calls and its mapped neighbours. `build`
  writes `build/ext/rotwk_map.tsv` (needs `git clone --depth 1 https://github.com/Open-BFME/Open-BFME-2
  build/ext/Open-BFME-2`).
- `scripts/measure-session.sh on|sample [label]|summary [since]|off` — one measuring session played by
  you: `on` turns the game patch's diagnostics on (passtimers, renderstats, particlestats, logicstats; ~2 ms/frame),
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
- `scripts/wine-0022.sh --stage|--install|--revert|--status` — wined3d patch 0022 (managed textures'
  system memory out of the 32-bit address space) on top of the installed series: builds it in
  wine/src-0022 + wine/build-0022, stages the DLL pair in build/wine-0022/ and an engine clone in
  build/engine-0022; `--install` copies the pair into engines/w10 (old pair kept as `*.pre0022-w10.bak`).
  `docs/MEMORY-4GB.md`.
- `scripts/texstash.sh [--gb G] [args]` + `tools/texstash.c` — 4.5 GB of managed textures in our formats
  in a large-address-aware 32-bit process, on engines/w10 and build/engine-0022: address space after each
  256 MB, first failure, upload and frame times, eviction, relock, GetDC and Reset, and a CRC of every
  texture drawn, compared between the two; `--reserve 1300` takes the game's own share of the address
  space first. Throwaway prefix build/prefix-texstash. `docs/MEMORY-4GB.md`.
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
- `tools/texupload.c` — what the first use of one texture costs the game thread under the Wine in use:
  per spec (`dxt5:512:512:0`, `tga32:2048:1024:1`, or `dx:<file>:mips`, a real file through the game's
  own `D3DXCreateTextureFromFileInMemoryEx` call with `WINEDLLOVERRIDES=d3dx9_27=b`) the median ms to
  load, create and fill, draw, and wait for the upload, against the same frame without it. i686
  mingw, run in a throwaway prefix. `docs/PERFORMANCE.md` §13.
- `tools/dxtslim.c` + `python3 -m sagekit.texslim [archive.big...|--selfcheck]` (`sagekit/texslim.py`) —
  texture and model memory of each archive (default: our installed ones) and its cap; `sagekit install`
  ships every opaque DXT5 sheet as the DXT1 that draws the same texels (half the memory), kept only
  when every level draws byte-identically through the game's d3dx9 call; `sagekit validate` checks the
  per-archive cap. i686 mingw, run in build/prefix-texbake. `docs/MEMORY-2GB.md`.
- `python3 -m sagekit.texreach [archive.big...]` (`sagekit/texreach.py`) — the lowest mip level each
  model texture can reach at the closest RTS camera (3024 px wide, 50° view, eye 120 up); `sagekit
  validate` fails a staged texture whose top level is never sampled. `docs/MEMORY-2GB.md`.
- `tools/texbake.c` + `python3 -m sagekit.texbake [archive.big...|--selfcheck]` (`sagekit/texbake.py`) —
  our TGA model textures (normal maps, house-colour masks) rewritten as the DDS the game's d3dx9 builds
  from them, checked identical level by level, so the game skips its mip generation (40-170 ms per
  texture); `sagekit install` and `sagekit unit --stage` apply it, `sagekit validate` checks the
  staged archives. The module alone lists what still ships as such a TGA. `docs/PERFORMANCE.md` §13.
- `python3 -m sagekit.drawcost_report [archive part...] [--rows] [--scene] [--json out.json]`
  (`sagekit/drawcost.py`, `drawcost_report.py`, `drawcost_scene.py`) — every staged object against EA's:
  render objects, main-view and shadow-pass draws, materials, triangles, house-colour meshes, particle
  systems and live particles per state, and the main-thread µs they cost; `--scene` the 8-player late
  game. `sagekit validate` caps each object at EA's draws x 1.10 + 2 and EA's render objects + 2.
  `docs/PERFORMANCE.md` §14.
- `python3 -m sagekit.fire_budget [faction/building ...]` (`sagekit/fire_budget.py`, `fire_lean.py`) — each
  burning recipe's fire in live particles against its budget: 20 for the buildings whose fire is their
  identity (`IDENTITY`), 6 for the rest (BurstCount / BurstDelay x Lifetime per system, over its points);
  `sagekit validate` and the check suite fail one over it. docs/ART.md "Fire budget".
- `python3 -m sagekit.fire_review --snapshot <out.json> | [--before <json>] <faction/building> ...`
  (`sagekit/fire_review.py`, `sagekit/paint/fire_composite.py` on Blender's Python) — the fire before and
  after drawn over the build's renders, healthy and damaged, in-game camera and close-up, live counts on
  each tile: `build/assets/_review_finish/fire_budget/`.
- `python3 -m sagekit.fire_grid [--before <snapshot.json>] [faction ...]` (`sagekit/fire_grid.py`) — per
  faction, every building with our fire before and after at the in-game camera (1:1 crop, healthy), live
  counts on each tile: `build/assets/_review_finish/fire_reduce/<faction>.jpg` (the fire reduction).
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
  the large-address flag). **It may crash the game: use it for measurement sessions only.** A
  session with it attached ended in a fault at `lotrbfme2ep1.exe+0x76D9E2` at exit, the address
  seen once before while eipsample suspended the game's threads. Start it in a Terminal while the
  game runs (menu or match); every 10 s `tools/memwatch.c` (built on first
  use) walks the game's address space read-only from a second Wine process and `tools/memwatch.py`
  adds the macOS side (resident, footprint) into `logs/memwatch-<date>.csv`: committed, reserved,
  largest free block (the out-of-memory predictor), free blocks over 16 MB, committed by type. Stops
  with the game or Ctrl-C and prints the summary; `scripts/memwatch.sh summary [csv] [--png]` again
  later. Each query runs on the game's main thread (~50 µs), so it paces itself under 2 % of it.

## Art

- `python3 -m sagekit install <faction> [--check|--revert [--dry-run]]` — installs a faction's built art into the
  game (`--check` stages without installing, `--revert` restores the last backup; an asset.dat a
  later install changed gets only the pack's own records put back, from `_install/installed-ops.json`,
  every other record untouched);
  `python3 -m sagekit.install` runs its self-checks on temporary files.
- `python3 -m sagekit.pack build|install|revert|status` (`sagekit/pack.py`, `sagekit/packbuild.py`) —
  the building packs players install without Blender, holding none of EA's files: `build` turns a
  staged faction and its builder into a pack (`members.bin`: each archive member as a delta against
  the EA files it was made from, checked to insert no run of over 256 bytes from them; `pack.json`:
  the EA files by SHA-256, the asset.dat operations and the records they need); `install <pack
  dir>... [--prefix]` checks them against that game, skips a faction that differs, rebuilds the
  archives from the player's EA files, and edits asset.dat in one transaction with a scoped receipt;
  `revert` restores it. The installer is standard library only.
- `python3 -m sagekit.delta` (`sagekit/delta.py`) — the packs' copy/insert delta format and the check
  for EA runs in the inserted bytes; run alone, its self-checks.
- `python3 -m sagekit.texrecords` (`sagekit/texrecords.py`) — asset.dat records for the textures the HUD,
  ui2x and icon archives ship: a new texture name gets a copy of its family's record (without one the
  game draws it magenta), taken back on revert; every install verifies its textures are filed. Run
  alone, its self-check.
- `python3 -m sagekit unit <faction>/<unit> [--render|--check|--stage|--install|--revert]`
  (`sagekit/units/`, `sagekit/blender/unit_pose.py`) — unit recipes, `assets/<faction>/porter/design.py`
  (every faction's builder, installed) and `assets/<faction>/worker/design.py` (the construction
  workers, staged for review: docs/UNITS.md *Construction workers*): builds the redesigned builder on
  EA's rig, checks it, renders EA's and ours in EA's animation poses, stages, installs and reverts it
  in any order with other units (a shared house-colour INI; asset.dat records put back one by one);
  `install.release()` is what the faction's building pack ships. `unit list`, `unit selfcheck`.
  How a recipe works: `docs/UNITS.md`. The Dwarven porter's `unit.py` and `preview.py` are the
  troop scripts' imports of the shared mesh primitives and motion decoder.
- `python3 -m assets.cah.<class>.build`, `python3 -m sagekit.units.cah --stage|--install|--revert
  [--dry-run] [--classes a,b]` (`sagekit/units/cah.py`, `assets/cah/`) — the cah pack: more Create-a-Hero choices
  (serious and fun parts appended to the creation screen's rows). Each class folder builds its model
  copies, sheets and INI fragment with the kit (`assets/cah/kit/`: `geom.py`, `ornament.py`,
  `paint.py`, `models.py`, `ini.py`); the pack composes every class into one
  `!!!!!!!!!!!sagekit-cah.big`. `python3 -m assets.cah.kit.survey [--markdown]` maps EA's subclasses;
  `python3 -m assets.cah.kit.render <class>` renders the overview (`sagekit/blender/cah_pose.py`).
  `python3 -m assets.cah.kit.attach <class> [--review | --review-only]` builds a class's parts as models of our own on
  the hero's bones (`kit/attach.py`, checks in `kit/attach_lint.py`, review sheet `kit/attach_review.py`; docs/CAH.md);
  every class is built this way and `--stage` takes only classes built this way.
  The evil classes use `python3 -m assets.cah.evil.render <class>` and `python3 -m assets.cah.evil.contents <class>`.
  How: `docs/CAH.md`.
- `python3 -m assets.heroes.build [--skip-art]`, `python3 -m sagekit.units.heroes --stage|--install|--revert [--dry-run]`
  (`assets/heroes/`, `sagekit/units/heroes.py`) — the heroes pack: EA's hidden heroes unlocked (Gamling
  finished, Damrod, Earnur for the Men), the Captain of Erebor (Dain's object and rig, the Erebor kit:
  `assets/heroes/captain/design.py`), Aragorn's level-8 armour (`assets/heroes/aragorn/design.py`),
  portraits and icons (`assets/heroes/portraits.py`, graded by `assets/heroes/imaging.py` on Blender's
  Python); INI composed onto EA's 2.02 files and linted, strings in a `lang\` archive.
  `python3 -m assets.heroes.audit [--markdown]` checks EA's hidden heroes; `python3 -m assets.heroes.render`
  writes the review sheets. How: `docs/HEROES.md`.
- `python3 -m sagekit icons <faction> [--map|--render|--stage|--install|--revert]` (`sagekit/icons/`,
  `sagekit/blender/icon.py`, `sagekit/paint/icons.py`) — EA's building portraits and buttons repainted
  from our buildings, framed per `assets/<faction>/icons.py`, graded to EA's sepia and sky look,
  composed into copies of EA's pages and checked; one shared `!!!!!!!!!!!!!!sagekit-icons.big` for
  every faction. Review sheet: `build/assets/<faction>/_review/icons_v1.jpg`. How: `docs/ICONS.md`.
- `python3 -m sagekit hud [--sheet|--stage|--install|--revert] [--1x]` (`sagekit/hud/`,
  `sagekit/paint/hud.py`, `hudrings.py`, `hudsheet.py`, `assets/hud/`) — the in-game palantir's frames,
  glass and button sheets repainted (Good bronze and gold, Evil blackened iron) at 1x and Retina 2x,
  the APT geometry's texture matrices doubled to match; `!!!!!!!!!!!!!!sagekit-hud.big`. Review sheets:
  `build/assets/_review_finish/hud/`. How: `docs/HUD.md`.
- `python3 -m sagekit hud --factions [--sheet|--stage|--install|--revert] [--dry-run]`
  (`sagekit/hud/factions.py`, `factionapt.py`, `factioncheck.py`, `aptfile.py`, `factionsheet.py`,
  `swatch.py`, `pieces.py`, `sagekit/blender/hudpieces.py`, `sagekit/paint/palantir/`, `assets/hud/factions/`)
  — one palantir frame per faction (Arnor shares Men's), each cut from its citadel's sheets
  (`swatches.py`) with its ornaments rendered in 3D (`pieces.py`), over the 2x pack, chosen by an APT edit from the side the game passes to SetPlayerFaction;
  checks, a bytecode dry trace per side; the same archive; `--revert` puts the Good/Evil 2x pack back.
  Review sheets: `build/assets/_review_finish/hud_faction/`, `hud_citadel/all.jpg`. How: `docs/HUD.md`.
- `python3 -m sagekit ui2x [--stage|--install|--revert|--sheet] [--dry-run]` (`sagekit/ui2x/`,
  `sagekit/paint/ui2x.py`) — Retina 2x MappedImage pages: unit and hero portraits, unit command,
  ability, hero bar and spell book buttons (EA's paintings upscaled by Real-ESRGAN with EA's grain put
  back, round masks redrawn), the tooltip frame in our bronze and gold (APT, geometry doubled) in
  `!!!!!!!!!!!!!!sagekit-ui2x.big`; our building icons' pages at 2x in the icon archive. Review
  sheets: `build/assets/_review_finish/ui2x/`. How: `docs/UI2X.md`.
- `python3 -m sagekit.fx --stage|--review [f,g]|--install|--revert|--status [--dry-run]` (`sagekit/fx/`,
  `sagekit/paint/particles.py`, `assets/<faction>/fx.py`) — effects in each faction's colours: tinted
  copies of EA's particle systems (colour keys only), the spell books' shared powers and the buildings'
  fire and smoke pointed at them. The shared `!!!!!!!!!!!!sagekit-fx.big` ships only
  fxparticlesystem.ini (with the fire systems), fxlist.ini and system.ini; each faction pack carries
  its own structure INIs' fire moves. Install it before the faction packs. Review sheets: `build/assets/_review_finish/fx/<faction>.jpg`.
  How: docs/ART.md "Effects".
- `assets/<faction>/troops/` — troop redesigns (Dwarves, Elves, Men; staged, not installed):
  `build.py`, `preview.py`, `audit.py`; each folder's README has the commands.
- `python3 -m sagekit list|validate|inventory|budget|build` — builds new art for a building from
  your install: `inventory dwarves/fortress` lists every part and lifecycle state the game draws,
  `build dwarves/fortress` runs extract → Blender geometry/bake/paint → export → night lights
  (`sagekit/nightlights.py`) → fix-up → derive → lifecycle (construction, really damaged and rubble models rebuilt around the new body along EA's
  pieces and animations, `sagekit/lifecycle.py`) → fire (the recipe's `fire_points` on a bone rig for EA's
  particle systems, `sagekit/fire.py`) → asset cache → checks → before/after renders into
  `build/assets/` (`renders/lifecycle/<model>.png` for the lifecycle models). Rules and layout:
  `assets/README.md`.
  `names dwarves --write` regenerates `assets/dwarves/NAMES.md`, every model and texture name the
  faction ships (pick new names against it).
  `owners elves` lists the models and sheets the faction shares with other factions (scan cached in
  `build/assets/_ownership.json`; `sheets` skips shared sheets, `validate` fails a recipe that would
  change another faction's art). `new elves --write` writes one stub recipe per design unit of EA's
  (never over an existing one). `measure elves/fortress` measures EA's body into `work/measure.json`
  (footprint, planes, levels, setbacks, openings, heads, symmetry; `sagekit/measure.py` for design()).
- `python3 -m sagekit preview <faction>/<building> [--views rts,close]` (`sagekit/preview.py`,
  `sagekit/blender/preview.py`) — a shape preview in 10-20 s: the pipeline's geometry job into `preview/`,
  EA's model and ours in EEVEE with new faces in their atlas tag's palette colour, `preview/compare_<view>.png`,
  and the checks that need no bake (budget, footprint, height, winding, sky-facing backs, closed solids).
- `python3 -m sagekit capture <faction>/<building> [--version v1]` (`sagekit/capture.py`,
  `sagekit/blender/capture.py`) — the capture dress review of a capturable neutral building (the Inn):
  EA's model and ours neutral, then ours as each faction holds it, its dress shown and its cloth in a
  sample player colour: `build/assets/<faction>/_review/<building>_<version>.jpg`. One Blender.
  `new neutral --write --only inn` writes one stub of a faction's survey.
- `python3 -m sagekit scenery audit|sheets|review|map [--culture a,b]` (`sagekit/scenery.py`,
  `sagekit/scenery_review.py`, `sagekit/blender/scenery_map.py`, `sagekit/formats/maps.py`,
  `assets/scenery/`) — the map scenery (EA's civilian buildings, ruins and set pieces): `audit` reads
  every map and ranks the cultures by maps placing them (`build/assets/scenery/_audit/audit.md`),
  `sheets` recolours each culture's sheets in its faction's palette or the Wilderland grade at EA's
  size and format (never a sheet a faction draws or one of our archives ships), `review` renders EA's
  objects against ours per culture, `map "<map name>"` a stretch of a real map
  (`build/assets/_review_finish/scenery/`). Ships as `!!!!!!!!!!!sagekit-scenery.big`:
  `python3 -m sagekit install scenery --check | install scenery | revert scenery`.
  `python3 -m assets.scenery.paint` is its per-sheet painter on Blender's Python.
- `python3 -m sagekit board <faction>` (`sagekit/board.py`, `sagekit/blender/board.py`) — the style
  board: EA's buildings of the faction as the game draws them, one labelled grid by role, level-up
  meshes in a last row: `build/assets/<faction>/_board/<faction>_board.jpg`. Works before any recipe
  exists (the scaffolder's survey); at most two Blender processes.
- `python3 -m sagekit palettes <faction> [--only A,B]` (`sagekit/palettes.py`,
  `sagekit/paint/palette.py`) — the palette options: EA's citadel (the style's `palette_building`)
  as it is and recoloured with each of the style's `palettes` through its flat-sheet layers, in the
  style's `palette_views`, with swatches: `build/assets/<faction>/_palettes/palette_options.jpg`.
- `python3 -m sagekit offload pack|run|results|unpack` (`sagekit/offload.py`, `sagekit/snapshot.py`) and
  `tools/colab/offload.ipynb` — a faction's full-quality Blender builds on a Colab A100 from a zip with
  the code, the extracted sources and a game snapshot, finished on the Mac (ship, shared, ini, cache,
  checks on the real game): `docs/OFFLOAD.md`.
- `tools/lifecycle_audit.py <faction>[/<building>] ... [--only-problems]` — after a build, whether
  each construction, damaged, really damaged, rubble and collapse model the game draws carries our
  body or stays EA's, and why (a sheet we have no variant of, the per-frame checks, no fit, an
  error), plus stale lifecycle renders, built models missing from `out/`, check failures, and fire
  rigs burning in a construction, rubble or placement state or over a body not our intact one.
  Reads `build/assets/` only (no Blender, no game).
- `tools/w3d_fixup.py <original.w3d> <exported.w3d>` — repairs what the OpenSAGE Blender add-on drops or
  changes on re-export (materials and texture references, mesh version 5.0, surface types, pivot
  fixups, and it generates the AABTREE collision trees BFME2 requires). Details in `docs/MODDING.md` §g.
- `tools/asset_dat.py show|check|patch|texture <asset.dat> ...` — `asset.dat`: BFME2 caches every
  model's chunk offsets and sizes and reads them blind, so an edited model must have its record
  patched to match (`check` says whether it does; the first write keeps `asset.dat.orig`); `texture`
  registers a new texture (without a record it renders magenta). Both tools are command lines over
  `sagekit/formats/`.

## Development

- `scripts/setup-prefix.sh <build>` — the development setup: build `prefixes/<build>` for
  `engines/<build>`, symlinking the game folders from `prefixes/stable` (idempotent; refuses to
  touch `stable`). New installs use `scripts/install.sh`.
- `scripts/lib.sh` — the helpers the scripts share: `game_running` (the one "is a game running"
  check) and `usage` (prints the script's header comment). `env.sh` sources it; scripts that need
  no Wine source it directly.
- `harness/README.md` — what the repo harness enforces and why.

## Experiments and dead ends

Kept for the record. The hands-free runs take over the screen and are not used any more: the
game is played by hand and measured from its logs (AGENTS.md). The DXVK and NX_COMPAT experiments
are under `scripts/play-bfme2-dxvk.sh` and `patches/README.md` above. History:
[the Wine 11 bisect](history/BISECT-2026-09-23.md), [the first state snapshot](history/STATE-2026-09-23.md),
[the load-time research](history/LOAD-TIME-RESEARCH-2026-09-22.md),
[the LAA investigation](history/LAA-W10-2026-09-27.md) and
[the September art and troop review log](history/ART-LOG-2026-09.md).

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
  231 s → 168 s on RotWK with Microsoft's d3dx9; the big win is `scripts/wine-fixes.sh`.
