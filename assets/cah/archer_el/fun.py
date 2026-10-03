"""The Archers' fun parts: clearly silly, well made, readable at the RTS camera. Fixed colours on
purpose (a pink cape stays pink), from their own sheet (paint.py FUN_TILES). The pink hood and
pink cape are a matching set; the cloaks and hood reuse the serious geometry with fun tiles."""
import math

from ..kit.geom import add, cross, mul, norm, sub
from . import geo as G
from . import serious as S
from .geo import H, HC, HEAD, SPINE, ball, bowdir, bowpt, edge, ellipse, leaf
from .place import region

(F_GOLD, F_SILVER, F_PINK, F_PINKDARK, F_RAINBOW, F_FLUFF, F_TIARA, F_PINKGEM, F_FUR, F_EARPINK, F_PETALPINK,
 F_PETALYELLOW, F_PETALWHITE, F_PETALBLUE, F_LEAF, F_PEARL, F_CARROT, F_CARROTTOP, F_CANDY, F_HEART, F_HEARTFACE,
 F_STRING, F_TWINE, F_BLACK, F_HOTPINK, F_CENTRE, F_HEARTPINK, F_LAVENDER) = range(28)

PINK_SET = {S.CLOTH: F_PINK, S.CLOTHVINE: F_FLUFF, S.LEAFGOLD: F_HEARTPINK, S.GOLD: F_GOLD, S.GEM: F_PINKGEM,
            S.LINING: F_PINKDARK}


def heart_outline(c, u, v, r, n=24):
    """A heart in the plane (u, v), point down -v, of half-width about r."""
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(add(c, add(mul(u, x * r / 16), mul(v, y * r / 16))))
    return pts


def heart(m, c, u, v, r, thick, tag, bone, bulge=.25):
    """A puffy heart: two convex halves (the slab needs convex outlines), a domed front."""
    nrm = norm(cross(u, v))
    pts = heart_outline(c, u, v, r)
    n = len(pts)
    for half in (pts[:n // 2 + 1], [pts[0]] + pts[n // 2:][::-1]):
        m.slab(half, thick, nrm, tag, bone, bevel=.04)
    m.stud(add(c, mul(nrm, thick * .5)), nrm, r * .55, tag, bone, h=bulge * r, sides=10)


# ------------------------------------------------------------------ helmets
def hood_pink(m):
    """The pink hood: the hood of Lorien in bubblegum pink with a white fluffy edge, closed at the
    throat by a pink heart (the pink cape's match)."""
    S.hood(m, S.LORIEN_RINGS, S.CLOTH, S.CLOTHVINE, None)
    heart(m, (1.85, 0, 20.1), [0, 1, 0], [0, 0, 1], .42, .14, F_HEARTPINK, H)


def tiara(m):
    """A sparkly tiara: a silver band over the crown, a tall pointed front with a big pink gem,
    smaller points stepping down to the ears, every point tipped with a crystal."""
    pts = [(HC[0] + 1.5 * math.cos(t), 1.18 * math.sin(t), 23.1 + .22 * math.cos(t)) for t in
           [-1.75 + 3.5 * i / 16 for i in range(17)]]
    m.sweep(pts, [.07] * len(pts), F_TIARA, H, sides=6, squash=.5)
    for k in range(-3, 4):
        t = k * .42
        base = (HC[0] + 1.52 * math.cos(t), 1.2 * math.sin(t), 23.1 + .22 * math.cos(t))
        hgt = [1.25, .8, .55, .35][abs(k)]
        out = norm((math.cos(t), math.sin(t), 0))
        side = norm(cross((0, 0, 1), out))
        w = .32 if k == 0 else .2
        top = add(base, (0, 0, hgt))
        m.slab([add(base, mul(side, -w)), add(add(base, mul(side, -w * .5)), (0, 0, hgt * .6)), top,
                add(add(base, mul(side, w * .5)), (0, 0, hgt * .6)), add(base, mul(side, w))], .07, out, F_TIARA, H, bevel=.02)
        ball(m, add(top, (0, 0, .1)), .1 if k else .14, F_PINKGEM if k % 2 == 0 else F_SILVER, H, sides=6)
    m.stud((HC[0] + 1.64, 0, 23.65), (1, 0, .2), .3, F_PINKGEM, H, h=.22, sides=10)
    for s in (1, -1):
        m.stud((HC[0] + 1.6 * math.cos(.42), s * 1.25 * math.sin(.42), 23.45), (1, s * .5, .1), .14, F_PINKGEM, H, h=.1)


def cat_ears(m):
    """Cat ears: a pink headband over the crown and two big ginger tabby ears with pink insides
    and white fluffy tufts."""
    band = [(HC[0] + .25 + .1 * math.cos(t), 1.32 * math.sin(t), 22.0 + 1.75 * math.cos(t) ** .5 if math.cos(t) > 0 else 22.0)
            for t in [-1.55 + 3.1 * i / 16 for i in range(17)]]
    m.sweep(band, [.11] * len(band), F_HEARTPINK, H, sides=6, squash=.5, up=[1, 0, 0])
    for s in (1, -1):
        base = (HC[0] + .2, s * .85, 23.25)
        tip = (HC[0] + .05, s * 1.75, 25.6)
        fwd, sd = (1, 0, 0), norm((0, s, -.3))
        outer = [add(base, mul(sd, -.7)), add(base, mul(sd, .9)), tip]
        m.slab(outer, .22, fwd, F_FUR, H, bevel=.05)
        inner = [add(add(base, mul(sd, -.42)), (.14, 0, .14)), add(add(base, mul(sd, .62)), (.14, 0, .14)),
                 add(tip, (.13, -s * .08, -.4))]
        m.slab(inner, .06, fwd, F_EARPINK, H, bevel=.02)
        for k in range(3):
            ball(m, add(add(base, mul(sd, -.1 + .25 * k)), (.25, 0, .3 + .12 * k)), .14, F_FLUFF, H, sides=6)


FLOWER_TAGS = (F_PETALPINK, F_PETALYELLOW, F_PETALWHITE, F_PETALBLUE, F_LAVENDER)


def flower(m, c, out, r, petal, bone=H, n=5):
    """A flower: n petals round a gold-orange centre."""
    up = [0, 0, 1] if abs(out[2]) < .9 else [1, 0, 0]
    u = norm(cross(out, up))
    v = cross(out, u)
    n = n if m.lod >= .6 else 4                     # trimmed: four petals read the same from afar
    for k in range(n):
        a = 2 * math.pi * k / n
        d = add(mul(u, math.cos(a)), mul(v, math.sin(a)))
        side = add(mul(u, -math.sin(a)), mul(v, math.cos(a)))
        p0 = add(c, mul(d, r * .2))
        m.slab([p0, add(add(c, mul(d, r * .7)), mul(side, r * .38)), add(add(c, mul(d, r)), mul(out, -r * .1)),
                add(add(c, mul(d, r * .7)), mul(side, -r * .38))], .05, out, petal, bone, bevel=.01)
    m.stud(add(c, mul(out, .02)), out, r * .3, F_CENTRE, bone, h=r * .22, sides=8)


def flower_crown(m):
    """A crown of flowers: a woven green vine round the head set with eleven flowers in pink,
    yellow, white, blue and lavender, leaves between them."""
    pts = ellipse(HC[0] - .05, 1.72, 1.34, 22.85, n=24, lift=lambda t: .25 * math.cos(t))
    m.sweep(pts, [.09] * len(pts), F_LEAF, H, sides=6)
    for k in range(11):
        t = 2 * math.pi * k / 11
        c = (HC[0] - .05 + 1.8 * math.cos(t), 1.42 * math.sin(t), 22.95 + .25 * math.cos(t))
        out = norm((math.cos(t) * .8, math.sin(t) * .8, .55))
        flower(m, c, out, .64 if k % 3 == 0 else .52, FLOWER_TAGS[k % 5])
        if m.lod < .5:                              # trimmed: the vine carries the green
            continue
        t2 = t + math.pi / 11
        c2 = (HC[0] - .05 + 1.78 * math.cos(t2), 1.4 * math.sin(t2), 22.8 + .25 * math.cos(t2))
        leaf(m, c2, norm((-math.sin(t2), math.cos(t2), .2)), (0, 0, 1), .5, .22, .04, F_LEAF, H, out=(math.cos(t2), math.sin(t2), 0))


def unicorn(m):
    """A unicorn horn circlet: a silver band, a long spiral pearl horn rising from the brow, gold
    stars at its root and a little rainbow forelock."""
    S.circlet(m, tag=F_SILVER)
    base = (1.62, 0, 23.15)
    d = norm((.55, 0, 1))
    n = 14
    pts, radii = [], []
    side = norm(cross(d, (0, 1, 0)))
    for i in range(n + 1):
        f = i / n
        twist = .05 * (1 - f) * math.sin(f * 9 * math.pi)
        pts.append(add(add(base, mul(d, 3.2 * f)), mul(side, twist)))
        radii.append(.36 * (1 - f) ** .9 + .015)
    m.sweep(pts, radii, F_PEARL, H, sides=10)
    m.tube(add(base, mul(d, -.1)), add(base, mul(d, .15)), .42, F_GOLD, H, sides=10)
    for s in (1, -1):
        c = (1.55, s * .5, 23.05)
        m.stud(c, (1, s * .4, .1), .17, F_GOLD, H, h=.1, sides=5)
    for k, tag in enumerate((F_PETALPINK, F_PETALYELLOW, F_PETALBLUE, F_LAVENDER)):
        y = (k - 1.5) * .22
        m.sweep([(1.45, y, 23.3), (1.85, y * 1.3, 23.0), (2.0, y * 1.6, 22.4)], [.14, .1, .03], tag, H, sides=5, squash=.6)


# ------------------------------------------------------------------ capes
def cape_pink(m):
    """The pink cape: a long bubblegum-pink cloak with white fluff along the hem and collar, two
    pink hearts for clasps on a gold chain (the pink hood's match)."""
    G.cloak(m, F_PINK, F_FLUFF, F_FLUFF, lining=F_PINKDARK)
    for s in (1, -1):
        c = (1.05, s * 1.65, 19.7)
        heart(m, c, [0, 1, 0], norm((.2, 0, 1)), .42, .12, F_HEARTPINK, SPINE)
        m.sweep([(-.5, s * 2.6, 20.0), (.2, s * 2.25, 19.95), c], [.06] * 3, F_GOLD, SPINE, sides=5)
    m.sweep([(1.15, 1.6, 19.5), (1.45, .8, 19.1), (1.55, 0, 18.95), (1.45, -.8, 19.1), (1.15, -1.6, 19.5)], [.04] * 5,
            F_GOLD, SPINE, sides=4)


def cloak_rainbow(m):
    """A rainbow cloak: each fold its own colour, gold-edged."""
    S.cloak_lorien(m, cloth=F_RAINBOW, hem=F_GOLD, clasp=F_GOLD, collar=F_FLUFF, chain=F_GOLD, gem=F_PINKGEM, lining=F_RAINBOW)


# ------------------------------------------------------------------ shield and bows
def shield_heart(m):
    """A heart shield: a puffy pink heart on the bow arm, its face a red heart in sparkles, a gold
    rim and a hot-pink gem boss."""
    region(m, "arm")
    bone = "BAT_FARML"
    mid = add(G.ELBOW, mul(G.FOREARM, 1.9))
    out = norm(sub((0, 1, 0), mul(G.FOREARM, G.FOREARM[1])))
    across = norm(cross(out, G.FOREARM))
    c = add(mid, mul(out, 1.0))
    v = mul(G.FOREARM, -1)
    pts = heart_outline(c, across, v, 2.1)
    face = [add(p, mul(out, .12)) for p in pts]
    uv = lambda p: (.5 + sum(a * b for a, b in zip(sub(p, c), across)) / 4.4, .5 + sum(a * b for a, b in zip(sub(p, c), v)) / 4.4)
    n = len(pts)
    for half in (face[:n // 2 + 1], [face[0]] + face[n // 2:][::-1]):
        cc = add(c, mul(out, .3))
        m.flat([cc] + half, F_HEARTFACE, bone, [uv(cc)] + [uv(p) for p in half])
    m.flat([add(p, mul(out, -.12)) for p in pts], F_GOLD, bone)
    edge(m, face + [face[0]], .13, F_GOLD, bone, sides=6)
    m.stud(add(c, mul(out, .3)), out, .35, F_PINKGEM, bone, h=.25, sides=10)


def bow_carrot(m):
    """A giant carrot for a bow: an orange ringed root curving from its thin tip to a fat crown of
    leafy tops, a twine grip, a white string."""
    region(m, "bow")
    L = 7.8
    x_of = lambda z: .95 - 3.0 * (abs(z) / L) ** 1.8
    zs = [L * (k / 12) for k in range(-12, 13)]
    path = [bowpt(x_of(z), 0, z) for z in zs]
    radii = [.06 + .55 * ((z + L) / (2 * L)) ** 1.4 for z in zs]
    m.sweep(path, radii, F_CARROT, G.BOW, sides=10)
    m.sweep([bowpt(x_of(z), 0, z) for z in (-.9, 0, .9)], [.42, .48, .52], F_TWINE, G.BOW, sides=8)
    top = bowpt(x_of(L), 0, L)
    for k in range(6):
        a = 2 * math.pi * k / 6
        d = bowdir(.4 * math.cos(a), .4 * math.sin(a), 1)
        m.sweep([top, add(top, mul(d, .9)), add(add(top, mul(d, 1.9)), bowdir(.2 * math.cos(a), .2 * math.sin(a), 0))],
                [.12, .08, .02], F_CARROTTOP, G.BOW, sides=5)
        leaf(m, add(top, mul(d, 1.7)), d, bowdir(-math.sin(a), math.cos(a), 0), .9, .45, .04, F_CARROTTOP, G.BOW,
             out=bowdir(math.cos(a), math.sin(a), 0))
    m.tube(bowpt(x_of(-L), 0, -L), top, .025, F_STRING, G.BOW, sides=3)


def bow_candy(m):
    """A candy cane bow: red-and-white spiral-striped limbs, both tips hooked over like a candy
    cane, a green ribbon bow at the grip."""
    region(m, "bow")
    L = 7.2
    x_of = lambda z: .95 - 2.7 * (abs(z) / L) ** 1.8
    zs = [L * (k / 12) for k in range(-12, 13)]
    m.sweep([bowpt(x_of(z), 0, z) for z in zs], [.26] * len(zs), F_CANDY, G.BOW, sides=10)
    for sgn in (1, -1):
        z0 = sgn * L
        hook = [bowpt(x_of(z0) + .9 - .9 * math.cos(a), 0, z0 + sgn * .9 * math.sin(a)) for a in
                [math.pi * k / 8 for k in range(9)]]
        m.sweep(hook, [.26] * 9, F_CANDY, G.BOW, sides=10)
    for s in (1, -1):
        m.slab([bowpt(1.2, 0, 0), bowpt(1.5, s * .9, .55), bowpt(1.5, s * 1.0, -.45)], .1, bowdir(1, 0, 0), F_LEAF, G.BOW)
    ball(m, bowpt(1.25, 0, 0), .22, F_LEAF, G.BOW, sides=8)
    m.tube(bowpt(x_of(-L), 0, -L), bowpt(x_of(L), 0, L), .025, F_STRING, G.BOW, sides=3)
