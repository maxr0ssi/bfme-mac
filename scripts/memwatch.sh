#!/bin/zsh
# scripts/memwatch.sh [interval_s] | summary [csv] [--png] — how close a match gets to the game's 2 GB (4 GB with LAA).
#   (no args)  start it once the game is running (any time: in the menu or mid-match). Every 2 s
#              (or interval_s) build/memwatch.exe walks the game's address space from a second Wine
#              process in the same prefix - read-only, no debugger, nothing suspended - and
#              tools/memwatch.py adds the macOS side of the same process (resident, footprint).
#              One row per sample in logs/memwatch-<date>.csv; stops by itself when the game exits,
#              or Ctrl-C. Then prints the summary.
#   summary    peak committed, smallest largest-free-block (the out-of-memory predictor) and when,
#              for the newest log or the one given; --png also writes <csv>.png next to it.
# Cost: each query is run by the game's main thread (~50 us); the probe paces itself and stretches
# the interval to keep that under 2 % of wall time (tools/memwatch.c). The per-sample cost is in the
# log (queries, query_ms). MEMWATCH_PREFIX / MEMWATCH_TARGET point it elsewhere (testing).
set -eu
BFME_ROOT="${0:A:h:h}"; cd "$BFME_ROOT"
EXE=build/memwatch.exe
GAME='(lotrbfme2(ep1)?\.exe|game\.dat) -win'

summary() { local -a png=(); [[ -n "${2:-}" ]] && png=(--png "${1%.csv}.png"); python3 tools/memwatch.py summary "$1" $png; }

if [[ "${1:-}" == summary ]]; then
  csv=${2:-}
  [[ -z "$csv" || "$csv" == --png ]] && csv=$(ls -t logs/memwatch-*.csv 2>/dev/null | head -1)
  [[ -n "$csv" ]] || { echo "no logs/memwatch-*.csv yet"; exit 1; }
  summary "$csv" "${${(M)@:#--png}:-}"; exit
fi
[[ "${1:-2}" == <-> ]] || { sed -n '2,13p' "$0"; exit 1; }
interval=${1:-2}

if [[ ! -x $EXE || tools/memwatch.c -nt $EXE ]]; then
  mkdir -p build
  nice -n 10 i686-w64-mingw32-gcc -O2 -Wl,--large-address-aware -o $EXE tools/memwatch.c -lpsapi
fi

if [[ -z "${MEMWATCH_TARGET:-}" ]]; then
  pid=$(pgrep -f "$GAME" | head -1 || true)
  [[ -n "$pid" ]] || { echo "the game is not running (start it with play-rotwk.sh / play-bfme2.sh)"; exit 1; }
  # A second Wine process in the game's first seconds can crash it (ahk/edgescroll.ahk): wait.
  secs() { local t=$(ps -o etime= -p $pid | tr -d ' ') d=0; [[ $t == *-* ]] && { d=${t%%-*}; t=${t#*-}; }
           local -a p=(${(s.:.)t}); local s=0; for x in $p; do s=$((s * 60 + 10#$x)); done; echo $((d * 86400 + s)); }
  while (( $(secs) < 60 )); do echo "waiting for the game to settle ($(secs) s up)"; sleep 10; done
fi

export WINE_BUILD=w10
. ./env.sh
[[ -n "${MEMWATCH_PREFIX:-}" ]] && export WINEPREFIX="$MEMWATCH_PREFIX"
export WINEMSYNC="${WINEMSYNC:-1}"              # the play scripts' setting: same wineserver mode
mkdir -p logs
out=logs/memwatch-$(date +%Y%m%d-%H%M%S).csv
echo "memwatch: every ${interval} s -> $out (Ctrl-C to stop)"
trap : INT
wine $EXE "$interval" "${MEMWATCH_TARGET:-}" 2>/dev/null | python3 tools/memwatch.py join > "$out" || true
trap - INT
echo
summary "$out" png
