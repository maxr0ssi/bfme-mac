"""Verify a built building against its original, the way the game will read it. Every limit comes
from the Building (footprint, height, triangle budget, tier) or from the original file (meshes,
bones, materials); texture names, UVs and tangents are read from the W3D bytes, not from Blender.
Prints PASS / FAIL / INFO lines; returns True when everything passed."""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from . import scene


class Report:
    def __init__(self):
        self.results = []

    def check(self, name, ok, detail=""):
        self.results.append(bool(ok))
        print("%s  %-60s %s" % ("PASS" if ok else "FAIL", name, detail), flush=True)

    def info(self, name, detail):
        print("INFO  %-60s %s" % (name, detail), flush=True)

    def section(self, title):
        print("--- " + title, flush=True)

    def summary(self):
        print("\n%d/%d checks passed\n%s" % (sum(self.results), len(self.results),
                                            "ALL PASS" if all(self.results) else "SOME CHECKS FAILED"))
        return all(self.results)


def snapshot(path):
    """What Blender imports from a model: bones, and per mesh its parent, materials, geometry."""
    scene.import_w3d(path)
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    s = {"n_arm": len(arms), "bones": {}, "meshes": {}}
    for b in arms[0].data.bones:
        s["bones"][b.name] = (tuple(b.head_local), tuple(b.tail_local), b.parent.name if b.parent else None)
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        me = o.data
        bm = bmesh.new()
        bm.from_mesh(me)
        cs = [v.co for v in me.vertices]
        uv2 = None
        if len(me.uv_layers) > 1:
            uv2 = np.zeros(2 * len(me.loops))
            me.uv_layers[1].data.foreach_get("uv", uv2)
        s["meshes"][o.name] = dict(
            parent_type=o.parent_type, parent_bone=o.parent_bone, tris=scene.tri_count(me),
            bbmin=[min(c[i] for c in cs) for i in range(3)], bbmax=[max(c[i] for c in cs) for i in range(3)],
            mats=[m.name if m else None for m in me.materials], mat_idx={p.material_index for p in me.polygons},
            uv_layers=len(me.uv_layers), uv2=uv2,
            uv_out=sum(1 for lp in me.uv_layers[0].data if not (-1e-4 <= lp.uv.x <= 1.0001 and -1e-4 <= lp.uv.y <= 1.0001)) if me.uv_layers else 0,
            zero_area=sum(1 for f in bm.faces if f.calc_area() < 1e-6), loose=sum(1 for v in bm.verts if not v.link_faces),
            tri_keys=[tuple(sorted(tuple(round(c, 3) for c in me.vertices[i].co) for i in p.vertices)) for p in me.polygons],
            verts=[tuple(v.co) for v in me.vertices], polys=[tuple(p.vertices) for p in me.polygons],
            fnormals=[tuple(p.normal) for p in me.polygons],
            vnormals=[[tuple(me.corner_normals[li].vector) for li in p.loop_indices] for p in me.polygons])
        bm.free()
    return s


def sky_dirs(n=64):
    out, ga = [], math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 0.03 + 0.97 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        out.append(Vector((r * math.cos(ga * i), r * math.sin(ga * i), z)))
    return out


def new_triangle_normals(new, old):
    """New triangles: (count, winding disagrees with vertex normals, visible from the sky, back seen)."""
    old_keys = set(old["tri_keys"])
    idx = [i for i, k in enumerate(new["tri_keys"]) if k not in old_keys]
    verts = [Vector(v) for v in new["verts"]]
    bvh = BVHTree.FromPolygons(verts, new["polys"])
    dirs = sky_dirs()
    disagree = visible = back_seen = 0
    for i in idx:
        fn = Vector(new["fnormals"][i])
        if fn.dot(sum((Vector(n) for n in new["vnormals"][i]), Vector())) <= 0:
            disagree += 1
        c = sum((verts[j] for j in new["polys"][i]), Vector()) / 3
        front = back = False
        for d in dirs:
            k = fn.dot(d)
            if abs(k) < 0.05 or (front and k > 0) or (back and k < 0):
                continue
            if bvh.ray_cast(c + d * 0.01, d, 2000.0)[0] is None:
                front, back = front or k > 0, back or k < 0
        visible += front or back
        back_seen += back
    return len(idx), disagree, visible, back_seen


def uv_overlap(uv, tris, R=2048):
    """(covered texels, texels covered more than once) rasterising every triangle's UVs."""
    cnt = np.zeros((R, R), np.int16)
    for a, b, c in uv[tris] * R:
        x0, x1 = max(int(math.floor(min(a[0], b[0], c[0]))), 0), min(int(math.ceil(max(a[0], b[0], c[0]))), R)
        y0, y1 = max(int(math.floor(min(a[1], b[1], c[1]))), 0), min(int(math.ceil(max(a[1], b[1], c[1]))), R)
        if x1 <= x0 or y1 <= y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)

        def e(p, q):
            return (q[0] - p[0]) * (ys - p[1]) - (q[1] - p[1]) * (xs - p[0])
        w0, w1, w2 = e(b, c), e(c, a), e(a, b)
        cnt[y0:y1, x0:x1] += ((w0 >= 0) & (w1 >= 0) & (w2 >= 0)) | ((w0 <= 0) & (w1 <= 0) & (w2 <= 0))
    return int((cnt > 0).sum()), int((cnt > 1).sum())


def tangent_convention(m):
    """Median dots of the stored tangent with -dP/dv and binormal with +dP/du (the game's frame)."""
    P, T, B = np.array(m.verts), np.array(m.tangents), np.array(m.bitangents)
    UV, F = np.array(m.uv), np.array(m.tris)
    e1, e2 = P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]
    d1, d2 = UV[F[:, 1]] - UV[F[:, 0]], UV[F[:, 2]] - UV[F[:, 0]]
    det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    ok = np.abs(det) > 1e-10
    det = np.where(ok, det, 1)[:, None]

    def nz(a):
        return a / np.maximum(np.linalg.norm(a, axis=1, keepdims=True), 1e-12)
    du = nz((e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / det)
    dv = nz((e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / det)
    Tt, Bt = nz(T[F].mean(1)), nz(B[F].mean(1))
    return float(np.median((Tt * -dv).sum(1)[ok])), float(np.median((Bt * du).sum(1)[ok]))


def run_checks(b, ws):
    from .checks_suite import run
    return run(b, ws, Report())

