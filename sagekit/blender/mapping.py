"""UVs for new geometry on the ORIGINAL atlas: every new face shows real painted stone, friezes and
reliefs (the painter later re-projects all of it into the building's own layout).

AtlasMapper.map(pts, tag) -> [(3D points, UVs)] pieces of one planar convex polygon:
  TILE     plain material: one tile at the atlas density when it fits (random placement, so
           neighbours differ), shrunk into one if at most `max_shrink` too big, else tiled;
  BAND     a frieze along the face (tag|v: up the face, tag|a: along its longest edge), cut into
           whole pattern repeats;
  STRETCH  one motif fitted to the face (pilaster strips, statue reliefs).
"""
import math
import random

from mathutils import Vector as V

from ..atlas import Region
from .geometry import Z, poly_area


def frame(normal):
    n = normal.normalized()
    t = Z.cross(n)
    if t.length < 1e-4:
        t = V((1, 0, 0))
    t.normalize()
    return t, n.cross(t).normalized()


def clip(poly2, poly3, axis, lo, hi):
    """Clip a convex polygon (2D coords paired with 3D points) to lo <= coord[axis] <= hi."""
    def cut(pts, keep, lim):
        out = []
        for i in range(len(pts)):
            A, B = pts[i], pts[(i + 1) % len(pts)]
            ia, ib = keep(A[0][axis]), keep(B[0][axis])
            if ia:
                out.append(A)
            if ia != ib:
                f = (lim - A[0][axis]) / (B[0][axis] - A[0][axis])
                out.append((A[0].lerp(B[0], f), A[1].lerp(B[1], f)))
        return out
    pts = list(zip(poly2, poly3))
    pts = cut(pts, lambda x: x >= lo - 1e-9, lo)
    if len(pts) < 3:
        return []
    pts = cut(pts, lambda x: x <= hi + 1e-9, hi)
    return pts if len(pts) >= 3 else []


class AtlasMapper:
    def __init__(self, atlas, seed=7):
        self.atlas = atlas
        self.rng = random.Random(seed)

    def _uv(self, x, y):
        """Atlas pixel (x right, y down) -> Blender UV."""
        s = float(self.atlas.size)
        return (x / s, 1.0 - y / s)

    def _axes(self, pts, tag):
        _, nn = poly_area(pts)
        t, b = frame(nn)
        if tag.endswith("|v"):
            return tag[:-2], b, -t
        if tag.endswith("|a"):
            e = max(((pts[(i + 1) % len(pts)] - pts[i]) for i in range(len(pts))), key=lambda v: v.length)
            e = e - nn.normalized() * e.dot(nn.normalized())
            t = e.normalized()
            b = nn.normalized().cross(t)
            if b.z < -1e-6 or (abs(b.z) < 1e-6 and b.x + b.y < 0):
                t, b = -t, -b
            return tag[:-2], t, b
        return tag, t, b

    def map(self, pts, tag):
        name, t, b = self._axes(pts, tag)
        reg = self.atlas.regions[name]
        x0, y0, x1, y1 = reg.rect
        W, H = reg.size
        p2 = [V((p.dot(t), p.dot(b))) for p in pts]
        umin, umax = min(q.x for q in p2), max(q.x for q in p2)
        vmin, vmax = min(q.y for q in p2), max(q.y for q in p2)
        if reg.kind == Region.STRETCH:
            su, sv = W / max(umax - umin, 1e-6), H / max(vmax - vmin, 1e-6)
            return [(pts, [self._uv(x0 + (q.x - umin) * su, y1 - (q.y - vmin) * sv) for q in p2])]
        if reg.kind == Region.BAND:
            return self._band(reg, p2, pts, umin, umax, vmin, vmax)
        return self._tile(reg, p2, pts, umin, umax, vmin, vmax)

    def _band(self, reg, p2, pts, umin, umax, vmin, vmax):
        x0, y0, x1, y1 = reg.rect
        W, H = reg.size
        sv = H / max(vmax - vmin, 1e-6)
        if reg.period:
            su = min(sv, 7.0)
            k = max(1, int(W // reg.period))          # tile = whole pattern repeats
            Lt = k * reg.period / su
        else:
            su = reg.su or sv
            Lt = W / su
        pieces, u, i = [], umin, 0
        while u < umax - 1e-6:
            lo, hi = umin + i * Lt, umin + (i + 1) * Lt
            pc = clip(p2, pts, 0, lo, hi)
            if pc:
                pieces.append(([q[1] for q in pc],
                               [self._uv(x0 + (q[0].x - lo) * su, y1 - (q[0].y - vmin) * sv) for q in pc]))
            i += 1
            u = hi
        return pieces

    def _tile(self, reg, p2, pts, umin, umax, vmin, vmax):
        x0, y0, x1, y1 = reg.rect
        W, H = reg.size
        s = self.atlas.density
        eu, ev = (umax - umin) * s, (vmax - vmin) * s
        fit = max(eu / W, ev / H)
        if 1.0 < fit <= self.atlas.max_shrink:
            s = s / fit * 0.999
            eu, ev = eu / fit, ev / fit
        if eu <= W and ev <= H:
            ou, ov = self.rng.uniform(0, W - eu), self.rng.uniform(0, H - ev)
            return [(pts, [self._uv(x0 + ou + (q.x - umin) * s, y1 - ov - (q.y - vmin) * s) for q in p2])]
        Tu, Tv = W / s, H / s
        nu = int(math.ceil((umax - umin) / Tu - 1e-6))
        nv = int(math.ceil((vmax - vmin) / Tv - 1e-6))
        pieces = []
        for i in range(nu):
            a = clip(p2, pts, 0, umin + i * Tu, umin + (i + 1) * Tu)
            if not a:
                continue
            for j in range(nv):
                c = clip([q[0] for q in a], [q[1] for q in a], 1, vmin + j * Tv, vmin + (j + 1) * Tv)
                if c:
                    pieces.append(([q[1] for q in c],
                                   [self._uv(x0 + (q[0].x - umin - i * Tu) * s, y1 - (q[0].y - vmin - j * Tv) * s)
                                    for q in c]))
        return pieces
