"""Renders of a lifecycle model at the frames the player sees (sagekit/lifecycle.py): EA's model as
the installed faction shows it today (recoloured sheets) and ours, each posed by its animation.

The add-on imports the model at rest; every mesh is then moved to its pose here (the same pose
code the lifecycle step builds with, sagekit/formats/w3dpose.py): positions, normals and the
tangent frame the normal map is read with. Meshes on bones the animation hides are not drawn.
The camera is the building's healthy "rts" view, so every frame and state is framed alike."""
import json
import math
import os

import bpy
import numpy as np

from .. import workspace
from ..formats.w3d import W3DFile
from ..game import Install
from . import render, scene
from .lifecycle import Model


SPREAD = 1.4


class Posed:
    """The W3D bytes' mesh data with its tangent frame posed (what game_material reads)."""

    def __init__(self, mesh, R):
        self.textures = mesh.textures
        rot = lambda vs: [tuple(r @ np.array(v)) for r, v in zip(R, vs)] if vs else vs   # noqa: E731
        self.tangents, self.bitangents = rot(mesh.tangents), rot(mesh.bitangents)


def imported(path, skeletons):
    """Import a model once, its meshes freed from the rig (they are posed by hand)."""
    scene.import_w3d(path, skeletons)
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            for mod in list(obj.modifiers):
                obj.modifiers.remove(mod)
            obj.parent = None
            obj.animation_data_clear()
            obj.matrix_world = ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))


def pose_meshes(m, frame, hidden=()):
    """Move the imported meshes of Model m to a frame (None: rest); returns {mesh: Posed}. Meshes
    on bones the frame hides, and `hidden` (a day render's night meshes), are not drawn."""
    pose = m.pose(frame)
    out = {}
    for name, mesh in m.w3d.meshes.items():
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "MESH":
            continue
        bones = m.vertex_bones(name)
        R = [np.array(pose[0][b]).reshape(3, 4)[:, :3] for b in bones]
        V = m.world(name, pose)
        me = obj.data
        if len(me.vertices) != len(V):
            print("WARN %s: %d vertices imported, %d in the file - left at rest" % (name, len(me.vertices), len(V)))
            continue
        me.vertices.foreach_set("co", V.astype(np.float32).ravel())
        if "custom_normal" in me.attributes:            # the file's normals, set at rest: the posed
            me.attributes.remove(me.attributes["custom_normal"])    # geometry's own shade it instead
        me.shade_smooth()
        me.update()
        obj.hide_render = not pose[1][bones[0]] or name in hidden
        out[name] = Posed(mesh, R)
    return out


def rts_camera(b, ws):
    """The healthy building's rts view: (centre, distance, elevation, azimuth, lens)."""
    if b.views and "rts" in b.views:                    # a little further out: the rubble falls wide
        c, d, e, a, lens = b.views["rts"]
        return c, d * SPREAD, e, a, lens
    h = Model(ws.source_model)
    V = h.world(b.target, h.pose(None))
    lo, hi = V.min(0), V.max(0)
    k, e, a, lens = render.AUTO_VIEWS["rts"]
    return tuple((lo + hi) / 2), k * math.dist(lo, hi) * SPREAD, e, a, lens


def render_model(b, model, who, out, res="1100x760", spp="48", **textures):
    """One side (who: "ea" or "ours") of a lifecycle model at each frame the player sees; one
    Blender process per side (the add-on does not survive importing an animated model twice)."""
    ws = workspace.Workspace(b)
    entry = next(m for m in json.load(open(ws.path("work", "lifecycle.json")))["models"] if m["model"] == model)
    plan = next(e for e in json.load(open(ws.path("work", "lifecycle_plan.json"))) if e["model"] == model)
    src = ws.path("src")
    skel = os.path.join(src, plan["skeleton"]) if plan["skeleton"] else None
    anim = os.path.join(src, plan["animation"]["file"]) if plan["animation"] else None
    texmap = ws.texture_map()
    texmap.update({k.lower(): v for k, v in textures.items()})
    path = os.path.join(src, model.lower() + ".w3d") if who == "ea" else ws.out(Install.model_path(b.shipped_name(model)))
    ref = ws.path("work", "ref", model.lower() + ".w3d")    # a derived model's src/ copy may be a chained
    if who == "ea" and entry.get("derived") and os.path.exists(ref):    # base's: EA's is the render step's
        path = ref
    imported(path, src)
    m = Model(path, skel, anim)
    from ..nightlights import day_hidden               # night meshes: the game hides them by day
    hidden = set(day_hidden(b, m.data))
    for o in bpy.data.objects:                          # EA's W3D boxes (B:...OBBOX), which the add-on imports
        if o.type == "MESH" and o.name not in m.w3d.meshes:     # as meshes: collision, never drawn in game
            o.hide_render = True
    render.rig(tuple(int(x) for x in res.split("x")), int(spp), hidden)
    sc = bpy.context.scene
    sc.camera = render.camera("rts", *rts_camera(b, ws))
    for f in entry["views"]:
        posed = pose_meshes(m, f, hidden)
        for name, mesh in m.w3d.meshes.items():
            obj = bpy.data.objects.get(name)
            if obj is not None and name in posed and mesh.textures and all(t.lower() in texmap for t in mesh.textures):
                render.game_material(obj, posed[name], texmap)
        sc.render.filepath = os.path.join(out, "%s_%s_%s.png" % (model.lower(), who, "rest" if f is None else f))
        bpy.ops.render.render(write_still=True)
