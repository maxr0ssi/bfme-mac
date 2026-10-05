#!/bin/zsh
# scripts/texstash.sh [--gb G] [texstash args] — wined3d patch 0022 offline: tools/texstash.c (4.5 GB of
# managed textures in our formats, in a large-address-aware 32-bit process) on the engine as installed
# (engines/w10) and on the staged 0022 engine (build/engine-0022, scripts/wine-0022.sh --stage), in a
# throwaway prefix (build/prefix-texstash). Prints both runs' address-space, upload and frame lines and
# compares every drawn texture's CRC between them (only textures both runs created). No game needed;
# opens a small window for about a minute per run. logs/texstash-<engine>.txt keeps each run.
set -eu
BFME_ROOT="${0:A:h:h}"
. "$BFME_ROOT/scripts/lib.sh"
[[ "${1:-}" == (-h|--help) ]] && usage
game_running && { echo "a game is running; close it first (the test competes for the GPU and memory)"; exit 1; }
cd "$BFME_ROOT"
exe=build/texstash.exe
[[ -x $exe && $exe -nt tools/texstash.c ]] || i686-w64-mingw32-gcc -O2 -msse2 -mfpmath=sse -Wl,--large-address-aware -o $exe tools/texstash.c -ld3d9 -lgdi32
[[ -d build/engine-0022 ]] || { echo "no build/engine-0022: run scripts/wine-0022.sh --stage first"; exit 1; }
export WINEPREFIX="$BFME_ROOT/build/prefix-texstash" WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml=" WINEMSYNC=1
export DYLD_FALLBACK_LIBRARY_PATH="$BFME_ROOT/engines:$BFME_ROOT/engines/template/Template-1.0.18.app/Contents/Frameworks"
mkdir -p logs
for name in w10 0022; do
  eng=engines/w10; [[ $name == 0022 ]] && eng=build/engine-0022
  echo "== $name ($eng)"
  PATH="$BFME_ROOT/$eng/wswine.bundle/bin:$PATH" wine $exe --crc-file "Z:$BFME_ROOT/logs/texstash-$name.crc" "$@" \
    > logs/texstash-$name.txt 2>/dev/null || echo "run exited $?"
  PATH="$BFME_ROOT/$eng/wswine.bundle/bin:$PATH" wineserver -w
  grep -E '^(VA (device|loaded|drawn|after|released)|LOAD|UPLOAD|FRAMES|EVICT|PEAK|FAIL)' logs/texstash-$name.txt \
    | awk '!/^VA loaded/ || ++n % 4 == 0 || /FAIL/'
done
python3 - "$BFME_ROOT/logs/texstash-w10.crc" "$BFME_ROOT/logs/texstash-0022.crc" <<'EOF'
import sys, collections
a, b = ({tuple(l.split()[1:3]): l.split()[3] for l in open(p) if l.startswith("CRC")} for p in sys.argv[1:3])
both = sorted(set(a) & set(b), key=lambda k: (k[0], int(k[1])))
diff = [k for k in both if a[k] != b[k]]
per = collections.Counter(k[0] for k in both)
print("CRC: %d draws in both runs (%s), %d differ%s" % (len(both), ", ".join("%s %d" % kv for kv in sorted(per.items())),
      len(diff), (": " + ", ".join("%s %s" % k for k in diff[:8])) if diff else ""))
print("only in the 0022 run: %d draws (textures the unpatched process could not create)" % len(set(b) - set(a)))
EOF
