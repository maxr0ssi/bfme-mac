"""The capture dress: a neutral building takes on the look of the player who captures it.

EA's capturable buildings (the Inn, the Outpost, the signal fire...; `neutral` in
sagekit/taxonomy.py) start owned by the neutral player and change hands with the capture flag they
are linked to (KindOf LINKED_TO_FLAG). The new owner's faction upgrade (Upgrade_DwarfFaction,
Upgrade_MenFaction...: every player template is born with one, playertemplate.ini InitialUpgrades)
then reaches the building's upgrade modules: EA's Inn swaps its command set that way
(CommandSetUpgrade per faction), its shipwright shows "good" or "evil" parts (SubObjectsUpgrade).

A recipe that is `Capturable` (below) adds, per faction, a small dress of kit pieces in that
faction's language: tags `<prefix>_<role>` (assets/neutral/atlas.py), painted in that faction's
ramps. Its build turns each dress into named sub-objects of a model of our own (NB...HC: the style's
house template renamed, its flag dropped), drawn by a Draw module of its own beside the body's:

    CAP_<P>        the dress's solid pieces, on our sheet and layout (one bake, one paint with the body)
    HC_CAP_<P>     its cloth, on EA's house-colour flag texture, tinted in the capturer's colour (the
                   tint follows the texture: housecolor.ini, so CAP_<P> stays as painted)

Both are written with the W3D "hidden" flag (EA's own use: the pathing planes, the Lorien archer's
helmet), so nothing shows while the building is neutral. One SubObjectsUpgrade per faction,
triggered by its faction upgrade (the Men's by Arnor's too), shows its two meshes and hides every
other faction's: the engine applies it to every Draw module of the object (Drawable::showSubObject)
and again after every model swap (W3DModelDraw updateSubObjects). Every dress mesh hangs on the
dress model's root, where no other sub-object hangs: hiding a sub-object also hides every
sub-object on bones below its own, so a body's bone (often the root of a skinned model whose
townsfolk hang below it) would not do. EA's capture flag shows its holder the same way (scripts.lua
OnCaptureFlagGenericEvent hides every FLAG_<FACTION> sub-object and shows the capturer's).

Recapture: a faction's module runs when its upgrade first reaches the building, exactly like EA's
CommandSetUpgrade beside it, so the dress follows the same rule as the units the building offers.
Whether a module runs again when a faction takes back a building it held before is checked in game.
"""
import json
import os
import struct

from .formats.w3d import (HLOD, HLOD_SUB_OBJECT, MESH, MESH_HEADER3, SUB, W3DFile, _cstr, _mesh_name, chunk_bytes,
                          chunks, fix, rename_model)
from .formats.w3dcopy import HLOD_SUB_OBJECT_ARRAY_HEADER, drop_meshes
from .formats.w3dmesh import renamed

HIDDEN = 0x00001000                     # W3D_MESH_FLAG_HIDDEN: hidden until shown (WW3D2 mesh.cpp)
DRESS = {"dwarves": "dw", "elves": "el", "men": "mn", "isengard": "is", "mordor": "mo", "goblins": "gb", "angmar": "an"}
UPGRADES = {"dwarves": ("Upgrade_DwarfFaction",), "elves": ("Upgrade_ElfFaction",),
            "men": ("Upgrade_MenFaction", "Upgrade_ArnorFaction"), "isengard": ("Upgrade_IsengardFaction",),
            "mordor": ("Upgrade_MordorFaction",), "goblins": ("Upgrade_WildFaction",), "angmar": ("Upgrade_AngmarFaction",)}
CLOTH = "cloth"


def mesh_name(faction):
    return "CAP_" + DRESS[faction].upper()


def house_mesh(faction):
    return "HC_" + mesh_name(faction)


def of_tag(tag):
    """The faction a face tag dresses (`dw_gilt` -> dwarves), or None for the body's own."""
    p = tag.split("|")[0].split("_", 1)[0]
    return next((f for f, x in DRESS.items() if x == p and "_" in tag), None)


class Capturable:
    """Mixin for a Building that dresses per capturer. The recipe gives `body(kit)` (its own
    solids, as design() would) and `dress(kit)` ({faction: [Solid]} tagged `<prefix>_<role>`);
    design() is both, and the build splits the dress off again (sagekit/blender/capture.py)."""

    capture = True
    house_tags = ()                     # the body's own cloth is painted; house colour is the dress's

    def body(self, kit):
        return []

    def dress(self, kit):
        return {}

    def design(self, kit):
        out = list(self.body(kit))
        for faction, solids in self.dress(kit).items():
            for s in solids:
                for poly in s.polys:
                    if of_tag(poly[1]) != faction:
                        raise ValueError("%s: %s's dress has a face tagged %s" % (self.id, faction, poly[1]))
            out += solids
        return out

    @property
    def dress_house_model(self):
        """The house-colour model of the dress's cloth: the style's house template's prefix and our
        model's stem (NBHCInn_SKN for NBInn_SKN)."""
        stem = self.shipped_name(self.source)
        return (self.style.house_template[:4] + stem[2:])[:15]


def capturable(b):
    return bool(getattr(b, "capture", False))


def dress_meshes(b):
    """Every dress sub-object name of a recipe ([] for an ordinary one)."""
    return [m for f in DRESS for m in (mesh_name(f), house_mesh(f))] if capturable(b) else []


def cloth_path(ws, faction):
    return ws.path("work", "dress_cloth_%s.json" % DRESS[faction])


# ------------------------------------------------------------------------------------ models
def _set_header(chunk, container, hidden=True):
    c = bytearray(chunk)
    for t, o, s, _ in chunks(c, 8, len(c)):
        if t == MESH_HEADER3:
            a = struct.unpack_from("<I", c, o + 12)[0]
            struct.pack_into("<I", c, o + 12, a | HIDDEN if hidden else a & ~HIDDEN)
            c[o + 32:o + 48] = container.encode("latin-1")[:15].ljust(16, b"\0")
    return bytes(c)


def add_meshes(model, new, after, bone):
    """Model bytes with mesh chunks `new` ({NAME: chunk}) inserted after mesh `after` (None: after
    the last mesh) and one HLOD sub-object each, on `bone`, in every LOD array that holds `after`
    (the first array when None). Earlier copies of the same names are replaced. Every other chunk
    keeps EA's bytes."""
    model = drop_meshes(model, list(new))
    container = None
    meshes = [(t, o, s) for t, o, s, _ in chunks(model, 0, len(model)) if t == MESH]
    last = meshes[-1][1] if meshes else None
    out = bytearray()
    for t, o, s, _ in chunks(model, 0, len(model)):
        raw = model[o:o + 8 + s]
        if t == HLOD:
            raw = _hlod_with(model, o, s, after, list(new), bone)
        out += raw
        if t == MESH and (_mesh_name(model, o, s) == (after or "").upper() or after is None and o == last):
            for t2, o2, s2, _ in chunks(model, o + 8, o + 8 + s):
                if t2 == MESH_HEADER3:
                    container = _cstr(model[o2 + 32:o2 + 48])
            out += b"".join(_set_header(c, container) for c in new.values())
    if container is None:
        raise ValueError("no mesh %s to put the dress after" % after)
    return bytes(out)


def _hlod_with(d, o, s, after, names, bone):
    model = None
    body, done = bytearray(), False
    for t2, o2, s2, has_sub in chunks(d, o + 8, o + 8 + s):
        if t2 == 0x701:                                 # HLOD_HEADER: the model name prefixes sub-objects
            model = _cstr(d[o2 + 16:o2 + 32])
        if not has_sub or t2 != 0x702 or done:          # (LOD arrays only; aggregates and proxies stay)
            body += d[o2:o2 + 8 + s2]
            continue
        subs = [(t3, d[o3:o3 + 8 + s3]) for t3, o3, s3, _ in chunks(d, o2 + 8, o2 + 8 + s2)]
        names_here = [_cstr(c[12:44]).split(".")[-1].upper() for t3, c in subs if t3 == HLOD_SUB_OBJECT]
        if after and after.upper() not in names_here:
            body += d[o2:o2 + 8 + s2]
            continue
        done = after is None
        kept = [c for t3, c in subs]
        for n in names:
            kept.append(chunk_bytes(HLOD_SUB_OBJECT, struct.pack("<I", bone) +
                                    ("%s.%s" % (model, n)).encode("latin-1")[:31].ljust(32, b"\0"), False))
        head = next(i for i, (t3, _) in enumerate(subs) if t3 == HLOD_SUB_OBJECT_ARRAY_HEADER)
        h = bytearray(kept[head])
        struct.pack_into("<I", h, 8, len(names_here) + len(names))
        kept[head] = bytes(h)
        body += chunk_bytes(t2, b"".join(kept), True)
    return chunk_bytes(HLOD, bytes(body), bool(struct.unpack_from("<I", d, o + 4)[0] & SUB))


def dress_chunks(b, orig, export, frame=None):
    """{CAP_<P>: mesh chunk} from the export (sagekit/blender/capture.py split them off the target),
    repaired like the target: the export is fixed against EA's model with a copy of EA's target
    under each dress's name (header version, surface types, materials renamed to our textures)."""
    from .formats.w3dframes import moved
    names = [mesh_name(f) for f in DRESS if mesh_name(f) in W3DFile(export).meshes]
    if not names:
        return {}
    ea = W3DFile(orig).meshes[b.target].bytes
    ref = orig + b"".join(renamed(ea, n) for n in names)
    renames = [(n, old, new) for n in names for _, old, new in b.renames()]
    out = {}
    for n in names:
        data = moved(export, n, n, frame) if frame is not None else export
        fixed, _ = fix(ref, data, renames)
        out[n] = W3DFile(fixed).meshes[n].bytes
    return out


# ------------------------------------------------------------------------------------ the house model
def house_model(b, install, ws):
    """The dress model: EA's house template renamed, its flag dropped; per faction a hidden HC_CAP_<P>
    built from the template's flag mesh (its house-colour material) with our cloth polygons
    (work/dress_cloth_<p>.json, model space) mapped onto the flag texture's plain cloth like the house
    step does (sagekit/house.py), and a hidden CAP_<P>: the export's dress pieces taken into model
    space. All on the root. Returns (member, bytes) or None."""
    from .formats.w3dmesh import Source, build_mesh
    from .formats.w3d import NORMALS, STAGE_TEXCOORDS, VERTICES
    from .house import cloth_rect
    from .housemesh import house_meshes
    tpl_name = b.style.house_template
    name = b.dress_house_model
    tpl = install.read(install.model_path(tpl_name))
    hc = house_meshes(W3DFile(tpl))[0]
    tchunk = W3DFile(tpl).meshes[hc].bytes
    rect = cloth_rect(W3DFile(tpl).meshes[hc])
    new = {}
    for f in DRESS:
        p = cloth_path(ws, f)
        polys = json.load(open(p)) if os.path.exists(p) else []
        if not polys:
            continue
        verts, tris = [], []
        for poly in polys:
            uvs, n = cloth_uvs(poly, rect)
            base = len(verts)
            for q, uv in zip(poly, uvs):
                verts.append(("t", [(0, 1.0)], IDENT, 0, {VERTICES: tuple(q), NORMALS: n, STAGE_TEXCOORDS: uv}))
            tris += [((base, base + i, base + i + 1), 13) for i in range(1, len(poly) - 1)]
        new[house_mesh(f)] = build_mesh(tchunk, {"t": Source(tchunk)}, house_mesh(f), name.upper(), verts, tris, False)
    if os.path.exists(ws.export_model):         # the solid pieces, in model space (the target's frame)
        from .formats.w3dframes import mesh_frames
        src = open(ws.source_model, "rb").read()
        frame = mesh_frames(src, lambda f: install.read(install.model_path(f[:-4])))[b.target]
        new.update(dress_chunks(b, src, open(ws.export_model, "rb").read(), frame))
    if not new:
        return None
    data = rename_model(drop_meshes(tpl, []), tpl_name, name)
    data = add_meshes(data, new, hc, 0)
    data = drop_meshes(data, [hc])                      # EA's flag goes: only the dress's cloth stays
    return install.model_path(name), data


IDENT = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0)        # a 3x4 matrix, rows flat (sagekit/formats/w3dpose.py point)


def cloth_uvs(poly, rect):
    """(UV per corner, face normal) for a cloth polygon: across the face horizontally, top of the
    cloth at the rect's top (sagekit/blender/house.py add_cloth, in plain Python)."""
    import math
    u0, v0, u1, v1 = rect
    a, b_, c = poly[0], poly[1], poly[2]
    e1, e2 = [b_[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
    n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
    ln = math.sqrt(sum(x * x for x in n)) or 1.0
    n = tuple(x / ln for x in n)
    side = (-n[1], n[0], 0.0)                           # (0, 0, 1) x n: horizontal across the face
    ls = math.hypot(side[0], side[1])
    side = (1.0, 0.0, 0.0) if ls < 1e-6 else (side[0] / ls, side[1] / ls, 0.0)
    s = [p[0] * side[0] + p[1] * side[1] for p in poly]
    z = [p[2] for p in poly]
    ds, dz = max(max(s) - min(s), 1e-6), max(max(z) - min(z), 1e-6)
    # Blender UV (v up) -> W3D texcoords as the exporter writes them (v up as well: the game flips rows)
    return [(u0 + (u1 - u0) * (si - min(s)) / ds, v0 + (v1 - v0) * (zi - min(z)) / dz) for si, zi in zip(s, z)], n


# ------------------------------------------------------------------------------------ build hooks
def present(ws):
    """{faction: [its dress mesh names that exist]} in this build's dress model."""
    out = {}
    house = house_path(ws)
    have = set(W3DFile(house).meshes) if house and os.path.exists(house) else set()
    for f in DRESS:
        names = [n for n in (mesh_name(f), house_mesh(f)) if n in have]
        if names:
            out[f] = names
    return out


def house_path(ws):
    from .game import Install
    b = ws.b
    return ws.out(Install.model_path(b.dress_house_model)) if capturable(b) else None


def write_house(b, install, ws):
    """The fixup step's part: the dress house model into out/ (or none, without dress cloth)."""
    if not capturable(b):
        return None
    made = house_model(b, install, ws)
    path = house_path(ws)
    if made is None:
        if os.path.exists(path):
            os.remove(path)
        return None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(made[1])
    print("  %s: %s" % (made[0], ", ".join(sorted(W3DFile(made[1]).meshes))))
    return path


def members(b, install):
    """Archive paths of models the capture dress ships besides the body's (the house model)."""
    return {install.model_path(b.dress_house_model).lower()} if capturable(b) else set()


def cache_ops(b, ws):
    """The dress model, filed as a copy of the style's house template's record (the body ships as
    an ordinary recipe's)."""
    if not capturable(b):
        return []
    house = house_path(ws)
    if house and os.path.exists(house):
        f = b.dress_house_model.lower() + ".w3d"
        return [("model", f, b.style.house_template.lower() + ".w3d"), ("patch", f)]
    return []


def ini_ops(b, install, ws):
    """{INI: [op]}: per faction a SubObjectsUpgrade on its faction upgrade showing its dress and
    hiding every other's, and the dress house model's Draw, shown in the states our dressed body
    stands in (healthy, snow, the derived damaged body), Model None in the rest. (Named the house
    model's Draw: it draws the cloth and the pieces alike.)"""
    if not capturable(b):
        return {}
    have = present(ws)
    every = [n for names in have.values() for n in names]
    out = {}
    standing = {b.source.lower()} | {m.lower() for m in ws.derived}
    house = house_path(ws)
    for obj, draws in b.objects(install).items():
        for d in draws:
            if not b.covers(d) or d.object != obj:      # (a ChildObject inherits its parent's modules)
                continue
            ops = out.setdefault(d.file, [])
            for f, names in have.items():
                block = ["Behavior = SubObjectsUpgrade ModuleTag_SagekitCapture%s" % DRESS[f].upper(),
                         "\tTriggeredBy\t\t\t= %s" % " ".join(UPGRADES[f]),
                         "\tRequiresAllTriggers\t= No",
                         "\tShowSubObjects\t\t= %s" % " ".join(names)]
                hide = [n for n in every if n not in names]
                if hide:
                    block.append("\tHideSubObjects\t\t= %s" % " ".join(hide))
                ops.append(("behavior", obj, "ModuleTag_SagekitCapture%s" % DRESS[f].upper(), block + ["End"]))
            if house and os.path.exists(house):
                tag = "ModuleTag_Draw_" + b.dress_house_model
                ops.append(("draw", obj, tag, b.dress_house_model))
                for st in b.own_states(d):
                    if st.kind == "model" and st.flags:
                        shown = bool(st.model) and st.model.lower() in standing
                        ops.append(("state", obj, tag, sorted(st.flags), b.dress_house_model if shown else "None"))
    return out


def without(b, data):
    """Model bytes without dress meshes (none in a body since they moved to the dress model)."""
    return drop_meshes(data, dress_meshes(b)) if capturable(b) else data


# ------------------------------------------------------------------------------------ the review sheet
LABELS = {"dwarves": "Dwarves", "elves": "Elves", "men": "Men (and Arnor)", "isengard": "Isengard", "mordor": "Mordor",
          "goblins": "Goblins", "angmar": "Angmar"}


def review(b, version="v1", res="1200x860", spp="48", render=True):
    """build/assets/<faction>/_review/<building>_<version>.jpg: EA against our neutral base (RTS and
    close), then our building as each faction holds it (its dress shown, its cloth in a sample player
    colour). One Blender run (sagekit/blender/capture.py render_review), then ImageMagick. A building
    without a dress (a lair): the build's own EA-against-ours renders, RTS over close."""
    import subprocess
    from . import paths
    from .pipeline import RUN_PY, blender_slot
    from .workspace import Workspace
    ws = Workspace(b)
    if not os.path.exists(ws.path("work", "checks.ok")):
        raise SystemExit("build %s first (its checks must pass)" % b.id)
    if not capturable(b):                       # a lair: EA's against ours, the build's own renders
        dest = os.path.join(paths.BUILD, b.faction, "_review", "%s_%s.jpg" % (b.name, version))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        subprocess.run(["magick"] + [ws.path("renders", "compare_%s.png" % v) for v in ("rts", "close")]
                       + ["-resize", "3200x", "-background", "#1a1a1a", "-append", "-quality", "88", dest], check=True)
        print("review sheet:", dest)
        return dest
    out = ws.path("renders", "capture")
    house = house_path(ws) or ""
    if render:                                  # (False: the sheet again from the last renders)
        with blender_slot():
            r = subprocess.run([paths.BLENDER, "-b", "--python", RUN_PY, "--", "capture_render", b.id, "out=" + out,
                                "house=" + house, "res=" + res, "spp=" + spp], capture_output=True, text=True)
        with open(os.path.join(ws.logs, "capture_render.log"), "w") as fh:
            fh.write(r.stdout + r.stderr)
        if "JOB OK" not in r.stdout:
            raise SystemExit("capture render failed - see %s\n%s" % (fh.name, (r.stdout + r.stderr)[-2000:]))
    dest = os.path.join(paths.BUILD, b.faction, "_review", "%s_%s.jpg" % (b.name, version))
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    def tile(name, label, width, crop):         # framed on the building (its renders leave room round it)
        return ["(", os.path.join(out, name + ".png"), "-gravity", "center", "-crop", crop + "x" + crop + "+0+0",
                "+repage", "-resize", "%dx" % width, "-gravity", "NorthWest", "-font", paths.FONT, "-fill", "white",
                "-undercolor", "#000000a0", "-pointsize", "22", "-annotate", "+8+6", label, ")"]
    title = b.name.replace("_", " ")
    head = [("ea_rts", "EA's %s" % title, "56%"), ("base_rts", "ours: neutral (nobody holds it)", "56%"),
            ("ea_close", "EA's %s, close" % title, "86%"), ("base_close", "ours: neutral, close", "86%")]
    rows = [(head, 800),                        # the key row: every holder side by side at the RTS camera
            ([("%s_rts" % f, LABELS[f], "60%") for f in DRESS], 3200 // len(DRESS)),
            ([("%s_close" % f, "%s, close" % LABELS[f], "86%") for f in list(DRESS)[:4]], 800),
            ([("%s_close" % f, "%s, close" % LABELS[f], "86%") for f in list(DRESS)[4:]], 800)]
    lines = []
    for row, width in rows:
        lines += ["("] + [x for name, label, crop in row for x in tile(name, label, width, crop)] + ["+append", ")"]
    cmd = ["magick"] + lines + ["-background", "#1a1a1a", "-append", "-quality", "88", dest]
    subprocess.run(cmd, check=True)
    print("review sheet:", dest)
    return dest
