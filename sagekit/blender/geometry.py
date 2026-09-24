"""Closed solids for new building geometry (mathutils only, no bpy ops).

A Solid is a list of [polygon, atlas tag, keep]: `keep` False marks a buried face (dropped, but it
still orients the solid). Tags are atlas Region names; 'name|v' runs a band vertically, 'name|a'
along the polygon's longest edge. Every constructor returns oriented solids (outward normals).
"""
from mathutils import Vector as V

Z = V((0, 0, 1))
DEFAULT_TAG = "stoneA"


def poly_area(p):
    """(area, unnormalised normal) of a planar polygon."""
    n = V((0, 0, 0))
    for i in range(len(p)):
        n += p[i].cross(p[(i + 1) % len(p)])
    return n.length / 2, n


def dedupe(p, eps=1e-5):
    out = []
    for q in p:
        if not out or (q - out[-1]).length > eps:
            out.append(q)
    if len(out) > 1 and (out[0] - out[-1]).length <= eps:
        out.pop()
    return out


class Solid:
    def __init__(self):
        self.polys = []

    def add(self, pts, tag, keep=True):
        pts = dedupe([V(p) for p in pts])
        if len(pts) >= 3 and poly_area(pts)[0] > 1e-6:
            self.polys.append([pts, tag, keep])

    def orient(self):
        """Flip every polygon if the signed volume is negative."""
        vol = 0.0
        for p, _, _ in self.polys:
            for i in range(1, len(p) - 1):
                vol += p[0].dot(p[i].cross(p[i + 1]))
        if vol < 0:
            for e in self.polys:
                e[0] = list(reversed(e[0]))
        return self


def loft(rings, tags, cap0=("top", False), cap1=("top", True)):
    """Skin a stack of rings (equal point counts, same winding). tags: one per ring interval, either
    a tag for every side or a list (one per side; None = buried)."""
    s = Solid()
    n = len(rings[0])
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(n):
            k = (j + 1) % n
            tg = tags[i][j] if isinstance(tags[i], (list, tuple)) else tags[i]
            s.add([a[j], a[k], b[k], b[j]], tg or DEFAULT_TAG, tg is not None)
    s.add(list(reversed(rings[0])), cap0[0], cap0[1])
    s.add(list(rings[-1]), cap1[0], cap1[1])
    return s.orient()


def rect_ring(c, t, n, u0, u1, d0, d1, z, ch=0.0):
    """Rectangle (optionally chamfered) in the plane z: u along t, d along n, around c."""
    c = V((c[0], c[1], z))
    t = V((t[0], t[1], 0))
    n = V((n[0], n[1], 0))

    def P(u, d):
        return c + t * u + n * d
    if ch <= 0:
        return [P(u0, d0), P(u1, d0), P(u1, d1), P(u0, d1)]
    return [P(u0 + ch, d0), P(u1 - ch, d0), P(u1, d0 + ch), P(u1, d1 - ch),
            P(u1 - ch, d1), P(u0 + ch, d1), P(u0, d1 - ch), P(u0, d0 + ch)]


def box_rings(xs, ys, z, ch):
    """Axis-aligned rect_ring: sides 0 (y0), 1 (+X), 2 (y1), 3 (-X); chamfered: 8 sides from y0."""
    return rect_ring((0, 0), (1, 0), (0, 1), xs[0], xs[1], ys[0], ys[1], z, ch)


def sweep(path, profile, tags, cap_start=True, cap_end=True, center=(0, 0)):
    """Mitred sweep of a closed convex (d, z) profile along a 2D polyline; d is measured along the
    outward normal (away from `center`). Returns (one Solid per segment, [(a, b, t, n)])."""
    P = [V((p[0], p[1])) for p in path]
    closed = (P[0] - P[-1]).length < 1e-6
    segs = []
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        t = (b - a).normalized()
        n = V((t.y, -t.x))
        if n.dot((a + b) / 2 - V(center)) < 0:
            n = -n
        segs.append((a, b, t, n))
    M = []
    for i in range(len(P)):
        if (i == 0 or i == len(P) - 1) and closed:
            n0, n1 = segs[-1][3], segs[0][3]
            M.append((n0 + n1) / (1 + n0.dot(n1)))
        elif i == 0:
            M.append(segs[0][3])
        elif i == len(P) - 1:
            M.append(segs[-1][3])
        else:
            n0, n1 = segs[i - 1][3], segs[i][3]
            M.append((n0 + n1) / (1 + n0.dot(n1)))
    out = []
    for i, (a, b, t, n) in enumerate(segs):
        r0 = [V((a.x + M[i].x * d, a.y + M[i].y * d, z)) for d, z in profile]
        r1 = [V((b.x + M[i + 1].x * d, b.y + M[i + 1].y * d, z)) for d, z in profile]
        s = Solid()
        m = len(profile)
        for j in range(m):
            k = (j + 1) % m
            s.add([r0[j], r0[k], r1[k], r1[j]], tags[j] or DEFAULT_TAG, tags[j] is not None)
        s.add(list(reversed(r0)), "stoneB", cap_start and i == 0 and not closed)
        s.add(list(r1), "stoneB", cap_end and i == len(segs) - 1 and not closed)
        out.append(s.orient())
    return out, segs


def prism_uz(a, t, n, poly, d0, d1, tags, front, back, bat=0.0):
    """A convex polygon in the plane of t (u) and z at anchor a, extruded along n from d0 to d1.
    tags: one per polygon edge (None = buried); front/back: cap tags at d1/d0 (None = buried).
    bat: the front leans back by bat per unit of height above the polygon's lowest point."""
    zmin = min(z for _, z in poly)

    def P(u, d, z):
        return V((a.x + t.x * u + n.x * d, a.y + t.y * u + n.y * d, z))
    r0 = [P(u, d0, z) for u, z in poly]
    r1 = [P(u, d1 - bat * (z - zmin), z) for u, z in poly]
    return loft([r0, r1], [tags], cap0=(back or "stoneB", back is not None), cap1=(front or "stoneB", front is not None))
