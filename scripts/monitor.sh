#!/bin/zsh
# scripts/monitor.sh last | report [dir] | list | bench [d3d9bench args] | start <pid> <log> <dir> — the session monitor.
# scripts/play-rotwk.sh turns it on for every game (BFME_MONITOR=0 turns it off): each game gets
# logs/sessions/<date-time>/ with report.html (frame-time graph lined up with thread CPU, memory,
# texture loads, GPU, objects; every slow frame with its context) and summary.txt. docs/PERFORMANCE.md §16.
#   last       the newest session's summary; opens its report.html
#   report [dir]  rebuild the report of the newest (or the given) session, e.g. after a tool update
#   list       the sessions, one line each
#   bench [args]  the whole pipeline without the game, on the synthetic D3D9 bench (tools/d3d9bench.c)
#              under the engine, with the play script's Wine settings: logs/sessions/bench-<date-time>/
#              (default args: --secs 20 --objects 2000 --cpu-ms 15; MONITOR=0 runs it unrecorded)
#   start <pid> <log> <dir>  what play-rotwk.sh runs in the background: tools/monitor_rec.py samples
#              the process from outside until it exits, then tools/monitor_report.py writes the report
set -eu
BFME_ROOT="${0:A:h:h}"
. "$BFME_ROOT/scripts/lib.sh"
cd "$BFME_ROOT"
S=logs/sessions
newest() { ls -td $S/*(/N) 2>/dev/null | head -1; }

case "${1:-}" in
start)
  (( $# >= 4 )) || usage 2
  exec python3 tools/monitor_rec.py --pid "$2" --log "$3" --dir "$4" --interval "${MONITOR_INTERVAL:-0.25}" ;;
report)
  d=${2:-$(newest)}; [[ -n "$d" && -f "$d/meta.json" ]] || { echo "no session (logs/sessions/*/meta.json)"; exit 1; }
  python3 tools/monitor_report.py "$d" ;;
last)
  d=$(newest); [[ -n "$d" && -f "$d/summary.txt" ]] || { echo "no finished session in $S"; exit 1; }
  cat "$d/summary.txt"; echo "report: $d/report.html"; open "$d/report.html" 2>/dev/null || true ;;
list)
  for d in $(ls -td $S/*(/N) 2>/dev/null); do
    printf '%s  %s\n' "${d:t}" "$(sed -n 's/^Frames ([^:]*: //p' "$d/summary.txt" 2>/dev/null | cut -c1-90)"
  done ;;
bench)
  shift
  game_running && { echo "a game is running; close it first"; exit 1; }
  export WINE_BUILD="${WINE_BUILD:-w10}" BFME_ROOT
  . ./env.sh
  exe=build/d3d9bench.exe
  if [[ ! -x $exe || tools/d3d9bench.c -nt $exe ]]; then
    i686-w64-mingw32-gcc -O2 -o "$exe" tools/d3d9bench.c -ld3d9 || { echo "build failed"; exit 1; }
  fi
  (( $# )) || set -- --secs 20 --objects 2000 --cpu-ms 15
  d=$S/bench-$(date +%Y%m%d-%H%M%S); mkdir -p "$d"
  export WINEMSYNC="${WINEMSYNC:-1}" WINEDLLOVERRIDES="mscoree,mshtml=;d3d9=b"
  if [[ "${MONITOR:-1}" == 0 ]]; then
    WINEDEBUG=-all wine "$exe" "$@" 2>/dev/null | grep -E '^(RESULT|PHASES)'; exit 0
  fi
  export WINEDEBUG="-all,+timestamp,+frametime"
  wine "$exe" "$@" > "$d/bench.out" 2> "$d/bench.log" &
  for i in {1..40}; do pid=$(pgrep -f "d3d9bench.exe $1" | head -1 || true); [[ -n "$pid" ]] && break; sleep 0.25; done
  [[ -n "${pid:-}" ]] || { echo "the bench did not start"; exit 1; }
  python3 tools/monitor_rec.py --pid "$pid" --log "$d/bench.log" --dir "$d" --any --interval "${MONITOR_INTERVAL:-0.25}"
  wait || true
  grep -E '^(RESULT|PHASES)' "$d/bench.out" || true ;;
-h|--help) usage ;;
*) usage 2 ;;
esac
