"""EA's game data as the heroes pack reads it: the effective INI files (Install: the first archive
wins), their top-level blocks, the objects, the macros and the English string table.

Nothing here is EA text in git: every function reads the player's own install.
"""
import functools
import re
from pathlib import Path

from sagekit import paths
from sagekit.formats.big import Archive
from sagekit.game import Install

I = "data\\ini\\"
NL = "\r\n"
# 2.02's English strings: the game reads data\lotr.str from lang\English*.big; 2.02's own units
# (BANNERUI:DwarvenZerker, ...) are named only in englishpatch202.big, so that table is the live one
STRINGS_ARCHIVE = "englishpatch202.big"


def strip(line):
    return re.split(r";|//", line, maxsplit=1)[0]


@functools.lru_cache(maxsize=None)
def install():
    return Install()


@functools.lru_cache(maxsize=None)
def text(member):
    """EA's effective file, latin-1 with EA's line ends kept."""
    return install().read(member).decode("latin-1")


@functools.lru_cache(maxsize=None)
def ini_members():
    return [m for m in install().members(I) if m.endswith((".ini", ".inc"))]


def blocks(src, kind):
    """{name: (start, end, body)} of top-level `kind Name ... End` blocks in `src` (a block's own
    nested Ends are indented; its closing End starts the line)."""
    out = {}
    for m in re.finditer(r"^%s[ \t]+(\S+)[^\n]*\n(.*?)^End\b[^\n]*" % kind, src, re.M | re.S | re.I):
        out.setdefault(m.group(1), (m.start(), m.end(), m.group(2)))
    return out


@functools.lru_cache(maxsize=None)
def objects():
    """{object: dict(member, kw, parent, body)} over every object INI (EA's 2.02 data)."""
    out = {}
    hdr = re.compile(r"^(Object|ChildObject|ObjectReskin)[ \t]+(\S+)(?:[ \t]+([^\s;/]+))?", re.M)
    for m in ini_members():
        if not m.startswith(I + "object\\"):
            continue
        t = text(m)
        hs = list(hdr.finditer(t))
        for k, h in enumerate(hs):
            body = t[h.end(): hs[k + 1].start() if k + 1 < len(hs) else len(t)]
            out.setdefault(h.group(2), dict(member=m, kw=h.group(1), parent=h.group(3) if h.group(1) != "Object" else None,
                                            body=body, start=h.start()))
    return out


def chain(name):
    """The object and its parents, child first."""
    objs, out = objects(), []
    while name in objs and name not in out:
        out.append(name)
        name = objs[name]["parent"]
    return out


def fields(name, key):
    """Every value of `key` (a top-level or module line `key = value`) in the object and its parents."""
    out = []
    for o in chain(name):
        for line in objects()[o]["body"].splitlines():
            m = re.match(r"\s*%s\s*=\s*(.*)" % key, strip(line), re.I)
            if m:
                out.append(m.group(1).strip())
    return out


@functools.lru_cache(maxsize=None)
def all_blocks(kind, members=None):
    """{name: body} of `kind` blocks over the given members (default every INI)."""
    out = {}
    for m in members or ini_members():
        for name, (_, _, body) in blocks(text(m), kind).items():
            out.setdefault(name, body)
    return out


@functools.lru_cache(maxsize=None)
def defines():
    out = {}
    for m in ini_members():
        for name, val in re.findall(r"^#define\s+(\S+)\s+([^;\r\n]*)", text(m), re.M | re.I):
            out.setdefault(name, val.strip())
    return out


@functools.lru_cache(maxsize=None)
def mapped_images():
    """{MappedImage: texture} over data\\ini\\mappedimages."""
    out = {}
    for m in ini_members():
        if m.startswith(I + "mappedimages\\"):
            for name, (_, _, body) in blocks(text(m), "MappedImage").items():
                t = re.search(r"Texture\s*=\s*(\S+)", body)
                out.setdefault(name.lower(), t.group(1) if t else None)
    return out


@functools.lru_cache(maxsize=None)
def strings_text():
    a = Archive(str(Path(paths.GAMEDIRS["rotwk"]) / "lang" / STRINGS_ARCHIVE))
    return a.read("data\\lotr.str").decode("utf-8", "replace")


@functools.lru_cache(maxsize=None)
def labels():
    """{label lower-case: text} of 2.02's English string table (comment lines between a label and
    its text are skipped, as the game does)."""
    out, label = {}, None
    for line in strings_text().splitlines():
        s = line.strip()
        if not s or s.startswith("//"):
            continue
        if label is None:
            if re.match(r"^[A-Za-z0-9_]+:\S+$", s):
                label = s
        elif s.upper() == "END":
            out.setdefault(label.lower(), "")
            label = None
        elif s.startswith('"'):
            out.setdefault(label.lower(), s.strip('"'))
    return out


@functools.lru_cache(maxsize=None)
def audio_events():
    """Every AudioEvent, Multisound and DialogEvent name the game defines (lower-case)."""
    out = set()
    for m in ini_members():
        out |= {n.lower() for n in re.findall(r"^(?:AudioEvent|Multisound|DialogEvent)[ \t]+(\S+)", text(m), re.M | re.I)}
    return out


def texture_exists(name):
    from sagekit.formats.textures import sheet_member
    return bool(name) and sheet_member(install(), name) is not None
