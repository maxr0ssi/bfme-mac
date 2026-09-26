#!/bin/zsh
# scripts/make-apps.sh — put "Battle for Middle-earth II.app" and "Rise of the Witch-king.app" in
# /Applications (or ~/Applications if that is not writable). Each is a plain macOS bundle whose
# launcher execs the play script from THIS checkout, so the apps always run whatever is committed
# here — nothing to rebuild after a pull. Re-run only if the repo moves or the icons change.
# Icons come from the games' own executables (tools/exe_icon.py).
#   scripts/make-apps.sh            build/refresh both apps
#   scripts/make-apps.sh --remove   delete them
set -e
export BFME_ROOT="${0:A:h:h}"
export WINE_BUILD="${WINE_BUILD:-w10}"
. "$BFME_ROOT/env.sh"
GAMES="$WINEPREFIX/drive_c/Program Files (x86)/Electronic Arts"

dest="/Applications"; [ -w "$dest" ] || dest="$HOME/Applications"
mkdir -p "$dest"

make_app() {  # make_app <App name> <play script> <exe for the icon> <bundle id suffix>
  local name="$1" play="$2" exe="$3" ident="$4"
  local app="$dest/$name.app"
  rm -rf "$app"
  # An AppleScript applet, not a bare shell-script bundle: macOS privacy protection (TCC) denies
  # a Finder-launched process every read under ~/Documents, where this checkout and the game
  # live, and only a real applet gets the "would like to access files in your Documents folder"
  # prompt. Allow it once per app. The play script is backgrounded so the applet exits at once;
  # its output goes to logs/app-<game>.log (Finder gives it no terminal).
  osacompile -o "$app" -e "do shell script \"mkdir -p '$BFME_ROOT/logs'; nohup '$BFME_ROOT/scripts/$play' >> '$BFME_ROOT/logs/app-$ident.log' 2>&1 &\""
  local plist="$app/Contents/Info.plist"
  setkey() { /usr/libexec/PlistBuddy -c "Delete :$1" "$plist" >/dev/null 2>&1 || true; /usr/libexec/PlistBuddy -c "Add :$1 string \"$2\"" "$plist" >/dev/null; }
  setkey CFBundleName "$name"
  setkey CFBundleDisplayName "$name"
  setkey CFBundleIdentifier "local.bfme-mac.$ident"
  setkey CFBundleVersion "$(git -C "$BFME_ROOT" rev-parse --short HEAD 2>/dev/null || echo 0)"
  setkey NSDocumentsFolderUsageDescription "The game, its Wine engine and this launcher live in Documents/BFME-MAC."
  # Icon: the exe's largest icon -> iconset at every size macOS wants -> the applet's .icns
  local tmp; tmp=$(mktemp -d)
  if python3 "$BFME_ROOT/tools/exe_icon.py" "$GAMES/$exe" "$tmp/src.png" >/dev/null 2>&1; then
    mkdir -p "$tmp/icon.iconset"
    for s in 16 32 128 256 512; do
      sips -z $s $s "$tmp/src.png" --out "$tmp/icon.iconset/icon_${s}x${s}.png" >/dev/null 2>&1
      sips -z $((s*2)) $((s*2)) "$tmp/src.png" --out "$tmp/icon.iconset/icon_${s}x${s}@2x.png" >/dev/null 2>&1
    done
    iconutil -c icns "$tmp/icon.iconset" -o "$app/Contents/Resources/applet.icns" 2>/dev/null || echo "  (iconutil failed; app keeps the applet icon)"
  else
    echo "  (no icon extracted from $exe; app keeps the applet icon)"
  fi
  rm -rf "$tmp"
  codesign --force --sign - --identifier "local.bfme-mac.$ident" "$app" >/dev/null 2>&1 || echo "  (codesign failed)"
  touch "$app"
  echo "made $app"
}

if [ "$1" = "--remove" ]; then
  # only apps that launch this checkout's scripts; another checkout's apps are left alone
  for app in "$dest/Battle for Middle-earth II.app" "$dest/Rise of the Witch-king.app"; do
    [ -d "$app" ] || continue
    if osadecompile "$app/Contents/Resources/Scripts/main.scpt" 2>/dev/null | grep -qF "'$BFME_ROOT/scripts/"; then
      rm -rf "$app"; echo "removed $app"
    else
      echo "left $app: it launches another checkout"
    fi
  done
  exit 0
fi
make_app "Battle for Middle-earth II" play-bfme2.sh "BFME2/lotrbfme2.exe" bfme2
make_app "Rise of the Witch-king"    play-rotwk.sh "RotWK/lotrbfme2ep1.exe" rotwk
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$dest/Battle for Middle-earth II.app" "$dest/Rise of the Witch-king.app" >/dev/null 2>&1 || true
echo "Launch from Launchpad/Spotlight or Finder > $dest. Logs still go to $BFME_ROOT/logs/."
