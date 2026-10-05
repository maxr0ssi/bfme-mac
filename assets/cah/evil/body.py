"""The Evil classes' shoulder-row parts: pauldrons in each faction's language, war cloaks, and the
fun ones that live in this row because the menu has no cape or skirt row (a rainbow war-banner
cape, a tutu). Each is drawn on the model's measured shoulders, back or hips (shapes.py).
"""
import math

from ..kit.geom import add, mul, norm
from .helms import (A_IRON, BONE, BRASS, BRASSORN, CLOTH, CRIMSON, EMBER, ENAMEL, FUR, GEM, GOLD, HAND, I_IRON, ICE, IRON,
                    LAMELLAR, PLATE, RED, SILVER, STEEL, TINE, WRAP)
from .shapes import T, cloak, edge, lame, of, pauldron, shoulder_frame, skirt

SIDES = ((1, "L"), (-1, "R"))


def _p(f, a, b, c):
    o, X, Y, Z = f[:4]
    r = f[4]
    return add(add(add(o, mul(X, a * r)), mul(Y, b * r)), mul(Z, c * r))


def _spike(m, f, bone, a, b, c, d, length, r0, tag, tip, hook=.25):
    """A hooked spike from shoulder-frame point (a, b, c) along frame direction d, in radii."""
    o, X, Y, Z, r = f
    dd = norm(add(add(mul(X, d[0]), mul(Y, d[1])), mul(Z, d[2])))
    base = _p(f, a, b, c)
    pts = [add(add(base, mul(dd, length * r * i / 5)), mul(Z, -hook * r * (i / 5) ** 2)) for i in range(6)]
    radii = [r0 * r * (1 - i / 5) ** .8 + .01 * r for i in range(6)]
    m.sweep(pts[:4], radii[:4], tag, bone, sides=5)
    m.sweep(pts[3:], radii[3:], tip, bone, sides=5)


def pauldrons_mordor(m):
    """Mordor war-plates: three overlapping black-iron plates over each shoulder, steel-edged, a row
    of hooked steel-tipped spikes along the top and an ember stud."""
    A = of(m)
    for s, _ in SIDES:
        bone = A.uarm[s]
        f = pauldron(m, A, s, PLATE, STEEL, [(1.25, 1.1, 0), (1.27, 1.12, .25), (1.1, .96, .7), (.7, .62, 1.0), (.05, .05, 1.1)],
                     sides=12)[:5]
        for k in range(3):
            _spike(m, f, bone, -.5 + .5 * k, 0, .8 + .2 * (k == 1), (.15 * (k - 1), .2, 1), 1.0 + .3 * (k == 1), .16, IRON, STEEL)
        m.stud(_p(f, .0, .55, .78), f[3], .14 * f[4], EMBER, bone, h=.1 * f[4], sides=6)
        for k in range(2):
            lame(m, A, s, k, WRAP, STEEL)


def pauldrons_goblin(m):
    """Goblin bone-plates: crimson-painted iron plates chipped to the metal, a small beast skull
    lashed on each, and a fan of three bone spikes behind it."""
    A = of(m)
    for s, _ in SIDES:
        bone = A.uarm[s]
        f = pauldron(m, A, s, CRIMSON, IRON, [(1.2, 1.05, 0), (1.22, 1.07, .25), (1.05, .92, .66), (.62, .55, .95), (.05, .05, 1.02)],
                     sides=12)[:5]
        o, X, Y, Z, r = f
        c = _p(f, .15, .2, .95)
        secs = []
        for x, hw, h in ((-.45, .28, .3), (-.15, .36, .38), (.15, .34, .34), (.45, .22, .22), (.65, .14, .14)):
            q = add(c, mul(X, x * r))
            secs.append([add(add(q, mul(Y, hw * r * math.cos(a))), mul(Z, h * r * (.6 + .4 * math.sin(a)) * (1 if math.sin(a) > 0 else .4)))
                         for a in [2 * math.pi * i / 8 for i in range(8)]])
        m.loft(secs, BONE, bone)
        for side in (1, -1):
            m.stud(add(add(c, mul(X, .05 * r)), add(mul(Y, side * .22 * r), mul(Z, .28 * r))), add(X, mul(Z, .5)), .08 * r, WRAP, bone,
                   h=.02 * r, sides=4)
        for k in range(3):
            _spike(m, f, bone, -.5, -.3 + .3 * k, .7, (-.5, .25 * (k - 1), 1), 1.1, .12, BONE, BONE, hook=.1)


def pauldrons_isengard(m):
    """Uruk-hai shoulder plates: a broad black-iron plate edged in silver with the White Hand
    stamped on a boss, two silver-edged lames below."""
    A = of(m)
    for s, _ in SIDES:
        bone = A.uarm[s]
        f = pauldron(m, A, s, I_IRON, SILVER, [(1.3, 1.15, 0), (1.32, 1.17, .22), (1.15, 1.0, .62), (.75, .66, .92), (.05, .05, 1.0)],
                     sides=16)[:5]
        o, X, Y, Z, r = f
        c = _p(f, 0, 0, .98)
        w = .42 * r
        m.slab([add(add(c, mul(X, -w)), mul(Y, -w)), add(add(c, mul(X, w)), mul(Y, -w)), add(add(c, mul(X, w)), mul(Y, w)),
                add(add(c, mul(X, -w)), mul(Y, w))], .08 * r, Z, HAND, bone, bevel=.02 * r)
        for k in range(2):
            lame(m, A, s, k, WRAP, SILVER)


def pauldrons_angmar(m):
    """Angmar frost-plates: blue iron caps with a rime rim, three tines rising and curving out,
    their tips frozen white, and an enamelled lame below."""
    A = of(m)
    for s, _ in SIDES:
        bone = A.uarm[s]
        f = pauldron(m, A, s, A_IRON, ICE, [(1.2, 1.05, 0), (1.22, 1.07, .25), (1.05, .92, .66), (.62, .55, .96), (.05, .05, 1.04)],
                     sides=14)[:5]
        for k in range(3):
            o, X, Y, Z, r = f
            base = _p(f, -.45 + .45 * k, .1, .85)
            d = norm(add(add(mul(X, .1 * (k - 1)), mul(Y, .45)), Z))
            L = (1.9 + .7 * (k == 1)) * r
            pts = [add(add(base, mul(d, L * i / 6)), mul(Y, .35 * r * (i / 6) ** 2)) for i in range(7)]
            m.sweep(pts, [.15 * r * (1 - i / 6) ** .9 + .01 * r for i in range(7)], TINE, bone, sides=5)
        lame(m, A, s, 0, ENAMEL, ICE)                       # an enamelled lame (Paint)
        m.stud(_p(f, .55, .3, .55), f[3], .16 * f[4], GEM, bone, h=.1 * f[4], sides=6)


def pauldrons_harad(m):
    """Haradrim shoulder guards: an engraved brass disc over each shoulder, a sash (colour G)
    from the left shoulder across the chest with gold tassels."""
    A = of(m)
    for s, _ in SIDES:
        bone = A.uarm[s]
        f = pauldron(m, A, s, BRASSORN, BRASS, [(1.15, 1.05, 0), (1.18, 1.07, .2), (1.0, .9, .55), (.6, .55, .78), (.05, .05, .85)],
                     sides=16)[:5]
        m.stud(_p(f, 0, 0, .82), f[3], .22 * f[4], RED, bone, h=.12 * f[4], sides=8)
        lame(m, A, s, 0, BRASS, None)
    b = sorted(A.bands, key=lambda q: q["z"])
    top, low = b[-1], b[len(b) // 3]
    sash = []
    for i in range(9):
        f = i / 8
        z = top["z"] + (low["z"] - top["z"]) * f
        q = min(b, key=lambda band: abs(band["z"] - z))
        y = A.shoulder[1]["joint"][1] * .8 * (1 - 2 * f)
        sash.append([q["front"] + .008 * A.height, y, z])
    m.sweep(sash, [.025 * A.height] * 9, CLOTH, A.spine, sides=6, squash=.25, up=[1, 0, 0])
    for k in range(3):
        p = sash[-1]
        m.tube(add(p, (0, .01 * A.height * (k - 1), 0)), add(p, (.005 * A.height, .012 * A.height * (k - 1), -.06 * A.height)),
               .008 * A.height, GOLD, A.spine, sides=4, r1=.004 * A.height)


def pauldrons_easterling(m):
    """Easterling lamellar shoulders: three tiers of black-lacquered lamellae laced in gold, each
    tier edged in gold, falling over the upper arm."""
    A = of(m)
    for s, _ in SIDES:
        bone = A.uarm[s]
        o, X, Y, Z, r = shoulder_frame(A, s)
        for k in range(3):
            lift = .55 - .45 * k
            rr = 1.05 + .18 * k
            rows = m.shell((add(o, mul(Z, lift * r)), X, Y, Z), [(rr * r, rr * .9 * r, 0), (rr * .85 * r, rr * .76 * r, .38 * r)],
                           LAMELLAR, bone, sides=14, double=True,
                           arc=(-math.pi * .95 if s > 0 else -math.pi * .05, math.pi * .05 if s > 0 else math.pi * .95))
            edge(m, rows[0], .05 * r, GOLD, bone, sides=4)
        m.stud(add(o, mul(Z, .95 * r)), Z, .2 * r, GOLD, bone, h=.12 * r, sides=8)
        m.stud(add(o, mul(Z, 1.07 * r)), Z, .1 * r, RED, bone, h=.08 * r, sides=6)


def cloak_mordor(m):
    """Mordor war cloak: a heavy cloak (colour G) with a ragged, burnt hem, a fur collar and
    black-iron shoulder clasps, each set with a hooked spike."""
    A = of(m)
    cloak(m, A, CLOTH, None, FUR, folds=6, tatter=.035, arc=1.15)
    for s, _ in SIDES:
        bone = A.uarm[s]
        f = pauldron(m, A, s, IRON, STEEL, [(.95, .85, 0), (.97, .87, .22), (.8, .7, .6), (.45, .4, .85), (.05, .05, .92)],
                     sides=10)[:5]
        _spike(m, f, bone, 0, .1, .8, (0, .35, 1), 1.0, .14, IRON, STEEL)


def cape_banner(m):
    """A rainbow war banner worn as a cape: rainbow stripes in seven folds, a swallow-tailed hem,
    the banner's crossbar across the shoulders with gold finials and gold tassels."""
    A = of(m)
    rows = cloak(m, A, 5, 28, 28, folds=7, arc=1.05, collar=False)
    top = rows[-1]
    H = A.height
    bar = [add(top[0], (0, -.04 * H, .01 * H)), add(top[len(top) // 2], (-.01 * H, 0, .015 * H)), add(top[-1], (0, .04 * H, .01 * H))]
    bar = [bar[0]] + [[bar[0][k] + (bar[2][k] - bar[0][k]) * i / 8 + (bar[1][k] - (bar[0][k] + bar[2][k]) / 2) *
                       math.sin(math.pi * i / 8) for k in range(3)] for i in range(1, 8)] + [bar[2]]
    m.sweep(bar, [.012 * H] * len(bar), 27, A.spine, sides=6)
    for e in (bar[0], bar[-1]):
        m.stud(e, (0, 1 if e[1] > 0 else -1, 0), .022 * H, 0, A.spine, h=.03 * H, sides=6)
    for col in (0, len(rows[0]) // 2, -1):
        p = rows[0][col]
        m.tube(p, add(p, (0, 0, -.05 * H)), .01 * H, 28, A.spine, sides=5, r1=.004 * H)


def tutu(m):
    """A ballet tutu: a fitted satin bodice band round the hips and two layers of stiff, ruffled
    pink tulle flaring out, with a satin bow at the back."""
    A = of(m)
    skirt(m, A, 4, [(1.12, .03), (1.15, -.01)], sides=28, double=False)
    skirt(m, A, 15, [(1.15, -.002), (1.75, -.012), (2.35, -.02)], sides=36, ruffle=.1)       # a pancake of tulle
    skirt(m, A, 15, [(1.12, -.016), (1.7, -.03), (2.15, -.045)], sides=32, ruffle=.12)
    skirt(m, A, 15, [(1.08, -.03), (1.5, -.05), (1.8, -.07)], sides=28, ruffle=.14)
    h = A.hips
    back = [h["c"][0] - h["rx"] * 1.2, 0.0, h["c"][2] + .01 * A.height]
    for s in (1, -1):
        m.sweep([back, add(back, (-.02 * A.height, s * .05 * A.height, .02 * A.height)),
                 add(back, (-.01 * A.height, s * .07 * A.height, -.015 * A.height)), back],
                [.012 * A.height, .02 * A.height, .02 * A.height, .012 * A.height], 4, A.pelvis, sides=6, squash=.4)
    m.stud(back, (-1, 0, 0), .018 * A.height, 4, A.pelvis, h=.015 * A.height, sides=6)


__all__ = ["pauldrons_mordor", "pauldrons_goblin", "pauldrons_isengard", "pauldrons_angmar", "pauldrons_harad", "pauldrons_easterling",
           "cloak_mordor", "cape_banner", "tutu", "T", "WRAP", "ICE"]
