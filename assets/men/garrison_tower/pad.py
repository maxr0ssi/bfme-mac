"""The Gondor garrison tower's pieces (Blender side), shared by its two build variations: EA's
GBFDOTOWA (men/garrison_tower) and GBFDOTOWB (men/garrison_tower_b) carry the same tower, B's
shifted DX_B along x and joined on its -X side to a wall run. Every function takes `dx`, the
shift from A's mesh frame, in which all the numbers below are measured.

EA's tower (GBFDOTOWA mesh coordinates):
    shaft    a chamfered square (centre 24.25, 0.26; half 13.05, chamfer 3.7), the citadel's tower
             section, to z 49.79; its foot 0.3 wider to 4.6; then a bevel and a neck in to 53.3
    gate     on the +X face: EA's frame x 39.49, |y| <= 11.17 (spring 28.5, crown 34.6), the
             opening |y| <= 8.3 (spring 26.1, crown 31.2) over a recess at x 38.39; a crest in
             relief above it (x 37.3..38.1, |y| <= 4.5, z 35..46.7)
    buttresses  diagonal, on the two +X corners: out to 41.9 below 17.5, a slope in to 39.7, up
             to 40, then a slope to the shaft's corner at 46.4
    belfry   a larger chamfered square (centre 24.4, 0; half 13.7, chamfer 4.0) from 54.23 to
             69.38, two round-arched windows on each face (u +-4.95 from its middle, 5.2 wide, sill
             57.3, jambs 63.2, crown 65.7)
    dome     chamfered-square rings 69.38 (13.7), 71.62 (10.53), 76.04 (7.73), 79.33 (4.19), a
             square cap and its point at 83.0
EA's footprint (x 10.67..42.82, |y| <= 18.4) leaves nothing on the -X side (toward the citadel's
pad and, in B, the wall): the gallery wraps the three outward faces only.

What stands on it:
    plinth     a moulded base course along the two side faces
    gate       rusticated quoins up the jambs, moulded imposts, a voussoir archivolt with a raised
               keystone, portcullis teeth in the arch
    buttresses a pinnacle on each diagonal buttress's head
    gallery    the citadel's machicolated gallery (corbels, a black band with silver stars, a
               parapet and square merlons) round the shaft top on the three outward faces
    belfry     a voussoir hood and a corbelled sill on every window, a slate-capped pinnacle on
               each chamfer
    crown      the shared tower top (men/wall_hub/dome.py): steel eave band, ribs, a lantern
               cupola, a gilt orb and a steel spike
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import box_rings, prism_uz, sweep

DX_B = -6.18                                  # GBFDOTOWB's tower against GBFDOTOWA's
SHAFT = (24.25, 0.26, 13.05, 3.7)             # centre x, y, half, chamfer
BELFRY = (24.4, 0.0, 13.7, 4.0)
Z_BELFRY = (54.23, 69.38)
DOME = [(69.38, 13.7), (71.62, 10.53), (76.04, 7.73), (79.33, 4.19)]
LANTERN = (79.0, 3.3, 83.6)                   # z0, r, top: EA's cap and point (to 83.0) inside it
FINIAL = (89.0, 98.5)                         # orb, tip (EA's top 83.0: +18.7 %)
GATE_X = 39.49
INNER, OUTER = (8.3, 5.1, 26.1), (11.35, 8.1, 26.1)   # (half, rise, spring) of the archivolt
Z_CORBEL, Z_SLAB, Z_WALK, Z_PARAPET = 43.6, 47.2, 49.8, 51.3
OUT = 2.0                                     # the gallery's front, out of the shaft's faces
WINDOWS = (-4.95, 4.95)                       # along each belfry face, from its middle
Y, X = V((0, 1, 0)), V((1, 0, 0))


def octagon(cx, cy, half, ch):
    return [(p.x, p.y) for p in box_rings((cx - half, cx + half), (cy - half, cy + half), 0.0, ch)]


def front_path(dx, shaft=SHAFT):
    """The shaft's outline from the -Y face's back end round +X to the +Y face's back end."""
    cx, cy, half, ch = shaft
    return octagon(cx + dx, cy, half, ch)[:6]


def build(kit, dx=0.0):
    return (plinth(dx) + gate(kit, dx) + buttress_pinnacles(kit, dx) + gallery(kit, dx)
            + belfry(kit, dx, back=dx != 0.0) + crown(kit, dx))


# ------------------------------------------------------------------ foot
def plinth(dx, shaft=SHAFT, x0=None):
    """A moulded base course along each side face of a chamfered-square shaft (from x0, default
    the back chamfer's end, to the front chamfer)."""
    cx, cy, half, ch = shaft
    prof = [(-0.4, 0.0), (1.2, 0.0), (1.2, 2.3), (0.75, 2.8), (0.75, 3.5), (0.25, 4.0), (-0.4, 4.0)]
    tags = [None, "stoneB", "top", "course", "top", "top", None]
    out = []
    for sy in (-1, 1):
        y = cy + sy * half
        path = [(cx + dx - half + ch if x0 is None else x0, y), (cx + dx + half - ch - 0.3, y)]
        out += sweep(path, prof, tags, center=(cx + dx, cy))[0]
    return out


# ------------------------------------------------------------------ the gate
def z_on(arc, y):
    h, r, s = arc
    return s + r * math.sqrt(max(0.0, 1 - (y / h) ** 2))


def gate(kit, dx):
    a = V((GATE_X + dx, 0.26, 0))
    out = []
    for sy in (-1, 1):                                       # rusticated quoins, long and short
        z, step = 0.4, (INNER[2] - 1.5) / 7
        for i in range(7):
            z1 = z + step
            w = 3.2 if i % 2 == 0 else 2.3
            u0, u1 = sorted((sy * (INNER[0] - 0.05), sy * (INNER[0] + w)))
            out.append(prism_uz(a, Y, X, [(u0, z + 0.12), (u1, z + 0.12), (u1, z1 - 0.12), (u0, z1 - 0.12)], -0.2, 0.75,
                                ["stoneB", "stoneB", "top", "stoneB"], "stoneA", None))
            z = z1
        u0, u1 = sorted((sy * (INNER[0] - 0.4), sy * (OUTER[0] + 0.45)))    # the impost, a moulded capital
        out.append(prism_uz(a, Y, X, [(u0, INNER[2] - 1.1), (u1, INNER[2] - 1.1), (u1, INNER[2]), (u0, INNER[2])],
                            -0.2, 1.55, ["stoneB", "course", "top", "course"], "course", None))
    out += kit.voussoirs(a, Y, X, INNER, OUTER, -0.2, 1.4, count=11, gap=0.1, key=(1.3, OUTER[2] + OUTER[1] + 1.9, 0.6))
    for i in range(7):                                       # portcullis teeth in the arch
        u = -6.3 + 2.1 * i
        top = z_on(INNER, u) + 0.4
        out.append(prism_uz(a, Y, X, [(u - 0.25, 23.0), (u + 0.25, 23.0), (u + 0.25, top), (u - 0.25, top)], -0.75, -0.3,
                            [None, "iron", None, "iron"], "iron", "iron"))
        out.append(prism_uz(a, Y, X, [(u - 0.34, 23.0), (u + 0.34, 23.0), (u, 21.9)], -0.78, -0.27, ["iron"] * 3, "iron", "iron"))
    for z in (24.4, 26.6):
        out.append(prism_uz(a, Y, X, [(-7.9, z - 0.25), (7.9, z - 0.25), (7.9, z + 0.25), (-7.9, z + 0.25)], -0.3, 0.0,
                            ["iron"] * 4, "iron", "iron"))
    return out


def buttress_pinnacles(kit, dx):
    """A pinnacle on the head of each diagonal buttress (its top at 40.0, 1.3 in from its face)."""
    out = []
    for sy in (-1, 1):
        out += kit.pinnacle(37.5 + dx, sy * 13.07, 38.0, 42.0, half=1.2, spire=3.6)
    return out


# ------------------------------------------------------------------ the gallery
def gallery(kit, dx, shaft=SHAFT, z=(Z_CORBEL, Z_SLAB, Z_WALK, Z_PARAPET), clear=5.2, back=0.75, skip=()):
    """The citadel's machicolated gallery (men/fortress/crown.py) round the shaft top on the three
    outward faces; no corbels within `clear` of the front face's middle (the gate's crest). The
    parapet and merlons stand from `back` out (clear of a belfry overhanging the shaft); `skip`:
    segments (0 the -Y face, 1 its chamfer, 2 the front, ...) without merlons (a turret there)."""
    cx, cy, half, ch = shaft
    z_corbel, z_slab, z_walk, z_parapet = z
    path = front_path(dx, shaft)
    c = (cx + dx, cy)
    slab = [(-2.5, z_walk - 0.7), (0.0, z_slab), (OUT, z_slab), (OUT, z_walk), (-2.5, z_walk)]
    out, segs = sweep(path, slab, ["stoneB", "stoneB", "enamel", "top", None], center=c)
    para = [(back, z_walk - 0.1), (OUT - 0.15, z_walk - 0.1), (OUT - 0.15, z_parapet), (back, z_parapet)]
    out += sweep(path, para, [None, "stoneA", "top", "stoneA"], center=c)[0]
    for i, (a, b, t, n) in enumerate(segs):
        L = (b - a).length
        a3 = V((a.x, a.y, 0))
        if L > 10:
            front = abs(n.x) > 0.9
            k = int((L - 1.2) // 3.2)
            u0 = (L - (k - 1) * 3.2) / 2
            for j in range(k):
                u = u0 + j * 3.2
                if front and abs(u - L / 2) < clear:
                    continue
                out += kit.corbel(a3, t, n, u, z_corbel, z1=z_corbel + 1.8, z2=z_slab)
        if i not in skip:
            out += kit.merlons(a3, t, n, 0.15, L - 0.15, z_parapet, back, OUT - 0.15, w=2.3, gap=1.7, h=2.5)
    return out


# ------------------------------------------------------------------ the belfry
def belfry(kit, dx, back=False):
    """A voussoir hood and a corbelled sill on the windows of the three outward faces (the -X face
    lies on EA's footprint); a pinnacle on each chamfer, standing on the belfry's cornice line."""
    bx, by, half, ch = BELFRY
    out = []
    faces = [(V((bx + dx + half, by, 0)), Y, X), (V((bx + dx, by + half, 0)), -X, Y), (V((bx + dx, by - half, 0)), X, -Y)]
    if back:                                                 # B: its wall leaves the -X face free
        faces.append((V((bx + dx - half, by, 0)), -Y, -X))
    for a0, t, n in faces:
        for u in WINDOWS:
            a = a0 + t * u
            out += kit.voussoirs(a, t, n, (3.0, 2.5, 63.2), (3.75, 3.25, 63.2), -0.3, 0.9, count=7, gap=0.07,
                                 key=(0.5, 67.1, 0.3))
            out.append(prism_uz(a, t, n, [(-3.6, 56.6), (3.6, 56.6), (3.6, 57.35), (-3.6, 57.35)], -0.3, 1.1,
                                ["stoneB", "stoneB", "top", "stoneB"], "course", None))
            for e in (-1, 1):
                out.append(prism_uz(a, t, n, [(e * 2.4 - 0.4, 55.2), (e * 2.4 + 0.4, 55.2), (e * 2.4 + 0.4, 56.6),
                                              (e * 2.4 - 0.4, 56.6)], -0.3, 0.8, ["stoneB", "stoneB", None, "stoneB"],
                                    "stoneA", None))
    for sx in (-1, 1):
        for sy in (-1, 1):
            out += kit.pinnacle(bx + dx + sx * 12.05, by + sy * 12.05, 62.5, 70.6, half=1.25, spire=6.2)
    return out


def crown(kit, dx):
    """The shared tower top on EA's dome: steel eave band and ribs, lantern, orb and spike."""
    from ..wall_hub import dome as D
    bx, by, half, ch = BELFRY
    sec = D.Section(bx + dx, by, chamfer=ch / half)
    # the band sits 0.6 under the eave: its buried back stays under the dome's first slope
    out = D.eave_band(sec, half, Z_BELFRY[1] - 0.6) + D.ribs(sec, DOME)
    z0, r, top = LANTERN
    out += kit.lantern(sec.cx, sec.cy, z0, r=r, top=top)
    return out + kit.finial(sec.cx, sec.cy, top - 0.1, *FINIAL)


def banner(kit, dx=0.0, face=-1, u=0.0, shaft=SHAFT, z_top=42.4, width=5.6, length=19.0):
    """The one house-colour banner, hung under the gallery's corbels on a side face."""
    cx, cy, half, ch = shaft
    a = V((cx + dx, cy + face * half, 0))
    t = X if face < 0 else -X
    return kit.banner(a, t, V((0, face, 0)), u, z_top, width, length, d=1.0)
