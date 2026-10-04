"""A stretch of a map with its scenery as the map places it, rendered twice: EA's sheets, then ours
(sagekit/scenery_review.py map_area). Each model is imported once into a collection of its own,
left out of the view layer, and drawn by one collection instance per placement (x, y, angle; the
terrain is left out, so every object stands on the ground plane).

    Blender -b --python sagekit/blender/scenery_map.py -- <spec.json>

spec: {"models": {name: {"path", "skeletons", "ea": texmap, "our": texmap, "hidden": [mesh]}},
"place": [[name, x, y, angle]], "size": units across, "out": prefix}: <out>ea.png and <out>our.png.
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import bpy  # noqa: E402

from sagekit.blender import scene  # noqa: E402
from sagekit.blender.render import camera, game_material, rig  # noqa: E402
from sagekit.formats.w3d import W3DFile  # noqa: E402


def load(name, m):
    """Import a model into a collection of its own; {mesh name: object} of what it drew."""
    coll = bpy.data.collections.new("M_" + name)
    bpy.context.scene.collection.children.link(coll)
    layer = bpy.context.view_layer.layer_collection.children[coll.name]
    bpy.context.view_layer.active_layer_collection = layer
    before = set(bpy.data.objects)
    scene.add_w3d(m["path"], m.get("skeletons"))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:                                       # everything the import made, in this collection
        for c in list(o.users_collection):
            if c is not coll:
                c.objects.unlink(o)
        if coll not in o.users_collection:
            coll.objects.link(o)
    hidden = set(m.get("hidden") or ())
    meshes = {}
    for o in new:
        base = re.sub(r"\.\d{3}$", "", o.name)
        if o.type == "MESH" and (base in hidden or o.hide_render):
            bpy.data.objects.remove(o)
        elif o.type == "MESH":
            meshes[base] = o
    layer.exclude = True
    return coll, meshes


def paint(models, loaded, who):
    for name, m in models.items():
        w3d = W3DFile(m["path"])
        texmap = {k.lower(): v for k, v in m[who].items()}
        for mesh_name, mesh in w3d.meshes.items():
            obj = loaded[name][1].get(mesh_name)
            if obj is not None and mesh.textures and all(t.lower() in texmap for t in mesh.textures):
                game_material(obj, mesh, texmap)


def main():
    spec = json.load(open(sys.argv[sys.argv.index("--") + 1]))
    scene.clear()
    models = spec["models"]
    loaded = {name: load(name, m) for name, m in models.items()}
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection
    for i, (name, x, y, angle) in enumerate(spec["place"]):
        inst = bpy.data.objects.new("P%d_%s" % (i, name), None)
        inst.instance_type, inst.instance_collection = "COLLECTION", loaded[name][0]
        inst.location, inst.rotation_euler = (x, y, 0.0), (0.0, 0.0, angle)
        bpy.context.scene.collection.objects.link(inst)
    rig((1800, 1280), 48)
    size = spec["size"]
    sc = bpy.context.scene
    sc.camera = camera("rts", (0.0, 0.0, 0.0), 1.45 * size, 50, -38, 50)
    for who in ("ea", "our"):
        paint(models, loaded, who)
        sc.render.filepath = spec["out"] + who + ".png"
        bpy.ops.render.render(write_still=True)
        print("SHOT", sc.render.filepath, flush=True)
    print("JOB OK scenery map", flush=True)


main()
