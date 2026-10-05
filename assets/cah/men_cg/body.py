"""The Men of the West's body gear, drawn from a subclass's anatomy (design.py's ANATOMY: shoulder
joints, the arm, the back for a cloak, EA's shield and sword frames) so the Captain and the
Shieldmaiden share every design: Gondor's pauldrons, the Mantle of the White Tree, the Cloak of
the Mark, the tower shield of Minas Tirith, Rohan's sun-wheel shield and both swords.

Bones are abstract ("SPINE", "UARM_L", "UARM_R", "SHIELD", "HAND"); BONE_MAP names them per
model. On a mounted model (its skeleton has the horse's spine) a cloak stops at the saddle.
"""
import math

from ..kit.geom import add, cross, mul, norm, sub
from . import paint as T

TAU = 2 * math.pi


def edge(m, pts, r, tag, bone, sides=6, squash=1.0):
    m.sweep(pts, [r] * len(pts), tag, bone, sides=sides, squash=squash)


def mounted(m):
    return "BAT_HSPINE1" in m.skeleton.names


def frame_pts(f, r1, r2, h, n=24, a0=0.0, a1=TAU):
    o, X, Y, Z = f
    return [add(add(add(o, mul(X, r1 * math.cos(a0 + (a1 - a0) * i / n))), mul(Y, r2 * math.sin(a0 + (a1 - a0) * i / n))),
                mul(Z, h)) for i in range(n + 1)]


def shoulder_frame(A, s):
    """(origin, X, Y, Z) over the shoulder of side s (+1 left): Z out and up."""
    x, y, z = A["shoulder"]
    Z = norm((A["up"][0], s * A["up"][1], A["up"][2]))
    X = [1, 0, 0]
    return [x, s * y, z], X, cross(Z, X), Z


def arm_frame(A, s, dist):
    """A frame round the upper arm `dist` below the shoulder joint: Z down the arm."""
    d = norm((A["arm"][0], s * A["arm"][1], A["arm"][2]))
    x, y, z = A["shoulder"]
    o = add([x, s * y, z], mul(d, dist))
    X = norm(cross([0, 0, s], d))
    X = X if X[0] > 0 else mul(X, -1)
    return o, X, cross(d, X), d


def outer_arc(s):
    c = math.pi * .5 if s < 0 else -math.pi * .5
    return c - 1.75, c + 1.75


# ------------------------------------------------------------------ shoulders
def pauldrons(m, A, plate=T.STEEL, trim=T.GOLD, boss=T.GEM, lames=3, lame=None):
    """Gondor's pauldrons: a bright steel dome over each shoulder edged in rolled gold with a
    sapphire boss, and riveted lames down the arm (in `lame`, default the plate's tile)."""
    K = A["pauldron"]
    for s, bone in ((1, "UARM_L"), (-1, "UARM_R")):
        f = shoulder_frame(A, s)
        prof = [(a * K, b * K, c * K) for a, b, c in [(1.0, .9, 0), (1.02, .92, .16), (.94, .84, .44), (.72, .64, .72),
                                                       (.4, .36, .88), (.03, .03, .93)]]
        m.shell(f, prof, plate, bone, sides=26)
        edge(m, frame_pts(f, 1.04 * K, .94 * K, .06 * K, 26), .07, trim, bone)
        o, X, Y, Z = f
        m.stud(add(o, mul(Z, .93 * K)), Z, .2 * K, trim, bone, h=.1 * K, sides=8)
        m.stud(add(o, mul(Z, 1.0 * K)), Z, .11 * K, boss, bone, h=.08 * K, sides=6)
        for k in range(lames):
            fo, fX, fY, fZ = arm_frame(A, s, K * (.55 + .38 * k))
            r = K * (.86 - .07 * k)
            arc = outer_arc(s)
            m.shell((fo, fX, fY, fZ), [(r, r * .95, 0), (r - .04, (r - .04) * .95, .4 * K)], lame or plate, bone, sides=14,
                    arc=arc, double=True)
            pts = [add(add(add(fo, mul(fX, (r + .02) * math.cos(t))), mul(fY, (r + .02) * .95 * math.sin(t))), mul(fZ, .4 * K))
                   for t in [arc[0] + (arc[1] - arc[0]) * i / 14 for i in range(15)]]
            edge(m, pts, .045, trim, bone)


def cloak(m, A, tag, hem, collar_tag, folds=7, clasp=T.GOLD, clasp_gem=T.GEM, collar=True, hem_r=.08):
    """A cloak from the shoulders to mid-thigh on the spine (EA's rigs have no cloth bones), in
    `folds` deep folds, braided along hem and sides; on a mounted model it ends at the saddle."""
    cx, prof = A["cloak_cx"], A["cloak"]
    if mounted(m):
        prof = prof[A["cloak_saddle"]:]
    back = ((cx, 0.0, 0.0), [1, 0, 0], [0, 1, 0], [0, 0, 1])
    arc = (math.pi * .64, math.pi * 1.36)
    K = len(prof)
    bump = lambda t, k: A["fold"] * (1 - k / (K - 1)) ** 1.2 * math.sin(folds * TAU * (t - arc[0]) / (arc[1] - arc[0]))
    rows = m.shell(back, prof, tag, "SPINE", sides=48, arc=arc, double=True, bump=bump, keep=28)
    edge(m, [add(p, (-.02, 0, -.02)) for p in rows[0]], hem_r, hem, "SPINE")
    for col in (0, -1):
        edge(m, [r[col] for r in rows], hem_r * .75, hem, "SPINE")
    if collar:
        x0, rx, ry, z = A["collar"]
        pts = [(x0 + rx * math.cos(a), ry * math.sin(a), z + .12 * math.cos(a)) for a in
               [math.pi * (.58 + .84 * i / 16) for i in range(17)]]
        m.sweep(pts, [A["collar_r"] * (1 + .25 * math.sin(math.pi * i / 16)) for i in range(17)], collar_tag, "SPINE", sides=10)
    if clasp is not None:
        for s in (1, -1):
            p = A["clasp"]
            m.stud((p[0], s * p[1], p[2]), (1, s * .35, .2), .24 * A["pauldron"], clasp, "SPINE", h=.14, sides=8)
            m.stud((p[0] + .08, s * p[1], p[2]), (1, s * .35, .2), .12 * A["pauldron"], clasp_gem, "SPINE", h=.1)
    return rows


def mantle_tree(m, A):
    """Mantle of the White Tree: steel shoulder caps and a sable cloak bearing the White Tree,
    with a fur collar and gold clasps."""
    pauldrons(m, A, lames=1 if m.lod >= .5 else 0)
    cloak(m, A, T.TREECLOAK, T.STEEL, T.FUR)


def cloak_mark(m, A):
    """Cloak of the Mark: a green riding cloak with a gold-braided hem and a horse-head brooch,
    over gilded leather shoulder guards."""
    pauldrons(m, A, plate=T.LEATHER, trim=T.GOLD, lames=1 if m.lod >= .5 else 0)
    cloak(m, A, T.MARKCLOAK, T.GOLD, T.FUR, folds=6)


# ------------------------------------------------------------------ shields
def shield_frame(A):
    c, n, up = A["shield"]
    n = norm(n)
    up = norm(sub(up, mul(n, sum(a * b for a, b in zip(up, n)))))
    return c, cross(up, n), up, n


def shield_gondor(m, A, face=T.TREE, rim=T.STEEL, back=T.PLANKS, strap=T.LEATHER):
    """Tower Shield of Minas Tirith: a tall heater shield, the White Tree beneath seven stars and
    the crown on a sable field, a rolled steel rim and a planked back."""
    c, X, Y, N = shield_frame(A)
    Hh, W = A["shield_size"]
    o = add(c, mul(N, A["shield_off"]))
    outline = []
    for i in range(13):                                    # flat top, curved sides to a point
        t = i / 12
        outline.append((-W + 2 * W * t, Hh * (.92 + .08 * math.sin(math.pi * t))))
    for i in range(1, 16):
        t = i / 16
        x = W * (1 - t ** 1.6)
        outline.append((x, Hh * (.92 - 1.92 * t)))
    for i in range(1, 16):
        t = 1 - i / 16
        outline.append((-W * (1 - t ** 1.6), Hh * (.92 - 1.92 * t)))
    outline = outline[:-1]
    R = Hh
    bulge = lambda u, v: .28 * W * (1 - (u / W) ** 2) * (1 - .3 * (v / Hh) ** 2)
    P = lambda u, v, h=0.0: add(add(add(o, mul(X, u)), mul(Y, v)), mul(N, h + bulge(u, v)))
    rows, uvs = [], []
    for k in range(5):                                    # the face: rings from the outline to the centre
        f = 1 - k / 4 * .98
        rows.append([P(u * f, v * f + (1 - f) * -.05 * Hh) for u, v in outline] + [P(outline[0][0] * f, outline[0][1] * f + (1 - f) * -.05 * Hh)])
        uvs.append([(.5 + .5 * u * f / R, .5 + .5 * (v * f + (1 - f) * -.05 * Hh) / R) for u, v in outline] +
                   [(.5 + .5 * outline[0][0] * f / R, .5 + .5 * (outline[0][1] * f) / R)])
    m.grid(rows, uvs, face, "SHIELD", wrap=True)
    ring = [P(u, v, .02) for u, v in outline] + [P(outline[0][0], outline[0][1], .02)]
    m.sweep(ring, [.16] * len(ring), rim, "SHIELD", sides=6)
    m.flat([add(add(add(o, mul(X, u)), mul(Y, v)), mul(N, -.1)) for u, v in outline][::-1], back, "SHIELD")
    for w in (-.35, .3):
        m.slab([add(add(o, mul(Y, Hh * w - .2)), add(mul(X, -W * .7), mul(N, -.18))),
                add(add(o, mul(Y, Hh * w - .2)), add(mul(X, W * .7), mul(N, -.18))),
                add(add(o, mul(Y, Hh * w + .2)), add(mul(X, W * .7), mul(N, -.18))),
                add(add(o, mul(Y, Hh * w + .2)), add(mul(X, -W * .7), mul(N, -.18)))], .07, mul(N, -1), strap, "SHIELD")


def shield_round(m, A, face=T.SUN, rim=T.GOLD, boss=T.GOLD, spike=T.STEEL, back=T.PLANKS, strap=T.LEATHER, studs=T.STEEL,
                 boss_r=.95):
    """Shield of the Mark: a round shield, Rohan's golden sun-wheel on a green field, a great
    domed boss, a gilded rim with sixteen steel studs, and a planked back."""
    c, X, Y, N = shield_frame(A)
    R = A["shield_size"][1] * 1.12
    o = add(c, mul(N, A["shield_off"]))
    f = (o, X, Y, N)
    m.shell(f, [(R * .98, R * .98, 0), (R, R, .1), (R * .9, R * .9, .26), (R * .7, R * .7, .4), (R * .42, R * .42, .5),
                (.02, .02, .55)], face, "SHIELD", sides=36, planar=R)
    pts = lambda r, h, n=36: [add(add(add(o, mul(X, r * math.cos(t))), mul(Y, r * math.sin(t))), mul(N, h))
                              for t in [TAU * i / n for i in range(n + 1)]]
    m.sweep(pts(R + .02, .05), [.17] * 37, rim, "SHIELD", sides=6)
    for k in range(16):
        t = TAU * k / 16
        m.stud(add(add(add(o, mul(X, (R - .25) * math.cos(t))), mul(Y, (R - .25) * math.sin(t))), mul(N, .16)), N, .09, studs,
               "SHIELD")
    m.shell((add(o, mul(N, .45)), X, Y, N), [(boss_r, boss_r, 0), (boss_r * .98, boss_r * .98, .12), (boss_r * .82, boss_r * .82, .42),
                                             (boss_r * .5, boss_r * .5, .66), (.02, .02, .76)], boss, "SHIELD", sides=20)
    m.sweep(pts(boss_r + .04, .47, 20), [.08] * 21, rim, "SHIELD", sides=6)
    if spike is not None:
        m.tube(add(o, mul(N, 1.1)), add(o, mul(N, 1.55)), .12, spike, "SHIELD", sides=6, r1=.01)
    m.flat(pts(R * .99, -.1, 36)[:-1][::-1], back, "SHIELD")
    for w in (-.6, .6):
        m.slab([add(add(o, mul(Y, w - .17)), add(mul(X, -R * .75), mul(N, -.18))),
                add(add(o, mul(Y, w - .17)), add(mul(X, R * .75), mul(N, -.18))),
                add(add(o, mul(Y, w + .17)), add(mul(X, R * .75), mul(N, -.18))),
                add(add(o, mul(Y, w + .17)), add(mul(X, -R * .75), mul(N, -.18)))], .07, mul(N, -1), strap, "SHIELD")


# ------------------------------------------------------------------ swords
def grip_frame(A):
    o, d, e = A["grip"]
    d = norm(d)
    e = norm(sub(e, mul(d, sum(a * b for a, b in zip(e, d)))))
    return o, d, e, cross(d, e)


def sword(m, A, length=12.6, width=.62, guard=1.6, droop=.35, pommel=T.GOLD, grip=T.GRIP, guard_tag=T.STEEL, blade=T.BLADE,
          gem=T.GEM, horse=False):
    """A longsword gripped like EA's: a fullered blade, a crossguard swept toward the blade, a
    wrapped grip and a pommel (a gem in Gondor's; a gilded horse's head in Rohan's)."""
    o, d, e, w = grip_frame(A)
    P = lambda t, s=0.0, q=0.0: add(add(add(o, mul(d, t)), mul(e, s)), mul(w, q))
    g0 = A["guard_at"]
    m.tube(P(g0 - 2.05), P(g0 - .05), .17, grip, "HAND", sides=8)
    for t in (g0 - 2.0, g0 - 1.0, g0 - .15):
        m.tube(P(t - .05), P(t + .05), .21, pommel, "HAND", sides=8)
    if horse:
        m.sweep([P(g0 - 2.1), P(g0 - 2.45, .05), P(g0 - 2.7, .25), P(g0 - 2.75, .55)], [.2, .19, .15, .1], pommel, "HAND", sides=8,
                squash=.6, up=w)
    else:
        m.shell((P(g0 - 2.35), d, e, w), [(.02, .02, -.28), (.24, .24, -.2), (.3, .3, 0), (.24, .24, .2), (.02, .02, .28)],
                pommel, "HAND", sides=8, keep=8)
        m.stud(P(g0 - 2.35, 0, .27), w, .12, gem, "HAND", h=.08)
    arm = [P(g0 + droop * (abs(k - 4) / 4) ** 1.5, guard * (k - 4) / 4) for k in range(9)]
    m.sweep(arm, [.13 + .05 * (abs(k - 4) / 4) for k in range(9)], guard_tag, "HAND", sides=6, squash=.7, up=w)
    m.stud(P(g0 + .05, 0, .12), w, .16, gem, "HAND", h=.08)
    lo = lambda s: g0 + .1
    hi = lambda s: g0 + length - .9 * (s / width) ** .8 - .1
    for sgn in (1, -1):
        m.blade(o, d, mul(e, sgn), mul(w, sgn), lo, hi, width, lambda s: .18 * max(0.0, 1 - s / width) ** .6, blade, "HAND",
                steps=(4, 10))
