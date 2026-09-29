#!/bin/zsh
# scripts/laa-probe.sh [laaprobe args] - builds tools/laaprobe.c as a LARGEADDRESSAWARE exe and runs
# it under engines/$WINE_BUILD (default w10) in a throwaway prefix (build/prefix-laa), bounded by a
# deadline. Opens a small window for the d3d9 tests. Never touches the game, its prefix or the engine.
#   scripts/laa-probe.sh                         every test, then every test with the low 2 GB filled
#   scripts/laa-probe.sh --fill-low --mb 1500 d3d9   one run with the given laaprobe arguments
# Prints the probe's output; the exit status is its failure count (124 on timeout).
set -eu
BFME_ROOT="${0:A:h:h}"
export BFME_ROOT WINE_BUILD="${WINE_BUILD:-w10}"
. "$BFME_ROOT/env.sh"
[[ "${1:-}" == (-h|--help) ]] && usage
game_running && { echo "a game is running; close it first"; exit 1; }
src=$BFME_ROOT/tools/laaprobe.c exe=$BFME_ROOT/build/laaprobe.exe
if [[ ! -x $exe || $src -nt $exe ]]; then
  i686-w64-mingw32-gcc -O2 -Wall -Wl,--large-address-aware -o "$exe" "$src" -ld3d9 -lgdi32 || { echo "build failed"; exit 1; }
fi
export WINEPREFIX="${LAA_PREFIX:-$BFME_ROOT/build/prefix-laa}" WINEDEBUG="${WINEDEBUG:--all}"
[[ -d $WINEPREFIX ]] || { wine wineboot -i >/dev/null 2>&1; wineserver -w; }

run() {   # one probe run with a deadline; a hung probe is killed with its (throwaway) wineserver
  echo "== WINE_BUILD=$WINE_BUILD laaprobe $*"
  wine "$exe" "$@" &
  local pid=$! i
  for i in {1..360}; do sleep 0.5; kill -0 $pid 2>/dev/null || break; done
  if kill -0 $pid 2>/dev/null; then echo "TIMEOUT"; wineserver -k; wait $pid 2>/dev/null; return 124; fi
  wait $pid
}
if [[ $# -gt 0 ]]; then run "$@"; exit $?; fi
rc=0
run all || rc=$?
run --fill-low all || rc=$(( rc + $? ))
exit $rc
