#!/bin/zsh
# retina.sh on|off — switch both games between the display's size in points (crisp UI; 1512x982
# on a 14" MacBook Pro) and full Retina (twice that, 3024x1964 there: 4x pixels, smaller text).
# Keeps Wine's RetinaMode and Options.ini in sync in every prefix that exists (w10 is what the play
# scripts use; the development machine also has stable), so the setting does not depend on which
# engine you launch with. BUILDS="w10" limits it.
export BFME_ROOT="${0:A:h:h}"
# the whole screen, a mode Wine offers: a resolution a few pixels short (the old 3024x1900) makes the
# Mac driver treat the window as not full-screen and keep the menu bar and Dock visible
pts=$(system_profiler SPDisplaysDataType 2>/dev/null | awk '/UI Looks like:/ {print $4, $6; exit}')
[[ "$pts" == <->' '<-> ]] || pts="1512 982"
case "$1" in
  on)  mode=y; res="$(( ${pts% *} * 2 )) $(( ${pts#* } * 2 ))";;
  off) mode=n; res="$pts";;
  *) echo "usage: retina.sh on|off"; exit 1;;
esac
for b in ${=BUILDS:-w10 stable}; do
  [[ -d "$BFME_ROOT/prefixes/$b" ]] || continue
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
