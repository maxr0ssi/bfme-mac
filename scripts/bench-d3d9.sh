#!/bin/zsh
# bench-d3d9.sh <variant> [d3d9bench args] - runs tools/d3d9bench.c (a synthetic D3D9 load in the
# shape of WW3D2, the games' renderer) against one wined3d.dll, RUNS times (default 3), and prints
# every run plus the median. Opens a 640x480 window for a few seconds per run; no game needed.
#   variant  stock        the engine's own wined3d (wined3d.dll.orig-w10, kept by wine-fixes.sh)
#            engine       whatever wined3d.dll engines/$WINE_BUILD has installed now (builtin load)
#            sse2|x87|..  build/wined3d-variants/wined3d-<variant>.dll
#            /path/to/wined3d.dll
# Anything but `engine` is copied to build/d3d9bench-run/<variant>/wined3d.dll next to a copy of the
# exe, with its "Wine builtin DLL" marker overwritten, and loaded with WINEDLLOVERRIDES=wined3d=n:
# ntdll refuses a builtin-marked file as native and would load the engine's copy instead. The engine
# files are never touched. The bench checks in-process that the file it runs is the one asked for
# (PE header fingerprint) and exits 2 otherwise.
# Passed through to Wine: WINED3D_WOW64_BUFFERS=off|pin|stream, WINE_D3D_CONFIG=renderer=vulkan,
# WINEDEBUG. RUNS=n changes the count; --crc runs once and prints the image checksum.
# Examples:  scripts/bench-d3d9.sh stock
#            WINED3D_WOW64_BUFFERS=off scripts/bench-d3d9.sh sse2 --objects 2000 --dyn-frac 0.5
#            scripts/bench-d3d9.sh x87 --crc --bmp x87.bmp
set -eu
BFME_ROOT="${0:A:h:h}"
export BFME_ROOT WINE_BUILD="${WINE_BUILD:-w10}"
. "$BFME_ROOT/env.sh"
[[ "${1:-}" == (|-h|--help) ]] && usage $(( $# == 0 ))
variant=$1; shift

if game_running; then
  echo "a game is running; close it first (the bench would compete with it for the GPU and CPU)"; exit 1
fi

src=$BFME_ROOT/tools/d3d9bench.c exe=$BFME_ROOT/build/d3d9bench.exe
if [[ ! -x $exe || $src -nt $exe ]]; then
  i686-w64-mingw32-gcc -O2 -o "$exe" "$src" -ld3d9 || { echo "build failed"; exit 1; }
fi

libdir=$BFME_ROOT/engines/$WINE_BUILD/wswine.bundle/lib/wine/i386-windows
[[ -d $libdir ]] || libdir=$BFME_ROOT/engines/$WINE_BUILD/lib/wine/i386-windows
case $variant in
  engine) dll=$libdir/wined3d.dll ;;
  stock)  dll=$libdir/wined3d.dll.orig-$WINE_BUILD ;;
  */*)    dll=${variant:A}; variant=${${variant:t}:r} ;;
  *)      dll=$BFME_ROOT/build/wined3d-variants/wined3d-$variant.dll ;;
esac
[[ -f $dll ]] || { echo "no such wined3d: $dll"; exit 1; }

run_exe=$exe overrides=$WINEDLLOVERRIDES
if [[ $variant != engine ]]; then
  stage=$BFME_ROOT/build/d3d9bench-run/$variant
  mkdir -p "$stage"
  cp "$exe" "$stage/d3d9bench.exe"
  cp "$dll" "$stage/wined3d.dll"
  printf 'Native copy DLL!' | dd of="$stage/wined3d.dll" bs=1 seek=64 conv=notrunc 2>/dev/null
  run_exe=$stage/d3d9bench.exe overrides="$WINEDLLOVERRIDES;wined3d=n"
fi

runs=${RUNS:-3}
[[ " $* " == *" --crc "* ]] && runs=1
mkdir -p "$BFME_ROOT/logs"
errlog=$BFME_ROOT/logs/bench-d3d9-stderr.log
echo "variant $variant: $dll"
echo "env: WINED3D_WOW64_BUFFERS=${WINED3D_WOW64_BUFFERS-(unset)} WINE_D3D_CONFIG=${WINE_D3D_CONFIG-(unset)}"
typeset -a mean p50 p95 p99 fps
for i in {1..$runs}; do
  out=$(WINEDLLOVERRIDES=$overrides wine "$run_exe" --expect-dll "Z:$dll" "$@" 2>>"$errlog") || {
    print -r -- "$out"; echo "run $i failed (Wine's stderr: $errlog)"; exit 1; }
  (( i == 1 )) && print -r -- "$out" | grep -E '^(d3d9bench|wined3d|expect|adapter|draws)'
  print -r -- "$out" | grep -E '^(RESULT|PHASES|CRC|FAIL|PROGRAMS)' | sed "s/^/run $i: /"
  r=$(print -r -- "$out" | grep '^RESULT') || continue
  mean+=${${r##*mean=}%% *} p50+=${${r##*p50=}%% *} p95+=${${r##*p95=}%% *}
  p99+=${${r##*p99=}%% *} fps+=${${r##*fps=}%% *}
done
(( ${#mean} )) || exit 0
med() { local -a s; s=(${(on)@}); print -r -- ${s[$(( (${#s} + 1) / 2 ))]}; }
line="MEDIAN of $runs: fps=$(med $fps) mean=$(med $mean) p50=$(med $p50) p95=$(med $p95) p99=$(med $p99) ms"
echo "$line"
echo "$(date '+%F %T') $variant WINED3D_WOW64_BUFFERS=${WINED3D_WOW64_BUFFERS-} WINE_D3D_CONFIG=${WINE_D3D_CONFIG-} args=[$*] $line" \
  >> "$BFME_ROOT/logs/bench-d3d9.log"
