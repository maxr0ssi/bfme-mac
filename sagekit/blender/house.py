"""Blender side of the house-colour step (sagekit/house.py): EA's house-colour model with the
buildings' cloth added to its HC_ mesh, exported for the fixup.

    Blender -b --python sagekit/blender/house.py -- <EA model.w3d> <out.w3d> <HC mesh> <u0,v0,u1,v1> keep|fresh <cloth.json>...

`fresh`: the mesh's own faces (a template's flag) are removed first.

Each cloth polygon (world space) is brought into the mesh's own space and mapped onto the rect of
EA's banner texture (its folded cloth inside the frame): across the face horizontally, top of the
cloth at the rect's top. The game tints the whole HC_ mesh in the player's colour.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector as V  # noqa: E402

from sagekit.blender import scene  # noqa: E402


def add_cloth(obj, polys, rect, fresh=False):
    u0, v0, u1, v1 = rect
    inv = obj.matrix_world.inverted()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    if fresh:
        bmesh.ops.delete(bm, geom=list(bm.verts), context="VERTS")
    uvl = bm.loops.layers.uv["UVMap"]
    added = 0
    for poly in polys:
        pts = [inv @ V(p) for p in poly]
        n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        side = V((0, 0, 1)).cross(n)                    # horizontal direction across the face
        if side.length < 1e-6:
            side = V((1, 0, 0))
        side.normalize()
        s = [p.dot(side) for p in pts]
        z = [p.z for p in pts]
        ds, dz = max(max(s) - min(s), 1e-6), max(max(z) - min(z), 1e-6)
        face = bm.faces.new([bm.verts.new(p) for p in pts])
        for lp, si, zi in zip(face.loops, s, z):
            lp[uvl].uv = (u0 + (u1 - u0) * (si - min(s)) / ds, v0 + (v1 - v0) * (zi - min(z)) / dz)
        added += 1
    bm.normal_update()
    bm.to_mesh(obj.data)
    bm.free()
    return added


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, out, mesh, rect = argv[0], argv[1], argv[2], [float(x) for x in argv[3].split(",")]
    scene.import_w3d(src)
    obj = bpy.data.objects[mesh]
    polys = [p for f in argv[5:] for p in json.load(open(f))]
    print("cloth faces", add_cloth(obj, polys, rect, argv[4] == "fresh"))
    scene.export_w3d(out, mesh)
    print("HOUSE OK", flush=True)


main()
