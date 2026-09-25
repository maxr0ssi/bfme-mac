#!/bin/zsh
# test-skirmish.sh [label] [-- extra game args]
#
# Hands-free harness for bisecting the "hang after loading" bug: kills any running RotWK, launches
# it via play-rotwk.sh (any WINEDEBUG / WINE_BUILD / other env vars set by the caller pass
# through; arguments after "--" are appended to the game command line), drives the menus with
# ahk/autoskirmish.ahk, then polls every 20 s (CPU + window capture classified by
# classify-capture.py) for up to 8 minutes and prints exactly one of
#   RESULT: MAP_RENDERED      the 3D map + HUD appeared (game is left running)
#   RESULT: HANG_AFTER_LOAD   loading UI vanished / window went dark and CPU dropped (game killed)
#   RESULT: CRASHED           process gone or a new DUMP_*.dmp appeared (game killed)
#   RESULT: TIMEOUT           nothing conclusive within the limit (game killed)
# Captures: logs/skirmish-<label>-*.png; log: logs/skirmish-<label>.log
set -u
export BFME_ROOT="${0:A:h:h}"
BFME="$BFME_ROOT"
# Default WINEDEBUG: trace-level seh so the main thread's access violation at the load->play
# transition is logged with its fault address/registers (see report_exception). The fault address
# is also read from any DUMP_*.dmp the game writes (tools/parse_minidump.py). Caller's WINEDEBUG
# always wins. NOTE: starting another Wine process (AutoHotkey) in the prefix during the game's
# first ~8 s made the game crash at +7 s (AV at 7BF2123D in ntdll reading 0x4DC9) in 3/3 tries,
# hence AHK_DELAY below.
export WINEDEBUG="${WINEDEBUG:-warn+d3d,+seh,err+all}"
# GAME=rotwk (default) or GAME=bfme2: which game to launch/drive. Both games play on the w10
# engine (each play-*.sh's default); the harness must source env.sh with the same build so that
# WINEPREFIX (dump dir, wineserver -k) matches the game it drives. WINE_BUILD=stable still overrides.
GAME=${GAME:-rotwk}
export WINE_BUILD="${WINE_BUILD:-w10}"
. "$BFME/env.sh"
case "$GAME" in
  rotwk) PLAY="$BFME/scripts/play-rotwk.sh"; GAMEDIR="$WINEPREFIX/drive_c/Program Files (x86)/Electronic Arts/RotWK"
         PROC_RE='lotrbfme2ep1.exe -win'; KILL_RE='lotrbfme2ep1'; WIN_RE='Witch' ;;
  bfme2) PLAY="$BFME/scripts/play-bfme2.sh";  GAMEDIR="$WINEPREFIX/drive_c/Program Files (x86)/Electronic Arts/BFME2"
         # lotrbfme2.exe spawns "game.dat -win"; match either. Window title has no "Witch-king".
         PROC_RE='(lotrbfme2\.exe|game\.dat) -win'; KILL_RE='lotrbfme2\.exe|game\.dat'; WIN_RE='Middle-earth' ;;
  *) echo "unknown GAME=$GAME (rotwk|bfme2)"; exit 2 ;;
esac
LOGDIR="$BFME/logs"; mkdir -p "$LOGDIR"
CLASSIFY="$BFME/tools/classify-capture.py"
[[ -n "${DRY_RUN:-}" ]] && { echo "GAME=$GAME WINE_BUILD=$WINE_BUILD WINEPREFIX=$WINEPREFIX PLAY=$PLAY wine=$(command -v wine)"; exit 0; }
# Window lister (tools/lswin.swift), compiled on first use into build/.
LSWIN="${LSWIN:-$BFME/build/lswin}"
[[ -x "$LSWIN" ]] || { mkdir -p "$BFME/build"; swiftc -O -o "$LSWIN" "$BFME/tools/lswin.swift" || { echo "cannot build lswin (needs the Xcode command-line tools)"; exit 2; }; }
# The resident AutoHotkey helper must not emulate edge scrolling while autoskirmish.ahk drives
# the menus (a parked cursor at a screen edge would hold arrow keys down).
export EDGESCROLL=off

LABEL=""
if [[ $# -gt 0 && "$1" != "--" ]]; then LABEL="$1"; shift; fi
[[ "${1:-}" == "--" ]] && shift
[[ -z "$LABEL" ]] && LABEL="$(date +%Y%m%d-%H%M%S)"
EXTRA_ARGS=("$@")

POLL=${POLL:-20}          # seconds between polls (5 for finer load-time measurements)
MAX_SECS=${MAX_SECS:-660}  # give up after this long on the loading screen (BFME2 on w10: ~490 s)
HANG_SECS=${HANG_SECS:-80} # dark screen without loading UI for this long = hang
IDLE_SECS=${IDLE_SECS:-40} # ...or with idle CPU for this long
LOW_CPU=${LOW_CPU:-50}     # % below which the loader is considered idle
# Thresholds are in seconds so that changing POLL does not change what counts as a hang.
MAX_POLLS=$(( MAX_SECS / POLL )); HANG_POLLS=$(( (HANG_SECS + POLL - 1) / POLL )); IDLE_POLLS=$(( (IDLE_SECS + POLL - 1) / POLL ))
AHK_DELAY=${AHK_DELAY:-12} # seconds after launch before AutoHotkey is started in the prefix
KEEP_ON_HANG=${KEEP_ON_HANG:-0} # 1 = leave the hung process alive (for live memory inspection)
# Menu timing (ms) handed to autoskirmish.ahk: wait before the first Esc, wait for the main menu.
# Engine-level, not per-game: the w10 engine starts the intro movie ~20 s later than 11.0 and its
# splash lasts ~50 s (measured on RotWK). BFME2 was still on the intro at +133 s with one Esc
# burst at preEsc, so autoskirmish.ahk now keeps tapping Esc through the first half of MENU_WAIT
# rather than these values being raised; the poll loop also re-clicks up to 3 times.
case "$WINE_BUILD" in
  w10) PRE_ESC=${PRE_ESC:-48000}; MENU_WAIT=${MENU_WAIT:-55000} ;;
  *)   PRE_ESC=${PRE_ESC:-6000};  MENU_WAIT=${MENU_WAIT:-20000} ;;
esac

T0=$(date +%s)
LOG="$LOGDIR/skirmish-$LABEL.log"
: > "$LOG"
log() { local m="$(date +%H:%M:%S) [+$(( $(date +%s) - T0 ))s] $*"; echo "$m"; echo "$m" >> "$LOG"; }

kill_game() {
  pkill -f "$KILL_RE" 2>/dev/null; pkill -f AutoHotkey 2>/dev/null
  sleep 1; wineserver -k 2>/dev/null
  # let the prefix settle: wineserver/start.exe must be gone before relaunching
  for _ in 1 2 3 4 5 6 7 8 9 10; do pgrep -f "wineserver|$KILL_RE" >/dev/null || break; sleep 1; done
  sleep 2
}
game_pid() { pgrep -f "$PROC_RE" | head -1; }
# Sum over every matching pid: BFME2's lotrbfme2.exe is an idle launcher stub, game.dat does the work.
game_cpu() { local t=0 c; for p in $(pgrep -f "$PROC_RE"); do c=$(ps -o %cpu= -p "$p" | tr -d ' '); t=$(( t + ${c%.*} )); done; echo "$t"; }
win_id() { "$LSWIN" 2>/dev/null | grep -i "$WIN_RE" | head -1 | sed -E 's/.*id=([0-9]+).*/\1/'; }
capture() {  # capture <name> -> prints class; saves logs/skirmish-LABEL-<name>.png
  local id out; id=$(win_id); out="$LOGDIR/skirmish-$LABEL-$1.png"
  if [[ -z "$id" ]]; then echo NOWINDOW; return; fi
  if ! screencapture -x -l "$id" "$out" 2>/dev/null; then echo NOWINDOW; return; fi
  python3 "$CLASSIFY" "$out" 2>/dev/null || echo UNKNOWN
}
new_dumps() { local f; for f in "$GAMEDIR"/DUMP_*.dmp(N); do [[ "$f" -nt "$STAMP" ]] && echo "$f"; done; }
ahk() { ( cd "$BFME/ahk" && wine AutoHotkeyU32.exe "$@" 2>/dev/null ); }

report_exception() {
  # 1) any new minidump: exception code / fault address via tools/parse_minidump.py
  local d
  new_dumps | while IFS= read -r d; do
    log "minidump $d:"; python3 "$BFME/tools/parse_minidump.py" "$d" 2>&1 | tee -a "$LOG"
  done
  # 2) game log: first trace:seh:dispatch_exception with code=c0000005 raised by the main thread
  #    (the lowest game thread id seen raising one) plus the register-dump lines that follow it;
  #    with warn+seh only the per-thread "EXCEPTION_ACCESS_VIOLATION ... raised" lines exist.
  local glog="$GAMELOG"
  [[ -f "$glog" ]] || { log "no game log to scan for exceptions"; return; }
  local tid
  tid=$(grep -E '^[0-9a-f]{4}:trace:seh:dispatch_exception code=c0000005' "$glog" | cut -d: -f1 | sort | head -1)
  if [[ -z "$tid" ]]; then
    log "no trace:seh access violation in $glog; warn:seh access violations per thread:"
    grep 'warn:seh:dispatch_exception EXCEPTION_ACCESS_VIOLATION' "$glog" | cut -d: -f1 | sort | uniq -c | tee -a "$LOG"
    grep -n -m1 -B2 -A3 -E 'MiniDumpWriteDump|stack overflow' "$glog" | tee -a "$LOG"
    return
  fi
  local n_av; n_av=$(grep -c -E "^${tid}:trace:seh:dispatch_exception code=c0000005" "$glog")
  log "main thread tid ${tid}: ${n_av} access violation(s); first one in $glog:"
  grep -n -m1 -A7 -E "^${tid}:trace:seh:dispatch_exception code=c0000005" "$glog" | tee -a "$LOG"
  if [[ "$n_av" -gt 1 ]]; then
    # The game catches some AVs itself during normal loading; the last one is the fatal one.
    local last; last=$(grep -n -E "^${tid}:trace:seh:dispatch_exception code=c0000005" "$glog" | tail -1 | cut -d: -f1)
    log "last main-thread access violation (line $last):"
    sed -n "${last},$(( last + 7 ))p" "$glog" | tee -a "$LOG"
  fi
  grep -n -m3 -E 'MiniDumpWriteDump|faultrep:ReportFault|stack overflow' "$glog" | tee -a "$LOG"
}

finish() {  # finish <RESULT> <detail>
  local r="$1"; shift
  log "RESULT: $r $*"
  echo "RESULT: $r"
  [[ "$r" == "HANG_AFTER_LOAD" || "$r" == "CRASHED" ]] && report_exception
  if [[ "$r" == "MAP_RENDERED" || ( "$r" == "HANG_AFTER_LOAD" && "$KEEP_ON_HANG" == "1" ) ]]; then
    log "game left running (pid $(game_pid)) — edge scrolling is OFF in harness-launched games; press Ctrl+Option+E in the game to turn it on"
  else
    kill_game; log "game killed"
  fi
  rm -f "$STAMP"
  exit 0
}

# --- launch -------------------------------------------------------------------------------
# Never take down someone's match: refuse to start while any game process exists unless the
# caller says FORCE=1 (the harness's own kill_game below is what stops the previous run).
if pgrep -f '(lotrbfme2(ep1)?\.exe|game\.dat) -win' >/dev/null && [[ "${FORCE:-0}" != "1" ]]; then
  echo "a game is already running; quit it (or FORCE=1 to kill it) before a hands-free run"; exit 3
fi
log "label=$LABEL GAME=$GAME WINEDEBUG=${WINEDEBUG:-} WINE_BUILD=$WINE_BUILD extra_args=(${EXTRA_ARGS[*]:-})"
kill_game
STAMP="$LOGDIR/.skirmish-$LABEL.stamp"; touch "$STAMP"
nohup "$PLAY" "${EXTRA_ARGS[@]}" > "$LOGDIR/skirmish-$LABEL-launch.out" 2>&1 &
sleep 2
GAMELOG=$(grep -m1 '^log:' "$LOGDIR/skirmish-$LABEL-launch.out" 2>/dev/null | cut -d' ' -f2-)
log "launched (game pid $(game_pid)); game log: $GAMELOG"

# --- menus --------------------------------------------------------------------------------
sleep "$AHK_DELAY"
if [[ -z "$(game_pid)" ]]; then finish CRASHED "process gone within ${AHK_DELAY}s of launch"; fi
ahk autoskirmish.ahk full "$GAME" "$PRE_ESC" "$MENU_WAIT" | tee -a "$LOG"
sleep 3
cls=$(capture "00-after-menus")
log "after autoskirmish: $cls"
# If a click did not land (human moved the mouse, menu came late), retry the click sequence.
tries=0
while [[ "$cls" != "LOADING" && $tries -lt 3 ]]; do
  tries=$((tries + 1))
  if [[ -z "$(game_pid)" ]]; then finish CRASHED "process gone during menu navigation"; fi
  case "$cls" in
    MENU)  log "retry $tries: main menu/setup still showing, re-clicking"; ahk autoskirmish.ahk clicks "$GAME" | tee -a "$LOG" ;;
    MOVIE) log "retry $tries: movie still playing, Esc + clicks"; ahk autoskirmish.ahk skip "$GAME" | tee -a "$LOG"; sleep 20; ahk autoskirmish.ahk clicks "$GAME" | tee -a "$LOG" ;;
    *)     log "retry $tries: screen is $cls, waiting 15 s then re-clicking"; sleep 15; ahk autoskirmish.ahk clicks "$GAME" | tee -a "$LOG" ;;
  esac
  sleep 4
  cls=$(capture "00-retry$tries")
  log "after retry $tries: $cls"
done
T_START=$(date +%s)
if [[ "$cls" == "LOADING" ]]; then
  log "loading screen reached (+$(( T_START - T0 ))s after launch)"
else
  log "WARNING: loading screen not confirmed (last screen: $cls); polling anyway"
fi

# --- poll ---------------------------------------------------------------------------------
seen_loading=0; [[ "$cls" == "LOADING" ]] && seen_loading=1
hang_polls=0; hang_lowcpu=0; last=""
for ((i = 1; i <= MAX_POLLS; i++)); do
  sleep "$POLL"
  if [[ -z "$(game_pid)" ]]; then finish CRASHED "process exited (poll $i)"; fi
  d=$(new_dumps); if [[ -n "$d" ]]; then log "new dump: $d"; finish CRASHED "minidump $d"; fi
  cpu=$(game_cpu)
  cls=$(capture "$(printf '%02d' "$i")")
  log "poll $i: cpu=${cpu}% screen=$cls"
  case "$cls" in
    LOADING) seen_loading=1; hang_polls=0; hang_lowcpu=0 ;;
    MAP)
      sleep 5; cls2=$(capture "$(printf '%02d' "$i")-confirm")
      log "map confirm: $cls2"
      [[ "$cls2" == "MAP" ]] && finish MAP_RENDERED "after $(( $(date +%s) - T_START ))s"
      hang_polls=0 ;;
    HANGBG|UNKNOWN|NOWINDOW)
      hang_polls=$((hang_polls + 1))
      [[ "${cpu%.*}" -lt $LOW_CPU ]] && hang_lowcpu=$((hang_lowcpu + 1)) || hang_lowcpu=0
      # Hang = dark screen without loading UI, either with idle CPU for IDLE_SECS or persisting
      # HANG_SECS. (The game's own pause menu classifies UNKNOWN too: a stray Esc as the map
      # appears looks like a hang for HANG_SECS, so check the captures before believing one.)
      if [[ $seen_loading -eq 1 && ( $hang_lowcpu -ge $IDLE_POLLS || $hang_polls -ge $HANG_POLLS ) ]]; then
        finish HANG_AFTER_LOAD "loading UI gone for ${hang_polls} polls, cpu=${cpu}%, $(( $(date +%s) - T_START ))s after start"
      fi ;;
    *) hang_polls=0 ;;
  esac
  last="$cls"
done
finish TIMEOUT "last screen=$last seen_loading=$seen_loading"
