#!/bin/zsh
# scripts/make-release.sh — package the built fixes as build/release/bfme-mac-fixes-<version>.tar.gz,
# the file scripts/install.sh installs from (--from <file>, or a GitHub Release once the repo is public).
#
# Contents: the patched Wine DLLs exactly as installed in engines/w10 (scripts/wine-fixes.sh builds and
# installs them; this script refuses if the build tree and the engine disagree), the game patch
# (dinput8.dll; gamepatch.ini with the diagnostic counters off; t_misc.exe, which checks a user's
# exe against every patch site before install), LICENSE, patches/COPYING.LIB, a SOURCES.md naming the Wine source and patch series (LGPL:
# the corresponding source is this repo at the recorded commit), and SHA256SUMS.
#   scripts/make-release.sh
# It only copies into a fresh staging dir; installed files are compared, never overwritten, so no
# .orig/.bak copies are needed here.
set -eu
BFME_ROOT="${0:A:h:h}"
cd "$BFME_ROOT"
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
cp LICENSE patches/COPYING.LIB "$STAGE/"
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
( cd "$STAGE" && find . -type f ! -name SHA256SUMS | sed 's|^\./||' | sort | xargs shasum -a 256 > SHA256SUMS )

tar -C "$BFME_ROOT/build/release" -czf "$BFME_ROOT/build/release/$name.tar.gz" "$name"
echo "build/release/$name.tar.gz ($(du -h "$BFME_ROOT/build/release/$name.tar.gz" | cut -f1))"
echo "sha256 $(shasum -a 256 "$BFME_ROOT/build/release/$name.tar.gz" | cut -d' ' -f1)"
echo "publish (install.sh downloads the latest release): gh release create v$version \\
  build/release/$name.tar.gz --title \"Fixes $version\" --notes-file $STAGE/SOURCES.md"
