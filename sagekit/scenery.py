"""The map scenery: EA's civilian buildings, ruins and set pieces, recoloured per culture.

About 1,700 objects nobody builds: Osgiliath's ruins, Minas Tirith's houses, Erebor's halls, the
Shire's smials, carts and fences. They are placed by the maps, so the audit reads every map
(sagekit/formats/maps.py) and ranks the cultures (assets/scenery/cultures.py) by how many maps place
them. The work is per SHEET, not per object: many objects share a sheet, and a sheet recoloured
once keeps every one of them consistent. Each sheet takes its culture's palette through that
faction's own flat-sheet layers (the ones `sagekit sheets <faction>` runs) or the Wilderland grade
(assets/scenery/style.py), at EA's size and format, with no geometry changed.

A sheet is left alone when a faction's art could change with it: drawn by any object outside the
civilian, obsolete, nature and cinematic folders (a faction's building, unit or shared prop, a
neutral capturable building), or shipped by any of our archives already (a faction's recoloured
sheet). So the seven faction packs and the neutral pack stay byte for byte as they are, and
`!!!!!!!!!!!sagekit-scenery.big` (sagekit/install.py) only adds EA sheets nobody else touches.

    python3 -m sagekit scenery audit                       the ranking: build/assets/scenery/_audit/
    python3 -m sagekit scenery sheets [--culture a,b]      recolour into build/assets/scenery/_sheets/out
    python3 -m sagekit scenery review [--culture a,b]      EA's against ours (sagekit/scenery_review.py)
    python3 -m sagekit install scenery --check | install scenery | revert scenery
"""
import glob
import json
import os
import re
import subprocess
from collections import defaultdict

from . import paths
from .formats.textures import compiled_path

OWNER = "scenery"
ROOT = os.path.join(paths.BUILD, OWNER)
AUDIT = os.path.join(ROOT, "_audit", "audit.json")
SHEETS = os.path.join(ROOT, "_sheets")
# INI folders (data\\ini\\object\\<folder>) whose objects a scenery recolour may change: map scenery only
FREE = ("civilian", "obsolete", "nature", "cinematic", "demotest")
NORMAL = re.compile(r"_nrm|_nml|nrm$|nml$|normal|_hf$|height|bump|_env$", re.I)
HOUSE = re.compile(r"house_?col|^..hc|_hc$", re.I)


def folder(member):
    return member.lower().split("\\")[3]


def in_scope(obj, o):
    """A map scenery object: in the civilian or obsolete folders, not a unit (townsfolk, animals),
    or one of the map props EA filed in a faction's folder (cultures.ALSO)."""
    from assets.scenery.cultures import ALSO, UNITS
    return obj in ALSO or folder(o["file"]) in ("civilian", "obsolete") and not o["file"].lower().endswith(UNITS)


def blockers(own):
    """{texture key: ["<folder>\\<object>" or "INI swap: <group>"]}: who outside the map scenery
    draws each sheet (a faction's building, unit or prop, a neutral capturable building, the
    system objects). Judged by each object's INI folder, not its ownership group: EA's
    GondorBuildingIthilien01 is civilian whatever its name says."""
    from assets.scenery.cultures import ALSO
    out = defaultdict(set)
    for obj, o in own.objects.items():
        if folder(o["file"]) in FREE or obj in ALSO:
            continue
        for _, models in o["draws"]:
            for m in models:
                for t in own.textures_of(m):
                    out[t].add("%s\\%s" % (folder(o["file"]), obj))
    for t, groups in own.swaps.items():         # (the civilian files' swaps are not recorded)
        out[t] |= {"INI swap: %s" % gr for gr in groups}
    return out


def sheet_member(g, key):
    """The archive member the game reads sheet `key` from: EA's DDS, else TGA, else JPG
    (Osgiliath's damaged sheets exist only as JPG); None when none is there."""
    for ext in (".dds", ".tga", ".jpg"):
        m = compiled_path(key, ext)
        if g.owner(m):
            return m
    return None


def shipped_by_us(own_archive=OWNER):
    """{member: archive} of everything our archives ship: the installed ones in the game folder
    and the staged ones under build/assets/*/_install, except the scenery archive itself."""
    from .formats.big import Archive
    out = {}
    found = []
    for d in paths.GAMEDIRS.values():
        found += [os.path.join(d, f) for f in os.listdir(d) if paths.is_ours(f) and f.lower().endswith(".big")]
    found += glob.glob(os.path.join(paths.BUILD, "*", "_install", "*.big"))
    for p in found:
        name = os.path.basename(p)
        if name.lower().endswith("-%s.big" % own_archive):
            continue
        for k in Archive(p).index():
            out.setdefault(k, name)
    return out


def audit(g=None, refresh=False):
    """The audit: every scenery object with its culture and map use, every sheet with its users,
    its decision and the palette it takes. Written to build/assets/scenery/_audit/audit.json."""
    from assets.scenery.cultures import ALSO, CULTURES, culture_of

    from .formats.maps import MP, map_name, placements
    from .game import Install
    from .ownership import load
    from .scaffold import FX_SHEET
    if not refresh and os.path.exists(AUDIT):
        return json.load(open(AUDIT))
    g = g or Install()
    own = load(g)
    used = defaultdict(lambda: [set(), set(), 0])           # object -> [mp maps, other maps, placed]
    for member, objs in placements(g).items():
        for name, *_ in objs:
            u = used[name]
            if member.startswith("maps\\"):
                u[0 if MP in member else 1].add(map_name(member))
            u[2] += 1
    objects, sheets = {}, {}
    for obj, o in sorted(own.objects.items()):
        if not in_scope(obj, o):
            continue
        models = sorted({m for _, ms in o["draws"] for m in ms if m and m.lower() != "none" and g.has_model(m)},
                        key=str.lower)
        if not models:
            continue
        mp, other, placed = used.get(obj, (set(), set(), 0))
        cul = ALSO.get(obj) or culture_of(obj, o["file"], models)
        tex = sorted({t for m in models for t in own.textures_of(m)})
        objects[obj] = dict(culture=cul, file=o["file"], models=models, textures=tex, mp=sorted(mp),
                            other=sorted(other), placed=placed)
        for t in tex:
            s = sheets.setdefault(t, dict(users={}, mp=set(), other=set(), placed=0))
            s["users"].setdefault(cul, []).append(obj)
            s["mp"] |= mp
            s["other"] |= other
            s["placed"] += placed
    ours, block = shipped_by_us(), blockers(own)
    our_stems = {k.rsplit(".", 1)[0]: a for k, a in ours.items()}
    for t, s in sheets.items():
        s["member"] = sheet_member(g, t)
        cul_mp = {c: len({m for o in objs for m in objects[o]["mp"]}) for c, objs in s["users"].items()}
        cul_pl = {c: sum(objects[o]["placed"] for o in objs) for c, objs in s["users"].items()}
        s["culture"] = max(s["users"], key=lambda c: (cul_mp[c], cul_pl[c], c))
        s["palette"] = CULTURES[s["culture"]][1]
        blocked = sorted(block.get(t, ()))
        if NORMAL.search(t):
            s["skip"] = "normal or height map"
        elif FX_SHEET.search(t) or HOUSE.search(t):
            s["skip"] = "effect, unit, light-map or house-colour sheet"
        elif not s["member"]:
            s["skip"] = "no file in EA's archives"
        elif blocked:
            s["skip"] = "drawn by %s%s" % (", ".join(blocked[:4]), " and %d more" % (len(blocked) - 4) if len(blocked) > 4 else "")
        elif s["member"].rsplit(".", 1)[0] in our_stems:
            s["skip"] = "shipped by %s" % our_stems[s["member"].rsplit(".", 1)[0]]
        elif not s["mp"] and not s["other"]:
            s["skip"] = "on no map"
        s["mp"], s["other"] = sorted(s["mp"]), sorted(s["other"])
        s["size"] = _size(g, s["member"]) if s["member"] else None
    out = dict(objects=objects, sheets=sheets, cultures=_rank(objects, sheets))
    os.makedirs(os.path.dirname(AUDIT), exist_ok=True)
    with open(AUDIT, "w") as fh:
        json.dump(out, fh, indent=0)
    with open(AUDIT[:-5] + ".md", "w") as fh:
        fh.write("\n".join(report(out)) + "\n")
    return out


def _size(g, member):
    """(width, height, format) of an EA sheet: DXT1/DXT5/..., TGA24/32 or JPG."""
    import struct
    d = g.read(member)
    if member.endswith(".dds"):
        h, w = struct.unpack_from("<II", d, 12)
        return w, h, d[84:88].decode("latin-1").strip("\0") or "RGBA"
    if member.endswith(".tga"):
        w, h = struct.unpack_from("<HH", d, 12)
        return w, h, "TGA%d" % d[16]
    from .formats.textures import MAGICK
    w, h = subprocess.check_output([MAGICK, "identify", "-format", "%w %h", "jpg:-"], input=d).split()
    return int(w), int(h), "JPG"


def _rank(objects, sheets):
    """[culture row], most multiplayer maps first."""
    from assets.scenery.cultures import CULTURES
    rows = []
    for c, (label, pal, *_) in CULTURES.items():
        objs = [o for o, r in objects.items() if r["culture"] == c]
        mine = [t for t, s in sheets.items() if s["culture"] == c]
        todo = [t for t in mine if "skip" not in sheets[t]]
        rows.append(dict(culture=c, label=label, palette=pal, objects=len(objs),
                         placed_objects=sum(1 for o in objs if objects[o]["placed"]),
                         placements=sum(objects[o]["placed"] for o in objs),
                         mp=len({m for o in objs for m in objects[o]["mp"]}),
                         other=len({m for o in objs for m in objects[o]["other"]}),
                         sheets=len(mine), recolour=len(todo),
                         mb=round(sum(_bytes(sheets[t]["size"]) for t in todo) / 2 ** 20, 1)))
    return sorted(rows, key=lambda r: (-r["mp"], -r["placements"]))


def _bytes(size):
    """Bytes a sheet takes in memory as the game holds it (DXT with mips; TGA and JPG as 32-bit)."""
    if not size:
        return 0
    w, h, f = size
    per = {"DXT1": 0.5, "DXT3": 1, "DXT5": 1}.get(f, 4)
    return int(w * h * per * 4 / 3)


def report(a):
    """Markdown lines: the ranking and every sheet's decision."""
    lines = ["# Map scenery audit", "",
             "| Rank | Culture | Palette | Objects (placed) | Placements | MP maps | Other maps | Sheets | Recoloured | MB |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(a["cultures"], 1):
        lines.append("| %d | %s | %s | %d (%d) | %d | %d | %d | %d | %d | %.1f |" % (
            i, r["label"], r["palette"], r["objects"], r["placed_objects"], r["placements"], r["mp"], r["other"],
            r["sheets"], r["recolour"], r["mb"]))
    for r in a["cultures"]:
        lines += ["", "## %s" % r["label"], ""]
        rows = sorted(((t, s) for t, s in a["sheets"].items() if s["culture"] == r["culture"]),
                      key=lambda ts: (-len(ts[1]["mp"]), ts[0]))
        for t, s in rows:
            lines.append("- `%s` %s, %d MP maps, %d objects: %s" % (
                t, "%dx%d %s" % tuple(s["size"]) if s["size"] else "-", len(s["mp"]),
                sum(len(v) for v in s["users"].values()), s.get("skip") or "recolour (%s)" % s["palette"]))
    return lines


def todo(a, cultures=None, only=None):
    """[(key, sheet)] the recolour runs: sheets not skipped, of the given cultures (default all)."""
    return [(t, s) for t, s in sorted(a["sheets"].items()) if "skip" not in s
            and (not cultures or s["culture"] in cultures) and (not only or only.lower() in t)]


def out_path(member):
    """Where a recoloured sheet is written: build/assets/scenery/_sheets/out/<EA's archive path>."""
    return os.path.join(SHEETS, "out", *member.split("\\"))


def signature(culture):
    """What a recolour was made with: the culture, its palette and options, and the paint code. A
    sheet painted under another signature is painted again."""
    import hashlib

    from assets.scenery.cultures import CULTURES
    code = open(os.path.join(paths.ASSETS, "scenery", "paint.py"), "rb").read()
    return "%s %r %s" % (culture, CULTURES[culture], hashlib.sha256(code).hexdigest()[:12])


def paint_one(g, key, s, force=False, done=None):
    """Recolour one sheet in its culture's palette (sagekit/paint/sheets.py on Blender's Python)
    at EA's path, size and format: a DDS as DXT1 (DXT5 where EA's has alpha), a TGA at its depth, a
    JPG through a TGA. Returns a line for the log."""
    import shutil
    import tempfile

    from .formats.textures import MAGICK
    from .pipeline import REALESRGAN
    member, (w, h, fmt) = s["member"], s["size"]
    out = out_path(member)
    if os.path.exists(out) and not force and (done or {}).get(key) == signature(s["culture"]):
        return "have %-28s %s" % (key, s["palette"])
    if fmt not in ("DXT1", "DXT3", "DXT5", "TGA24", "TGA32", "JPG"):
        return "skip %-28s EA's is %s: kept as it is" % (key, fmt)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        ext = ".tga" if fmt in ("JPG", "TGA24", "TGA32") else ".dds"
        src, dst = os.path.join(tmp, "src" + ext), os.path.join(tmp, "out" + ext)
        data = g.read(member)
        if fmt == "JPG":                            # a TGA to paint, a JPG again at the end
            subprocess.run([MAGICK, "jpg:-", "-alpha", "off", "-type", "TrueColor", "-depth", "8", "-compress",
                            "None", src], input=data, check=True)
        else:
            open(src, "wb").write(data)
        r = subprocess.run([paths.blender_python(), "-m", "assets.scenery.paint", s["culture"], src, dst, str(h), REALESRGAN],
                           capture_output=True, text=True, cwd=paths.REPO, env=dict(os.environ, PYTHONPATH=paths.REPO))
        if r.returncode:
            return "FAIL %s\n%s" % (key, r.stderr[-1500:])
        if fmt == "JPG":
            subprocess.check_call([MAGICK, dst, "-quality", "95", "-sampling-factor", "4:4:4", out])
        else:
            shutil.copy(dst, out)
    got = _size_file(out)
    if got[:2] != (w, h):
        os.remove(out)
        return "FAIL %s: written %dx%d, EA's is %dx%d" % (key, got[0], got[1], w, h)
    return "ok   %-28s %4dx%-4d %-5s %s" % (key, w, h, got[2], s["palette"])


def _size_file(path):
    import struct
    d = open(path, "rb").read(128)
    if path.endswith(".dds"):
        hh, ww = struct.unpack_from("<II", d, 12)
        return ww, hh, d[84:88].decode("latin-1")
    if path.endswith(".tga"):
        ww, hh = struct.unpack_from("<HH", d, 12)
        return ww, hh, "TGA%d" % d[16]
    from .formats.textures import MAGICK
    ww, hh = subprocess.check_output([MAGICK, "identify", "-format", "%w %h", path]).split()
    return int(ww), int(hh), "JPG"


def paint(cultures=None, only=None, force=False):
    """Recolour the planned sheets of the given cultures, four at a time. 0 when every one passed."""
    from concurrent.futures import ThreadPoolExecutor

    from .game import Install
    from .pipeline import game_running
    if game_running() and not force:
        print("the game is running - recolouring would take its CPU and GPU. Close it, or pass --force")
        return 1
    g, a = Install(), audit()
    g.owner("")                                 # the index once, before the threads read it
    jobs = todo(a, cultures, only)
    manifest = os.path.join(SHEETS, "painted.json")
    done = json.load(open(manifest)) if os.path.exists(manifest) else {}
    with ThreadPoolExecutor(4) as ex:
        results = list(ex.map(lambda ks: paint_one(g, *ks, force=force or bool(only), done=done), jobs))
    print("\n".join(results))
    for (key, s), r in zip(jobs, results):
        if r.startswith("ok"):
            done[key] = signature(s["culture"])
    planned = {k for k, _ in todo(a)}
    with open(manifest, "w") as fh:
        json.dump({k: v for k, v in sorted(done.items()) if k in planned}, fh, indent=0)
    stale = {out_path(s["member"]) for _, s in todo(a)}       # a recolour the audit no longer plans: out
    for root, _, names in os.walk(os.path.join(SHEETS, "out")):
        for n in names:
            p = os.path.join(root, n)
            if p not in stale:
                os.remove(p)
                print("removed %s (no longer planned)" % os.path.relpath(p, SHEETS))
    return 1 if any(r.startswith("FAIL") for r in results) else 0


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="python3 -m sagekit scenery", description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=["audit", "sheets", "review", "map"])
    ap.add_argument("map", nargs="?", help="map: the map's name, e.g. \"map mp osgiliath\"")
    ap.add_argument("--culture", help="comma-separated cultures (assets/scenery/cultures.py; default: all)")
    ap.add_argument("--only", help="sheets: one sheet (a name or part of one), painted again")
    ap.add_argument("--per", type=int, default=8, help="review: objects per culture")
    ap.add_argument("--at", help="map: the stretch's centre x,y (default: its densest scenery)")
    ap.add_argument("--size", type=float, default=900.0, help="map: the stretch's width in game units")
    ap.add_argument("--force", action="store_true", help="sheets: paint again / run while the game runs")
    a = ap.parse_args(argv)
    cultures = a.culture.split(",") if a.culture else None
    if a.action == "audit":
        r = audit(refresh=True)
        print("\n".join(report(r)[:4 + len(r["cultures"])]))
        print(os.path.relpath(AUDIT[:-5] + ".md", paths.REPO))
        return 0
    if a.action == "sheets":
        return paint(cultures, a.only, a.force)
    from .scenery_review import map_area, review
    if a.action == "review":
        return review(cultures, a.per)
    return map_area(a.map, tuple(float(v) for v in a.at.split(",")) if a.at else None, a.size)
