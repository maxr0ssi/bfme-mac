"""Render a model the way the game draws it: every mesh gets the textures its W3D bytes name, and
the normal map is applied like NormalMapped.fx with the tangent frame stored in the file
(n = (2r-1)(-binormal) + (2g-1)(-tangent) + (2b-1) normal; see sagekit/paint/imageio.py).

Cameras: a Building's `views`, else framed from the model's bounding box so any building gets the
standard set (rts: the usual RTS angle, close: three-quarter close-up, ingame: BFME2's own pitch
and zoom, the whole building small).
"""
import math

import bpy
import mathutils
import numpy as np

from . import scene

# name: (distance in bounding-box diagonals, elevation, azimuth, lens)
AUTO_VIEWS = {"rts": (2.2, 50, -38, 50), "close": (1.3, 24, -30, 45), "ingame": (5.0, 53, -62, 50)}


def rig(res, samples, hidden=()):
    sc = bpy.context.scene
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name in hidden:
            o.hide_render = True
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    scene.use_gpu(sc)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    w = bpy.data.worlds.get("W") or bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    bg, out = nt.nodes.new("ShaderNodeBackground"), nt.nodes.new("ShaderNodeOutputWorld")
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "HOSEK_WILKIE"
    sky.sun_direction = (-0.5, 0.4, 0.75)
    sky.turbidity = 3
    nt.links.new(sky.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 0.35
    nt.links.new(bg.outputs[0], out.inputs[0])
    sd = bpy.data.lights.new("Sun", "SUN")          # warm sun from the camera's upper left
    sd.energy, sd.color, sd.angle = 4.2, (1.0, 0.86, 0.68), math.radians(2.0)
    sun = bpy.data.objects.new("Sun", sd)
    bpy.context.collection.objects.link(sun)
    a, e = math.radians(285), math.radians(42)
    d = mathutils.Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
    sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    me = bpy.data.meshes.new("GroundM")
    s = 2000
    me.from_pydata([(-s, -s, -0.05), (s, -s, -0.05), (s, s, -0.05), (-s, s, -0.05)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new("Ground", me)
    bpy.context.collection.objects.link(g)
    gm = bpy.data.materials.new("GroundMat")
    gm.use_nodes = True
    b = gm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.16, 0.15, 0.12, 1)
    b.inputs["Roughness"].default_value = 0.95
    me.materials.append(gm)


def camera(name, target, dist, elev, azim, lens=50):
    cd = bpy.data.cameras.new(name)
    cd.lens, cd.clip_end = lens, 5000
    c = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(c)
    t, e, a = mathutils.Vector(target), math.radians(elev), math.radians(azim)
    c.location = t + mathutils.Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))) * dist
    c.rotation_euler = (t - c.location).to_track_quat("-Z", "Y").to_euler()
    return c


def views_for(building, target_obj):
    if building.views:
        return building.views
    cs = [target_obj.matrix_world @ v.co for v in target_obj.data.vertices]
    lo = [min(c[i] for c in cs) for i in range(3)]
    hi = [max(c[i] for c in cs) for i in range(3)]
    centre = [(lo[i] + hi[i]) / 2 for i in range(3)]
    diag = math.dist(lo, hi)
    return {n: (centre, k * diag, e, a, lens) for n, (k, e, a, lens) in AUTO_VIEWS.items()}


def game_material(obj, mesh, texmap):
    """Principled material with the file's own diffuse / normal textures and tangent frame."""
    me = obj.data
    names = [t.lower() for t in mesh.textures]
    diff = [t for t in names if "nrm" not in t][0]
    nrm = next((t for t in names if "nrm" in t), None)
    for nm, vecs in (("gameT", mesh.tangents), ("gameB", mesh.bitangents)) if mesh.tangents else ():
        a = me.attributes.get(nm) or me.attributes.new(nm, "FLOAT_VECTOR", "POINT")
        a.data.foreach_set("vector", np.array(vecs, np.float32).ravel())
    mat = bpy.data.materials.new(obj.name + ".game")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    out, bsdf = N("ShaderNodeOutputMaterial"), N("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.8
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    uv = N("ShaderNodeUVMap")
    uv.uv_map = "UVMap"

    def tex(path, noncolor):
        n = N("ShaderNodeTexImage")
        n.image = bpy.data.images.load(path, check_existing=False)
        n.image.colorspace_settings.name = "Non-Color" if noncolor else "sRGB"
        nt.links.new(uv.outputs[0], n.inputs[0])
        return n
    nt.links.new(tex(texmap[diff], False).outputs[0], bsdf.inputs["Base Color"])
    me.materials.clear()
    me.materials.append(mat)
    if nrm is None or not mesh.tangents:
        return                                  # no normal-map pass: the geometry's own normals
    tn = tex(texmap[nrm], True)
    sep, m2 = N("ShaderNodeSeparateXYZ"), N("ShaderNodeVectorMath")
    m2.operation = "MULTIPLY_ADD"
    m2.inputs[1].default_value, m2.inputs[2].default_value = (2, 2, 2), (-1, -1, -1)
    nt.links.new(tn.outputs[0], m2.inputs[0])
    nt.links.new(m2.outputs[0], sep.inputs[0])

    def world(attr):
        a, vt, nz = N("ShaderNodeAttribute"), N("ShaderNodeVectorTransform"), N("ShaderNodeVectorMath")
        a.attribute_type, a.attribute_name = "GEOMETRY", attr
        vt.vector_type, vt.convert_from, vt.convert_to = "VECTOR", "OBJECT", "WORLD"
        nz.operation = "NORMALIZE"
        nt.links.new(a.outputs["Vector"], vt.inputs[0])
        nt.links.new(vt.outputs[0], nz.inputs[0])
        return nz.outputs[0]

    def scaled(vec, comp, sign):
        s, mul = N("ShaderNodeVectorMath"), N("ShaderNodeMath")
        s.operation, mul.operation = "SCALE", "MULTIPLY"
        mul.inputs[1].default_value = sign
        nt.links.new(sep.outputs[comp], mul.inputs[0])
        nt.links.new(vec, s.inputs[0])
        nt.links.new(mul.outputs[0], s.inputs["Scale"])
        return s.outputs[0]
    terms = [scaled(world("gameB"), 0, -1.0), scaled(world("gameT"), 1, -1.0),
             scaled(N("ShaderNodeNewGeometry").outputs["Normal"], 2, 1.0)]
    s1, s2, nz = N("ShaderNodeVectorMath"), N("ShaderNodeVectorMath"), N("ShaderNodeVectorMath")
    s1.operation = s2.operation = "ADD"
    nz.operation = "NORMALIZE"
    nt.links.new(terms[0], s1.inputs[0])
    nt.links.new(terms[1], s1.inputs[1])
    nt.links.new(s1.outputs[0], s2.inputs[0])
    nt.links.new(terms[2], s2.inputs[1])
    nt.links.new(s2.outputs[0], nz.inputs[0])
    nt.links.new(nz.outputs[0], bsdf.inputs["Normal"])


def render_views(building, w3d_path, w3d, texmap, prefix, views, res, samples, skeletons=None):
    scene.import_w3d(w3d_path, skeletons)
    rig(res, samples, building.bake_hidden)
    for name, mesh in w3d.meshes.items():
        obj = bpy.data.objects.get(name)
        if obj is not None and not obj.hide_render and mesh.textures and all(t.lower() in texmap for t in mesh.textures):
            game_material(obj, mesh, texmap)
    presets = views_for(building, bpy.data.objects[building.target])
    for v in views:
        c = camera(v, *presets[v])
        sc = bpy.context.scene
        sc.camera, sc.render.filepath = c, prefix + v + ".png"
        bpy.ops.render.render(write_still=True)
