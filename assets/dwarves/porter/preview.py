"""Blender preview of the selectable builder, posed from the actual W3D animation bytes.

Invoked by unit.py; never loads the game. Both sides use identical cameras and lighting.
"""
import json
import importlib
import io
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sagekit.blender import render, scene
from sagekit.blender.lifecycle import Model
from sagekit.formats.w3dpose import Animation
from sagekit.formats.w3d import chunks


def animation(data):
    """Use the installed OpenSAGE decoder for motion channels the building reader lacks."""
    a = Animation(data)
    module = importlib.import_module("io_mesh_w3d.w3d.structs.compressed_animation")
    decode = importlib.import_module("io_mesh_w3d.w3d.adaptive_delta").decode
    for t,o,s,_ in chunks(data,0,len(data)):
        if t != 0x280:
            continue
        for tag,p,size,_ in chunks(data,o+8,o+8+s):
            if tag != 0x284:
                continue
            c = module.MotionChannel.read(io.BytesIO(data[p+8:p+8+size]))
            if c.delta_type:
                values = decode(c.type,c.vector_len,c.num_time_codes,c.data.scale,c.data.data)
                values = list(enumerate(values))
            else:
                values = [(d.time_code,d.value) for d in c.data]
            if c.type == 15:
                a.vis[c.pivot] = (True,[(f,bool(v)) for f,v in values],True)
            elif c.type in (0,1,2,6):
                a._add(c.pivot,c.type,[(f,(v.x,v.y,v.z,v.w) if c.type==6 else (v,),False) for f,v in values])
            else:
                raise ValueError("Unsupported motion channel: %s" % c.type)
    assert a.keys, "An animated preview must contain decoded motion, never silently show the rest pose"
    return a


def run():
    args = sys.argv[sys.argv.index("--") + 1:]
    who, state = args[:2]
    folder = ROOT / "build/assets/dwarves/porter"
    src = folder / "src"
    model = src / "duporter_skn.w3d" if who == "original" else folder / "work/duporter_skn.w3d"
    textures = json.loads((folder / ("textures.json" if who == "original" else "work/textures.json")).read_text())
    anim, frame = {"portrait": ("idla", 0), "rts": ("idla", 0), "run": ("runa", 8),
                   "work": ("wrkb", 23), "water": ("fira", 38), "death": ("diea", 45)}[state]
    m = Model(str(model), str(src / "duporter_skl.w3d"))
    m.anim = animation((src / ("duporter_" + anim + ".w3d")).read_bytes())
    for f in range(m.anim.frames):
        matrices,_ = m.pose(f)
        assert np.isfinite(np.array(matrices)).all()
    first,last = np.array(m.pose(0)[0]),np.array(m.pose(m.anim.frames//2)[0])
    assert np.max(np.abs(first-last)) > .001, "Animation decoded without movement"
    (folder/"work"/("motion_"+anim+".txt")).write_text("PASS: OpenSAGE motion channels decoded; finite poses at all frames; animation moves.\n")
    pose = m.pose(frame)
    scene.clear()
    for name, mesh in m.w3d.meshes.items():
        bones = m.vertex_bones(name)
        verts = m.world(name, pose)
        faces = [t for t in mesh.tris if all(pose[1][bones[v]] for v in t)]
        if not faces:
            continue
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts.tolist(), [], faces)
        me.update()
        obj = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(obj)
        uv = me.uv_layers.new(name="UVMap")
        for lp in me.loops:
            uv.data[lp.index].uv = mesh.uv[lp.vertex_index]
        if name in ("DWARF", "HELM", "POUCHES"):
            me.shade_smooth()
        render.game_material(obj, mesh, textures)
    render.rig((1200, 1050) if state == "portrait" else (1100, 900), 32)
    sc = bpy.context.scene
    target = (8, 0, 9)
    sc.camera = render.camera("builder", target, 66 if state == "portrait" else 77,
                              22 if state == "portrait" else 48, -38, 52)
    if state == "death":
        sc.camera = render.camera("death", (8, 0, 5), 80, 48, -38, 52)
    if state == "work":
        sc.camera = render.camera("work", (14, 0, 8), 105, 48, -38, 52)
    out = folder / "renders"
    out.mkdir(exist_ok=True)
    sc.render.filepath = str(out / (who + "_" + state + ".png"))
    bpy.ops.render.render(write_still=True)
    print("PREVIEW OK", who, state)


if __name__ == "__main__":
    run()
