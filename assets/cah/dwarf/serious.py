"""The Dwarven Create-a-Hero pilot's serious parts: forged Erebor-language gear (assets/dwarves'
palette, painted in paint.py).

Design space is CHDW_TM_U_SKN's rest space: +X front, +Y the dwarf's left, +Z up (head bone at
z 14.8; EA's helmets between z 15.5 and 19). Helmets are drawn on a round head guide and seated on
the dwarf's head by helm_fit (EA's brim height). Every function draws one sub-object into a Gear.
"""
import math

from ..kit.geom import add, cross, mul, norm, sub

HEAD = ((0.18, 0.0, 0.0), [1, 0, 0], [0, 1, 0], [0, 0, 1])

def helm_fit(p):
    """Seat a helmet drawn on the round head guide on the dwarf's own head: 12 % narrower, raised
    to EA's brim height (HLMT_06's rim sits at z 16.6) with the brow tilted up at the front."""
    x, y, z = p
    return (0.1 + (x - 0.18) * 0.88, y * 0.9, 16.0 + (z - 16.0) * 0.95 + 0.36 + 0.24 * (x - 0.18) / 2.3)

def brow(t):
    """The helmet rim rises over the eyes and drops over the nape."""
    return 0.32 * math.cos(t) - 0.05

def along(profile, t, lift, rim=brow, start=0):
    """The dome's surface line at angle t, bottom to top, `lift` above it."""
    out = []
    for k, (rx, ry, z) in enumerate(profile[start:], start):
        out.append((HEAD[0][0] + (rx + lift) * math.cos(t), (ry + lift) * math.sin(t), z + (rim(t) if rim and k == 0 else 0)))
    return out

def _shoulder_frame(s):
    """(origin, X, Y, Z) over the shoulder joint of side s (+1 left, -1 right): Z out and up."""
    joint = (-0.77, s * 2.6, 14.04)
    Z = norm((0.0, s * 0.62, 0.79))
    X = [1, 0, 0]
    Y = cross(Z, X)
    return add(joint, mul(Z, -0.05)), X, Y, Z

def _arm_frame(s, along):
    """A frame round the upper arm, `along` units from the joint: Z down the arm."""
    d = norm((0.06, s * 0.65, -0.76))
    o = add((-0.77, s * 2.6, 14.04), mul(d, along))
    X = norm(cross([0, 0, 1] if s > 0 else [0, 0, -1], d))
    X = X if X[0] > 0 else mul(X, -1)
    Y = cross(d, X)
    return o, X, Y, d

def _outer_arc(s):
    """The arc of an arm band facing away from the body (frame Y points out on the right side,
    in on the left)."""
    c = math.pi * .5 if s < 0 else -math.pi * .5
    return (c - 1.75, c + 1.75)

AXE_C = (1.31, -7.4, 7.67)

AXE_D = norm((0.986, -0.024, -0.163))

AXE_B = norm(sub((0, 0, -1), mul(AXE_D, -0.163)))


(BRONZE, GOLD, IRON, STEEL, MITHRIL, ENAMEL, CLOAK, WRAP, OAK, RUNEBAND, DEVICE, MAIL, GEM, SPANGEN, HEXBRONZE, FUR,
 CREST, FACEPLATE, BLADE, HORN, BRAID, CHEEK, IRONDOME, BRONZEDOME, LEATHER, KDRUNES, BLUESTEEL, FEATHER, PLANKS) = range(29)
H = "B_HEAD"
CX = HEAD[0][0]


def ring(r_x, r_y, z, n=40, a0=0.0, a1=2 * math.pi, rim=brow, closed=True):
    pts = [(CX + r_x * math.cos(a0 + (a1 - a0) * i / n), r_y * math.sin(a0 + (a1 - a0) * i / n),
            z + (rim(a0 + (a1 - a0) * i / n) if rim else 0)) for i in range(n + (0 if closed else 1))]
    return pts + [pts[0]] if closed else pts


def edge(m, pts, r, tag, bone=H, sides=6, squash=1.0):
    m.sweep(pts, [r] * len(pts), tag, bone, sides=sides, squash=squash)


def band_shell(m, r_x, r_y, z0, z1, tag, sides=40):
    """A vertical band whose every ring follows the brow line."""
    prof = [(r_x - .04, r_y - .04, z0), (r_x, r_y, z0 + .05), (r_x, r_y, z1 - .05), (r_x - .04, r_y - .04, z1)]
    rows = []
    o, X, Y, Z = HEAD
    sides = m._sides(sides)
    th = [2 * math.pi * i / sides for i in range(sides + 1)]
    for rx, ry, z in prof:
        rows.append([(CX + rx * math.cos(t), ry * math.sin(t), z + brow(t)) for t in th])
    uvs = [[(i / sides, k / 3) for i in range(sides + 1)] for k in range(4)]
    if m.lod < .8:                          # trimmed: the band's two bevel rings dropped
        rows, uvs = [rows[0], rows[3]], [uvs[0], uvs[3]]
    m.grid(rows, uvs, tag, H, wrap=True)


def fin(m, path, heights, thick, tag, centre):
    """A crest fin standing on `path` (points on the dome), outward from `centre`, of the given
    heights, as convex quad plates, with a rolled gold edge along its top."""
    tops = []
    for p, h in zip(path, heights):
        d = norm(sub(p, centre))
        tops.append(add(p, mul(d, h)))
    if m.lod >= .8:
        for a, b, ta, tb in zip(path, path[1:], tops, tops[1:]):
            m.slab([a, b, tb, ta], thick, (0, 1, 0), tag, H, bevel=.025)
    else:                                   # trimmed: one plate, the same outline
        m.ribbon(path, tops, tag, H)
    edge(m, tops, thick * .55, GOLD, sides=6)
    edge(m, path, thick * .7, GOLD, sides=6)


def nasal2(m, x, top, mid, bottom, w_top, w_mid, w_bot, tag, ridge_tag=GOLD, thick=.15):
    m.slab([(x, -w_top, top), (x, w_top, top), (x + .03, w_mid, mid), (x + .03, -w_mid, mid)], thick, (1, 0, .1), tag, H)
    m.slab([(x + .03, -w_mid, mid), (x + .03, w_mid, mid), (x + .07, w_bot, bottom), (x + .07, -w_bot, bottom)], thick,
           (1, 0, .1), tag, H)
    edge(m, [(x + .1, 0, top), (x + .12, 0, mid), (x + .16, 0, bottom + .05)], .05, ridge_tag)


def cheeks(m, rx, ry, z0, z1, centre, half, tag, rivets=3):
    for s in (1, -1):
        c = s * centre
        m.shell(HEAD, [(rx + .06, ry + .06, z0), (rx, ry, (z0 + z1) / 2), (rx - .04, ry - .04, z1)], tag, H, sides=8,
                arc=(c - half, c + half), double=True)
        edge(m, [(CX + (rx + .09) * math.cos(c + a), (ry + .09) * math.sin(c + a), z0) for a in
                 [half * (2 * i / 6 - 1) for i in range(7)]], .07, GOLD)
        edge(m, [(CX + (rx + .07) * math.cos(c + half * .98), (ry + .07) * math.sin(c + half * .98), z) for z in
                 (z0, (z0 + z1) / 2, z1)], .06, GOLD)
        for k in range(rivets):
            a = c + half * (k - (rivets - 1) / 2) * .6
            m.stud((CX + (rx + .03) * math.cos(a), (ry + .03) * math.sin(a), z1 - .18), (math.cos(a), math.sin(a), 0),
                   .08, STEEL, H, sides=6)


# ------------------------------------------------------------------ helmets
ER_DOME = [(2.18, 1.98, 15.92), (2.30, 2.10, 16.05), (2.31, 2.11, 16.5), (2.25, 2.06, 17.0), (2.06, 1.89, 17.55),
           (1.72, 1.58, 18.05), (1.22, 1.12, 18.45), (.62, .57, 18.7), (.05, .05, 18.8)]


def helm_erebor(m):
    """The crowned helm of Erebor: an engraved bronze dome on a blue rune band, a gilded crown of
    eight points set with sapphires, a tall gilded crest from brow to nape, heavy gold brows over a
    flared nasal, engraved cheek guards and a nape guard."""
    m.shell(HEAD, ER_DOME, BRONZEDOME, H, sides=40, rim=brow)
    band_shell(m, 2.38, 2.18, 16.0, 16.56, RUNEBAND)
    edge(m, ring(2.41, 2.21, 16.0), .08, GOLD)
    edge(m, ring(2.41, 2.21, 16.56), .08, GOLD)
    for k in range(8):                       # the crown: pointed gilded plates leaning on the dome
        t = k * math.pi / 4 + math.pi / 8
        z = 16.56 + brow(t)
        r0x, r0y, r1x, r1y = 2.37, 2.17, 2.18, 2.0
        c, s = math.cos(t), math.sin(t)
        tx, ty = -s, c
        P = lambda rx, ry, w, zz: (CX + rx * c + w * tx, ry * s + w * ty, zz)
        m.slab([P(r0x, r0y, -.28, z), P(r0x, r0y, .28, z), P((r0x + r1x) / 2, (r0y + r1y) / 2, .2, z + .42),
                P(r1x, r1y, 0, z + .78), P((r0x + r1x) / 2, (r0y + r1y) / 2, -.2, z + .42)], .1, (c, s, .25), CREST, H,
               bevel=.03)
        m.stud(P(2.31, 2.11, 0, z + .3), (c, s, .3), .1, GEM, H, h=.08)
    front = along(ER_DOME, 0.0, 0.0, start=3)
    back = along(ER_DOME, math.pi, 0.0, start=3)
    path = front[:-1] + back[::-1][1:]
    n = len(path)
    fin(m, path, [.25 + .55 * math.sin(math.pi * i / (n - 1)) for i in range(n)], .14, CREST, (CX, 0, 16.3))
    for s in (1, -1):                         # heavy gold brows over the eyes
        edge(m, [(CX + 2.47 * math.cos(s * a), 2.27 * math.sin(s * a), 16.3 + brow(a) + .1 * math.sin(math.pi * a / .95))
                 for a in [.08 + .87 * i / 8 for i in range(9)]], .1, GOLD, squash=.6)
    nasal2(m, 2.42, 16.45, 15.75, 15.2, .22, .14, .26, CHEEK)
    cheeks(m, 2.42, 2.24, 14.75, 16.0, math.pi / 2 * .74, .44, CHEEK)
    m.shell(HEAD, [(2.42, 2.24, 15.0), (2.34, 2.16, 15.5), (2.24, 2.06, 15.9)], BRONZE, H, sides=20,
            arc=(math.pi * .64, math.pi * 1.36), double=True)
    edge(m, ring(2.45, 2.27, 15.0, n=14, a0=math.pi * .64, a1=math.pi * 1.36, rim=None, closed=False), .07, GOLD)


IH_DOME = [(2.22, 2.02, 15.85), (2.36, 2.16, 15.95), (2.38, 2.18, 16.7), (2.30, 2.10, 17.45), (2.06, 1.88, 18.1),
           (1.55, 1.42, 18.55), (.85, .78, 18.8), (.04, .04, 18.88)]


def helm_ironhills(m):
    """Iron Hills war-mask: a black-iron helm in eight riveted plates with a steel comb, and a
    full boar mask: a brow bar, cheek plates and a jutting boar snout with ivory tusks, the eyes
    left in shadowed slots, over three nape lames."""
    m.shell(HEAD, IH_DOME, IRONDOME, H, sides=8, rim=brow, arc=(math.pi / 8, math.pi / 8 + 2 * math.pi))
    edge(m, ring(2.44, 2.24, 15.95), .13, IRON, sides=8)
    comb = along(IH_DOME, 0.0, -.02, start=2)[:-1] + along(IH_DOME, math.pi, -.02, start=2)[::-1][1:]
    fin(m, comb, [.22] * len(comb), .2, IRON, (CX, 0, 16.3))
    o = HEAD
    # the mask (pre-fit space: eyes 15.4-15.85, nose 14.6)
    m.shell(o, [(2.80, 2.42, 15.85), (2.84, 2.46, 16.05), (2.78, 2.40, 16.35)], FACEPLATE, H, sides=16, arc=(-1.2, 1.2),
            double=True)
    for s in (1, -1):
        a = (.16, 1.2) if s > 0 else (-1.2, -.16)
        m.shell(o, [(2.86, 2.48, 14.55), (2.88, 2.5, 15.0), (2.82, 2.44, 15.4)], FACEPLATE, H, sides=8, arc=a, double=True)
        b = (.62, 1.2) if s > 0 else (-1.2, -.62)
        m.shell(o, [(2.82, 2.44, 15.4), (2.80, 2.42, 15.85)], FACEPLATE, H, sides=6, arc=b, double=True)
        for k in range(4):
            t = s * (.3 + .25 * k)
            m.stud((CX + 2.92 * math.cos(t), 2.53 * math.sin(t), 14.68), (math.cos(t), math.sin(t), 0), .08, STEEL, H)
            m.stud((CX + 2.88 * math.cos(t), 2.48 * math.sin(t), 16.2), (math.cos(t), math.sin(t), .2), .08, STEEL, H)
        tusk = [(3.2, s * .5, 14.75), (3.36, s * .8, 14.72), (3.42, s * 1.12, 14.9), (3.32, s * 1.35, 15.25),
                (3.12, s * 1.45, 15.55)]
        m.sweep(tusk, [.15, .13, .1, .07, .02], HORN, H, sides=8)
    secs = []                                  # the snout: rounded sections jutting forward
    for k, (x, hw, z0, z1) in enumerate([(2.7, .42, 14.5, 15.95), (2.98, .46, 14.5, 15.6), (3.25, .44, 14.55, 15.25),
                                         (3.5, .40, 14.6, 15.05), (3.62, .36, 14.62, 14.98)]):
        zc, hz = (z0 + z1) / 2, (z1 - z0) / 2
        secs.append([(x, hw * math.cos(a), zc + hz * math.sin(a)) for a in [2 * math.pi * i / 12 for i in range(12)]])
    m.loft(secs, FACEPLATE, H, uv=lambda k, i: (i / 12, k / 4))
    for s in (1, -1):
        m.stud((3.64, s * .14, 14.8), (1, 0, 0), .09, IRON, H, h=.03)
    for k, (z0, z1, r) in enumerate([(15.45, 15.95, 2.44), (15.0, 15.5, 2.62), (14.55, 15.05, 2.8)]):
        arc = (math.pi * .56, math.pi * 1.44)
        m.shell(HEAD, [(r, r * .93, z0), (r - .16, (r - .16) * .93, z1)], IRONDOME, H, sides=16, arc=arc, double=True)
        edge(m, ring(r + .02, (r + .02) * .93, z0, n=16, a0=arc[0], a1=arc[1], rim=None, closed=False), .07, STEEL)


KD_DOME = [(2.20, 2.00, 15.88), (2.32, 2.12, 15.96), (2.32, 2.12, 16.55), (2.22, 2.02, 17.3), (1.92, 1.75, 18.2),
           (1.40, 1.27, 19.1), (.78, .71, 19.85), (.25, .23, 20.35), (.04, .04, 20.5)]


def helm_khazad(m):
    """Moria spangenhelm: eight mithril plates (each with a raised sheen ridge) joined by gilded
    spangen and steel rivets, a rune band in gold on mithril set with sapphires, a long spike
    finial, a long nasal and a scalloped mail aventail on a leather band."""
    m.shell(HEAD, KD_DOME, SPANGEN, H, sides=16, rim=brow,
            bump=lambda t, k: .06 * abs(math.cos(4 * t)) ** 6 * (k > 1))
    for k in range(8):
        t = k * math.pi / 4 + math.pi / 8
        strip = along(KD_DOME, t, .05, start=2)[:-1]
        m.sweep(strip, [.15 if m.lod >= .5 else .11] * len(strip), GOLD, H, sides=6, squash=.4)
        for p in strip[:-1]:
            m.stud(add(p, (.04 * math.cos(t), .04 * math.sin(t), 0)), (math.cos(t), math.sin(t), .3), .07, STEEL, H)
    band_shell(m, 2.38, 2.18, 16.0, 16.62, KDRUNES)
    edge(m, ring(2.41, 2.21, 16.0), .07, GOLD)
    edge(m, ring(2.41, 2.21, 16.62), .07, GOLD)
    for k in range(8):
        t = k * math.pi / 4
        m.stud((CX + 2.43 * math.cos(t), 2.23 * math.sin(t), 16.31 + brow(t)), (math.cos(t), math.sin(t), 0),
               .22 if k == 0 else .15, GEM, H)
    m.tube((CX, 0, 20.4), (CX, 0, 21.3), .14, MITHRIL, H, sides=8, r1=.01)
    m.stud((CX, 0, 20.3), (0, 0, 1), .3, GOLD, H, h=.22, sides=8)
    nasal2(m, 2.44, 16.62, 15.6, 14.85, .2, .13, .2, MITHRIL)
    arc = (math.pi * .38, math.pi * 1.62)
    m.shell(HEAD, [(2.66, 2.46, 14.25), (2.6, 2.4, 14.8), (2.46, 2.26, 15.35), (2.30, 2.10, 15.95)], MAIL, H, sides=30,
            arc=arc, double=True, rim=lambda t: -.16 * abs(math.sin(9 * t)))
    edge(m, ring(2.34, 2.14, 15.95, n=24, a0=arc[0], a1=arc[1], rim=None, closed=False), .09, LEATHER, sides=6, squash=.6)


RM_DOME = [(2.2, 2.0, 15.9), (2.32, 2.12, 16.0), (2.33, 2.13, 16.6), (2.24, 2.05, 17.2), (1.98, 1.82, 17.8),
           (1.5, 1.38, 18.3), (.85, .78, 18.6), (.04, .04, 18.72)]


def helm_ram(m):
    """Grey Mountains ram helm: a dark bronze dome on an engraved band, with two great ridged rams'
    horns curling back from the temples and down past the ears, a nasal and small cheek plates."""
    m.shell(HEAD, RM_DOME, BRONZEDOME, H, sides=36, rim=brow)
    band_shell(m, 2.38, 2.18, 16.0, 16.5, HEXBRONZE)
    edge(m, ring(2.41, 2.21, 16.0), .08, GOLD)
    edge(m, ring(2.41, 2.21, 16.5), .06, GOLD)
    ridge = along(RM_DOME, 0.0, 0, start=2)[:-1] + along(RM_DOME, math.pi, 0, start=2)[::-1][1:]
    m.sweep(ridge, [.13] * len(ridge), BRONZE, H, sides=6, squash=.5)
    for s in (1, -1):
        C = (-0.15, s * 2.4, 16.75)
        A, n = 1.75 * math.pi, 26
        pts, radii = [], []
        for i in range(n + 1):
            f = i / n
            a = 1.15 + A * f
            r = 1.0 + .75 * f
            pts.append((C[0] + r * math.cos(a), C[1] + s * (.05 + 1.1 * f), C[2] + r * math.sin(a)))
            radii.append(.62 * (1 - f) ** .75 + .06)
        m.sweep(pts, radii, HORN, H, sides=10)
        m.stud((C[0] + .3, s * 2.32, 17.6), (0, s, .2), .3, GOLD, H, h=.15, sides=8)
    nasal2(m, 2.42, 16.4, 15.8, 15.3, .2, .13, .2, BRONZE)
    cheeks(m, 2.42, 2.24, 14.95, 16.0, math.pi / 2 * .74, .36, CHEEK, rivets=2)


BM_DOME = [(2.18, 1.98, 15.92), (2.3, 2.1, 16.0), (2.31, 2.11, 16.45), (2.2, 2.02, 17.1), (1.95, 1.79, 17.7),
           (1.5, 1.38, 18.2), (.9, .83, 18.55), (.04, .04, 18.7)]


def helm_bluemountains(m):
    """Ered Luin winged helm: a blue-steel cap on a gold braid band, bronze feathered wings rising
    from the temples, a gem finial and a short nasal: the western halls' lighter style."""
    m.shell(HEAD, BM_DOME, BLUESTEEL, H, sides=36, rim=brow)
    band_shell(m, 2.37, 2.17, 16.0, 16.4, BRAID)
    edge(m, ring(2.4, 2.2, 16.0), .07, GOLD)
    edge(m, ring(2.4, 2.2, 16.4), .07, GOLD)
    for s in (1, -1):
        base = (-.05, s * 2.2, 16.85)
        for k in range(6):
            a = math.radians(28 + 17 * k)
            L = 2.0 + .28 * k - .035 * k * k
            d = (-math.cos(a) * .9, s * .35, math.sin(a))
            dn = norm(d)
            side = norm(cross(dn, (0, s, 0)))
            y_off = (0, s * .05 * k, 0)
            b0 = add(base, y_off)
            tip = add(b0, mul(dn, L))
            w = .3
            m.slab([add(b0, mul(side, w * .5)), add(add(b0, mul(dn, L * .55)), mul(side, w)), tip,
                    add(add(b0, mul(dn, L * .55)), mul(side, -w)), add(b0, mul(side, -w * .5))], .07, (0, s, 0), FEATHER, H,
                   bevel=.02)
        m.stud((base[0] + .1, s * 2.3, 16.85), (0, s, 0), .26, GEM, H, h=.15)
    m.stud((CX, 0, 18.66), (0, 0, 1), .25, GOLD, H, h=.2, sides=8)
    m.stud((CX, 0, 18.85), (0, 0, 1), .14, GEM, H, h=.18)
    nasal2(m, 2.41, 16.35, 15.8, 15.35, .18, .11, .17, BLUESTEEL)


# ------------------------------------------------------------------ shoulders, cloak
def pauldrons_erebor(m):
    """Erebor pauldrons: an engraved bronze dome edged in rolled gold over each shoulder, a
    sapphire hexagon boss, three riveted lames down the arm."""
    K = .85
    for s, bone in ((1, "BAT_UARML"), (-1, "BAT_UARMR")):
        f = _shoulder_frame(s)
        prof = [(a * K, b * K, c * K) for a, b, c in [(2.15, 1.85, 0), (2.18, 1.88, .28), (1.98, 1.70, .78), (1.50, 1.30, 1.2),
                                                       (.85, .75, 1.45), (.05, .05, 1.55)]]
        m.shell(f, prof, BRONZEDOME, bone, sides=28)
        o, X, Y, Z = f
        rim = [add(add(add(o, mul(X, 2.2 * K * math.cos(t))), mul(Y, 1.9 * K * math.sin(t))), mul(Z, .1))
               for t in [2 * math.pi * i / 28 for i in range(29)]]
        edge(m, rim, .1, GOLD, bone)
        top = add(o, mul(Z, 1.5 * K))
        m.stud(top, Z, .4, HEXBRONZE, bone, h=.18, sides=6)
        m.stud(add(top, mul(Z, .16)), Z, .22, GEM, bone, h=.14, sides=6)
        for k, a_ in enumerate((1.0, 1.65, 2.3)):
            fo, fX, fY, fZ = _arm_frame(s, a_)
            r = (1.6 - .13 * k) * .92
            arc = _outer_arc(s)
            m.shell((fo, fX, fY, fZ), [(r, r * .95, 0), (r - .05, (r - .05) * .95, .58)], BRONZE, bone, sides=14, arc=arc,
                    double=True)
            pts = [add(add(add(fo, mul(fX, (r + .02) * math.cos(t))), mul(fY, (r + .02) * .95 * math.sin(t))), mul(fZ, .58))
                   for t in [arc[0] + (arc[1] - arc[0]) * i / 14 for i in range(15)]]
            edge(m, pts, .06, GOLD, bone)
            for t in (arc[0] + .5, (arc[0] + arc[1]) / 2, arc[1] - .5):
                p = add(add(add(fo, mul(fX, r * math.cos(t))), mul(fY, r * .95 * math.sin(t))), mul(fZ, .3))
                m.stud(p, add(mul(fX, math.cos(t)), mul(fY, math.sin(t))), .07, STEEL, bone)


def mantle_erebor(m):
    """Erebor mantle: black-iron shoulder caps rimmed in bronze and a heavy cloak of Erebor blue
    hanging from a fur collar, falling in seven deep folds to a gold-braided hem below the belt,
    flared to clear the hips (it rides the upper spine: EA's in-game rig has no cape bones)."""
    for s, bone in ((1, "BAT_UARML"), (-1, "BAT_UARMR")):
        f = _shoulder_frame(s)
        o, X, Y, Z = f
        m.shell(f, [(2.0, 1.74, 0), (2.03, 1.76, .25), (1.76, 1.52, .78), (1.08, .94, 1.22), (.05, .05, 1.36)], IRONDOME, bone,
                sides=24)
        edge(m, [add(add(add(o, mul(X, 2.06 * math.cos(t))), mul(Y, 1.8 * math.sin(t))), mul(Z, .08))
                 for t in [2 * math.pi * i / 24 for i in range(25)]], .09, BRONZE, bone)
        m.stud(add(o, mul(Z, 1.32)), Z, .26, BRONZE, bone, h=.16)
    back = ((-0.7, 0.0, 0.0), [1, 0, 0], [0, 1, 0], [0, 0, 1])
    arc = (math.pi * .66, math.pi * 1.34)
    prof = [(3.95, 4.05, 7.9), (3.75, 3.9, 8.9), (3.55, 3.75, 9.9), (3.4, 3.62, 10.8), (3.2, 3.45, 11.8), (3.0, 3.3, 12.9), (2.75, 3.15, 13.9), (2.5, 3.0, 14.7),
            (2.28, 2.88, 15.25)]
    K = len(prof)
    folds = lambda t, k: .24 * (1 - k / (K - 1)) ** 1.2 * math.sin(7 * 2 * math.pi * (t - arc[0]) / (arc[1] - arc[0]))
    rows = m.shell(back, prof, CLOAK, "BAT_SPINE2", sides=56, arc=arc, double=True, bump=folds)
    edge(m, [add(p, (-.02, 0, -.02)) for p in rows[0]], .1, BRAID, "BAT_SPINE2", sides=6)
    for col in (0, -1):
        edge(m, [r[col] for r in rows], .08, BRAID, "BAT_SPINE2", sides=6)
    collar = [(-0.7 + 2.45 * math.cos(a), 3.0 * math.sin(a), 15.35 + .15 * math.cos(a)) for a in
              [math.pi * (.6 + .8 * i / 16) for i in range(17)]]
    m.sweep(collar, [.36 + .1 * math.sin(math.pi * i / 16) for i in range(17)], FUR, "BAT_SPINE2", sides=10)
    for s in (1, -1):
        m.stud((.35, s * 2.55, 15.1), (1, s * .3, .2), .3, GOLD, "BAT_SPINE2", h=.18, sides=8)
        m.stud((.5, s * 2.6, 15.15), (1, s * .3, .2), .16, GEM, "BAT_SPINE2", h=.14)
    m.sweep([(.45, -2.55, 15.0), (1.15, -1.3, 14.35), (1.35, 0, 14.15), (1.15, 1.3, 14.35), (.45, 2.55, 15.0)],
            [.07] * 5, GOLD, "BAT_SPINE2", sides=6)


# ------------------------------------------------------------------ shield and axe
def shield_erebor(m):
    """Erebor round shield: the Lonely Mountain device in gold on a domed blue field, a rolled gold
    rim with sixteen steel rivets, a gold inner ring, a three-tier boss (hexagonal plate, gilded
    dome, steel spike), and a planked oak back with leather straps."""
    o = (-0.6, 4.78, 11.5)
    fx = norm((0.143, 0.624, -0.776))
    fy = norm((0.99, -0.092, 0.109))
    face = mul(cross(fx, fy), -1)
    c = add(add(o, mul(fx, 1.7)), mul(face, 1.55))
    up = norm(sub((0, 0, 1), mul(face, face[2])))          # the device stands upright at rest
    Y = up
    X = cross(Y, face)
    f = (c, X, Y, face)
    R = 2.75
    m.shell(f, [(R * .98, R * .98, 0), (R, R, .12), (R * .92, R * .92, .3), (R * .74, R * .74, .48), (R * .45, R * .45, .62),
                (R * .2, R * .2, .68), (.02, .02, .7)], DEVICE, "BAT_FARML", sides=40, planar=R)
    pts = lambda r, h, n=40: [add(add(add(c, mul(X, r * math.cos(t))), mul(Y, r * math.sin(t))), mul(face, h))
                              for t in [2 * math.pi * i / n for i in range(n + 1)]]
    m.sweep(pts(R + .02, .06), [.2] * 41, GOLD, "BAT_FARML", sides=8)
    m.sweep(pts(R * .62, .53), [.06] * 41, GOLD, "BAT_FARML", sides=6)
    for k in range(16):
        t = 2 * math.pi * k / 16
        p = add(add(add(c, mul(X, (R - .3) * math.cos(t))), mul(Y, (R - .3) * math.sin(t))), mul(face, .2))
        m.stud(p, face, .1, STEEL, "BAT_FARML")
    m.stud(add(c, mul(face, .6)), face, .78, HEXBRONZE, "BAT_FARML", h=.24, sides=6)
    m.stud(add(c, mul(face, .82)), face, .5, GOLD, "BAT_FARML", h=.45, sides=12)
    m.tube(add(c, mul(face, 1.2)), add(c, mul(face, 1.75)), .14, STEEL, "BAT_FARML", sides=8, r1=.01)
    back = pts(R * .99, -.12, 40)[:-1]
    m.flat(back[::-1], PLANKS, "BAT_FARML")
    for w in (-.7, .7):
        m.slab([add(add(c, mul(Y, w - .18)), add(mul(X, -1.6), mul(face, -.2))),
                add(add(c, mul(Y, w - .18)), add(mul(X, 1.6), mul(face, -.2))),
                add(add(c, mul(Y, w + .18)), add(mul(X, 1.6), mul(face, -.2))),
                add(add(c, mul(Y, w + .18)), add(mul(X, -1.6), mul(face, -.2)))], .08, mul(face, -1), LEATHER, "BAT_FARML")


def axe_erebor(m):
    """Erebor bearded war axe: a broad steel blade sweeping down into a long beard, gold-inlaid
    knotwork along it, a hexagonal bronze socket with gold collars and steel langets, a back spike,
    an oak haft in blue leather wraps and a hexagonal pommel. EA's AXE_02 grip and reach."""
    p = lambda t, s=0.0, w=0.0: add(add(add(AXE_C, mul(AXE_D, t)), mul(AXE_B, s)), mul(cross(AXE_D, AXE_B), w))
    bone = "B_HAND_R"
    side = cross(AXE_D, AXE_B)
    m.tube(p(-7.0), p(3.6), .2, OAK, bone, sides=8)
    for t0, t1 in ((-5.5, -3.1), (-1.4, -.5)):
        m.tube(p(t0), p(t1), .245, WRAP, bone, sides=8)
    for t in (-6.85, -5.55, -3.05, -.45):
        m.tube(p(t - .1), p(t + .1), .28, GOLD, bone, sides=8)
    m.stud(p(-7.05), mul(AXE_D, -1), .38, HEXBRONZE, bone, h=.45, sides=6)
    secs = [[p(t, .4 * math.cos(a), .4 * math.sin(a)) for a in [2 * math.pi * i / 6 + math.pi / 6 for i in range(6)]]
            for t in (.7, 3.35)]
    m.loft(secs, HEXBRONZE, bone)
    for t in (.7, 3.35):
        m.tube(p(t - .09), p(t + .09), .46, GOLD, bone, sides=6)
    m.tube(p(3.35), p(3.75), .3, GOLD, bone, sides=6, r1=.05)
    for w in (1, -1):                       # langets down the haft
        m.sweep([p(.75, 0, w * .22), p(-.2, 0, w * .22), p(-.95, 0, w * .2)], [.08, .07, .04], STEEL, bone, sides=4,
                squash=.4)
    lo = lambda s: 1.25 - 3.4 * (s / 3.4) ** 2.4          # the beard sweeps down toward the hand
    hi = lambda s: 2.75 + 1.05 * (s / 3.4) ** 2.2         # the toe flares up past the socket
    mid, half = (1.25 - 3.4 + 2.75 + 1.05) / 2, (2.75 + 1.05 - 1.25 + 3.4) / 2
    m.blade(p(0, .35), AXE_D, AXE_B, side, lo, hi, 3.4, lambda s: .46 * max(0.0, 1 - s / 3.4) ** .7, BLADE, bone,
            steps=(14, 12), bulge=lambda t: .55 * max(0.0, 1 - ((t - mid) / half) ** 2))
    m.tube(p(2.05, -.35), p(2.05, -1.75), .3, STEEL, bone, sides=6, r1=.02)
    m.tube(p(2.05, -.3), p(2.05, -.55), .36, GOLD, bone, sides=6)


SERIOUS = {   # sub-object: (group, design, name, description)
    "SKH_HLMT_ER": ("CreateAHero_Helmet", helm_erebor, "Crown-helm of Erebor",
                    "The crowned helm of the Lonely Mountain: a gilded crest and crown over a blue rune band."),
    "SKH_HLMT_IH": ("CreateAHero_Helmet", helm_ironhills, "Iron Hills War-mask",
                    "Black iron of Dain's folk: a boar mask with ivory tusks and riveted plates."),
    "SKH_HLMT_KD": ("CreateAHero_Helmet", helm_khazad, "Spangenhelm of Khazad-dum",
                    "A tall mithril helm of Moria, gilded and rune-banded, with a mail aventail."),
    "SKH_HLMT_RM": ("CreateAHero_Helmet", helm_ram, "Ram Helm of the Grey Mountains",
                    "Dark bronze crowned by the curling horns of the mountain ram."),
    "SKH_HLMT_BM": ("CreateAHero_Helmet", helm_bluemountains, "Winged Helm of Ered Luin",
                    "A blue-steel cap of the western halls with bronze feathered wings."),
    "SKH_SLDR_ER": ("CreateAHero_ShoulderPlates", pauldrons_erebor, "Erebor Pauldrons",
                    "Engraved bronze shoulder domes with riveted lames and a sapphire boss."),
    "SKH_SLDR_MN": ("CreateAHero_ShoulderPlates", mantle_erebor, "Erebor Mantle",
                    "Iron shoulder caps and a heavy cloak of Erebor blue with a fur collar."),
    "SKH_SHLD_ER": ("CreateAHero_Shield", shield_erebor, "Shield of Erebor",
                    "The Lonely Mountain beneath the star, in gold on Erebor blue."),
    "SKH_AXE_ER": ("CreateAHero_Weapon", axe_erebor, "Erebor War Axe",
                   "A bearded war axe of the Lonely Mountain, its blade inlaid with gold knotwork."),
}
