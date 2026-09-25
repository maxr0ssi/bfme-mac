#!/bin/zsh
# scripts/d3dx9-fix.sh [--revert] — kept for the docs that name it: our Wine fixes (the d3dx9 loading
# fix among them) are built and installed together by scripts/wine-fixes.sh now.
exec "${0:A:h}/wine-fixes.sh" "$@"
