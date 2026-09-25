#!/bin/bash
# Configure, build and install a from-source WoW64 Wine on this Mac (Apple Silicon, host side
# x86_64 under Rosetta 2, PE side cross-compiled with mingw-w64). The why: patches/WINE-BUILD.md.
#
#   scripts/build-wine.sh <label> [extra configure args...]     configure + make + make install
#   CONFIGURE_ONLY=1 scripts/build-wine.sh <label> ...          stop after configure
#   WINE_SRC=<tree> MAKE_TARGETS="<targets>" scripts/build-wine.sh <label> ...
#   I386_CFLAGS="<flags>" overrides the compiler flags of 32-bit PE code (with MAKE_TARGETS)
#                    build other sources (e.g. a git worktree) and only the named targets, no install
#
# Builds out of tree in wine/build-<label>/, installs to engines/src-<label>/ (env.sh then
# resolves WINE_BUILD=src-<label>). The checkout in wine/src must already be on the commit you
# want: nothing is checked out here, so it is usable from `git bisect run`. Needs
# `brew install bison mingw-w64` and the x86_64 FreeType under build/deps-x86_64 (see the doc).

set -euo pipefail

LABEL="${1:?usage: build-wine.sh <label> [extra configure args]}"
shift || true

BFME_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WINE_SRC="${WINE_SRC:-$BFME_ROOT/wine/src}"
BUILD_DIR="$BFME_ROOT/wine/build-$LABEL"
PREFIX="$BFME_ROOT/engines/src-$LABEL"
DEPS="$BFME_ROOT/build/deps-x86_64"      # our own x86_64 freetype (see BUILD.md)

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

[ -e "$WINE_SRC/.git" ] || { echo "no Wine checkout at $WINE_SRC (git clone https://gitlab.winehq.org/wine/wine.git wine/src)"; exit 1; }
[ -f "$DEPS/lib/libfreetype.6.dylib" ] || { echo "no x86_64 FreeType under $DEPS — build it first (patches/WINE-BUILD.md, Host dependencies)"; exit 1; }

# Everything runs inside a Rosetta (x86_64) shell so that config.guess, the compiler default
# target and every configure test program are x86_64.  Tools invoked from here (bison, flex,
# mingw-w64 gcc, pkgconf) are arm64-native binaries; macOS happily exec()s those from an
# x86_64 process, and they are build tools whose own architecture is irrelevant.
arch -x86_64 /bin/bash -c '
set -euo pipefail

# bison 3.8 (keg-only) must win over /usr/bin/bison 2.3, which Wine rejects.
export PATH="/opt/homebrew/opt/bison/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Only our x86_64 deps are visible to pkg-config; without LIBDIR pinned, pkgconf would hand
# configure the arm64 Homebrew .pc files and the link would fail late and confusingly.
export PKG_CONFIG_LIBDIR="'"$DEPS"'/lib/pkgconfig"
export PKG_CONFIG_PATH="'"$DEPS"'/lib/pkgconfig"

export CC="clang -arch x86_64"
export CXX="clang++ -arch x86_64"
export CFLAGS="-arch x86_64 -O2 -g -mmacosx-version-min=11.0"
export CXXFLAGS="$CFLAGS"
export LDFLAGS="-arch x86_64 -mmacosx-version-min=11.0"
export CPPFLAGS="-I'"$DEPS"'/include"

# Baked into the generated Makefile so that a later bare `make` cannot fall back to
# /usr/bin/bison 2.3, which chokes on tools/widl/parser.y (`invalid directive: %code`).
# win32u dlopen()s FreeType by soname at runtime; configure would otherwise record the bare
# leaf name "libfreetype.6.dylib", which dyld cannot find outside its default search paths
# ("Wine cannot find the FreeType font library" on every start).  Pin the absolute path.
export ac_cv_lib_soname_freetype="'"$DEPS"'/lib/libfreetype.6.dylib"

export BISON="/opt/homebrew/opt/bison/bin/bison"
export FLEX="/usr/bin/flex"

"'"$WINE_SRC"'/configure" \
  --prefix="'"$PREFIX"'" \
  --build=x86_64-apple-darwin \
  --enable-archs=i386,x86_64 \
  --disable-winebth_sys \
  --without-alsa \
  --without-capi \
  --with-coreaudio \
  --with-cups \
  --without-dbus \
  --without-ffmpeg \
  --with-freetype \
  --with-gettext \
  --without-gettextpo \
  --without-gphoto \
  --without-gnutls \
  --without-gssapi \
  --without-gstreamer \
  --without-inotify \
  --without-krb5 \
  --without-netapi \
  --with-opencl \
  --without-opengl \
  --without-oss \
  --with-pcap \
  --without-pcsclite \
  --with-pthread \
  --without-pulse \
  --without-sane \
  --without-sdl \
  --without-udev \
  --without-usb \
  --without-v4l2 \
  --without-va \
  --without-vulkan \
  --without-wayland \
  --without-x \
  '"$*"'
'

[ -n "${CONFIGURE_ONLY:-}" ] && { echo "configured $BUILD_DIR (CONFIGURE_ONLY set)"; exit 0; }
# The generated Makefile has BISON baked in, but keep bison 3.8 first on PATH for build dirs
# configured by hand; /usr/bin/bison 2.3 dies on tools/widl/parser.y ("invalid directive: %code").
export PATH="/opt/homebrew/opt/bison/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
start=$(date +%s)
if [ -n "${MAKE_TARGETS:-}" ]; then
  arch -x86_64 make -j"$(sysctl -n hw.ncpu)" ${I386_CFLAGS:+"i386_CFLAGS=$I386_CFLAGS"} $MAKE_TARGETS
  echo "built $MAKE_TARGETS in $(( $(date +%s) - start )) s"; exit 0
fi
arch -x86_64 make -j"$(sysctl -n hw.ncpu)"
arch -x86_64 make install
echo "built and installed $PREFIX in $(( $(date +%s) - start )) s"
"$PREFIX/bin/wine" --version
[ -d "$PREFIX/lib/wine/i386-windows" ] && [ -d "$PREFIX/lib/wine/x86_64-windows" ] && echo "WoW64 layout ok" || { echo "WoW64 layout MISSING"; exit 1; }
