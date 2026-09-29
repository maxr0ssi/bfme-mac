#!/bin/sh
# Shared environment for the BFME-on-Mac setup. Source it before any wine command:
#   . "$BFME_ROOT/env.sh"            scripts set BFME_ROOT from their own location first
#   WINE_BUILD=w10 . ./env.sh        pick a build: engines/<build> + prefixes/<build>
BFME_ROOT="${BFME_ROOT:-$HOME/Documents/BFME-MAC}"
export BFME_ROOT
. "$BFME_ROOT/scripts/lib.sh"      # game_running, usage
# Not exported when unset: each launch script picks its own default (play-rotwk.sh needs w10).
_build="${WINE_BUILD:-stable}"

# engines/<build>/ may be a Gcenx .app's contents, a Sikarugir wswine.bundle, or a plain
# bin/lib tree (a self-built Wine); the first bin/wine found wins.
_engine="$BFME_ROOT/engines/$_build"
for _bin in "$_engine/bin" "$_engine/wswine.bundle/bin" "$_engine/Contents/Resources/wine/bin"; do
  if [ -x "$_bin/wine" ]; then export PATH="$_bin:$PATH"; break; fi
done
[ -x "$_bin/wine" ] || echo "env.sh: no wine binary under $_engine (WINE_BUILD=$_build)" >&2

case "$_build" in
  staging) export WINEPREFIX="$BFME_ROOT/prefixes/stable" ;;   # 11.17 shares the 11.0 prefix
  *)       export WINEPREFIX="$BFME_ROOT/prefixes/$_build" ;;
esac
case "$_build" in
  w10|cx)
    # Sikarugir/CrossOver engines dlopen() their support libs (FreeType, gnutls, MoltenVK...) by
    # name; they live in engines/ (symlinks) and the wrapper template's Frameworks.
    export DYLD_FALLBACK_LIBRARY_PATH="$BFME_ROOT/engines:$BFME_ROOT/engines/template/Template-1.0.18.app/Contents/Frameworks${DYLD_FALLBACK_LIBRARY_PATH:+:$DYLD_FALLBACK_LIBRARY_PATH}" ;;
esac
unset _engine _bin _build

# Silence Wine's debug spam; override with WINEDEBUG=warn+all when hunting a crash.
export WINEDEBUG="${WINEDEBUG:--all}"
# Keep Wine from showing its own "install Mono/Gecko?" dialogs; the game needs neither.
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-mscoree,mshtml=}"
