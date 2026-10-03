"""Shared shapes for the Archers' parts, in the Elven Archer's creation-screen rest space (+X
front, +Y the archer's left, +Z up; place.py). Anatomy measured from CHAR_EL_C_SKN: the head's
centre HC (face at x 1.9, back of the skull -1.55, crown z 23.6, half-width 1.25), the neck at z
20.2, the shoulders at z 19.5 (half-width 3.4), the braid down the back to x -3.2, the left forearm
along FOREARM and EA's bow bone BOW_REST (the bow along its local z, the string on -x)."""
import math

from ..kit.geom import add, cross, mul, norm, sub
from .place import region

HC = (0.18, 0.0, 21.85)
HEAD = ((0.18, 0.0, 0.0), [1, 0, 0], [0, 1, 0], [0, 0, 1])
H, SPINE, LOW = "B_HEAD", "BAT_SPINE2", "BAT_SPINE1"
BOW = "BOWBONE"
BOW_REST = [-0.0, 0.0, 1.0, 0.037, 0.501, 0.865, -0.0, 9.719, -0.865, 0.501, -0.0, 11.195]
ELBOW, FOREARM = (-0.51, 6.10, 15.35), norm((0.12, 0.69, -0.71))


def bowpt(x, y, z):
    """A point in the bow bone's local frame (bow along z, grip at 0, string toward -x)."""
    r = BOW_REST
    return [r[0] * x + r[1] * y + r[2] * z + r[3], r[4] * x + r[5] * y + r[6] * z + r[7], r[8] * x + r[9] * y + r[10] * z + r[11]]


def bowdir(x, y, z):
    r = BOW_REST
    return norm([r[0] * x + r[1] * y + r[2] * z, r[4] * x + r[5] * y + r[6] * z, r[8] * x + r[9] * y + r[10] * z])


def edge(m, pts, r, tag, bone=H, sides=6, squash=1.0):
    m.sweep(pts, [r] * len(pts), tag, bone, sides=sides, squash=squash)


def ball(m, c, r, tag, bone=H, sides=10):
    prof = [(r * math.sin(a), r * math.sin(a), r * -math.cos(a)) for a in [math.pi * k / 6 for k in range(1, 6)]]
    m.shell((list(c), [1, 0, 0], [0, 1, 0], [0, 0, 1]), [(.001, .001, -r)] + prof + [(.001, .001, r)], tag, bone,
            sides=sides, keep=sides)


def ellipse(c, rx, ry, z, n=24, a0=0.0, a1=2 * math.pi, lift=lambda t: 0.0, closed=True):
    pts = [(c + rx * math.cos(a0 + (a1 - a0) * i / n), ry * math.sin(a0 + (a1 - a0) * i / n),
            z + lift(a0 + (a1 - a0) * i / n)) for i in range(n + (0 if closed else 1))]
    return pts + [pts[0]] if closed else pts


def brow(t):
    """A circlet or helm rim: higher over the brow than at the nape."""
    return .28 * math.cos(t)


def opening_rings(m, rings, tag, bone, n=20, lining=None, inset=.06):
    """A hood: rings (cx, z, rx, ry, a) bottom to top, each running round the back from angle a to
    2pi - a (a = half the face opening; 0 closes it), lined inside (its own vertices, so both sides
    shade true). Returns the outer rows."""
    n = m._sides(n, 12)
    out = []
    for flip, d, t_ in ((False, 0.0, tag), (True, inset, tag if lining is None else lining)):
        rows, uvs = [], []
        for k, (cx, z, rx, ry, a) in enumerate(rings):
            th = [a + (2 * math.pi - 2 * a) * i / n for i in range(n + 1)]
            th = th[::-1] if flip else th
            rows.append([(cx + max(.01, rx - d) * math.cos(t), max(.01, ry - d) * math.sin(t), z) for t in th])
            uvs.append([(i / n, k / (len(rings) - 1)) for i in range(n + 1)])
        m.grid(rows, uvs, t_, bone, fallback=lambda k, i: [0, 0, 1])
        out.append(rows)
    return out[0]


def leaf_outline(c, along, across, length, width, n=10, tip=1.0):
    """A convex leaf: pointed at both ends, widest a little below the middle."""
    pts = []
    for i in range(n):
        s = i / (n - 1)
        w = width * .5 * math.sin(math.pi * s) ** .85 * (1 + .12 * (.5 - s))
        pts.append(add(add(c, mul(along, (s - .5) * length)), mul(across, w)))
    for i in range(n - 2, 0, -1):
        s = i / (n - 1)
        w = width * .5 * math.sin(math.pi * s) ** .85 * (1 + .12 * (.5 - s))
        pts.append(add(add(c, mul(along, (s - .5) * length)), mul(across, -w)))
    return pts


def leaf(m, c, along, across, length, width, thick, tag, bone, rib=None, out=None):
    """A leaf plate (gold clasp, Mirkwood leather) with an optional raised midrib on its `out`
    side (default: away from the head's centre)."""
    nrm = norm(cross(along, across))
    ref = out or sub(c, HC)
    if sum(a * b for a, b in zip(nrm, ref)) < 0:
        nrm = mul(nrm, -1)
    m.slab(leaf_outline(c, along, across, length, width), thick, nrm, tag, bone, bevel=min(.04, thick * .3))
    if rib is not None:
        edge(m, [add(add(c, mul(along, (s - .5) * length * .9)), mul(nrm, thick * .5)) for s in (0, .5, 1)],
             thick * .35, rib, bone, sides=4)


def leaf_shield(m, face_tag, rim_tag, back_tag, rib_tag, boss_tag):
    """A leaf-shaped shield on the outer left forearm: a domed pointed oval (its tip toward the
    hand), a rolled rim, a midrib and a boss, a birch back."""
    region(m, "arm")
    bone = "BAT_FARML"
    mid = add(ELBOW, mul(FOREARM, 1.9))
    out = norm(sub((0, 1, 0), mul(FOREARM, FOREARM[1])))
    across = norm(cross(out, FOREARM))
    c = add(mid, mul(out, .95))
    L, W, n, K = 5.4, 2.6, 9, 5
    rows, uvs = [], []
    for j in range(K):
        f = 1 - j / (K - 1)                       # rings of the dome, rim inward
        row, urow = [], []
        for i in range(2 * n + 1):
            a = 2 * math.pi * i / (2 * n)
            s = .5 - .5 * math.cos(a)
            w = .5 * W * math.sin(math.pi * s) ** .85 * (1 if a <= math.pi else -1)
            along_ = (s - .5) * L * f
            dome = .55 * (1 - f ** 2)
            p = add(add(add(c, mul(FOREARM, along_)), mul(across, w * f)), mul(out, dome))
            row.append(p)
            urow.append((.5 + w * f / W, .5 - along_ / L))
        rows.append(row)
        uvs.append(urow)
    if m.lod < .7:
        rows, uvs = rows[::2], uvs[::2]
    m.grid(rows, uvs, face_tag, bone, wrap=True)
    m.flat(rows[0][:-1][::-1], back_tag, bone)
    edge(m, rows[0], .12, rim_tag, bone, sides=6)
    edge(m, [add(add(c, mul(FOREARM, (s - .5) * L * .85)), mul(out, .58 * (1 - (2 * s - 1) ** 2) + .03))
             for s in [k / 8 for k in range(9)]], .07, rib_tag, bone, sides=5)
    m.stud(add(c, mul(out, .58)), out, .38, boss_tag, bone, h=.25, sides=10)
    return c, out, across


def cloak(m, tag, hem, collar_tag, rim=None, folds=8, hem_z=9.6, lining=None):
    """A long cloak from the shoulders to mid-thigh, riding the upper spine (EA's rigs have no cape
    on the creation screen; the game rig's cape bones are not used), clear of the braid, falling
    in `folds` folds, edged along the hem and sides, a rolled collar round the back of the neck."""
    region(m, "back")
    back = ((-0.3, 0.0, 0.0), [1, 0, 0], [0, 1, 0], [0, 0, 1])
    arc = (math.pi * .56, math.pi * 1.44)
    prof = [(3.55, 3.75, hem_z), (3.3, 3.45, 11.2), (3.12, 3.15, 13.0), (3.2, 3.05, 15.0), (3.45, 3.2, 17.0),
            (3.4, 3.4, 18.5), (2.85, 3.5, 19.45), (2.05, 2.5, 20.1)]
    K = len(prof)
    bump = lambda t, k: .26 * (1 - k / (K - 1)) ** 1.1 * math.sin(folds * 2 * math.pi * (t - arc[0]) / (arc[1] - arc[0]))
    rows = m.shell(back, prof, tag, SPINE, sides=48, arc=arc, bump=bump, rim=rim, keep=26)
    inner = [(rx - .07, ry - .07, z) for rx, ry, z in prof]        # the lining: its own vertices, wound inward
    m.shell(back, inner, tag if lining is None else lining, SPINE, sides=48, arc=arc[::-1], bump=bump, rim=rim, keep=26)
    edge(m, [add(p, (-.02, 0, -.02)) for p in rows[0]], .09, hem, SPINE)
    for col in (0, -1):
        edge(m, [r[col] for r in rows], .08, hem, SPINE)
    collar = [(-0.3 + 2.1 * math.cos(a), 2.55 * math.sin(a), 20.15 + .12 * math.cos(a))
              for a in [math.pi * (.56 + .88 * i / 14) for i in range(15)]]
    m.sweep(collar, [.2 + .06 * math.sin(math.pi * i / 14) for i in range(15)], collar_tag, SPINE, sides=8)
    return rows
