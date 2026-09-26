"""Measure EA's body mesh: the numbers a recipe used to type by hand (sagekit/measure.py has the why
and the API design() uses). Runs on Blender's Python (numpy), no Blender needed:

    python3.11 -m sagekit.blender.measure <faction/building>   -> build/.../work/measure.json

Everything is in the recipe's design frame: the target mesh's own coordinates, or model space for
`world_space` recipes (the mesh taken through its bone) - the frame design() builds in. Units are
the game's. The mesh is read from EA's file (the source model), never from our build.
"""
import json
import math
import os
import sys
from collections import deque

import numpy as np

COS_PLANE = math.cos(math.radians(4))        # triangles within 4 degrees and PLANE_TOL units: one plane
PLANE_TOL = 0.12
GRID = 0.5                                   # openings and heights are rasterised at 0.5 units


# ------------------------------------------------------------------------------------ geometry
def triangles(P, T):
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    cr = np.cross(b - a, c - a)
    area = np.linalg.norm(cr, axis=1) / 2
    n = cr / np.maximum(2 * area, 1e-12)[:, None]
    return n, area, (a + b + c) / 3


def hull(pts):
    """Convex hull (counter-clockwise) of 2D points, collinear points dropped."""
    pts = sorted(set(map(tuple, np.round(pts, 3))))
    if len(pts) < 3:
        return pts

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and (out[-1][0] - out[-2][0]) * (p[1] - out[-2][1]) - \
                    (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0]) <= 1e-6:
                out.pop()
            out.append(p)
        return out
    lo, hi = half(pts), half(pts[::-1])
    return lo[:-1] + hi[:-1]


def polygon_area(poly):
    return 0.5 * abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1])))


def axes_for(n):
    """In-plane axes (u, v): u horizontal and v up for walls; x and y for floors and roofs."""
    if abs(n[2]) < 0.7:
        u = np.array([-n[1], n[0], 0.0])
        u /= np.linalg.norm(u)
        return u, np.array([0.0, 0.0, 1.0])
    return np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])


def raster(P2, T, lo, shape, grid=GRID):
    """Boolean coverage of 2D triangles on a grid (cell centres), origin lo."""
    cov = np.zeros(shape, bool)
    for t in T:
        a, b, c = P2[t[0]], P2[t[1]], P2[t[2]]
        x0, y0 = np.floor((np.minimum(np.minimum(a, b), c) - lo) / grid).astype(int)
        x1, y1 = np.ceil((np.maximum(np.maximum(a, b), c) - lo) / grid).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, shape[0]), min(y1, shape[1])
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(lo[0] + (np.arange(x0, x1) + 0.5) * grid, lo[1] + (np.arange(y0, y1) + 0.5) * grid, indexing="ij")

        def e(p, q):
            return (q[0] - p[0]) * (gy - p[1]) - (q[1] - p[1]) * (gx - p[0])
        w0, w1, w2 = e(b, c), e(c, a), e(a, b)
        cov[x0:x1, y0:y1] |= ((w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)) | ((w0 <= 1e-9) & (w1 <= 1e-9) & (w2 <= 1e-9))
    return cov


def components(mask):
    """[[(i, j)...]] 4-connected components of a boolean grid."""
    seen, out = np.zeros(mask.shape, bool), []
    for i, j in zip(*np.nonzero(mask)):
        if seen[i, j]:
            continue
        comp, q = [], deque([(i, j)])
        seen[i, j] = True
        while q:
            a, b = q.popleft()
            comp.append((a, b))
            for x, y in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                if 0 <= x < mask.shape[0] and 0 <= y < mask.shape[1] and mask[x, y] and not seen[x, y]:
                    seen[x, y] = True
                    q.append((x, y))
        out.append(comp)
    return out


# ------------------------------------------------------------------------------------ measurements
def planes(P, T, n, area, cen, keep=24):
    """Dominant face planes, largest first: normal, offset (n.p), area, in-plane extents."""
    free = np.ones(len(T), bool)
    order = np.argsort(-area)
    out = []
    d_all = (n * cen).sum(1)
    for i in order:
        if not free[i] or area[i] < 1e-6:
            continue
        sel = free & ((n @ n[i]) > COS_PLANE) & (np.abs(d_all - d_all[i]) < PLANE_TOL)
        free &= ~sel
        a = area[sel].sum()
        nn = (n[sel] * area[sel, None]).sum(0)
        nn /= np.linalg.norm(nn)
        u, v = axes_for(nn)
        V = P[np.unique(T[sel])]
        out.append({"normal": [round(float(x), 3) for x in nn], "offset": round(float((d_all[sel] * area[sel]).sum() / a), 2),
                    "area": round(float(a), 1), "tris": int(sel.sum()),
                    "kind": "wall" if abs(nn[2]) < 0.2 else "floor" if nn[2] > 0.95 else "underside" if nn[2] < -0.95
                    else "slope" if nn[2] > 0 else "overhang",
                    "u_axis": [round(float(x), 3) for x in u], "u": [round(float((V @ u).min()), 2), round(float((V @ u).max()), 2)],
                    "v_axis": [round(float(x), 3) for x in v], "v": [round(float((V @ v).min()), 2), round(float((V @ v).max()), 2)],
                    "_sel": sel})
    out.sort(key=lambda p: -p["area"])
    total = area.sum()
    return [p for p in out if p["area"] >= 0.004 * total][:keep]


def levels(n, area, cen, P, T, zmin, H):
    """Horizontal up-facing area by height: the ledges, walkways and roofs (peaks), low to high."""
    up = n[:, 2] > 0.95
    if not up.any():
        return []
    z = cen[up, 2]
    bins = np.round(z / 0.1).astype(int)
    acc = {}
    for b, a in zip(bins, area[up]):
        acc[b] = acc.get(b, 0) + a
    out, total = [], area[up].sum()
    for b in sorted(acc):
        if out and b * 0.1 - out[-1][0] <= 0.3:        # merge within 0.3 units
            z0, a0 = out[-1]
            out[-1] = ((z0 * a0 + b * 0.1 * acc[b]) / (a0 + acc[b]), a0 + acc[b])
        else:
            out.append((b * 0.1, acc[b]))
    return [{"z": round(float(z), 2), "area": round(float(a), 1)} for z, a in out if a >= max(0.003 * total, 0.5)]


def section(P, T, z):
    """(xmin, xmax, ymin, ymax) of the mesh's cross-section at height z, or None."""
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    pts = []
    for p, q in ((a, b), (b, c), (c, a)):
        s = (p[:, 2] - z) * (q[:, 2] - z) < 0
        if s.any():
            t = ((z - p[s, 2]) / (q[s, 2] - p[s, 2]))[:, None]
            pts.append(p[s, :2] + t * (q[s, :2] - p[s, :2]))
    if not pts:
        return None
    pts = np.concatenate(pts)
    return pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max()


def profile(P, T, zmin, zmax, step=0.25, jump=0.25):
    """The outline's setbacks: heights where the cross-section's extent changes by more than `jump`
    (a plinth, a band, the head over the shaft), with the extents above and below."""
    rows = []
    for z in np.arange(zmin + step / 2, zmax, step):
        s = section(P, T, z)
        if s:
            rows.append((float(z),) + tuple(float(x) for x in s))
    out = []
    for r0, r1 in zip(rows, rows[1:]):
        d = max(abs(a - b) for a, b in zip(r0[1:], r1[1:]))
        if d > jump:
            out.append({"z": round((r0[0] + r1[0]) / 2, 2), "below": [round(x, 2) for x in r0[1:]],
                        "above": [round(x, 2) for x in r1[1:]]})
    return out, rows


def openings(P, T, n, plist, H):
    """Doors, arches and niches in the big walls: cells of a wall's own rectangle its faces leave
    open, not touching its sides or top (a door may touch the ground), at least 1.5 x 2 units.
    A recess is closed behind by a parallel face (its depth given); a hole is open."""
    out = []
    d_all = (n * ((P[T[:, 0]] + P[T[:, 1]] + P[T[:, 2]]) / 3)).sum(1)
    for k, p in enumerate(plist):
        if p["kind"] != "wall" or p["area"] < 0.01 * H * H:
            continue
        nn, u = np.array(p["normal"]), np.array(p["u_axis"])
        P2 = np.stack([P @ u, P[:, 2]], 1)
        lo = np.array([p["u"][0], p["v"][0]])
        shape = tuple(int(math.ceil(x)) for x in (np.array([p["u"][1], p["v"][1]]) - lo) / GRID)
        if min(shape) < 4 or shape[0] * shape[1] > 400000:
            continue
        cov = raster(P2, T[p["_sel"]], lo, shape)
        par = np.abs(n @ nn - 1) < 1 - COS_PLANE
        behind = par & (d_all < p["offset"] - 0.2) & (d_all > p["offset"] - 12)
        front = par & (d_all > p["offset"] + 0.2) & (d_all < p["offset"] + 12)
        ahead = raster(P2, T[front], lo, shape) if front.any() else np.zeros(shape, bool)
        for comp in components(~cov):
            ij = np.array(comp)
            if ij[:, 0].min() == 0 or ij[:, 0].max() == shape[0] - 1 or ij[:, 1].max() == shape[1] - 1:
                continue
            w, h = (ij[:, 0].ptp() + 1) * GRID, (ij[:, 1].ptp() + 1) * GRID
            if w < 1.5 or h < 2.0:
                continue
            u0, u1 = lo[0] + ij[:, 0].min() * GRID, lo[0] + (ij[:, 0].max() + 1) * GRID
            z0, z1 = lo[1] + ij[:, 1].min() * GRID, lo[1] + (ij[:, 1].max() + 1) * GRID
            if ahead[ij[:, 0], ij[:, 1]].mean() > 0.5:
                continue                        # a pilaster, frame or buttress standing proud: not an opening
            depth = None
            if behind.any():
                back = raster(P2, T[behind], lo, shape)
                hit = back[ij[:, 0], ij[:, 1]]
                if hit.mean() > 0.5:
                    ds = d_all[behind]
                    depth = round(float(p["offset"] - np.median(ds)), 2)
            tops = {}
            for i, j in comp:
                tops[i] = max(tops.get(i, 0), j)
            cols = sorted(tops)
            mid, side = tops[cols[len(cols) // 2]], min(tops[cols[0]], tops[cols[-1]])
            out.append({"plane": k, "normal": p["normal"], "offset": p["offset"], "u": [round(u0, 2), round(u1, 2)],
                        "centre_u": round((u0 + u1) / 2, 2), "z": [round(z0, 2), round(z1, 2)], "width": w, "height": h,
                        "kind": "recess" if depth is not None else "hole", "depth": depth,
                        "top": "pointed or round" if (mid - side) * GRID >= 1.0 else "flat",
                        "top_z": {"middle": round(lo[1] + (mid + 1) * GRID, 2), "jambs": round(lo[1] + (side + 1) * GRID, 2)},
                        "at_ground": bool(ij[:, 1].min() == 0)})
    return out


def heightmap(P, T, lo, shape, grid=GRID):
    """Max z per cell (NaN where nothing is)."""
    hm = np.full(shape, np.nan)
    for t in T:
        tri = P[t]
        x0, y0 = np.floor((tri[:, :2].min(0) - lo) / grid).astype(int)
        x1, y1 = np.ceil((tri[:, :2].max(0) - lo) / grid).astype(int) + 1
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, shape[0]), min(y1, shape[1])
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(lo[0] + (np.arange(x0, x1) + 0.5) * grid, lo[1] + (np.arange(y0, y1) + 0.5) * grid, indexing="ij")
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
        det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(det) < 1e-9:                      # a vertical face: its roof neighbours carry its top
            continue
        l1 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / det
        l2 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / det
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        z = l1 * az + l2 * bz + l3 * cz
        cur = hm[x0:x1, y0:y1]
        hm[x0:x1, y0:y1] = np.where(inside, np.fmax(cur, z), cur)
    return hm


def heads(P, T, zmin, H, radius=6.0, prominence=3.0):
    """Tower and column heads: local maxima of the height map standing `prominence` above the
    lowest roof within `radius`, highest first, with the top's box (cells within 3 units of it)."""
    lo = P[:, :2].min(0) - GRID
    shape = tuple(int(x) for x in np.ceil((P[:, :2].max(0) + GRID - lo) / GRID))
    if shape[0] * shape[1] > 1_500_000:
        return []
    hm = heightmap(P, T, lo, shape)
    h = np.nan_to_num(hm, nan=zmin)
    r = int(radius / GRID)
    pad = np.pad(h, r, mode="edge")
    win = np.lib.stride_tricks.sliding_window_view(pad, (2 * r + 1, 2 * r + 1))
    mx, mn = win.max((2, 3)), win.min((2, 3))
    peak = (h >= mx - 1e-6) & (h - mn >= prominence) & (h >= zmin + 0.3 * H)
    out = []
    boxes = lo[0], lo[1], (P[:, 0].max() - P[:, 0].min()) * (P[:, 1].max() - P[:, 1].min())
    for comp in sorted(components(peak), key=lambda c: -max(h[i, j] for i, j in c)):
        ij = np.array(comp)
        z = float(h[ij[:, 0], ij[:, 1]].max())
        c = lo + (ij.mean(0) + 0.5) * GRID
        if any(o["top_box"][0] <= c[0] <= o["top_box"][1] and o["top_box"][2] <= c[1] <= o["top_box"][3] for o in out):
            continue                            # another peak of a head already found (a crown's merlons)
        (i0, j0), k = ij[0], 8 * r              # the top: cells within 3 units of it, around it
        win = (slice(max(i0 - k, 0), i0 + k + 1), slice(max(j0 - k, 0), j0 + k + 1))
        top = next(np.array(t) for t in components(h[win] >= z - 3.0) if (i0 - win[0].start, j0 - win[1].start) in t)
        top += [win[0].start, win[1].start]
        b0, b1 = lo + top.min(0) * GRID, lo + (top.max(0) + 1) * GRID
        if (b1 - b0).prod() > 0.1 * boxes[2] and z < zmin + 0.9 * H:
            continue                            # a roof or walkway, not a head
        m = (b0 + b1) / 2
        out.append({"centre": [round(float(m[0]), 2), round(float(m[1]), 2)], "z": round(z, 2),
                    "top_box": [round(float(b0[0]), 2), round(float(b1[0]), 2), round(float(b0[1]), 2), round(float(b1[1]), 2)]})
    return sorted(out, key=lambda o: -o["z"])[:24]


def symmetry(P, tol=0.3):
    """Mirror axes (x = c, y = c, the diagonal through the centre) and the quarter turn that map at
    least 95% of the vertices onto vertices (cells of `tol`, neighbours included)."""
    V = np.unique(np.round(P, 2), axis=0)
    K = np.array([1 << 42, 1 << 21, 1], np.int64)

    def cells(Q):
        return (np.floor(Q / tol).astype(np.int64) + (1 << 20)) @ K
    have = np.unique(cells(V))
    offsets = np.array([(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)], np.int64) @ K

    def score(Q):
        q = cells(Q)
        return float(np.any([np.isin(q + o, have) for o in offsets], axis=0).mean())
    cx, cy = (V[:, 0].min() + V[:, 0].max()) / 2, (V[:, 1].min() + V[:, 1].max()) / 2
    mx, my = V[:, 0].mean(), V[:, 1].mean()
    out = []
    for name, f, cs in (("mirror x = c", lambda c: V * [-1, 1, 1] + [2 * c, 0, 0], (cx, mx)),
                        ("mirror y = c", lambda c: V * [1, -1, 1] + [0, 2 * c, 0], (cy, my))):
        tries = {round(c0 + d, 2) for c0 in cs for d in np.arange(-3, 3.01, 0.05)}
        scored = [(score(f(c)), c) for c in sorted(tries)]
        top = max(sc for sc, _ in scored)
        plateau = [c for sc, c in scored if sc >= top - 0.002]     # the cells tolerate a band of c: its middle
        if top >= 0.95:
            out.append({"axis": name, "c": round(float(np.median(plateau)), 2), "match": round(top, 3)})
    for name, f in (("mirror diagonal x - cx = y - cy", lambda Q: np.stack([Q[:, 1] - cy + cx, Q[:, 0] - cx + cy, Q[:, 2]], 1)),
                    ("turn 90 degrees about (cx, cy)", lambda Q: np.stack([cx - (Q[:, 1] - cy), cy + (Q[:, 0] - cx), Q[:, 2]], 1))):
        sc = score(f(V))
        if sc >= 0.95:
            out.append({"axis": name, "c": [round(float(cx), 2), round(float(cy), 2)], "match": round(sc, 3)})
    return out


# ------------------------------------------------------------------------------------ the job
def measure(P, T):
    P, T = np.asarray(P, float), np.asarray(T, int)
    n, area, cen = triangles(P, T)
    lo, hi = P.min(0), P.max(0)
    H = float(hi[2] - lo[2])
    hl = hull(P[:, :2])
    pl = planes(P, T, n, area, cen)
    lv = levels(n, area, cen, P, T, lo[2], H)
    steps, rows = profile(P, T, lo[2], hi[2])
    big = [x for x in lv if x["z"] > lo[2] + 0.2]
    bands = {"ground": round(float(lo[2]), 2), "top": round(float(hi[2]), 2),
             "plinth_top": next((x["z"] for x in big if x["z"] <= lo[2] + 0.3 * H), None),
             "roof": max(big, key=lambda x: (x["area"] >= 0.2 * max(y["area"] for y in big), x["z"]))["z"] if big else None}
    bands["walkways"] = [x["z"] for x in big if x["z"] not in (bands["plinth_top"], bands["roof"])
                         and x["area"] >= 0.05 * max(y["area"] for y in big)]
    out = {"tris": len(T), "bbox": [[round(float(x), 2) for x in lo], [round(float(x), 2) for x in hi]],
           "footprint": {"hull": [[round(x, 2), round(y, 2)] for x, y in hl], "area": round(polygon_area(hl), 1)},
           "planes": pl, "levels": lv, "bands": bands, "setbacks": steps,
           "openings": openings(P, T, n, pl, H), "heads": heads(P, T, lo[2], H), "symmetry": symmetry(P)}
    for p in pl:
        p.pop("_sel")
    return out


def run(building_id):
    from ..formats.w3d import W3DFile
    from ..formats.w3dframes import apply, mesh_frames
    from ..game import Install
    from ..registry import load
    from ..workspace import Workspace
    b, g = load(building_id), Install()
    data = g.read(g.model_path(b.source))
    mesh = W3DFile(data).meshes[b.target]
    frame = mesh_frames(data, lambda skl: g.read(g.model_path(skl[:-4])))[b.target]
    P = [apply(frame, v) for v in mesh.verts] if b.world_space else mesh.verts
    out = {"building": b.id, "model": b.source, "mesh": b.target,
           "space": "model (world_space)" if b.world_space else "mesh-local", "bone_frame": frame}
    out.update(measure(P, mesh.tris))
    path = Workspace(b).path("work", "measure.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    return path, out


def summary(m):
    lo, hi = m["bbox"]
    lines = ["%s %s (%s, %d tris): x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f" % (
        m["model"], m["mesh"], m["space"], m["tris"], lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])]
    lines.append("  bands: %s" % m["bands"])
    lines.append("  levels (z: area): %s" % ", ".join("%.2f: %.0f" % (x["z"], x["area"]) for x in m["levels"]))
    for p in m["planes"][:12]:
        lines.append("  plane %-9s n %-22s d %7.2f area %7.1f  u %s  v %s" % (p["kind"], p["normal"], p["offset"], p["area"], p["u"], p["v"]))
    for s in m["setbacks"][:16]:
        lines.append("  setback z %.2f: %s -> %s" % (s["z"], s["below"], s["above"]))
    for o in m["openings"]:
        lines.append("  %s in plane %d (n %s d %.2f): u %s z %s, %s top %s%s" % (
            o["kind"], o["plane"], o["normal"], o["offset"], o["u"], o["z"], o["top"], o["top_z"],
            ", depth %.2f" % o["depth"] if o["depth"] is not None else ""))
    for h in m["heads"]:
        lines.append("  head at %s z %.2f, top box %s" % (h["centre"], h["z"], h["top_box"]))
    lines.append("  symmetry: %s" % (", ".join("%s (c %s, %.1f%%)" % (s["axis"], s["c"], 100 * s["match"]) for s in m["symmetry"]) or "none"))
    return "\n".join(lines)


if __name__ == "__main__":
    p, m = run(sys.argv[1])
    print(summary(m))
    print("wrote", os.path.relpath(p))
