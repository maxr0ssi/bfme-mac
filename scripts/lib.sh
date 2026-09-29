#!/bin/sh
# Helpers shared by the scripts. env.sh sources this file; a script that does not need Wine
# sources it directly: . "$BFME_ROOT/scripts/lib.sh". POSIX sh, so zsh, bash and sh can source it.

# The running script's path, taken the first time it sources this file (before it can cd), for
# usage. ZSH_ARGZERO: in zsh, $0 is the sourced file's or the function's name, not the script's.
if [ -z "${BFME_SELF:-}" ]; then
  BFME_SELF="${ZSH_ARGZERO:-$0}"
  case "$BFME_SELF" in /*) ;; *) BFME_SELF="$PWD/$BFME_SELF" ;; esac
fi

# A running BFME2 or RotWK: both are started with -win, and BFME2's lotrbfme2.exe hands over to
# game.dat. pgrep leaves itself out, and the pattern does not match its own text, so one
# script's check never sees another's.
BFME_GAME_RE='(lotrbfme2(ep1)?\.exe|game\.dat) -win'
game_running() { pgrep -f "$BFME_GAME_RE" >/dev/null; }

# usage [status]: print the script's header (the comment lines after the shebang, without the
# leading "# ") and exit with status, default 0; on stderr when status is not 0.
usage() {
  if [ "${1:-0}" -eq 0 ]; then _bfme_header; else _bfme_header >&2; fi
  exit "${1:-0}"
}
_bfme_header() { awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$BFME_SELF"; }
