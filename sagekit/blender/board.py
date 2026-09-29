"""Renders of EA's models as the game draws them, for a faction's style board and palette options
(sagekit/board.py): no Building needed, one Blender process for a list of shots.

    Blender -b --python sagekit/blender/board.py -- <shots.json>

shots.json: [{"model": w3d path, "skeletons": folder or null, "texmap": {texture name: file},
"hidden": [mesh names], "zoom": distance factor, "views": {name: [target, distance, elevation, azimuth, lens]} or null,
"out": prefix}]. With no views, the standard set framed from the visible meshes' bounding box
(blender/render.py AUTO_VIEWS). Each view is written to <out><view>.png.
"""
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import bpy  # noqa: E402

from sagekit.blender import scene  # noqa: E402
from sagekit.blender.render import AUTO_VIEWS, camera, game_material, rig  # noqa: E402
from sagekit.formats.w3d import W3DFile  # noqa: E402


def visible_box(hidden):
    pts = [o.matrix_world @ v.co for o in bpy.data.objects
           if o.type == "MESH" and o.name not in hidden and o.name not in ("Ground",) for v in o.data.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return lo, hi


def shoot(shot, res, samples):
    scene.import_w3d(shot["model"], shot.get("skeletons"))
    hidden = set(shot.get("hidden") or ())
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name in hidden:
            o.hide_render = True
    w3d = W3DFile(shot["model"])
    texmap = {k.lower(): v for k, v in shot["texmap"].items()}
    lo, hi = visible_box(hidden)
    rig(res, samples, hidden)
    for name, mesh in w3d.meshes.items():
        obj = bpy.data.objects.get(name)
        if obj is not None and not obj.hide_render and mesh.textures and all(t.lower() in texmap for t in mesh.textures):
            game_material(obj, mesh, texmap)
    views = shot.get("views")
    if not views:
        centre = [(lo[i] + hi[i]) / 2 for i in range(3)]
        diag = math.dist(lo, hi)
        views = {n: (centre, k * diag * shot.get("zoom", 1.0), e, a, lens) for n, (k, e, a, lens) in AUTO_VIEWS.items()
                 if n in shot.get("auto", ("rts",))}
    sc = bpy.context.scene
    for v, preset in views.items():
        sc.camera, sc.render.filepath = camera(v, *preset), shot["out"] + v + ".png"
        bpy.ops.render.render(write_still=True)
        print("SHOT", sc.render.filepath, flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    spec = json.load(open(argv[0]))
    res = tuple(spec.get("res", (900, 780)))
    for shot in spec["shots"]:
        shoot(shot, res, int(spec.get("samples", 32)))
    print("JOB OK board", flush=True)


main()
