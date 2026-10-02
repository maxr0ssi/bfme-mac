"""Blender side of assets/cah/kit/render.py: each job poses one CaH model from EA's animation bytes,
draws only the sub-objects the job shows (the body plus the chosen parts, as the game's
SubObjectsUpgrades do), tints the masked areas with the hero's three colours, and renders.
blender -b --python sagekit/blender/cah_pose.py -- <jobs.json>"""
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


def tint(obj, mask_path, colours):
    """Preview of the CaH colours: tint = R*c1 + G*c2 + B*c3 from the mask's channels, mixed
    over the texture by the mask's alpha (EA's masks carry the shading in each channel)."""
    nt = obj.data.materials[0].node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    link = next(l for l in nt.links if l.to_socket == bsdf.inputs["Base Color"])
    base = link.from_socket
    uv = next(n for n in nt.nodes if n.type == "UVMAP")
    N = nt.nodes.new
    mt = N("ShaderNodeTexImage")
    mt.image = bpy.data.images.load(mask_path, check_existing=True)
    mt.image.colorspace_settings.name = "Non-Color"
    mt.image.alpha_mode = "STRAIGHT"
    nt.links.new(uv.outputs[0], mt.inputs[0])
    sep = N("ShaderNodeSeparateColor")
    nt.links.new(mt.outputs["Color"], sep.inputs[0])
    acc = None
    for ch, c in zip(("Red", "Green", "Blue"), colours):
        mul = N("ShaderNodeVectorMath")
        mul.operation = "SCALE"
        mul.inputs[0].default_value = [x / 255 for x in c]
        nt.links.new(sep.outputs[ch], mul.inputs["Scale"])
        if acc is None:
            acc = mul
        else:
            add = N("ShaderNodeVectorMath")
            add.operation = "ADD"
            nt.links.new(acc.outputs[0], add.inputs[0])
            nt.links.new(mul.outputs[0], add.inputs[1])
            acc = add
    mix = N("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(mt.outputs["Alpha"], mix.inputs["Factor"])
    nt.links.new(base, mix.inputs[6])
    nt.links.new(acc.outputs[0], mix.inputs[7])
    nt.links.remove(link)
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])


def run(j):
    m = Model(j["model"], j["skeleton"])
    m.anim = animation(Path(j["anim"]).read_bytes())
    frame = min(j["frame"], m.anim.frames - 1)
    pose = m.pose(frame)
    for f in range(0, m.anim.frames, 5):
        assert np.isfinite(np.array(m.pose(f)[0])).all()
    scene.clear()
    shown = [n.upper() for n in j["show"]]
    pts = []
    for name, mesh in m.w3d.meshes.items():
        if name not in shown:
            continue
        bones = m.vertex_bones(name)
        faces = [t for t in mesh.tris if all(pose[1][bones[v]] for v in t)]
        world = m.world(name, pose)
        pts.append(world)
        me = bpy.data.meshes.new(name)
        me.from_pydata(world.tolist(), [], faces)
        me.update()
        obj = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(obj)
        uv = me.uv_layers.new(name="UVMap")
        for lp in me.loops:
            uv.data[lp.index].uv = mesh.uv[lp.vertex_index]
        if mesh.normals:
            me.shade_smooth()
        render.game_material(obj, mesh, j["textures"])
        for node in obj.data.materials[0].node_tree.nodes:     # EA's CaH sheets keep data in alpha
            if node.type == "TEX_IMAGE":
                node.image.alpha_mode = "NONE"
        tex = [t.lower() for t in mesh.textures if "nrm" not in t.lower()][0]
        if j.get("colours") and tex in j["masks"]:
            tint(obj, j["masks"][tex], j["colours"])
    render.rig(tuple(j["size"]), j.get("samples", 32))
    allp = np.concatenate(pts)
    if j.get("focus") == "head":                # the same head shot whatever the helmet
        hb = m.skel.index(j.get("head_bone", "B_HEAD"))
        mat = np.array(pose[0][hb]).reshape(3, 4)
        target = (mat[:, 3] + np.array([0.6, 0, 1.2]) * (mat[2, 3] / 14.8)).tolist()
        dist = 15.0 * mat[2, 3] / 14.8
    elif j.get("focus") == "part":              # a part close-up at a fixed distance
        sel = np.concatenate([m.world(n, pose) for n in m.w3d.meshes if n.upper() in [x.upper() for x in j["part"]]])
        target = ((sel.min(axis=0) + sel.max(axis=0)) / 2).tolist()
        dist = j["dist"]
    else:
        lo, hi = allp.min(axis=0), allp.max(axis=0)
        target = ((lo + hi) / 2).tolist()
        dist = float(np.linalg.norm(hi - lo)) * j.get("scale", 2.1)
    sc = bpy.context.scene
    sc.camera = render.camera(j["name"], target, dist, j.get("elevation", 12), j.get("azimuth", 28), j.get("lens", 52))
    sc.render.filepath = j["out"]
    bpy.ops.render.render(write_still=True)
    print("CAH RENDER OK", j["out"], flush=True)


if __name__ == "__main__":
    for job in json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text()):
        run(job)
