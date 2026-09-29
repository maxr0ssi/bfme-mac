#!/bin/zsh
# scripts/perf-install.sh [--revert|--status] — every performance fix for RotWK in one step:
#   1. scripts/wine-fixes.sh   Wine 10.0 fixes (d3dx9 load time; patches/wined3d-wow64-buffers)
#   2. scripts/game-patch.sh   the in-memory game patch (gamepatch/gamepatch.ini says which are on)
# msync (WINEMSYNC=1) is already the default in play-rotwk.sh / play-bfme2.sh.
#
#   scripts/perf-install.sh            build and install both (first Wine build takes a few minutes)
#   scripts/perf-install.sh --revert   remove both: the engine's own DLLs and an unpatched game
#   scripts/perf-install.sh --status   what is installed now
#
# Switches without reinstalling (environment or gamepatch.ini in the RotWK folder):
#   GAMEPATCH=0 (all game patches off), GAMEPATCH_<NAME>=0/1 (one; SHADOWPAR=1 turns on multi-core
#   shadows), WINED3D_CLIENT_MAPS=0 (wined3d 0012-0014), WINED3D_PROGRAM_CACHE=0 (0019),
#   WINED3D_WOW64_BUFFERS=off (0003/0009/0016), WINEMSYNC=0.
set -eu
BFME_ROOT="${0:A:h:h}"
S="$BFME_ROOT/scripts"
. "$S/lib.sh"
[[ "${1:-}" == (-h|--help) ]] && usage
game_running && { echo "a game is running; quit it first"; exit 1; }

case "${1:-}" in
--revert)
  "$S/game-patch.sh" --revert || true
  "$S/wine-fixes.sh" --revert
  exit 0 ;;
--status)
  E="$BFME_ROOT/engines/${WINE_BUILD:-w10}/wswine.bundle/lib/wine"
  B="$BFME_ROOT/wine/build-d3dx10/dlls/wined3d"
  w=$(md5 -q "$E/i386-windows/wined3d.dll")
  if [[ -f "$B/i386-windows/wined3d.dll" && "$w" == "$(md5 -q "$B/i386-windows/wined3d.dll")" ]]; then
    echo "wined3d: patched build installed ($(ls "$BFME_ROOT"/patches/wined3d-wow64-buffers/*.patch | wc -l | tr -d ' ') patches)"
  elif [[ -f "$E/i386-windows/wined3d.dll.orig-${WINE_BUILD:-w10}" && "$w" == "$(md5 -q "$E/i386-windows/wined3d.dll.orig-${WINE_BUILD:-w10}")" ]]; then
    echo "wined3d: the engine's own (not patched)"
  else
    v=""; for f in "$BFME_ROOT"/build/wined3d-variants/*.dll(N); do [[ "$(md5 -q "$f")" == "$w" ]] && v=${f:t}; done
    echo "wined3d: ${v:+variant $v, }not the current patch build (md5 $w)"
  fi
  [[ -f "$E/x86_64-unix/wined3d.so.added-${WINE_BUILD:-w10}" ]] && echo "wined3d.so: ours, installed" || echo "wined3d.so: not installed"
  "$S/game-patch.sh" --status
  exit 0 ;;
"") ;;
*) usage 2 ;;
esac

"$S/wine-fixes.sh"
"$S/game-patch.sh"
echo
echo "done. Play with scripts/play-rotwk.sh; game-patch log: logs/gamepatch.log. Undo: scripts/perf-install.sh --revert"
