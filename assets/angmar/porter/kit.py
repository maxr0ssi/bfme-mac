"""The Angmar builder's shapes: dressed stone blocks with snow caps, ice (crystal shards, icicles, a
faceted block), the citadel's frozen-tip tine in small, chains and wheel rings.

Ice is angular crystal, never round, as on the citadel (assets/angmar/shapes_ice.py): faceted
prisms ending in a point, icicles three-sided. Every function adds faces to a sagekit.units Mesh in
the model's rest space, on the mesh's bone (or `bone`); faces are wound outward from each solid's
centre (the writer's normals follow the winding).
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
    return mul(a, 1 / math.sqrt(dot(a, a)))


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


def hexa(m, corners, tag, bone=None, tags=None):
    """A six-sided solid from 8 corners (bottom 4, then top 4, same order); `tags` per face
    (bottom, top, then the four sides) overrides `tag`."""
    c = mul(tuple(map(sum, zip(*corners))), 1 / 8)
    faces = ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
    for k, f in enumerate(faces):
        outward(m, [corners[i] for i in f], c, tags[k] if tags else tag, bone)


def slab(m, lo, hi, tag, bone=None):
    """A plain box (12 triangles): planks, bands and straps too small for a bevel."""
    x, y, z = lo
    X, Y, Z = hi
    hexa(m, [(x, y, z), (X, y, z), (X, Y, z), (x, Y, z), (x, y, Z), (X, y, Z), (X, Y, Z), (x, Y, Z)], tag, bone)


def turned(c, sx, sy, z, yaw):
    """The four corners of a sx x sy rectangle round c (x, y), turned `yaw` radians, at height z."""
    ca, sa = math.cos(yaw), math.sin(yaw)
    return [(c[0] + dx * ca - dy * sa, c[1] + dx * sa + dy * ca, z)
            for dx, dy in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2))]


def block(m, c, size, yaw, tag, snow, rng, side=None, bone=None):
    """A dressed stone block (c its bottom centre, size x, y, z) turned `yaw`, a drift of snow
    (tag `snow`, or None) on its top. `side` tags the long faces (a lighter cut face)."""
    sx, sy, sz = size
    lo, hi = turned(c, sx, sy, c[2], yaw), turned(c, sx, sy, c[2] + sz, yaw)
    hexa(m, lo + hi, tag, bone, tags=None if side is None else (tag, tag, side, tag, side, tag))
    # the snow: a thin cap a little inside the top, thicker at its middle
    if snow is None:
        return
    k = rng.uniform(.62, .78)
    cap_lo = turned(c, sx * k, sy * k, c[2] + sz - .02, yaw + rng.uniform(-.15, .15))
    cap_hi = turned((c[0] + rng.uniform(-.15, .15), c[1] + rng.uniform(-.15, .15)), sx * k * .7, sy * k * .7,
                    c[2] + sz + rng.uniform(.12, .2), yaw)
    hexa(m, cap_lo + cap_hi, snow, bone)


def frame(d):
    """Two unit vectors square to d."""
    d = unit(d)
    s = unit(cross(d, (0, 0, 1) if abs(d[2]) < .9 else (1, 0, 0)))
    return s, cross(d, s)


def shard(m, base, d, length, r, tag, bone=None, sides=5, point=.4, tip=None, twist=.3):
    """One ice crystal: a `sides`-sided prism from base along d (r across its corners), its last
    `point` of the length a pyramid (`tip` tags it)."""
    d = unit(d)
    s, t = frame(d)
    mid = add(base, mul(d, length * (1 - point)))
    end = add(base, mul(d, length))

    def ring(c, rr, tw):
        return [add(c, add(mul(s, rr * math.cos(i * math.tau / sides + tw)), mul(t, rr * math.sin(i * math.tau / sides + tw))))
                for i in range(sides)]
    a, b = ring(base, r, 0), ring(mid, r * .92, twist)
    centre = add(base, mul(d, length * .4))
    for i in range(sides):
        j = (i + 1) % sides
        outward(m, (a[i], a[j], b[j], b[i]), centre, tag, bone)
        outward(m, (b[i], b[j], end), centre, tip if tip is not None else tag, bone)
        outward(m, (a[j], a[i], base), add(centre, mul(d, length)), tag, bone)


def icicle(m, top, length, r, tag, bone=None):
    """A three-sided icicle hanging from `top`."""
    shard(m, top, (0.04, 0.02, -1), length, r, tag, bone, sides=3, point=.7, twist=.5)


def horn(m, pts, r0, r1, tag, bone=None, sides=5, tip=None):
    """A tapering spike along the polyline pts (radius r0 to r1); `tip` tags its last segment."""
    n = len(pts) - 1
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        ra, rb = r0 + (r1 - r0) * i / n, r0 + (r1 - r0) * (i + 1) / n
        m.tube(a, b, ra, tip if tip is not None and i == n - 1 else tag, bone, sides=sides, r1=rb)


def tine(m, base, out, h, r, iron, ice, rime, bone=None, crystals=2):
    """The citadel's forged tine in small: a dark iron spike rising `h` from base, leaning out along
    `out` and curving back over at the top, its upper third frozen: cased in a faceted ice sleeve,
    a rime-white point, ice crystals growing out of the casing."""
    out = unit((out[0], out[1], 0))
    pts = [add(base, add((0, 0, h * t), mul(out, h * o))) for t, o in ((0, 0), (.3, .1), (.6, .24), (.82, .3), (1.0, .22))]
    horn(m, pts[:4], r, r * .55, iron, bone, sides=6)
    # the frozen tip: an ice sleeve from the frost line, the iron's point white with rime
    frost = pts[2]
    sleeve = lerp(pts[3], pts[4], .45)
    m.tube(frost, pts[3], r * .95, ice, bone, sides=5, r1=r * 1.05)
    m.tube(pts[3], sleeve, r * 1.05, ice, bone, sides=5, r1=r * .6)
    m.tube(sleeve, add(pts[4], mul(sub(pts[4], pts[3]), .35)), r * .6, rime, bone, sides=5, r1=.02)
    for k in range(crystals):
        a = k * math.tau / crystals + .8
        s, t = frame(sub(pts[3], pts[2]))
        d = add(mul(add(mul(s, math.cos(a)), mul(t, math.sin(a))), .8), (0, 0, .7))
        shard(m, lerp(frost, pts[3], .5 + .3 * k / max(1, crystals)), d, h * .22, r * .45, ice, bone, sides=4, tip=rime)


def link(m, c, d, w, length, r, tag, bone=None):
    """One chain link: a rhombus of four bars round c, its long axis along d, its plane along w."""
    d, w = mul(unit(d), length / 2), mul(unit(w), length * .3)
    p = [add(c, d), add(c, w), sub(c, d), sub(c, w)]
    for i in range(4):
        m.tube(p[i], p[(i + 1) % 4], r, tag, bone, sides=3)


def chain(m, pts, size, r, tag, bone=None):
    """A chain along the polyline pts, links of about `size`, alternating their plane."""
    i = 0
    for a, b in zip(pts, pts[1:]):
        count = max(1, round(math.dist(a, b) / (size * .8)))
        side = unit(cross(sub(b, a), (0, 0, 1))) if abs(unit(sub(b, a))[2]) < .95 else (1, 0, 0)
        for k in range(count):
            p, q = lerp(a, b, k / count), lerp(a, b, (k + 1) / count)
            d = sub(q, p)
            w = side if i % 2 else unit(cross(d, side))
            link(m, lerp(p, q, .5), d, w, math.dist(p, q) * 1.25, r, tag, bone)
            i += 1


def disc_ring(m, c, y0, y1, r0, r1, tag, bone, segments=20):
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


def ice_block(m, lo, hi, rng, light, dark, bone=None):
    """A sawn block of river ice, its edges chipped: an octagonal section (the corners cut) in
    three rings, jittered, its faces alternately lit and deep."""
    (x, y, z), (X, Y, Z) = lo, hi
    c = ((x + X) / 2, (y + Y) / 2, (z + Z) / 2)
    hx, hy = (X - x) / 2, (Y - y) / 2
    cut = .22
    sect = [(1, -1 + cut), (1, 1 - cut), (1 - cut, 1), (-1 + cut, 1), (-1, 1 - cut), (-1, -1 + cut), (-1 + cut, -1), (1 - cut, -1)]
    rings = []
    for h, k in ((z, .94), (z + (Z - z) * .55, 1.0), (Z, .9)):
        rings.append([(c[0] + hx * k * u + rng.uniform(-.08, .08), c[1] + hy * k * v + rng.uniform(-.08, .08),
                       h + (rng.uniform(-.12, .12) if h > z else 0)) for u, v in sect])
    n = len(sect)
    for r, (lo_ring, hi_ring) in enumerate(zip(rings, rings[1:])):
        for i in range(n):
            j = (i + 1) % n
            outward(m, (lo_ring[i], lo_ring[j], hi_ring[j], hi_ring[i]), c, light if (i + r) % 2 else dark, bone)
    top = (c[0] + rng.uniform(-.2, .2), c[1] + rng.uniform(-.2, .2), Z + .25)
    for i in range(n):
        j = (i + 1) % n
        outward(m, (rings[-1][i], rings[-1][j], top), c, light, bone)
        outward(m, (rings[0][j], rings[0][i], (c[0], c[1], z)), c, dark, bone)
    return [p for ring in rings for p in ring]
