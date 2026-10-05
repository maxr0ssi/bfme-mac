"""Texture memory of our archives: what each one costs when loaded, a cap per archive, and the exact
savings the pipeline applies (docs/MEMORY-2GB.md, "Texture memory of our archives").

Every texture the game loads is a D3DPOOL_MANAGED texture with its full mip chain (art\\compiledtextures;
APT textures under art\\textures take one level). Under our wined3d each texture byte costs 1.03 bytes
of the game's 4 GB address space for as long as the texture is loaded, and one more byte of host GL
memory outside it (docs/MEMORY-2GB.md).

The saving applied here changes no texel: a DXT5 sheet whose alpha is 255 everywhere (216 of our sheets,
mostly state variants and opaque production sheets) ships as the DXT1 that draws the same texels at half
the memory. tools/dxtslim.c writes it and keeps it only when the game's d3dx9 call loads both and every
level draws byte-identically on this machine's renderer (point-sampled into a render target). Results are
cached by the DDS's and the d3dx9 DLL's SHA-256 in build/texslim/. A DDS byte-identical to EA's file of
that name stays as it is.

    python3 -m sagekit.texslim [archive.big ...]   memory of each archive (default: our installed ones),
                                                    and what the DXT1 rewrite would save
    python3 -m sagekit.texslim --selfcheck          rewrites a synthetic opaque DXT5 and checks it
"""
import hashlib
import os
import struct
import subprocess
import sys
from pathlib import Path

from . import paths
from .texbake import D3DX, ENGINE, PREFIX, PREFIX_DIR

CACHE = Path(paths.REPO) / "build" / "texslim"
EXE = Path(paths.REPO) / "build" / "dxtslim.exe"
SRC = Path(paths.TOOLS) / "dxtslim.c"
MB = 1 << 20
# In-memory texture MB a staged archive may hold. Faction packs: the largest today (Men, 625 MB);
# lower it as packs slim. An 8-player match that loads every structure of all 7 factions would need
# about 2.9 GB of the ~2.8 GB the address space leaves after the game (docs/MEMORY-2GB.md).
CAP_MB = {"faction": 640, "other": 96}


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def memory(member, data):
    """Bytes a texture member takes once loaded (the texel data of its mip chain), 0 for anything else."""
    m = member.lower().replace("/", "\\")
    if not m.endswith((".dds", ".tga")) or len(data) < 18:
        return 0
    one = not m.startswith(PREFIX_DIR)
    if data[:4] == b"DDS " and len(data) >= 128:
        h, w = struct.unpack_from("<II", data, 12)
        fourcc = data[84:88]
        if struct.unpack_from("<I", data, 80)[0] & 4:
            block = 8 if fourcc == b"DXT1" else 16
            bpp = None
        else:
            bits = struct.unpack_from("<I", data, 88)[0]
            bpp = 4 if bits == 24 else max(1, bits // 8)
    elif m.endswith(".tga"):
        w, h = struct.unpack_from("<HH", data, 12)
        bpp = 4 if data[16] in (24, 32) else max(1, data[16] // 8)
    else:
        return 0
    n, lw, lh = 0, w, h
    for _ in range(1 if one else max(w, h).bit_length()):
        n += ((lw + 3) // 4) * ((lh + 3) // 4) * block if bpp is None else lw * lh * bpp
        lw, lh = max(1, lw // 2), max(1, lh // 2)
    return n


def _opaque_block(b):
    a0, a1 = b[0], b[1]
    if a0 == 255 and a1 == 255:
        return True
    v = [a0, a1] + ([(a0 * (7 - i) + a1 * i) // 7 for i in range(1, 7)] if a0 > a1 else
                    [(a0 * (5 - i) + a1 * i) // 5 for i in range(1, 5)] + [0, 255])
    bits = int.from_bytes(b[2:8], "little")
    return all(v[(bits >> (3 * j)) & 7] == 255 for j in range(16))


def _opaque_top(data):
    """Filter: every alpha of the first level is 255. tools/dxtslim.c checks every level exactly."""
    h, w = struct.unpack_from("<II", data, 12)
    top = data[128:128 + ((w + 3) // 4) * ((h + 3) // 4) * 16]
    if top[0::16].count(255) == len(top) // 16 and top[1::16].count(255) == len(top) // 16:
        return True
    return all(_opaque_block(top[o:o + 8]) for o in range(0, len(top), 16))


def eligible(member, data):
    m = member.lower().replace("/", "\\")
    return (m.startswith(PREFIX_DIR) and m.endswith(".dds") and len(data) > 128 and data[:4] == b"DDS "
            and data[84:88] == b"DXT5" and _opaque_top(data))


def _exe():
    if not EXE.exists() or EXE.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.check_call(["i686-w64-mingw32-gcc", "-O2", "-o", str(EXE), str(SRC), "-ld3d9"])
    return EXE


def _run(listfile):
    env = dict(os.environ, WINE_BUILD=ENGINE, BFME_ROOT=str(paths.REPO))
    cmd = ('. ./env.sh && export WINEPREFIX="%s" WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml=;d3d9=b;d3dx9_27=b" '
           '&& wine "%s" "Z:%s"' % (PREFIX, _exe(), listfile))
    r = subprocess.run(["zsh", "-c", cmd], cwd=paths.REPO, env=env, capture_output=True, text=True)
    if r.returncode not in (0, 1):
        raise SystemExit("texslim: tools/dxtslim.c did not run (exit %d): %s" % (r.returncode, r.stdout[-400:] + r.stderr[-400:]))
    return r.stdout.splitlines()


def slimmed(datas):
    """{sha256 of DXT5: DXT1 bytes or None (kept as DXT5)} for DDS byte strings, rewriting the ones not
    cached yet."""
    key = _sha(D3DX.read_bytes())[:16]
    CACHE.mkdir(parents=True, exist_ok=True)
    want = {_sha(d): d for d in datas}
    mark = lambda h: CACHE / ("%s-%s.res" % (h, key))
    todo = {h: d for h, d in want.items() if not mark(h).exists()}
    if todo:
        lines = []
        for h, d in todo.items():
            (CACHE / (h + ".dds")).write_bytes(d)
            lines.append("Z:%s|Z:%s" % (CACHE / (h + ".dds"), CACHE / ("%s-%s.dxt1.dds" % (h, key))))
        listfile = CACHE / "list.txt"
        listfile.write_text("\n".join(lines) + "\n")
        out = _run(listfile)
        for h in todo:
            (CACHE / (h + ".dds")).unlink(missing_ok=True)
            res = CACHE / ("%s-%s.dxt1.dds" % (h, key))
            line = next((x for x in out if x.split(" ")[1:2] in (["Z:%s" % res], ["Z:%s" % (CACHE / (h + ".dds"))])), "")
            if line.startswith("FAIL"):
                print("texslim: kept as DXT5, " + line)
            mark(h).write_text((line or "FAIL no result") + "\n")
            if not line.startswith("OK"):
                res.unlink(missing_ok=True)
    out = {}
    for h in want:
        res = CACHE / ("%s-%s.dxt1.dds" % (h, key))
        out[h] = res.read_bytes() if mark(h).read_text().startswith("OK") and res.exists() else None
    return out


def slim(files, log=print):
    """{member: bytes} with every opaque DXT5 model texture replaced by its identical-drawing DXT1
    (same member name); EA's own files and everything else unchanged."""
    from .game import Install
    cand = {m: d for m, d in files.items() if eligible(m, d)}
    if not cand:
        return files
    g = Install()
    cand = {m: d for m, d in cand.items() if not (g.owner(m) and g.read(m) == d)}
    res = slimmed(list(cand.values()))
    out, before, after = dict(files), 0, 0
    for m, d in cand.items():
        new = res[_sha(d)]
        if new is not None:
            out[m] = new
            before, after = before + memory(m, d), after + memory(m, new)
    n = sum(1 for d in cand.values() if res[_sha(d)] is not None)
    log("texslim: %d opaque DXT5 textures shipped as the DXT1 that draws the same texels (%.1f -> %.1f MB in memory)"
        % (n, before / MB, after / MB))
    return out


def archive_memory(path):
    """(texture bytes in memory, model bytes, [(bytes, member)] largest first) of a .big."""
    from .formats.big import Archive
    a = Archive(str(path))
    tex, w3d, rows = 0, 0, []
    for k, e in a.index().items():
        if k.endswith(".w3d"):
            w3d += e.size
        elif k.endswith((".dds", ".tga")) and k.startswith("art\\"):
            n = memory(k, a.read(k))
            tex += n
            rows.append((n, k))
    return tex, w3d, sorted(rows, reverse=True)


def cap_mb(name):
    n = os.path.basename(str(name)).lstrip("!").lower()
    small = ("-builder", "-worker", "-heroes", "-units", "-hud", "-icons", "-ui2x", "-fx")
    return CAP_MB["other"] if n.startswith("sagekit-") and any(s in n for s in small) or "/_units/" in str(name) \
        else CAP_MB["faction"]


def validate():
    """sagekit validate: no staged archive holds more texture memory than its cap. Returns failures."""
    from .texbake import staged
    bad, total = 0, 0
    for p in staged():
        tex = archive_memory(p)[0]
        total += tex
        if tex > cap_mb(p) * MB:
            print("FAIL texture memory %s: %.0f MB in memory, cap %d MB (sagekit/texslim.py CAP_MB)" % (p.name, tex / MB, cap_mb(p)))
            bad += 1
    if not bad:
        print("ok   texture memory: %d staged archives within their caps (%.0f MB in all if everything loaded)"
              % (len(staged()), total / MB))
    return bad


def selfcheck():
    """A 64x32 opaque DXT5 with blocks in every endpoint order through dxtslim.c."""
    w, h, levels = 64, 32, 7
    blocks = []
    lw, lh = w, h
    for lvl in range(levels):
        for i in range(((lw + 3) // 4) * ((lh + 3) // 4)):
            c0, c1 = (i * 2654435761) & 0xFFFF, (i * 40503 + lvl * 7) & 0xFFFF
            c1 = c0 if i % 5 == 0 else c1
            alpha = bytes([255, 255]) + bytes(6) if i % 3 else bytes([255, 0]) + bytes(6)   # index 0 = a0 = 255
            blocks.append(alpha + struct.pack("<HHI", c0, c1, (i * 2246822519) & 0xFFFFFFFF))
        lw, lh = max(1, lw // 2), max(1, lh // 2)
    hd = [0] * 31
    hd[0], hd[1], hd[2], hd[3], hd[6] = 124, 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x80000, h, w, levels
    hd[4] = (w // 4) * (h // 4) * 16
    hd[18], hd[19] = 32, 4
    hd[26] = 0x1000 | 0x400008
    dds = b"DDS " + struct.pack("<18I", *hd[:18]) + struct.pack("<I", hd[18]) + struct.pack("<I", hd[19]) + b"DXT5" \
        + struct.pack("<10I", *hd[21:31]) + b"".join(blocks)
    member = "art\\compiledtextures\\zz\\zzslimtest.dds"
    out = slim({member: dds}, log=lambda s: None)[member]
    assert out[84:88] == b"DXT1" and len(out) == 128 + (len(dds) - 128) // 2, "not rewritten"
    assert memory(member, out) * 2 == memory(member, dds)
    print("texslim selfcheck ok (64x32 opaque DXT5 -> DXT1, 7 levels, every level draws identically)")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selfcheck"]:
        selfcheck()
        sys.exit(0)
    import glob
    from .formats.big import Archive
    arcs = sys.argv[1:] or sorted(glob.glob(os.path.join(paths.GAMEDIRS["rotwk"], "*sagekit-*.big")))
    for p in arcs:
        tex, w3d, rows = archive_memory(p)
        a = Archive(str(p))
        save = sum(memory(k, a.read(k)) for _, k in rows if eligible(k, a.read(k))) // 2
        print("%-40s textures %6.1f MB in memory (cap %3d)  models %6.1f MB  opaque DXT5 -> DXT1 saves %5.1f MB"
              % (os.path.basename(p).lstrip("!"), tex / MB, cap_mb(p), w3d / MB, save / MB))
