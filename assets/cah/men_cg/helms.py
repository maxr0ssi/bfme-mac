"""The Men of the West's helmets, drawn once on a canonical head and seated on each subclass's own
head by its SEAT function (design.py): Gondor (the Citadel Guard, the winged helm of the kings,
an Ithilien hood), Dol Amroth's swan helm, Arnor's star crown, and the Rohirrim's helms (the
horse-crest, the Golden Hall's guard, the shieldmaiden's).

Canonical head space: origin at the head's centre at brow height, +X front, +Y the hero's left,
+Z up; the skull's crown at z 1.75, the face in front of x 1.1 between z -1.3 and 0.3. The bone is
the abstract "HEAD" (BONE_MAP names it per model). Tiles are the Men sheet's (paint.py).
"""
import math

from ..kit.geom import add, cross, mul, norm, sub
from . import paint as T

HEAD = ((0.0, 0.0, 0.0), [1, 0, 0], [0, 1, 0], [0, 0, 1])
H = "HEAD"
TAU = 2 * math.pi


def brow(t):
    """The rim rises over the eyes and drops over the nape."""
    return .18 * math.cos(t) - .06


def ring(rx, ry, z, n=32, a0=0.0, a1=TAU, rim=brow, closed=True, cx=0.0):
    pts = [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), ry * math.sin(a0 + (a1 - a0) * i / n),
            z + (rim(a0 + (a1 - a0) * i / n) if rim else 0)) for i in range(n + (0 if closed else 1))]
    return pts + [pts[0]] if closed else pts


def edge(m, pts, r, tag, bone=H, sides=6, squash=1.0):
    m.sweep(pts, [r] * len(pts), tag, bone, sides=sides, squash=squash)


def along(profile, t, lift=0.0, start=0, rim=brow):
    """The dome's surface line at angle t, bottom to top, `lift` above it."""
    return [((rx + lift) * math.cos(t), (ry + lift) * math.sin(t), z + (rim(t) if rim and k == 0 else 0))
            for k, (rx, ry, z) in enumerate(profile[start:], start)]


def band(m, rx, ry, z0, z1, tag, sides=32, rim=brow):
    """A vertical band whose rings follow the brow line, with bevelled edges."""
    n = m._sides(sides)
    th = [TAU * i / n for i in range(n + 1)]
    prof = [(rx - .03, ry - .03, z0), (rx, ry, z0 + .04), (rx, ry, z1 - .04), (rx - .03, ry - .03, z1)]
    if m.lod < .8:
        prof = [prof[0], prof[3]]
    rows = [[(r_x * math.cos(t), r_y * math.sin(t), z + rim(t)) for t in th] for r_x, r_y, z in prof]
    uvs = [[(i / n, k / (len(prof) - 1)) for i in range(n + 1)] for k in range(len(prof))]
    m.grid(rows, uvs, tag, H, wrap=True)


def fin(m, path, heights, thick, tag, centre, edge_tag=T.STEEL):
    """A crest standing on `path` (points on the dome), outward from `centre`, rolled edge on top."""
    tops = [add(p, mul(norm(sub(p, centre)), h)) for p, h in zip(path, heights)]
    if m.lod >= .8:
        for a, b, ta, tb in zip(path, path[1:], tops, tops[1:]):
            m.slab([a, b, tb, ta], thick, (0, 1, 0), tag, H, bevel=.02)
    else:
        m.ribbon(path, tops, tag, H)
    edge(m, tops, thick * .55, edge_tag)


def plate(m, outline, normal, tag, bone=H, thick=.03):
    """A thin plate seen from both sides: the convex outline twice, `thick` apart, facing out."""
    n = norm(normal)
    a, b, c = outline[:3]
    if sum(x * y for x, y in zip(cross(sub(b, a), sub(c, a)), n)) < 0:
        outline = outline[::-1]
    m.flat([add(p, mul(n, thick / 2)) for p in outline], tag, bone)
    m.flat([add(p, mul(n, -thick / 2)) for p in outline[::-1]], tag, bone)


def wing(m, base, s, feathers, length, rise, spread, tag, sweep=.85, width=.2, out=.28, twist=40):
    """A seabird wing of feathers fanned from `base` on side s (+1 left): each feather a pointed
    plate, the longest in the middle, swept back by `sweep`, leaning out by `out`; the wing's plane
    turned `twist` degrees from the helm's side toward the front so it reads from the front too."""
    tw = math.radians(twist)
    nref = norm((math.sin(tw), s * math.cos(tw), 0))
    for k in range(feathers):
        f = k / max(1, feathers - 1)
        a = math.radians(spread[0] + (spread[1] - spread[0]) * f)
        L = length * (.62 + .38 * math.sin(math.pi * (.35 + .65 * f)))
        d = norm((-math.cos(a) * sweep, s * out, math.sin(a) * rise))
        side = norm(cross(d, nref))
        b0 = add(base, (-.05 * k, s * .025 * k, .03 * k))
        tip = add(b0, mul(d, L))
        mid = add(b0, mul(d, L * .55))
        plate(m, [add(b0, mul(side, width * .45)), add(mid, mul(side, width)), tip, add(mid, mul(side, -width * .6)),
                  add(b0, mul(side, -width * .45))], nref, tag)


def cheeks(m, rx, ry, z0, z1, centre, half, tag, trim=T.STEEL, rivets=2):
    for s in (1, -1):
        c = s * centre
        m.shell(HEAD, [(rx + .05, ry + .05, z0), (rx, ry, (z0 + z1) / 2), (rx - .03, ry - .03, z1)], tag, H, sides=8,
                arc=(c - half, c + half), double=True)
        edge(m, [((rx + .08) * math.cos(c + a), (ry + .08) * math.sin(c + a), z0) for a in
                 [half * (2 * i / 6 - 1) for i in range(7)]], .05, trim)
        for k in range(rivets):
            a = c + half * (k - (rivets - 1) / 2) * .7
            m.stud(((rx + .02) * math.cos(a), (ry + .02) * math.sin(a), z1 - .15), (math.cos(a), math.sin(a), 0), .06, trim,
                   H, sides=6)


def nasal(m, x, top, bottom, w_top, w_bot, tag, ridge=T.STEEL, thick=.1):
    m.slab([(x, -w_top, top), (x, w_top, top), (x + .08, w_bot, bottom), (x + .08, -w_bot, bottom)], thick, (1, 0, .1), tag, H)
    edge(m, [(x + .06, 0, top), (x + .12, 0, bottom + .04)], .04, ridge)


def nape(m, rx, ry, z0, z1, tag, trim=T.STEEL, arc=(math.pi * .6, math.pi * 1.4)):
    m.shell(HEAD, [(rx + .2, ry + .2, z0), (rx + .08, ry + .08, (z0 + z1) / 2), (rx, ry, z1)], tag, H, sides=18, arc=arc,
            double=True)
    edge(m, ring(rx + .22, ry + .22, z0, n=14, a0=arc[0], a1=arc[1], rim=None, closed=False), .05, trim)


DOME = [(1.56, 1.43, -.02), (1.64, 1.5, .1), (1.66, 1.52, .5), (1.62, 1.48, .92), (1.5, 1.37, 1.3), (1.27, 1.16, 1.63),
        (.92, .84, 1.88), (.48, .44, 2.02), (.04, .04, 2.06)]


def dome(m, tag, prof=DOME, sides=32, bump=None):
    return m.shell(HEAD, prof, tag, H, sides=sides, rim=brow, bump=bump)


def lip(m, tag, rx=1.7, ry=1.56, r=.07):
    edge(m, ring(rx, ry, .0), r, tag, sides=6)


def ridge(m, prof, tag, r=.07, start=2, lift=.02):
    path = along(prof, 0, lift, start=start)[:-1] + along(prof, math.pi, lift, start=start)[::-1][1:]
    m.sweep(path, [r] * len(path), tag, H, sides=6, squash=.6)
    return path


def ribs(m, prof, n, tag, r=.06, start=1, a0=0.0):
    n = n if m.lod >= .7 or n < 6 else n // 2           # trimmed: every other rib
    for k in range(n):
        strip = along(prof, a0 + TAU * k / n, .025, start=start)[:-1]
        m.sweep(strip, [r] * len(strip), tag, H, sides=6, squash=.45)


# ------------------------------------------------------------------ Gondor
CIT = [(1.56, 1.43, -.02), (1.64, 1.5, .1), (1.66, 1.52, .55), (1.62, 1.47, 1.05), (1.49, 1.33, 1.55), (1.25, 1.08, 2.0),
       (.88, .74, 2.38), (.45, .38, 2.6), (.04, .04, 2.68)]


def helm_citadel(m):
    """Helm of the Citadel Guard: the tall sable helm of the Tower Guard, a high steel crest from
    brow to nape, silver seabird wings swept up from the temples, long cheek guards, a steel brow
    band and a nape guard."""
    dome(m, T.ENAMEL, CIT)
    band(m, 1.69, 1.55, .0, .3, T.STEEL)
    lip(m, T.STEEL, 1.71, 1.57, .06)
    path = along(CIT, 0, -.02, start=1)[:-1] + along(CIT, math.pi, -.02, start=1)[::-1][1:]
    n = len(path)
    fin(m, path, [.1 + .5 * max(0.0, math.sin(math.pi * i / (n - 1))) ** .7 for i in range(n)], .08, T.STEEL, (0, 0, .5))
    for s in (1, -1):
        wing(m, (.15, s * 1.52, .35), s, 6, 1.9, 1.3, (18, 88), T.WINGS, width=.24, sweep=.9, out=.3, twist=55)
        m.stud((.2, s * 1.66, .3), (0, s, .1), .17, T.STEEL, H, h=.1, sides=8)
    cheeks(m, 1.69, 1.55, -1.2, .02, math.pi / 2 * .7, .44, T.ENAMEL, rivets=3)
    nape(m, 1.62, 1.48, -1.0, .0, T.ENAMEL)
    nasal(m, 1.7, .3, -.55, .13, .09, T.STEEL)


KING = [(1.56, 1.43, -.02), (1.64, 1.5, .1), (1.67, 1.53, .6), (1.65, 1.5, 1.15), (1.55, 1.4, 1.7), (1.36, 1.22, 2.2),
        (1.04, .93, 2.6), (.6, .54, 2.84), (.04, .04, 2.92)]


def helm_king(m):
    """Winged Helm of the Kings: the tall white crown-helm of Gondor, ribbed in gold, a gold band
    set with seven gems and a star on the brow, and great seabird wings rising from the temples."""
    dome(m, T.MITHRIL, KING)
    ribs(m, KING, 8, T.GOLD, .05, start=1, a0=TAU / 16)
    band(m, 1.7, 1.56, .02, .44, T.GOLDBAND)
    lip(m, T.GOLD, 1.72, 1.58, .06)
    edge(m, ring(1.72, 1.58, .44), .05, T.GOLD)
    for k in (range(7) if m.lod >= .5 else (1, 3, 5)):
        t = (k - 3) * .5
        m.stud((1.73 * math.cos(t), 1.59 * math.sin(t), .23 + brow(t)), (math.cos(t), math.sin(t), 0), .13 if k == 3 else .09,
               T.GEM, H, h=.08)
    for k in range(5 if m.lod >= .5 else 0):         # a star of white gold above the brow
        a = math.pi / 2 + TAU * k / 5
        plate(m, [(1.66, 0, 1.0), (1.64, .36 * math.cos(a - .2), 1.0 + .36 * math.sin(a - .2)),
                  (1.62, .42 * math.cos(a), 1.0 + .42 * math.sin(a)), (1.64, .36 * math.cos(a + .2), 1.0 + .36 * math.sin(a + .2))],
              (1, 0, .1), T.GOLD, thick=.05)
    m.stud((1.7, 0, 1.0), (1, 0, .1), .12, T.GEM, H, h=.08)
    for s in (1, -1):
        wing(m, (.0, s * 1.56, .6), s, 7 if m.lod >= .5 else 5, 2.7, 1.5, (20, 96), T.WINGS, width=.32, sweep=.8, out=.32,
             twist=55)
        m.stud((.05, s * 1.68, .55), (0, s, .1), .2, T.GOLD, H, h=.12, sides=8)
    cheeks(m, 1.69, 1.55, -.95, .02, math.pi / 2 * .74, .36, T.MITHRIL, trim=T.GOLD)
    nape(m, 1.62, 1.48, -.8, .0, T.MITHRIL, trim=T.GOLD)


HOOD = [(1.5, 1.52, -1.6), (1.66, 1.64, -.9), (1.82, 1.74, -.1), (1.84, 1.72, .7), (1.7, 1.58, 1.4), (1.36, 1.26, 1.98),
        (.85, .78, 2.3), (.04, .04, 2.42)]


def hood_ithilien(m):
    """Ithilien Ranger's Hood: a deep hood of forest cloth close round the head, open at the face
    and drawn to a peak behind, hemmed in a darker band, with a cloth mask up to the nose."""
    opening = 1.0
    rows = m.shell(HEAD, HOOD, T.HOODCLOTH, H, sides=28, arc=(opening, TAU - opening), double=True,
                   bump=lambda t, k: .04 * math.sin(7 * t) * (k < 3))
    edge(m, [r[0] for r in rows[:-1]] + [r[-1] for r in rows[:-1]][::-1], .08, T.MASK)
    peak = [(-1.15, 0, 1.6), (-1.75, 0, 1.75), (-2.3, 0, 1.2), (-2.5, 0, .3)]
    m.sweep(peak, [.55, .42, .26, .05], T.HOODCLOTH, H, sides=8, squash=.45, up=[0, 1, 0])
    arc = (-1.25, 1.25)
    m.shell(HEAD, [(1.6, 1.55, -1.45), (1.58, 1.52, -.95), (1.5, 1.45, -.5), (1.42, 1.4, -.32)], T.MASK, H, sides=14, arc=arc,
            double=True)
    edge(m, ring(1.44, 1.42, -.32, n=12, a0=arc[0], a1=arc[1], rim=None, closed=False), .04, T.MASK)


SWAN = [(1.56, 1.43, -.02), (1.64, 1.5, .1), (1.66, 1.52, .55), (1.6, 1.46, 1.0), (1.44, 1.31, 1.42), (1.15, 1.04, 1.76),
        (.7, .63, 1.98), (.04, .04, 2.06)]


def helm_swan(m):
    """Swan Helm of Dol Amroth: a silver helm on a sea-blue band; a white swan sits on the crown,
    its neck curving up and forward over the brow, its wings swept back along the sides."""
    dome(m, T.STEEL, SWAN)
    band(m, 1.69, 1.55, .02, .4, T.SEABAND)
    lip(m, T.STEEL, 1.71, 1.57, .06)
    edge(m, ring(1.71, 1.57, .4), .05, T.STEEL)
    body = [(-.9, 0, 1.85), (-.4, 0, 2.15), (.25, 0, 2.2), (.75, 0, 2.05)]
    m.sweep(body, [.2, .5, .48, .25], T.FEATHER, H, sides=10, squash=.75, up=[0, 1, 0])
    neck = [(.7, 0, 2.1), (1.1, 0, 2.55), (1.12, 0, 3.15), (.9, 0, 3.6), (.95, 0, 3.95), (1.25, 0, 4.08)]
    m.sweep(neck, [.26, .2, .17, .16, .19, .16], T.FEATHER, H, sides=8)
    m.sweep([(1.28, 0, 4.08), (1.68, 0, 3.98)], [.11, .03], T.GOLD, H, sides=6)
    for s in (1, -1):
        m.stud((1.27, s * .15, 4.13), (0, s, 0), .05, T.BLACKG, H, h=.03, sides=4)
        wing(m, (.2, s * .45, 2.15), s, 6, 2.2, .55, (8, 32), T.FEATHER, width=.26, sweep=1.0, out=.6)
    cheeks(m, 1.69, 1.55, -.9, .02, math.pi / 2 * .74, .36, T.STEEL)
    nasal(m, 1.7, .3, -.55, .14, .1, T.STEEL)


ARN = [(1.56, 1.43, -.02), (1.64, 1.5, .1), (1.66, 1.52, .5), (1.6, 1.46, .95), (1.45, 1.32, 1.35), (1.18, 1.07, 1.68),
       (.78, .71, 1.92), (.36, .33, 2.04), (.04, .04, 2.07)]


def helm_arnor(m):
    """Star Crown of Arnor: an open helm of dark steel fluted in eight, on a night-blue band with silver
    stars; a crown of seven bright silver star points, and the Elendilmir, a white star-gem, bound
    on the brow."""
    dome(m, T.IRON, ARN, bump=lambda t, k: .05 * abs(math.cos(4 * t)) ** 3 * (1 < k < 7))
    ribs(m, ARN, 8, T.MITHRIL, .045, start=1)
    band(m, 1.69, 1.55, .02, .46, T.STARBAND)
    lip(m, T.MITHRIL, 1.71, 1.57, .06)
    edge(m, ring(1.71, 1.57, .46), .05, T.MITHRIL)
    for k in range(7):                               # star points standing round the front of the crown
        t = math.pi * (k - 3) / 4.5
        c, s = math.cos(t), math.sin(t)
        tx, ty = -s, c
        P = lambda w, z: (1.73 * c + w * tx, 1.59 * s + w * ty, z + brow(t))
        hgt = 1.15 if k == 3 else .75 + .07 * (3 - abs(k - 3))
        plate(m, [P(-.2, .44), P(.2, .44), P(.06, .44 + hgt * .55), P(0, .44 + hgt), P(-.06, .44 + hgt * .55)], (c, s, 0),
              T.WHITE, thick=.06)
        m.stud(P(0, .44 + hgt * .42), (c, s, .1), .07, T.GEM, H, h=.05)
    for k in range(4):                               # the Elendilmir: a four-rayed star on the brow
        a = math.pi / 4 + math.pi / 2 * k
        plate(m, [(1.76, 0, .24), (1.76, .3 * math.cos(a - .25), .24 + .3 * math.sin(a - .25)),
                  (1.76, .4 * math.cos(a), .24 + .4 * math.sin(a)), (1.76, .3 * math.cos(a + .25), .24 + .3 * math.sin(a + .25))],
              (1, 0, 0), T.WHITE, thick=.05)
    m.stud((1.79, 0, .24), (1, 0, 0), .14, T.WHITE, H, h=.1)
    nape(m, 1.62, 1.48, -.75, .0, T.IRON, trim=T.MITHRIL)


# ------------------------------------------------------------------ Rohan
RH = [(1.56, 1.43, -.02), (1.64, 1.5, .1), (1.66, 1.52, .55), (1.6, 1.46, 1.05), (1.43, 1.3, 1.5), (1.13, 1.02, 1.9),
      (.7, .63, 2.18), (.3, .27, 2.34), (.04, .04, 2.4)]


def plume(m, start, tag, length=1.0, width=1.0):
    """A horsehair tail flowing back from the crest and down past the nape."""
    x, y, z = start
    path = [(x, y, z), (x - .5, y, z + .35 * length), (x - 1.3, y, z + .3 * length), (x - 2.0, y, z - .25 * length),
            (x - 2.4, y, z - 1.2 * length), (x - 2.5, y, z - 2.3 * length), (x - 2.45, y, z - 3.1 * length)]
    m.sweep(path, [w * width for w in (.22, .36, .42, .4, .36, .27, .06)], tag, H, sides=10, squash=.75, up=[0, 1, 0])


HORSE = ([(0, 0), (.32, 0), (.38, .55), (.12, .95), (-.06, .62)],                    # neck
         [(.12, .95), (.38, .55), (.74, .36), (.9, .5), (.72, .74), (.42, .97)],     # head
         [(.12, .92), (.15, 1.22), (.28, .99)])                                       # ear


def horse_head(m, base, k, tag, mane=None):
    """Rohan's horse's head standing on the helm's crest line (side view in x/z, `k` tall)."""
    bx, _, bz = base
    for poly in HORSE:
        pts = [(bx + k * x, 0, bz + k * z) for x, z in poly]
        if m.lod >= .7:
            m.slab(pts, .16, (0, 1, 0), tag, H, bevel=.03)
        else:
            plate(m, pts, (0, 1, 0), tag, thick=.12)
    if mane is not None:
        m.sweep([(bx - .06 * k, 0, bz + .1 * k), (bx - .07 * k, 0, bz + .6 * k), (bx + .1 * k, 0, bz + .97 * k)],
                [.09, .1, .06], mane, H, sides=6, squash=.6, up=[0, 1, 0])
    for s in (1, -1):
        m.stud((bx + .52 * k, s * .09, bz + .72 * k), (0, s, 0), .05, T.BLACKG, H, h=.03, sides=4)


def helm_eorl(m, hair=T.HORSEHAIR, plate_tag=T.STEEL, gilt=T.GOLD):
    """Helm of the Eorlingas: a steel helm in gilded spangen on a knotwork band, a golden horse's
    head standing on the brow, a horsehair tail flowing from the crest, knotwork cheek plates."""
    dome(m, plate_tag, RH)
    band(m, 1.69, 1.55, .02, .36, T.KNOTGOLD)
    lip(m, gilt, 1.71, 1.57, .06)
    ribs(m, RH, 6, gilt, .07, start=1, a0=TAU / 12)
    path = ridge(m, RH, gilt, .1, start=3)
    horse_head(m, (1.12, 0, 1.15), 1.25, gilt, mane=hair)
    plume(m, (-.2, 0, 2.38), hair, .62, .85)
    cheeks(m, 1.69, 1.55, -1.05, .02, math.pi / 2 * .74, .42, T.KNOTGOLD, trim=gilt)
    nasal(m, 1.7, .3, -.5, .13, .09, plate_tag, ridge=gilt)
    nape(m, 1.62, 1.48, -.7, .0, plate_tag, trim=gilt)


GG = [(1.56, 1.43, -.02), (1.64, 1.5, .1), (1.66, 1.52, .5), (1.58, 1.44, 1.0), (1.38, 1.25, 1.5), (1.04, .94, 1.98),
      (.64, .58, 2.42), (.3, .27, 2.78), (.08, .07, 3.05), (.02, .02, 3.2)]


def helm_guard(m):
    """Helm of the Golden Hall: the royal guard's tall gilded helm rising to a spike, engraved
    knotwork bands, a long nasal, cheek plates, and a white horsetail falling from the spike."""
    dome(m, T.GILT, GG)
    band(m, 1.69, 1.55, .02, .42, T.KNOTGOLD)
    lip(m, T.GOLD, 1.71, 1.57, .06)
    edge(m, ring(1.71, 1.57, .42), .05, T.GOLD)
    ribs(m, GG, 4, T.GOLD, .08, start=1, a0=TAU / 8)
    m.stud((0, 0, 3.1), (0, 0, 1), .22, T.GOLD, H, h=.2, sides=8)
    hair = [(0, 0, 3.25), (-.35, 0, 3.5), (-.95, 0, 3.35), (-1.5, 0, 2.7), (-1.85, 0, 1.7), (-2.05, 0, .55), (-2.1, 0, -.6)]
    m.sweep(hair, [.13, .24, .3, .32, .3, .22, .05], T.WHITEHAIR, H, sides=10, squash=.55, up=[0, 1, 0])
    nasal(m, 1.7, .4, -.8, .16, .11, T.GILT, ridge=T.GOLD)
    cheeks(m, 1.69, 1.55, -1.15, .02, math.pi / 2 * .75, .44, T.KNOTGOLD, trim=T.GOLD, rivets=3)
    nape(m, 1.62, 1.48, -.85, .0, T.GILT, trim=T.GOLD)


SH = [(1.56, 1.43, -.02), (1.63, 1.49, .1), (1.64, 1.5, .5), (1.57, 1.43, .98), (1.38, 1.26, 1.45), (1.05, .96, 1.86),
      (.62, .57, 2.16), (.2, .18, 2.34), (.02, .02, 2.4)]


def helm_shieldmaiden(m):
    """Shieldmaiden's Helm: a light steel helm rising to a point, a green-enamelled brow band in
    gold, swept cheek guards laid back like a horse's ears, and a short mail curtain."""
    dome(m, T.STEEL, SH)
    band(m, 1.67, 1.53, .02, .32, T.ENAMEL)
    lip(m, T.GOLD, 1.69, 1.55, .055)
    edge(m, ring(1.69, 1.55, .32), .05, T.GOLD)
    ridge(m, SH, T.GOLD, .07, start=2)
    m.stud((0, 0, 2.38), (0, 0, 1), .15, T.GOLD, H, h=.2, sides=8)
    for s in (1, -1):
        c = s * math.pi / 2 * .72
        m.shell(HEAD, [(1.72, 1.58, -.95), (1.68, 1.54, -.45), (1.66, 1.52, .02)], T.STEEL, H, sides=8, arc=(c - .4, c + .4),
                double=True, rim=lambda t: .25 * math.sin(t - c) * s)
        edge(m, [(1.76 * math.cos(c + a), 1.62 * math.sin(c + a), -.95 + .25 * math.sin(a) * s) for a in
                 [.4 * (2 * i / 6 - 1) for i in range(7)]], .045, T.GOLD)
    arc = (math.pi * .45, math.pi * 1.55)
    m.shell(HEAD, [(1.84, 1.68, -1.1), (1.75, 1.6, -.5), (1.65, 1.51, .0)], T.MAIL, H, sides=22, arc=arc, double=True,
            rim=lambda t: -.12 * abs(math.sin(8 * t)))
