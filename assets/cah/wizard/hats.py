"""The Wizards' parts: the Istari's hats (drawn on the Men's canonical head, assets/cah/men_cg/
helms.py, and seated on the wizards' taller head), the travelling cloaks, the rune-carved staff and
the lollipop. Hat tiles are the wizard sheet's (paint.py); the fun ones remap them.
"""
import math

from ..kit.geom import add, cross, mul, norm
from ..men_cg import body as B
from ..men_cg import fun as MF
from ..men_cg import helms as Hm
from ..men_cg import paint as MP
from . import paint as W

H = Hm.H
TAU = 2 * math.pi
ball = MF.ball


def brim(m, r_out, droop, tag, wave=0.0, waves=5, r_in=(1.52, 1.4), sides=36):
    """A hat's brim: a ring from the head to r_out, drooping `droop` at the edge, waved."""
    rows = [(r_in[0], r_in[1], .05), ((r_in[0] + r_out) / 2, (r_in[1] + r_out * .96) / 2, .02 - droop * .25),
            (r_out, r_out * .96, -droop)]
    return m.shell(Hm.HEAD, rows, tag, H, sides=sides, double=True,
                   bump=lambda t, k: wave * math.sin(waves * t) * (k == 2), rim=None)


def crown(m, path, radii, tag, squash=.94, sides=16):
    m.sweep(path, radii, tag, H, sides=sides, squash=squash, up=[0, 1, 0])


def hat_grey(m):
    """The Grey Pilgrim's hat: a tall pointed hat of grey felt, its crown bent back and crumpled,
    a wide drooping brim and a band in the hero's colour."""
    brim(m, 3.0, .28, W.GREYFELT, wave=.12, waves=3)
    path = [(0, 0, -.05), (-.05, 0, .9), (-.15, 0, 1.8), (-.38, 0, 2.6), (-.8, 0, 3.3), (-1.4, 0, 3.8), (-2.05, 0, 3.98),
            (-2.55, 0, 3.72)]
    crown(m, path, [1.62, 1.42, 1.15, .88, .62, .4, .2, .05], W.GREYFELT)
    m.shell(Hm.HEAD, [(1.6, 1.5, .05), (1.62, 1.52, .12), (1.56, 1.46, .5), (1.5, 1.4, .58)], W.BAND, H, sides=24, rim=None)


def hat_white(m):
    """The hat of the White Council: a tall straight cone of white felt on a narrow flat brim, a
    silver rune band and a white stone on the brow."""
    brim(m, 2.35, .08, W.WHITEFELT)
    path = [(0, 0, -.05), (-.03, 0, 1.2), (-.08, 0, 2.4), (-.15, 0, 3.5), (-.25, 0, 4.5), (-.32, 0, 5.1)]
    crown(m, path, [1.6, 1.3, .98, .64, .3, .04], W.WHITEFELT)
    m.shell(Hm.HEAD, [(1.6, 1.5, .05), (1.61, 1.51, .1), (1.52, 1.42, .55), (1.46, 1.36, .62)], W.RUNES, H, sides=24, rim=None)
    m.stud((1.56, 0, .33), (1, 0, .05), .2, W.WHITE, H, h=.14, sides=8)
    Hm.edge(m, Hm.ring(2.36, 2.27, .05, n=32, rim=None), .05, W.SILVER)


def hat_brown(m):
    """Radagast's hat: a battered brown hat with a floppy brim, a dented crown with feathers in
    the band, and a bird's nest on top with three blue eggs and a little blue bird."""
    brim(m, 3.1, .55, W.BROWNFELT, wave=.3, waves=4)
    m.shell(Hm.HEAD, [(1.62, 1.5, .0), (1.6, 1.48, .5), (1.4, 1.3, 1.05), (1.1, 1.0, 1.5), (.85, .78, 1.8),
                      (.04, .04, 1.62)], W.BROWNFELT, H, sides=20, bump=lambda t, k: .1 * math.sin(3 * t + k * 1.3), rim=None)
    m.shell(Hm.HEAD, [(1.64, 1.52, .05), (1.68, 1.56, .12), (1.66, 1.54, .45), (1.62, 1.5, .52)], W.LEATHER, H, sides=20, rim=None)
    for k, a in enumerate((2.6, 2.9)):              # feathers tucked in the band
        b = (1.62 * math.cos(a), 1.5 * math.sin(a), .3)
        d = norm((math.cos(a) * .3 - .5, math.sin(a) * .3, 1.0))
        side = norm(cross(d, (math.cos(a), math.sin(a), 0)))
        tip = add(b, mul(d, 1.7 - .3 * k))
        Hm.plate(m, [add(b, mul(side, .08)), add(add(b, mul(d, .9)), mul(side, .22)), tip, add(add(b, mul(d, .9)), mul(side, -.18)),
                     add(b, mul(side, -.08))], (math.cos(a), math.sin(a), 0), W.FEATHER, thick=.04)
    nest = [(.75 * math.cos(t) - .15, .7 * math.sin(t), 1.78) for t in [TAU * i / 14 for i in range(15)]]
    m.sweep(nest, [.32] * 15, W.NEST, H, sides=8)
    m.shell(((-.15, 0, 1.58), [1, 0, 0], [0, 1, 0], [0, 0, 1]), [(.04, .04, 0), (.7, .65, .2)], W.NEST, H, sides=12)
    for k in range(3):
        a = TAU * k / 3 + .4
        ball(m, (-.15 + .28 * math.cos(a), .28 * math.sin(a), 1.88), .2, W.EGG, sides=8)
    b0 = (.25, -.6, 2.03)                            # the bird, perched on the nest's rim facing front
    ball(m, b0, .32, W.BIRD, sides=10)
    ball(m, add(b0, (.28, 0, .3)), .2, W.BIRD, sides=8)
    m.sweep([add(b0, (.45, 0, .3)), add(b0, (.62, 0, .27))], [.07, .01], W.BEAK, H, sides=4)
    for s in (1, -1):
        ball(m, add(b0, (.38, s * .12, .38)), .045, W.BLACK, sides=4)
    Hm.plate(m, [add(b0, (-.2, -.1, 0)), add(b0, (-.65, -.12, .25)), add(b0, (-.7, 0, .3)), add(b0, (-.2, .1, 0))], (0, 0, 1),
             W.BIRD, thick=.04)


HOOD = [(1.5, 1.52, -1.6), (1.68, 1.64, -.9), (1.84, 1.74, -.1), (1.86, 1.72, .7), (1.72, 1.58, 1.4), (1.4, 1.28, 1.95),
        (.95, .86, 2.3), (.3, .28, 2.5)]


def hat_blue(m):
    """The Blue Wizards' cowl: a deep blue hood rising to a tall point bent back, a silver circlet
    under it with a star-sapphire on the brow, the hood's edge hemmed in a band of the Paint colour."""
    rows = m.shell(Hm.HEAD, HOOD, W.BLUEFELT, H, sides=26, arc=(1.0, TAU - 1.0), double=True, rim=None,
                   bump=lambda t, k: .04 * math.sin(7 * t) * (k < 3))
    Hm.edge(m, [r[0] for r in rows] + [r[-1] for r in rows][::-1], .08, W.BAND)
    path = [(-.2, 0, 2.0), (-.45, 0, 2.8), (-.8, 0, 3.6), (-1.35, 0, 4.25), (-1.95, 0, 4.55)]
    crown(m, path, [1.05, .78, .5, .26, .04], W.BLUEFELT, squash=.9, sides=12)
    m.shell(Hm.HEAD, [(1.62, 1.5, .0), (1.64, 1.52, .06), (1.64, 1.52, .26), (1.62, 1.5, .32)], W.SILVER, H, sides=24, rim=None)
    for k in range(4):
        a = math.pi / 4 + math.pi / 2 * k
        Hm.plate(m, [(1.68, 0, .45), (1.68, .28 * math.cos(a - .25), .45 + .28 * math.sin(a - .25)),
                     (1.68, .38 * math.cos(a), .45 + .38 * math.sin(a)), (1.68, .28 * math.cos(a + .25), .45 + .28 * math.sin(a + .25))],
                 (1, 0, 0), W.SILVER, thick=.05)
    m.stud((1.7, 0, .45), (1, 0, 0), .15, W.GEM, H, h=.1)


# ------------------------------------------------------------------ cloaks
def cloak_travel(m, A):
    """A travelling cloak in the hero's colour, its hood thrown back on the shoulders, bound at the
    hem in leather and fastened with a brass clasp and a crystal."""
    B.cloak(m, A, W.CLOAK, W.LEATHER, W.CLOAK, folds=6, clasp=W.BRASS, clasp_gem=W.GEM, hem_r=.1)


def cloak_stars(m, A):
    """The Blue Wizards' mantle: a deep blue cloak with silver stars along the hem, a silver
    collar and clasp."""
    B.cloak(m, A, W.HEMSTARS, W.SILVER, W.SILVER, folds=6, clasp=W.SILVER, clasp_gem=W.GEM, hem_r=.1)


def cloak_glitter(m, A):
    """A cloak of night-blue sewn with gold stars, its hem and collar trimmed in rainbow glitter."""
    B.cloak(m, A, MP.F_SPANGLE, MP.F_GLITTER, MP.F_GLITTER, folds=6, clasp=MP.F_GOLD, clasp_gem=MP.F_PINKGEM, hem_r=.22)


# ------------------------------------------------------------------ staffs
def staff_frame(A):
    c, a, e1 = A["staff"]
    a = norm(a)
    e2 = cross(a, e1)
    return c, a, norm(e1), norm(e2)


def staff_rune(m, A):
    """A rune-carved staff: a gnarled shaft of dark wood, a leather-wrapped grip, a silver band of
    runes under a head of four carved prongs cradling a crystal (it glows the hero's colour)."""
    c, a, e1, e2 = staff_frame(A)
    lo, hi, grip = A["staff_span"]
    P = lambda t, u=0.0, v=0.0: add(add(add(c, mul(a, t)), mul(e1, u)), mul(e2, v))
    n = 12
    path = [P(lo + (hi - 1.6 - lo) * i / n, .08 * math.sin(i * 1.9), .08 * math.cos(i * 2.7)) for i in range(n + 1)]
    m.sweep(path, [.16 + .03 * math.sin(i * 2.3) + .05 * i / n for i in range(n + 1)], W.WOOD, "HAND", sides=8)
    m.tube(P(lo - .1), P(lo + .5), .2, W.SILVER, "HAND", sides=8, r1=.18)
    m.tube(P(grip - .9), P(grip + .9), .25, W.WRAP, "HAND", sides=8)
    m.tube(P(hi - 2.9), P(hi - 1.7), .3, W.RUNES, "HAND", sides=10)
    for t in (hi - 2.95, hi - 1.65):
        m.tube(P(t - .05), P(t + .05), .34, W.SILVER, "HAND", sides=10)
    for k in range(4):                                  # carved prongs curling round the crystal
        ang = TAU * k / 4 + .4
        u, v = math.cos(ang), math.sin(ang)
        pr = [P(hi - 1.7, .22 * u, .22 * v), P(hi - 1.0, .55 * u, .55 * v), P(hi - .2, .62 * u, .62 * v),
              P(hi + .4, .35 * u, .35 * v), P(hi + .55, .1 * u, .1 * v)]
        m.sweep(pr, [.15, .13, .11, .08, .04], W.WOOD, "HAND", sides=6)
    ball(m, P(hi - .35), .45, W.GEM, "HAND", sides=10)


def staff_lolly(m, A):
    """A giant rainbow-swirl lollipop on a striped stick, with a pink bow (it fights as a staff)."""
    c, a, e1, e2 = staff_frame(A)
    lo, hi, grip = A["staff_span"]
    P = lambda t, u=0.0, v=0.0: add(add(add(c, mul(a, t)), mul(e1, u)), mul(e2, v))
    m.tube(P(lo + 1.5), P(hi - 2.0), .16, MP.F_WHITE, "HAND", sides=8)
    o = P(hi - .2)
    R = 2.1
    f = (o, e2, a, e1)
    m.shell(f, [(R, R, -.2), (R * 1.01, R * 1.01, 0), (R, R, .2), (R * .6, R * .6, .3), (.02, .02, .33)], MP.F_LOLLY, "HAND",
            sides=28, planar=R)
    m.shell((o, e2, mul(a, -1), mul(e1, -1)), [(R, R, .2), (R * .6, R * .6, .3), (.02, .02, .33)], MP.F_LOLLY, "HAND", sides=28,
            planar=R)
    for s in (1, -1):                                   # a pink bow where the stick meets the sweet
        b = P(hi - 2.3)
        Hm.plate(m, [b, add(b, add(mul(e2, s * .9), mul(a, .45))), add(b, add(mul(e2, s * 1.0), mul(a, -.35)))], e1, MP.F_PINK,
                 bone="HAND", thick=.08)
        m.sweep([b, add(b, add(mul(e2, s * .35), mul(a, -.9)))], [.08, .04], MP.F_PINK, "HAND", sides=4)
    ball(m, P(hi - 2.3), .16, MP.F_PINKGEM, "HAND", sides=8)
