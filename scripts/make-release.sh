#!/bin/zsh
# scripts/make-release.sh — package the built fixes as build/release/bfme-mac-fixes-<version>.tar.gz,
# the file scripts/install.sh installs from (--from <file>, or a GitHub Release once the repo is public).
#
# Contents: the patched Wine DLLs exactly as installed in engines/w10 (scripts/wine-fixes.sh builds and
# installs them; this script refuses if the build tree and the engine disagree), the game patch
# (dinput8.dll; gamepatch.ini with the diagnostic counters off; t_misc.exe, which checks a user's
# exe against every patch site before install), LICENSE, NOTICE, patches/COPYING.LIB, a SOURCES.md naming the Wine source and patch series (LGPL:
# the corresponding source is this repo at the recorded commit), and SHA256SUMS.
#   scripts/make-release.sh [--buildings [dwarves,elves,men,goblins,isengard,mordor,angmar,neutral]]
# --buildings also packs the finished buildings (every faction above by default but neutral, the
# capturable inns and lairs, which joins once it has been checked in game; with its builder where it has one) as build/release/bfme-mac-buildings-<faction>-<version>.tar.gz, the files
# install.sh --buildings installs: `python3 -m sagekit install <faction> --check` stages the current
# build (a builder is staged by `python3 -m sagekit unit <faction>/porter --stage`; the pack refuses
# one that is not the reviewed build; its HUD icons, `!!!!!!!!!!!!!!sagekit-icons-<faction>.big`, come from
# the last `python3 -m sagekit icons <faction>` run whose page checks passed), then `python3 -m sagekit.pack build` turns every archive
# member into a delta against the EA files it was made from, checks the inserted bytes hold no run of
# EA's, and adds the asset.dat edits (sagekit/pack.py, sagekit/packbuild.py). No EA file is in a pack. The fixes file lists the packs in BUILDINGS (faction, file, SHA-256, bytes);
# build/release/SHA256SUMS-<version> covers every file to publish.
# It only copies into a fresh staging dir; installed files are compared, never overwritten, so no
# .orig/.bak copies are needed here.
set -eu
BFME_ROOT="${0:A:h:h}"
. "$BFME_ROOT/scripts/lib.sh"
cd "$BFME_ROOT"
BUILDINGS=""
while (( $# )); do
  case "$1" in
    --buildings) if [[ $# -gt 1 && "$2" != -* ]]; then BUILDINGS="${2//,/ }"; shift; else BUILDINGS="dwarves elves men goblins isengard mordor angmar"; fi ;;
    -h|--help) usage ;;
    *) usage 2 ;;
  esac
  shift
done
ENGINE_TAR="WS12WineSikarugir10.0_6.tar.xz"
ENGINE_SHA="9da7ee0cbf386522f3a9906943726d9c3c125dbbd9ab120e3cde80e88d6091b2"
WB="$BFME_ROOT/wine/build-d3dx10"
LIB="$BFME_ROOT/engines/w10/wswine.bundle/lib/wine"
# release path | built file | installed file (must be identical)
FILES=(
  "wine/i386-windows/d3dx9_27.dll|$WB/dlls/d3dx9_27/i386-windows/d3dx9_27.dll|$LIB/i386-windows/d3dx9_27.dll"
  "wine/i386-windows/wined3d.dll|$WB/dlls/wined3d/i386-windows/wined3d.dll|$LIB/i386-windows/wined3d.dll"
  "wine/x86_64-unix/wined3d.so|$WB/dlls/wined3d/wined3d.so|$LIB/x86_64-unix/wined3d.so"
)

for f in $FILES; do
  built=${${f#*|}%%|*}; inst=${f##*|}
  [[ -f "$built" ]] || { echo "missing $built: run scripts/wine-fixes.sh first"; exit 1; }
  cmp -s "$built" "$inst" || { echo "$inst differs from the build: run scripts/wine-fixes.sh, play-test, then release"; exit 1; }
done
make -s -C gamepatch MINGW="${MINGW:-/opt/homebrew/bin/i686-w64-mingw32-gcc}"

commit=$(git rev-parse --short HEAD)
[[ -z "$(git status --porcelain -- patches gamepatch)" ]] || { echo "patches/ or gamepatch/ has uncommitted changes; commit first"; exit 1; }
version="$(date +%Y%m%d)-$commit"
name="bfme-mac-fixes-$version"
STAGE="$BFME_ROOT/build/release/$name"
rm -rf "$STAGE"; mkdir -p "$STAGE/wine/i386-windows" "$STAGE/wine/x86_64-unix" "$STAGE/gamepatch"

for f in $FILES; do cp "${${f#*|}%%|*}" "$STAGE/${f%%|*}"; done
cp build/gamepatch/dinput8.dll build/gamepatch/t_misc.exe gamepatch/gamepatch.ini "$STAGE/gamepatch/"
# diagnostics ship off (scripts/measure-session.sh on turns them on); every patch keeps the repo default
sed -i '' -E 's/^(passtimers|shadowstats|renderstats|particlestats)=1$/\1=0/' "$STAGE/gamepatch/gamepatch.ini"
cp LICENSE NOTICE patches/COPYING.LIB "$STAGE/"
{
  echo "# bfme-mac-fixes $version"
  echo
  echo "Built from https://github.com/maxr0ssi/bfme-mac at commit $commit."
  echo
  echo "Wine files (LGPL-2.1-or-later, COPYING.LIB): Wine 10.0 (tag wine-10.0,"
  echo "https://gitlab.winehq.org/wine/wine) with these patch series from the repo's patches/ applied in"
  echo "order, 32-bit code built with \`-O2 -msse2 -mfpmath=sse\` (scripts/wine-fixes.sh):"
  echo
  for s in d3dx9-setrawvalue wined3d-wow64-buffers; do
    for p in patches/$s/*.patch; do echo "- \`$p\` $(shasum -a 256 "$p" | cut -c1-16)"; done
  done
  echo
  echo "For the Wine engine $ENGINE_TAR (Sikarugir, sha256 $ENGINE_SHA)."
  echo
  echo "Game patch (MIT, LICENSE): gamepatch/ at the same commit, for Rise of the Witch-king 2.02."
} > "$STAGE/SOURCES.md"
echo "$ENGINE_TAR $ENGINE_SHA" > "$STAGE/ENGINE"
OUT="$BFME_ROOT/build/release"
packs=()
for f in ${=BUILDINGS}; do
  p="bfme-mac-buildings-$f-$version"
  python3 -m sagekit install "$f" --check
  python3 -m sagekit.pack build "$f" --version "$version" --out "$OUT"
  tar -C "$OUT" -czf "$OUT/$p.tar.gz" "$p" && rm -rf "$OUT/$p"
  echo "$f $p.tar.gz $(shasum -a 256 "$OUT/$p.tar.gz" | cut -d' ' -f1) $(stat -f %z "$OUT/$p.tar.gz")" >> "$STAGE/BUILDINGS"
  packs+=("$p.tar.gz")
  echo "$p.tar.gz ($(du -h "$OUT/$p.tar.gz" | cut -f1))"
done
[[ -z "$BUILDINGS" ]] || echo "Building packs (BUILDINGS): the finished buildings from assets/ at the same commit (sagekit/pack.py), for RotWK 2.02. They hold our changes only; the installer rebuilds each file from the player's own game." >> "$STAGE/SOURCES.md"
( cd "$STAGE" && find . -type f ! -name SHA256SUMS | sed 's|^\./||' | sort | xargs shasum -a 256 > SHA256SUMS )

tar -C "$OUT" -czf "$OUT/$name.tar.gz" "$name"
( cd "$OUT" && shasum -a 256 "$name.tar.gz" "${packs[@]}" > "SHA256SUMS-$version" )
echo "build/release/$name.tar.gz ($(du -h "$OUT/$name.tar.gz" | cut -f1))"
echo "sha256 $(shasum -a 256 "$OUT/$name.tar.gz" | cut -d' ' -f1)"
echo "publish (install.sh downloads the latest release): gh release create v$version \\
  build/release/$name.tar.gz ${packs[@]/#/build/release/} build/release/SHA256SUMS-$version \\
  --title \"Fixes $version\" --notes-file $STAGE/SOURCES.md"
