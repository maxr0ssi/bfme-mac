"""A faction's style board: `python3 -m sagekit board <faction>`.

EA's buildings of the faction as they are, rendered like the game draws them (every mesh with the
textures its W3D names, the normal maps applied; blender/board.py) and laid out in one labelled
grid by role: build/assets/<faction>/_board/<faction>_board.jpg. The units come from the
scaffolder's survey (sagekit/scaffold.py plan), so the board works before any recipe exists.
Units, effects and night meshes are hidden; a building with level-up meshes (the pieces its
SubObjectsUpgrades show and hide) gets a second tile with them shown, in the last row.

Tiles: build/assets/<faction>/_board/out/ea_<model>.png. The palette options on the faction's
citadel are sagekit/palettes.py, which shares the extraction and rendering here.
"""
import json
import os
import re
import subprocess

from . import paths
from .formats.textures import compiled_path
from .formats.w3d import W3DFile

# rows of the board: (title, roles of sagekit/scaffold.py ROLES)
ROWS = [("Fortress and add-ons", ("fortress", "fortress_upgrade", "fortress_addon", "citadel")),
        ("Expansions (fortress pads)", ("catapult_tower", "tower_expansion", "hall_expansion", "fortress_wall_hub")),
        ("Production and economy (level 1, as built)", ("barracks", "archery", "stable", "siege", "economy",
                                                        "special", "other")),
        ("Towers", ("tower", "bunker")),
        ("Walls", ("wall_segment", "wall_hub", "wall_gate", "wall_end", "wall_tower", "wall_postern", "wall_trebuchet"))]
LEVELS_ROW = "Level 3: the level-up meshes shown"
NIGHT = re.compile(r"^N_", re.I)
MAX_BLENDERS = 2                            # Blender processes at once (each renders a share of the shots)


def root(faction, what):
    return os.path.join(paths.BUILD, faction, what)


# ------------------------------------------------------------------------------------ extraction
def extract(g, model, dest):
    """EA's model, its skeleton and every texture its meshes name, under dest/w3d and dest/tex.
    Returns (model path, skeleton folder, {texture name: file}); a missing texture is left out
    (the importer's plain stand-in draws it)."""
    w3d, tex = os.path.join(dest, "w3d"), os.path.join(dest, "tex")
    os.makedirs(w3d, exist_ok=True)
    os.makedirs(tex, exist_ok=True)
    path = os.path.join(w3d, model.lower() + ".w3d")
    data = g.read(g.model_path(model))
    with open(path, "wb") as fh:
        fh.write(data)
    f = W3DFile(data)
    skl = f.skeleton()
    if skl:
        with open(os.path.join(w3d, skl), "wb") as fh:
            fh.write(g.read(g.model_path(skl[:-4])))
    texmap = {}
    for m in f.meshes.values():
        for t in m.textures:
            key = t.lower()
            if key in texmap:
                continue
            for ext in (".dds", ".tga"):
                member = compiled_path(t, ext)
                if g.owner(member):
                    out = os.path.join(tex, member.split("\\")[-1])
                    if not os.path.exists(out):
                        with open(out, "wb") as fh:
                            fh.write(g.read(member))
                    texmap[key] = out
                    break
    return path, w3d, texmap


def hidden_meshes(data, switched=(), show_levels=False):
    """What a day render of the building leaves out: night meshes, meshes painted only from unit or
    effect sheets (the goblins, orcs and fire cards of EA's models), and the level-up meshes unless
    show_levels."""
    from .scaffold import FX_SHEET, UNIT_SHEET
    out = []
    for name, m in W3DFile(data).meshes.items():
        tex = [t for t in m.textures if "_nrm" not in t.lower()]
        if NIGHT.match(name) or tex and all(UNIT_SHEET.match(t) or FX_SHEET.search(t) for t in tex):
            out.append(name)
        elif name.upper() in switched and not show_levels:
            out.append(name)
    return out


def survey(faction, g):
    """[(row title, label, model, level-up mesh names)] of the faction's design units, main
    models only (an upgrade's second body is the same model)."""
    from .ownership import load
    from .scaffold import plan, roots, switched
    units, _ = plan(faction, g, load(g))
    by_obj = g.object_draws(roots(faction))
    rows, seen = [], set()
    for u in units:
        if u["second"] or u["source"].lower() in seen:
            continue
        seen.add(u["source"].lower())
        pairs = {(d.file, d.object) for o in u["objects"] for d in by_obj.get(o, [])}
        levels = sorted(switched(g, pairs)[0]) if pairs else []
        row = next((t for t, roles in ROWS if u["role"] in roles), ROWS[2][0])
        label = u["name"].replace("_", " ")
        rows.append((row, label, u["source"], levels))
    return rows


# ------------------------------------------------------------------------------------ rendering
def render(shots, spec_path, res=(900, 780), samples=32):
    """Render the shots in at most MAX_BLENDERS Blender processes (sharing the build slots)."""
    from .pipeline import blender_slot
    script = os.path.join(paths.REPO, "sagekit", "blender", "board.py")
    todo = [s for s in shots if not all(os.path.exists(s["out"] + v + ".png") for v in s.get("expect", ()))]
    if not todo:
        return
    n = min(MAX_BLENDERS, len(todo))
    procs = []
    for i in range(n):
        part = "%s.%d.json" % (spec_path[:-5], i)
        with open(part, "w") as fh:
            json.dump({"res": list(res), "samples": samples, "shots": todo[i::n]}, fh, indent=1)
        procs.append((part, part[:-5] + ".log"))

    def run(part, log):
        with blender_slot():
            r = subprocess.run([paths.BLENDER, "-b", "--python", script, "--", part], capture_output=True, text=True)
        open(log, "w").write(r.stdout + r.stderr)
        if "JOB OK" not in r.stdout or "Traceback" in r.stdout + r.stderr:
            raise SystemExit("board render failed - see %s\n%s" % (log, (r.stdout + r.stderr)[-2500:]))
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(n) as ex:
        list(ex.map(lambda pl: run(*pl), procs))


def magick(cmd):
    r = subprocess.run(["magick"] + cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("magick %s\n%s" % (" ".join(cmd[:6]), r.stderr[-1500:]))


def tile(src, dst, text, w=420, h=364):
    """A labelled tile: the render scaled into w x h, its label under it."""
    magick([src, "-resize", "%dx%d^" % (w, h), "-gravity", "center", "-extent", "%dx%d" % (w, h),
            "-background", "#1c1d21", "-fill", "#e8e4dc", "-font", paths.FONT, "-pointsize", "16",
            "-gravity", "South", "-splice", "0x30", "-annotate", "+0+6", text, dst])


def sheet(title, note, rows, dest, width=None):
    """Rows [(heading, [tile png])] under a title and a note, on the boards' dark ground."""
    out = os.path.dirname(dest)
    parts = []
    for i, (heading, tiles) in enumerate(rows):
        if not tiles:
            continue
        head = os.path.join(out, "_row_%d_head.png" % i)
        magick(["-size", "1200x44", "xc:#1c1d21", "-font", paths.FONT, "-pointsize", "24", "-fill", "#f2ede2",
                "-gravity", "West", "-annotate", "+10+0", heading, head])
        body = os.path.join(out, "_row_%d.png" % i)
        magick(tiles[:1] + sum((["(", "-size", "6x10", "xc:#1c1d21", ")", t] for t in tiles[1:]), []) + ["+append", body])
        parts += [head, body]
    top = os.path.join(out, "_title.png")
    magick(["-size", "1600x92", "xc:#1c1d21", "-font", paths.FONT, "-fill", "#f2ede2", "-pointsize", "34",
            "-annotate", "+12+44", title, "-fill", "#a8a49c", "-pointsize", "17", "-annotate", "+12+78", note, top])
    magick(["-background", "#1c1d21", top] + parts + ["-gravity", "West", "-append", "-bordercolor", "#1c1d21",
                                                       "-border", "18", "-quality", "90", dest])
    for p in parts + [top]:
        os.remove(p)
    return dest


def run(faction):
    from .game import Install
    g = Install()
    out = root(faction, "_board")
    os.makedirs(os.path.join(out, "out"), exist_ok=True)
    units = survey(faction, g)
    shots, tiles = [], {}
    for row, label, model, levels in units:
        path, skl, texmap = extract(g, model, out)
        data = open(path, "rb").read()
        levels = [n for n in levels if n in W3DFile(data).meshes]     # the model's own level-up meshes
        for lv in ((False, True) if levels else (False,)):
            name = "ea_%s%s_" % (model.lower(), "_lvl3" if lv else "")
            prefix = os.path.join(out, "out", name)
            shots.append({"model": path, "skeletons": skl, "texmap": texmap, "out": prefix, "expect": ["rts"], "zoom": 0.62,
                          "hidden": hidden_meshes(data, levels, lv)})
            text = "%s%s  (%s)" % (label, ", level 3" if lv else "", model)
            tiles.setdefault(LEVELS_ROW if lv else row, []).append((prefix + "rts.png", text))
    render(shots, os.path.join(out, "shots.json"))
    rows = []
    for heading in [t for t, _ in ROWS] + [LEVELS_ROW]:
        pngs = []
        for i, (src, text) in enumerate(tiles.get(heading, [])):
            dst = src[:-8] + "_tile.png"
            tile(src, dst, text)
            pngs.append(dst)
        for k in range(0, len(pngs), 6):                    # at most six a line
            rows.append((heading if k == 0 else " ", pngs[k:k + 6]))
    dest = sheet("%s: style board - EA's buildings as they are" % faction.capitalize(),
                 "EA's own models and sheets at the pipeline's RTS light (units, effects and night meshes hidden). "
                 "This board is the \"before\".", rows, os.path.join(out, "%s_board.jpg" % faction))
    print(os.path.relpath(dest, paths.REPO))
    return 0
