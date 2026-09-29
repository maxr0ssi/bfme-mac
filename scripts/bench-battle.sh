#!/bin/zsh
# scripts/bench-battle.sh <label> [max_minutes] - hands-free big-battle profile of RotWK.
# Starts the skirmish set up in the player's Skirmish.ini (for this, an idle human + AI ally vs two
# AIs; backup Skirmish.ini.pre-aibattle), logs frame times every 15 s with tools/perfprobe.py
# (--no-eip), and once two windows in a row fall below 20 FPS (the AIs are fighting) saves a
# screenshot, runs build/rotwk-re/memprobe.exe (read-only: logic vs render time) and finally
# build/eipsample.exe in "main" mode (samples only the game thread). Then closes the game.
set -u
export BFME_ROOT="${0:A:h:h}" WINE_BUILD=w10
. "$BFME_ROOT/env.sh"
cd "$BFME_ROOT"
[[ "${1:-}" == (|-h|--help) ]] && usage $(( $# == 0 ))
L=$1; MAXMIN="${2:-25}"
OUT="logs/battle-$L"; mkdir -p "$OUT"
game_running && { echo "a game is running; close it first"; exit 1; }
# One game session at a time across agents: logs/.game-session holds the owner while a run is on.
[ -e logs/.game-session ] && { echo "logs/.game-session exists ($(cat logs/.game-session)); another run owns the game"; exit 1; }
echo "bench-battle $L $$" > logs/.game-session; trap 'rm -f logs/.game-session' EXIT
# Same battle every run: the skirmish setup the game accepted for the first run (idle human + AIs).
SK="$WINEPREFIX/drive_c/users/$USER/AppData/Roaming/My Rise of the Witch-king Files/Skirmish.ini"
[ -f build/Skirmish.ini.aibattle ] && cp build/Skirmish.ini.aibattle "$SK"
# Keep the game frontmost while the harness clicks through the menus: when another app (e.g. the
# Claude app) is in front, macOS delivers the clicks there and the menu navigation fails.
( end=$(( $(date +%s) + 600 ))
  while (( $(date +%s) < end )); do
    pid=$(pgrep -f 'lotrbfme2ep1[.]exe -win' | head -1)  # [.]: this pgrep's own command line must not match test-skirmish.sh's "is a game running" check
    if [[ -n $pid ]]; then
      front=$(osascript -e 'tell application "System Events" to get unix id of first application process whose frontmost is true' 2>/dev/null)
      [[ "$front" != "$pid" ]] && osascript -e "tell application \"System Events\" to set frontmost of (first application process whose unix id is $pid) to true" >/dev/null 2>&1
    fi
    sleep 3
  done ) &
FOCUS=$!
WINEDEBUG=-all,+fps,+frametime POLL=5 GAME=rotwk scripts/test-skirmish.sh "battle-$L" | grep RESULT | tail -1
kill $FOCUS 2>/dev/null
pgrep -f 'lotrbfme2ep1.exe -win' >/dev/null || { echo "game not running after the harness"; exit 1; }
echo "$(date +%T) match running; waiting for the battle (max $MAXMIN min)"
end=$(( $(date +%s) + MAXMIN * 60 )); low=0
while [ $(date +%s) -lt $end ] && pgrep -f 'lotrbfme2ep1.exe -win' >/dev/null; do
  line=$(python3 tools/perfprobe.py "$L-watch" 15 --no-eip 2>&1 | grep '^frames')
  echo "$(date +%T) $line" | tee -a "$OUT/watch.txt"
  fps=$(echo "$line" | sed -n 's/.*(\([0-9.]*\) FPS).*/\1/p')
  if [ -n "$fps" ] && [ "$(echo "$fps < 20" | bc)" = 1 ]; then low=$((low+1)); else low=0; fi
  [ $low -ge 2 ] && break
done
if [ $low -ge 2 ]; then
  echo "$(date +%T) battle detected: probing"
  screencapture -x "$OUT/battle.png" 2>/dev/null
  WINEDEBUG=-all wine build/rotwk-re/memprobe.exe "Z:${BFME_ROOT//\//\\}\\build\\rotwk-re\\probe-$L" 25 1 > "$OUT/memprobe.txt" 2>&1
  python3 tools/perfprobe.py "$L-battle" 20 --no-eip > "$OUT/perfprobe-battle.txt" 2>&1
  WINEDEBUG=-all wine build/eipsample.exe 20 5 lotrbfme2ep1.exe main > "$OUT/eipsample-main.txt" 2>&1  # harness-allow: profiler target name, not a launch
  echo "$(date +%T) probes done"
else
  echo "$(date +%T) no battle within $MAXMIN min"
fi
pkill -f lotrbfme2ep1; sleep 2; wineserver -k 2>/dev/null
echo "$(date +%T) done; outputs in $OUT"
