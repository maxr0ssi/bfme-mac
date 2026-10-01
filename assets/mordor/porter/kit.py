"""The Mordor builder's shapes: rough basalt, hooked spikes, jagged teeth, chain links and rings.

Every function adds faces to a sagekit.units Mesh in the model's rest space, on the mesh's bone
(or `bone`). Faces are wound outward from each solid's centre (the writer's normals follow the
winding), so the convex and star-shaped pieces need no hand-ordered corners.
"""
import math


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def mul(a, s):
    return tuple(x * s for x in a)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def unit(a):
    n = math.sqrt(dot(a, a))
    return mul(a, 1 / n)


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def outward(m, pts, centre, tag, bone=None, uvs=None):
    """A face wound so its normal points away from `centre`."""
    n = cross(sub(pts[1], pts[0]), sub(pts[2], pts[0]))
    mid = mul(tuple(map(sum, zip(*pts))), 1 / len(pts))
    if dot(n, sub(mid, centre)) < 0:
        pts = pts[::-1]
        uvs = uvs[::-1] if uvs else None
    m.face(list(pts), tag, bone, uvs)


def slab(m, lo, hi, tag, bone=None):
    """A plain six-sided box (12 triangles): bands, planks and straps too small for a bevel."""
    x, y, z = lo
    X, Y, Z = hi
    c = ((x + X) / 2, (y + Y) / 2, (z + Z) / 2)
    p = [(x, y, z), (X, y, z), (X, Y, z), (x, Y, z), (x, y, Z), (X, y, Z), (X, Y, Z), (x, Y, Z)]
    for f in ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        outward(m, [p[i] for i in f], c, tag, bone)


def rock(m, c, size, rng, tag, bone=None, sides=6):
    """A rough, faceted basalt lump: three jittered rings round c (size: half extents x, y, z),
    a flattish base so it sits, and a broken top."""
    sx, sy, sz = size
    phase = rng.uniform(0, math.tau)
    rings = []
    for h, k in ((-1, .78), (-.15 + rng.uniform(-.15, .15), 1.0), (.75, .62)):
        ring = []
        for i in range(sides):
            a = phase + i * math.tau / sides + rng.uniform(-.25, .25)
            r = k * rng.uniform(.82, 1.12)
            ring.append((c[0] + sx * r * math.cos(a), c[1] + sy * r * math.sin(a),
                         c[2] + sz * (h + rng.uniform(-.08, .08) * (h > -1))))
        rings.append(ring)
    bottom = (c[0], c[1], c[2] - sz)
    top = (c[0] + sx * rng.uniform(-.2, .2), c[1] + sy * rng.uniform(-.2, .2), c[2] + sz * rng.uniform(.9, 1.15))
    for lo, hi in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            outward(m, (lo[i], lo[j], hi[j]), c, tag, bone)
            outward(m, (lo[i], hi[j], hi[i]), c, tag, bone)
    for i in range(sides):
        j = (i + 1) % sides
        outward(m, (bottom, rings[0][i], rings[0][j]), c, tag, bone)
        outward(m, (top, rings[-1][i], rings[-1][j]), c, tag, bone)


def horn(m, pts, r0, r1, tag, bone=None, sides=5, tip=None):
    """A tapering, bending spike along the polyline pts (radius r0 to r1); `tip` gives its last
    segment another tag (the steel point)."""
    n = len(pts) - 1
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        ra, rb = r0 + (r1 - r0) * i / n, r0 + (r1 - r0) * (i + 1) / n
        m.tube(a, b, ra, tip if tip is not None and i == n - 1 else tag, bone, sides=sides, r1=rb)


def hook(m, base, up, out, h, r, tag, bone=None, tip=None, sides=5):
    """The citadel's hooked spike in small: rising `h` from base along `up`, leaning out along
    `out`, its point curling back over."""
    up, out = unit(up), unit(out)
    pts = [base]
    for t, o in ((.35, .12), (.65, .32), (.88, .42), (1.0, .30)):
        pts.append(add(base, add(mul(up, h * t), mul(out, h * o))))
    horn(m, pts, r, r * .06, tag, bone, sides, tip)


def blade(m, a, b, tip, thick, tag, bone=None):
    """A flat triangular tooth (a, b its base, `tip` its point), `thick` deep."""
    n = unit(cross(sub(b, a), sub(tip, a)))
    off = mul(n, thick / 2)
    front = [add(p, off) for p in (a, b, tip)]
    back = [sub(p, off) for p in (a, b, tip)]
    c = mul(add(add(a, b), tip), 1 / 3)
    outward(m, front, c, tag, bone)
    outward(m, back, c, tag, bone)
    for i in range(3):
        j = (i + 1) % 3
        outward(m, (front[i], front[j], back[j], back[i]), c, tag, bone)


def link(m, c, d, w, length, r, tag, bone=None):
    """One chain link: a rhombus of four bars round c, its long axis along d, its plane along w."""
    d, w = mul(unit(d), length / 2), mul(unit(w), length * .3)
    p = [add(c, d), add(c, w), sub(c, d), sub(c, w)]
    for i in range(4):
        m.tube(p[i], p[(i + 1) % 4], r, tag, bone, sides=3)


def chain(m, a, b, sag, size, r, tag, bone=None):
    """A hanging chain from a to b sagging `sag` at its middle, links alternating their plane."""
    span = math.dist(a, b)
    count = max(2, int(span / (size * .78)))
    pts = []
    for i in range(count + 1):
        t = i / count
        p = lerp(a, b, t)
        pts.append((p[0], p[1], p[2] - sag * 4 * t * (1 - t)))
    side = unit(cross(sub(b, a), (0, 0, 1)))
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        d = sub(q, p)
        w = side if i % 2 else unit(cross(d, side))
        link(m, lerp(p, q, .5), d, w, math.dist(p, q) * 1.25, r, tag, bone)
    return pts


def ring(m, c, axis, radius, r, tag, bone=None, segments=8, sides=4):
    """A round iron ring (a shackle's cuff) round c, its axis along `axis`."""
    axis = unit(axis)
    u = unit(cross(axis, (0, 0, 1) if abs(axis[2]) < .9 else (0, 1, 0)))
    v = cross(axis, u)
    pts = [add(c, add(mul(u, radius * math.cos(i * math.tau / segments)), mul(v, radius * math.sin(i * math.tau / segments))))
           for i in range(segments)]
    for i in range(segments):
        m.tube(pts[i], pts[(i + 1) % segments], r, tag, bone, sides=sides)


def disc_ring(m, c, y0, y1, r0, r1, tag, bone, segments=24):
    """A flat annulus on the wheel's axis (along y), from y0 to y1 and r0 to r1 about c (x, z)."""
    cx, cz = c
    for i in range(segments):
        a, b = i * math.tau / segments, (i + 1) * math.tau / segments
        P = lambda r, ang, y: (cx + r * math.cos(ang), y, cz + r * math.sin(ang))  # noqa: E731
        for y, flip in ((y0, False), (y1, True)):
            q = [P(r0, a, y), P(r1, a, y), P(r1, b, y), P(r0, b, y)]
            m.face(q[::-1] if flip else q, tag, bone)
        for r in (r0, r1):
            q = [P(r, a, y0), P(r, a, y1), P(r, b, y1), P(r, b, y0)]
            m.face(q[::-1] if r == r0 else q, tag, bone)
