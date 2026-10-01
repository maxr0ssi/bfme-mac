"""Blender side of sagekit/units/render.py: each job poses a unit from EA's animation bytes and
renders it. blender -b --python unit_pose.py -- <jobs.json>; both sides of a comparison share the
camera and lighting. Never loads the game."""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sagekit.blender import render, scene  # noqa: E402
from sagekit.blender.lifecycle import Model  # noqa: E402
from sagekit.units.motion import animation  # noqa: E402


def camera(j, anim, frame):
    v = j["view"]
    target, dist = v["target"], v["distance"]
    if v["fit"]:                                # framed on EA's model in this pose
        ref = Model(j["reference"], j["skeleton"])
        ref.anim = anim
        rp = ref.pose(frame)
        points = np.concatenate([ref.world(n, rp) for n in ref.w3d.meshes])
        lo, hi = points.min(axis=0), points.max(axis=0)
        target, dist = ((lo + hi) / 2).tolist(), max(v["fit_min"], float(np.linalg.norm(hi - lo)) * v["fit_scale"])
    return render.camera(j["state"], target, dist, v["elevation"], v["azimuth"], v["lens"])


def run(j):
    m = Model(j["model"], j["skeleton"])
    m.anim = animation(Path(j["anim"]).read_bytes())
    for f in range(m.anim.frames):
        matrices, _ = m.pose(f)
        assert np.isfinite(np.array(matrices)).all()
    assert np.max(np.abs(np.array(m.pose(0)[0]) - np.array(m.pose(m.anim.frames // 2)[0]))) > .001, \
        "Animation decoded without movement"
    Path(j["motion"]).write_text("PASS: OpenSAGE motion channels decoded; finite poses at all frames; animation moves.\n")
    frame = min(j["frame"], m.anim.frames - 1)
    pose = m.pose(frame)
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
        if name in j["smooth"]:
            me.shade_smooth()
        render.game_material(obj, mesh, j["textures"])
        if j["opaque"]:
            for node in obj.data.materials[0].node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    node.image.alpha_mode = "NONE"
    render.rig(tuple(j["view"]["size"]), 32)
    sc = bpy.context.scene
    sc.camera = camera(j, m.anim, frame)
    sc.render.filepath = j["out"]
    bpy.ops.render.render(write_still=True)
    print("PREVIEW OK", j["who"], j["state"], flush=True)


if __name__ == "__main__":
    for job in json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text()):
        run(job)
