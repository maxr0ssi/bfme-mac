"""The Goblin builder's shapes: crooked beams, lathed bundles, skulls, tattered rags and the house region.

Every helper adds faces to a sagekit.units Mesh in the model's rest space (x towards the orc, y
across, z up), on one of EA's bones. design.py composes them.
"""
import math

from sagekit.units.mesh import uv_for

# The atlas' left half repeats EA's 64 px cart mask HC_MUPortCart.tga (sagekit/units/paint.py): in
# every 64 px tile, x 51..63 and y 35..63 (running on into the next tile's full-alpha top band) is
# solid house colour. HOUSE faces map into the inner, alpha-1 part of one tile mid-atlas, so the
# player's colour lands on our rags, and only there; the rest of the atlas takes none.
HOUSE = 16
HOUSE_BOX = (448 + 53, 448 + 38, 448 + 57, 448 + 66)     # atlas pixels x0, y0, x1, y1 (2048 x 1024)


def uvs(tag, u, v):
    """uv_for, plus the HOUSE region in the atlas' left half."""
    if tag == HOUSE:
        x0, y0, x1, y1 = HOUSE_BOX
        return (x0 + (x1 - x0) * u) / 2048, 1 - (y0 + (y1 - y0) * (1 - v)) / 1024
    return uv_for(tag, u, v)


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def mul(a, k):
    return tuple(x * k for x in a)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a):
    n = math.sqrt(sum(x * x for x in a))
    return tuple(x / n for x in a)


def frame(d, up=(0, 0, 1)):
    """(along, across, up) right-handed unit axes for direction d."""
    d = unit(d)
    s = cross(up, d)
    if sum(x * x for x in s) < 1e-6:
        s = cross((1, 0, 0), d)
    s = unit(s)
    return d, s, cross(d, s)


def beam(m, a, b, w, h, tag, bone=None, up=(0, 0, 1)):
    """A square-cut timber (or plate) from a to b, w across and h high: crooked work at any angle.
    UVs run along its length, so the painted grain follows the plank."""
    d, s, t = frame(sub(b, a), up)
    length = math.sqrt(sum(x * x for x in sub(b, a)))
    c = mul(add(a, b), .5)
    axes = [mul(d, length / 2), mul(s, w / 2), mul(t, h / 2)]
    for i in range(3):
        j, k = (i + 1) % 3, (i + 2) % 3
        for sign in (1, -1):
            centre = add(c, mul(axes[i], sign))
            corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
            pts = [add(centre, add(mul(axes[j], cj), mul(axes[k], ck))) for cj, ck in corners]
            if j == 0:
                uv = [((cj + 1) / 2, (ck + 1) / 2) for cj, ck in corners]
            elif k == 0:
                uv = [((ck + 1) / 2, (cj + 1) / 2) for cj, ck in corners]
            else:
                uv = [(.3 + .4 * (cj + 1) / 2, .3 + .4 * (ck + 1) / 2) for cj, ck in corners]
            if sign < 0:
                pts, uv = pts[::-1], uv[::-1]
            m.face(pts, tag, bone, uv)


def lathe(m, a, b, profile, tag, bone=None, sides=8):
    """A turned bundle from a to b: profile [(t, radius)], t 0..1 along it."""
    pts = [(add(a, mul(sub(b, a), t)), r) for t, r in profile]
    for (p, r), (q, r1) in zip(pts, pts[1:]):
        m.tube(p, q, max(r, .04), tag, bone, sides=sides, r1=max(r1, .04))


def horn(m, root, tip, bend, r, tag, bone=None, steps=4):
    """A tapering horn or tusk curving through root + bend at its middle."""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        base = add(root, mul(sub(tip, root), t))
        pts.append(add(base, mul(bend, 4 * t * (1 - t))))
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        m.tube(p, q, r * (1 - i / steps) + .03, tag, bone, sides=6, r1=r * (1 - (i + 1) / steps) + .03)


def skull(m, c, size, face, tag, socket, bone=None, horns=None):
    """A skull at c (the base of the cranium), looking along face (horizontal): cranium, muzzle,
    dark eye sockets and nose; horns=(tag, length) adds curling horns."""
    f = unit((face[0], face[1], 0))
    s = (-f[1], f[0], 0)
    z = (0, 0, 1)
    lathe(m, c, add(c, mul(z, 1.6 * size)),
          [(0, .55 * size), (.22, .92 * size), (.48, 1.0 * size), (.72, .86 * size), (.9, .5 * size), (1, .12 * size)],
          tag, bone, sides=8)
    snout = add(c, mul(z, .25 * size))
    beam(m, add(snout, mul(f, .2 * size)), add(snout, mul(f, 1.12 * size)), 1.0 * size, .75 * size, tag, bone)
    beam(m, add(c, add(mul(f, .25 * size), mul(z, -.25 * size))), add(c, add(mul(f, 1.0 * size), mul(z, -.2 * size))),
         .8 * size, .3 * size, tag, bone)
    for side in (-1, 1):
        eye = add(c, add(mul(f, .74 * size), add(mul(s, side * .4 * size), mul(z, .72 * size))))
        beam(m, eye, add(eye, mul(f, .36 * size)), .36 * size, .3 * size, socket, bone)
    nose = add(snout, add(mul(f, 1.05 * size), mul(z, .15 * size)))
    beam(m, sub(nose, mul(f, .1 * size)), add(nose, mul(f, .1 * size)), .26 * size, .3 * size, socket, bone)
    if horns:
        htag, length = horns
        for side in (-1, 1):
            root = add(c, add(mul(s, side * .8 * size), mul(z, 1.05 * size)))
            tip = add(root, add(mul(s, side * .9 * length), add(mul(z, .55 * length), mul(f, .25 * length))))
            horn(m, root, tip, add(mul(s, side * .25 * length), mul(z, -.25 * length)), .34 * size, htag, bone)


def bone_shaft(m, a, b, r, tag, bone=None):
    """A long bone: the shaft and a knuckle at each end."""
    m.tube(a, b, r, tag, bone, sides=6)
    d = unit(sub(b, a))
    for p in (a, b):
        m.tube(sub(p, mul(d, r * 1.3)), add(p, mul(d, r * .9)), r * 1.75, tag, bone, sides=6)


def rag(m, top, across, length, tag, bone=None, sway=(0, 0, 0), strips=3, cut=(1, .7, .85), wave=.25):
    """A tattered hanging cloth, double-sided: `strips` tails from the edge top..top+across, each
    `length` x cut[i] long, curling by sway at the bottom."""
    out = unit(cross(across, (0, 0, 1)))
    for i in range(strips):
        a, b = add(top, mul(across, i / strips)), add(top, mul(across, (i + .97) / strips))
        rows = 4
        drop = length * cut[i % len(cut)]
        ring = []
        for r in range(rows + 1):
            t = r / rows
            off = add(mul(sway, t * t), mul(out, wave * math.sin(t * 3.0 + i * 1.7)))
            narrow = mul(sub(b, a), .08 * t * (1 if i % 2 else -1))
            ring.append((add(add(a, narrow), add(off, (0, 0, -drop * t))),
                         add(sub(b, narrow), add(off, (0, 0, -drop * t)))))
        for r in range(rows):
            (p, q), (p1, q1) = ring[r], ring[r + 1]
            v0, v1 = 1 - r / rows, 1 - (r + 1) / rows
            m.face([p1, q1, q, p], tag, bone, [(0, v1), (1, v1), (1, v0), (0, v0)])
            m.face([p, q, q1, p1], tag, bone, [(0, v0), (1, v0), (1, v1), (0, v1)])


def disc(m, centre, radius, half, tag, bone=None, n=18, jitter=None):
    """A solid wheel of planks about the y axis: two faces and its tread; jitter [r per corner]."""
    cx, cy, cz = centre
    ring = [(radius + (jitter[i] if jitter else 0), i * math.tau / n) for i in range(n)]
    pts = [[(cx + r * math.cos(a), cy + y, cz + r * math.sin(a)) for r, a in ring] for y in (-half, half)]
    uv = [(.5 + .5 * math.cos(a) * r / radius, .5 + .5 * math.sin(a) * r / radius) for r, a in ring]
    m.face(pts[0], tag, bone, uv)
    m.face(pts[1][::-1], tag, bone, uv[::-1])
    for i in range(n):
        k = (i + 1) % n
        m.face([pts[0][i], pts[1][i], pts[1][k], pts[0][k]], tag, bone, [(.1, 0), (.1, 1), (.3, 1), (.3, 0)])


def ring(m, centre, r0, r1, half, tag, bone=None, n=20):
    """A rim about the y axis between radii r0 and r1: its two faces, tread and inner face."""
    cx, cy, cz = centre
    for i in range(n):
        a, b = i * math.tau / n, (i + 1) * math.tau / n

        def p(r, ang, y):
            return (cx + r * math.cos(ang), cy + y, cz + r * math.sin(ang))
        m.face([p(r0, a, -half), p(r1, a, -half), p(r1, b, -half), p(r0, b, -half)], tag, bone)
        m.face([p(r0, a, half), p(r1, a, half), p(r1, b, half), p(r0, b, half)][::-1], tag, bone)
        m.face([p(r1, a, -half), p(r1, a, half), p(r1, b, half), p(r1, b, -half)], tag, bone)
        m.face([p(r0, a, -half), p(r0, a, half), p(r0, b, half), p(r0, b, -half)][::-1], tag, bone)


def drape(m, lo, hi, lumps, tag, bone=None, n=7):
    """A cloth thrown over lumps [((x, y), radius, height)]: a sagging grid from lo (x, y, floor) to
    hi (x, y), its edges on the floor, double-sided where it lifts."""
    x0, y0, z0 = lo
    x1, y1 = hi

    def z(i, j):
        x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * j / n
        h = max([hh * max(0, 1 - ((x - cx) ** 2 + (y - cy) ** 2) / (r * r * 1.6)) ** .6 for (cx, cy), r, hh in lumps])
        edge = min(i, j, n - i, n - j)
        return x, y, z0 + .05 + (h if edge else 0) + (.15 * math.sin(i * 2.1 + j * 1.3) if edge else 0)
    for i in range(n):
        for j in range(n):
            p = [z(i, j), z(i + 1, j), z(i + 1, j + 1), z(i, j + 1)]
            uv = [(i / n, j / n), ((i + 1) / n, j / n), ((i + 1) / n, (j + 1) / n), (i / n, (j + 1) / n)]
            m.face(p[:3], tag, bone, uv[:3])
            m.face([p[0], p[2], p[3]], tag, bone, [uv[0], uv[2], uv[3]])
