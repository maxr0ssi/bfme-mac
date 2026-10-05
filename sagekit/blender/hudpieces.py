"""Render the faction palantirs' ornaments in 3D (Blender, Cycles): blender -b --python hudpieces.py -- job.json

The job (sagekit/hud/pieces.py writes it from assets/hud/factions/pieces.py): page size, scale (4: the
painter's 4x pixels), light, materials and pieces in page pixels (x right, y down, z up out of the
page). The pieces lie on the page as reliefs and are seen straight from the front, lit from the top
left like EA's frame. A shadow-catcher plane at z 0 adds their contact and drop shadows to the alpha.
The output is an RGBA PNG at scale times the page size: the pieces, then their shadows (black, with
the shadow's alpha).
"""
import json
import math
import sys

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

Z = Vector((0, 0, 1))


def W(p):
    """Page px (x, y down, z) -> world."""
    return Vector((p[0], -p[1], p[2] if len(p) > 2 else 0.0))


# ---------------------------------------------------------------------------------- materials
def material(name, d):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = N["Principled BSDF"]
    base = d.get("base", (0.5, 0.5, 0.5))
    b.inputs["Metallic"].default_value = d.get("metal", 0.0)
    b.inputs["Roughness"].default_value = d.get("rough", 0.4)
    if d.get("ss"):
        b.inputs["Subsurface Weight"].default_value = d["ss"]
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.3)
        b.inputs["Subsurface Scale"].default_value = d.get("ss_scale", 0.6)
    if d.get("trans"):
        b.inputs["Transmission Weight"].default_value = d["trans"]
        b.inputs["IOR"].default_value = d.get("ior", 1.31)
    if d.get("coat"):
        b.inputs["Coat Weight"].default_value = d["coat"]
        b.inputs["Coat Roughness"].default_value = d.get("coat_rough", 0.08)
    if d.get("emit"):
        b.inputs["Emission Color"].default_value = tuple(d["emit"]) + (1,)
        b.inputs["Emission Strength"].default_value = d.get("emit_s", 1.0)
    col = N.new("ShaderNodeRGB")
    col.outputs[0].default_value = tuple(base) + (1,)
    out = col.outputs[0]
    scale = d.get("noise_scale", 0.35)
    if d.get("grime") or d.get("blood") or d.get("var"):
        tc = N.new("ShaderNodeNewGeometry")                # world position: page px
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = scale
        nz.inputs["Detail"].default_value = 6
        L.new(tc.outputs["Position"], nz.inputs["Vector"])
    if d.get("var"):                                     # a little tone variation across the surface
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = d["var"]
        L.new(out, mix.inputs[6])
        L.new(nz.outputs["Color"], mix.inputs[7])
        out = mix.outputs[2]
    if d.get("grime"):                                   # dirt in the hollows (ambient occlusion)
        ao = N.new("ShaderNodeAmbientOcclusion")
        ao.inputs["Distance"].default_value = d.get("ao_dist", 2.0)
        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.25
        ramp.color_ramp.elements[0].color = tuple(d.get("grime_col", (0.12, 0.08, 0.05))) + (1,)
        ramp.color_ramp.elements[1].position = 0.85
        ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
        L.new(ao.outputs["AO"], ramp.inputs[0])
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = d["grime"]
        L.new(out, mix.inputs[6])
        L.new(ramp.outputs[0], mix.inputs[7])
        out = mix.outputs[2]
    if d.get("wear"):                                    # edge wear: convex edges brighten
        geo = N.new("ShaderNodeNewGeometry")
        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.5
        ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        ramp.color_ramp.elements[1].position = 0.56
        ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
        L.new(geo.outputs["Pointiness"], ramp.inputs[0])
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["Factor"].default_value = d["wear"]
        mix.inputs[7].default_value = tuple(d.get("wear_col", (0.8, 0.8, 0.82))) + (1,)
        fac = N.new("ShaderNodeMath")
        fac.operation = "MULTIPLY"
        fac.inputs[1].default_value = d["wear"]
        L.new(ramp.outputs[0], fac.inputs[0])
        L.new(fac.outputs[0], mix.inputs["Factor"])
        L.new(out, mix.inputs[6])
        out = mix.outputs[2]
    if d.get("frost"):                                   # rime on the up-facing surfaces
        geo = N.new("ShaderNodeNewGeometry")
        sep = N.new("ShaderNodeSeparateXYZ")
        L.new(geo.outputs["Normal"], sep.inputs[0])
        ramp = N.new("ShaderNodeMapRange")
        ramp.inputs[1].default_value = 0.2
        ramp.inputs[2].default_value = 0.75
        L.new(sep.outputs[1], ramp.inputs[0])            # world +y: the page's top
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs[7].default_value = (0.82, 0.9, 1.0, 1)
        fac = N.new("ShaderNodeMath")
        fac.operation = "MULTIPLY"
        fac.inputs[1].default_value = d["frost"]
        L.new(ramp.outputs[0], fac.inputs[0])
        L.new(fac.outputs[0], mix.inputs["Factor"])
        L.new(out, mix.inputs[6])
        out = mix.outputs[2]
    if d.get("blood"):                                   # patches of dried and wet blood
        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.7 - 0.25 * d["blood"]
        ramp.color_ramp.elements[1].position = 0.76 - 0.25 * d["blood"]
        L.new(nz.outputs["Fac"], ramp.inputs[0])
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs[7].default_value = (0.16, 0.01, 0.005, 1)
        L.new(ramp.outputs[0], mix.inputs["Factor"])
        L.new(out, mix.inputs[6])
        out = mix.outputs[2]
        rr = N.new("ShaderNodeMapRange")
        rr.inputs[3].default_value = d.get("rough", 0.5)
        rr.inputs[4].default_value = 0.12
        L.new(ramp.outputs[0], rr.inputs[0])
        L.new(rr.outputs[0], b.inputs["Roughness"])
    L.new(out, b.inputs["Base Color"])
    return m


# ---------------------------------------------------------------------------------- geometry
def link(obj, mat, smooth=True):
    bpy.context.scene.collection.objects.link(obj)
    if obj.type == "MESH":
        obj.data.materials.append(mat)
        for p in obj.data.polygons:
            p.use_smooth = smooth
    else:
        obj.data.materials.append(mat)
    return obj


def catmull(pts, n):
    P = [W(p) for p in pts]
    if len(P) == 2:
        return [P[0].lerp(P[1], i / (n - 1)) for i in range(n)], [i / (n - 1) for i in range(n)]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out, ts = [], []
    segs = len(P) - 3
    for i in range(n):
        u = i / (n - 1) * segs
        k = min(int(u), segs - 1)
        t = u - k
        p0, p1, p2, p3 = P[k:k + 4]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        ts.append(i / (n - 1))
    return out, ts


PROFILES = {
    "round": [(math.cos(a), math.sin(a)) for a in [2 * math.pi * i / 14 for i in range(14)]],
    "hex": [(math.cos(a), math.sin(a)) for a in [2 * math.pi * i / 6 + math.pi / 6 for i in range(6)]],
    "blade": [(1, 0), (0.55, 0.45), (0, 1), (-0.55, 0.45), (-1, 0), (-0.55, -0.45), (0, -1), (0.55, -0.45)],
    "leaf": [(math.cos(a), math.sin(a) * (0.5 + 0.5 * abs(math.cos(a)))) for a in
             [2 * math.pi * i / 16 for i in range(16)]],
}


def tube(p, mat):
    """A tapering tube along a path: horns, tusks, blades, icicles, spires, branches, leaves."""
    path, ts = catmull(p["pts"], p.get("n", 28))
    radii = p["r"]
    prof = PROFILES[p.get("profile", "round")]
    asp = p.get("aspect", 1.0)
    bm = bmesh.new()
    rings = []
    up_ref = Z
    for i, c in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = t.cross(up_ref)
        if side.length < 1e-4:
            side = t.cross(Vector((1, 0, 0)))
        side.normalize()
        up = side.cross(t).normalized()
        u = ts[i] * (len(radii) - 1)
        k = min(int(u), len(radii) - 2)
        r = radii[k] + (radii[k + 1] - radii[k]) * (u - k)
        r = max(r, 0.02)
        rings.append([bm.verts.new(c + side * (x * r) + up * (y * r * asp)) for x, y in prof])
    m = len(prof)
    for a, b in zip(rings, rings[1:]):
        for j in range(m):
            bm.faces.new((a[j], a[(j + 1) % m], b[(j + 1) % m], b[j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bm.normal_update()
    me = bpy.data.meshes.new(p.get("name", "tube"))
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(me.name, me)
    return link(obj, mat, p.get("profile", "round") in ("round", "leaf"))


def prism(p, mat):
    """An outline (page px) extruded h px off the page, its edges bevelled: crests, plates, stars."""
    pts = p.get("poly")
    if p["kind"] == "star":
        cx, cy = p["at"][:2]
        n, R, inner = p.get("n", 6), p["r"], p.get("inner", 0.45)
        pts = [(cx + (R if i % 2 == 0 else R * inner) * math.sin(math.pi * i / n + p.get("rot", 0)),
                cy - (R if i % 2 == 0 else R * inner) * math.cos(math.pi * i / n + p.get("rot", 0)))
               for i in range(2 * n)]
    if p["kind"] == "box":
        cx, cy = p["at"][:2]
        sx, sy = p["size"][:2]
        pts = [(cx - sx / 2, cy - sy / 2), (cx + sx / 2, cy - sy / 2), (cx + sx / 2, cy + sy / 2), (cx - sx / 2, cy + sy / 2)]
    if p["kind"] == "disc":
        cx, cy = p["at"][:2]
        pts = [(cx + p["r"] * math.cos(2 * math.pi * i / 40), cy + p["r"] * math.sin(2 * math.pi * i / 40))
               for i in range(40)]
    z0 = p.get("z", 0.0)
    h = p.get("h", 2.0)
    bm = bmesh.new()
    base = [bm.verts.new(W((x, y, z0))) for x, y in pts]
    f = bm.faces.new(base)
    bm.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    top = [v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=top, vec=Vector((0, 0, h)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(p.get("name", p["kind"]))
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(me.name, me)
    mod = obj.modifiers.new("bevel", "BEVEL")
    mod.width = p.get("bevel", 0.6)
    mod.segments = p.get("segments", 3)
    mod.limit_method = "ANGLE"
    mod.harden_normals = False
    return link(obj, mat, True)


def gem(p, mat):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:                                   # a cabochon: flat-ish crown, faceted
        v.co.z = max(v.co.z, -0.1) * 0.75
    me = bpy.data.meshes.new("gem")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("gem", me)
    obj.location = W(p["at"])
    obj.scale = (p["r"], p["r"], p["r"])
    return link(obj, mat, p.get("smooth", False))


def metaball(p, mat, build):
    mb = bpy.data.metaballs.new(p["kind"])
    mb.resolution = p.get("res", 0.045)
    mb.render_resolution = p.get("res", 0.03)
    mb.threshold = 0.6
    build(mb)
    obj = bpy.data.objects.new(p["kind"], mb)
    s = p["size"]
    obj.location = W(p["at"])
    obj.rotation_euler = (0, 0, -math.radians(p.get("rot", 0.0)))
    obj.scale = (s, s, s)
    return link(obj, mat)


def el(mb, kind, co, r, neg=False, size=None, rot=None):
    e = mb.elements.new(type=kind)
    e.co = co
    e.radius = r
    e.use_negative = neg
    if size:
        e.size_x, e.size_y, e.size_z = size
    if rot is not None:
        e.rotation = Quaternion(Z, rot)
    return e


def ellipsoid(bm, c, r):
    g = bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ Matrix.Diagonal(Vector(r).to_4d()), verts=g["verts"])


def capsule(bm, a, b, r):
    a, b = Vector(a), Vector(b)
    d = b - a
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r, radius2=r, depth=d.length)
    rot = d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=g["verts"])
    ellipsoid(bm, a, (r, r, r))
    ellipsoid(bm, b, (r, r, r))


SKULL = dict(
    plus=[("e", (0, 0.1, 0.0), (0.36, 0.40, 0.30)), ("e", (0, -0.19, 0.05), (0.28, 0.24, 0.25)),
          ("e", (0, -0.37, 0.07), (0.18, 0.12, 0.16)), ("e", (0.21, -0.15, 0.1), (0.09, 0.08, 0.1)),
          ("e", (-0.21, -0.15, 0.1), (0.09, 0.08, 0.1))],
    minus=[("e", (0.135, -0.07, 0.3), (0.105, 0.095, 0.17)), ("e", (-0.135, -0.07, 0.3), (0.105, 0.095, 0.17)),
           ("e", (0, -0.23, 0.31), (0.035, 0.06, 0.1)), ("e", (0, -0.385, 0.24), (0.13, 0.012, 0.1))]
    + [("e", (x, -0.385, 0.25), (0.006, 0.06, 0.1)) for x in (-0.09, -0.045, 0, 0.045, 0.09)],
    voxel=0.018)
HAND = dict(
    plus=[("e", (0, -0.14, 0), (0.24, 0.24, 0.11))]
    + [("c", (x, 0.04, 0.02), (x * 1.15, 0.04 + ln, 0.03), 0.07) for x, ln in ((-0.165, 0.27), (-0.055, 0.33),
                                                                                (0.055, 0.34), (0.165, 0.28))]
    + [("c", (-0.18, -0.2, 0.02), (-0.36, -0.02, 0.03), 0.075)],
    minus=[], voxel=0.016)


def organic(p, mat, spec):
    """Overlapping ellipsoids and capsules fused by a voxel remesh, cut, smoothed: skulls, hands."""
    def build(parts):
        bm = bmesh.new()
        for q in parts:
            if q[0] == "e":
                ellipsoid(bm, Vector(q[1]), q[2])
            else:
                capsule(bm, q[1], q[2], q[3])
        me = bpy.data.meshes.new("part")
        bm.to_mesh(me)
        bm.free()
        return bpy.data.objects.new("part", me)
    obj = build(spec["plus"])
    bpy.context.scene.collection.objects.link(obj)
    rm = obj.modifiers.new("remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = spec["voxel"]
    if spec["minus"]:
        cut = build(spec["minus"])
        bpy.context.scene.collection.objects.link(cut)
        cut.hide_render = True
        cut.display_type = "WIRE"
        crm = cut.modifiers.new("remesh", "REMESH")
        crm.mode = "VOXEL"
        crm.voxel_size = spec["voxel"] * 0.6
        cut.parent = obj
        bo = obj.modifiers.new("cut", "BOOLEAN")
        bo.operation = "DIFFERENCE"
        bo.object = cut
        bo.solver = "EXACT"
    sm = obj.modifiers.new("smooth", "SMOOTH")
    sm.factor, sm.iterations = 0.5, 6
    obj.location = W(p["at"])
    obj.rotation_euler = (0, 0, -math.radians(p.get("rot", 0.0)))
    s = p["size"]
    obj.scale = (s, s, s)
    obj.data.materials.append(mat)
    for f in obj.data.polygons:
        f.use_smooth = True
    return obj


def bone(mb):
    """A long bone along x, unit length: the shaft and the two knobbed ends."""
    el(mb, "CAPSULE", (0, 0, 0), 0.12, size=(0.42, 1, 1))
    for s in (1, -1):
        el(mb, "BALL", (0.47 * s, 0.07, 0), 0.13)
        el(mb, "BALL", (0.47 * s, -0.07, 0), 0.13)


BUILD = {"bone": bone}


def piece(p, mats):
    mat = mats[p["mat"]]
    k = p["kind"]
    if k == "tube":
        return tube(p, mat)
    if k in ("prism", "star", "box", "disc"):
        return prism(p, mat)
    if k == "gem":
        return gem(p, mat)
    if k == "skull":
        return organic(p, mat, SKULL)
    if k == "hand":
        return organic(p, mat, HAND)
    if k in BUILD:
        if k == "bone":                                  # placed from a to b
            a, b = W(p["a"]), W(p["b"])
            p = dict(p, at=[(a.x + b.x) / 2, -(a.y + b.y) / 2, (a.z + b.z) / 2], size=(b - a).length,
                     rot=-math.degrees(math.atan2((b - a).y, (b - a).x)))
        return metaball(p, mat, BUILD[k])
    raise ValueError(k)


# ---------------------------------------------------------------------------------- scene
def studio(job, L):
    """What polished metal and gems reflect: a dark room with three emissive panels the camera does not
    see (a large soft box toward the key light, a strip above the page's top, a coloured rim panel
    from the bottom right). A dim world fills the rest."""
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = tuple(job.get("sky", (0.9, 0.88, 0.85))) + (1,)
    bg.inputs[1].default_value = job.get("ambient", 0.35) * 0.5
    c = Vector((job["w"] / 2, -job["h"] / 2, 0))
    rim = Vector((0.65, -0.55, 0.5)).normalized()
    for name, d, size, strength, col in (
            ("softbox", L, 520, job.get("softbox", 2.6), (1, 0.98, 0.95)),
            ("strip", Vector((0.0, 0.62, 0.78)).normalized(), 360, 1.2, (1, 1, 1)),
            ("overhead", Vector((-0.25, 0.3, 0.92)).normalized(), 600, 0.35, (1, 1, 1)),
            ("rimbox", rim, 300, job.get("rim", 0.8) * 1.2, job.get("rim_col", (0.7, 0.75, 0.85)))):
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        ob.location = c + d * 700
        ob.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = tuple(col) + (1,)
        em.inputs[1].default_value = strength
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs[0], out.inputs[0])
        me.materials.append(m)
        ob.visible_camera = False
        ob.visible_shadow = False
        bpy.context.scene.collection.objects.link(ob)
    return world


def scene(job):
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    w, h, k = job["w"], job["h"], job["scale"]
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception:
        sc.cycles.device = "CPU"
    sc.cycles.samples = job.get("samples", 64)
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = w * k, h * k
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "16"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = job.get("exposure", 0.0)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(w, h)
    cam.data.clip_end = 1000
    cam.location = (w / 2, -h / 2, 300)
    sc.collection.objects.link(cam)
    sc.camera = cam
    key = job.get("light", (-0.5, -0.75, 0.62))                        # page coords: from the top left
    L = Vector((key[0], -key[1], key[2])).normalized()
    sc.world = studio(job, L)
    sun = bpy.data.objects.new("key", bpy.data.lights.new("key", "SUN"))
    sun.data.energy = job.get("key", 3.2) * 0.7
    sun.data.angle = math.radians(job.get("soft", 10))
    sun.rotation_euler = L.to_track_quat("Z", "Y").to_euler()
    sc.collection.objects.link(sun)
    rim = bpy.data.objects.new("rim", bpy.data.lights.new("rim", "SUN"))
    rim.data.energy = job.get("rim", 0.8)
    rim.data.color = job.get("rim_col", (0.7, 0.75, 0.85))
    rim.rotation_euler = Vector((0.65, -0.55, 0.5)).normalized().to_track_quat("Z", "Y").to_euler()
    sc.collection.objects.link(rim)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=max(w, h))
    me = bpy.data.meshes.new("catcher")
    bm.to_mesh(me)
    bm.free()
    pl = bpy.data.objects.new("catcher", me)
    pl.location = (w / 2, -h / 2, 0)
    pl.is_shadow_catcher = True
    sc.collection.objects.link(pl)


def main(path):
    job = json.load(open(path))
    for r in job["renders"]:
        scene(dict(job, **r))
        mats = {n: material(n, d) for n, d in r["mats"].items()}
        for p in r["pieces"]:
            piece(p, mats)
        bpy.context.scene.render.filepath = r["out"]
        bpy.ops.render.render(write_still=True)
        print("RENDERED", r["out"])
    print("JOB OK")


main(sys.argv[sys.argv.index("--") + 1])
