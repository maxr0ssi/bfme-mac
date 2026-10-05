#!/bin/zsh
# Launch Rise of the Witch-king (Patch 2.02; the HD Edition is optional) under Wine. Logs go to logs/.
#   scripts/play-rotwk.sh
set -e
# RotWK plays on the Wine 10.0 engine; Wine 11.x kills the main thread at match start (see patches/WINE-BUG-REPORT.md).
export WINE_BUILD="${WINE_BUILD:-w10}"
export BFME_ROOT="${0:A:h:h}"
. "$BFME_ROOT/env.sh"
GAMEDIR="$WINEPREFIX/drive_c/Program Files (x86)/Electronic Arts/RotWK"
LOGDIR="$BFME_ROOT/logs"; mkdir -p "$LOGDIR"
LOG="$LOGDIR/rotwk-$(date +%Y%m%d-%H%M%S).log"

export WINE_CPU_TOPOLOGY=1:0   # one core for Wine builds that read it; the w10 engine does not
# msync: Wine's in-process (Mach) sync objects instead of a wineserver round trip per wait/release.
# The game takes a kernel mutex around its rendering thousands of times a second; in a big battle that
# cost ~19 ms of every frame, ~2.5 ms with msync (docs/PERFORMANCE.md). WINEMSYNC=0 turns it off.
export WINEMSYNC="${WINEMSYNC:-1}"
export WINEDLLOVERRIDES="mscoree,mshtml=;d3d9=b"   # Wine's own d3d9 (wined3d, OpenGL)
# Game-side performance patch (gamepatch/, installed by scripts/install.sh or scripts/game-patch.sh):
# a proxy dinput8.dll in the game folder that patches the running game in memory at startup. Wine
# prefers its builtin dinput8, so the native one is asked for explicitly, only while the patch is
# installed. Log: logs/gamepatch.log.
if [[ -f "$GAMEDIR/gamepatch.ini" ]]; then
  export WINEDLLOVERRIDES="$WINEDLLOVERRIDES;dinput8=n,b"
  export GAMEPATCH_LOG="${GAMEPATCH_LOG:-Z:${LOGDIR//\//\\}\\gamepatch.log}"
fi

# Session monitor (scripts/monitor.sh, docs/PERFORMANCE.md §16), on unless BFME_MONITOR=0: wined3d
# writes each frame's time to the log (+frametime, one line a frame, +timestamp for the clock), a
# sampler reads thread CPU, memory and GPU from outside, the game patch (if installed) writes its
# frame records; when the game exits, logs/sessions/<date-time>/report.html. Overhead: docs §16.
if [[ "${BFME_MONITOR:-1}" != 0 ]]; then
  SESSION="$LOGDIR/sessions/$(date +%Y%m%d-%H%M%S)"; mkdir -p "$SESSION"
  if [[ "$WINEDEBUG" == -all ]]; then export WINEDEBUG="-all,+timestamp,+frametime"
  else export WINEDEBUG="$WINEDEBUG,+timestamp,+frametime"; fi
  [[ -f "$GAMEDIR/gamepatch.ini" ]] && export GAMEPATCH_MONITOR="Z:${SESSION//\//\\}\\game.txt"
  # With the monitor, the game patch's stall sampler (gamepatch.ini stalls) names the code of every frame
  # over 150 ms, and logicstats (~20 ns per update-module call; est. under 0.3 % of a core at 1,500 objects)
  # gives it the logic phase; GAMEPATCH_LOGICSTATS=0 turns that off.
  export GAMEPATCH_LOGICSTATS="${GAMEPATCH_LOGICSTATS:-1}"
  "$BFME_ROOT/scripts/monitor.sh" start $$ "$LOG" "$SESSION" >"$SESSION/recorder.out" 2>&1 &
  echo "monitor: $SESSION"
fi
cd "$GAMEDIR"
echo "log: $LOG"
# -win: exclusive fullscreen minimizes on focus loss and returns black under the Mac driver.
# Borderless: once the game window exists, AutoHotkey strips its title bar and pins it to (0,0)
# at screen size, so it behaves like fullscreen without exclusive mode. edgescroll.ahk does that
# and then stays resident to emulate screen-edge camera scrolling (the engine disables it in
# windowed mode); one Wine process for both jobs, because a second one this early crashes the
# game (see ahk/edgescroll.ahk and the note in scripts/test-skirmish.sh).
( cd "$BFME_ROOT/ahk" && sleep 8 && wine AutoHotkeyU32.exe edgescroll.ahk "${EDGESCROLL:-on}" 4 "${EDGESCROLL_SEND:-input}" >/dev/null 2>&1 ) &
# The game window's real macOS frame, logged beside edgescroll's Wine rect (docs/PLAYING.md,
# "Picture shifted down"). $$ becomes the game's pid at the exec below.
"$BFME_ROOT/scripts/window-watch.sh" $$ >/dev/null 2>&1 &
# CURSORPROBE=<seconds>: log which pointer macOS shows (tools/cursorprobe.swift, built by
# scripts/cursor-test.sh) to logs/cursorprobe-*.log; read-only, off unless set.
[[ -n "${CURSORPROBE:-}" && -x "$BFME_ROOT/build/cursorprobe" ]] &&
  "$BFME_ROOT/build/cursorprobe" "$CURSORPROBE" game >"$LOGDIR/cursorprobe-$(date +%Y%m%d-%H%M%S).log" 2>&1 &
exec wine lotrbfme2ep1.exe -win "$@" >"$LOG" 2>&1
