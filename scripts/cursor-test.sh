#!/bin/zsh
# scripts/cursor-test.sh - every RotWK cursor through engines/$WINE_BUILD's Mac driver (default w10),
# without the game. Builds tools/cursortest.c, runs it in a throwaway prefix (build/prefix-cursor)
# with WINEDEBUG=+cursor, and checks each cursor became NSCursor frames, not the macOS arrow
# (winemac falls back to the arrow when it cannot convert a cursor). Reads the cursor files from the
# game folder and never writes there. Moves the pointer once and puts it back.
#   scripts/cursor-test.sh            exit status = cursors that became the arrow (0 = pass)
set -eu
BFME_ROOT="${0:A:h:h}"
export BFME_ROOT WINE_BUILD="${WINE_BUILD:-w10}"
. "$BFME_ROOT/env.sh"
[[ "${1:-}" == (-h|--help) ]] && usage
game_running && { echo "a game is running; close it first"; exit 1; }
cursors="$WINEPREFIX/drive_c/Program Files (x86)/Electronic Arts/RotWK/data/cursors"
[[ -d $cursors ]] || { echo "no $cursors"; exit 1; }
src=$BFME_ROOT/tools/cursortest.c exe=$BFME_ROOT/build/cursortest.exe
if [[ ! -x $exe || $src -nt $exe ]]; then
  i686-w64-mingw32-gcc -O2 -Wall -o "$exe" "$src" -lgdi32 || { echo "build failed"; exit 1; }
fi
export WINEPREFIX="$BFME_ROOT/build/prefix-cursor"
[[ -d $WINEPREFIX ]] || { WINEDEBUG=-all wine wineboot -i >/dev/null 2>&1; wineserver -w; }
out=$BFME_ROOT/build/cursortest.out trace=$BFME_ROOT/build/cursortest.trace
WINEDEBUG=+cursor wine "$exe" "Z:${cursors//\//\\}" >"$out" 2>"$trace"
wineserver -w
# each handle the tool set -> what macdrv_SetCursor made of it (frames, or a named Cocoa cursor)
awk '
  FNR == NR { if ($2 ~ /\./) name[tolower($1)] = $2; next }
  /macdrv_SetCursor 0x/ { split($0, f, " "); h = f[3]; sub(/^0x/, "", h); h = sprintf("%08s", h); gsub(/ /, "0", h); last = tolower(h); next }
  /setting cursor with cursor_name/ && (last in name) {
    if ($0 ~ /cursor_name \(null\) cursor_frames 0x[1-9a-f]/) ok[last] = 1; else bad[last] = $0
  }
  END {
    n = 0; for (h in name) { if (h in bad) { print "ARROW " name[h] ": " bad[h]; fails++ } else if (h in ok) n++; else { print "NOT SET " name[h]; fails++ } }
    printf "%d cursors converted to frames, %d failed\n", n, fails; exit fails
  }' "$out" "$trace"
