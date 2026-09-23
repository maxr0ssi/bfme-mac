#!/bin/zsh
# Launch BFME2 with DXVK (D3D9 -> Vulkan -> MoltenVK -> Metal) instead of Wine's wined3d/OpenGL.
# The DXVK d3d9.dll lives in the prefix's syswow64; "d3d9=n" selects it, play-bfme2.sh uses "d3d9=b".
# Shows an FPS overlay (DXVK_HUD) so the two renderers can be compared.
# Runs on the Wine 11.0 engine (WINE_BUILD unset -> stable), where the DXVK d3d9.dll is installed;
# that engine has the WoW64 bug, so this is an experiment script, not a way to play.
set -e
export BFME_ROOT="${0:A:h:h}"
. "$BFME_ROOT/env.sh"
GAMEDIR="$WINEPREFIX/drive_c/Program Files (x86)/Electronic Arts/BFME2"
LOGDIR="$BFME_ROOT/logs"; mkdir -p "$LOGDIR"
LOG="$LOGDIR/bfme2-dxvk-$(date +%Y%m%d-%H%M%S).log"

export WINE_CPU_TOPOLOGY=1:0
export WINEDLLOVERRIDES="mscoree,mshtml=;d3d9=n"
# DXVK's own HUD is off: its text shader uses gl_DrawID, which MoltenVK can't translate to Metal
# ("DrawIndex is not supported in MSL") and it takes the whole renderer down. Apple's Metal
# performance HUD gives FPS/frametime for any Metal-backed app instead.
export DXVK_HUD="${DXVK_HUD:-}"
export MTL_HUD_ENABLED="${MTL_HUD_ENABLED:-1}"
export DXVK_LOG_LEVEL="${DXVK_LOG_LEVEL:-info}"
export DXVK_LOG_PATH="$LOGDIR"
# MoltenVK: let it advertise features DXVK wants and log its own decisions.
export MVK_CONFIG_LOG_LEVEL="${MVK_CONFIG_LOG_LEVEL:-1}"

cd "$GAMEDIR"
echo "log: $LOG"
# Borderless: once the game window exists, AutoHotkey strips its title bar and pins it to (0,0)
# at screen size, so it behaves like fullscreen without exclusive mode (see ahk/borderless.ahk).
( cd "$BFME_ROOT/ahk" && sleep 8 && wine AutoHotkeyU32.exe borderless.ahk >/dev/null 2>&1 ) &
exec wine lotrbfme2.exe -win "$@" >"$LOG" 2>&1
