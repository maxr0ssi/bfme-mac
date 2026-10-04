"""The Captain of Erebor's helm and pauldrons, drawn with the CaH dwarf's helpers and tiles
(assets/cah/dwarf/serious.py, its sheet painted from the Dwarven palette), in the CaH dwarf's head
space (seated on the head by serious.helm_fit).

Dark blue-steel, gold only as trim: a rounded skull in eight faint facets under a low ridge crest,
a gold-runed band of Erebor blue (it takes the player's colour), a heavy brow guard over the eyes,
a long nasal with a gold ridge, cheek plates curving in to the jaw, a nape guard; on the shoulders
blue-steel domes with gold rims and lames.
"""
import math

from assets.cah.dwarf import serious as SR
from assets.cah.dwarf.serious import (BLUESTEEL, CX, GEM, GOLD, H, HEAD, HEXBRONZE, RUNEBAND, STEEL, along, band_shell,
                                      brow, edge, fin, nasal2, ring)
from assets.cah.kit.geom import add, mul

DOME = [(2.20, 2.00, 15.90), (2.33, 2.13, 16.02), (2.35, 2.15, 16.55), (2.30, 2.10, 17.1), (2.12, 1.95, 17.68),
        (1.80, 1.66, 18.2), (1.30, 1.20, 18.62), (.68, .63, 18.9), (.05, .05, 19.0)]


def dain_fit(p):
    """Seat a helm drawn on the CaH head guide on King Dain's head, which is larger than the CaH
    dwarf's (its brow 0.3 further forward, its crown 0.7 higher): centred over Dain's skull, the
    band on his brow, tilted up at the front as the CaH seat is."""
    x, y, z = p
    return (0.32 + (x - CX) * 0.97, y * 0.95, z + 0.7 + 0.26 * (x - CX) / 2.3)


def facets(t, k):
    """Eight faint facets on the skull (the plates' raised centres), none on the band row."""
    return .05 * abs(math.cos(4 * t)) ** 4 * (k > 1)


def cheek_plates(m, z0=14.45, z1=16.0):
    """Cheek plates curving round the face: broad under the band, tapering to a point at the jaw
    (EA's Dain wears pointed guards), domed out a little, gold-edged and riveted."""
    centre = math.pi / 2 * .8
    K, J = 7, 6
    for s in (1, -1):
        rows, uvs = [], []
        for k in range(K + 1):
            f = k / K                                   # 0 at the band, 1 at the tip
            z = z1 - (z1 - z0) * f
            half = .4 * (1 - f) ** .8 + .03
            r = 2.42 + .1 * math.sin(math.pi * min(1, f * 1.3)) - .16 * f * f   # out over the cheek, in at the jaw
            row = []
            for i in range(J + 1):
                a = s * centre + half * (2 * i / J - 1)
                bulge = .05 * math.cos(math.pi * (i / J - .5))
                row.append((CX + (r + bulge) * math.cos(a), (r * .92 + bulge) * math.sin(a), z))
            rows.append(row)
            uvs.append([(i / J, f) for i in range(J + 1)])
        m.grid(rows, uvs, BLUESTEEL, H, double=True)
        for col in (0, J):                              # gold along both edges to the point
            edge(m, [(p[0] * 1.01, p[1] * 1.01, p[2]) for p in [r[col] for r in rows]], .05, GOLD)
        edge(m, [(p[0] * 1.01, p[1] * 1.01, p[2]) for p in rows[1][1:-1]], .04, GOLD)
        for k in (2, 4):
            mid = rows[k][J // 2]
            n = (mid[0] - CX, mid[1], 0)
            m.stud((mid[0] + .03 * math.cos(s * centre), mid[1] + .03 * math.sin(s * centre), mid[2]), n, .075, GOLD, H, sides=6)


def helm_captain(m):
    """The Captain of Erebor's helm."""
    m.shell(HEAD, DOME, BLUESTEEL, H, sides=40, rim=brow, bump=facets)
    for k in range(8):                              # the facets' seams, thin gilt lines from band to crown
        t = k * math.pi / 4 + math.pi / 8
        strip = along(DOME, t, .025, start=2)[:-2]
        m.sweep(strip, [.035] * len(strip), GOLD, H, sides=4, squash=.5)
    band_shell(m, 2.40, 2.20, 15.98, 16.62, RUNEBAND)
    edge(m, ring(2.44, 2.24, 15.98), .08, GOLD)
    edge(m, ring(2.43, 2.23, 16.62), .065, GOLD)
    front = along(DOME, 0.0, 0.0, start=3)
    back = along(DOME, math.pi, 0.0, start=3)
    path = front[:-1] + back[::-1][1:]
    n = len(path)
    fin(m, path, [.16 + .42 * math.sin(math.pi * i / (n - 1)) for i in range(n)], .13, BLUESTEEL, (CX, 0, 16.3))
    for s in (1, -1):                               # the brow guard, a heavy rolled arch over each eye
        arch = [(CX + 2.5 * math.cos(s * a), 2.3 * math.sin(s * a), 16.05 + brow(a) + .12 * math.sin(math.pi * a / .95))
                for a in [.06 + .89 * i / 10 for i in range(11)]]
        m.sweep(arch, [.13] * len(arch), BLUESTEEL, H, sides=8, squash=.55)
        edge(m, [add(p, (.06, 0, .07)) for p in arch], .04, GOLD)
    nasal2(m, 2.45, 16.5, 15.55, 14.95, .2, .12, .17, BLUESTEEL)
    m.stud((CX + 2.47, 0, 16.25 + brow(0)), (1, 0, .15), .2, GOLD, H, h=.1, sides=8)
    m.stud((CX + 2.52, 0, 16.27 + brow(0)), (1, 0, .15), .11, GEM, H, h=.08, sides=6)
    cheek_plates(m)
    arc = (math.pi * .66, math.pi * 1.34)           # the nape guard: two lames
    for z0, z1, r in ((15.45, 15.95, 2.42), (14.95, 15.45, 2.56)):
        m.shell(HEAD, [(r, r * .92, z0), (r - .14, (r - .14) * .92, z1)], BLUESTEEL, H, sides=16, arc=arc, double=True)
        edge(m, ring(r + .02, (r + .02) * .92, z0, n=16, a0=arc[0], a1=arc[1], rim=None, closed=False), .05, GOLD)


def pauldrons_captain(m):
    """Blue-steel shoulder domes, a gold rim, a hexagonal boss, three lames, as the Erebor pauldrons
    of the CaH dwarf (assets/cah/dwarf/serious.py) in the Captain's steel."""
    K = .85
    for s, bone in ((1, "BAT_UARML"), (-1, "BAT_UARMR")):
        f = SR._shoulder_frame(s)
        prof = [(a * K, b * K, c * K) for a, b, c in [(2.15, 1.85, 0), (2.18, 1.88, .28), (1.98, 1.70, .78), (1.50, 1.30, 1.2),
                                                       (.85, .75, 1.45), (.05, .05, 1.55)]]
        m.shell(f, prof, BLUESTEEL, bone, sides=28)
        o, X, Y, Z = f
        rim = [add(add(add(o, mul(X, 2.2 * K * math.cos(t))), mul(Y, 1.9 * K * math.sin(t))), mul(Z, .1))
               for t in [2 * math.pi * i / 28 for i in range(29)]]
        edge(m, rim, .08, GOLD, bone)
        top = add(o, mul(Z, 1.5 * K))
        m.stud(top, Z, .36, HEXBRONZE, bone, h=.16, sides=6)
        m.stud(add(top, mul(Z, .14)), Z, .18, GEM, bone, h=.12, sides=6)
        for k, a_ in enumerate((1.0, 1.65, 2.3)):
            fo, fX, fY, fZ = SR._arm_frame(s, a_)
            r = (1.6 - .13 * k) * .92
            arc = SR._outer_arc(s)
            m.shell((fo, fX, fY, fZ), [(r, r * .95, 0), (r - .05, (r - .05) * .95, .58)], BLUESTEEL, bone, sides=14, arc=arc,
                    double=True)
            pts = [add(add(add(fo, mul(fX, (r + .02) * math.cos(t))), mul(fY, (r + .02) * .95 * math.sin(t))), mul(fZ, .58))
                   for t in [arc[0] + (arc[1] - arc[0]) * i / 14 for i in range(15)]]
            edge(m, pts, .045, GOLD, bone)


def tiles():
    """The CaH dwarf's tiles with the Captain's darker blue-steel: forged at a lower value, engraved
    with vertical panel lines and rows of rivets (the CaH helmets' BLUESTEEL is a light cap)."""
    from assets.cah.dwarf import paint as DP
    from assets.cah.kit import ornament as O
    t = dict(DP.TILES)
    t[BLUESTEEL] = ("bluesteel", .44, .32, "v", None,
                    {"engrave": (["line %d,0 %d,256" % (64 * k, 64 * k) for k in range(5)] + O.border(18), 2),
                     "rivet": (O.rivets_row(30, 8) + O.rivets_row(226, 8), 2)})
    return t
