"""The shape preview (sagekit/preview.py), inside Blender: the geometry stage and EA's model drawn
with EEVEE in flat colours, and the checks that need no bake.

Colours: every new face in the palette's mid colour for its atlas tag (the style's TagRamp for the
tag over the mean luminance of the tag's region on the sheet, else the tag's own ramp, else stone
through the Recolour's stone mapping); EA's faces and other meshes a neutral clay; the house cloth
(work/house_cloth.json's copy) in the renders' player colour. The full render's sun, a soft sky,
shadows on a ground plane and screen-space AO make depth read.

Checks: those of the standard suite (blender/checks_suite.py) that read only the target's
geometry, computed on the stage instead of the exported file (triangle budget, footprint, height
growth, winding, sky-facing backs, zero-area faces, UVs in [0,1]), plus closed solids: every solid
design() returns is watertight and consistently wound (T-junctions allowed).
"""
import json
import math
import os
import time

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from ..formats.w3d import W3DFile
from . import scene
from .checks import Report, new_triangle_normals
from .layout import TAG_ATTR, tag_names
from .render import PREVIEW_HOUSE_COLOUR, camera, views_for

CLAY = (0.60, 0.58, 0.55)           # EA's faces and meshes: neutral, so the new faces stand out
OTHER = (0.50, 0.49, 0.47)          # EA's other meshes (props, banners, platforms)
GROUND = (0.33, 0.31, 0.27)
SKY = (0.36, 0.40, 0.48)


def run(b, ws, prefix, views, res, cloth=None):
    t0 = time.time()
    hidden = day_hidden(b, ws)
    obj = bpy.data.objects[b.target]
    new = stats(obj, b.world_space)
    colours = tag_colours(b, ws)
    names = tag_names(b.style.atlas)
    used = paint_target(obj, names, colours)
    for o in bpy.data.objects:
        if o.type == "MESH" and o is not obj:
            paint(o, OTHER)
    if cloth and os.path.exists(cloth):
        n = add_cloth(cloth)
        if n:
            used["house cloth"] = (n, PREVIEW_HOUSE_COLOUR[:3])
    shoot(b, obj, hidden, prefix + "new_", views, res)
    with open(prefix + "legend.json", "w") as fh:
        json.dump([[tag, n, [round(c, 4) for c in col]] for tag, (n, col) in used.items()], fh)
    t1 = time.time()

    r = Report()
    closed_solids(b, r)
    scene.import_w3d(ws.source_model, ws.src)
    old = stats(bpy.data.objects[b.target], b.world_space)
    geometry_checks(b, ws, new, old, r)
    t2 = time.time()
    if ws.reference_model != ws.source_model:
        scene.import_w3d(ws.reference_model, ws.src)
    for o in bpy.data.objects:
        if o.type == "MESH":
            paint(o, CLAY if o.name == b.target else OTHER)
    shoot(b, bpy.data.objects[b.target], hidden, prefix + "orig_", views, res)
    r.summary()
    print("PREVIEW TIMES renders %.1fs, checks %.1fs" % (time.time() - t2 + t1 - t0, t2 - t1), flush=True)


def day_hidden(b, ws):
    from ..nightlights import day_hidden as hidden
    return set(hidden(b, W3DFile(ws.source_model).data))


# ---------------------------------------------------------------------------------------- colours
def srgb_to_linear(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def region_lums(b, ws):
    """{region: mean sRGB luminance of its rectangle on the faction sheet} (the paint's cv.lum)."""
    a, path = b.style.atlas, ws.master_upscale
    if not os.path.exists(path):
        return {}
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    lum = (px.reshape(h, w, 4)[..., :3] @ np.array([0.3, 0.59, 0.11], np.float32))
    k = w / float(a.size)
    out = {}
    for name, reg in a.regions.items():
        x0, y0, x1, y1 = reg.rect
        rows = slice(max(int(h - y1 * k), 0), max(int(h - y0 * k), 1))      # Blender's rows run bottom-up
        patch = lum[rows, int(x0 * k):max(int(x1 * k), int(x0 * k) + 1)]
        if patch.size:
            out[name] = float(patch.mean())
    return out


def tag_colours(b, ws):
    """{atlas tag: sRGB colour}: the mid colour the paint stack gives the tag's new faces."""
    from ..paint.fields import ramp
    pal = b.style.palette
    try:
        layers = b.style.layers(b)
    except Exception as e:                  # a stack that needs the bake: plain ramps then
        print("preview: no paint stack (%s): plain ramps" % e)
        layers = []
    tagramps = {getattr(x, "tag", None): x for x in layers if hasattr(x, "ramp_name") and hasattr(x, "tag")}
    rec = next((x for x in layers if all(hasattr(x, k) for k in ("pivot", "gain", "mid"))), None)
    pivot, gain, mid = (rec.pivot, rec.gain, rec.mid) if rec else (0.45, 1.12, 0.47)
    lums = region_lums(b, ws)
    out = {}
    for tag in b.style.atlas.regions:
        L = lums.get(tag, 0.5)
        stem = tag.rstrip("ABCD") if tag not in pal.ramps else tag
        if tag in tagramps and tagramps[tag].ramp_name in pal.ramps:
            t = tagramps[tag]
            x, stops = np.clip(L * t.gain + t.lift, 0, 1), pal.ramps[t.ramp_name]
        elif stem in pal.ramps and stem != "stone":
            x, stops = L, pal.ramps[stem]
        else:
            x, stops = np.clip((L - pivot) * gain + mid, 0, 1), pal.ramps["stone"]
        out[tag] = tuple(float(c) for c in ramp(np.float32(x), stops))
    return out


def colour_attr(me, rgb_per_face):
    """A face-corner colour attribute from one sRGB colour per face, made the active one."""
    for a in list(me.color_attributes):
        if a.name == "preview":
            me.color_attributes.remove(a)
    attr = me.color_attributes.new("preview", "FLOAT_COLOR", "CORNER")
    lin = srgb_to_linear(rgb_per_face)
    counts = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get("loop_total", counts)
    per_loop = np.repeat(lin, counts, axis=0)
    rgba = np.concatenate([per_loop, np.ones((len(per_loop), 1), np.float32)], 1)
    attr.data.foreach_set("color", rgba.ravel())
    me.color_attributes.active_color = attr
    me.color_attributes.render_color_index = me.color_attributes.active_color_index


def paint(o, rgb):
    colour_attr(o.data, np.tile(np.asarray(rgb, np.float32), (len(o.data.polygons), 1)))


def paint_target(obj, names, colours):
    """Each face in its tag's colour; returns {tag: (faces, colour)} for the legend."""
    me = obj.data
    tags = np.zeros(len(me.polygons), np.int32)
    if TAG_ATTR in me.attributes:
        me.attributes[TAG_ATTR].data.foreach_get("value", tags)
    table = np.array([CLAY] + [colours.get(n, CLAY) for n in names[1:]], np.float32)
    colour_attr(me, table[np.clip(tags, 0, len(table) - 1)])
    used = {}
    for i in np.unique(tags):
        if i:
            used[names[i]] = (int((tags == i).sum()), tuple(float(c) for c in table[i]))
    return dict(sorted(used.items(), key=lambda kv: -kv[1][0]))


def add_cloth(path):
    """The cloth the geometry step sent to the house-colour model, drawn where it hangs."""
    polys = json.load(open(path))
    if not polys:
        return 0
    verts, faces = [], []
    for p in polys:
        faces.append(list(range(len(verts), len(verts) + len(p))))
        verts += [tuple(v) for v in p]
    me = bpy.data.meshes.new("PreviewCloth")
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new("PreviewCloth", me)
    bpy.context.collection.objects.link(o)
    paint(o, PREVIEW_HOUSE_COLOUR[:3])
    return len(polys)


# ---------------------------------------------------------------------------------------- render
def rig(res):
    """EEVEE, a few samples: the full render's sun and ground (blender/render.py rig), a soft sky,
    shadows and screen-space AO; every mesh drawn in its "preview" colours."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.eevee.taa_render_samples = 16
    sc.eevee.use_shadows = True
    for k, v in (("use_raytracing", True), ("ray_tracing_method", "SCREEN"), ("fast_gi_method", "AMBIENT_OCCLUSION_ONLY")):
        if hasattr(sc.eevee, k):                # (names of Blender 4.2-4.5's EEVEE)
            setattr(sc.eevee, k, v)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    w = bpy.data.worlds.get("PreviewSky") or bpy.data.worlds.new("PreviewSky")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = tuple(srgb_to_linear(SKY)) + (1.0,)
    bg.inputs[1].default_value = 1.0
    mat = bpy.data.materials.get("PreviewColour")
    if mat is None:
        mat = bpy.data.materials.new("PreviewColour")
        mat.use_nodes = True
        nt = mat.node_tree
        a, bsdf = nt.nodes.new("ShaderNodeAttribute"), nt.nodes["Principled BSDF"]
        a.attribute_name = "preview"
        bsdf.inputs["Roughness"].default_value = 0.85
        bsdf.inputs["Specular IOR Level"].default_value = 0.2
        nt.links.new(a.outputs["Color"], bsdf.inputs["Base Color"])
    if "PreviewGround" not in bpy.data.objects:
        me = bpy.data.meshes.new("PreviewGroundM")
        s = 2000
        me.from_pydata([(-s, -s, -0.05), (s, -s, -0.05), (s, s, -0.05), (-s, s, -0.05)], [], [(0, 1, 2, 3)])
        g = bpy.data.objects.new("PreviewGround", me)
        bpy.context.collection.objects.link(g)
        paint(g, GROUND)
        sd = bpy.data.lights.new("PreviewSun", "SUN")          # as render.rig: warm, upper left of the camera
        sd.energy, sd.color, sd.angle = 4.2, (1.0, 0.86, 0.68), math.radians(2.0)
        sun = bpy.data.objects.new("PreviewSun", sd)
        bpy.context.collection.objects.link(sun)
        az, el = math.radians(285), math.radians(42)
        d = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
        sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(mat)


def shoot(b, frame_obj, hidden, prefix, views, res):
    rig(res)
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name in hidden:
            o.hide_render = True
    presets = views_for(b, frame_obj)
    sc = bpy.context.scene
    for v in views:
        if v not in presets:
            raise SystemExit("no view %s (the recipe has %s)" % (v, ", ".join(presets)))
        sc.camera, sc.render.filepath = camera(v, *presets[v]), prefix + v + ".png"
        bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------------------------------- checks
def stats(o, world=False):
    """What checks.snapshot records for a mesh, from the live object (world: in world axes)."""
    me = o.data
    if world:
        me = me.copy()
        me.transform(o.matrix_world)
        me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    cs = [v.co for v in me.vertices]
    uv = np.zeros(2 * len(me.loops))
    if me.uv_layers:
        me.uv_layers[0].data.foreach_get("uv", uv)
    s = dict(
        tris=scene.tri_count(me),
        bbmin=[min(c[i] for c in cs) for i in range(3)], bbmax=[max(c[i] for c in cs) for i in range(3)],
        uv_out=int(((uv < -1e-4) | (uv > 1.0001)).reshape(-1, 2).any(1).sum()),
        zero_area=sum(1 for f in bm.faces if f.calc_area() < 1e-6), loose=sum(1 for v in bm.verts if not v.link_faces),
        tri_keys=[tuple(sorted(tuple(round(c, 3) for c in me.vertices[i].co) for i in p.vertices)) for p in me.polygons],
        verts=[tuple(v.co) for v in me.vertices], polys=[tuple(p.vertices) for p in me.polygons],
        fnormals=[tuple(p.normal) for p in me.polygons],
        vnormals=[[tuple(me.corner_normals[li].vector) for li in p.loop_indices] for p in me.polygons])
    bm.free()
    return s


def geometry_checks(b, ws, m, a, r):
    """The standard suite's target-geometry checks (checks_suite.run), same limits and wording."""
    from ..owncopy import extent
    target = b.target
    r.section("geometry (the stage, before export)")
    r.check("%s zero-area faces / loose verts" % target, m["zero_area"] == 0 and m["loose"] == 0,
            "%d / %d" % (m["zero_area"], m["loose"]))
    r.check("%s UVs inside [0,1]" % target, m["uv_out"] == 0, "%d out" % m["uv_out"])
    lim = dict(zip(("bbmin", "bbmax"), extent(b, ws, a["bbmin"], a["bbmax"])))
    r.check("%s triangles <= %d" % (target, b.tri_budget), m["tris"] <= b.tri_budget, "%d -> %d" % (a["tris"], m["tris"]))
    for i, ax in enumerate("XY"):
        e = b.footprint_margin + 1e-3
        r.check("%s %s footprint inside the original [%.2f, %.2f]%s" % (target, ax, lim["bbmin"][i], lim["bbmax"][i],
                                                                      " + %.1f" % b.footprint_margin if b.footprint_margin else ""),
                m["bbmin"][i] >= lim["bbmin"][i] - e and m["bbmax"][i] <= lim["bbmax"][i] + e,
                "new [%.2f, %.2f]" % (m["bbmin"][i], m["bbmax"][i]))
    h0, h1 = lim["bbmax"][2] - lim["bbmin"][2], m["bbmax"][2] - m["bbmin"][2]
    r.check("%s height growth <= %d%%" % (target, 100 * b.max_z_growth),
            h1 <= h0 * (1 + b.max_z_growth) + 1e-3 and m["bbmin"][2] >= lim["bbmin"][2] - 1e-3,
            "%.2f -> %.2f (%+.1f%%)" % (h0, h1, 100 * (h1 / h0 - 1)))
    cnt, disagree, visible, back_seen = new_triangle_normals(m, a)
    r.check("new triangles: winding matches vertex normals", disagree == 0, "%d of %d disagree" % (disagree, cnt))
    r.check("new triangles: no back face visible from the sky", back_seen == 0,
            "%d of %d visible show their back (%d buried)" % (back_seen, visible, cnt - visible))


def open_edges(solid, eps=1e-4):
    """Directed edges of a solid without a matching opposite one: 0 for a closed, consistently
    wound solid. Edges are split at the solid's own vertices lying on them (T-junctions)."""
    key = lambda p: tuple(round(c / eps) for c in p)          # noqa: E731
    pts = {}
    for poly, _, _ in solid.polys:
        for p in poly:
            pts.setdefault(key(p), p)
    P = list(pts.values())
    count = {}
    for poly, _, _ in solid.polys:
        for i in range(len(poly)):
            a, c = poly[i], poly[(i + 1) % len(poly)]
            d = c - a
            ll = d.length_squared
            if ll < eps * eps:
                continue
            on = sorted(((q - a).dot(d) / ll, key(q)) for q in P
                        if 1e-6 < (q - a).dot(d) / ll < 1 - 1e-6 and (q - a).cross(d).length < eps * d.length)
            chain = [key(a)] + [k for _, k in on] + [key(c)]
            for u, v in zip(chain, chain[1:]):
                if u != v:
                    count[(u, v)] = count.get((u, v), 0) + 1
    return sum(abs(n - count.get((v, u), 0)) for (u, v), n in count.items())


def closed_solids(b, r):
    """Every solid of design() closed and consistently wound (buried faces included)."""
    r.section("design() solids")
    solids = b.design(b.style.shapes())
    bad = []
    for i, s in enumerate(solids):
        n = open_edges(s)
        if n:
            tags = sorted({t.split("|")[0] for _, t, _ in s.polys})
            lo = [round(min(p[k] for poly, _, _ in s.polys for p in poly), 1) for k in range(3)]
            bad.append("#%d (%s) at %s: %d open edges" % (i, "/".join(tags), lo, n))
    r.check("closed solids (%d)" % len(solids), not bad, "; ".join(bad[:4]) + (" ..." if len(bad) > 4 else ""))
