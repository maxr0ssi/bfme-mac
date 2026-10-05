#!/bin/zsh
# scripts/game-patch.sh [--revert | --test | --status | --bundle]
# Game-side performance patch for Rise of the Witch-king 2.02 (gamepatch/): builds the proxy
# dinput8.dll, checks that every patch matches the installed lotrbfme2ep1.exe, and copies the DLL
# and gamepatch.ini into the RotWK folder. scripts/play-rotwk.sh loads it (dinput8=n,b) whenever
# gamepatch.ini is there and sends its log to logs/gamepatch.log. The exe on disk is never changed.
#   (no option)  build, check, install
#   --revert     remove the DLL and gamepatch.ini (a dinput8.dll that was there before comes back
#                from dinput8.dll.orig)
#   --test       build and run every standalone test (bit-exactness etc.) in a throwaway prefix,
#                results in logs/gamepatch/ (the full inverse-sqrt, particle-colour and logic-math
#                tests take ~5 min each on all cores)
#   --status     what is installed
#   --bundle     build/gamepatch/bundle/: the two files a friend drops into their RotWK folder
set -eu
export BFME_ROOT="${0:A:h:h}" WINE_BUILD="${WINE_BUILD:-w10}"
. "$BFME_ROOT/env.sh"
GAMEDIR="$WINEPREFIX/drive_c/Program Files (x86)/Electronic Arts/RotWK"
OUT="$BFME_ROOT/build/gamepatch"
DLL="$GAMEDIR/dinput8.dll"; INI="$GAMEDIR/gamepatch.ini"
winpath() { print -r -- "Z:${1//\//\\}"; }
ours() { [[ -f "$DLL" ]] && grep -aq "gamepatch proxy dinput8.dll for RotWK" "$DLL"; }
build() { make -s -C "$BFME_ROOT/gamepatch" MINGW="${MINGW:-/opt/homebrew/bin/i686-w64-mingw32-gcc}"; }

case "${1:-}" in
--status)
  if ours; then echo "installed: $DLL"; grep -v '^;' "$INI" 2>/dev/null | sed 's/ *;.*//' | grep . ; else echo "not installed"; fi
  [[ -f "$BFME_ROOT/logs/gamepatch.log" ]] && { echo "last log lines:"; tail -12 "$BFME_ROOT/logs/gamepatch.log"; }
  exit 0 ;;
--revert)
  game_running && { echo "the game is running; quit it first"; exit 1; }
  if [[ -f "$DLL" ]] && ! ours; then echo "$DLL is not gamepatch's; left alone"; exit 1; fi
  rm -f "$DLL" "$INI"
  [[ -f "$DLL.orig" ]] && mv "$DLL.orig" "$DLL" && echo "restored the previous dinput8.dll"
  echo "gamepatch removed; the game runs unmodified (play-rotwk.sh no longer loads a native dinput8)"
  exit 0 ;;
--test)
  build
  export WINEPREFIX="$OUT/prefix" WINEDEBUG=-all
  [[ -d "$WINEPREFIX/drive_c" ]] || { echo "creating the test prefix $WINEPREFIX"; wine wineboot -i >/dev/null 2>&1; }
  mkdir -p "$BFME_ROOT/logs/gamepatch"
  EXE="$(winpath "$GAMEDIR/lotrbfme2ep1.exe")"
  st=0
  # (wine's output goes to a file, not a pipe: the prefix's background services inherit a pipe
  # and keep it open, so a reader would never see EOF)
  L="$BFME_ROOT/logs/gamepatch"
  runt() {  # runt <label> <exe> [args]: run one test, keep its output, print its verdict
    local label=$1; shift
    wine "$@" > "$L/$label.raw" 2>&1 || true
    grep -v 'mvk-info\|VK_\|^	' "$L/$label.raw" > "$L/$label.txt"; rm -f "$L/$label.raw"
    local r=$(tail -1 "$L/$label.txt"); r=${r%$'\r'}; echo "$label: $r"; [[ "$r" == PASS ]]   # Wine writes CRLF
  }
  for t in t_regs t_misc t_dxlock t_quat t_hittest t_invsqrt t_shadow t_perf t_particle t_anim t_adecode t_rstats t_pstats t_monitor t_logic t_ftol2 t_lstats; do
    runt $t "$OUT/$t.exe" "$EXE" || st=1
  done
  WINEDLLOVERRIDES="mscoree,mshtml=;dinput8=n,b" runt t_attach "$OUT/t_attach.exe" \
      "$(winpath "$OUT/proxytest/dinput8.dll")" "$(winpath "$L/t_attach-gamepatch.log")" || st=1
  WINEDLLOVERRIDES="mscoree,mshtml=;dinput8=n,b" runt t_highmem "$OUT/t_highmem.exe" \
      "$(winpath "$OUT/proxytest/dinput8.dll")" "$(winpath "$L/t_highmem-gamepatch.log")" || st=1
  ( cd "$OUT/proxytest" && GAMEPATCH_LOG="$(winpath "$L/t_proxy-gamepatch.log")" \
      WINEDLLOVERRIDES="mscoree,mshtml=;dinput8=n,b" runt t_proxy ./t_proxy.exe ) || st=1
  wineserver -k 2>/dev/null || true   # harness-allow: the throwaway test prefix's server, no game there
  sleep 2                             # msync needs a server started with it
  WINEMSYNC=1 runt t_dxlock-msync "$OUT/t_dxlock.exe" "$EXE" || st=1
  wineserver -k 2>/dev/null || true   # harness-allow: the throwaway test prefix's server, no game there
  exit $st ;;
--bundle)
  build
  mkdir -p "$OUT/bundle"; cp "$OUT/dinput8.dll" "$BFME_ROOT/gamepatch/gamepatch.ini" "$OUT/bundle/"
  echo "friends: copy $OUT/bundle/{dinput8.dll,gamepatch.ini} into the RotWK 2.02 folder (Windows: nothing"
  echo "else; Wine/Mac: also WINEDLLOVERRIDES=dinput8=n,b). Log: gamepatch.log next to the DLL."
  exit 0 ;;
-h|--help) usage ;;
"") ;;
*) usage 2 ;;
esac

game_running && { echo "the game is running; quit it first"; exit 1; }
[[ -f "$GAMEDIR/lotrbfme2ep1.exe" ]] || { echo "no RotWK in $GAMEDIR"; exit 1; }
build
# Every patch checks its bytes again at game start; checking here too means an unexpected exe is
# reported now rather than as "patch skipped" lines in the log.
EXE="$(winpath "$GAMEDIR/lotrbfme2ep1.exe")"
WINEDEBUG=-all wine "$OUT/t_misc.exe" "$EXE" sites > "$OUT/sites.txt" 2>&1 || true
chk=$(grep '^\[1\]' "$OUT/sites.txt" || true)
echo "${chk:-byte check did not run}"
[[ "$chk" == *"8 of 8"* ]] || { echo "not installing: the exe does not match every patch"; exit 1; }
if [[ -f "$DLL" ]] && ! ours; then cp -p "$DLL" "$DLL.orig"; echo "kept the existing dinput8.dll as dinput8.dll.orig"; fi
cp "$OUT/dinput8.dll" "$DLL"
[[ -f "$INI" ]] || cp "$BFME_ROOT/gamepatch/gamepatch.ini" "$INI"
echo "installed $DLL (+ gamepatch.ini). Start the game with scripts/play-rotwk.sh; log: logs/gamepatch.log"
