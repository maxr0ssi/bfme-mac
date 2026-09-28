"""The Gondor trebuchet tower's drum (Blender side), shared by its two build variations: EA's
GBFTRTOWA (men/trebuchet) and GBFTRTOWB (men/trebuchet_b) carry the same drum, B's shifted DX_B
along x and joined on its -X side to a platform block. Every function takes `dx`, the shift from
A's mesh frame, in which the numbers below are measured.

EA's drum (GBFTRTOWA mesh coordinates): a twelve-sided body from the ground to 44 (BODY, going
round from -X; a narrow prow at +X, x 38.46, carrying EA's carved pilaster), EA's corbel arcade
painted from 38 to 43; a cornice battering out to 22 at z 50 on the +X half; the open platform at
z 50 (P1, the trebuchet's bone, stands on it: nothing new rises inside the parapet) and, on the +X
half, a parapet 1 thick from 50 to 56, battered (its outer face 22 out at 50, 21 at 56: PARAPET is
its outer line at 56). EA's footprint: x -12.75..38.46, |y| <= 22.

What stands on it:
    plinth     a moulded base course round the outward faces
    pilasters  up the body's corners from the plinth to the arcade, weathered tops
    slits      arrow slits in stone surrounds with round heads and sills, on the long faces
    shields    White Tree shields on the two faces beside the prow
    parapet    a black band with the citadel's silver stars on the parapet's face, square
               merlons with capstones on its top, pinnacles at its ends and over the prow
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import prism_uz, sweep

DX_B = 0.25                                 # GBFTRTOWB's drum against GBFTRTOWA's
BODY = [(-12.75, 0.0), (-10.67, -13.68), (0.84, -21.04), (11.84, -21.01), (23.3, -21.0), (34.72, -13.0),
        (36.99, -1.72), (38.46, 0.0)]       # the -Y half; the +Y half mirrors it
CENTRE = (12.0, 0.0)
PARAPET = [(11.84, -21.0), (23.3, -21.0), (34.72, -13.0), (36.99, 0.0)]       # outer line at z 56 (-Y half)
Z_TOP = 56.0
BAND = (52.8, 55.4)                         # the parapet's black band (StarBand)
MERLONS = dict(w=2.2, gap=1.7, h=2.6, cap=0.5)


def mirror(pts):
    return [(x, -y) for x, y in reversed(pts)]


def shift(pts, dx):
    return [(x + dx, y) for x, y in pts]


def segments(path, center):
    """[(a3, t, n, L)] along a polyline, n pointing away from `center`."""
    out = []
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        a, b = V((x0, y0, 0)), V((x1, y1, 0))
        t = (b - a).normalized()
        n = V((t.y, -t.x, 0))
        if n.dot((a + b) / 2 - V((center[0], center[1], 0))) < 0:
            n = -n
        out.append((a, t, n, (b - a).length))
    return out


# ------------------------------------------------------------------ the body
def plinth(path, center):
    prof = [(-0.4, 0.0), (0.9, 0.0), (0.9, 2.0), (0.55, 2.5), (0.55, 3.2), (0.15, 3.6), (-0.4, 3.6)]
    return sweep(path, prof, [None, "stoneB", "top", "course", "top", "top", None], center=center)[0]


def pilaster(x, y, ang, z0=3.2, z1=36.6, w=0.75, d=0.55):
    """A flat pilaster up a corner (ang: its outward direction), a weathered top."""
    n = V((math.cos(ang), math.sin(ang), 0))
    t = V((-n.y, n.x, 0))
    a = V((x, y, 0))
    return [prism_uz(a, t, n, [(-w, z0), (w, z0), (w, z1), (-w, z1)], -0.6, d, [None, "stoneB", None, "stoneB"], "stoneA", None),
            prism_uz(a, t, n, [(-w - 0.15, z1), (w + 0.15, z1), (w + 0.15, z1 + 0.6), (-w - 0.15, z1 + 0.6)], -0.6, d + 0.1,
                     ["stoneB", "stoneB", "top", "stoneB"], "course", None),
            prism_uz(a, t, n, [(-w, z1 + 0.6), (w, z1 + 0.6), (0, z1 + 1.6)], -0.6, d, ["stoneB", "top", "top"], "top", None)]


def slit(kit, a, t, n, u, z0=17.0, z1=27.0, w=0.7):
    """An arrow slit: EA's painted slit window in a stone surround 0.6 wide, a round head of five
    voussoirs with a keystone, a moulded sill."""
    a = a + t * u
    rise = w
    spring = z1 - rise
    arch = [(w * math.cos(math.pi * j / 6), spring + rise * math.sin(math.pi * j / 6)) for j in range(7)]
    out = [prism_uz(a, t, n, [(-w, z0), (w, z0)] + arch, -0.3, 0.2, [None] * 9, "enamel", None)]   # a dark slit
    for e in (-1, 1):
        out.append(prism_uz(a, t, n, [(e * w, z0), (e * (w + 0.6), z0), (e * (w + 0.6), spring), (e * w, spring)], -0.3, 0.7,
                            ["stoneB"] * 4, "stoneA", None))
    out += kit.voussoirs(a, t, n, (w, rise, spring), (w + 0.6, rise + 0.6, spring), -0.3, 0.7, count=5, gap=0.05,
                         key=(0.35, z1 + 1.0, 0.25))
    out.append(prism_uz(a, t, n, [(-w - 0.9, z0 - 0.6), (w + 0.9, z0 - 0.6), (w + 0.9, z0), (-w - 0.9, z0)], -0.3, 0.85,
                        ["stoneB", "stoneB", "top", "stoneB"], "course", None))
    return out


def body(kit, dx, center=None):
    """Pilasters, slits and shields on both halves of the drum (from the -X faces round to the prow)."""
    c = center or (CENTRE[0] + dx, CENTRE[1])
    out = []
    for half in (BODY, mirror(BODY)[::-1]):
        pts = shift(half, dx)
        for i in (2, 4, 5):                                  # the corners (11.84 lies on the long face)
            (xp, yp), (x, y), (xn, yn) = pts[i - 1], pts[i], pts[i + 1]
            n0 = V((yp - y, x - xp, 0)).normalized()
            n1 = V((y - yn, xn - x, 0)).normalized()
            m = n0 + n1
            if m.dot(V((x - c[0], y - c[1], 0))) < 0:
                m = -m
            out += pilaster(x, y, math.atan2(m.y, m.x))
        segs = segments(pts, c)
        a, t, n, L = segs[2]                                 # 0.84 .. 11.84 .. 23.3: the long face in two
        a2, t2, n2, L2 = segs[3]
        out += slit(kit, a, t, n, L * 0.52) + slit(kit, a2, t2, n2, L2 * 0.48)
        a, t, n, L = segs[4]                                 # the diagonal face
        out += slit(kit, a, t, n, L / 2)
        a, t, n, L = segs[5]                                 # beside the prow: a White Tree shield
        out += kit.shield(a, t, n, L / 2 - 0.4, 22.5, 3.2, 10.2)
    return out


# ------------------------------------------------------------------ the parapet
def band(path, center):
    """A black band standing proud of the parapet's battered face (1.0 to 1.45 out at z 50, flush
    at 56), its front 0.95 out of the top's outer line: inside EA's footprint (|y| 22)."""
    z0, z1 = BAND
    prof = [(-0.5, z0), (0.95, z0), (0.95, z1), (-0.5, z1)]
    return sweep(path, prof, ["stoneB", "enamel", "top", None], center=center)[0]


def merlons(kit, path, center, trim0=0.15, trim1=0.15):
    """Square merlons along the parapet's top (its outer line `path`, 1.0 thick)."""
    out = []
    segs = segments(path, center)
    for i, (a, t, n, L) in enumerate(segs):
        u0 = trim0 if i == 0 else 0.15
        u1 = L - (trim1 if i == len(segs) - 1 else 0.15)
        if u1 - u0 >= MERLONS["w"]:
            out += kit.merlons(a, t, n, u0, u1, Z_TOP, -0.95, -0.05, **MERLONS)
    return out


def build(kit, dx=0.0):
    """Trebuchet A's additions (B adds its own round its block: men/trebuchet_b)."""
    c = (CENTRE[0] + dx, CENTRE[1])
    out = []
    for half in (BODY, mirror(BODY)[::-1]):
        out += plinth(shift(half[1:-1], dx), c)
    out += body(kit, dx)
    ring = shift(PARAPET, dx) + [(x, -y) for x, y in shift(PARAPET, dx)[::-1][1:]]
    out += band(ring, c)
    for half in (PARAPET, [(x, -y) for x, y in PARAPET]):
        out += merlons(kit, shift(half, dx), c, trim0=1.8, trim1=1.7)
    out += kit.pinnacle(36.2 + dx, 0.0, Z_TOP - 0.4, Z_TOP + 2.8, half=1.1, spire=4.2)
    for sy in (-1, 1):
        out += kit.pinnacle(12.8 + dx, sy * 20.55, Z_TOP - 0.4, Z_TOP + 2.8, half=0.95, spire=4.0)
    return out


# ------------------------------------------------------------------ the stair-house (B variations)
def stair_house(kit, x_front, x_back, sides, hw, dh, floor, shield=(2.7, 8.4, 56.0)):
    """EA's little barrel-roofed stair-house on a B variation's block or wall walk (trebuchet_b,
    arrow_tower_b: the same house, sized per model): its door on the +X face (half dh, springing at
    68.06, crown 72.0) under a voussoir archivolt with a keystone crest, moulded imposts and
    rusticated quoins down the jambs to the floor; pinnacles on its four corners (the barrel
    springs at 69.9); a White Tree shield on each side face (sides: its -Y and +Y faces' y)."""
    yc = (sides[0] + sides[1]) / 2
    a, t, n = V((x_front, yc, 0)), V((0, 1, 0)), V((1, 0, 0))
    # under the facade's barrel line (the stones' backs are open): outer crown 73.7, keystone 74.4
    out = kit.voussoirs(a, t, n, (dh, 3.95, 68.06), (hw - 0.1, 5.6, 68.06), -0.2, 1.2, count=9, gap=0.08,
                        key=(0.9, 74.4, 0.5))
    long = hw - dh - 0.25
    for e in (-1, 1):
        u0, u1 = sorted((e * (dh - 0.4), e * (hw + 0.4)))
        out.append(prism_uz(a, t, n, [(u0, 67.0), (u1, 67.0), (u1, 68.06), (u0, 68.06)], -0.2, 1.5,
                            ["stoneB", "course", "top", "course"], "course", None))
        z, step = floor + 0.2, (67.0 - floor - 0.2) / 5
        for i in range(5):
            w = long if i % 2 == 0 else 0.7 * long
            u0, u1 = sorted((e * (dh - 0.05), e * (dh - 0.05 + w)))
            out.append(prism_uz(a, t, n, [(u0, z + 0.1), (u1, z + 0.1), (u1, z + step - 0.1), (u0, z + step - 0.1)],
                                -0.2, 0.6, ["stoneB", "stoneB", "top", "stoneB"], "stoneA", None))
            z += step
        for x in (x_front - 0.78, x_back + 0.76):
            out += kit.pinnacle(x, yc + e * (hw - 0.8), 64.5, 70.6, half=0.95, spire=4.0)
        half, height, zs = shield
        side = V(((x_front + x_back) / 2, sides[1] if e > 0 else sides[0], 0))
        out += kit.shield(side, V((-e, 0, 0)), V((0, e, 0)), 0.0, zs, half, height)
    return out
