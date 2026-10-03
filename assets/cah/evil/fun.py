"""The Evil classes' fun helmets: clearly silly and well made, readable at the RTS camera. Most
are fixed colours (pink stays pink); the party hat and the top hat's band take the hero's colours.

Drawn on the unit skull guide like the serious ones (shapes.py), from the fun sheet; the pink
spiked helm is the Helm of the Dark Tower redrawn from the serious sheet's hot-pink tiles.
"""
import math

from ..kit.geom import add, mul
from . import helms as S
from .shapes import T, ball, dome, edge, leaf, of, ring

(F_GOLD, F_FELT, F_BAND, F_GLASS, F_PINK, F_RAINBOW, F_PARTY, F_POMPOM, F_RUBBER, F_RED, F_ORANGE, F_BLACK, F_WHITE,
 F_LOLLY, F_STICK, F_TULLE, F_PETAL_W, F_PETAL_Y, F_PETAL_P, F_PETAL_B, F_LEAF, F_TIN, F_TINRIM, F_SIGN, F_PLANK,
 F_PINKMETAL, F_PINKTIP, F_POLE, F_TASSEL, F_STEEL, F_IRON, F_LILAC) = range(32)

PINK_SPIKED = {S.IRON: S.HOTPINK, S.PLATE: S.HOTPINK, S.STEEL: S.PINKTIP, S.CLOTH: S.PINKTIP, S.EYE: S.EYE}


def hat_party(m):
    """A party hat: a tall striped cone (the hero's colours) on an elastic, a white pompom."""
    A = of(m)
    s, H = A.head["s"], A.head_bone
    dome(m, A, [(.72, .72, .55), (.74, .74, .62), (.38, .38, 1.55), (.03, .03, 2.55)], F_PARTY, sides=20, rim=None)
    edge(m, ring(A, .75, .56, n=20, rim=None), .04 * s, F_GOLD, H)
    ball(m, A.hp(0, 0, 2.62), .26 * s, F_POMPOM, H)
    for side in (1, -1):
        m.sweep([list(A.hp(.1, side * .72, .58)), list(A.hp(.45, side * 1.05, -.2)), list(A.hp(.8, side * .85, -1.05))],
                [.02 * s] * 3, F_BLACK, H, sides=4)


def hat_top(m):
    """A top hat and monocle: a tall black felt crown with a silk band (colour G), a curled brim,
    and a gold-rimmed monocle in the right eye on a fine gold chain."""
    A = of(m)
    s, H = A.head["s"], A.head_bone
    dome(m, A, [(1.02, .16), (1.0, .3), (.98, 1.2), (1.03, 1.85), (1.0, 1.9), (.02, 1.92)], F_FELT, sides=24, rim=None)
    dome(m, A, [(.995, .3), (1.0, .3), (1.01, .62), (1.005, .62)], F_BAND, sides=24, rim=None)
    brim = dome(m, A, [(1.0, .18), (1.45, .16), (1.62, .26)], F_FELT, sides=24, rim=lambda t: .12 * math.sin(t) ** 2,
                double=True)
    edge(m, brim[-1], .05 * s, F_FELT, H)
    eye = A.hp(1.06, -.42, -.42)
    o = [eye[0] + .05 * s, eye[1], eye[2]]
    X, Y, Z = [0, 1, 0], [0, 0, 1], [1, 0, 0]
    ring_pts = [add(o, add(mul(X, .3 * s * math.cos(a)), mul(Y, .3 * s * math.sin(a)))) for a in [T * i / 16 for i in range(17)]]
    m.sweep(ring_pts, [.045 * s] * 17, F_GOLD, H, sides=5)
    m.shell((o, X, Y, Z), [(.28 * s, .28 * s, 0), (.2 * s, .2 * s, .03 * s), (.01 * s, .01 * s, .04 * s)], F_GLASS, H, sides=12)
    chain = [ring_pts[12], list(A.hp(1.0, -.75, -.9)), list(A.hp(.7, -1.0, -1.2)), list(A.hp(.3, -1.05, -.85))]
    m.sweep(chain, [.018 * s] * 4, F_GOLD, H, sides=4)


def _flower(m, A, c, n_out, size, petal, heart):
    s, H = A.head["s"], A.head_bone
    up = [n_out[0] * .3, n_out[1] * .3, 1.0]
    for k in range(5):
        a = T * k / 5
        d = [math.cos(a), math.sin(a), 0]
        tip = add(c, mul(d, size * s))
        l = add(c, mul([math.cos(a + .5), math.sin(a + .5), 0], size * .5 * s))
        r = add(c, mul([math.cos(a - .5), math.sin(a - .5), 0], size * .5 * s))
        leaf(m, [c, r, add(tip, (0, 0, .05 * s)), l], petal, H)
    m.stud(list(add(c, (0, 0, .03 * s))), up, size * .38 * s, heart, H, h=size * .3 * s, sides=6)


def flower_crown(m):
    """A crown of flowers: a woven green wreath of leaves round the brow set with daisies and
    pink, blue and yellow blossoms, two ribbons trailing down the back."""
    A = of(m)
    s, H = A.head["s"], A.head_bone
    path = ring(A, 1.08, .25, n=20, rim=lambda t: .15 * math.cos(t))
    m.sweep([list(p) for p in path], [.11 * s] * len(path), F_LEAF, H, sides=6)
    for k in range(14):                                      # leaves
        t = T * k / 14 + .2
        b = A.hp(1.12 * math.cos(t), 1.12 * math.sin(t), .25 + .15 * math.cos(t))
        tip = A.hp(1.35 * math.cos(t + .15), 1.35 * math.sin(t + .15), .38 + .15 * math.cos(t))
        side = A.hp(1.2 * math.cos(t + .2), 1.2 * math.sin(t + .2), .2 + .15 * math.cos(t))
        leaf(m, [b, side, tip], F_LEAF, H)
    petals = [F_PETAL_W, F_PETAL_P, F_PETAL_B, F_PETAL_Y, F_PETAL_W, F_PETAL_P, F_LILAC, F_PETAL_W]
    for k, petal in enumerate(petals):
        t = (k - 3.5) * .55
        c = A.hp(1.14 * math.cos(t), 1.14 * math.sin(t), .38 + .15 * math.cos(t))
        _flower(m, A, c, (math.cos(t), math.sin(t)), .3 if k % 2 == 0 else .24, petal,
                F_PETAL_Y if petal != F_PETAL_Y else F_ORANGE)
    for side in (1, -1):
        m.sweep([list(A.hp(-1.1, side * .2, .2)), list(A.hp(-1.35, side * .35, -.4)), list(A.hp(-1.4, side * .3, -1.1)),
                 list(A.hp(-1.5, side * .45, -1.6))], [.05 * s] * 4, F_PINK, H, sides=4, squash=.3)


def bucket(m):
    """A galvanised tin bucket worn upside down: pressed ridges, a rolled rim over the brow, a dent,
    the wire handle hanging under the chin on its two lugs."""
    A = of(m)
    s, H = A.head["s"], A.head_bone
    dome(m, A, [(1.22, -.45), (1.24, -.38), (1.18, .3), (1.1, 1.05), (1.08, 1.4), (.02, 1.42)], F_TIN, sides=22,
         rim=lambda t: .08 * math.cos(t), bump=lambda t, k: -.09 * math.exp(-((t - 2.2) ** 2) * 5) * (k in (2, 3)))
    edge(m, ring(A, 1.25, -.43, n=22, rim=lambda t: .08 * math.cos(t)), .07 * s, F_TINRIM, H)
    for z in (.1, .75):
        edge(m, ring(A, 1.16 - .1 * z, z, n=22, rim=None), .035 * s, F_TINRIM, H, sides=4)
    for side in (1, -1):
        m.stud(list(A.hp(0, side * 1.22, -.15)), (0, side, 0), .12 * s, F_TINRIM, H, h=.06 * s)
    handle = [A.hp(0, 1.25, -.15)] + [A.hp(.55 * math.sin(a) + .2, 1.2 * math.cos(a), -.15 - .95 * math.sin(a))
                                      for a in [math.pi * i / 10 for i in range(1, 10)]] + [A.hp(0, -1.25, -.15)]
    m.sweep([list(p) for p in handle], [.035 * s] * len(handle), F_STEEL, H, sides=4)


PINK = PINK_SPIKED
__all__ = ["hat_party", "hat_top", "flower_crown", "bucket", "PINK_SPIKED", "PINK", "F_TULLE", "F_LOLLY", "F_STICK",
           "F_SIGN", "F_PLANK", "F_PINKMETAL", "F_PINKTIP", "F_RAINBOW", "F_RUBBER", "F_RED", "F_WHITE", "F_POLE",
           "F_TASSEL", "F_IRON"]
