#!/bin/zsh
# scripts/cahrecolor.sh [--engine DIR] [cahrecolor args] — the Create-a-Hero colour rebuild without the game:
# tools/cahrecolor.c (a house-colour mask loaded, saved, drawn, then relocked, recoloured and mip-filtered
# the way game.dat 0x531c77 does it) on an engine (default engines/w10) with Wine patch 0022's stash on
# (WINED3D_STASH_MANAGED=1) and off (=0), in a throwaway prefix (build/prefix-texstash). Prints each run's
# ok/-- lines and FAIL lines; logs/cahrecolor-<stash>.txt keeps each run, with the count of 0022's
# "Stashed"/"Restored" traces (proof the stash ran). Opens a small window for a few seconds per run.
# docs/CAH.md, "Hero colours".
set -eu
BFME_ROOT="${0:A:h:h}"
. "$BFME_ROOT/scripts/lib.sh"
[[ "${1:-}" == (-h|--help) ]] && usage
eng=engines/w10
[[ "${1:-}" == --engine ]] && { eng=$2; shift 2; }
game_running && { echo "a game is running; close it first"; exit 1; }
cd "$BFME_ROOT"
renice -n 10 $$ >/dev/null   # not nice(1): macOS drops DYLD_* when it runs a /usr/bin program
exe=build/cahrecolor.exe
[[ -x $exe && $exe -nt tools/cahrecolor.c ]] || i686-w64-mingw32-gcc -O2 -o $exe tools/cahrecolor.c -ld3d9
export WINEPREFIX="$BFME_ROOT/build/prefix-texstash" WINEDLLOVERRIDES="mscoree,mshtml=;d3dx9_27=b" WINEMSYNC=1
export DYLD_FALLBACK_LIBRARY_PATH="$BFME_ROOT/engines:$BFME_ROOT/engines/template/Template-1.0.18.app/Contents/Frameworks"
export PATH="$BFME_ROOT/$eng/wswine.bundle/bin:$PATH"
mkdir -p logs
for stash in 1 0; do
  echo "== $eng, WINED3D_STASH_MANAGED=$stash"
  WINED3D_STASH_MANAGED=$stash WINEDEBUG=-all,trace+d3d wine $exe "$@" > logs/cahrecolor-$stash.txt 2> logs/cahrecolor-$stash.trace \
    || echo "exit $? (failures)"
  wineserver -w
  grep -E '^(ok|--|FAIL|pass|WINED3D|[0-9]+ failure)' logs/cahrecolor-$stash.txt || tail -5 logs/cahrecolor-$stash.trace
  echo "0022 traces: $(grep -c 'Stashed ' logs/cahrecolor-$stash.trace || true) stashed, $(grep -c 'Restored ' logs/cahrecolor-$stash.trace || true) restored"
  grep -m1 'Stashing uploaded' logs/cahrecolor-$stash.trace || true
  gzip -f logs/cahrecolor-$stash.trace
done
