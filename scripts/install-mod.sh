#!/bin/zsh
# scripts/install-mod.sh <bfme2|rotwk> <directory | zip> — drop a mod's files
# (.big archives and anything else it ships) into a game folder, keeping a restorable copy of
# everything it overwrites as <file>.premod.bak, and logging what it did to mods-installed.log
# next to the game. Art-only mods are multiplayer-safe; anything touching an .ini is not, and
# every peer needs the identical files (see MULTIPLAYER.md, docs/MODDING.md).
#   scripts/install-mod.sh bfme2 ~/Downloads/mymod     a directory tree of files to copy in
#   scripts/install-mod.sh rotwk ~/Downloads/mod.zip   a zip of the same
#   scripts/install-mod.sh rotwk --revert              put the .premod.bak originals back
# GAMEDIR= overrides the target folder (used by the tests); WINE_BUILD= picks the prefix.
set -e
export WINE_BUILD="${WINE_BUILD:-w10}"
export BFME_ROOT="${0:A:h:h}"
. "$BFME_ROOT/env.sh"

SELF="${0:A}"   # zsh rebinds $0 to the function name inside a function; keep the path here
usage() {
  sed -n '2,11p' "$SELF" | sed 's/^# \{0,1\}//'
  exit 1
}

game=""; src=""; revert=0
for a in "$@"; do
  case "$a" in
    --revert) revert=1 ;;
    -h|--help) usage ;;
    bfme2|rotwk) game="$a" ;;
    *) src="$a" ;;
  esac
done
case "$game" in
  bfme2) sub="BFME2" ;;
  rotwk) sub="RotWK" ;;
  *) usage ;;
esac
[ -n "$src" ] || [ "$revert" = 1 ] || usage

GAMEDIR="${GAMEDIR:-$WINEPREFIX/drive_c/Program Files (x86)/Electronic Arts/$sub}"
[ -d "$GAMEDIR" ] || { echo "no game folder at $GAMEDIR"; exit 1; }
LOG="$GAMEDIR/mods-installed.log"
stamp="$(date +%Y-%m-%dT%H:%M:%S)"

# A half-written .big under a running game is how you lose an install (same guard as the
# NX_COMPAT experiment in patches/nxcompat/install.sh).
pgrep -f 'lotrbfme2ep1|lotrbfme2.exe|game.dat' >/dev/null && { echo "a game is running; quit it first"; exit 1; }

if [ "$revert" = 1 ]; then
  # Only the installs since the last revert are live; everything before it was already undone.
  typeset -a added
  if [ -f "$LOG" ]; then
    while IFS=$'\t' read -r _s act _g kind rel _rest; do
      [ "$act" = "revert" ] && added=() && continue
      [ "$act" = "install" ] && [ "$kind" = "new" ] && added+=("$rel")
    done < "$LOG"
  fi
  n=0
  for b in "$GAMEDIR"/**/*.premod.bak(N); do
    mv "$b" "${b%.premod.bak}"
    printf '%s\trevert\t%s\trestored\t%s\t-\n' "$stamp" "$game" "${${b%.premod.bak}#$GAMEDIR/}" >>"$LOG"
    n=$((n+1))
  done
  m=0
  for rel in $added; do
    [ -f "$GAMEDIR/$rel" ] || continue
    rm -f "$GAMEDIR/$rel"
    printf '%s\trevert\t%s\tremoved\t%s\t-\n' "$stamp" "$game" "$rel" >>"$LOG"
    m=$((m+1))
  done
  echo "reverted $sub: $n file(s) restored from .premod.bak, $m added file(s) removed"
  exit 0
fi

# ---- where the files come from -------------------------------------------------------------
if [ -d "$src" ]; then
  srcdir="${src:A}"
elif [ -f "$src" ] && [[ "$src" == *.zip ]]; then
  srcdir="$BFME_ROOT/build/mod-staging/${${src:t}%.zip}"
  mkdir -p "$srcdir"
  echo "unzipping ${src:t} -> $srcdir"
  unzip -oq "$src" -d "$srcdir"
else
  echo "$src is neither a directory nor a .zip"; exit 1
fi
[ -d "$srcdir" ] || { echo "nothing to install from $src"; exit 1; }

# ---- copy it in, backing up first ------------------------------------------------------------
echo "installing into $GAMEDIR"
n=0; b=0
while IFS= read -r -d '' f; do
  rel="${f#$srcdir/}"
  dest="$GAMEDIR/$rel"
  mkdir -p "${dest:h}"
  kind="new"
  if [ -f "$dest" ]; then
    # Keep the *first* backup: a second install must not overwrite the pristine original.
    [ -f "$dest.premod.bak" ] || cp "$dest" "$dest.premod.bak"
    kind="backup"; b=$((b+1))
  fi
  cp "$f" "$dest"
  printf '%s\tinstall\t%s\t%s\t%s\t%s\n' "$stamp" "$game" "$kind" "$rel" "$src" >>"$LOG"
  echo "  $kind  $rel"
  n=$((n+1))
done < <(find "$srcdir" -type f ! -name '.DS_Store' ! -name '*.part' -print0)

echo "installed $n file(s) into $sub ($b replaced, originals kept as *.premod.bak)"
echo "log: $LOG    undo: scripts/install-mod.sh $game --revert"
