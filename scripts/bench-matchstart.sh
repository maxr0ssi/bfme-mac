#!/bin/zsh
# scripts/bench-matchstart.sh <label> [seconds] — repeatable hands-free frame-rate benchmark.
# Starts a RotWK skirmish with scripts/test-skirmish.sh (same map and camera every time), lets the
# match-start view settle, records frame times and per-thread CPU with tools/perfprobe.py
# (--no-eip: nothing suspends game threads), then closes the game. Any env var passes through to the
# game (e.g. WINED3D_WOW64_BUFFERS=off). Results: logs/perf-<label>-*.txt; see docs/PERFORMANCE.md.
set -u
export BFME_ROOT="${0:A:h:h}"
export WINE_BUILD="${WINE_BUILD:-w10}"
. "$BFME_ROOT/env.sh"
[[ "${1:-}" == (|-h|--help) ]] && usage $(( $# == 0 ))
LABEL=$1; SECS="${2:-20}"
game_running && { echo "a game is running; close it first"; exit 1; }
WINEDEBUG=-all,+fps,+frametime POLL=5 GAME=rotwk "$BFME_ROOT/scripts/test-skirmish.sh" "bench-$LABEL" \
  | grep -E "RESULT" | tail -1
if pgrep -f 'lotrbfme2ep1.exe -win' >/dev/null; then
  sleep 10
  python3 "$BFME_ROOT/tools/perfprobe.py" "$LABEL" "$SECS" --no-eip
fi
pkill -f 'lotrbfme2ep1' ; sleep 2; wineserver -k 2>/dev/null
exit 0
