"""Work-round for sagekit.blender.layout.own_layout on an organic target (Blender side only).

own_layout seams the ORIGINAL faces only at hard edges (> 40 degrees) and at folds of their atlas
mapping, then unwraps (angle based) and packs. EA's crumpled rock shell (OBJPOLYSURFACE1, 832
triangles) then keeps islands of up to 463 triangles whose unwrap overlaps itself: 1.55 % of the
layout overlaps and the 'UVs non-overlapping' check fails - with or without any new geometry
(new faces never join old islands).

`patch()` wraps layout._seams: after the framework's seams it also seams old faces at > 15 degrees,
then unwraps on a scratch UV layer, finds the islands that still overlap themselves, splits them
further (> 5 degrees, then every edge), and repeats until none does. The scratch layer is removed;
own_layout then unwraps and packs as always.
"""
import math

import bmesh
import bpy
import numpy as np
from bpy_extras import bmesh_utils

SCRATCH = "SEAMTRIAL"


def _tri_overlap(uvs, res=256):
    """Texels covered more than once by the triangles [(a, b, c)] of one island, rastered with the
    island's longer side at `res` texels."""
    P = np.array(uvs, float).reshape(-1, 2)
    lo, hi = P.min(0), P.max(0)
    s = res / max(float((hi - lo).max()), 1e-9)
    cnt = np.zeros((res + 2, res + 2), np.int16)
    for tri in uvs:
        a, b, c = [(np.array(p) - lo) * s for p in tri]
        x0, x1 = int(math.floor(min(a[0], b[0], c[0]))), int(math.ceil(max(a[0], b[0], c[0])))
        y0, y1 = int(math.floor(min(a[1], b[1], c[1]))), int(math.ceil(max(a[1], b[1], c[1])))
        if x1 <= x0 or y1 <= y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)

        def e(p, q):
            return (q[0] - p[0]) * (ys - p[1]) - (q[1] - p[1]) * (xs - p[0])
        w0, w1, w2 = e(b, c), e(c, a), e(a, b)
        cnt[y0:y1, x0:x1] += ((w0 > 0) & (w1 > 0) & (w2 > 0)) | ((w0 < 0) & (w1 < 0) & (w2 < 0))
    return int((cnt > 1).sum())


def _seam_old(me, tag_attr, angle=None, faces=None):
    """Seam the edges between original faces (tag 0) steeper than `angle` degrees (None: every
    edge), only among `faces` (face indices) if given."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    tagl = bm.faces.layers.int[tag_attr]
    for e in bm.edges:
        lf = e.link_faces
        if len(lf) != 2 or lf[0][tagl] or lf[1][tagl]:
            continue
        if faces is not None and lf[0].index not in faces and lf[1].index not in faces:
            continue
        if angle is None or lf[0].normal.angle(lf[1].normal, 0) > math.radians(angle):
            e.seam = True
    bm.to_mesh(me)
    bm.free()


def _overlapping_islands(obj, layout):
    """Unwrap on a scratch layer like own_layout does; the face indices of every island (of
    original faces) that overlaps itself."""
    me = obj.data
    buf = [0.0] * (2 * len(me.loops))
    me.uv_layers["UVMap"].data.foreach_get("uv", buf)
    scratch = me.uv_layers.new(name=SCRATCH)
    scratch.data.foreach_set("uv", buf)
    me.uv_layers.active = scratch
    layout._edit(obj, lambda: bpy.ops.uv.unwrap(method="ANGLE_BASED", fill_holes=True, correct_aspect=True, margin=0.001))
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv[SCRATCH]
    tagl = bm.faces.layers.int[layout.TAG_ATTR]
    bad = []
    for isl in bmesh_utils.bmesh_linked_uv_islands(bm, uvl):
        if len(isl) < 2 or any(f[tagl] for f in isl):
            continue
        tris = []
        for f in isl:
            u = [tuple(lp[uvl].uv) for lp in f.loops]
            tris += [(u[0], u[i], u[i + 1]) for i in range(1, len(u) - 1)]
        if _tri_overlap(tris) > 2:
            bad.append({f.index for f in isl})
    bm.free()
    me.uv_layers.remove(me.uv_layers[SCRATCH])
    me.uv_layers.active = me.uv_layers["UVMap"]
    return bad


def patch():
    from sagekit.blender import layout
    orig = layout._seams
    if getattr(orig, "sagekit_split", False):
        return

    def seams(me, *args):                   # (layout's own options, e.g. facet_islands, pass through)
        orig(me, *args)
        obj = next(o for o in bpy.data.objects if o.type == "MESH" and o.data == me)
        _seam_old(me, layout.TAG_ATTR, 15.0)
        for angle in (5.0, None, None):
            bad = _overlapping_islands(obj, layout)
            print("layout_fix: %d self-overlapping islands of original faces" % len(bad), flush=True)
            if not bad:
                return
            _seam_old(me, layout.TAG_ATTR, angle, set().union(*bad))
        print("layout_fix: islands still overlap after every split", flush=True)
    seams.sagekit_split = True
    layout._seams = seams
