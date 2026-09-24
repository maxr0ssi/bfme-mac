#!/bin/zsh
# scripts/d3dx9-fix.sh [--revert] — build Wine 10.0's d3dx9_27.dll with patches/d3dx9-setrawvalue/,
# install it into engines/$WINE_BUILD (default w10) and switch prefixes/$WINE_BUILD over to it.
#
# Why: the slow second half of the loading bar is Microsoft's native d3dx9_27 (2005, x87 code that
# Rosetta emulates slowly) processing textures. Wine's own d3dx9_27 loads the same map in ~12 s instead
# of ~170 s, but Wine 10.0 draws skinned units invisible because ID3DXEffect::SetRawValue is a stub
# and the games upload their bone palette through it. The patches backport upstream's SetRawValue,
# add the struct case the games need, and import windowscodecs directly (delay-loaded, it faults
# with the Homebrew mingw toolchain). Details: docs/LOAD-TIME.md, patches/d3dx9-setrawvalue/README.md.
#
#   scripts/d3dx9-fix.sh             build (first run ~2 min), install, set *d3dx9_27=builtin
#   scripts/d3dx9-fix.sh --revert    put the engine's own DLL back and Microsoft's d3dx9_27 in charge
set -e
export BFME_ROOT="${0:A:h:h}"
export WINE_BUILD="${WINE_BUILD:-w10}"
. "$BFME_ROOT/env.sh"
command -v wine >/dev/null || exit 1
pgrep -f 'lotrbfme2|game\.dat' >/dev/null && { echo "a game is running; close it first"; exit 1; }

DLLDIR="$(cd "$(dirname "$(command -v wine)")/../lib/wine/i386-windows" && pwd)"
DLL="$DLLDIR/d3dx9_27.dll"
ORIG="$DLL.orig-$WINE_BUILD"          # the engine's own copy, kept before the first overwrite
SRC="$BFME_ROOT/wine/src-d3dx10"
PATCHES="$BFME_ROOT/patches/d3dx9-setrawvalue"

set_override() {
  wine reg add 'HKCU\Software\Wine\DllOverrides' /v '*d3dx9_27' /t REG_SZ /d "$1" /f >/dev/null 2>&1
  wineserver -w
  echo "prefixes/$WINE_BUILD: *d3dx9_27 = $1"
}

if [[ "${1:-}" == "--revert" ]]; then
  [[ -f "$ORIG" ]] && cp "$ORIG" "$DLL" && echo "restored the engine's d3dx9_27.dll"
  set_override native
  exit 0
fi

# Wine 10.0 + the patches, in a worktree of the existing clone so wine/src stays on its own branch.
if [[ ! -e "$SRC/.git" ]]; then
  [[ -d "$BFME_ROOT/wine/src/.git" ]] || { echo "no Wine clone at wine/src (patches/WINE-BUILD.md)"; exit 1; }
  git -C "$BFME_ROOT/wine/src" worktree add --detach "$SRC" wine-10.0
  git -C "$SRC" checkout -q -b d3dx9-setrawvalue-10.0
  git -C "$SRC" am -q "$PATCHES"/*.patch
fi
want=$(ls "$PATCHES"/*.patch | wc -l | tr -d ' ')
have=$(git -C "$SRC" rev-list --count wine-10.0..HEAD)
[[ "$have" == "$want" ]] || { echo "$SRC has $have commits on wine-10.0, expected $want; rebuild the worktree"; exit 1; }

WINE_SRC="$SRC" MAKE_TARGETS=dlls/d3dx9_27/i386-windows/d3dx9_27.dll \
  "$BFME_ROOT/scripts/build-wine.sh" d3dx10 --disable-tests

[[ -f "$ORIG" ]] || cp "$DLL" "$ORIG"
cp "$BFME_ROOT/wine/build-d3dx10/dlls/d3dx9_27/i386-windows/d3dx9_27.dll" "$DLL"
echo "installed patched d3dx9_27.dll into $DLLDIR (engine copy kept as $(basename "$ORIG"))"
set_override builtin
