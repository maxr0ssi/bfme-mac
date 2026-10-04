"""Blender side of a skinned target (sagekit/skinbody.py): new pieces bound to EA's bones, and the
two exports.

The importer stands a skin at rest in model space with an Armature modifier and one vertex group per
bone (EA's weights). Our solids are added as for a rigid body, a bone at a time: each solid's
`bone` (set by Building.ride; the root, ROOTTRANSFORM, when it has none) becomes the vertex group of
its new vertices at weight 1, so the Armature modifier moves it rigidly with that bone (the root
does not move). Solids never share vertices (sagekit/blender/layout.py add_solids), so a vertex
rides exactly one bone.
"""
import bpy

from .layout import add_solids


def is_skin(obj):
    return any(m.type == "ARMATURE" for m in obj.modifiers)


def add(obj, solids, atlas, world=False, root="ROOTTRANSFORM", bones=()):
    """add_solids, and for a skin each new vertex in its solid's bone's vertex group. bones: the
    skeleton's pivot names (a ride on a bone it lacks fails here, not in the exporter)."""
    if not is_skin(obj):
        return add_solids(obj, solids, atlas, world)
    obj["sagekit_ea_verts"] = len(obj.data.vertices)     # EA's (what `clear` left), ahead of ours
    groups = {}
    for s in solids:
        groups.setdefault(getattr(s, "bone", None) or root, []).append(s)
    added, stats, rides = 0, {}, {}
    names = {n.upper(): n for n in bones}
    for bone, group in groups.items():
        if bones and bone.upper() not in names:
            raise ValueError("%s rides on %s: no such bone in the skeleton" % (obj.name, bone))
        bone = names.get(bone.upper(), bone)
        n0 = len(obj.data.vertices)
        a, st = add_solids(obj, group, atlas, world)
        added += a
        for k, v in st.items():
            stats[k] = stats.get(k, 0) + v
        new = list(range(n0, len(obj.data.vertices)))
        if not new:
            continue
        vg = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
        vg.add(new, 1.0, "REPLACE")
        rides[bone] = rides.get(bone, 0) + len(new)
    print("SKIN rides", rides, flush=True)
    return added, stats


def export(ws, b):
    """A skinned target: the skin export (work/export_skin/) for the fixup, then the body made rigid
    at rest (modifier, vertex groups and parent gone, the transform kept) exported as every rigid body
    is (work/export/). Returns False for a rigid target (nothing done)."""
    import json
    import os

    from ..skinbody import export_skin
    from . import scene
    obj = bpy.data.objects[b.target]
    if not is_skin(obj):
        return False
    missing = [v.index for v in obj.data.vertices if not v.groups]
    if missing:
        raise ValueError("%s: %d vertices ride no bone" % (b.target, len(missing)))
    path = export_skin(ws)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path[:-4] + ".json", "w") as fh:          # the exporter keeps the mesh's vertex order and
        json.dump({"ea": obj.get("sagekit_ea_verts", len(obj.data.vertices)),  # appends what it splits
                   "verts": len(obj.data.vertices)}, fh)
    scene.export_w3d(path, b.target)
    mw = obj.matrix_world.copy()
    for m in [m for m in obj.modifiers if m.type == "ARMATURE"]:
        obj.modifiers.remove(m)
    obj.vertex_groups.clear()
    obj.parent = None
    obj.matrix_world = mw
    scene.export_w3d(ws.export_model, b.target)
    return True
