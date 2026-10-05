"""Our model textures that ship as TGA (normal maps, house-colour masks) rewritten as the DDS the game
would build from them, so it loads them without generating mipmaps on its thread.

The game loads every texture with D3DXCreateTextureFromFileInMemoryEx (game.dat 0x53117e). For a TGA,
d3dx9 box-filters the whole mip chain on the game's thread: measured 45 ms for a 1024x1024 normal
map, 136-170 ms at 2048x2048, 28 ms for a 2048x1024 house-colour mask; the same textures as a DDS
holding the chain cost 5, 12 and 8 ms (tools/texupload.c, docs/PERFORMANCE.md "First-use texture
loads"). The game reads `name.dds` before `name.tga` for every texture (0x530d29) and files both
under the `.tga` name in asset.dat, so only the archive member changes.

tools/texbake.c does the work under Wine with the game's own d3dx9_27: it makes the game's call on
the TGA, writes every level it built into an uncompressed DDS (X8R8G8B8 or A8R8G8B8, as d3dx9 chose),
loads that DDS with the same call and compares every byte of every level. Only identical bakes ship,
so the game draws the same texels. Bakes are cached by the TGA's and the d3dx9 DLL's SHA-256 in
build/texbake/. A TGA byte-identical to EA's file of that name keeps EA's form.

    python3 -m sagekit.texbake [archive.big ...]   what in those archives (default: our installed
                                                    ones) still ships as a TGA with mips to build
    python3 -m sagekit.texbake --selfcheck          bakes a synthetic TGA and checks the DDS
"""
import hashlib
import os
import struct
import subprocess
import sys
from pathlib import Path

from . import paths

CACHE = Path(paths.REPO) / "build" / "texbake"
EXE = Path(paths.REPO) / "build" / "texbake.exe"
SRC = Path(paths.TOOLS) / "texbake.c"
PREFIX = Path(paths.REPO) / "build" / "prefix-texbake"
ENGINE = "w10"
D3DX = Path(paths.REPO) / "engines" / ENGINE / "wswine.bundle" / "lib" / "wine" / "i386-windows" / "d3dx9_27.dll"
PREFIX_DIR = "art\\compiledtextures\\"


def eligible(member, data):
    """A model texture the game would build mips for: an uncompressed true-colour TGA under
    art\\compiledtextures (APT textures live in art\\textures and load with one level)."""
    m = member.lower().replace("/", "\\")
    return (m.startswith(PREFIX_DIR) and m.endswith(".tga") and len(data) > 18
            and data[2] in (2, 10) and data[16] in (24, 32))


def dds_member(member):
    return member[:-4] + ".dds"


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _engine_key():
    if not D3DX.exists():
        raise SystemExit("texbake: no d3dx9_27 in engines/%s (%s)" % (ENGINE, D3DX))
    return _sha(D3DX.read_bytes())[:16]


def _exe():
    if not EXE.exists() or EXE.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.check_call(["i686-w64-mingw32-gcc", "-O2", "-o", str(EXE), str(SRC), "-ld3d9"])
    return EXE


def _run(listfile):
    """Run tools/texbake.c over a list under the engine the game plays on; {out path: line}."""
    env = dict(os.environ, WINE_BUILD=ENGINE, BFME_ROOT=str(paths.REPO))
    cmd = ('. ./env.sh && export WINEPREFIX="%s" WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml=;d3d9=b;d3dx9_27=b" '
           '&& wine "%s" "Z:%s"' % (PREFIX, _exe(), listfile))
    r = subprocess.run(["zsh", "-c", cmd], cwd=paths.REPO, env=env, capture_output=True, text=True)
    out = {}
    for line in r.stdout.splitlines():
        if line.startswith("OK "):
            out[line.split()[1]] = line
        elif line.startswith("FAIL"):
            print("texbake: " + line)
    if r.returncode not in (0, 1):
        raise SystemExit("texbake: tools/texbake.c did not run (exit %d): %s" % (r.returncode, r.stdout[-400:] + r.stderr[-400:]))
    return out


def baked(datas):
    """{sha256 of TGA: DDS bytes} for TGA byte strings, baking the ones not cached yet."""
    key = _engine_key()
    CACHE.mkdir(parents=True, exist_ok=True)
    want = {_sha(d): d for d in datas}
    todo = {h: d for h, d in want.items() if not (CACHE / ("%s-%s.ok" % (h, key))).exists()}
    if todo:
        lines = []
        for h, d in todo.items():
            (CACHE / (h + ".tga")).write_bytes(d)
            lines.append("Z:%s|Z:%s" % (CACHE / (h + ".tga"), CACHE / ("%s-%s.dds" % (h, key))))
        listfile = CACHE / "list.txt"
        listfile.write_text("\n".join(lines) + "\n")
        ok = _run(listfile)
        for h in todo:
            dds = CACHE / ("%s-%s.dds" % (h, key))
            (CACHE / (h + ".tga")).unlink(missing_ok=True)
            if "Z:%s" % dds in ok and dds.exists():
                (CACHE / ("%s-%s.ok" % (h, key))).write_text(ok["Z:%s" % dds] + "\n")
        missing = [h for h in todo if not (CACHE / ("%s-%s.ok" % (h, key))).exists()]
        if missing:
            raise SystemExit("texbake: %d texture(s) did not bake identically; nothing staged" % len(missing))
    return {h: (CACHE / ("%s-%s.dds" % (h, key))).read_bytes() for h in want}


def unbaked(files):
    """The eligible TGA members of {member: bytes} that are not EA's own file (what bake() would
    convert); EA's game is only consulted when there is a candidate."""
    cand = [m for m, d in files.items() if eligible(m, d)]
    if not cand:
        return []
    from .game import Install
    g = Install()
    return sorted(m for m in cand if not (g.owner(m) and g.read(m) == files[m]))


def bake(files, log=print):
    """{member: bytes} with every eligible TGA replaced by its baked DDS (same stem); EA's own TGAs and
    ineligible members unchanged. Refuses a stem shipped as both .tga and .dds."""
    from .game import Install
    g = Install()
    names = {m.lower() for m in files}
    todo = {}
    for m, d in files.items():
        if not eligible(m, d):
            continue
        if dds_member(m).lower() in names:
            raise SystemExit("texbake: %s ships as both .tga and .dds" % m)
        if g.owner(m) and g.read(m) == d:
            continue                                     # EA's file: the game has it already
        todo[m] = d
    if not todo:
        return files
    dds = baked(list(todo.values()))
    out = {m: d for m, d in files.items() if m not in todo}
    for m, d in todo.items():
        out[dds_member(m)] = dds[_sha(d)]
    tga, new = sum(map(len, todo.values())), sum(len(out[dds_member(m)]) for m in todo)
    log("texbake: %d TGA textures shipped with their mip chains built (%.1f MB as TGA, %.1f MB as DDS)"
        % (len(todo), tga / 1e6, new / 1e6))
    return out


def check(files, what):
    """(ok, line) for a check suite: no model texture ships as a TGA the game must build mips for."""
    left = sorted(m for m, d in files.items() if eligible(m, d))
    if left:
        return False, "%s: %d TGA textures would build their mips on the game's thread: %s" % (
            what, len(left), ", ".join(m.split("\\")[-1] for m in left[:6]))
    return True, "%s: no TGA model texture left to build mips in game" % what


def staged():
    """Every archive our stages write: faction packs, units (builders, workers, heroes, Create-a-Hero),
    scenery, FX, and the UI archives (sagekit/hud, ui2x, icons)."""
    from .units import ids
    b, live = Path(paths.BUILD), set(ids())
    units = {p for p in b.glob("*/*/_install/*sagekit-*.big") if "%s/%s" % (p.parts[-4], p.parts[-3]) in live}
    return sorted(set(b.glob("*/_install/!!!!!!!!!!!sagekit-*.big")) | units
                  | set(b.glob("_hud/_install/factions/*.big")) | set(b.glob("_ui2x/_install/*.big"))
                  | set(b.glob("_fx/_install/*.big")) | set(b.glob("_units/*.big")))


def ui_rule(member, head):
    """None, or why a UI texture breaks the size and format limits: MappedImage pages DXT and at
    most 1024 (a first use measured 0.6-1.1 ms), APT textures at most 2048x1024 and one level."""
    m = member.lower()
    if m.startswith(PREFIX_DIR) and m.endswith(".dds"):
        h, w = struct.unpack_from("<II", head, 12)
        if head[84:88] not in (b"DXT1", b"DXT3", b"DXT5") or max(w, h) > 1024:
            return "%s: %s %dx%d (pages are DXT, at most 1024)" % (member, head[84:88], w, h)
    if m.startswith("art\\textures\\apt_") and m.endswith(".tga"):
        w, h = struct.unpack_from("<HH", head, 12)
        if w * h > 2048 * 1024:
            return "%s: %dx%d (APT textures at most 2048x1024)" % (member, w, h)
    return None


def validate():
    """sagekit validate: the staged archives ship no TGA that builds mips in game, and the UI pages
    keep their limits. Returns the number of failures."""
    from .formats.big import Archive
    bad = 0
    for p in staged():
        a = Archive(str(p))
        ui = any(k in p.name for k in ("-ui2x", "-icons", "-hud"))
        if ui:
            why = [w for w in (ui_rule(k, a.read(k)[:128]) for k in a.index() if k.endswith((".dds", ".tga"))) if w]
        else:
            why = ["%s %dx%d %d-bit TGA" % (m, w, h, bpp) for _, m, w, h, bpp in scan([p])]
        for w in why[:3]:
            print("FAIL texture formats %s: %s" % (p.name, w))
        bad += bool(why)
    if not bad:
        print("ok   texture formats: %d staged archives, no TGA builds its mips in game, UI pages in limits" % len(staged()))
    return bad


def scan(archives):
    """[(archive, member, w, h, bpp)] eligible TGAs in .big files."""
    from .formats.big import Archive
    out = []
    for p in archives:
        a = Archive(str(p))
        for k, e in a.index().items():
            if k.startswith(PREFIX_DIR) and k.endswith(".tga"):
                head = a.read(k)[:18]
                if eligible(k, head + b"\0"):
                    w, h = struct.unpack_from("<HH", head, 12)
                    out.append((Path(p).name, k, w, h, head[16]))
    return out


def selfcheck():
    w, h = 64, 32
    px = bytes((x * 7 + y * 13 + c * 50) & 0xFF for y in range(h) for x in range(w) for c in range(4))
    tga = bytes([0, 0, 2]) + b"\0" * 9 + struct.pack("<HH", w, h) + bytes([32, 8]) + px
    out = bake({"art\\compiledtextures\\zz\\zzselftest.tga": tga}, log=lambda s: None)
    dds = out["art\\compiledtextures\\zz\\zzselftest.dds"]
    hh, ww, levels = struct.unpack_from("<III", dds, 12)[0], struct.unpack_from("<I", dds, 16)[0], struct.unpack_from("<I", dds, 28)[0]
    assert dds[:4] == b"DDS " and (ww, hh, levels) == (w, h, 7), (ww, hh, levels)
    assert len(dds) == 128 + sum(max(1, w >> i) * max(1, h >> i) * 4 for i in range(7))
    assert check(out, "selfcheck")[0] and not check({"art\\compiledtextures\\zz\\zzselftest.tga": tga}, "x")[0]
    print("texbake selfcheck ok (64x32 TGA -> A8R8G8B8 DDS, 7 levels, identical to d3dx9's texture)")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selfcheck"]:
        selfcheck()
        sys.exit(0)
    import glob
    arcs = sys.argv[1:] or sorted(glob.glob(os.path.join(paths.GAMEDIRS["rotwk"], "*sagekit-*.big")))
    rows = scan(arcs)
    for arc, m, w, h, bpp in rows:
        print("%-44s %-52s %4dx%-4d %d-bit" % (arc, m, w, h, bpp))
    print("%d TGA model textures that build their mips in game" % len(rows))
