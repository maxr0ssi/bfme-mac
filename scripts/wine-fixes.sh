#!/bin/zsh
# scripts/wine-fixes.sh [--revert] — build our fixes to Wine 10.0 and install them into
# engines/$WINE_BUILD (default w10), the engine both games play on.
#
# Each fix is a patch series under patches/ and the one DLL it changes. The series are applied in
# FIXES order onto wine-10.0 in the worktree wine/src-d3dx10, only the DLLs are built, and each is
# copied over the engine's own (kept once as <dll>.orig-$WINE_BUILD):
#
#   d3dx9    patches/d3dx9-setrawvalue       d3dx9_27.dll  loading time ~170 s -> ~12 s (docs/LOAD-TIME.md)
#   wined3d  patches/wined3d-wow64-buffers   wined3d.dll + wined3d.so (new unix library)
#            big battles: buffer locks stop waiting for the render thread and are written straight into
#            host GPU memory; redundant state work removed (docs/PERFORMANCE.md)
#
# The 32-bit DLLs are built with SSE2 maths instead of x87, which Rosetta emulates slowly
# (FIX_CFLAGS; objects are rebuilt when it changes). A unix library the engine does not have is
# installed next to its DLLs with a <name>.added-$WINE_BUILD marker, so --revert can remove it.
#
#   scripts/wine-fixes.sh             build (first run ~2 min), install every fix
#   scripts/wine-fixes.sh --revert    put the engine's own DLLs back
set -e
export BFME_ROOT="${0:A:h:h}"
export WINE_BUILD="${WINE_BUILD:-w10}"
. "$BFME_ROOT/env.sh"
command -v wine >/dev/null || exit 1
pgrep -f '(lotrbfme2(ep1)?\.exe|game\.dat) -win' >/dev/null && { echo "a game is running; close it first"; exit 1; }

# name | patch series | make target | DLL override to set ("" = none) | unix library target ("" = none)
FIXES=(
  "d3dx9|d3dx9-setrawvalue|dlls/d3dx9_27/i386-windows/d3dx9_27.dll|*d3dx9_27=builtin|"
  "wined3d|wined3d-wow64-buffers|dlls/wined3d/i386-windows/wined3d.dll||dlls/wined3d/wined3d.so"
)
FIX_CFLAGS="-g -O2 -msse2 -mfpmath=sse"
DLLDIR="$(cd "$(dirname "$(command -v wine)")/../lib/wine/i386-windows" && pwd)"
UNIXDIR="${DLLDIR:h}/x86_64-unix"
SRC="$BFME_ROOT/wine/src-d3dx10"
BRANCH=bfme-fixes-10.0

set_override() {   # "name=value"
  wine reg add 'HKCU\Software\Wine\DllOverrides' /v "${1%%=*}" /t REG_SZ /d "${1#*=}" /f >/dev/null 2>&1
  wineserver -w
  echo "prefixes/$WINE_BUILD: $1"
}

if [[ "${1:-}" == "--revert" ]]; then
  for f in $FIXES; do
    dll="$DLLDIR/$(basename "$(echo "$f" | cut -d'|' -f3)")"
    [[ -f "$dll.orig-$WINE_BUILD" ]] && cp "$dll.orig-$WINE_BUILD" "$dll" && echo "restored the engine's $(basename "$dll")"
    ov=$(echo "$f" | cut -d'|' -f4)
    [[ -n "$ov" ]] && set_override "${ov%%=*}=native"
    ux=$(echo "$f" | cut -d'|' -f5)
    so="$UNIXDIR/$(basename "$ux")"
    [[ -n "$ux" && -f "$so.added-$WINE_BUILD" ]] && rm -f "$so" "$so.added-$WINE_BUILD" && echo "removed $(basename "$so")"
  done
  exit 0
fi

# wine-10.0 + every series, in a worktree of the existing clone so wine/src stays on its own branch
series=()
for f in $FIXES; do series+=("$BFME_ROOT/patches/$(echo "$f" | cut -d'|' -f2)"); done
want=0
for s in $series; do want=$(( want + $(ls "$s"/*.patch | wc -l) )); done
if [[ ! -e "$SRC/.git" ]]; then
  [[ -d "$BFME_ROOT/wine/src/.git" ]] || { echo "no Wine clone at wine/src (patches/WINE-BUILD.md)"; exit 1; }
  git -C "$BFME_ROOT/wine/src" worktree add --detach "$SRC" wine-10.0
fi
have=$(git -C "$SRC" rev-list --count wine-10.0..HEAD)
if [[ "$have" != "$want" ]]; then
  echo "rebuilding the worktree branch $BRANCH: wine-10.0 + ${#series} patch series ($want patches)"
  git -C "$SRC" checkout -q -B "$BRANCH" wine-10.0
  for s in $series; do git -C "$SRC" am -q "$s"/*.patch; done
fi

targets=()
for f in $FIXES; do
  targets+=("$(echo "$f" | cut -d'|' -f3)")
  ux=$(echo "$f" | cut -d'|' -f5); [[ -n "$ux" ]] && targets+=("$ux")
done
# make does not track compiler flags: drop the fixed DLLs' 32-bit objects when FIX_CFLAGS changed
BUILD="$BFME_ROOT/wine/build-d3dx10"; stamp="$BUILD/.wine-fixes-cflags"
if [[ -d "$BUILD" && "$(cat "$stamp" 2>/dev/null)" != "$FIX_CFLAGS" ]]; then
  for f in $FIXES; do find "$BUILD/$(dirname "$(echo "$f" | cut -d'|' -f3)")" -name '*.o' -delete 2>/dev/null; done
fi
WINE_SRC="$SRC" MAKE_TARGETS="${targets[*]}" I386_CFLAGS="$FIX_CFLAGS" "$BFME_ROOT/scripts/build-wine.sh" d3dx10 --disable-tests
echo "$FIX_CFLAGS" > "$stamp"

for f in $FIXES; do
  target=$(echo "$f" | cut -d'|' -f3); ov=$(echo "$f" | cut -d'|' -f4)
  dll="$DLLDIR/$(basename "$target")"
  [[ -f "$dll.orig-$WINE_BUILD" ]] || cp "$dll" "$dll.orig-$WINE_BUILD"
  cp "$BFME_ROOT/wine/build-d3dx10/$target" "$dll"
  echo "installed patched $(basename "$dll") into $DLLDIR (engine copy kept as $(basename "$dll").orig-$WINE_BUILD)"
  [[ -n "$ov" ]] && set_override "$ov"
  ux=$(echo "$f" | cut -d'|' -f5)
  if [[ -n "$ux" ]]; then
    so="$UNIXDIR/$(basename "$ux")"
    [[ -f "$so" || -f "$so.added-$WINE_BUILD" ]] || touch "$so.added-$WINE_BUILD"
    [[ -f "$so.added-$WINE_BUILD" ]] || { echo "$so exists and is not ours; not replacing it"; continue; }
    cp "$BFME_ROOT/wine/build-d3dx10/$ux" "$so"
    echo "installed $(basename "$so") into $UNIXDIR (remove with --revert)"
  fi
done
