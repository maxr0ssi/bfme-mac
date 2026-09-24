#!/bin/zsh
# retina.sh on|off — switch both games between native points (1512x982, crisp UI) and
# full Retina (3024x1964, 4x pixels, smaller text). Keeps Wine's RetinaMode and Options.ini in
# sync in every prefix that has a game (w10 is what the play scripts use; stable is the 11.0
# spare), so the setting does not depend on which engine you launch with. BUILDS="w10" limits it.
export BFME_ROOT="${0:A:h:h}"
case "$1" in
  # 3024x1964 is the whole screen, a mode Wine offers; the old 3024x1900 was 64 px short, so the
  # Mac driver no longer saw a full-screen window and kept the menu bar and Dock visible.
  on)  mode=y; res="3024 1964";;
  off) mode=n; res="1512 982";;
  *) echo "usage: retina.sh on|off"; exit 1;;
esac
for b in ${=BUILDS:-w10 stable}; do
  (
    export WINE_BUILD=$b
    . "$BFME_ROOT/env.sh"
    wine reg add "HKCU\Software\Wine\Mac Driver" /v RetinaMode /t REG_SZ /d $mode /f >/dev/null 2>&1
    for d in "My Battle for Middle-earth II Files" "My Rise of the Witch-king Files"; do
      f="$WINEPREFIX/drive_c/users/$USER/AppData/Roaming/$d/Options.ini"
      [ -f "$f" ] && { chmod u+w "$f"; sed -i '' "s/^Resolution = .*/Resolution = $res/" "$f"; }
    done
    wineserver -w
    echo "$b: RetinaMode=$mode, Resolution = $res"
  )
done
