#!/bin/zsh
# scripts/wine-0022.sh --stage | --install | --revert | --status — wined3d patch 0022 (managed textures'
# system memory kept in host memory, out of the game's 4 GB; docs/MEMORY-4GB.md "Patch 0022") on top of
# the series scripts/wine-fixes.sh installs, staged and installed on its own so it can be tried and
# taken back without touching the rest.
#
#   --stage    worktree wine/src-0022 = the branch wine-fixes.sh builds (bfme-fixes-10.0, wine/src-d3dx10)
#              + patches/wined3d-wow64-buffers/unbuilt/0022-*.patch; builds wined3d.dll and wined3d.so in
#              wine/build-0022 with wine-fixes.sh's flags; copies them to build/wine-0022/ and makes
#              build/engine-0022 (an APFS clone of engines/$WINE_BUILD with them in) for scripts/texstash.sh.
#              Refuses when the engine's wined3d is not the series build (run scripts/wine-fixes.sh first).
#   --install  copies the staged pair into engines/$WINE_BUILD (the engine's current pair kept once as
#              <file>.pre0022-$WINE_BUILD.bak); WINED3D_STASH_MANAGED=0 switches it off without reinstalling
#   --revert   puts the kept pair back
#   --status   which wined3d the engine has
# To make it permanent, move the patch out of unbuilt/ (wine-fixes.sh then builds it with the rest).
set -eu
BFME_ROOT="${0:A:h:h}"
export BFME_ROOT WINE_BUILD="${WINE_BUILD:-w10}"
. "$BFME_ROOT/scripts/lib.sh"
cd "$BFME_ROOT"
[[ "${1:-}" == (--stage|--install|--revert|--status) ]] || usage 2
LIB=engines/$WINE_BUILD/wswine.bundle/lib/wine
DLL=$LIB/i386-windows/wined3d.dll SO=$LIB/x86_64-unix/wined3d.so
OUT=build/wine-0022
PATCH=(patches/wined3d-wow64-buffers/unbuilt/0022-*.patch)

case $1 in
--status)
  for f in $DLL $SO; do
    s=$(md5 -q $f)
    w=series; [[ -f $OUT/${f:t} && $s == $(md5 -q $OUT/${f:t}) ]] && w=0022
    echo "${f:t}: $w ($s)"
  done ;;
--stage)
  series=wine/build-d3dx10/dlls/wined3d
  [[ $(md5 -q $DLL) == $(md5 -q $series/i386-windows/wined3d.dll) && $(md5 -q $SO) == $(md5 -q $series/wined3d.so) ]] \
    || { echo "engines/$WINE_BUILD's wined3d is not the series build; run scripts/wine-fixes.sh first"; exit 1; }
  base=$(git -C wine/src-d3dx10 rev-parse HEAD)
  if [[ ! -e wine/src-0022/.git ]]; then git -C wine/src worktree add --detach "$BFME_ROOT/wine/src-0022" $base; fi
  if [[ $(git -C wine/src-0022 rev-parse HEAD~1) != $base || $(git -C wine/src-0022 log -1 --format=%s) != *"host memory under WoW64"* ]]; then
    git -C wine/src-0022 checkout -q --detach $base
    git -C wine/src-0022 -c user.name="bfme" -c user.email="bfme@localhost" am -q "$BFME_ROOT/$PATCH[1]"
  fi
  WINE_SRC="$BFME_ROOT/wine/src-0022" MAKE_TARGETS="dlls/wined3d/i386-windows/wined3d.dll dlls/wined3d/wined3d.so" \
    I386_CFLAGS="-g -O2 -msse2 -mfpmath=sse" scripts/build-wine.sh 0022 --disable-tests | tail -1
  mkdir -p $OUT
  cp wine/build-0022/dlls/wined3d/i386-windows/wined3d.dll wine/build-0022/dlls/wined3d/wined3d.so $OUT/
  [[ -d build/engine-0022 ]] && mv build/engine-0022 build/.trash-engine-0022-$(date +%s)
  cp -cR engines/$WINE_BUILD build/engine-0022
  cp $OUT/wined3d.dll build/engine-0022/wswine.bundle/lib/wine/i386-windows/
  cp $OUT/wined3d.so build/engine-0022/wswine.bundle/lib/wine/x86_64-unix/
  echo "staged $OUT/wined3d.dll + wined3d.so ($(md5 -q $OUT/wined3d.dll)); build/engine-0022 for scripts/texstash.sh"
  echo "install: scripts/wine-0022.sh --install   (undo: scripts/wine-0022.sh --revert)" ;;
--install)
  game_running && { echo "a game is running; quit it first"; exit 1; }
  [[ -f $OUT/wined3d.dll && -f $OUT/wined3d.so ]] || { echo "nothing staged: scripts/wine-0022.sh --stage"; exit 1; }
  for f in $DLL $SO; do
    [[ -f $f.pre0022-$WINE_BUILD.bak ]] || cp $f $f.pre0022-$WINE_BUILD.bak
    cp $OUT/${f:t} $f
    echo "installed 0022 ${f:t} into ${f:h} (previous kept as ${f:t}.pre0022-$WINE_BUILD.bak)"
  done ;;
--revert)
  game_running && { echo "a game is running; quit it first"; exit 1; }
  for f in $DLL $SO; do
    [[ -f $f.pre0022-$WINE_BUILD.bak ]] && mv $f.pre0022-$WINE_BUILD.bak $f && echo "restored ${f:t}"
  done ;;
esac
