"""The Evil classes' weapons and shields, drawn on each model's measured grip (EA's own reference
weapon there: its axis, reach and edge) and shield arm (EA's shield: its face and rim).

Weapon space: t along the reach from the grip, b along the edge, w across, in units of a twelfth
of EA's reference weapon's reach in that model; so an orc's cleaver and a troll's maul are each
as long, relative to their wielder, as EA's own.
"""
import math

from ..kit.geom import add, mul
from .helms import (A_IRON, BLADE, BRASS, BRASSORN, EMBER, EYE, GOLD, HAFT, HAND, I_IRON, IRON, MORGUL, PLATE, RED, SILVER,
                    STEEL, TINE, WRAP)
from .shapes import ball, edge, emblem, of


def _k(A):
    return A.k


def blade_loft(m, A, samples, tag, back=.35, sides_tag=None):
    """A blade through sections [(t, offset along b, width, thickness)]: each a six-point lens, keen
    on +b, blunt (back x width) on -b; capped."""
    k, W = _k(A), A.weapon
    secs = []
    for t, c, wd, th in samples:
        o = A.wp(t, c, 0)
        P = lambda bb, ww: list(add(add(o, mul(W["B"], bb * k)), mul(W["W"], ww * k)))
        secs.append([P(wd * .5, 0), P(wd * .1, th * .5), P(-wd * back, th * .5), P(-wd * back - th * .2, 0),
                     P(-wd * back, -th * .5), P(wd * .1, -th * .5)])
    m.loft(secs, tag, W["bone"], uv=lambda kk, i: ((i % 6) / 6, kk / max(1, len(secs) - 1)))


def haft(m, A, t0, t1, r, tag, sides=8, r1=None):
    k = _k(A)
    m.tube(list(A.wp(t0)), list(A.wp(t1)), r * k, tag, A.weapon["bone"], sides=sides, r1=None if r1 is None else r1 * k)


def cleaver_mordor(m):
    """Morgul cleaver: a broad black-iron blade with a hard steel edge, a saw-toothed spine and a
    hooked tip, an iron ring guard, a leather-wrapped grip and an ember-set pommel."""
    A = of(m)
    k, bone = _k(A), A.weapon["bone"]
    haft(m, A, -1.6, 1.4, .17, WRAP)
    haft(m, A, 1.2, 1.6, .32, IRON, sides=6)
    m.stud(list(A.wp(-1.7)), [-x for x in A.weapon["D"]], .26 * k, IRON, bone, h=.3 * k, sides=6)
    m.stud(list(A.wp(-1.95)), [-x for x in A.weapon["D"]], .14 * k, EMBER, bone, h=.1 * k, sides=6)
    blade_loft(m, A, [(1.5, .55, 1.0, .14), (4.0, .8, 1.6, .12), (7.5, .95, 1.9, .1), (10.2, .95, 2.0, .08),
                      (11.6, .75, 1.3, .06), (12.2, .2, .2, .04)], IRON, back=.45)
    blade_loft(m, A, [(1.6, 1.12, .35, .08), (4.0, 1.58, .45, .07), (7.5, 1.85, .5, .06), (10.2, 1.9, .5, .05),
                      (11.6, 1.38, .4, .04), (12.1, .35, .1, .03)], BLADE, back=.5)
    for i in range(6):                                     # saw-teeth along the spine
        t = 2.5 + 1.45 * i
        a, b, tip = A.wp(t, -.05), A.wp(t + 1.0, -.08), A.wp(t + .25, -.55)
        m.slab([list(a), list(b), list(tip)], .09 * k, A.weapon["W"], STEEL, bone, bevel=.02 * k)
    hook = [A.wp(11.3, -.1), A.wp(12.0, -.6), A.wp(12.3, -1.1), A.wp(12.0, -1.5)]
    m.sweep([list(p) for p in hook], [.12 * k, .1 * k, .06 * k, .01 * k], STEEL, bone, sides=5)


def scimitar_harad(m):
    """Haradrim scimitar: a deeply curved, broadening blade of bright steel, a brass guard with
    down-turned quillons, a crimson-wrapped grip (colour R) and a brass pommel."""
    A = of(m)
    k, bone = _k(A), A.weapon["bone"]
    haft(m, A, -1.4, 1.2, .16, RED)
    m.stud(list(A.wp(-1.5)), [-x for x in A.weapon["D"]], .24 * k, BRASS, bone, h=.3 * k, sides=8)
    for s in (1, -1):
        guard = [A.wp(1.25, 0, 0), A.wp(1.35, s * .6, 0), A.wp(1.15, s * 1.1, 0), A.wp(.85, s * 1.3, 0)]
        m.sweep([list(p) for p in guard], [.13 * k, .11 * k, .08 * k, .04 * k], BRASS, bone, sides=6)
    m.stud(list(A.wp(1.3)), A.weapon["W"], .2 * k, BRASSORN, bone, h=.08 * k, sides=6)
    samples = []
    for i in range(9):
        f = i / 8
        t = 1.4 + 10.4 * f
        curve = -1.4 * f * f
        wd = .7 + .55 * math.sin(math.pi * min(1, f * 1.15)) * (f < .87) + (.0 if f < .87 else -.5)
        samples.append((t, curve, max(.1, wd) * (1 - .9 * (f == 1)), .1 * (1 - .5 * f)))
    blade_loft(m, A, samples, BLADE, back=.3)


def maul_mordor(m):
    """Mordor siege maul: a long iron-shod haft, a massive black-iron head banded in steel with
    hooked spikes on every face and an ember core glowing through its slots."""
    A = of(m)
    k, bone, W = _k(A), A.weapon["bone"], A.weapon
    haft(m, A, -1.5, 9.5, .22, HAFT)
    for t0 in (-1.0, 3.0):
        haft(m, A, t0, t0 + .5, .27, IRON, sides=6)
    haft(m, A, -.5, 2.6, .25, WRAP)
    c = 10.5
    secs = []
    for t, h in ((8.8, 1.0), (9.1, 1.25), (11.9, 1.25), (12.2, 1.0)):
        o = A.wp(t)
        secs.append([list(add(add(o, mul(W["B"], h * k * math.cos(a))), mul(W["W"], h * k * math.sin(a))))
                     for a in [math.pi / 4 + math.pi / 2 * i for i in range(4)]])
    m.loft(secs, PLATE, bone, uv=lambda kk, i: (i / 4, kk / 3))
    for t in (9.25, 11.75):
        haft(m, A, t - .12, t + .12, 1.0, STEEL, sides=4)
    haft(m, A, 10.3, 10.7, .95, EMBER, sides=4)
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for t in (9.8, 11.2):
            base = A.wp(t, d[0] * 1.0, d[1] * 1.0)
            tip = A.wp(t + .4, d[0] * 2.0, d[1] * 2.0)
            m.tube(list(base), list(tip), .28 * k, STEEL, bone, sides=4, r1=.02 * k)
    m.tube(list(A.wp(12.1)), list(A.wp(13.4)), .35 * k, STEEL, bone, sides=4, r1=.02 * k)


def club_angmar(m):
    """Rime-club of Angmar: a gnarled tree trunk bound in blue iron, studded with tines frozen white
    at their tips, an iron cap and a rope-wrapped grip."""
    A = of(m)
    k, bone, W = _k(A), A.weapon["bone"], A.weapon
    secs = []
    for t, r in ((-1.6, .3), (1.0, .33), (4.0, .5), (7.0, .78), (9.6, 1.0), (11.6, 1.05), (12.4, .8)):
        o = A.wp(t)
        secs.append([list(add(add(o, mul(W["B"], r * k * (1 + .12 * math.sin(3 * a + t)) * math.cos(a))),
                              mul(W["W"], r * k * (1 + .12 * math.sin(3 * a + t)) * math.sin(a)))) for a in [2 * math.pi * i / 8 for i in range(8)]])
    m.loft(secs, HAFT, bone, uv=lambda kk, i: (i / 8, kk / 6))
    haft(m, A, -1.0, 2.2, .36, WRAP, sides=6)
    for t, r in ((5.5, .66), (8.6, .93), (11.0, 1.1)):
        haft(m, A, t - .2, t + .2, r, A_IRON, sides=8)
    for i in range(10):
        a = 2 * math.pi * i / 10 * 1.618
        t = 7.2 + 4.6 * i / 9
        r = .8 + .25 * i / 9
        d = (math.cos(a), math.sin(a))
        base = A.wp(t, d[0] * r * .9, d[1] * r * .9)
        tip = A.wp(t + .5, d[0] * (r + 1.3), d[1] * (r + 1.3))
        m.tube(list(base), list(tip), .2 * k, TINE, bone, sides=4, r1=.02 * k)
    m.stud(list(A.wp(12.3)), W["D"], .75 * k, A_IRON, bone, h=.5 * k, sides=8)


def rubber_chicken(m):
    """A rubber chicken held by its feet: a plump pale-yellow body, a long limp neck, a red comb and
    wattle, an orange beak, black eyes and stubby wings; it squeaks (it fights as a sword)."""
    A = of(m)
    k, bone, W = _k(A), A.weapon["bone"], A.weapon
    for s in (1, -1):                                      # the legs in the fist
        m.tube(list(A.wp(-.6, 0, s * .2)), list(A.wp(1.6, 0, s * .3)), .14 * k, 10, bone, sides=4)
        for d in (-1, 1):
            m.tube(list(A.wp(-.6, 0, s * .2)), list(A.wp(-1.1, d * .3, s * .25 + d * .1)), .07 * k, 10, bone, sides=3, r1=.03 * k)
    secs = []
    for t, hb, hw in ((1.4, .5, .5), (2.4, 1.3, 1.1), (3.8, 1.6, 1.3), (5.2, 1.4, 1.15), (6.2, .8, .7), (6.8, .38, .36)):
        o = A.wp(t)
        secs.append([list(add(add(o, mul(W["B"], hb * k * math.cos(a))), mul(W["W"], hw * k * math.sin(a))))
                     for a in [2 * math.pi * i / 8 for i in range(8)]])
    m.loft(secs, 8, bone, uv=lambda kk, i: (i / 8, kk / 5))
    neck = [A.wp(6.6, 0), A.wp(8.0, .3), A.wp(9.4, .9), A.wp(10.4, 1.5)]
    m.sweep([list(p) for p in neck], [.38 * k, .3 * k, .28 * k, .3 * k], 8, bone, sides=6)
    head = A.wp(10.8, 1.7)
    ball(m, head, .62 * k, 8, bone, sides=7)
    m.tube(list(A.wp(11.2, 1.75)), list(A.wp(11.8, 1.5)), .22 * k, 10, bone, sides=6, r1=.03 * k)
    for i in range(3):                                     # the comb
        ball(m, A.wp(10.5 + .35 * i, 2.3 - .05 * i), .24 * k, 9, bone, sides=5)
    ball(m, A.wp(11.0, 1.1), .2 * k, 9, bone, sides=5)
    for s in (1, -1):
        ball(m, A.wp(11.0, 1.95, s * .45), .14 * k, 11, bone, sides=4)
        m.slab([list(A.wp(3.0, .3, s * 1.2)), list(A.wp(5.0, .6, s * 1.3)), list(A.wp(4.6, -.6, s * 1.2))], .15 * k,
               mul(W["W"], s), 8, bone, bevel=.04 * k)


def lollipop(m):
    """A giant swirl lollipop: a white stick and a fat disc of pink, white and lilac spiral with a
    rainbow rim, a pink ribbon bow where the stick meets the sweet."""
    A = of(m)
    k, bone, W = _k(A), A.weapon["bone"], A.weapon
    haft(m, A, -1.5, 8.6, .2, 14, sides=8)
    c = A.wp(11.2)
    R = 3.0 * k
    face = W["W"]
    prof = [(.05 * k, .05 * k, -.55 * k), (R * .8, R * .8, -.55 * k), (R, R, -.32 * k), (R * 1.02, R * 1.02, 0),
            (R, R, .32 * k), (R * .8, R * .8, .55 * k), (.05 * k, .05 * k, .55 * k)]
    m.shell((list(c), list(W["D"]), list(W["B"]), list(face)), prof, 13, bone, sides=28, planar=R * 1.02)
    for s in (1, -1):
        loop = [A.wp(8.3, 0, 0), A.wp(7.9, s * .9, .5), A.wp(7.3, s * 1.1, 0), A.wp(7.9, s * .9, -.5), A.wp(8.3, 0, 0)]
        m.sweep([list(p) for p in loop[:-1]], [.12 * k, .2 * k, .2 * k, .12 * k], 4, bone, sides=6, squash=.5)
        m.sweep([list(A.wp(8.2, 0, 0)), list(A.wp(6.9, s * .5, 0)), list(A.wp(6.3, s * .8, 0))], [.1 * k, .1 * k, .03 * k], 4,
                bone, sides=4, squash=.4)
    ball(m, A.wp(8.3), .22 * k, 4, bone, sides=6)


# ------------------------------------------------------------------ shields
def _shield(A):
    S = A.shield
    return S["c"], S["N"], S["U"], S["V"], S["R"], S["bone"]


def shield_whitehand(m):
    """Shield of the White Hand: a tall black-iron Uruk shield, pointed below, rimmed in silver,
    the White Hand painted across its face and a silver boss spike."""
    A = of(m)
    c, N, U, V, R, bone = _shield(A)
    c = add(c, mul(N, .05 * R))
    P = lambda x, y, z=0.0: list(add(add(add(c, mul(V, x * R)), mul(U, y * R)), mul(N, z * R)))
    xy = [(-.62, .95), (.62, .95), (.68, .1), (.42, -.75), (0, -1.12), (-.42, -.75), (-.68, .1)]
    outline = [P(x, y) for x, y in xy]
    m.slab(outline, .08 * R, N, I_IRON, bone, bevel=.03 * R)
    face = [(.95, .6), (.1, .66), (-.75, .41), (-1.1, .02)]            # (height, half width), top down
    rows = [[P(-hw * (1 - 2 * i / 6), y, .045) for i in range(7)] for y, hw in face[::-1]]
    uvs = [[((.7 + hw * (1 - 2 * i / 6)) / 1.4, (y + .5) / 1.4) for i in range(7)] for y, hw in face[::-1]]
    m.grid(rows, uvs, HAND, bone)                           # the viewer's right is -V
    edge(m, outline + [outline[0]], .045 * R, SILVER, bone, sides=5)
    edge(m, [P(x * .88, y * .9, .07) for x, y in xy + xy[:1]], .022 * R, WRAP, bone, sides=4)
    m.tube(P(0, -.62, .05), P(0, -.62, .3), .09 * R, SILVER, bone, sides=6, r1=.01 * R)
    for x, y in ((-.5, .8), (.5, .8), (-.55, .0), (.55, .0), (-.3, -.65), (.3, -.65)):
        m.stud(P(x, y, .05), N, .045 * R, SILVER, bone, sides=4)


def shield_mordor(m):
    """Shield of the Black Gate: a round, domed black-iron shield on riveted plates, a rim of hooked
    steel spikes, and the Eye in ember on a raised boss plate."""
    A = of(m)
    c, N, U, V, R, bone = _shield(A)
    c = add(c, mul(N, .05 * R))
    R = R * .85
    X = mul(V, -1)                                         # the viewer's right
    f = (c, X, U, N)
    m.shell(f, [(R * .98, R * .98, 0), (R, R, .06 * R), (R * .8, R * .8, .16 * R), (R * .42, R * .42, .22 * R),
                (.02, .02, .24 * R)], PLATE, bone, sides=24, planar=R)
    rim = [add(add(c, mul(X, R * math.cos(a))), add(mul(U, R * math.sin(a)), mul(N, .04 * R))) for a in [2 * math.pi * i / 24 for i in range(25)]]
    edge(m, rim, .05 * R, STEEL, bone, sides=5)
    edge(m, [add(c, add(mul(X, R * .86 * math.cos(a)), add(mul(U, R * .86 * math.sin(a)), mul(N, .1 * R))))
             for a in [2 * math.pi * i / 20 for i in range(21)]], .035 * R, WRAP, bone, sides=4)
    for i in range(10):
        a = 2 * math.pi * i / 10 + .3
        d = add(mul(X, math.cos(a)), mul(U, math.sin(a)))
        base = add(add(c, mul(d, R * .95)), mul(N, .05 * R))
        side = add(mul(X, -math.sin(a)), mul(U, math.cos(a)))
        pts = [add(add(base, mul(d, R * .32 * t)), mul(side, R * .14 * t * t)) for t in (0, .35, .7, 1.0)]
        m.sweep(pts, [.07 * R, .055 * R, .03 * R, .004 * R], STEEL, bone, sides=4)
    o = add(c, mul(N, .2 * R))
    P = lambda x, y: add(add(o, mul(X, x * R)), mul(U, y * R))
    m.slab([P(-.42, .22), P(.42, .22), P(.42, -.22), P(-.42, -.22)], .06 * R, N, IRON, bone, bevel=.02 * R)
    o = add(o, mul(N, .045 * R))
    emblem(m, [P(-.4, .2), P(.4, .2), P(.4, -.2), P(-.4, -.2)], EYE, bone)


def shield_hugme(m):
    """The "Hug me" sign: a hand-painted plank sign, red letters and a heart, nailed to a crossbar
    and carried on the shield arm."""
    A = of(m)
    c, N, U, V, R, bone = _shield(A)
    P = lambda x, y, z=0.0: list(add(add(add(c, mul(V, x * R)), mul(U, y * R)), mul(N, z * R)))
    m.slab([P(-.85, .62), P(.85, .62), P(.85, -.62), P(-.85, -.62)], .09 * R, N, 24, bone, bevel=.025 * R)
    emblem(m, [P(.82, .6, .05), P(-.82, .6, .05), P(-.82, -.6, .05), P(.82, -.6, .05)], 23, bone)
    for y in (.45, -.45):
        m.slab([P(-.95, y + .1, -.08), P(.95, y + .1, -.08), P(.95, y - .1, -.08), P(-.95, y - .1, -.08)], .07 * R, N, 24, bone,
               bevel=.02 * R)
    for x in (-.78, .78):
        for y in (.45, -.45):
            m.stud(P(x, y, .05), N, .035 * R, 29, bone, sides=4)
    edge(m, [P(-.85, .62, .03), P(.85, .62, .03), P(.85, -.62, .03), P(-.85, -.62, .03), P(-.85, .62, .03)], .03 * R, 27, bone,
         sides=4)


__all__ = ["club_angmar", "cleaver_mordor", "scimitar_harad", "maul_mordor", "rubber_chicken", "lollipop", "shield_whitehand",
           "shield_hugme", "shield_mordor", "GOLD", "MORGUL"]
