"""Who draws what: every model and texture sheet the game's objects show, by faction.

A faction's redesign must never change art another faction draws (docs/FACTIONS-PLAN.md): the
Dwarves' old castle walls draw Gondor's GBWallTwr, three factions MBLumberMill, and
art\\compiledtextures\\eb mixes Elven sheets with Erebor's (EBBarracks.* is the Dwarven barracks).
One pass over the game answers "who else draws this?" for every model and sheet:

  - every Draw module of every object under data\\ini\\object (parse_draws), its models and INI
    texture swaps, attributed to a group by the INI's folder: goodfaction\\structures\\elven -> elves,
    ...\\units\\rohan -> men; the civilian files by the culture they are named after
    (civilian\\ereborbuildings.ini -> civilian/erebor, which counts as the Dwarves');
  - every drawn model read once for the textures its meshes name.

Groups that are not a playable faction (civilian props, nature, cinematics, ents) are reported but
never block: a map-placed Rivendell house is Elven art. Arnor reuses Gondor's models one for one
and counts as the Men's (FOLLOWS). The result is cached in build/assets/_ownership.json, keyed by
the archives' sizes and dates, so a rescan happens only when the game's files change.

    python3 -m sagekit owners <faction>      the report: shared models and sheets, recipe problems
"""
import json
import os
import re

from . import paths
from .formats.ini import parse_draws
from .taxonomy import FACTIONS

VERSION = 3
CACHE = os.path.join(paths.BUILD, "_ownership.json")

# INI folder name -> group (good/evilfaction\structures|units|hordes\<name>)
ALIASES = {"dwarven": "dwarves", "elven": "elves", "wild": "goblins", "gondor": "men", "rohan": "men"}
# civilian\<culture>buildings.ini: the culture the file is named after, and the faction it belongs to
CULTURES = {"erebor": "dwarves", "dwarven": "dwarves", "bluemountains": "dwarves", "rivendell": "elves",
            "greyhaven": "elves", "harlindon": "elves", "isengard": "isengard", "minasmorgul": "mordor",
            "carndum": "angmar", "ettenmoors": "angmar", "moria": "goblins", "gondor": "men", "minastirith": "men",
            "ministirith": "men", "osgiliath": "men", "ithilien": "men", "fornost": "men", "angfornost": "men",
            "amonsul": "men", "weathertop": "men"}
FOLLOWS = {"arnor": "men"}          # a group whose drawing counts as a faction's
# an object named for a faction is that faction's wherever its INI lives (the Dwarven undermine hole
# is in the Goblins' holes.ini)
NAMED = re.compile(r"^(Dwarven|Dwarf|Elven|Isengard|Mordor|Angmar|Arnor|Gondor)(?=[A-Z_])")
NAMED_GROUP = {"Dwarven": "dwarves", "Dwarf": "dwarves", "Elven": "elves", "Gondor": "men"}


def group_of(member):
    """The group an INI under data\\ini\\object belongs to (a faction, 'civilian/<culture>', or a folder)."""
    p = member.lower().split("\\")[3:]
    if len(p) >= 4 and p[0] in ("goodfaction", "evilfaction") and p[1] in ("structures", "units", "hordes"):
        return ALIASES.get(p[2], p[2])
    if p and p[0] in ("goodfaction", "evilfaction"):
        return "good_shared" if p[0] == "goodfaction" else "evil_shared"
    if p and p[0] == "civilian":
        stem = re.sub(r"(buildings|structureupgrades|modules)?\.ini$", "", p[-1])
        return "civilian/" + stem if stem in CULTURES else "civilian"
    return p[0] if len(p) > 1 else "other"


def faction_of(group):
    """The playable faction a group's drawing counts for, or None."""
    g = FOLLOWS.get(group, CULTURES.get(group.split("/", 1)[1]) if group.startswith("civilian/") else group)
    return g if g in FACTIONS else None


def key(texture):
    """Case- and extension-free texture key: 'EBFortress.tga' -> 'ebfortress'."""
    t = texture.lower().replace("/", "\\").split("\\")[-1]
    return t[:-4] if t.endswith((".tga", ".dds")) else t


# ------------------------------------------------------------------------------------ the scan
def scan(install):
    """{"objects": {object: {"group", "file", "draws": [[tag, [models]]]}}, "models": {model (lower):
    {"name", "textures": [keys]}}, "swaps": {texture key: [groups]}} - the raw index."""
    objects, swaps, names = {}, {}, {}
    for member in install.members("data\\ini\\object"):
        if not member.endswith(".ini"):
            continue
        folder = group_of(member)
        for d in parse_draws(install.read(member).decode("latin-1")):
            m = NAMED.match(d.object or "")
            g = NAMED_GROUP.get(m.group(1), m.group(1).lower()) if m else folder
            models = d.models() + d.fields.get("ModelName", "").split()[:1]      # W3DTreeDraw & co.
            o = objects.setdefault(d.object, {"group": g, "file": member, "draws": []})
            o["draws"].append([d.tag, models])
            names.update({m.lower(): m for m in models})
            if g.startswith("civilian"):        # map castles swap in each owner's decal (USER_n): not theirs
                continue
            for st in d.states:
                for pair in st.textures:
                    for t in pair:
                        swaps.setdefault(key(t), set()).add(g)
    from .formats.w3d import W3DFile
    models = {}
    for low, name in sorted(names.items()):
        if not install.has_model(name):
            continue
        try:
            meshes = W3DFile(install.read(install.model_path(name))).meshes.values()
        except Exception:                           # noqa: BLE001 - a model the reader cannot parse
            continue
        models[low] = {"name": name, "textures": sorted({key(t) for m in meshes for t in m.textures})}
    return {"objects": objects, "models": models, "swaps": {k: sorted(v) for k, v in swaps.items()}}


def fingerprint(install):
    return [VERSION] + [[os.path.basename(a.path), os.path.getsize(a.path), int(os.path.getmtime(a.path))]
                        for a in install.archives()]


class Ownership:
    """Queries over the index: groups and factions drawing a model or a sheet."""

    def __init__(self, data):
        self.objects, self.models, self.swaps = data["objects"], data["models"], data["swaps"]
        self.model_users, self.sheet_users = {}, {}
        for obj, o in self.objects.items():
            for _, models in o["draws"]:
                for m in models:
                    self.model_users.setdefault(m.lower(), {}).setdefault(o["group"], set()).add(obj)
        for low, users in self.model_users.items():
            for t in (self.models.get(low) or {}).get("textures", ()):
                s = self.sheet_users.setdefault(t, {})
                for g, objs in users.items():
                    s.setdefault(g, set()).add(self.models[low]["name"])
        for t, groups in self.swaps.items():
            for g in groups:
                self.sheet_users.setdefault(t, {}).setdefault(g, set()).add("INI swap")

    def model_groups(self, model):
        """{group: {objects}} drawing `model`."""
        return self.model_users.get(model.lower(), {})

    def sheet_groups(self, texture):
        """{group: {models (or 'INI swap')}} drawing texture `texture`."""
        return self.sheet_users.get(key(texture), {})

    @staticmethod
    def _factions(groups):
        return {f for f in map(faction_of, groups) if f}

    def model_factions(self, model):
        return self._factions(self.model_groups(model))

    def sheet_factions(self, texture):
        return self._factions(self.sheet_groups(texture))

    def other_model(self, model, faction):
        """Other playable factions drawing `model` ({faction: {objects}})."""
        out = {}
        for g, objs in self.model_groups(model).items():
            f = faction_of(g)
            if f and f != faction:
                out.setdefault(f, set()).update(objs)
        return out

    def other_sheet(self, texture, faction):
        """Other playable factions drawing `texture` ({faction: {models}})."""
        out = {}
        for g, models in self.sheet_groups(texture).items():
            f = faction_of(g)
            if f and f != faction:
                out.setdefault(f, set()).update(models)
        return out

    def textures_of(self, model):
        return (self.models.get(model.lower()) or {}).get("textures", [])

    def house_models(self, model):
        """EA's house-colour models (xxHC*) the objects drawing `model` show beside it."""
        out = set()
        for o in self.objects.values():
            if any(model.lower() in (m.lower() for m in ms) for _, ms in o["draws"]):
                out |= {m for _, ms in o["draws"] for m in ms if re.match(r"^[A-Za-z]{2}HC", m)}
        return sorted(out, key=str.lower)

    def body_draw_models(self, model):
        """Every model shown by the Draw modules that show `model` (its lifecycle family)."""
        out = {model.lower()}
        for o in self.objects.values():
            for _, models in o["draws"]:
                if model.lower() in (m.lower() for m in models):
                    out |= {m.lower() for m in models}
        return sorted(out)


_loaded = {}


def load(install=None, refresh=False):
    """The Ownership index, from build/assets/_ownership.json when the archives are unchanged."""
    from .game import Install
    install = install or Install()
    fp = fingerprint(install)
    if not refresh and "index" in _loaded and _loaded["fp"] == fp:
        return _loaded["index"]
    data = None
    if not refresh and os.path.exists(CACHE):
        with open(CACHE) as fh:
            cached = json.load(fh)
        data = cached["index"] if cached.get("fingerprint") == fp else None
    if data is None:
        data = scan(install)
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE + ".tmp", "w") as fh:
            json.dump({"fingerprint": fp, "index": data}, fh)
        os.replace(CACHE + ".tmp", CACHE)
    _loaded.update(fp=fp, index=Ownership(data))
    return _loaded["index"]


# ------------------------------------------------------------------------------------ uses
def faction_sheets(style, install, own=None):
    """(recolour, skipped) for `sagekit sheets`: the style's sheets minus those another faction
    draws. skipped: [(member, {faction: models}, the style's copy or None)]. A sheet nobody's Draw
    modules name (debris, props spawned by OCLs) stays in: it lives in the faction's folder."""
    own = own or load(install)
    copies = {key(k): v for k, v in (getattr(style, "shared_sheets", None) or {}).items()}
    keep, skipped = [], []
    for m in style.sheets(install):
        others = own.other_sheet(m, style.faction)
        if others:
            skipped.append((m, others, copies.get(key(m))))
        else:
            keep.append(m)
    return keep, skipped


def empty_model(own, model, install):
    """A model without meshes (OBBFoundationX, the foundations' stand-in five factions draw): no art
    of anyone's to change, so no reason for an own copy."""
    if own.textures_of(model):
        return False
    from .formats.w3d import W3DFile
    return install.has_model(model) and not W3DFile(install.read(install.model_path(model))).meshes


def recipe_problems(b, own=None, install=None):
    """Why a recipe would change another faction's art: its model family (the Draw modules showing
    its source) drawn by another faction without `own_model`, or its sheet drawn by another faction
    without a pinned `own_textures` name or a `style.shared_sheets` copy. [] when it is safe. Only
    the models the recipe ships count: those its covered Draw modules show in its own states
    (not another build variation's, GBFARTOWB beside GBFARTOWA, nor the models another faction's
    Draw shows beside the source, Blue Mountains' bb_tower03), and none without meshes."""
    from .game import Install
    own = own or load()
    install = install or Install()
    out = []
    ships = {m.lower() for m in [b.source] + b.drawn_models(install)}
    for m in own.body_draw_models(b.source):
        if m not in ships or empty_model(own, m, install):
            continue
        others = own.other_model(m, b.faction)
        if others and b.shipped_name(m).lower() == m.lower():
            out.append("%s is drawn by %s too: ship an own copy (own_model)" % (
                own.models.get(m, {}).get("name", m), ", ".join("%s (%s)" % (f, ", ".join(sorted(o)[:3]))
                                                              for f, o in sorted(others.items()))))
    # a house-colour model another faction draws too gets an own copy (Building.own_house_copy)
    sheet = b.sheet_atlas.texture
    others = own.other_sheet(sheet, b.faction)
    pinned = {key(k) for k in b.own_textures} | {key(k) for k in (getattr(b.style, "shared_sheets", None) or {})}
    if others and key(sheet) not in pinned:
        out.append("sheet %s is drawn by %s too: pin its own name in own_textures (or copy it in style.shared_sheets)"
                   % (sheet, ", ".join(sorted(others))))
    return out


def report(faction, install=None):
    """Markdown lines for `sagekit owners <faction>`."""
    from .game import Install
    from .registry import building_ids, load as load_building
    install = install or Install()
    own = load(install)
    lines = ["# %s: what other factions draw too" % faction, ""]
    mine = sorted({m for o in own.objects.values() if faction_of(o["group"]) == faction
                   for _, ms in o["draws"] for m in ms}, key=str.lower)
    shared = [(m, own.other_model(m, faction)) for m in mine]
    shared = [(m, o) for m, o in shared if o]
    lines += ["## Models the faction draws that another faction draws too (%d of %d)" % (len(shared), len(mine)), ""]
    lines += ["- `%s`: %s" % (m, "; ".join("%s: %s" % (f, ", ".join(sorted(o)[:4])) for f, o in sorted(ob.items())))
              for m, ob in shared]
    sheets = sorted({t for m in mine for t in own.textures_of(m)})
    shared = [(t, own.other_sheet(t, faction)) for t in sheets]
    shared = [(t, o) for t, o in shared if o]
    lines += ["", "## Sheets the faction draws that another faction draws too (%d of %d)" % (len(shared), len(sheets)), ""]
    lines += ["- `%s`: %s" % (t, "; ".join("%s: %s" % (f, ", ".join(sorted(o)[:4])) for f, o in sorted(ob.items())))
              for t, ob in shared]
    style = None
    ids = [i for i in building_ids() if i.startswith(faction + "/")]
    try:
        from .__main__ import _style
        style = _style(faction)
    except (ImportError, StopIteration):
        pass
    if style is not None and style.sheet_dir:
        keep, skipped = faction_sheets(style, install, own)
        lines += ["", "## `sagekit sheets %s`: %d sheets recoloured, %d skipped (another faction's)" % (
            faction, len(keep), len(skipped)), ""]
        lines += ["- skip `%s`: %s%s" % (m.split("\\")[-1], ", ".join(sorted(o)),
                                         " (the style's copy: %s)" % c if c else "") for m, o, c in skipped]
    lines += ["", "## Recipes (%d)" % len(ids), ""]
    for bid in ids:
        probs = recipe_problems(load_building(bid), own, install)
        lines.append("- %s: %s" % (bid, "; ".join(probs) if probs else "ok"))
    return lines
