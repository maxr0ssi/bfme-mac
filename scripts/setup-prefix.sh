#!/bin/zsh
# scripts/setup-prefix.sh <build> — create prefixes/<build> for the Wine build under engines/<build>,
# symlinking the game folders from prefixes/stable so every prefix shares installs, saves and
# patches. Idempotent. Refuses to touch the primary (stable) prefix.
#   scripts/setup-prefix.sh w10      Sikarugir Wine 10.0 engine
#   scripts/setup-prefix.sh cx       CrossOver-derived engine
set -e
export BFME_ROOT="${0:A:h:h}"
. "$BFME_ROOT/scripts/lib.sh"
case "${1:-}" in -h|--help) usage ;; "") usage 1 ;; esac
export WINE_BUILD="$1"
. "$BFME_ROOT/env.sh"
[ "$WINEPREFIX" = "$BFME_ROOT/prefixes/stable" ] && { echo "refusing to rebuild the primary prefix"; exit 1; }
command -v wine >/dev/null || exit 1
echo "engine: $(command -v wine) ($(wine --version 2>/dev/null))"

wine wineboot -u >/dev/null 2>&1 || true
wine winecfg -v win10 >/dev/null 2>&1 || true
# Games: symlink the existing install so both prefixes share files, saves and patches.
mkdir -p "$WINEPREFIX/drive_c/Program Files (x86)"
[ -e "$WINEPREFIX/drive_c/Program Files (x86)/Electronic Arts" ] || \
  ln -s "$BFME_ROOT/prefixes/stable/drive_c/Program Files (x86)/Electronic Arts" "$WINEPREFIX/drive_c/Program Files (x86)/Electronic Arts"
# Registry + per-game settings.
wine regedit /S "$BFME_ROOT/config/bfme2.reg" >/dev/null 2>&1
wine regedit /S "$BFME_ROOT/config/rotwk.reg" >/dev/null 2>&1
for k in "The Battle for Middle-earth II" "The Lord of the Rings, The Rise of the Witch-king"; do
  wine reg add "HKLM\SOFTWARE\WOW6432Node\Electronic Arts\Electronic Arts\$k\ergc" /ve /t REG_SZ /d "$(LC_ALL=C tr -dc 'A-Z0-9' </dev/urandom | head -c 20)" /f >/dev/null 2>&1
done
wine reg add "HKCU\Software\Wine\WineDbg" /v ShowCrashDialog /t REG_DWORD /d 0 /f >/dev/null 2>&1
wine reg add "HKCU\Software\Wine\Direct3D" /v VideoMemorySize /t REG_SZ /d 4096 /f >/dev/null 2>&1
wine reg add "HKCU\Software\Wine\Mac Driver" /v UsePreciseScrolling /t REG_SZ /d n /f >/dev/null 2>&1
U="$WINEPREFIX/drive_c/users/$USER/AppData/Roaming"
for d in "My Battle for Middle-earth II Files" "My Rise of the Witch-king Files"; do
  mkdir -p "$U/$d"
  cp "$BFME_ROOT/prefixes/stable/drive_c/users/$USER/AppData/Roaming/$d/Options.ini" "$U/$d/Options.ini" 2>/dev/null || true
done
# DirectX 9 helper DLLs (the game imports d3dx9_27).
"$BFME_ROOT/downloads/winetricks" -q d3dx9 >/dev/null 2>&1 || echo "winetricks d3dx9 reported a problem (may be fine if the engine bundles d3dx9)"
# winetricks forces Microsoft's d3dx9 DLLs native. If scripts/wine-fixes.sh has installed the patched
# builtin d3dx9_27 in this engine, use that instead: Microsoft's is what makes the second half of the
# loading bar crawl (x87 texture code under Rosetta, docs/LOAD-TIME.md).
if [ -f "$(dirname "$(command -v wine)")/../lib/wine/i386-windows/d3dx9_27.dll.orig-$WINE_BUILD" ]; then
  wine reg add 'HKCU\Software\Wine\DllOverrides' /v '*d3dx9_27' /t REG_SZ /d builtin /f >/dev/null 2>&1
  echo "d3dx9_27: patched builtin (scripts/wine-fixes.sh)"
fi
ls "$WINEPREFIX/drive_c/windows/syswow64/d3dx9_27.dll" >/dev/null 2>&1 && echo "d3dx9_27 present" || echo "WARNING: d3dx9_27.dll missing in $WINEPREFIX"
echo "prefix ready: $WINEPREFIX"
