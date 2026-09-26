#!/bin/zsh
# scripts/measure-session.sh on|sample [label]|summary|off — one measuring session of RotWK, played by you.
#   on        diagnostics on in the installed gamepatch.ini (passtimers, renderstats, particlestats);
#             they cost ~2 ms/frame, so judge smoothness in a normal session, not this one
#   sample    during a heavy fight: 20 s read-only sample of the game's main thread with stack scan
#             (build/eipsample.exe, pauses the thread ~80 us every 5 ms; never attaches a debugger),
#             then the inclusive call tree (tools/callstacks.py) -> logs/incl-<label>{,-tree}.txt
#   summary   frame-time distribution and the latest per-pass lines from logs/gamepatch.log
#   off       diagnostics off again (the speed patches stay on)
set -eu
BFME_ROOT="${0:A:h:h}"; cd "$BFME_ROOT"
INI="prefixes/w10/drive_c/Program Files (x86)/Electronic Arts/RotWK/gamepatch.ini"
LOG=logs/gamepatch.log
running() { pgrep -f '(lotrbfme2(ep1)?\.exe|game\.dat) -win' >/dev/null; }
setkey() {   # setkey name value: [patches] name=value, added after the [patches] header if missing
  if grep -q "^$1=" "$INI"; then sed -i '' "s/^$1=.*/$1=$2/" "$INI"
  else sed -i '' "/^\[patches\]/a\\
$1=$2
" "$INI"; fi
}
case "${1:-}" in
on|off)
  [[ -f "$INI" ]] || { echo "gamepatch is not installed (scripts/game-patch.sh)"; exit 1; }
  v=$([[ $1 == on ]] && echo 1 || echo 0)
  for k in passtimers renderstats particlestats; do setkey $k $v; done
  running && echo "note: the game is running; this applies from its next start"
  grep -E '^(passtimers|renderstats|particlestats)=' "$INI" ;;
sample)
  running || { echo "the game is not running"; exit 1; }
  label=${2:-$(date +%Y%m%d-%H%M%S)}; out=logs/incl-$label.txt
  echo "sampling the main thread for 20 s -> $out"
  WINE_BUILD=w10 . ./env.sh
  WINEMSYNC=1 WINEDEBUG=-all wine build/eipsample.exe 20 5 lotrbfme2ep1.exe main > "$out" 2>/dev/null   # harness-allow: sampler, not a game launch
  python3 tools/callstacks.py "$out" --exe build/rotwk-re/disk.exe --funcs build/rotwk-re/funcs.txt \
    --names build/rotwk-re/names-auto.txt --names build/rotwk-re/names.txt \
    --root 0x44b788 --root 0x449cf8 --root 0x62e4e8 --root 0x59cd70 > "${out%.txt}-tree.txt"
  head -12 "$out"; echo "tree: ${out%.txt}-tree.txt" ;;
summary)
  since=${2:-00:00:00}
  awk -v s="$since" '$2>=s' "$LOG" | grep "passtimers: 5.0 s" | sed -E 's/.*\(([0-9.]+) ms\/frame.*/\1/' | python3 -c "
import sys
v=[float(x) for x in sys.stdin]
if not v: sys.exit('no passtimers windows since then')
print(f'{len(v)} windows of 5 s ({len(v)*5/60:.0f} min)')
for lo,hi in ((0,34),(34,40),(40,50),(50,60),(60,1e9)):
    c=sum(lo<=x<hi for x in v); print(f'  {lo:>3}-{hi if hi<1e9 else \"\":<3} ms: {c:4d} ({100*c/len(v):.0f}%)')
print('  worst:', sorted(v)[-3:])"
  awk -v s="$since" '$2>=s' "$LOG" | grep -E "renderstats: (ms|HLod|last)|particlestats:|logicmath:" | tail -6 | cut -c12-400 ;;
*) sed -n '2,10p' "$0"; exit 1 ;;
esac
