"""Shared shapes for the Evil parts, drawn on a model's measured anatomy (anatomy.py).

Helmets are drawn on the unit skull guide (x front, y left, z up; radius 1 = the skull), placed by
the head frame (anisotropic: an orc's long skull, a troll's low brow); thicknesses scale with the
skull. Shoulder pieces sit over the upper-arm joint, capes follow the measured back, skirts the hips.
"""
import math

from ..kit.geom import add, cross, mul, norm, sub
from .anatomy import of

T = 2 * math.pi


def head_frame(A):
    c, (rx, ry, rz) = A.head["c"], A.head["r"]
    return (list(c), [rx, 0.0, A.head["tilt"] * rz], [0.0, ry, 0.0], [0.0, 0.0, rz])


def brow(t, lift=.3):
    """A helmet's rim rises over the eyes and drops over the nape (unit z)."""
    return lift * math.cos(t) - .05


def ring(A, r, z, n=24, a0=0.0, a1=T, rim=brow, closed=True, ry=None):
    ry = r if ry is None else ry
    pts = [A.hp(r * math.cos(a0 + (a1 - a0) * i / n), ry * math.sin(a0 + (a1 - a0) * i / n),
                z + (rim(a0 + (a1 - a0) * i / n) if rim else 0)) for i in range(n + (0 if closed else 1))]
    return pts + [pts[0]] if closed else pts


def edge(m, pts, r, tag, bone, sides=6, squash=1.0):
    m.sweep([list(p) for p in pts], [r] * len(pts), tag, bone, sides=sides, squash=squash)


def dome(m, A, prof, tag, sides=24, rim=brow, bump=None, arc=(0, T), double=False):
    """A helmet shell: prof [(r, z)] or [(rx, ry, z)] in skull units, bottom to top."""
    p3 = [(q[0], q[0], q[1]) if len(q) == 2 else q for q in prof]
    return m.shell(head_frame(A), p3, tag, A.head_bone, sides=sides, rim=rim, bump=bump, arc=arc, double=double)


def patch(m, A, r, z0, z1, half, tag, centre=0.0, n=8, rows=4, lift=0.0):
    """A curved emblem patch on the skull guide (u across, v up: an upright picture), `half` radians
    either side of `centre`, between skull heights z0 and z1."""
    o, X, Y, Z = head_frame(A)
    pts, uvs = [], []
    for k in range(rows):
        z = z0 + (z1 - z0) * k / (rows - 1)
        rr = r * math.sqrt(max(.2, 1 - max(0, z) ** 2 * .35)) + lift
        row, urow = [], []
        for i in range(n + 1):
            t = centre - half + 2 * half * i / n          # u toward the hero's left: the viewer's right
            row.append(add(add(add(o, mul(X, rr * math.cos(t))), mul(Y, rr * math.sin(t))), mul(Z, z)))
            urow.append((i / n, k / (rows - 1)))
        pts.append(row)
        uvs.append(urow)
    m.grid(pts, uvs, tag, A.head_bone)


def emblem(m, corners, tag, bone):
    """A flat picture on four corners (top-left, top-right, bottom-right, bottom-left, seen from the
    front): its tile upright, facing the viewer."""
    tl, tr, br, bl = corners
    m.flat([list(p) for p in (tl, bl, br, tr)], tag, bone, [(0, 1), (0, 0), (1, 0), (1, 1)])


def band(m, A, r, z0, z1, tag, sides=24, rim=brow):
    """A vertical band (a crown's foot) whose rings follow the brow line."""
    rim = rim or (lambda t: 0.0)
    o, X, Y, Z = head_frame(A)
    n = m._sides(sides)
    th = [T * i / n for i in range(n + 1)]
    rows = [[add(add(add(o, mul(X, rr * math.cos(t))), mul(Y, rr * math.sin(t))), mul(Z, z + rim(t))) for t in th]
            for rr, z in ((r - .03, z0), (r, z0 + .04), (r, z1 - .04), (r - .03, z1))]
    uvs = [[(i / n, k / 3) for i in range(n + 1)] for k in range(4)]
    if m.lod < .8:
        rows, uvs = [rows[0], rows[3]], [uvs[0], uvs[3]]
    m.grid(rows, uvs, tag, A.head_bone, wrap=True)


def spike(m, A, base, out, length, r0, tag, hook=0.0, tip_tag=None, sides=6, up=(0, 0, 1)):
    """A (hooked) spike from a skull-unit point along `out` (unit dir), `length` and base radius
    `r0` in skull units; hook bends its last half toward `up`; tip_tag draws the last third."""
    s = A.head["s"]
    o = norm(out)
    pts = []
    for i in range(6):
        f = i / 5
        h = hook * f * f
        p = [base[k] + o[k] * length * f + up[k] * h for k in range(3)]
        pts.append(A.hp(*p))
    radii = [r0 * s * (1 - f) ** .8 + .01 * s for f in [i / 5 for i in range(6)]]
    sides = sides if m.lod >= .7 else 4
    if m.lod < .5:                        # trimmed: one sweep, the steel tip folded into the iron
        tip_tag = None
    if tip_tag is None:
        m.sweep([list(p) for p in pts], radii, tag, A.head_bone, sides=sides)
    else:
        m.sweep([list(p) for p in pts[:4]], radii[:4], tag, A.head_bone, sides=sides, cap=True)
        m.sweep([list(p) for p in pts[3:]], radii[3:], tip_tag, A.head_bone, sides=sides)


def tine(m, A, base, out, length, r0, tag, curl=0.0, sides=5):
    """A tall curved tine (Angmar): out from the band, curving back over the skull by `curl`."""
    s = A.head["s"]
    o = norm(out)
    pts, radii = [], []
    for i in range(7):
        f = i / 6
        p = [base[k] + o[k] * length * f for k in range(3)]
        p[0] -= curl * f * f
        pts.append(list(A.hp(*p)))
        radii.append(r0 * s * (1 - f) ** .9 + .008 * s)
    m.sweep(pts, radii, tag, A.head_bone, sides=sides if m.lod >= .7 else 3)


# ------------------------------------------------------------------ shoulders
def shoulder_frame(A, s, lift=0.0, out=0.0):
    """(origin, X, Y, Z) over the upper-arm joint of side s (+1 left): Z out and up."""
    sh = A.shoulder[s]
    j = sh["joint"]
    r = sh["r"]
    Z = norm((0.0, s * .55, .83))
    X = [1.0, 0.0, 0.0]
    Y = cross(Z, X)
    o = add(add(j, mul(Z, r * (.25 + lift))), [0.0, s * r * out, 0.0])
    return o, X, Y, Z, r


def pauldron(m, A, s, tag, edge_tag, prof, sides=20, bump=None, lift=0.0, out=0.0):
    """A domed shoulder plate on side s from prof [(rx, ry, z)] in shoulder radii."""
    o, X, Y, Z, r = shoulder_frame(A, s, lift, out)
    bone = A.uarm[s]
    rows = m.shell((o, X, Y, Z), [(a * r, b * r, c * r) for a, b, c in prof], tag, bone, sides=sides, bump=bump)
    if edge_tag is not None:
        edge(m, rows[0], .06 * r, edge_tag, bone)
    return o, X, Y, Z, r, rows


def lame(m, A, s, k, tag, edge_tag, r_scale=1.0, sides=12):
    """The k-th riveted lame below a pauldron: an open arc round the upper arm's outside."""
    j = A.shoulder[s]["joint"]
    hand = A.at(A.farm[s])
    d = norm(sub(hand, j))
    r = A.shoulder[s]["r"] * .95 * r_scale
    o = add(j, mul(d, r * (.55 + .45 * k)))
    X = norm(cross([0, 0, 1], d)) if abs(d[2]) < .95 else [1.0, 0.0, 0.0]
    X = X if X[0] > 0 else mul(X, -1)
    Y = cross(d, X)
    c = math.pi * .5 if s * Y[1] > 0 else -math.pi * .5
    arc = (c - 1.6, c + 1.6)
    rows = m.shell((o, X, Y, mul(d, -1)), [(r * (1.0 - .06 * k), r * (1.0 - .06 * k), 0), (r * (.94 - .06 * k), r * (.94 - .06 * k), .42 * r)],
                   tag, A.uarm[s], sides=sides, arc=arc, double=True)
    if edge_tag is not None:
        edge(m, rows[0], .04 * A.shoulder[s]["r"], edge_tag, A.uarm[s], sides=4)


# ------------------------------------------------------------------ capes and skirts
def back_rows(A, top_drop=0.0, hem=.42, gap=.06, arc=1.05, n=8, flare=.5):
    """Rows of a cape round the measured back from the shoulders (top) down to `hem` of the height
    above the ground; each row an arc of +-arc around the back. Returns [rows of (x, y, z)], bottom first."""
    H = A.height
    bands = sorted(A.bands, key=lambda b: b["z"])
    ztop = bands[-1]["z"] - .005 * H - top_drop * H
    zbot = hem * H
    rows = []
    for k in range(n):
        f = k / (n - 1)                       # 0 at the hem, 1 at the top
        z = zbot + (ztop - zbot) * f
        b = min(bands, key=lambda q: abs(q["z"] - z)) if z >= bands[0]["z"] else bands[0]
        g = gap * H * (1 + flare * (1 - f) * 2)
        cx = (b["back"] + b["front"]) / 2
        rx = (b["front"] - b["back"]) / 2 + g
        ry = b["w"] * (1 + .25 * (1 - f) * flare) + g
        rows.append((cx, rx, ry, z))
    return rows


def cloak(m, A, tag, hem_tag, collar_tag, folds=7, sides=40, hem=.42, arc=1.05, tatter=0.0, collar=True):
    """A cloak hanging from the shoulders round the back (on the upper spine, as EA's rigs have no
    cape bones), in `folds` folds; tatter cuts a ragged hem."""
    prof = back_rows(A, hem=hem)
    K = len(prof)
    a0, a1 = math.pi - arc, math.pi + arc
    n = m._sides(sides, keep=24)
    rows, uvs = [], []
    for k, (cx, rx, ry, z) in enumerate(prof):
        row, urow = [], []
        for i in range(n + 1):
            t = a0 + (a1 - a0) * i / n
            fold = .035 * A.height * (1 - k / (K - 1)) ** 1.2 * math.sin(folds * T * (t - a0) / (a1 - a0))
            zz = z - (tatter * A.height * (.5 + .5 * math.sin(i * 2.7)) * (k == 0))
            row.append([cx + (rx + fold) * math.cos(t), (ry + fold) * math.sin(t), zz])
            urow.append((i / n, k / (K - 1)))
        rows.append(row)
        uvs.append(urow)
    m.grid(rows, uvs, tag, A.spine, double=True)
    if hem_tag is not None:
        edge(m, rows[0], .006 * A.height, hem_tag, A.spine)
        for col in (0, -1):
            edge(m, [r[col] for r in rows], .005 * A.height, hem_tag, A.spine)
    if collar:
        top = rows[-1]
        edge(m, [add(p, (0, 0, .004 * A.height)) for p in top[::2]], .018 * A.height, collar_tag, A.spine, sides=8)
    return rows


def skirt(m, A, tag, rings, sides=36, ruffle=0.0, double=True):
    """A skirt round the hips: rings [(scale of the hip radii, dz in heights)], top first."""
    h = A.hips
    n = m._sides(sides, keep=24)
    rows, uvs = [], []
    for k, (sc, dz) in enumerate(rings):
        row = []
        for i in range(n + 1):
            t = T * i / n
            b = 1 + ruffle * math.sin(t * 14) * (k / max(1, len(rings) - 1))
            row.append([h["c"][0] + h["rx"] * sc * b * math.cos(t), h["ry"] * sc * b * math.sin(t), h["c"][2] + dz * A.height])
        rows.append(row)
        uvs.append([(i / n, k / max(1, len(rings) - 1)) for i in range(n + 1)])
    m.grid(rows[::-1], uvs[::-1], tag, A.pelvis, wrap=True, double=double)
    return rows


def leaf(m, pts, tag, bone):
    """A thin two-sided plate (a petal, a leaf) on its outline: one face, both windings."""
    t0 = len(m.tris)
    m.flat([list(p) for p in pts], tag, bone)
    m.tris += [((a, c, b), sf) for (a, b, c), sf in m.tris[t0:]]


def ball(m, c, r, tag, bone, sides=10):
    prof = [(r * math.sin(a), r * math.sin(a), r * -math.cos(a)) for a in [math.pi * k / 6 for k in range(1, 6)]]
    m.shell((list(c), [1, 0, 0], [0, 1, 0], [0, 0, 1]), [(.001, .001, -r)] + prof + [(.001, .001, r)], tag, bone,
            sides=sides, keep=sides)


__all__ = ["of", "head_frame", "brow", "ring", "edge", "dome", "band", "patch", "emblem", "spike", "tine", "shoulder_frame", "pauldron",
           "lame", "back_rows", "cloak", "skirt", "ball", "leaf", "T"]
