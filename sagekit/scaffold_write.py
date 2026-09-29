"""Writing the stubs `sagekit new` plans (sagekit/scaffold.py): names, flags, text.

Nothing existing is overwritten: a folder that already holds a building.py, or a recipe of the
faction on the same source and target, is left alone and reported."""
import math
import os

from . import names as namelib
from . import paths
from .formats.w3dframes import apply
from .scaffold import plan

PREFIX = {"elves": "EB", "dwarves": "DB", "men": "GB", "isengard": "IB", "mordor": "MB", "goblins": "WB", "angmar": "KB"}
STYLE_CLASS = {"elves": "ElvenStyle", "dwarves": "DwarvenStyle", "men": "MenStyle", "isengard": "IsengardStyle",
               "mordor": "MordorStyle", "goblins": "GoblinStyle", "angmar": "AngmarStyle"}
AUTO_VIEWS = {"rts": (2.2, 50, -38, 50), "close": (1.3, 24, -30, 45), "ingame": (5.0, 53, -62, 50)}   # render.py's


def style_class(faction):
    """The faction style's class name: from assets/<faction>/style.py when it exists."""
    p = os.path.join(paths.ASSETS, faction, "style.py")
    if os.path.exists(p):
        import re
        m = re.search(r"^class (\w+)\(.*Style\)", open(p).read(), re.M)
        if m:
            return m.group(1)
    return STYLE_CLASS[faction]


def free_model(u, install, faction, taken):
    """An own model name for a unit another faction draws: the faction's prefix on EA's name, else
    a digit after its stem; its lifecycle models' names (stem + EA's suffix) free and <= 15 too."""
    src = u["source"]
    stem, suffix = (src[:-4], src[-4:]) if src.lower().endswith("_skn") else (src, "")
    tries = ([PREFIX[faction] + stem[2:]] if stem[:2].upper() != PREFIX[faction] else []) + [stem + d for d in "23456789"]
    caches = list(install.asset_caches().values())
    for s in tries:
        names = [s + suffix] + [s + m[len(stem):] for m in u["lifecycle"] if m.startswith(stem.lower() + "_")]
        if all(len(n) <= 15 and not install.has_model(n) and n.lower() not in taken
               and not any(c.has_model(n.lower() + ".w3d") for c in caches) for n in names):
            taken.update(n.lower() for n in names)
            return s + suffix
    return None


def world_box(u):
    P = [apply(u["frame"], v) for v in u["mesh"].verts]
    return [min(p[i] for p in P) for i in range(3)], [max(p[i] for p in P) for i in range(3)]


def local_box(u):
    P = [apply(u["frame"], v) for v in u["mesh"].verts] if u["world_space"] else u["mesh"].verts
    return [min(p[i] for p in P) for i in range(3)], [max(p[i] for p in P) for i in range(3)]


def views(u):
    lo, hi = world_box(u)
    c = tuple(round((a + b) / 2, 1) for a, b in zip(lo, hi))
    d = math.dist(lo, hi)
    return {n: (c, round(k * d), e, a, lens) for n, (k, e, a, lens) in AUTO_VIEWS.items()}


def decide(units, faction, install):
    """Fill in each unit's recipe attributes: own names, flags, notes."""
    taken = namelib.ea_texture_stems(install) | namelib.recipe_texture_stems()
    models = set()
    for u in sorted(units, key=lambda x: x["tier"] != "HERO" if "tier" in x else not (x["role"] == "fortress" and x["main"])):
        u["world_space"] = u["tilt"] > 5.0
        if u.get("recipe"):                     # a recipe exists: its name stands (and is taken already)
            u["own_textures"] = {u["sheet"]: u["recipe"].own_diffuse}
        else:
            u["own_textures"] = {u["sheet"]: namelib.free_texture(u["sheet"], taken, "HXBCDEFGJKLMNPQRSTVWYZ23456789")}
            taken.add(u["own_textures"][u["sheet"]][:-4].lower())
        u["own_model"] = free_model(u, install, faction, models) if u["others"] else None
        u["house_draw"] = None if u["houses"] else "ModuleTag_Draw_HC" + "".join(w.capitalize() for w in u["name"].split("_"))
        u["house_shared"] = [m for m in u["houses"] if u["house_others"].get(m)]
        u["tier"] = "HERO" if u["role"] == "fortress" and u["main"] else "STANDARD"
        u["alpha"] = u["sheet_format"] in ("DXT3", "DXT5") and u["sheet_alpha"]
    by = {}
    for u in units:
        by.setdefault(tuple(u["objects"]), []).append(u)
    for u in units:
        mates = [x for x in by[tuple(u["objects"])] if x["source"] != u["source"]]
        split = any(x["source"].lower().startswith(u["source"].lower().split("_skn")[0] + "_") for x in mates)
        u["parts"] = (u["tag"],) if u["upgrade"] or (not u["main"] and not u["second"] and not u["suffix"]) \
            or (u["main"] and split) else ()        # (a second build variation: its own states, Building.own_states)
        u["base"] = None
        if u["second"]:
            u["base"] = "%s/%s" % (faction, next(x["name"] for x in units if x["source"] == u["source"] and not x["second"]))


def sheet_alpha(install, sheet):
    """(fourcc, has alpha below opaque) of a sheet's DDS."""
    from .formats.textures import compiled_path
    data = install.read(compiled_path(sheet, ".dds")) if install.owner(compiled_path(sheet, ".dds")) else b""
    if not data:
        return "missing", False
    fcc = data[84:88].decode("latin-1")
    if fcc not in ("DXT3", "DXT5"):
        return fcc, False
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".dds") as fh:
        fh.write(data)
        fh.flush()
        lo = float(subprocess.check_output(["magick", fh.name + "[0]", "-alpha", "extract", "-format", "%[fx:minima]", "info:"]))
    return fcc, lo < 254 / 255


# ------------------------------------------------------------------------------------ text
def facts(u, faction):
    lo, hi = local_box(u)
    lines = ["EA's %s (objects %s; role %s): body %s, %d triangles, painted from %s%s (%s%s)." % (
        u["source"], ", ".join(u["objects"]), u["role"], u["target"], len(u["mesh"].tris), u["sheet"],
        " + " + u["normal"] if u["normal"] else ", no normal map", u["sheet_format"],
        ", cut-out alpha: our texture is DXT5" if u["alpha"] else ""),
        "In %s coordinates: x %.2f..%.2f, y %.2f..%.2f, z %.2f..%.2f." % (
            "model (world_space)" if u["world_space"] else u["target"] + " mesh", lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])]
    if u.get("rivals"):
        lines.append("Target ambiguous: %s could be the body too (the rule takes a normal-mapped mesh standing on "
                     "the ground, then the largest); set `target` to the mesh the design redesigns." % ", ".join(
                         "%s (%d triangles)" % r for r in u["rivals"]))
    if u["tilt"] > 0.5:
        lines.append("Its bone is tilted %.0f degrees from upright%s." % (
            u["tilt"], ": world_space, every number in world axes" if u["world_space"] else ""))
    other = [(n, len(m.tris), m.textures) for n, m in u["model_meshes"].items() if n != u["target"]]
    if other:
        lines.append("Other meshes (EA's, untouched): " + "; ".join(
            "%s %d%s" % (n, t, " (%s)" % ", ".join(tx) if tx else "") for n, t, tx in sorted(other, key=lambda x: -x[1])[:8]) + ".")
    if u["twin"]:
        lines.append("Its body is %s's body under another model: one design can serve both." % u["twin"])
    if u["variation"]:
        lines.append("Build variation %s of %s's %s: the recipe covers that variation's states only (%s is "
                     "the other's; Building.own_states)." % (u["variation"], ", ".join(u["objects"]), u["tag"],
                                                             ", ".join(sorted(u["names"].get(m, m) for m in u["theirs"])) or "-"))
    if u["lifecycle"]:
        lines.append("Lifecycle models in its Draw module: %s." % ", ".join(sorted(u["names"].get(m, m) for m in u["lifecycle"])))
    lines.append("House colour: %s." % (", ".join(u["houses"]) if u["houses"] else
                                        "none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template)"))
    if u["others"]:
        lines.append("Other factions draw %s too (%s): it ships as its own copy, own_model %s." % (
            ", ".join(sorted(u["names"].get(m, m) for m in u["others"])),
            ", ".join(sorted({f for o in u["others"].values() for f in o})), u["own_model"]))
    if u["house_shared"]:
        lines.append("%s is drawn by another faction too: the house step ships an own copy (Building.own_house_copy)."
                     % ", ".join(u["house_shared"]))
    if u["sheet_others"]:
        lines.append("Its sheet is drawn by %s too: our own texture is pinned in own_textures." % ", ".join(sorted(u["sheet_others"])))
    return lines


def wrap(text, width=98, indent=""):
    out, line = [], indent
    for w in text.split():
        if len(line) + len(w) + 1 > width and line.strip():
            out.append(line.rstrip())
            line = indent
        line += w + " "
    out.append(line.rstrip())
    return out


def stub(u, faction):
    head = "%s %s (%s): stub from `sagekit new %s`." % (faction.capitalize(), u["name"].replace("_", " "),
                                                        ", ".join(u["objects"]), faction)
    doc = wrap(head) + [""]
    for f in facts(u, faction):
        doc += wrap(f)
    doc += wrap("EA's body measured: `python3 -m sagekit measure %s/%s` -> work/measure.json." % (faction, u["name"]))
    doc += ["", "Nearest Dwarven recipe: assets/dwarves/%s (the same role; start from its shapes)." % u["nearest"]
            if u["nearest"] else "No Dwarven recipe plays this role."]
    if u["base"]:
        doc += wrap("A second body of %s: chained on %s (`base`), built after it." % (u["source"], u["base"]))
    cls = "".join(w.capitalize() for w in u["name"].split("_"))
    body = ['"""' + doc[0]] + doc[1:] + ['"""', "from sagekit.building import Building"]
    body += ["from sagekit.taxonomy import Tier" if u["tier"] == "HERO" else None, "", "from ..style import %s" % style_class(faction),
             "", "", "class %s(Building):" % cls, "    style = %s()" % style_class(faction),
             '    source = "%s"' % u["source"], '    target = "%s"' % u["target"]]
    body = [x for x in body if x is not None]
    if u["tier"] == "HERO":
        body.append("    tier = Tier.HERO")
    if u["base"]:
        body.append('    base = "%s"' % u["base"])
    if u["own_model"]:
        body.append('    own_model = "%s"            # %s draws %s too (sagekit/ownership.py)' % (
            u["own_model"], ", ".join(sorted({f for o in u["others"].values() for f in o})), u["source"]))
    body.append('    sheet = "%s"' % u["sheet"])
    body.append('    sheet_normal = %s' % ('"%s"' % u["normal"] if u["normal"] else "None"))
    body.append('    own_textures = {"%s": "%s"}      # free in EA\'s files and every recipe (sagekit/names.py)' % (
        u["sheet"], u["own_textures"][u["sheet"]]))
    if u["parts"]:
        body.append("    parts = (%s,)" % ", ".join('"%s"' % p for p in u["parts"]))
    if u["world_space"]:
        body.append("    world_space = True                  # its bone is tilted %.0f degrees" % u["tilt"])
    if u["house_draw"]:
        body.append('    HOUSE_DRAW = "%s"' % u["house_draw"])
    body.append("    views = {")
    for n, (c, d, e, a, lens) in views(u).items():
        body.append('        "%s": (%s, %d, %d, %d, %d),' % (n, c, d, e, a, lens))
    body += ["    }", "", "    def design(self, kit):", "        return []", ""]
    return "\n".join(body)


def readme(u, faction):
    t = ["# %s %s (`%s`)" % (faction.capitalize(), u["name"].replace("_", " "), "`, `".join(u["objects"])), "",
         "Stub from `python3 -m sagekit new %s`: nothing redesigned yet (`design()` returns no solids)." % faction, "",
         "- Source model `%s`, target mesh `%s` (%d triangles), sheet `%s` -> own `%s`%s." % (
             u["source"], u["target"], len(u["mesh"].tris), u["sheet"], u["own_textures"][u["sheet"]],
             ", DXT5 (EA's cut-out alpha kept)" if u["alpha"] else ""),
         "- Role %s; nearest Dwarven recipe `%s`." % (u["role"], u["nearest"])]
    if u["own_model"]:
        t.append("- Ships as `%s`: another faction draws `%s` too." % (u["own_model"], u["source"]))
    if u["parts"]:
        t.append("- Covers the Draw module%s %s." % ("s" if len(u["parts"]) > 1 else "", ", ".join("`%s`" % p for p in u["parts"])))
    t += ["- EA's body measured: `python3 -m sagekit measure %s/%s` -> `work/measure.json`." % (faction, u["name"]), "",
          "## Status", "", "- [ ] healthy body designed", "- [ ] checks pass, renders reviewed", ""]
    return "\n".join(t)


# ------------------------------------------------------------------------------------ the command
def execute(faction, write):
    from .game import Install
    from .ownership import load
    from .registry import building_ids, load as load_building
    g = Install()
    own = load(g)
    units, skipped = plan(faction, g, own)
    for u in units:
        from .formats.w3d import W3DFile
        u["model_meshes"] = W3DFile(g.read(g.model_path(u["source"]))).meshes
        u["house_others"] = {m: own.other_model(m, faction) for m in u["houses"]}
        u["names"] = {m: own.models.get(m, {}).get("name", m) for m in u["lifecycle"] + list(u["others"]) + list(u["theirs"])}
        u["sheet_format"], u["sheet_alpha"] = sheet_alpha(g, u["sheet"])
    have, recipes = {}, {}
    for bid in building_ids():
        if bid.startswith(faction + "/"):
            b = load_building(bid)
            have[(b.source.lower(), b.target.upper())] = bid
            recipes[bid] = b
    for u in units:                             # an existing recipe keeps its own names
        bid = have.get((u["source"].lower(), u["target"].upper())) or "%s/%s" % (faction, u["name"])
        u["recipe"] = recipes.get(bid) if bid in recipes and recipes[bid].source.lower() == u["source"].lower() else None
    decide(units, faction, g)
    print("%-30s %-16s %-16s %6s  %-18s %s" % ("stub", "source", "target", "tris", "nearest Dwarven", "flags"))
    written = []
    for u in units:
        flags = [f for f, on in (("HERO", u["tier"] == "HERO"), ("parts", u["parts"]), ("world_space", u["world_space"]),
                                 ("own_model " + str(u["own_model"]), u["own_model"]), ("HOUSE_DRAW", u["house_draw"]),
                                 ("DXT5", u["alpha"]), ("base", u["base"]), ("own house copy", u["house_shared"])) if on]
        folder = os.path.join(paths.ASSETS, faction, u["name"])
        exists = have.get((u["source"].lower(), u["target"].upper())) or \
            (os.path.exists(os.path.join(folder, "building.py")) and "%s/%s" % (faction, u["name"]))
        print("%-30s %-16s %-16s %6d  %-18s %s%s" % (u["name"], u["source"], u["target"], len(u["mesh"].tris), u["nearest"] or "-",
                                                     ", ".join(flags), "   (exists: %s - left alone)" % exists if exists else ""))
        if write and not exists:
            os.makedirs(folder, exist_ok=True)
            open(os.path.join(folder, "__init__.py"), "a").close()
            with open(os.path.join(folder, "building.py"), "w") as fh:
                fh.write(stub(u, faction))
            with open(os.path.join(folder, "README.md"), "w") as fh:
                fh.write(readme(u, faction))
            written.append(u)
    for m, why in skipped:
        print("  not a unit: %-16s %s" % (m, why))
    if written:
        measure_written(written, faction)
    return 0


def measure_written(units, faction):
    """Measure every stub just written (work/measure.json)."""
    from .measure import path, run
    for u in units:
        bid = "%s/%s" % (faction, u["name"])
        try:
            run(bid)
        except (RuntimeError, ImportError, OSError) as e:
            print("  %s: not measured (%s) - run `python3 -m sagekit measure %s` once the style exists" % (
                bid, str(e).strip().splitlines()[-1] if str(e).strip() else e, bid))
            continue
        print("  measured %s -> %s" % (bid, path(bid)))

