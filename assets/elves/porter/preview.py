"""Offline Elven builder poses from the original shared Gondor porter animations."""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from assets.dwarves.porter.preview import animation
from sagekit.blender import render, scene
from sagekit.blender.lifecycle import Model

STATES = {"portrait": ("idla", 0), "rts": ("idla", 0), "run": ("runa", 8),
          "walk": ("wlka", 8), "water": ("fira", 38), "death": ("diea", 45),
          "fall": ("dieb", 10), "idle": ("idlb", 30)}


def run():
    who, state = sys.argv[sys.argv.index("--") + 1:][:2]
    folder = ROOT / "build/assets/elves/porter"
    src = folder / "src"
    model = src / "euporter_skn.w3d" if who == "original" else folder / "work/euporter_skn.w3d"
    textures = json.loads((folder / ("textures.json" if who == "original" else "work/textures.json")).read_text())
    anim, frame = STATES[state]
    m = Model(str(model), str(src / "guporter_skl.w3d"))
    m.anim = animation((src / ("guporter_" + anim + ".w3d")).read_bytes())
    for f in range(m.anim.frames):
        matrices, _ = m.pose(f)
        assert np.isfinite(np.array(matrices)).all()
    assert np.max(np.abs(np.array(m.pose(0)[0])-np.array(m.pose(m.anim.frames//2)[0]))) > .001
    (folder / "work").mkdir(exist_ok=True)
    (folder / "work" / ("motion_" + anim + ".txt")).write_text(
        "PASS: original motion channels decoded; finite transforms at all frames; animation moves.\n")
    pose = m.pose(min(frame, m.anim.frames-1))
    scene.clear()
    for name, mesh in m.w3d.meshes.items():
        bones = m.vertex_bones(name)
        faces = [t for t in mesh.tris if all(pose[1][bones[v]] for v in t)]
        if not faces:
            continue
        me = bpy.data.meshes.new(name)
        me.from_pydata(m.world(name, pose).tolist(), [], faces)
        me.update()
        obj = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(obj)
        uv = me.uv_layers.new(name="UVMap")
        for lp in me.loops:
            uv.data[lp.index].uv = mesh.uv[lp.vertex_index]
        if name == "ELF":
            me.shade_smooth()
        render.game_material(obj, mesh, textures)
        # These legacy opaque meshes ignore texture alpha in game. Blender otherwise
        # premultiplies the stored diffuse colours, turning most of EUWorker black.
        for node in obj.data.materials[0].node_tree.nodes:
            if node.type == "TEX_IMAGE":
                node.image.alpha_mode = "NONE"
    render.rig((1200, 1100) if state == "portrait" else (1100, 950), 32)
    sc = bpy.context.scene
    sc.camera = render.camera("builder", (8, 0, 11), 76 if state == "portrait" else 84,
                              22 if state == "portrait" else 48, -38, 52)
    if state in ("death", "fall"):
        reference=Model(str(src/"euporter_skn.w3d"),str(src/"guporter_skl.w3d"))
        reference.anim=m.anim
        rp=reference.pose(min(frame,m.anim.frames-1))
        points=np.concatenate([reference.world(n,rp) for n in reference.w3d.meshes])
        lo,hi=points.min(axis=0),points.max(axis=0)
        sc.camera = render.camera("fallen builder", ((lo+hi)/2).tolist(),
                                  max(90,float(np.linalg.norm(hi-lo))*2.2),48,-38,52)
    out = folder / "renders"
    out.mkdir(exist_ok=True)
    sc.render.filepath = str(out / (who + "_" + state + ".png"))
    bpy.ops.render.render(write_still=True)
    print("PREVIEW OK", who, state)


if __name__ == "__main__":
    run()
