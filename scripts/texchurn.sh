#!/bin/zsh
# scripts/texchurn.sh [--engine DIR] [--stash 0|1] [--tag NAME] [texchurn args] — the terrain tile
# texture churn (tools/texchurn.c: create, fill, D3DXFilterTexture, draw, release, many times) in a
# throwaway prefix (build/prefix-texstash), with the process's macOS resident memory and physical
# footprint sampled from outside every 0.5 s (tools/monitor_rec.py's libproc reads). Prints one line
# per report of the test: cycle, textures made, 32-bit committed MB, resident MB, footprint MB, and
# the footprint's growth per 1000 textures over the second half of the run (with --grow: and the MB of
# textures kept). No game needed; a small
# window for the length of the run. logs/texchurn-<tag>.txt keeps the run.
#   --engine DIR  a Wine engine (default engines/$WINE_BUILD, w10); e.g. build/engine-0022s
#   --stash 0|1   WINED3D_STASH_MANAGED (default: unset, the engine's default)
#   --report TAG  only print the summary of an earlier run (logs/texchurn-TAG.*)
set -eu
BFME_ROOT="${0:A:h:h}"
. "$BFME_ROOT/scripts/lib.sh"
[[ "${1:-}" == (-h|--help) ]] && usage
game_running && { echo "a game is running; close it first (the test competes for the GPU and memory)"; exit 1; }
cd "$BFME_ROOT"
eng=engines/${WINE_BUILD:-w10} stash= tag= report=
while [[ $# -gt 0 ]]; do
  case $1 in
    --engine) eng=$2; shift 2 ;;
    --stash) stash=$2; shift 2 ;;
    --tag) tag=$2; shift 2 ;;
    --report) tag=$2 report=1; shift 2 ;;
    *) break ;;
  esac
done
[[ -n $tag ]] || tag=${eng:t}-stash${stash:-default}
out=logs/texchurn-$tag.txt mem=logs/texchurn-$tag.mem
if [[ -z $report ]]; then
exe=build/texchurn.exe
[[ -x $exe && $exe -nt tools/texchurn.c ]] || i686-w64-mingw32-gcc -O2 -msse2 -mfpmath=sse -Wl,--large-address-aware -o $exe tools/texchurn.c -ld3d9
export WINEPREFIX="$BFME_ROOT/build/prefix-texstash" WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml=" WINEMSYNC=1
export DYLD_FALLBACK_LIBRARY_PATH="$BFME_ROOT/engines:$BFME_ROOT/engines/template/Template-1.0.18.app/Contents/Frameworks"
[[ -n $stash ]] && export WINED3D_STASH_MANAGED=$stash
mkdir -p logs
# (not nice(1): a SIP binary drops DYLD_FALLBACK_LIBRARY_PATH; renice the process instead)
PATH="$BFME_ROOT/$eng/wswine.bundle/bin:$PATH" wine $exe "$@" > $out 2>/dev/null &
pid=
for i in {1..80}; do pid=$(pgrep -f 'texchurn\.exe' | head -1) && [[ -n $pid ]] && break; sleep 0.25; done
[[ -n $pid ]] || { echo "texchurn.exe did not start"; exit 1; }
renice -n 10 -p $pid >/dev/null || true
python3 -I - "$BFME_ROOT/tools" $pid > $mem <<'EOF'
import sys, time
sys.path.insert(0, sys.argv[1])
import monitor_rec as mr
pid = int(sys.argv[2])
while mr.alive(pid):
    rss, fp = mr.memory(pid)
    if rss:
        print("%.2f %.1f %.1f" % (time.time(), rss, fp), flush=True)
    time.sleep(0.5)
EOF
wait || true
PATH="$BFME_ROOT/$eng/wswine.bundle/bin:$PATH" wineserver -w
fi
python3 -I - $out $mem <<'EOF'
import sys
lines = open(sys.argv[1]).read().splitlines()
mem = [tuple(map(float, l.split())) for l in open(sys.argv[2]) if l.strip()]
print(lines[0] if lines else "no output")
cs = [l.split() for l in lines if l.startswith("C ")]
if not cs or not mem:
    print("\n".join(l for l in lines if l.startswith(("FAIL", "END")))); sys.exit(0)
# the test's clock starts at its first C line; line the samples up by elapsed time from the first
# sample whose footprint passes the device's (the first C line comes after CreateDevice)
t_first = mem[0][0]
start = next((m[0] for m in mem if m[2] > 40), t_first)
pts = []
for c in cs:
    t = start + float(c[3]) / 1000.0
    m = min(mem, key=lambda m: abs(m[0] - t))
    pts.append((int(c[1]), int(c[2]), float(c[4]), m[1], m[2], float(c[7]) if len(c) > 7 else 0.0))
step = max(1, len(pts) // 12)
print("cycle  textures  committed32  resident  footprint  kept (MB)")
for p in pts[::step] + ([pts[-1]] if (len(pts) - 1) % step else []):
    print("%5d %9d %11.0f %9.0f %10.0f %5.0f" % p)
h = pts[len(pts) // 2:]
if len(h) > 1 and h[-1][1] > h[0][1]:
    k = 1000.0 / (h[-1][1] - h[0][1])
    print("second half: footprint %+.1f MB, resident %+.1f MB, committed32 %+.1f MB per 1000 textures"
          % ((h[-1][4] - h[0][4]) * k, (h[-1][3] - h[0][3]) * k, (h[-1][2] - h[0][2]) * k))
print("peak footprint %.0f MB" % max(m[2] for m in mem))
print("\n".join(l for l in lines if l.startswith(("FAIL", "END"))))
EOF
