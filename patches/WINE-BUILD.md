# Building Wine from source on this Mac

A from-source WoW64 Wine for the d3d9 test suite and the Wine bug work (wine-11.0 built this way
installs to `engines/src-11.0`, ~11 min at -j16). The shipped fixes are built by
`scripts/wine-fixes.sh` on wine-10.0 (worktree `wine/src-d3dx10`, branch `bfme-fixes-10.0`) with the
same toolchain.

```
wine/src/              git clone of gitlab.winehq.org/wine/wine.git (full history, ~900 MB)
scripts/build-wine.sh  configure + make + install wrapper — this is the reproducible build recipe
wine/build-<label>/    out-of-tree build dir
engines/src-<label>/   install prefix; env.sh finds engines/<name>/bin/wine, so
                       WINE_BUILD=src-11.0 selects it
build/deps-x86_64/     our own x86_64 FreeType (see "Host dependencies")
build/deps-src/        source tarballs for the above
```

## The shape of the problem

Wine here must run 32-bit Windows code, so the **host** side (the Unix `wine` binary and the
`*.so` unixlibs) has to be **x86_64 Mach-O**, executed under Rosetta 2 — an arm64 host build
cannot load an i386 PE process. The **PE** side (the Windows DLLs) is cross-compiled and its
toolchain's own architecture is irrelevant.

So: host = `clang -arch x86_64`, everything run inside `arch -x86_64 /bin/bash` so that
`config.guess`, the compiler default target and every configure test program are x86_64 and can
still be *executed* (Rosetta) — which keeps `cross_compiling=no` and lets configure's run-tests work.
Build tools invoked from that shell (bison, flex, `*-w64-mingw32-gcc`, pkgconf) are arm64-native
Homebrew binaries; macOS exec()s those from an x86_64 process without complaint.

## Toolchain installed

| Need | Where it came from |
|---|---|
| Xcode CLT / Apple clang 17 | already present (`/Applications/Xcode.app`), universal, `-arch x86_64` works |
| Rosetta 2 | already present |
| bison ≥ 3.0 | `brew install bison` — **keg-only**, so `/opt/homebrew/opt/bison/bin` must come first in PATH; `/usr/bin/bison` is 2.3 and Wine rejects it |
| flex | `/usr/bin/flex` 2.6.4 (system), fine |
| pkg-config | `/opt/homebrew/bin/pkg-config` (pkgconf), fine |
| mingw-w64 14.0.0 | `brew install mingw-w64` — gives both `i686-w64-mingw32-gcc` and `x86_64-w64-mingw32-gcc`, which is exactly what `--enable-archs=i386,x86_64` needs |

`brew install bison mingw-w64` is the whole install step (arm64 Homebrew at `/opt/homebrew`).

## Host dependencies — what we have and what we dropped

Gcenx's reference builds (github.com/Gcenx/macOS_Wine_builds) take their x86_64 host libraries from
MacPorts plus a custom overlay; the equivalent here would be a **second, x86_64 Homebrew at
`/usr/local`**. That is not installed on this machine, and installing it needs `sudo`.

Instead only the one library the game actually needs is built from source, x86_64, into
`build/deps-x86_64`:

```sh
# FreeType 2.13.3 — needed for text rendering; without it the game has no fonts.
cd build/deps-src && curl -LO https://download.savannah.gnu.org/releases/freetype/freetype-2.13.3.tar.xz
tar xf freetype-2.13.3.tar.xz && cd freetype-2.13.3
arch -x86_64 /bin/bash -c '
  export PKG_CONFIG_LIBDIR=/nonexistent
  export CC="clang -arch x86_64"
  export CFLAGS="-arch x86_64 -O2 -mmacosx-version-min=11.0"
  export LDFLAGS="-arch x86_64 -mmacosx-version-min=11.0"
  ./configure --prefix=$BFME_ROOT/build/deps-x86_64 --build=x86_64-apple-darwin \
    --enable-shared --enable-static \
    --with-zlib=yes --with-bzip2=no --with-png=no --with-harfbuzz=no --with-brotli=no
  make -j4 && make install'
```

**It must be a shared library.** Wine's configure links a test program and then inspects it with
`otool -L` for a dylib install name (`checking for -lfreetype ... libfreetype.6.dylib`); a
static-only `libfreetype.a` links fine but reports *not found* and configure aborts with
"FreeType 64-bit development files not found".

**And the soname must be pinned to an absolute path.** `win32u` does not link FreeType, it
`dlopen()`s it at runtime using the string configure captured above — a bare leaf name. dyld only
searches its default paths for a leaf name, our deps dir is not one of them, and every single
`wine` invocation prints *"Wine cannot find the FreeType font library"* and runs with no TrueType
fonts. The build looks completely successful; only the smoke test catches it. `scripts/build-wine.sh`
therefore presets the configure cache variable:

```sh
export ac_cv_lib_soname_freetype="$BFME_ROOT/build/deps-x86_64/lib/libfreetype.6.dylib"
```

which lands in `include/config.h` as `SONAME_LIBFREETYPE`. Consequence: **`engines/src-*` depends on
`build/deps-x86_64` staying where it is.** If that tree is ever moved or wiped, rebuild FreeType
there and re-run configure + `make`.

`PKG_CONFIG_LIBDIR` is pinned to `build/deps-x86_64/lib/pkgconfig` for the same reason in reverse:
left at its default, pkgconf hands configure the **arm64** Homebrew `.pc` files and the link fails
much later and far less legibly.

Dropped relative to Gcenx, because no x86_64 build of them exists here — none is needed by
BFME2/RotWK, and each is a one-line change if that turns out to be wrong:

| Dropped | Consequence |
|---|---|
| `gnutls` | no TLS in `bcrypt`/`secur32`. The games never use it. |
| `gstreamer`, `ffmpeg` | no video playback (Bink/VP6 intro movies). `Esc` skips the intro anyway. |
| `sdl2` | no gamepad. Mouse+keyboard only, which is what these games use. |
| `vulkan` / MoltenVK | no Vulkan. We render through **wined3d → OpenGL**; DXVK already renders black here (`scripts/play-bfme2-dxvk.sh`). |
| `pcsclite` | no smartcards. Also fails to configure: the MacPorts `libpcsclite` Gcenx uses is absent. |
| `inotify` | no `libinotify`; directory-change notifications fall back to polling. |

Kept from Gcenx because they resolve to macOS SDK frameworks or system libs, which are universal:
`--with-coreaudio --with-cups --with-opencl --with-pcap --with-pthread`.

`--without-opengl` is kept **exactly as Gcenx has it** and is not a mistake: that option controls the
Unix-side `libGL`/EGL used by the X11 and Wayland drivers. On macOS `winemac.drv` talks to
`OpenGL.framework` directly, and this is the configuration the working Gcenx 11.0 engine in
`engines/stable` is built with.

## The configure line

Driven by `scripts/build-wine.sh <label> [extra args]`, which builds in `wine/build-<label>`
and installs to `engines/src-<label>`. It does not check anything out. The command it runs:

```sh
cd wine/build-11.0
arch -x86_64 /bin/bash -c '
export PATH="/opt/homebrew/opt/bison/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PKG_CONFIG_LIBDIR="$BFME_ROOT/build/deps-x86_64/lib/pkgconfig"
export PKG_CONFIG_PATH="$BFME_ROOT/build/deps-x86_64/lib/pkgconfig"
export CC="clang -arch x86_64"
export CXX="clang++ -arch x86_64"
export CFLAGS="-arch x86_64 -O2 -g -mmacosx-version-min=11.0"
export CXXFLAGS="$CFLAGS"
export LDFLAGS="-arch x86_64 -mmacosx-version-min=11.0"
export CPPFLAGS="-I$BFME_ROOT/build/deps-x86_64/include"

$BFME_ROOT/wine/src/configure \
  --prefix=$BFME_ROOT/engines/src-11.0 \
  --build=x86_64-apple-darwin \
  --enable-archs=i386,x86_64 \
  --disable-winebth_sys \
  --without-alsa --without-capi --with-coreaudio --with-cups --without-dbus \
  --without-ffmpeg --with-freetype --with-gettext --without-gettextpo --without-gphoto \
  --without-gnutls --without-gssapi --without-gstreamer --without-inotify --without-krb5 \
  --without-netapi --with-opencl --without-opengl --without-oss --with-pcap \
  --without-pcsclite --with-pthread --without-pulse --without-sane --without-sdl \
  --without-udev --without-usb --without-v4l2 --without-va --without-vulkan \
  --without-wayland --without-x'
```

`--without-va` is reported as an unrecognized option by Wine 11.0's configure; it is kept only so
the line stays diffable against Gcenx's published option list. `-g` is added to `CFLAGS` (Gcenx
ships stripped release builds) because the whole point of this tree is debugging.

Differences from the Gcenx option list, besides the dropped libraries above:

* **`--disable-tests` is deliberately NOT passed.** Gcenx disables the test suite for distribution;
  the d3d9 test suite needs `dlls/d3d9/tests`. For a build that runs no tests, add it back
  (`scripts/build-wine.sh <label> --disable-tests`); it saves a good part of the build time.
* Gcenx builds the PE side with MacPorts **llvm-mingw** (`--with-mingw=/opt/local/libexec/llvm-mingw/bin/clang`);
  we use **mingw-w64 GCC**. The faulting code in the bug report (`wow64cpu!syscall_32to64`) is
  hand-written assembly in `dlls/wow64cpu/`, so it is byte-identical either way. If the bug turns
  out **not** to reproduce in this build, suspect this difference first and retry with
  `brew install llvm` and `--with-mingw=clang`.

## Building

`scripts/build-wine.sh` does this after configure (pass `CONFIGURE_ONLY=1` to stop before it; never
run a compile on top of a timing-sensitive `scripts/test-skirmish.sh` run):

```sh
cd wine/build-11.0
# REQUIRED: the generated Makefile records a bare `BISON = bison`, and /usr/bin/bison is 2.3,
# which dies on tools/widl/parser.y with "invalid directive: `%code`" four seconds in.
export PATH="/opt/homebrew/opt/bison/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
arch -x86_64 make -j$(sysctl -n hw.ncpu)
arch -x86_64 make install
```

`scripts/build-wine.sh` also exports `BISON=/opt/homebrew/opt/bison/bin/bison`, so Makefiles it
generates are self-contained; the PATH line covers build dirs configured without it.

(`make` does not strictly need the Rosetta shell once configure has baked `CC` into the Makefile,
but running it under `arch -x86_64` keeps every recursive tool invocation consistent.)

Measured on the M3 Max, `-j16`, tests enabled: **~11 min** for a full build, ~20 s for `make install`.
`wine/build-11.0` is 5.4 GB, `engines/src-11.0` 1.5 GB.

Verify WoW64: `engines/src-11.0/bin/wine --version` prints `wine-11.0`, and **both**
`engines/src-11.0/lib/wine/i386-windows/` and `.../x86_64-windows/` must exist.

`WINE_BUILD=src-11.0 . ./env.sh` already resolves to this build (it finds `engines/<name>/bin/wine`)
and points `WINEPREFIX` at `prefixes/src-11.0`, which does not exist yet — create it with
`scripts/setup-prefix.sh src-11.0` when you are ready to run the game on this engine.

Smoke test in a throwaway prefix only — never point a fresh build at `prefixes/`:

```sh
WINEPREFIX=$BFME_ROOT/build/prefix-smoke engines/src-11.0/bin/wine wineboot -u
WINEPREFIX=$BFME_ROOT/build/prefix-smoke engines/src-11.0/bin/wine cmd /c ver
```

## Bisecting 10.0 → 11.0

Done; there is no good commit to bisect from: [docs/history/BISECT-2026-09-23.md](../docs/history/BISECT-2026-09-23.md).
