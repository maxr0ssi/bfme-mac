#!/bin/zsh
# Install (or remove) the NX_COMPAT-flagged copies of every native module the games load.
# Wine's loader re-enables "force all memory executable" for each module lacking the flag
# (dlls/ntdll/loader.c alloc_module), and RWX pages are where Rosetta hands Wine bogus faults.
#   patches/nxcompat/install.sh install   # backs up originals as <file>.preNX.bak, copies flagged files in
#   patches/nxcompat/install.sh revert    # restores the .preNX.bak originals
# Result: no difference (the fault is a WoW64 mode-switch bug, see patches/WINE-BUG-REPORT.md).
set -e
cd "${0:A:h:h:h}"   # repo root; the file names under all/ encode paths relative to it ("__" = "/")
pgrep -f 'lotrbfme2ep1|lotrbfme2.exe|game.dat' >/dev/null && { echo "a game is running; stop it first"; exit 1; }
case "$1" in
  install)
    n=0
    for f in patches/nxcompat/all/*; do
      dest="${${f:t}//__//}"            # "prefixes__stable__drive_c__..." -> "prefixes/stable/drive_c/..."
      [ -f "$dest" ] || { echo "skip (missing): $dest"; continue; }
      [ -f "$dest.preNX.bak" ] || cp "$dest" "$dest.preNX.bak"
      cp "$f" "$dest"; n=$((n+1))
    done
    echo "installed $n NX-compatible modules"
    ;;
  revert)
    n=0
    # zsh recursive glob, not $(find ...): the game paths contain spaces ("Program Files (x86)"),
    # which command substitution would split into unusable words. (N) = no error when none are left.
    for b in prefixes/stable/**/*.preNX.bak(N); do mv "$b" "${b%.preNX.bak}"; n=$((n+1)); done
    echo "reverted $n modules"
    ;;
  *) echo "usage: $0 install|revert"; exit 1;;
esac
