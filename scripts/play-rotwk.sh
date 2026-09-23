#!/bin/zsh
# Launch Rise of the Witch-king (Patch 2.02 + HD Edition) under Wine. Logs go to logs/.
#   ./play-rotwk.sh            wined3d (OpenGL) renderer
#   RENDERER=dxvk ./play-rotwk.sh   DXVK renderer (needs d3d9.dll from downloads/dxvk in the game dir)
set -e
# RotWK plays on the Wine 10.0 engine; Wine 11.x kills the main thread at match start (see patches/WINE-BUG-REPORT.md).
export WINE_BUILD="${WINE_BUILD:-w10}"
export BFME_ROOT="${0:A:h:h}"
. "$BFME_ROOT/env.sh"
GAMEDIR="$WINEPREFIX/drive_c/Program Files (x86)/Electronic Arts/RotWK"
LOGDIR="$BFME_ROOT/logs"; mkdir -p "$LOGDIR"
LOG="$LOGDIR/rotwk-$(date +%Y%m%d-%H%M%S).log"

export WINE_CPU_TOPOLOGY=1:0
if [[ "$RENDERER" == "dxvk" ]]; then
  export WINEDLLOVERRIDES="mscoree,mshtml=;d3d9=n"
  export DXVK_HUD=""            # DXVK's HUD text shader can't compile on MoltenVK (gl_DrawID)
  export MTL_HUD_ENABLED=1      # Apple's Metal HUD for FPS instead
  export DXVK_LOG_PATH="$LOGDIR"
else
  export WINEDLLOVERRIDES="mscoree,mshtml=;d3d9=b"
fi

cd "$GAMEDIR"
echo "log: $LOG"
# -win: exclusive fullscreen minimizes on focus loss and returns black under the Mac driver.
# Borderless: once the game window exists, AutoHotkey strips its title bar and pins it to (0,0)
# at screen size, so it behaves like fullscreen without exclusive mode. edgescroll.ahk does that
# and then stays resident to emulate screen-edge camera scrolling (the engine disables it in
# windowed mode); one Wine process for both jobs, because a second one this early crashes the
# game (see ahk/edgescroll.ahk and the note in scripts/test-skirmish.sh).
( cd "$BFME_ROOT/ahk" && sleep 8 && wine AutoHotkeyU32.exe edgescroll.ahk "${EDGESCROLL:-on}" 4 "${EDGESCROLL_SEND:-input}" >/dev/null 2>&1 ) &
exec wine lotrbfme2ep1.exe -win "$@" >"$LOG" 2>&1
