"""Mesh helpers for the Isengard builder: oriented polygons, prisms, wheels, chains and the White Hand.

Everything is in the model's rest space (sagekit/units/mesh.py). Polygons are convex and listed
around their perimeter; `poly` turns each to face `out` and gives it planar UVs, so any number of
corners works (Mesh.face's default UVs cover four).
"""
import math

from sagekit.units.mesh import uv_for

# EA's HC_MUPortCart.tga tiles every 64 px over the atlas' left half. In each tile x 52..63, y 42..63
# is full alpha and runs on into the next tile's full-alpha top band (y 0..6): a solid
# 12 x 29 px house-colour patch. HOUSE faces map inside it (tile 0, which the orc never samples),
# so the player's colour lands on our cloth and nowhere else.
HOUSE = 16
HOUSE_BOX = (54, 45, 61, 67)        # atlas pixels x0, y0, x1, y1 (2048 x 1024)


def uvs(tag, u, v):
    """uv_for, plus the HOUSE patch in the atlas' left half."""
    if tag == HOUSE:
        x0, y0, x1, y1 = HOUSE_BOX
        return (x0 + .5 + (x1 - x0) * u) / 2048, 1 - (y0 + .5 + (y1 - y0) * (1 - v)) / 1024
    return uv_for(tag, u, v)


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def mul(a, k):
    return tuple(x * k for x in a)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a):
    n = math.sqrt(dot(a, a))
    return tuple(x / n for x in a)


def poly(m, pts, tag, out, bone=None):
    """A convex polygon facing `out`, UVs projected on its own plane."""
    n = cross(sub(pts[1], pts[0]), sub(pts[2], pts[0]))
    if dot(n, out) < 0:
        pts = pts[::-1]
        n = mul(n, -1)
    a = unit(sub(pts[1], pts[0]))
    b = unit(cross(n, a))
    pa, pb = [dot(p, a) for p in pts], [dot(p, b) for p in pts]
    sa, sb = (max(pa) - min(pa)) or 1, (max(pb) - min(pb)) or 1
    m.face(pts, tag, bone, [((x - min(pa)) / sa, (y - min(pb)) / sb) for x, y in zip(pa, pb)])


def solid(m, lo, hi, tag, bone=None, caps=(True, True)):
    """A convex prism or frustum between two matching polygons (each listed around its perimeter)."""
    centre = mul(tuple(map(sum, zip(*(lo + hi)))), 1 / (2 * len(lo)))

    def side(pts):
        fc = mul(tuple(map(sum, zip(*pts))), 1 / len(pts))
        poly(m, pts, tag, sub(fc, centre), bone)
    for i in range(len(lo)):
        j = (i + 1) % len(lo)
        side([lo[i], lo[j], hi[j], hi[i]])
    if caps[0]:
        side(lo)
    if caps[1]:
        side(hi)


def spike(m, base, tip, r, tag, bone=None, sides=4, twist=math.pi / 4):
    """A faceted point: a pyramid of `sides` faces from a base of radius r to the tip."""
    d = unit(sub(tip, base))
    u = unit(cross(d, (0, 0, 1) if abs(d[2]) < .9 else (1, 0, 0)))
    v = cross(d, u)
    ring = [add(base, add(mul(u, r * math.cos(twist + i * math.tau / sides)), mul(v, r * math.sin(twist + i * math.tau / sides))))
            for i in range(sides)]
    for i in range(sides):
        j = (i + 1) % sides
        poly(m, [ring[i], ring[j], tip], tag, sub(add(ring[i], ring[j]), mul(base, 2)), bone)
    poly(m, ring, tag, mul(d, -1), bone)


def plane(origin, out, up=(0, 0, 1)):
    """Map (a, b, depth) on a vertical plane facing `out` to rest space (a to the viewer's right)."""
    right = cross(up, out)

    def at(a, b, d=0):
        return add(origin, add(add(mul(right, a), mul(up, b)), mul(out, d)))
    return at


def flat(m, at, shape, s, depth, tag, out, bone=None):
    poly(m, [at(a * s, b * s, depth) for a, b in shape], tag, out, bone)


FINGERS = [(-.36, .9), (-.12, 1.02), (.12, .98), (.36, .8)]       # (centre, tip height)


def hand_shapes(grow=0):
    """The hand's convex pieces in hand units; `grow` widens each (an outline behind)."""
    g = grow
    shapes = [[(-.5 - g, -.62 - g), (.5 + g, -.62 - g), (.56 + g, .22 + g), (-.5 - g, .22 + g)],
              [(-.5 + g, -.36 - g), (-.46 + g, .02 + g), (-.84, .52 + g * 1.5), (-1.0 - g * 1.5, .4)]]
    for c, top in FINGERS:
        w = .105 + g
        shapes.append([(c - w, .2), (c + w, .2), (c + w, top - .09), (c, top + g), (c - w, top - .09)])
    return shapes


def white_hand(m, at, s, depth, tag, out, bone=None, outline=None):
    """Saruman's open right hand: palm, four fingers together, the thumb out to one side; with
    `outline`, a dark rim behind it so it reads on any player colour."""
    if outline is not None:
        for shape in hand_shapes(.07):
            flat(m, at, shape, s, depth - .04, outline, out, bone)
    for shape in hand_shapes():
        flat(m, at, shape, s, depth, tag, out, bone)


def annulus(m, cx, cz, y, half, r0, r1, tag, bone, n=24):
    """A flat ring (both faces and both bands) round the y axis at (cx, cz)."""
    for i in range(n):
        a, b = i * math.tau / n, (i + 1) * math.tau / n

        def p(r, t, yy):
            return (cx + r * math.cos(t), yy, cz + r * math.sin(t))
        for yy, s in ((y - half, -1), (y + half, 1)):
            poly(m, [p(r0, a, yy), p(r1, a, yy), p(r1, b, yy), p(r0, b, yy)], tag, (0, s, 0), bone)
        for r, s in ((r0, -1), (r1, 1)):
            mid = (math.cos((a + b) / 2) * s, 0, math.sin((a + b) / 2) * s)
            poly(m, [p(r, a, y - half), p(r, a, y + half), p(r, b, y + half), p(r, b, y - half)], tag, mid, bone)


def chain(m, path, tag, bone=None, step=.52):
    """Alternating links along a polyline: a broad link, then a narrow one turned edge-on."""
    pts = [path[0]]
    for a, b in zip(path, path[1:]):
        d = math.dist(a, b)
        k = max(1, round(d / step))
        pts += [add(a, mul(sub(b, a), i / k)) for i in range(1, k + 1)]
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        mid = mul(add(a, b), .5)
        d = mul(sub(b, a), .62)
        m.tube(sub(mid, d), add(mid, d), .19 if i % 2 else .13, tag, bone, sides=4)


def arc(centre, r, a0, a1, n):
    """Points on a circle in the y-z plane (angles from +y towards +z)."""
    y, z = centre
    return [(y + r * math.cos(a0 + (a1 - a0) * i / n), z + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def endgrain(m, centre, axis, r, tag, sides, bone=None):
    """A log's sawn face: a disc whose UVs map the swatch round its centre (the rings)."""
    d = unit(axis)
    u = unit(cross(d, (0, 0, 1)))
    v = cross(d, u)
    pts, uv = [], []
    for i in range(sides):
        t = i * math.tau / sides
        pts.append(add(centre, add(mul(u, r * math.cos(t)), mul(v, r * math.sin(t)))))
        uv.append((.5 + .5 * math.cos(t), .5 + .5 * math.sin(t)))
    n = cross(sub(pts[1], pts[0]), sub(pts[2], pts[0]))
    if dot(n, d) < 0:
        pts, uv = pts[::-1], uv[::-1]
    m.face(pts, tag, bone, uv)
