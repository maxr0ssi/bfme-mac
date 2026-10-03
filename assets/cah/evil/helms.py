"""The Evil classes' serious helmets, each in its faction's building language (assets/<faction>):

- Mordor (F2: black iron, ember, a touch of hard steel): a faceted sallet under a Barad-dur crown of
  hooked spikes, a saw-toothed comb, the Eye in ember on the brow plate, a cloth aventail;
- Isengard (black iron edged in silver): a peaked Uruk kettle with a silver comb and the White Hand;
- Angmar (blue iron, frozen tips): a crown of tall tines curling back, rime on every point;
- Goblin (crimson, bone and skulls): a crimson cap under a horned beast skull;
- Harad (brass and crimson): a spired brass helm over a wrapped turban with a mail veil;
- Easterling (black lacquer and gold): a lamellar helm with a gold face mask and a wide neck guard.

All drawn on the unit skull guide (shapes.py); `of(m)` gives the model's anatomy.
"""
import math

from ..kit.geom import add, mul, norm
from .shapes import T, band, brow, dome, edge, emblem, of, patch, ring, spike, tine

(IRON, PLATE, STEEL, EMBER, EYE, CLOTH, WRAP, I_IRON, SILVER, HAND, A_IRON, ICE, TINE, CRIMSON, BONE, BRASS, TURBAN,
 RED, LAMELLAR, GOLD, MAIL, HAFT, GEM, BLADE, FUR, MORGUL, GRIP, BRASSORN, MASK, HOTPINK, PINKTIP, IRONORN) = range(32)

SALLET = [(1.04, -.32), (1.12, -.26), (1.15, .12), (1.08, .52), (.88, .86), (.52, 1.1), (.05, 1.2)]


def _eye_plate(m, A, x, z, w, h, tag=EYE):
    """A plate on the brow carrying a painted emblem, upright and facing out."""
    sk = A.head["s"]
    p = lambda y, zz, d=0.0: list(A.hp(x + d, y, zz))
    m.slab([p(-w, z - h * .5), p(w, z - h * .5), p(w * .8, z + h * .5), p(-w * .8, z + h * .5)], .05 * sk,
           (1, 0, .1), IRONORN if tag == EYE else tag, A.head_bone, bevel=.015 * sk)
    d = .03 * sk / max(A.head["r"][0], 1e-6)
    emblem(m, [p(-w * .8, z + h * .5, d), p(w * .8, z + h * .5, d), p(w, z - h * .5, d), p(-w, z - h * .5, d)], tag, A.head_bone)


def helm_mordor(m):
    """Helm of the Dark Tower: a faceted black-iron sallet on a riveted crown band, a Barad-dur
    crown of hooked steel-tipped spikes, a saw-toothed comb, the Eye in ember on the brow, jagged
    cheek plates and a cloth aventail (colour G) at the nape."""
    A = of(m)
    s, H = A.head["s"], A.head_bone
    dome(m, A, SALLET, IRON, sides=10, arc=(math.pi / 10, math.pi / 10 + T))
    band(m, A, 1.17, -.24, .12, PLATE, sides=20)
    edge(m, ring(A, 1.2, -.24, n=20), .05 * s, STEEL, H)
    for k in range(9):                                     # the crown: tallest at the brow
        t = (k - 4) * math.pi / 5.2
        if abs(t) > math.pi:
            continue
        h = 1.3 - .14 * abs(k - 4)
        base = (1.15 * math.cos(t), 1.15 * math.sin(t), .12 + brow(t))
        out = (math.cos(t) * .45, math.sin(t) * .45, 1.0)
        spike(m, A, base, out, h, .15, IRON, hook=.22, tip_tag=STEEL, up=(math.cos(t) * .9, math.sin(t) * .9, -.2))
    path = [(.9 - 1.9 * i / 8, 0, 1.18 - .45 * ((i / 8 - .4) ** 2)) for i in range(9)]   # saw-tooth comb
    for i in range(8):
        a, b = path[i], path[i + 1]
        tip = (b[0] + .05, 0, b[2] + .32)
        m.slab([list(A.hp(*a)), list(A.hp(*b)), list(A.hp(*tip))], .05 * s, (0, 1, 0), STEEL, H, bevel=.012 * s)
    _eye_plate(m, A, 1.17, -.05, .42, .3)
    for side in (1, -1):                                   # jagged cheek plates
        t0 = side * .9
        pts = [A.hp(1.1 * math.cos(t0 + side * a), 1.1 * math.sin(t0 + side * a), z) for a, z in
               ((0, -.2), (.5, -.2), (.55, -.72), (.3, -.95), (.12, -.7), (0, -.95))]
        m.slab([list(p) for p in pts[:4]], .06 * s, (math.cos(t0), math.sin(t0), 0), PLATE, H, bevel=.02 * s)
        m.slab([list(p) for p in (pts[0], pts[3], pts[4], pts[5])], .06 * s, (math.cos(t0), math.sin(t0), 0), PLATE, H,
               bevel=.02 * s)
    arc = (math.pi * .55, math.pi * 1.45)
    dome(m, A, [(1.22, -.95), (1.16, -.6), (1.1, -.28)], CLOTH, sides=14, rim=lambda t: -.12 * abs(math.sin(5 * t)),
         arc=arc, double=True)


IS_DOME = [(1.05, -.3), (1.12, -.22), (1.15, .15), (1.08, .55), (.88, .88), (.5, 1.14), (.05, 1.24)]


def helm_isengard(m):
    """Uruk-hai of Isengard: a black-iron helm rising to a tall silver-edged crest from brow to
    nape, a flared brim pointed over the eyes, a T-shaped nasal, cheek guards and nape lames, and
    the White Hand painted large across its brow."""
    A = of(m)
    s, H = A.head["s"], A.head_bone
    rim = lambda t: brow(t, .2)
    dome(m, A, IS_DOME, I_IRON, sides=20, rim=rim)
    patch(m, A, 1.165, -.12, .66, .62, HAND, n=8, rows=4)
    crest_lo = [A.hp(1.12 * math.cos(a) * (1.0 if a < math.pi / 2 else 1.0), 0, 1.2 * math.sin(a) + .05)
                for a in [math.pi * (.3 + .55 * i / 8) for i in range(9)]]
    crest_hi = [A.hp((1.12 + .55 * math.sin(math.pi * i / 8) ** .7) * math.cos(a), 0,
                     (1.2 + .55 * math.sin(math.pi * i / 8) ** .7) * math.sin(a) + .05)
                for i, a in enumerate([math.pi * (.3 + .55 * i / 8) for i in range(9)])]
    m.ribbon([list(p) for p in crest_lo], [list(p) for p in crest_hi], CLOTH, H, edge_r=.06 * s, edge_tag=SILVER)
    brim_in = [A.hp(1.1 * math.cos(t), 1.1 * math.sin(t), rim(t) - .26) for t in [T * i / 16 for i in range(17)]]
    brim_out = [A.hp((1.3 + .3 * max(0, math.cos(t)) ** 6) * math.cos(t), (1.3) * math.sin(t),
                     rim(t) - .4 - .06 * max(0, math.cos(t)) ** 6) for t in [T * i / 16 for i in range(17)]]
    m.grid([[list(p) for p in brim_in], [list(p) for p in brim_out]], [[(i / 16, k) for i in range(17)] for k in (0, 1)],
           I_IRON, H, double=True)
    edge(m, brim_out, .05 * s, SILVER, H)
    nasal = [A.hp(1.36, 0, -.3), A.hp(1.3, 0, -.65), A.hp(1.22, 0, -.95)]
    edge(m, nasal, .08 * s, SILVER, H, sides=4, squash=.5)
    for side in (1, -1):
        arc = (min(side * 1.15, side * 2.0), max(side * 1.15, side * 2.0))
        dome(m, A, [(1.2, -1.05), (1.18, -.6), (1.13, -.32)], I_IRON, sides=5, rim=None, arc=arc, double=True)
        edge(m, ring(A, 1.21, -1.05, n=5, a0=arc[0], a1=arc[1], rim=None, closed=False), .04 * s, SILVER, H)
    arc = (math.pi * .65, math.pi * 1.35)
    for k, (z0, z1, r) in enumerate(((-.66, -.36, 1.2), (-1.0, -.66, 1.26))):
        dome(m, A, [(r, z0), (r - .06, z1)], I_IRON, sides=9, rim=None, arc=arc, double=True)
        edge(m, ring(A, r + .02, z0, n=9, a0=arc[0], a1=arc[1], rim=None, closed=False), .04 * s, SILVER, H)


def helm_angmar(m):
    """Iron crown of Angmar: a blue-iron skullcap with a pointed brow, a crown band set with a cold
    blue gem and a ring of tall tines curling back, their tips frozen to rime."""
    A = of(m)
    s, H = A.head["s"], A.head_bone
    dome(m, A, [(1.04, -.25), (1.1, -.2), (1.12, .2), (1.02, .6), (.75, .95), (.3, 1.14), (.04, 1.18)], A_IRON, sides=18,
         rim=lambda t: brow(t, .25) + .22 * max(0, math.cos(t)) ** 12)
    band(m, A, 1.15, -.2, .14, A_IRON, sides=20, rim=lambda t: brow(t, .25))
    edge(m, ring(A, 1.18, .14, n=20, rim=lambda t: brow(t, .25)), .045 * s, ICE, H)
    for k in range(11):
        t = (k - 5) * math.pi / 5.5
        lead = abs(k - 5)
        length = 1.85 - .13 * lead + (.35 if lead == 0 else 0)
        base = (1.14 * math.cos(t), 1.14 * math.sin(t), .1 + brow(t, .25))
        out = (math.cos(t) * .2, math.sin(t) * .2, 1.0)
        tine(m, A, base, out, length, .12 if lead else .15, TINE, curl=.55 + .06 * lead)
    m.stud(list(A.hp(1.18, 0, .0)), (1, 0, .1), .17 * s, GEM, H, h=.12 * s, sides=6)
    m.stud(list(A.hp(1.2, 0, .0)), (1, 0, .1), .24 * s, ICE, H, h=.05 * s, sides=6)
    for side in (1, -1):                                   # cheek tines sweeping down
        tine(m, A, (1.0 * math.cos(side * 1.0), 1.0 * math.sin(side * 1.0), -.3), (.25, side * .3, -1), .75, .09, TINE, curl=-.2)


def helm_goblin(m):
    """Goblin skull-cap: a crimson-painted iron cap (chipped to the metal) under the bleached skull
    of a horned beast, its jaws over the brow, eye sockets dark, two horns sweeping back."""
    A = of(m)
    s, H = A.head["s"], A.head_bone
    dome(m, A, [(1.04, -.3), (1.1, -.24), (1.12, .1), (1.03, .5), (.8, .82), (.4, 1.02), (.04, 1.08)], CRIMSON, sides=16)
    edge(m, ring(A, 1.12, -.3, n=16), .07 * s, WRAP, H)
    for k in range(6):                                      # rivets round the rim
        t = k * T / 6 + .3
        m.stud(list(A.hp(1.13 * math.cos(t), 1.13 * math.sin(t), -.15 + brow(t))), (math.cos(t), math.sin(t), 0), .06 * s, IRON, H)
    # the skull on top: a cranium, a long muzzle over the brow, sockets
    secs = []
    for x, hw, z0, z1 in ((-.55, .45, .75, 1.25), (-.1, .62, .78, 1.42), (.35, .6, .76, 1.38), (.75, .42, .62, 1.1),
                          (1.1, .32, .45, .85), (1.35, .26, .36, .62)):
        zc, hz = (z0 + z1) / 2, (z1 - z0) / 2
        secs.append([list(A.hp(x, hw * math.cos(a), zc + hz * math.sin(a))) for a in [T * i / 10 for i in range(10)]])
    m.loft(secs, BONE, H, uv=lambda k, i: (i / 10, k / 5))
    for side in (1, -1):
        m.stud(list(A.hp(.82, side * .33, .98)), (.5, side * .8, .3), .14 * s, IRON, H, h=.02 * s, sides=6)
        horn = [A.hp(-.1, side * .55, 1.25), A.hp(-.25, side * 1.05, 1.5), A.hp(-.7, side * 1.45, 1.55),
                A.hp(-1.15, side * 1.5, 1.25), A.hp(-1.3, side * 1.3, .9)]
        m.sweep([list(p) for p in horn], [.2 * s, .17 * s, .13 * s, .08 * s, .02 * s], BONE, H, sides=7)
        for k in range(3):                                  # fangs over the brow
            m.tube(list(A.hp(1.2 - .2 * k, side * (.2 + .05 * k), .42)), list(A.hp(1.22 - .2 * k, side * (.18 + .05 * k), .1)),
                   .05 * s, BONE, H, sides=4, r1=.005 * s)


def helm_harad(m):
    """Helm of the Haradrim: a fluted brass spire on a crimson-and-cloth turban (colour G) wound in
    bands, an engraved brass brow plate, and a mail veil falling round the neck."""
    A = of(m)
    s, H = A.head["s"], A.head_bone
    dome(m, A, [(1.08, -.3), (1.2, -.18), (1.24, .1), (1.16, .38), (.95, .55)], TURBAN, sides=20,
         bump=lambda t, k: .05 * math.sin(6 * t + k * 1.3))
    dome(m, A, [(.98, .5), (.92, .78), (.7, 1.05), (.4, 1.35), (.15, 1.75), (.02, 2.1)], BRASS, sides=16,
         bump=lambda t, k: .035 * abs(math.cos(4 * t)) * (k < 4))
    edge(m, ring(A, .99, .5, n=16, rim=None), .05 * s, BRASS, H)
    m.stud(list(A.hp(0, 0, 2.08)), (0, 0, 1), .1 * s, GEM, H, h=.16 * s)
    _eye_plate(m, A, 1.2, -.02, .38, .34, BRASSORN)
    edge(m, [A.hp(1.24 * math.cos(t), 1.24 * math.sin(t), .12 + .04 * math.cos(t)) for t in [-.9 + 1.8 * i / 8 for i in range(9)]],
         .06 * s, RED, H)
    arc = (math.pi * .32, math.pi * 1.68)
    dome(m, A, [(1.28, -1.15), (1.2, -.7), (1.1, -.28)], MAIL, sides=24, rim=lambda t: -.1 * abs(math.sin(8 * t)), arc=arc,
         double=True)


def helm_easterling(m):
    """Easterling lamellar helm: black-lacquered lamellae laced in gold over a pointed gold crown,
    a gold face mask with stern brows, and a wide lamellar neck guard flaring to the shoulders."""
    A = of(m)
    s, H = A.head["s"], A.head_bone
    dome(m, A, [(1.06, -.25), (1.13, -.18), (1.15, .2), (1.06, .6), (.8, .95), (.4, 1.25), (.04, 1.5)], LAMELLAR, sides=16)
    edge(m, ring(A, 1.15, -.25, n=16), .05 * s, GOLD, H)
    for k in range(4):                                      # gold ribs to a finial
        t = k * math.pi / 2 + math.pi / 4
        rib = [A.hp(1.13 * math.cos(t) * r, 1.13 * math.sin(t) * r, z) for r, z in ((1.0, .1), (.92, .62), (.68, .98), (.34, 1.28), (.03, 1.5))]
        edge(m, rib, .04 * s, GOLD, H, sides=4)
    m.tube(list(A.hp(0, 0, 1.45)), list(A.hp(0, 0, 2.05)), .07 * s, GOLD, H, sides=6, r1=.005 * s)
    m.stud(list(A.hp(0, 0, 1.5)), (0, 0, 1), .14 * s, RED, H, h=.1 * s, sides=8)
    # the face mask: a gold plate over the face, stern brows, a slit mouth
    mask = []
    for z in (-.95, -.6, -.3, .02):
        w = .62 if z > -.8 else .45
        mask.append([list(A.hp(1.06 + .07 * (1 - abs(y)) - .1 * (z < -.7) - .25 * abs(y) ** 2, y * w * 1.3, z))
                     for y in [-1 + 2 * i / 6 for i in range(7)]])
    m.grid(mask, [[(i / 6, k / 3) for i in range(7)] for k in range(4)], MASK, H, double=True)
    for side in (1, -1):
        edge(m, [A.hp(1.24, side * .1, -.1), A.hp(1.22, side * .45, .0), A.hp(1.12, side * .8, .12)], .045 * s, GOLD, H, sides=4)
    arc = (math.pi * .38, math.pi * 1.62)
    rows = dome(m, A, [(1.55, -1.05), (1.38, -.75), (1.22, -.45), (1.14, -.24)], LAMELLAR, sides=22, rim=None, arc=arc,
                double=True)
    edge(m, rows[0], .04 * s, GOLD, H, sides=4)


__all__ = ["helm_mordor", "helm_isengard", "helm_angmar", "helm_goblin", "helm_harad", "helm_easterling"]
