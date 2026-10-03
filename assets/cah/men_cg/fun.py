"""The Men of the West's fun choices (the Wizards reuse the hats): clearly silly and well made,
readable from the RTS camera, mostly fixed colours (a pink cape stays pink). Hats are drawn on the
canonical head (helms.py), body pieces from the subclass's anatomy (body.py), on the fun sheet.
"""
import math

from ..kit.geom import add, cross, mul, norm
from . import body as B
from . import helms as Hm
from . import paint as T

H = Hm.H
TAU = 2 * math.pi


def ball(m, c, r, tag, bone=H, sides=10):
    prof = [(r * math.sin(a), r * math.sin(a), -r * math.cos(a)) for a in [math.pi * k / 6 for k in range(1, 6)]]
    m.shell((list(c), [1, 0, 0], [0, 1, 0], [0, 0, 1]), [(.001, .001, -r)] + prof + [(.001, .001, r)], tag, bone, sides=sides,
            keep=sides)


# ------------------------------------------------------------------ hats
def crown_cheese(m):
    """A crown of cheese: a ring of holey cheddar wedges standing round the head on a waxed rind
    band, with a cocktail-stick olive on top."""
    rx, ry = 1.66, 1.52
    n = 8
    band = [(rx, ry, -.02), (rx + .03, ry + .03, .08), (rx + .03, ry + .03, .4), (rx, ry, .46)]
    m.shell(Hm.HEAD, band, T.F_RIND, H, sides=32, rim=Hm.brow)
    for k in range(n):                                  # wedges: triangular prisms, points up, holes on the faces
        t = TAU * k / n
        c, s = math.cos(t), math.sin(t)
        tx, ty = -s, c
        P = lambda r, w, z: (r * rx * c + w * tx, r * ry * s + w * ty, z + Hm.brow(t))
        hgt = 1.1 if k == 0 else .85
        m.slab([P(1.0, -.6, .4), P(1.0, .6, .4), P(.96, 0, .4 + hgt)], .32, (c, s, .15), T.F_CHEESE, H, bevel=.05)
    m.tube((0, 0, 1.6), (0, 0, 2.7), .04, T.F_OAK, H, sides=4)
    ball(m, (0, 0, 2.75), .22, T.F_LEAF, sides=8)


def umbrella(m):
    """A tiny umbrella hat: a red cap with a little stem, a red and white canopy of eight gores
    tilted at a jaunty angle, gold tips and a gold tassel."""
    m.shell(Hm.HEAD, [(1.62, 1.48, .25), (1.6, 1.46, .7), (1.4, 1.28, 1.3), (1.0, .92, 1.75), (.5, .46, 2.0), (.04, .04, 2.06)],
            T.F_CANOPY, H, sides=24, rim=Hm.brow)
    Hm.edge(m, Hm.ring(1.64, 1.5, .25, n=24), .07, T.F_GOLD)
    tilt = math.radians(16)
    up = (math.sin(tilt) * .5, -math.sin(tilt), math.cos(tilt))
    X = norm(cross([0, 1, 0], up))
    Y = cross(up, X)
    base = (-.1, .05, 1.95)
    f = (list(base), X, Y, list(up))
    m.tube(base, add(base, mul(up, 1.45)), .06, T.F_DARKWOOD, H, sides=6)
    m.shell(f, [(.08, .08, .55), (.7, .7, .5), (1.35, 1.35, .72), (1.5, 1.5, .82), (1.24, 1.24, 1.08), (.7, .7, 1.28),
                (.04, .04, 1.36)], T.F_CANOPY, H, sides=32, bump=lambda t, k: .08 * abs(math.sin(4 * t)) * (k == 3), double=True)
    for k in range(8):
        t = TAU * k / 8 + TAU / 16
        tip = add(add(add(base, mul(X, 1.5 * math.cos(t))), mul(Y, 1.5 * math.sin(t))), mul(up, .84))
        m.stud(tip, add(mul(X, math.cos(t)), mul(Y, math.sin(t))), .06, T.F_GOLD, H, h=.05)
    ball(m, add(base, mul(up, 1.46)), .12, T.F_GOLD, sides=8)
    m.sweep([add(base, mul(up, 1.5)), add(base, add(mul(up, 1.42), mul(X, -.25))), add(base, add(mul(up, 1.15), mul(X, -.32)))],
            [.04, .05, .02], T.F_GOLD, H, sides=4)


# ------------------------------------------------------------------ body
def cape_pink(m, A):
    """A bright pink cape with gold trim, a white fluffy collar and a big pink bow."""
    B.cloak(m, A, T.F_PINK, T.F_GOLD, T.F_FLUFF, clasp=None)
    x, y, z = A["clasp"]
    for s in (1, -1):
        m.slab([(x + .05, 0, z - .1), (x + .2, s * 1.0, z + .45), (x + .22, s * 1.1, z - .35), (x + .1, s * .2, z - .25)], .12,
               (1, 0, 0), T.F_PINK, "SPINE", bevel=.03)
        m.sweep([(x + .1, s * .12, z - .2), (x + .22, s * .4, z - .9), (x + .28, s * .6, z - 1.6)], [.13, .11, .05], T.F_PINK,
                "SPINE", sides=6, squash=.4)
    ball(m, (x + .18, 0, z - .08), .24, T.F_PINKGEM, "SPINE", sides=8)


def shield_pizza(m, A):
    """A whole pizza as a shield: a golden crust rim, tomato, melted cheese, pepperoni and basil,
    strapped to a wooden board."""
    c, X, Y, N = B.shield_frame(A)
    R = A["shield_size"][1] * 1.12
    o = add(c, mul(N, A["shield_off"]))
    m.shell((o, X, Y, N), [(R * .92, R * .92, .02), (R * .88, R * .88, .16), (R * .5, R * .5, .2), (.02, .02, .22)], T.F_PIZZA,
            "SHIELD", sides=32, planar=R)
    pts = [add(add(add(o, mul(X, R * .95 * math.cos(t))), mul(Y, R * .95 * math.sin(t))), mul(N, .1 + .04 * math.sin(5 * t)))
           for t in [TAU * i / 32 for i in range(33)]]
    m.sweep(pts, [.26 + .04 * math.sin(i * 1.7) for i in range(33)], T.F_CRUST, "SHIELD", sides=8, squash=.75)
    for k, (u, v) in enumerate(((.3, -.2), (-.45, .35), (.1, .5), (-.2, -.5))):     # basil leaves
        p = add(add(add(o, mul(X, u * R)), mul(Y, v * R)), mul(N, .26))
        a = k * 1.3
        d = add(mul(X, math.cos(a)), mul(Y, math.sin(a)))
        side = cross(N, d)
        m.slab([add(p, mul(d, -.35)), add(p, mul(side, .16)), add(p, mul(d, .35)), add(p, mul(side, -.16))], .03, N, T.F_LEAF,
               "SHIELD", bevel=.01)
    m.flat([add(add(add(o, mul(X, R * .97 * math.cos(t))), mul(Y, R * .97 * math.sin(t))), mul(N, -.06))
            for t in [TAU * i / 24 for i in range(24)]][::-1], T.F_OAK, "SHIELD")


def frying_pan(m, A):
    """A cast-iron frying pan on a long oak handle (it fights as a sword of the West)."""
    o, d, e, w = B.grip_frame(A)
    P = lambda t, s=0.0: add(add(o, mul(d, t)), mul(e, s))
    g0 = A["guard_at"]
    m.tube(P(g0 - 2.3), P(g0 + 2.2), .2, T.F_OAK, "HAND", sides=8)
    m.tube(P(g0 + 2.0), P(g0 + 3.4), .17, T.F_IRON, "HAND", sides=6)
    m.sweep([add(P(g0 - 2.6), add(mul(d, .25 * math.cos(a)), mul(e, .25 * math.sin(a)))) for a in [TAU * k / 10 for k in range(11)]],
            [.06] * 11, T.F_IRON, "HAND", sides=4)
    c = P(g0 + 5.6)
    e, w = mul(e, -1), mul(w, -1)                        # the pan opens toward the viewer (still right-handed)
    f = (c, d, e, w)
    m.shell(f, [(.05, .05, -.1), (2.0, 2.0, -.1), (2.18, 2.18, .02), (2.3, 2.3, .38), (2.22, 2.22, .4)], T.F_PAN, "HAND", sides=28,
            planar=2.3, double=True)
    Hm.edge(m, [add(add(c, mul(d, 2.28 * math.cos(a))), add(mul(e, 2.28 * math.sin(a)), mul(w, .4)))
                for a in [TAU * k / 28 for k in range(29)]], .07, T.F_IRON, "HAND")
    for k in range(2):                                   # a fried egg, still in the pan
        p = add(c, add(mul(d, .3 - .9 * k), mul(e, .5 * k - .2)))
        m.shell((add(p, mul(w, -.08)), d, e, w), [(.85, .7, 0), (.75, .6, .05), (.02, .02, .07)], T.F_WHITE, "HAND", sides=12)
        ball(m, add(p, mul(w, .02)), .28, T.F_CHEESE, "HAND", sides=8)


def turkey_leg(m, A):
    """A roast turkey leg, held by the bone in a paper frill (it fights as a sword of the West)."""
    o, d, e, w = B.grip_frame(A)
    P = lambda t, s=0.0, q=0.0: add(add(add(o, mul(d, t)), mul(e, s)), mul(w, q))
    g0 = A["guard_at"]
    m.tube(P(g0 - 2.4), P(g0 + 1.6), .2, T.F_BONE, "HAND", sides=8)
    for s in (1, -1):
        ball(m, P(g0 - 2.5, s * .2), .3, T.F_BONE, "HAND", sides=8)
    m.sweep([P(g0 - 1.2), P(g0 - .6)], [.3, .38], T.F_FRILL, "HAND", sides=10)
    secs = []
    for t, r in ((g0 + 1.2, .3), (g0 + 1.7, .78), (g0 + 2.7, 1.25), (g0 + 3.9, 1.45), (g0 + 4.9, 1.32), (g0 + 5.7, .95),
                 (g0 + 6.1, .35)):
        secs.append([P(t, r * math.cos(a), r * .85 * math.sin(a)) for a in [TAU * k / 12 for k in range(12)]])
    m.loft(secs, T.F_ROAST, "HAND", uv=lambda k, i: (i / 12, k / 6))
