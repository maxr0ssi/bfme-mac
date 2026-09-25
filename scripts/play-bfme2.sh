#!/bin/zsh
# Launch BFME2 under Wine. Logs go to logs/.
#   ./play-bfme2.sh            normal run
#   DEBUG=1 ./play-bfme2.sh    verbose d3d logging for diagnosing rendering problems
set -e
# BFME2 plays on the Wine 10.0 engine too: Wine 11.0 faults in WoW64 whenever a second Wine process
# starts in the game's first ~8 s (see patches/WINE-BUG-REPORT.md), which the AutoHotkey helper does.
export WINE_BUILD="${WINE_BUILD:-w10}"
export BFME_ROOT="${0:A:h:h}"
. "$BFME_ROOT/env.sh"
GAMEDIR="$WINEPREFIX/drive_c/Program Files (x86)/Electronic Arts/BFME2"
LOGDIR="$BFME_ROOT/logs"; mkdir -p "$LOGDIR"
LOG="$LOGDIR/bfme2-$(date +%Y%m%d-%H%M%S).log"

# The engine's startup CPU benchmark never converges on a many-core machine under
# Rosetta and picks an LOD preset that crashes it; pin it to one core (DrewHoo's fix #2).
export WINE_CPU_TOPOLOGY=1:0
# msync: Wine's in-process (Mach) sync objects instead of a wineserver round trip per wait/release.
# The game takes a kernel mutex around its rendering thousands of times a second; in a big battle that
# cost ~19 ms of every frame, ~2.5 ms with msync (docs/PERFORMANCE.md). WINEMSYNC=0 turns it off.
export WINEMSYNC="${WINEMSYNC:-1}"
# Force Wine's own d3d9 (wined3d/OpenGL); play-bfme2-dxvk.sh flips this to the DXVK dll in syswow64.
export WINEDLLOVERRIDES="mscoree,mshtml=;d3d9=b"

if [[ -n "$DEBUG" ]]; then
  export WINEDEBUG="warn+d3d,fixme+d3d,fixme+d3d_shader,err+all"
fi

cd "$GAMEDIR"
echo "log: $LOG"
# Always windowed (-win): exclusive fullscreen minimizes on focus loss and comes back black
# under Wine's Mac driver.
# Borderless: once the game window exists, AutoHotkey strips its title bar and pins it to (0,0)
# at screen size, so it behaves like fullscreen without exclusive mode. edgescroll.ahk does that
# and then stays resident to emulate screen-edge camera scrolling (the engine disables it in
# windowed mode); one Wine process for both jobs, because a second one this early crashes the
# game (see ahk/edgescroll.ahk and the note in scripts/test-skirmish.sh).
( cd "$BFME_ROOT/ahk" && sleep 8 && wine AutoHotkeyU32.exe edgescroll.ahk "${EDGESCROLL:-on}" 4 "${EDGESCROLL_SEND:-input}" >/dev/null 2>&1 ) &
exec wine lotrbfme2.exe -win "$@" >"$LOG" 2>&1
