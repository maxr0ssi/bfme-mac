#!/bin/zsh
# Build the R5 parallel-framework prototypes with mingw and run one under Wine in an ISOLATED
# research prefix, bounded by a deadline (a hung test is killed, then that prefix's wineserver).
#   build-and-run.sh [bench|rectest|place] [args...]      e.g. build-and-run.sh bench forkjoin
# Research only: refuses to run while a game session is live; never touches the game or its prefix.
set -e
BFME_ROOT="${BFME_ROOT:-$HOME/Documents/BFME-MAC}"
HERE="${0:A:h}"
OUT="$BFME_ROOT/build/parallel-r5"            # build/ is gitignored
DEADLINE="${DEADLINE:-150}"

if pgrep -f '(lotrbfme2(ep1)?\.exe|game\.dat) -win' >/dev/null; then
  echo "a game session is running - aborting (standalone Wine tests must run alone)"; exit 1
fi

MINGW=/opt/homebrew/bin/i686-w64-mingw32-gcc
CF=(-O2 -msse2 -mfpmath=sse -ffp-contract=off -Wall -Wextra -I"$HERE" -static-libgcc)
mkdir -p "$OUT"
$MINGW $CF -o "$OUT/bench.exe"   "$HERE/bench.c"   "$HERE/parallel.c"
$MINGW $CF -o "$OUT/rectest.exe" "$HERE/rectest.c" "$HERE/recorder.c" "$HERE/parallel.c"
$MINGW -O2 -o "$OUT/place.exe"   "$HERE/place.c"

WINE_BUILD=w10 . "$BFME_ROOT/env.sh"
export WINEPREFIX="$BFME_ROOT/build/prefix-research" WINEMSYNC=1 WINEDEBUG=-all
[ -d "$WINEPREFIX" ] || wine wineboot -i >/dev/null 2>&1

exe="${1:-bench}"; shift || true
wine "$OUT/$exe.exe" "$@" > "$OUT/$exe.out" 2>/dev/null &
pid=$!
for i in $(seq 1 $((DEADLINE * 2))); do sleep 0.5; kill -0 $pid 2>/dev/null || break; done
if kill -0 $pid 2>/dev/null; then
  echo "TIMEOUT after ${DEADLINE}s - killing $exe.exe"
  pkill -f "parallel-r5/$exe.exe" || true
  sleep 1; wineserver -k               # our isolated research prefix only, after killing the test
fi
wait $pid 2>/dev/null || true
cat "$OUT/$exe.out"
