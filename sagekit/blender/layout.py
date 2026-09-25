"""Add a building's new solids to its target mesh and give the mesh its own UV layout.

UV layers on the target mesh afterwards:
  UVMap      the new unique layout (exported: the W3D material pass's one texcoord set)
  UVMap.001  identical copy. The importer always creates this second layer for a W3X-only second
             texcoord set and leaves it zeroed; the exporter never writes it, but it splits
             vertices wherever ANY layer disagrees, so it must match UVMap.
  ATLAS      the original sheet's coordinates (old faces from the file, new faces from
             AtlasMapper). Bake source only; removed before export.
Face attribute 'r2tag': 0 for original faces, else 1 + the atlas region index of the new face.
"""
import math

import bmesh
import bpy
from bpy_extras import bmesh_utils
from mathutils import Vector as V
from mathutils.bvhtree import BVHTree

from . import scene
from .geometry import poly_area
from .mapping import AtlasMapper

TAG_ATTR = "r2tag"


def tag_names(atlas):
    return ["old"] + list(atlas.regions)


def add_solids(obj, solids, atlas):
    """Append every kept polygon of `solids` to obj's mesh with atlas UVs. Pieces of one polygon
    (tiling cuts) share vertices, so each polygon becomes one island in the new layout."""
    tags = tag_names(atlas)
    mapper = AtlasMapper(atlas)
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv0 = bm.loops.layers.uv["UVMap"]
    tagl = bm.faces.layers.int.new(TAG_ATTR)
    for f in bm.faces:
        f[tagl] = 0
    added, stats = 0, {}
    for solid in solids:
        for pts, tag, keep in solid.polys:
            if not keep:
                continue
            base = tag.split("|")[0]
            vmap = {}

            def vert(p):
                k = tuple(round(c, 4) for c in p)
                if k not in vmap:
                    vmap[k] = bm.verts.new(p)
                return vmap[k]
            for ppts, uvs in mapper.map(pts, tag):
                ppts = [V(p) for p in ppts]
                if poly_area(ppts)[0] < 1e-4:          # slivers left by tiling cuts
                    continue
                vs = [vert(p) for p in ppts]
                for i in range(1, len(vs) - 1):
                    tri = (vs[0], vs[i], vs[i + 1])
                    if len(set(tri)) < 3 or (tri[1].co - tri[0].co).cross(tri[2].co - tri[0].co).length < 1e-6:
                        continue
                    f = bm.faces.new(tri)
                    f.material_index = 0
                    f[tagl] = tags.index(base)
                    for lp, uv in zip(f.loops, (uvs[0], uvs[i], uvs[i + 1])):
                        lp[uv0].uv = uv
                    added += 1
                    stats[base] = stats.get(base, 0) + 1
    bm.to_mesh(me)
    bm.free()
    me.update()
    return added, stats


def sky_dirs(n, el_lo, el_hi):
    out, ga = [], math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = math.sin(math.radians(el_lo)) + (math.sin(math.radians(el_hi)) - math.sin(math.radians(el_lo))) * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        out.append(V((r * math.cos(ga * i), r * math.sin(ga * i), z)))
    return out


def face_weights(me, building):
    """Per face: how much the RTS camera sees it (rays toward 30..65 degree elevations, any
    azimuth, 0..1) times the building's emphasis; undersides get less."""
    bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    dirs = sky_dirs(48, 30, 65)
    w = []
    for p in me.polygons:
        n, c = p.normal, p.center
        seen = 0
        for d in dirs:
            k = n.dot(d)
            if k <= 0.05:
                continue
            if bvh.ray_cast(c + n * 0.02, d, 3000.0)[0] is None:
                seen += k
        vis = min(1.0, seen / len(dirs) * 2.0)
        e = building.emphasis(c, n)
        if n.z < -0.3:
            e *= 0.4
        w.append((0.10 + 0.90 * vis) * e)
    return w


def _seams(me):
    """Seams on original faces at hard edges (> 40 degrees) and folds of their atlas mapping; new
    faces are islands per planar polygon."""
    bm = bmesh.new()
    bm.from_mesh(me)
    auv = bm.loops.layers.uv["ATLAS"]
    tagl = bm.faces.layers.int[TAG_ATTR]

    def uv_sign(f):
        a, b, c = [lp[auv].uv for lp in f.loops][:3]
        return (b - a).cross(c - a) >= 0
    for e in bm.edges:
        e.seam = False
        if len(e.link_faces) != 2:
            e.seam = True
            continue
        f1, f2 = e.link_faces
        if f1[tagl] or f2[tagl]:
            e.seam = f1[tagl] != f2[tagl] or not (f1.normal.dot(f2.normal) > 0.9999)
            continue
        if f1.normal.angle(f2.normal, 0) > math.radians(40) or uv_sign(f1) != uv_sign(f2):
            e.seam = True
    bm.to_mesh(me)
    bm.free()


def _edit(obj, fn):
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.view_layer.objects:
        o.select_set(o == obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    fn()
    bpy.ops.object.mode_set(mode="OBJECT")


def own_layout(obj, building):
    """Give obj its own non-overlapping layout, texel density weighted by face_weights."""
    me = obj.data
    # the shading the exporter writes: vertex normals (face-angle weighted), not custom normals
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    for p in me.polygons:
        p.use_smooth = True
    for e in me.edges:
        e.use_edge_sharp = False
    buf = [0.0] * (2 * len(me.loops))
    me.uv_layers["UVMap"].data.foreach_get("uv", buf)
    me.uv_layers.new(name="ATLAS").data.foreach_set("uv", buf)
    _seams(me)
    me.uv_layers.active = me.uv_layers["UVMap"]
    _edit(obj, lambda: bpy.ops.uv.unwrap(method="ANGLE_BASED", fill_holes=True, correct_aspect=True, margin=0.001))

    w = face_weights(me, building)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    uvl = bm.loops.layers.uv["UVMap"]
    islands = bmesh_utils.bmesh_linked_uv_islands(bm, uvl)
    for isl in islands:                              # scale: uniform world density x sqrt(weight)
        a3 = sum(f.calc_area() for f in isl)
        auv = 0.0
        for f in isl:
            u = [lp[uvl].uv for lp in f.loops]
            auv += abs((u[1] - u[0]).cross(u[2] - u[0])) / 2
        if a3 <= 0 or auv <= 0:
            continue
        wi = sum(w[f.index] * f.calc_area() for f in isl) / a3
        s = math.sqrt(a3 / auv) * math.sqrt(wi) * 0.01
        cen = sum((lp[uvl].uv for f in isl for lp in f.loops), V((0, 0))) / (3 * len(isl))
        for f in isl:
            for lp in f.loops:
                lp[uvl].uv = cen + (lp[uvl].uv - cen) * s
    bm.to_mesh(me)
    bm.free()
    _edit(obj, lambda: bpy.ops.uv.pack_islands(
        udim_source="CLOSEST_UDIM", rotate=True, rotate_method="AXIS_ALIGNED", scale=True, merge_overlap=False,
        margin_method="FRACTION", margin=0.001, pin=False, shape_method="CONCAVE"))
    scene.mirror_uv(me)
    me.uv_layers.active = me.uv_layers["UVMap"]
    me.uv_layers["UVMap"].active_render = True
    return len(islands)
