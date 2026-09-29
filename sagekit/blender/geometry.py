"""Closed solids for new building geometry (mathutils only, no bpy ops).

A Solid is a list of [polygon, atlas tag, keep]: `keep` False marks a buried face (dropped, but it
still orients the solid). Tags are atlas Region names; 'name|v' runs a band vertically, 'name|a'
along the polygon's longest edge. Every constructor returns oriented solids (outward normals).
"""
from mathutils import Vector as V

Z = V((0, 0, 1))
DEFAULT_TAG = "stoneA"


def poly_area(p):
    """(area, unnormalised normal) of a planar polygon, in doubles about the vertices' mean.
    mathutils is single precision: summed about the world origin, a 1 cm face at 150 units lost its
    area and tilted its normal (up to 2.6 degrees on goblins/fortress)."""
    q = [(float(v[0]), float(v[1]), float(v[2])) for v in p]
    if not q:
        return 0.0, V((0, 0, 0))
    ox, oy, oz = (sum(a[k] for a in q) / len(q) for k in range(3))
    q = [(x - ox, y - oy, z - oz) for x, y, z in q]
    nx = ny = nz = 0.0
    for (ax, ay, az), (bx, by, bz) in zip(q, q[1:] + q[:1]):
        nx += ay * bz - az * by
        ny += az * bx - ax * bz
        nz += ax * by - ay * bx
    return (nx * nx + ny * ny + nz * nz) ** 0.5 / 2, V((nx, ny, nz))


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
        if signed_volume([p for p, _, _ in self.polys]) < 0:
            for e in self.polys:
                e[0] = list(reversed(e[0]))
        return self


def signed_volume(polys):
    """Six times the volume a closed polygon set encloses (negative: wound inwards), in doubles about
    the vertices' mean. mathutils is single precision: summed about the world origin, the terms of a
    0.2-unit solid at 150 units are ~1e6 against a volume of ~1e-2, so the sign was noise."""
    pts = [(float(v[0]), float(v[1]), float(v[2])) for p in polys for v in p]
    if not pts:
        return 0.0
    ox, oy, oz = (sum(q[k] for q in pts) / len(pts) for k in range(3))
    vol, i = 0.0, 0
    for p in polys:
        q = [(x - ox, y - oy, z - oz) for x, y, z in pts[i:i + len(p)]]
        i += len(p)
        ax, ay, az = q[0]
        for (bx, by, bz), (cx, cy, cz) in zip(q[1:-1], q[2:]):
            vol += ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz) + az * (bx * cy - by * cx)
    return vol


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


def box(x0, x1, y0, y1, z0, z1, tags="stoneA", cap0=("stoneB", False), cap1=("top", True), ch=0.0):
    """An axis-aligned block, chamfered by `ch`; tags per side (0: -y, 1: +x, 2: +y, 3: -x) or one
    for all; cap0 and cap1 (tag, keep) close its bottom and top."""
    return loft([box_rings((x0, x1), (y0, y1), z0, ch), box_rings((x0, x1), (y0, y1), z1, ch)], [tags],
                cap0=cap0, cap1=cap1)


def closed(solids):
    """Keep every face of `solids`, the buried ones too: for pieces on a one-sided shell (EA's
    single-plane walls, level-up meshes), where the sky check would look in behind a buried back."""
    for s in solids:
        for p in s.polys:
            p[2] = True
    return solids


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


def check_orient():
    """Standalone check (Blender -b --python sagekit/blender/geometry.py): small convex boxes and
    spikes far from the origin, lofted from rings of either winding, come out with every face
    pointing away from their centre (tested in doubles). Single-precision orient() failed 215 of 800."""
    def inside_out(s):
        pts = [tuple(map(float, q)) for p, _, _ in s.polys for q in p]
        c = [sum(q[k] for q in pts) / len(pts) for k in range(3)]
        for p, _, _ in s.polys:
            q = [[float(v[k]) - c[k] for k in range(3)] for v in p]
            n = V((0, 0, 0))
            for a, b in zip(q, q[1:] + q[:1]):
                n += V(a).cross(V(b))
            if n.dot(V([sum(v[k] for v in q) for k in range(3)])) < 0:
                return True
        return False
    bad = cases = 0
    for size in (0.1, 0.2, 0.5, 1.0):
        for i in range(50):
            x, y, z = 150 + 0.37 * i, -120 - 0.21 * i, 130 + 0.13 * i
            for rev in (1, -1):
                r0 = box_rings((x, x + size), (y, y + size), z, 0)[::rev]
                r1 = box_rings((x, x + size), (y, y + size), z + size, 0)[::rev]
                apex = [V((x + size / 2, y + size / 2, z + 4 * size))] * 4
                for s in (loft([r0, r1], ["stoneA"]), loft([r0, apex], ["stoneA"])):
                    cases += 1
                    bad += inside_out(s)
    assert bad == 0, "%d of %d small far solids inside out" % (bad, cases)
    print("orient: %d small solids at ~(150, -120, 130), both windings, all outward" % cases)


def check_poly_area():
    """Standalone check: tiny planar polygons (3-8 sides, 2 mm to 20 cm, any orientation) around
    (150, -120, 130) give the area and normal of an exact rational computation on the same float32
    points (area to 1e-9 relative, normal to 1e-4 degrees). Single precision failed all 400 (area
    off up to 459 times, normals up to 169 degrees)."""
    import math
    import random
    from fractions import Fraction

    def exact(p):
        q = [[Fraction(float(c)) for c in v] for v in p]
        n = [Fraction(0)] * 3
        for a, b in zip(q, q[1:] + q[:1]):
            n = [n[0] + a[1] * b[2] - a[2] * b[1], n[1] + a[2] * b[0] - a[0] * b[2], n[2] + a[0] * b[1] - a[1] * b[0]]
        return [float(c) for c in n]
    rng, worst, cases = random.Random(3), [0.0, 0.0], 0
    for size in (0.002, 0.01, 0.05, 0.2):
        for i in range(100):
            c = V([base + rng.uniform(-30, 30) for base in (150, -120, 130)])
            u = V([rng.gauss(0, 1) for _ in range(3)]).normalized()
            w = u.cross(V([rng.gauss(0, 1) for _ in range(3)])).normalized()
            k = 3 + i % 6
            p = [c + (u * math.cos(2 * math.pi * j / k) + w * math.sin(2 * math.pi * j / k)) * size for j in range(k)]
            area, n = poly_area(p)
            e, n = exact(p), [float(x) for x in n]
            ea = math.sqrt(sum(x * x for x in e)) / 2
            cx = (n[1] * e[2] - n[2] * e[1], n[2] * e[0] - n[0] * e[2], n[0] * e[1] - n[1] * e[0])
            ang = math.degrees(math.atan2(math.sqrt(sum(x * x for x in cx)), sum(x * y for x, y in zip(n, e))))
            worst = [max(worst[0], abs(area - ea) / ea), max(worst[1], ang)]
            cases += 1
    assert worst[0] < 1e-9 and worst[1] < 1e-4, "poly_area off: area %.3g relative, normal %.3g degrees" % tuple(worst)
    print("poly_area: %d tiny polygons at ~(150, -120, 130): area within %.1g, normal within %.1g degrees of exact"
          % (cases, worst[0], worst[1]))


if __name__ == "__main__":
    check_orient()
    check_poly_area()
