"""Item 4: the tooltip frame (the help box over a hovered button, and the notification box) in our
metal at 2x.

Both movies draw PalantirExport's helpBox* images through their APT import tables (no texture of
their own): `ingamehelpbox` and `ingamenotificationbox` import them, nothing else does. The image
lives on art\\textures\\apt_palantirexport_<n>.tga, and the game divides each matrix that samples it
by that texture's size (docs/HUD.md), so the 2x texture ships with every importing style's matrix
doubled. PalantirExport's own .ru files sample only the palantir frames (the HUD pack's), never
these.
"""
import os
import re
import struct
import subprocess

from ..hud import tga
from ..hud.apt import Apt, geometry, scale
from ..icons import pixels
from ..pipeline import REALESRGAN
from . import root
from .build import blender_py

SOURCE = "PalantirExport"
# PalantirExport's image ids (its .dat: each its own texture) and what they are
TEXTURES = {1: ("helpBoxTopGlow.tga", "glow"), 2: ("helpBoxTop.tga", "frame"),
            3: ("helpBoxSliverGlow.tga", "glow"), 4: ("helpBoxSliver.tga", "frame"),
            5: ("helpBoxMiddleRight.tga", "frame"), 6: ("helpBoxMiddleLeft.tga", "frame"),
            7: ("helpBoxMiddleGlow_Right.tga", "glow"), 8: ("helpBoxMiddleGlow_Left.tga", "glow"),
            9: ("helpBoxBottomGlow.tga", "glow"), 10: ("helpBoxBottom.tga", "frame")}
MOVIES = ("ingamehelpbox", "ingamenotificationbox")


def member(tid):
    return "art\\textures\\apt_%s_%d.tga" % (SOURCE.lower(), tid)


def _strings(data):
    return {m.start(): m.group().decode("latin-1") for m in re.finditer(rb"[ -~]{3,}(?=\0)", data)}


def imports(data):
    """{local character id: (movie, name)} of an .apt file's import table: the records are
    (movie string offset, name string offset, character, 0), the strings in the same file."""
    s = _strings(data)
    out = {}
    for off in range(0, len(data) - 15, 4):
        m, n, c, p = struct.unpack_from("<4I", data, off)
        if m in s and n in s and p == 0 and s[m].lower() == SOURCE.lower() and s[n].lower().endswith(".tga"):
            out[c] = (s[m], s[n])
    return out


def exports(data):
    """{export name: character id} of an .apt file's export table ((name offset, character) pairs)."""
    s = _strings(data)
    out = {}
    for off in range(0, len(data) - 7, 4):
        n, c = struct.unpack_from("<2I", data, off)
        if n in s and s[n].lower().startswith("helpbox") and c < 4096:
            out[s[n].lower()] = c
    return out


def check_tables(apt):
    """The import and export tables say what this module assumes, or SystemExit."""
    ex = exports(apt.read("%s.apt" % SOURCE.lower()))
    for tid, (name, _) in TEXTURES.items():
        if ex.get(name.lower()) != tid:
            raise SystemExit("%s exports %s as %s, not %d" % (SOURCE, name, ex.get(name.lower()), tid))
    for m in apt.members(""):
        if m.endswith(".apt") and m[:-4] not in MOVIES and m[:-4] != SOURCE.lower():
            if any(n.lower() in {v[0].lower() for v in TEXTURES.values()} for _, n in imports(apt.read(m)).values()):
                raise SystemExit("%s imports the help box images too: double it as well" % m)


def doubled(apt):
    """{member: bytes} of the two movies' .ru files with every style sampling a helpBox image doubled."""
    names = {v[0].lower() for v in TEXTURES.values()}
    out, n = {}, 0
    for mv in MOVIES:
        ids = {c for c, (_, name) in imports(apt.read(mv + ".apt")).items() if name.lower() in names}
        if len(ids) != len(TEXTURES):
            raise SystemExit("%s imports %d of the %d help box images" % (mv, len(ids), len(TEXTURES)))
        for m, data in geometry(apt, mv).items():
            text, k = scale(data.decode("latin-1"), ids, 2)
            if k:
                out[m] = text.encode("latin-1")
                n += k
    return out, n


def build():
    """{member: bytes} of item 4: the ten textures at 2x and the doubled geometry; and a report."""
    apt = Apt()
    check_tables(apt)
    jobs = []
    for tid, (name, kind) in sorted(TEXTURES.items()):
        data = apt.read(member(tid))
        src = root("tips", "src", "%d.png" % tid)
        pixels.write(src, *tga.decode(data))
        rgb, x4, a2 = (root("tips", "up", "%d%s.png" % (tid, s)) for s in ("_rgb", "_x4", "_a2"))
        subprocess.check_call([pixels.MAGICK, src, "-alpha", "off", rgb])
        subprocess.check_call([REALESRGAN, "-i", rgb, "-o", x4, "-n", "realesrgan-x4plus",
                               "-m", os.path.join(os.path.dirname(REALESRGAN), "models")],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call([pixels.MAGICK, src, "-alpha", "extract", "-filter", "Lanczos", "-resize", "200%",
                               "-depth", "8", a2])
        jobs.append(dict(name="%d %s" % (tid, name), kind=kind, x4=x4, alpha2=a2,
                         out2=root("tips", "2x", "%d.png" % tid), tid=tid))
    blender_py("tips", dict(textures=jobs, report=root("tips", "paint.txt")))
    files = {}
    for j in jobs:
        ea = apt.read(member(j["tid"]))
        w, h, rgba = pixels.read(j["out2"])
        ew, eh = tga.info(ea)[:2]
        if (w, h) != (2 * ew, 2 * eh):
            raise SystemExit("%s: %dx%d, want %dx%d" % (j["name"], w, h, 2 * ew, 2 * eh))
        files[member(j["tid"])] = tga.encode(ea, w, h, rgba)
    geo, n = doubled(apt)
    files.update(geo)
    for m in files:
        if apt.owner(m) is None:
            raise SystemExit("%s: EA has no such member" % m)
    return files, "tooltip: %d textures at 2x, %d styles in %d geometry files doubled" % (len(TEXTURES), n, len(geo))
