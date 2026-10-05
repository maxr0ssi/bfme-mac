"""Blender side of the capture dress (sagekit/capture.py).

geometry  each faction's dress cloth (`<prefix>_cloth`) leaves the solids for its house-colour mesh
          (work/dress_cloth_<prefix>.json, model space), like the house step's cloth
export    after the paint, each faction's dress faces (by their r2tag) leave the target for a mesh
          of their own, CAP_<P>, with its UVs (one bake, one paint, one sheet); the fixup moves them
          into the dress model (sagekit/capture.py house_model)
render    the review: EA's model, ours neutral, and ours dressed for each capturer in a sample
          player colour (renders/capture/)
"""
import os

import bmesh
import bpy

from .. import capture
from . import scene
from .layout import TAG_ATTR, tag_names, take_faces


def take_cloth(b, obj, solids, ws):
    """Write each faction's dress cloth to its JSON and drop it from `solids`; {faction: faces}."""
    if not capture.capturable(b):
        return {}
    out = {}
    for f, p in capture.DRESS.items():
        out[f] = take_faces(obj, solids, ("%s_%s" % (p, capture.CLOTH),), capture.cloth_path(ws, f), b.world_space)
    print("dress cloth:", out)
    return out


def split(b):
    """Move every faction's dress faces from the target into CAP_<P> (copies of the target object:
    parent, bone, materials and UV layers as the target's; the bake-only ATLAS layer dropped)."""
    if not capture.capturable(b):
        return []
    obj = bpy.data.objects[b.target]
    names = tag_names(b.style.atlas)
    made = []
    for f in capture.DRESS:
        ids = {i for i, n in enumerate(names) if capture.of_tag(n) == f}
        piece = obj.copy()
        piece.data = obj.data.copy()
        piece.name = piece.data.name = capture.mesh_name(f)
        for c in obj.users_collection:
            c.objects.link(piece)
        n = _keep(piece.data, lambda t: t in ids)
        if not n:
            bpy.data.objects.remove(piece)
            continue
        me = piece.data
        if "ATLAS" in me.uv_layers:
            me.uv_layers.remove(me.uv_layers["ATLAS"])
        scene.mirror_uv(me)
        me.uv_layers.active = me.uv_layers["UVMap"]
        me.uv_layers["UVMap"].active_render = True
        made.append((piece.name, n))
    every = {i for i, n in enumerate(names) if capture.of_tag(n)}
    left = _keep(obj.data, lambda t: t not in every)
    print("dress meshes:", made, "body faces left:", left)
    return made


def _keep(me, keep):
    bm = bmesh.new()
    bm.from_mesh(me)
    tl = bm.faces.layers.int.get(TAG_ATTR)
    gone = [f for f in bm.faces if not keep(f[tl] if tl else 0)]
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(me)
    n = len(bm.faces)
    bm.free()
    me.update()
    return n


# sample player colours for the review: a common pick per faction (BFME2's player colours)
SAMPLE = {"dwarves": (0.05, 0.16, 0.62, 1), "elves": (0.06, 0.40, 0.12, 1), "men": (0.70, 0.70, 0.74, 1),
          "isengard": (0.75, 0.68, 0.10, 1), "mordor": (0.62, 0.05, 0.04, 1), "goblins": (0.62, 0.30, 0.04, 1),
          "angmar": (0.30, 0.10, 0.52, 1)}


def render_review(b, out, house_model, res="1200x860", spp="48"):
    """renders/capture/: ea_<view>.png (EA's model), base_<view>.png (ours, neutral), <faction>_<view>.png
    (ours dressed for that capturer, its cloth in a sample player colour)."""
    from ..formats.w3d import W3DFile
    from ..nightlights import day_hidden
    from ..workspace import Workspace
    from .render import camera, game_material, rig, views_for
    ws = Workspace(b)
    res = tuple(int(x) for x in res.split("x"))
    texmap = ws.texture_map()
    os.makedirs(out, exist_ok=True)
    sc = bpy.context.scene

    def shoot(prefix, views):
        presets = views_for(b, bpy.data.objects[b.target])
        for v in views:
            c = camera(v, *presets[v])
            sc.camera, sc.render.filepath = c, os.path.join(out, prefix + v + ".png")
            bpy.ops.render.render(write_still=True)

    for who, path in (("ea", ws.reference_model), ("ours", ws.shipped_model)):
        scene.import_w3d(path, ws.src)
        w3d = W3DFile(path)
        if who == "ours" and house_model and os.path.exists(house_model):
            scene.add_w3d(house_model)
            H = W3DFile(house_model)
            for name, mesh in H.meshes.items():         # the dress pieces: our sheet, as the body
                o = bpy.data.objects.get(name)
                if o is not None and name.startswith("CAP_") and all(t.lower() in texmap for t in mesh.textures):
                    game_material(o, mesh, texmap)
        rig(res, int(spp), day_hidden(b, w3d.data))
        for name, mesh in w3d.meshes.items():
            o = bpy.data.objects.get(name)
            if o is not None and mesh.textures and all(t.lower() in texmap for t in mesh.textures):
                game_material(o, mesh, texmap)
        if who == "ea":
            shoot("ea_", ("rts", "close"))
            continue
        cloth = {}
        for f, colour in SAMPLE.items():
            mat = bpy.data.materials.new("player_" + f)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            bsdf.inputs["Base Color"].default_value = colour
            bsdf.inputs["Roughness"].default_value = 0.85
            o = bpy.data.objects.get(capture.house_mesh(f))
            if o is not None:
                o.data.materials.clear()
                o.data.materials.append(mat)
                cloth[f] = o
        dress = {f: [bpy.data.objects.get(n) for n in (capture.mesh_name(f), capture.house_mesh(f))] for f in capture.DRESS}
        for who_f in [None] + list(capture.DRESS):
            for f, objs in dress.items():
                for o in objs:
                    if o is not None:
                        o.hide_render = f != who_f
                        o.hide_set(False)
            shoot(("%s_" % who_f) if who_f else "base_", ("rts", "close") if who_f in (None,) else ("rts", "close"))
    print("review renders in", out)


def checks(b, ws, r):
    """The capture dress as the game reads it (nothing for an ordinary recipe)."""
    if not capture.capturable(b):
        return
    import numpy as np

    from ..formats.w3d import W3DFile
    from ..formats.w3dframes import IDENTITY, apply, mesh_frames
    from ..formats.w3dpose import hlod
    from .checks import uv_overlap
    r.section("capture dress (sagekit/capture.py)")
    have = capture.present(ws)
    r.check("a dress for every faction, pieces and cloth", sorted(have) == sorted(capture.DRESS)
            and all(len(v) == 2 for v in have.values()), ", ".join("%s %d" % (f, len(v)) for f, v in sorted(have.items())))
    shipped = open(ws.shipped_model, "rb").read()
    W, E = W3DFile(shipped), W3DFile(ws.source_model)
    r.check("the body carries no dress (it is the dress model's)", not set(W.meshes) & set(capture.dress_meshes(b)), "")
    H = W3DFile(open(capture.house_path(ws), "rb").read())
    bones = hlod(H.data)[2]
    own = sorted(b.texture_names().values())
    for f, names in sorted(have.items()):
        for n in names:
            m = H.meshes[n]
            tex_ok = m.textures == own if n.startswith("CAP_") else bool(m.textures) and all("house" in t.lower() for t in m.textures)
            r.check("%s: %s hidden until captured, on the root, %s" % (b.dress_house_model, n, ", ".join(m.textures)),
                    _hidden(m.bytes) and bones.get(n) == 0 and tex_ok, "bone %s" % bones.get(n))
    F = mesh_frames(shipped, lambda x: open(os.path.join(ws.src, x), "rb").read()).get(b.target, IDENTITY)
    E_pts = [apply(F, v) for v in E.meshes[b.target].verts]          # (the dress model is in model space)
    lo = [min(v[i] for v in E_pts) for i in range(3)]
    hi = [max(v[i] for v in E_pts) for i in range(3)]
    pts = [v for n, m in H.meshes.items() for v in m.verts]
    if pts:
        dlo = [min(p[i] for p in pts) for i in range(3)]
        dhi = [max(p[i] for p in pts) for i in range(3)]
        e = b.footprint_margin + 1e-3
        r.check("dress inside EA's footprint%s" % (" + %.1f" % b.footprint_margin if b.footprint_margin else ""),
                all(dlo[i] >= lo[i] - e and dhi[i] <= hi[i] + e for i in (0, 1)),
                "x [%.1f, %.1f] y [%.1f, %.1f]" % (dlo[0], dhi[0], dlo[1], dhi[1]))
        r.check("dress height within %d%% growth" % (100 * b.max_z_growth),
                dhi[2] <= lo[2] + (hi[2] - lo[2]) * (1 + b.max_z_growth) + 1e-3, "top %.1f" % dhi[2])
    caps = [H.meshes[n] for n in H.meshes if n.startswith("CAP_")]
    uv, tris, off = [], [], 0
    for m in [W.meshes[b.target]] + caps:
        uv += list(m.uv)
        tris += [(x + off, y + off, z + off) for x, y, z in m.tris]
        off += len(m.uv)
    uv, tris = np.array(uv), np.array(tris)
    cov, over = uv_overlap(uv, tris)
    r.check("body and dress share one layout, no overlap", over / max(cov, 1) < 1e-4 and bool(((uv >= 0) & (uv <= 1)).all()),
            "overlap %.5f%%" % (100 * over / max(cov, 1)))
    r.info("dress triangles", "%d pieces, %d cloth (body %d)" % (sum(len(m.tris) for m in caps),
                                                              sum(len(m.tris) for n, m in H.meshes.items() if n.startswith("HC_")),
                                                              len(W.meshes[b.target].tris)))
    _ini_checks(b, ws, r, have)


def _hidden(mesh_bytes):
    import struct

    from ..formats.w3d import MESH_HEADER3, chunks
    for t, o, s, _ in chunks(mesh_bytes, 8, len(mesh_bytes)):
        if t == MESH_HEADER3:
            return bool(struct.unpack_from("<I", mesh_bytes, o + 12)[0] & capture.HIDDEN)
    return False


def _ini_checks(b, ws, r, have):
    import re
    from ..game import Install
    g = Install()
    every = {n for names in have.values() for n in names}
    from ..fire_systems import MEMBER as FIRE_SYSTEMS
    for member in b.ini_ops(g, ws.variants):
        if member == FIRE_SYSTEMS:                  # the fire's particle INI (sagekit/fire.py) holds no Draws
            continue
        path = ws.out(member)
        text = open(path, encoding="latin-1").read() if os.path.exists(path) else ""
        for f, names in sorted(have.items()):
            tag = "ModuleTag_SagekitCapture" + capture.DRESS[f].upper()
            m = re.search(r"Behavior\s*=\s*SubObjectsUpgrade\s+%s\s*\n(.*?)\n\s*End" % tag, text, re.S)
            body = m.group(1) if m else ""
            trig = re.search(r"TriggeredBy\s*=\s*([^\n;]*)", body)
            show = re.search(r"ShowSubObjects\s*=\s*([^\n;]*)", body)
            hide = re.search(r"HideSubObjects\s*=\s*([^\n;]*)", body)
            ok = bool(m and trig and show) and trig.group(1).split() == list(capture.UPGRADES[f]) \
                and sorted(show.group(1).split()) == sorted(names) \
                and sorted(hide.group(1).split() if hide else []) == sorted(every - set(names))
            r.check("%s: %s shows %s's dress on %s" % (member.split("\\")[-1], tag, f, " ".join(capture.UPGRADES[f])),
                    ok, " ".join(names))
