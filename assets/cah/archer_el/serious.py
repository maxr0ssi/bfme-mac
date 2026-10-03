"""The Archers' serious parts, in the language of our Elven buildings (assets/elves: mithril silver,
mallorn gold, pale birch, crystal; the cloth the player's colour) and the Rangers' green-brown
camo. Drawn in the Elven Archer's creation-screen rest space (geo.py); each draws one sub-object.
"""
import math

from ..kit.geom import add, cross, mul, norm, sub
from . import geo as G
from .geo import BOW, H, HC, HEAD, LOW, SPINE, ball, bowdir, bowpt, edge, ellipse, leaf, opening_rings
from .place import region

(MITH, GOLD, CLOTH, CLOTHVINE, LEAFGOLD, FILIGREE, GEM, LEATHER, ANTLER, GOLDFLUTE, ENAMEL, CAMO, CAMODARK, STAR,
 BIRCH, GRIP, BLADE, FEATHER, LEAFLEATHER, SHIELDFACE, BIRCHBACK, STRING, MITHDARK, SEAGLASS, DARKWOOD, AUTUMN,
 MITHPLATE, LINING) = range(28)


# ------------------------------------------------------------------ hoods
LORIEN_RINGS = [(-0.4, 18.35, 2.3, 3.45, .5), (-0.33, 19.35, 2.12, 2.95, .4), (-0.25, 20.2, 1.98, 2.0, .3),
                (-0.1, 20.95, 2.06, 1.64, .64), (0.0, 21.75, 2.08, 1.64, .64), (-0.02, 22.55, 2.0, 1.58, .58),
                (-0.12, 23.25, 1.8, 1.44, .5), (-0.3, 23.85, 1.4, 1.12, .38), (-0.6, 24.2, .85, .66, .2),
                (-1.05, 24.35, .25, .22, 0.0)]


def hood(m, rings, cloth, trim, clasp, gem=None, star=False, lining=LINING):
    """A hood and short capelet in one: the hood's face opening edged in `trim`, the capelet open
    down the chest, fastened at the throat by a leaf clasp (or the Dunedain star)."""
    rows = opening_rings(m, rings, cloth, H, lining=lining)
    k_open = 3
    rim = [r[0] for r in rows[k_open:]] + [r[-1] for r in rows[k_open:]][::-1][1:]
    edge(m, [add(p, (.04, 0, 0)) for p in rim], .08, trim, H, sides=6)
    edge(m, [add(p, (0, 0, -.03)) for p in rows[0]], .08, trim, H, sides=6)
    for col in (0, -1):
        edge(m, [r[col] for r in rows[:k_open + 1]], .07, trim, H, sides=5)
    c = (1.75, 0.0, 20.15)
    if star:
        m.stud(c, (1, 0, .1), .42, STAR, H, h=.12, sides=16)
        for k in range(8):
            a = math.pi * k / 4
            tip = add(c, (.12, .75 * math.cos(a), .75 * math.sin(a)))
            m.slab([add(c, (.1, .12 * math.cos(a + 1.3), .12 * math.sin(a + 1.3))), tip,
                    add(c, (.1, .12 * math.cos(a - 1.3), .12 * math.sin(a - 1.3)))], .06, (1, 0, 0), MITH, H, bevel=.01)
    elif clasp is not None:
        for s in (1, -1):
            leaf(m, add(c, (0, s * .32, .05)), norm((0, s * .55, .83)), (0, -.83, .55) if s > 0 else (0, .83, .55),
                 1.1, .55, .1, clasp, H, rib=GOLD)
        if gem is not None:
            m.stud(add(c, (.08, 0, .02)), (1, 0, 0), .18, gem, H, h=.14, sides=8)


def hood_lorien(m):
    """The hood of Lorien: a deep cloth hood with an elven point, its edge embroidered in a mallorn
    vine, a capelet over the shoulders, two gold mallorn leaves at the throat round a crystal."""
    hood(m, LORIEN_RINGS, CLOTH, CLOTHVINE, LEAFGOLD, gem=GEM)


RANGER_RINGS = [(-0.4, 18.2, 2.4, 3.5, .52), (-0.33, 19.3, 2.18, 3.0, .42), (-0.25, 20.2, 2.02, 2.05, .3),
                (-0.02, 20.95, 2.15, 1.72, .66), (0.12, 21.75, 2.2, 1.72, .62), (0.18, 22.55, 2.12, 1.66, .55),
                (0.12, 23.3, 1.95, 1.52, .45), (-0.08, 23.98, 1.55, 1.2, .3), (-0.45, 24.4, .95, .72, .12),
                (-0.9, 24.5, .3, .25, 0.0)]


def hood_ranger(m):
    """A Ranger's deep cowl in green-brown camo, its edge pulled forward over the brow, a ragged
    capelet and the star of the Dunedain at the throat."""
    hood(m, RANGER_RINGS, CAMO, CAMODARK, None, star=True, lining=CAMODARK)


# ------------------------------------------------------------------ circlets and helms
def circlet(m, z=22.95, tag=FILIGREE, rx=1.6, ry=1.2, cx=.1, r=.075, n=28):
    """A circlet band round the brow (a flat ribbon of metal following the brow line)."""
    pts = ellipse(cx, rx, ry, z, n=n, lift=lambda t: .12 * math.cos(t) - .1)
    m.sweep(pts, [r * 1.6] * len(pts), tag, H, sides=6, squash=.35, up=[0, 0, 1])
    return pts


def circlet_rivendell(m):
    """The circlet of Rivendell: a blue-silver band, its brow piece a mithril leaf round a large
    crystal, fine leaf tendrils sweeping back over the temples."""
    circlet(m)
    c = (1.78, 0, 23.02)
    leaf(m, add(c, (0, 0, .18)), (0, 0, 1), (0, 1, 0), 1.25, .62, .1, MITHPLATE, H, rib=MITH)
    m.stud(add(c, (.08, 0, .05)), (1, 0, .15), .2, GEM, H, h=.16, sides=8)
    for s in (1, -1):
        pts = [(1.68, s * .3, 23.05), (1.4, s * .82, 23.3), (.9, s * 1.12, 23.55), (.3, s * 1.24, 23.7), (-.3, s * 1.2, 23.65)]
        m.sweep(pts, [.05, .045, .04, .03, .02], MITH, H, sides=5)
        for k, p in enumerate(pts[1:4]):
            leaf(m, add(p, (0, s * .06, .12)), norm((-1, s * .3, .7)), (0, s, 0), .48, .2, .05, MITHPLATE, H)
        m.stud((1.62, s * .62, 22.95), (1, s * .5, 0), .08, GEM, H, h=.07, sides=6)


RV_DOME = [(1.86, 1.4, 22.25), (1.95, 1.47, 22.4), (1.96, 1.48, 22.95), (1.88, 1.41, 23.5), (1.66, 1.24, 24.02),
           (1.25, .93, 24.42), (.66, .5, 24.68), (.04, .04, 24.76)]


def fin(m, lower, upper, thick, tag, bone=H, edge_tag=None):
    """A standing crest plate between two lines (convex quads, solid), its top edge rolled."""
    for a, b, ta, tb in zip(lower, lower[1:], upper, upper[1:]):
        m.slab([a, b, tb, ta], thick, (0, 1, 0), tag, bone, bevel=.02)
    if edge_tag is not None:
        edge(m, upper, thick * .6, edge_tag, bone, sides=5)


def helm_rivendell(m):
    """The winged helm of Rivendell: a bright blue-silver cap on a filigree band with a gold leaf
    crest from brow to nape, great swept wings of mithril feathers rising from the temples, and
    leaf-shaped cheek guards."""
    m.shell(HEAD, RV_DOME, MITH, H, sides=28, rim=lambda t: .3 * math.cos(t) - .05)
    pts = ellipse(.18, 1.98, 1.5, 22.3, n=28, lift=lambda t: .3 * math.cos(t) - .05)
    m.sweep(pts, [.13] * len(pts), FILIGREE, H, sides=6, squash=.5)
    path = [(.18 + .98 * r, 0, z + .0) for r, _, z in RV_DOME[2:-1]] + [(.18, 0, RV_DOME[-1][2])] + \
           [(.18 - .98 * r, 0, z) for r, _, z in RV_DOME[2:-1]][::-1]
    n = len(path)
    top = [add(p, mul(norm(sub(p, (.18, 0, 22.4))), .12 + .42 * math.sin(math.pi * i / (n - 1)))) for i, p in enumerate(path)]
    fin(m, path, top, .09, GOLD, edge_tag=GOLD)
    leaf(m, (2.14, 0, 22.75), (0, 0, 1), (0, 1, 0), 1.0, .55, .08, LEAFGOLD, H, rib=GOLD)
    m.stud((2.2, 0, 22.62), (1, 0, .1), .15, GEM, H, h=.12, sides=8)
    for s in (1, -1):
        base = (-.05, s * 1.5, 23.05)
        for k in range(6):
            a = math.radians(30 + 12 * k)
            L = 2.9 - .12 * k
            d = norm((-math.cos(a), s * .42, math.sin(a)))
            side = norm(cross(d, (0, s, 0)))
            b0 = add(base, (-.1 * k, s * .025 * k, -.05 * k))
            tip = add(b0, mul(d, L))
            w = .3
            m.slab([add(b0, mul(side, w * .5)), add(add(b0, mul(d, L * .55)), mul(side, w)), tip,
                    add(add(b0, mul(d, L * .55)), mul(side, -w)), add(b0, mul(side, -w * .5))], .07, (0, s, 0), FEATHER, H,
                   bevel=.02)
        m.stud((.0, s * 1.55, 23.0), (0, s, 0), .26, GOLD, H, h=.14, sides=8)
        m.stud((.05, s * 1.66, 23.0), (0, s, 0), .15, GEM, H, h=.12)
        leaf(m, (1.25, s * 1.44, 21.7), norm((.25, 0, -1)), norm((1, -s * .25, .1)), 1.7, .66, .08, MITHPLATE, H, rib=GOLD,
             out=(0, s, 0))


def circlet_mirkwood(m):
    """The antlered circlet of Mirkwood: a band of dark wood bound in bronze, two branching antlers
    rising back from the temples, red-gold autumn leaves at the brow."""
    circlet(m, z=22.85, tag=DARKWOOD, r=.09)
    for s in (1, -1):
        root = (.55, s * 1.1, 23.35)
        main = [root, (.35, s * 1.55, 24.2), (-.05, s * 1.9, 25.1), (-.55, s * 2.05, 25.9), (-1.0, s * 1.95, 26.5)]
        m.sweep(main, [.16, .13, .1, .07, .03], ANTLER, H, sides=6)
        for k, (i, d, L) in enumerate(((1, (.55, s * .5, .7), .9), (2, (.25, s * .25, .95), .85), (3, (-.2, s * .7, .5), .6))):
            p = main[i]
            tine = [p, add(p, mul(norm(d), L * .55)), add(p, mul(norm(d), L))]
            m.sweep(tine, [.09 - .01 * k, .06, .02], ANTLER, H, sides=5)
        m.tube(add(root, (0, 0, -.25)), add(root, (0, 0, .12)), .2, GOLD, H, sides=6)
    for k, (y, a) in enumerate(((0, 0), (.42, .6), (-.42, -.6))):
        leaf(m, (1.72 - .12 * abs(y), y, 23.15 + .1 * (k == 0)), norm((0, -math.sin(a) * .5, 1)), norm((0, math.cos(a), math.sin(a) * .3)),
             .9 if k == 0 else .7, .45, .07, AUTUMN, H, rib=GOLD)


NL_DOME = [(1.88, 1.42, 22.15), (1.98, 1.5, 22.3), (1.99, 1.5, 22.95), (1.9, 1.43, 23.65), (1.68, 1.26, 24.38),
           (1.3, .98, 25.05), (.86, .64, 25.58), (.42, .31, 25.95), (.04, .04, 26.15)]


def helm_noldor(m):
    """The tall helm of the Noldor: a fluted gold helm on a star-set enamel band, a tall gold
    crest rising from the brow and sweeping back to a long point, long leaf cheek guards."""
    rim = lambda t: .32 * math.cos(t) - .05
    m.shell(HEAD, NL_DOME, GOLDFLUTE, H, sides=28, rim=rim)
    m.shell(HEAD, [(r + .03, ry + .03, z) for r, ry, z in NL_DOME[1:3]], ENAMEL, H, sides=28, rim=rim)
    for z in (22.2, 22.95):
        pts = ellipse(.18, 2.02, 1.53, z, n=28, lift=rim)
        m.sweep(pts, [.08] * len(pts), GOLD, H, sides=6, squash=.6)
    path = [(.18 + .99 * r, 0, z + (rim(0) if k == 0 else 0)) for k, (r, _, z) in enumerate(NL_DOME[3:-1])] + [(.18, 0, 25.26)] + \
           [(.18 - .99 * r, 0, z) for r, _, z in NL_DOME[4:-1]][::-1]
    n = len(path)
    hgt = [.2 + 1.3 * math.sin(math.pi * (i / (n - 1)) ** .6) ** 1.2 for i in range(n)]
    top = [add(p, (-.75 * h, 0, .8 * h)) for p, h in zip(path, hgt)]
    fin(m, path, top, .1, GOLD, edge_tag=GOLD)
    m.stud((2.08, 0, 22.62), (1, 0, .1), .2, GEM, H, h=.14, sides=8)
    for s in (1, -1):
        leaf(m, (1.2, s * 1.55, 21.35), norm((.3, 0, -1)), norm((1, -s * .3, .1)), 2.1, .85, .1, GOLDFLUTE, H, rib=GOLD,
             out=(0, s, 0))
        m.stud((.2, s * 1.6, 22.7), (0, s, 0), .22, GEM, H, h=.12, sides=8)


# ------------------------------------------------------------------ cloaks and shoulders
def cloak_lorien(m, cloth=CLOTH, hem=CLOTHVINE, clasp=LEAFGOLD, collar=CLOTH, chain=GOLD, gem=GEM, lining=LINING):
    """The leaf-clasp cloak of Lorien: a long cloak in seven soft folds, its hem embroidered with a
    mallorn vine, pinned at the collarbones by two gold mallorn leaves joined by a fine chain."""
    G.cloak(m, cloth, hem, collar, lining=lining)
    for s in (1, -1):
        c = (1.0, s * 1.65, 19.75)
        leaf(m, c, norm((.2, s * .5, .85)), norm((0, -.86, .5)) if s > 0 else norm((0, .86, .5)), 1.0, .5, .1, clasp, SPINE, rib=chain,
             out=(1, 0, 0))
        m.sweep([(-.5, s * 2.6, 20.0), (.2, s * 2.25, 19.95), c], [.07] * 3, chain, SPINE, sides=5)
    m.sweep([(1.15, 1.6, 19.55), (1.45, .8, 19.15), (1.55, 0, 19.0), (1.45, -.8, 19.15), (1.15, -1.6, 19.55)], [.04] * 5,
            chain, SPINE, sides=4)
    if gem is not None:
        m.stud((1.62, 0, 19.0), (1, 0, -.1), .14, gem, SPINE, h=.1, sides=6)


def cloak_ranger(m):
    """A Ranger's cloak of the North: green-brown camo, the hem left ragged, a leather collar and
    the star of the Dunedain pinned at the left shoulder."""
    G.cloak(m, CAMO, CAMODARK, CAMODARK, lining=CAMODARK, rim=lambda t: -.35 * abs(math.sin(11 * t)) - .2 * abs(math.sin(5 * t + 1)))
    c = (1.05, 1.6, 19.7)
    m.stud(c, (1, .3, .25), .45, STAR, SPINE, h=.12, sides=16)
    for k in range(8):
        a = math.pi * k / 4
        u, v = norm((-.3, 1, 0)), (0, 0, 1)
        tip = add(add(c, mul(u, .8 * math.cos(a))), add(mul(v, .8 * math.sin(a)), (.12, 0, 0)))
        m.slab([add(add(c, mul(u, .12 * math.cos(a + 1.3))), mul(v, .12 * math.sin(a + 1.3))), tip,
                add(add(c, mul(u, .12 * math.cos(a - 1.3))), mul(v, .12 * math.sin(a - 1.3)))], .06, (1, .3, .2), MITH, SPINE,
               bevel=.01)
    m.sweep([(-.4, -2.6, 20.0), (.6, -2.0, 19.8), (1.2, -.3, 19.4), (1.05, 1.6, 19.7)], [.06] * 4, CAMODARK, SPINE, sides=5)


def _shoulder(s):
    """(origin, X, Y, Z) over the shoulder joint of side s (+1 left): Z out and up."""
    joint = (-0.6, s * 3.0, 18.4)
    Z = norm((0.05, s * .62, .79))
    X = norm(cross([0, s, 0], Z)) if s > 0 else norm(cross(Z, [0, 1, 0]))
    X = X if X[0] > 0 else mul(X, -1)
    Y = cross(Z, X)
    return joint, X, Y, Z


def pauldrons_mirkwood(m):
    """Mirkwood leaf-leather pauldrons: a domed leather cap over each shoulder, three overlapping
    leather leaves down the arm, edged and ribbed in bronze-gold."""
    region(m, "back")
    for s, bone in ((1, "BAT_UARML"), (-1, "BAT_UARMR")):
        f = _shoulder(s)
        o, X, Y, Z = f
        m.shell(f, [(1.6, 1.45, 0), (1.62, 1.47, .25), (1.42, 1.3, .7), (.95, .86, 1.05), (.05, .05, 1.18)], LEAFLEATHER, bone,
                sides=20)
        edge(m, [add(add(add(o, mul(X, 1.66 * math.cos(t))), mul(Y, 1.5 * math.sin(t))), mul(Z, .06))
                 for t in [2 * math.pi * i / 20 for i in range(21)]], .07, GOLD, bone)
        down = norm((0.05, s * .7, -.72))
        for k in range(3):
            c = add(add(o, mul(down, 1.0 + .75 * k)), mul(Z, .95 - .12 * k))
            c = add(c, mul(X, .35 * (k - 1)))
            leaf(m, c, down, X, 2.0 - .2 * k, 1.15 - .1 * k, .1, LEATHER, bone, rib=GOLD)
        m.stud(add(o, mul(Z, 1.17)), Z, .26, GOLD, bone, h=.12, sides=8)


# ------------------------------------------------------------------ shield, knives, bow
def shield_leaf(m):
    """The leaf shield of Lorien: a domed pointed oval in the hero's colour with a gold mallorn
    leaf, a rolled gold rim and midrib, a crystal boss, worn on the bow arm."""
    G.leaf_shield(m, SHIELDFACE, GOLD, BIRCHBACK, GOLD, GEM)


def _knife(m, hilt, d, side, flip):
    """A leaf-bladed long knife in its slate sheath, hilt up: gold leaf guard, wrapped grip."""
    bone = LOW
    up = mul(d, -1)
    m.tube(add(hilt, mul(up, -.1)), add(hilt, mul(up, 1.1)), .11, GRIP, bone, sides=6)
    m.stud(add(hilt, mul(up, 1.15)), up, .16, GOLD, bone, h=.18, sides=6)
    leaf(m, add(hilt, mul(d, .12)), side, cross(side, d) if flip else cross(d, side), .9, .3, .08, GOLD, bone)
    secs = []
    for t, w in ((.2, .26), (1.2, .34), (2.4, .32), (3.4, .2), (3.95, .04)):
        p = add(hilt, mul(d, t))
        secs.append([add(add(p, mul(side, w * math.cos(a))), mul(cross(d, side), .1 * math.sin(a))) for a in
                     [2 * math.pi * k / 6 for k in range(6)]])
    m.loft(secs, MITHDARK, bone)
    m.tube(add(hilt, mul(d, 3.45)), add(hilt, mul(d, 4.0)), .12, GOLD, bone, sides=5, r1=.02)


def knives_galadhrim(m):
    """Twin leaf-bladed long knives of the Galadhrim, sheathed crossed at the small of the back."""
    region(m, "back")
    for s in (1, -1):
        hilt = (-2.25, s * 1.85, 14.7)
        d = norm((-.15, -s * .62, -.78))
        side = norm(cross(d, (1, 0, 0)))
        _knife(m, hilt, d, side, s < 0)
        m.sweep([(-2.05, s * 1.2, 13.3), (-2.15, 0, 12.6), (-2.05, -s * 1.2, 11.9)], [.05] * 3, LEATHER, LOW, sides=4)


def bow_limbs(m, wood, wrap, tip_tag, string, collar, length=7.8, depth=3.1, recurve=.7, ornament=None):
    """A recurve bow in EA's bow frame: the grip at 0 (+x, away from the archer), the limbs
    curving back toward the string and recurving at the tips; a wrapped grip, gold collars, nocks
    and a straight string."""
    region(m, "bow")
    def x_of(z):
        f = abs(z) / length
        return .95 - depth * f ** 1.8 + recurve * max(0, f - .82) ** 2 / .0324
    zs = [length * (k / 10) for k in range(-10, 11)]
    path = [bowpt(x_of(z), 0, z) for z in zs]
    radii = [.24 - .13 * abs(z) / length for z in zs]
    m.sweep(path, radii, wood, BOW, sides=8, squash=.6, up=bowdir(0, 1, 0))
    m.sweep([bowpt(x_of(z) - .02, 0, z) for z in (-1.0, -.5, 0, .5, 1.0)], [.27] * 5, wrap, BOW, sides=8, squash=.75,
            up=bowdir(0, 1, 0))
    for z in (-1.15, 1.15):
        m.tube(bowpt(x_of(z), 0, z - .08), bowpt(x_of(z), 0, z + .08), .3, collar, BOW, sides=8)
    tips = [bowpt(x_of(z), 0, z) for z in (-length, length)]
    for t, z in zip(tips, (-length, length)):
        ball(m, t, .14, tip_tag, BOW, sides=6)
    m.tube(tips[0], tips[1], .025, string, BOW, sides=3)
    if ornament:
        ornament(m, x_of)
    return x_of


def bow_galadhrim(m):
    """The bow of the Galadhrim: a long recurve of pale birch inlaid with a gold vine, a wrapped
    grip between gold collars, gold leaf plates on both limbs and gold leaf-shaped nocks."""
    def orn(m, x_of):
        for z in (-3.6, 3.6):
            leaf(m, bowpt(x_of(z) + .2, 0, z), bowdir(0, 0, 1 if z > 0 else -1), bowdir(0, 1, 0), 1.3, .42, .07, LEAFGOLD, BOW,
                 out=bowdir(1, 0, 0))
        for z in (-7.8, 7.8):
            leaf(m, bowpt(x_of(z) + .1, 0, z * 1.02), bowdir(.4, 0, 1 if z > 0 else -1), bowdir(0, 1, 0), .8, .3, .06, GOLD, BOW,
                 out=bowdir(1, 0, 0))
    bow_limbs(m, BIRCH, GRIP, GOLD, STRING, GOLD, ornament=orn)
