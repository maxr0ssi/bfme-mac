"""The scenery review: EA's objects against ours at the RTS camera, one sheet per culture, and a
stretch of a real map with its scenery placed as the map places it.

    python3 -m sagekit scenery review [--culture a,b] [--per 8]
        -> build/assets/_review_finish/scenery/<culture>.jpg
    python3 -m sagekit scenery map "<map name>" [--at x,y] [--size 900]
        -> build/assets/_review_finish/scenery/map_<map>.jpg

The objects shown are the culture's most used (multiplayer maps first) whose sheets we recolour,
one per model, rendered with EA's sheets and with ours (sagekit/board.py's renderer: the game's
own meshes, textures and normal maps). Renders: build/assets/scenery/_review/.
"""
import json
import os
import re

from . import paths
from .formats.textures import compiled_path

REVIEW = os.path.join(paths.REPO, "build", "assets", "_review_finish", "scenery")
WORK = os.path.join(paths.BUILD, "scenery", "_review")
DAMAGED = re.compile(r"_D\d?$|_D\d?_|_RUBBLE|_DES", re.I)


def extract(g, model, dest):
    """board.extract, and the sheets EA shipped only as JPG (Osgiliath's damaged ones), which
    board's DDS-then-TGA lookup leaves out."""
    from . import board
    from .formats.w3d import W3DFile
    path, skl, texmap = board.extract(g, model, dest)
    for m in W3DFile(path).meshes.values():
        for t in m.textures:
            jpg = compiled_path(t, ".jpg")
            if t.lower() not in texmap and g.owner(jpg):
                out = os.path.join(dest, "tex", jpg.split("\\")[-1])
                with open(out, "wb") as fh:
                    fh.write(g.read(jpg))
                texmap[t.lower()] = out
    return path, skl, texmap


def ours_texmap(texmap, a):
    """EA's {texture: file} with every sheet we recolour swapped for ours."""
    from .scenery import out_path
    out = {}
    for t, path in texmap.items():
        s = a["sheets"].get(t[:-4] if t.endswith((".tga", ".dds")) else t)
        mine = s and "skip" not in s and out_path(s["member"])
        out[t] = mine if mine and os.path.exists(mine) else path
    return out


def pick(a, culture, per=8):
    """[(object, model)] to show: the culture's most used objects, one per model, each drawing a
    sheet we recolour; healthy bodies first, one damaged one if there is room."""
    todo = {t for t, s in a["sheets"].items() if "skip" not in s and s["culture"] == culture}
    objs = sorted(((o, r) for o, r in a["objects"].items() if r["culture"] == culture and set(r["textures"]) & todo
                   and (r["mp"] or r["other"])), key=lambda o_r: (-len(o_r[1]["mp"]), -o_r[1]["placed"], o_r[0]))
    out, seen, stems = [], set(), set()
    for o, r in objs:
        stem = re.sub(r"(Snow|Snowy|\d+)$", "", o)
        healthy = [m for m in r["models"] if not DAMAGED.search(m)] or r["models"]
        m = healthy[0]
        if m.lower() in seen or stem in stems and len(out) >= per // 2:
            continue
        seen.add(m.lower())
        stems.add(stem)
        out.append((o, m))
        if len(out) == per - 1:
            break
    dmg = next(((o, m) for o, r in objs for m in r["models"] if DAMAGED.search(m) and m.lower() not in seen), None)
    return out + ([dmg] if dmg else [])


def render_culture(g, a, culture, per=8):
    from . import board
    from .formats.w3d import W3DFile
    from assets.scenery.cultures import CULTURES
    work = os.path.join(WORK, culture)
    os.makedirs(os.path.join(work, "out"), exist_ok=True)
    shots, tiles = [], []
    for obj, model in pick(a, culture, per):
        path, skl, texmap = extract(g, model, work)
        hidden = board.hidden_meshes(open(path, "rb").read())
        need = {t.lower() for m in W3DFile(path).meshes.values() for t in m.textures if "nrm" not in t.lower()}
        if not need or need - set(texmap):
            continue                                    # EA's own model draws untextured: nothing to compare
        for who, tm in (("ea", texmap), ("our", ours_texmap(texmap, a))):
            prefix = os.path.join(work, "out", "%s_%s_" % (who, model.lower()))
            if who == "our" and os.path.exists(prefix + "rts.png"):
                os.remove(prefix + "rts.png")           # ours follow the sheets: always again
            shots.append({"model": path, "skeletons": skl, "texmap": tm, "out": prefix, "expect": ["rts"],
                          "zoom": 0.62, "hidden": hidden})
            tiles.append((prefix + "rts.png", "%s  %s (%s)" % ("EA" if who == "ea" else "ours", obj, model)))
    board.render(shots, os.path.join(work, "shots.json"), res=(760, 640), samples=24)
    pngs = []
    for src, text in tiles:
        dst = src[:-8] + "_tile.png"
        board.tile(src, dst, text, w=420, h=354)
        pngs.append(dst)
    rows = [(" ", pngs[k:k + 4]) for k in range(0, len(pngs), 4)]
    label, palette = CULTURES[culture][:2]
    os.makedirs(REVIEW, exist_ok=True)
    return board.sheet("%s: EA's against ours (palette: %s)" % (label, palette),
                       "Left of each pair EA's sheets, right ours, at the RTS camera; the culture's most used objects "
                       "first. Geometry is EA's; only the sheets change.", rows, os.path.join(REVIEW, "%s.jpg" % culture))


def review(cultures=None, per=8):
    from .game import Install
    from .scenery import audit
    g, a = Install(), audit()
    cultures = cultures or [r["culture"] for r in a["cultures"] if r["recolour"]]
    for c in cultures:
        print(os.path.relpath(render_culture(g, a, c, per), paths.REPO))
    return 0


# ------------------------------------------------------------------------------------ a map stretch
def map_area(map_name, at=None, size=900.0, limit=160):
    """A size x size stretch of map `map_name` (its densest scenery by default) with every scenery
    object the map places there, EA's and ours, from the RTS camera's angle. One Blender."""
    from . import board
    from .formats.maps import placements
    from .game import Install
    from .pipeline import blender_slot
    from .scenery import audit
    g, a = Install(), audit()
    member = next(m for m in placements(g) if m.split("\\")[1].lower() == map_name.lower())
    objs = [o for o in placements(g)[member] if o[0] in a["objects"]]
    if at is None:                                  # the square holding the most scenery placements
        best = max(objs, key=lambda o: sum(abs(p[1] - o[1]) < size / 2 and abs(p[2] - o[2]) < size / 2 for p in objs))
        at = best[1:3]
    near = [o for o in objs if abs(o[1] - at[0]) < size / 2 and abs(o[2] - at[1]) < size / 2][:limit]
    work = os.path.join(WORK, "map")
    os.makedirs(os.path.join(work, "out"), exist_ok=True)
    models, place = {}, []
    for name, x, y, z, angle in near:
        r = a["objects"][name]
        healthy = [m for m in r["models"] if not DAMAGED.search(m)] or r["models"]
        m = healthy[0]
        if m.lower() not in models:
            path, skl, texmap = extract(g, m, work)
            models[m.lower()] = dict(path=path, skeletons=skl, ea=texmap, our=ours_texmap(texmap, a),
                                     hidden=board.hidden_meshes(open(path, "rb").read()))
        place.append([m.lower(), x - at[0], y - at[1], angle])
    stem = re.sub(r"\W+", "_", map_name.lower()).strip("_")
    spec = os.path.join(work, "%s.json" % stem)
    with open(spec, "w") as fh:
        json.dump({"models": models, "place": place, "size": size, "out": os.path.join(work, "out", stem + "_")}, fh)
    import subprocess
    script = os.path.join(paths.REPO, "sagekit", "blender", "scenery_map.py")
    with blender_slot():
        r = subprocess.run([paths.BLENDER, "-b", "--python", script, "--", spec], capture_output=True, text=True)
    open(spec[:-5] + ".log", "w").write(r.stdout + r.stderr)
    if "JOB OK" not in r.stdout:
        raise SystemExit("map render failed - see %s\n%s" % (spec[:-5] + ".log", (r.stdout + r.stderr)[-2500:]))
    prefix = os.path.join(work, "out", stem + "_")
    tiles = []
    for who, text in (("ea", "EA's sheets"), ("our", "ours")):
        dst = prefix + who + "_tile.png"
        board.tile(prefix + who + ".png", dst, "%s: %s" % (map_name, text), w=900, h=640)
        tiles.append(dst)
    os.makedirs(REVIEW, exist_ok=True)
    dest = board.sheet("%s: the map's scenery, EA's and ours" % map_name,
                       "%d placements of %d models within %d units of (%d, %d), as the map places them (terrain left out)"
                       % (len(place), len(models), size // 2, at[0], at[1]), [(" ", tiles)],
                       os.path.join(REVIEW, "map_%s.jpg" % stem))
    print(os.path.relpath(dest, paths.REPO))
    return 0
