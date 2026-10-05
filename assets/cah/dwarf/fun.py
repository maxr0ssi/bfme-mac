"""The fun choices: well made and clearly silly, readable at the RTS camera. Most ignore the hero's
three colours on purpose (a pink cape is pink); the jester and party hats still take them.

They draw from their own sheet (SKCAH_DWFUN.tga, paint.py FUN_TILES), so the serious sheet keeps
its tiles; the shields reuse the Erebor shield's geometry with fun tiles, and the colour variants of
the crown-helm (gold-plated, hot pink) redraw it from fixed-colour tiles of the serious sheet.
Design space and helmet seating as in serious.py.
"""
import math

from ..kit.geom import add, cross, mul
from . import serious as S
from .serious import AXE_B, AXE_C, AXE_D, HEAD, brow, ring

(F_GOLD, F_IRON, F_OAK, F_STEEL, F_PINK, F_RAINBOW, F_BOA, F_JESTER_A, F_JESTER_B, F_PARTY, F_PLUME, F_DUCK, F_BEAK,
 F_BLACK, F_PINKMETAL, F_PINKFACE, F_SMILEY, F_SCALES, F_FIN, F_PAN, F_POMPOM, F_HORN, F_BRONZE, F_PINKGEM, F_COPPER,
 F_WHITE) = range(26)
H = "B_HEAD"
CX = HEAD[0][0]
SPINE = "BAT_SPINE2"


def dome(m, prof, tag, sides=24):
    return m.shell(HEAD, prof, tag, H, sides=sides, rim=brow)


def ball(m, c, r, tag, bone=H, sides=10):
    """A sphere (a stack of rings)."""
    prof = [(r * math.sin(a), r * math.sin(a), r * -math.cos(a)) for a in [math.pi * k / 6 for k in range(1, 6)]]
    m.shell((list(c), [1, 0, 0], [0, 1, 0], [0, 0, 1]), [(.001, .001, -r)] + prof + [(.001, .001, r)], tag, bone,
            sides=sides, keep=sides)


# ------------------------------------------------------------------ helmets
def hat_party(m):
    """A party hat: a tall striped cone on an elastic band, a white pompom on top."""
    m.shell((list((CX - .1, 0, 0)), [1, 0, 0], [0, 1, 0], [0, 0, 1]),
            [(1.5, 1.42, 16.9), (1.52, 1.44, 17.05), (.75, .72, 19.0), (.05, .05, 21.0)], F_PARTY, H, sides=20)
    S.edge(m, ring(1.53, 1.45, 16.92, n=20, rim=None), .07, F_GOLD)
    ball(m, (CX - .1, 0, 21.15), .55, F_POMPOM)
    for s in (1, -1):
        m.sweep([(CX + .2, s * 1.4, 17.0), (CX + .7, s * 2.05, 15.9), (CX + 1.4, s * 1.7, 14.3)], [.04] * 3, F_BLACK, H, sides=4)


def hat_jester(m):
    """A jester's cap: a two-tone felt cap and three floppy points, each with a golden bell."""
    dome(m, [(2.2, 2.0, 15.95), (2.3, 2.1, 16.1), (2.25, 2.06, 16.9), (1.9, 1.75, 17.7), (1.1, 1.0, 18.3),
             (.05, .05, 18.5)], F_JESTER_A, sides=24)
    S.edge(m, ring(2.36, 2.16, 16.0, n=24), .16, F_JESTER_B, sides=6)
    for k, (dy, tag) in enumerate(((-1, F_JESTER_B), (0, F_JESTER_A), (1, F_JESTER_B))):
        base = (CX - .2 * abs(dy), dy * .9, 18.25)
        tip = (CX - 1.0 - .6 * (dy == 0), dy * 3.4, 16.4 if dy else 17.2)
        mid = (CX - .3, dy * 1.9, 20.0 if dy else 20.4)
        if dy == 0:
            tip = (CX - 2.6, 0, 16.6)
            mid = (CX - 1.2, 0, 20.3)
        path = [base, add(mul(base, .5), mul(mid, .5)), mid, add(mul(mid, .45), mul(tip, .55)), tip]
        m.sweep(path, [.75, .66, .5, .3, .12], tag, H, sides=10)
        ball(m, add(tip, (0, 0, -.32)), .32, F_GOLD, sides=8)


def hat_plume(m):
    """A steel helm with an enormous red plume sweeping from the brow to below the shoulders."""
    dome(m, [(2.18, 1.98, 15.92), (2.3, 2.1, 16.05), (2.31, 2.11, 16.6), (2.2, 2.02, 17.3), (1.9, 1.75, 17.95),
             (1.3, 1.2, 18.45), (.05, .05, 18.7)], F_STEEL)
    S.edge(m, ring(2.36, 2.16, 16.0, n=24), .1, F_GOLD)
    m.stud((CX, 0, 18.62), (0, 0, 1), .4, F_GOLD, H, h=.35, sides=8)
    path = [(CX + 1.6, 0, 18.4), (CX + .9, 0, 19.9), (CX - .4, 0, 21.0), (CX - 2.0, 0, 21.0), (CX - 3.3, 0, 19.8),
            (CX - 4.0, 0, 17.6), (CX - 4.2, 0, 15.2), (CX - 4.0, 0, 13.3)]
    m.sweep(path, [.35, .9, 1.25, 1.35, 1.25, 1.0, .7, .2], F_PLUME, H, sides=12, squash=.42, up=[0, 1, 0])


def hat_pot(m):
    """A copper cooking pot worn upside down: a dented belly, a rolled lip, two loop handles and a
    wooden ladle tucked through one of them."""
    m.shell(HEAD, [(2.35, 2.2, 15.75), (2.48, 2.32, 15.85), (2.55, 2.4, 16.6), (2.58, 2.43, 17.6), (2.5, 2.36, 18.45),
                   (2.2, 2.1, 18.9), (1.2, 1.15, 19.08), (.05, .05, 19.12)], F_COPPER, H, sides=24, rim=lambda t: .12 * math.cos(t),
            bump=lambda t, k: -.12 * math.exp(-((t - 2.3) ** 2) * 6) * (2 <= k <= 4))
    S.edge(m, ring(2.52, 2.36, 15.83, n=24, rim=lambda t: .12 * math.cos(t)), .13, F_COPPER, sides=6)
    for s in (1, -1):
        loop = [(CX + .7 * math.cos(a), s * (2.62 + .55 * math.sin(a) ** 2), 17.6 + .55 * math.sin(a))
                for a in [math.pi * k / 8 for k in range(9)]]
        m.sweep(loop, [.1] * 9, F_IRON, H, sides=6)
    m.tube((CX - .3, -2.95, 18.1), (CX + 1.6, -2.95, 21.4), .11, F_OAK, H, sides=6)
    m.shell(((CX + 1.75, -2.95, 21.7), [1, 0, 0], [0, 1, 0], [0, 0, 1]),
            [(.02, .02, -.35), (.45, .4, -.25), (.55, .5, 0), (.5, .46, .05)], F_OAK, H, sides=10)


def hat_duck(m):
    """A rubber duck sitting on the hero's head: a round yellow body and tail, a big head, an
    orange beak and two black eyes with white highlights."""
    m.shell(HEAD, [(1.7, 1.6, 16.3), (2.2, 1.95, 16.6), (2.35, 2.05, 17.3), (2.1, 1.85, 18.1), (1.35, 1.2, 18.6),
                   (.05, .05, 18.75)], F_DUCK, H, sides=20, rim=lambda t: .25 * math.cos(t))
    m.tube((CX - 2.1, 0, 17.4), (CX - 2.9, 0, 18.5), .55, F_DUCK, H, sides=8, r1=.05)
    head = (CX + 1.45, 0, 19.35)
    ball(m, head, 1.05, F_DUCK, sides=14)
    m.sweep([add(head, (.8, 0, -.12)), add(head, (1.5, 0, -.18)), add(head, (1.9, 0, -.12))], [.42, .38, .1], F_BEAK, H,
            sides=8, squash=.45, up=[0, 0, 1])
    for s in (1, -1):
        e = add(head, (.62, s * .58, .35))
        ball(m, e, .2, F_BLACK, sides=8)
        ball(m, add(e, (.16, s * .07, .1)), .06, F_WHITE, sides=6)


def hat_viking(m):
    """A bronze viking helm with comically huge ivory horns, gold-ringed at the roots."""
    dome(m, [(2.18, 1.98, 15.92), (2.3, 2.1, 16.05), (2.31, 2.11, 16.6), (2.22, 2.03, 17.25), (1.95, 1.78, 17.9),
             (1.4, 1.28, 18.4), (.05, .05, 18.65)], F_BRONZE)
    S.edge(m, ring(2.36, 2.16, 16.05, n=24), .12, F_GOLD)
    for s in (1, -1):
        path = [(CX - .1, s * 2.0, 17.3), (CX + .1, s * 3.1, 17.6), (CX + .5, s * 4.3, 18.6), (CX + .8, s * 5.1, 20.2),
                (CX + .9, s * 5.2, 21.9), (CX + .6, s * 4.7, 23.2), (CX + .1, s * 4.0, 23.9)]
        m.sweep(path, [.78, .74, .64, .5, .36, .2, .04], F_HORN, H, sides=12)
        m.tube(add(path[0], (0, s * .3, 0)), add(path[0], (0, s * .75, .1)), .85, F_GOLD, H, sides=12)


# ------------------------------------------------------------------ capes
def cloak(m, tag, hem_tag, collar_tag, folds=7):
    """A cloak from the shoulders to below the belt on the upper spine (EA's in-game rig has no
    cape bones), in `folds` deep folds, braided along its hem and sides."""
    back = ((-0.7, 0.0, 0.0), [1, 0, 0], [0, 1, 0], [0, 0, 1])
    arc = (math.pi * .66, math.pi * 1.34)
    prof = [(3.95, 4.05, 7.9), (3.75, 3.9, 8.9), (3.55, 3.75, 9.9), (3.4, 3.62, 10.8), (3.2, 3.45, 11.8),
            (3.0, 3.3, 12.9), (2.75, 3.15, 13.9), (2.5, 3.0, 14.7), (2.28, 2.88, 15.25)]
    K = len(prof)
    bump = lambda t, k: .24 * (1 - k / (K - 1)) ** 1.2 * math.sin(folds * 2 * math.pi * (t - arc[0]) / (arc[1] - arc[0]))
    rows = m.shell(back, prof, tag, SPINE, sides=48, arc=arc, double=True, bump=bump, keep=28)
    S.edge(m, [add(p, (-.02, 0, -.02)) for p in rows[0]], .1, hem_tag, SPINE)
    for col in (0, -1):
        S.edge(m, [r[col] for r in rows], .08, hem_tag, SPINE)
    collar = [(-0.7 + 2.45 * math.cos(a), 3.0 * math.sin(a), 15.35 + .15 * math.cos(a))
              for a in [math.pi * (.6 + .8 * i / 16) for i in range(17)]]
    m.sweep(collar, [.36 + .1 * math.sin(math.pi * i / 16) for i in range(17)], collar_tag, SPINE, sides=10)
    return rows


def cape_pink(m):
    """A bright pink cape with gold trim, a white fluffy collar and a big pink bow at the throat."""
    cloak(m, F_PINK, F_GOLD, F_POMPOM)
    for s in (1, -1):
        m.slab([(.55, 0, 14.6), (.7, s * 1.25, 15.25), (.72, s * 1.35, 14.4), (.6, s * .2, 14.35)], .14, (1, 0, 0),
               F_PINK, SPINE, bevel=.03)
        m.sweep([(.62, s * .15, 14.4), (.75, s * .45, 13.6), (.8, s * .7, 12.7)], [.16, .14, .06], F_PINK, SPINE,
                sides=6, squash=.4)
    ball(m, (.72, 0, 14.55), .3, F_PINKGEM, SPINE, sides=8)


def cape_rainbow(m):
    """A rainbow-striped cloak, each fold its own colour, with a white fur collar."""
    cloak(m, F_RAINBOW, F_GOLD, F_POMPOM, folds=7)


def boa(m):
    """A fluffy pink feather boa slung round the neck, both ends hanging down the chest."""
    for s in (1, -1):
        path = [(1.5, s * .9, 11.0), (1.95, s * 1.5, 12.4), (1.6, s * 2.3, 14.1), (.6, s * 2.75, 15.2),
                (-.6, s * 2.6, 15.55), (-1.6, s * 1.5, 15.6), (-1.95, 0, 15.6)]
        radii = [.45 + .14 * math.sin(i * 2.7) for i in range(len(path))]
        m.sweep(path, radii, F_BOA, SPINE, sides=10)
        for k, p in enumerate(path[:-1]):
            ball(m, add(p, (0, s * .2 * math.sin(k), .25 * math.cos(k * 1.7))), .4, F_BOA, SPINE, sides=6)


# ------------------------------------------------------------------ weapons and shields
def _p(t, s=0.0, w=0.0):
    return add(add(add(AXE_C, mul(AXE_D, t)), mul(AXE_B, s)), mul(cross(AXE_D, AXE_B), w))


def frying_pan(m):
    """A cast-iron frying pan on a long handle (it fights as the dwarven axes do)."""
    bone = "B_HAND_R"
    side = cross(AXE_D, AXE_B)
    m.tube(_p(-6.6), _p(.3), .2, F_OAK, bone, sides=8)
    m.tube(_p(.1), _p(1.0), .17, F_IRON, bone, sides=6)
    m.sweep([_p(-6.9 + .25 * math.cos(a), .25 * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(11)]],
            [.06] * 11, F_IRON, bone, sides=4)
    c = _p(3.15, .0)
    f = (c, AXE_D, AXE_B, side)
    m.shell(f, [(.05, .05, -.1), (2.0, 2.0, -.1), (2.18, 2.18, .02), (2.3, 2.3, .38), (2.22, 2.22, .4)], F_PAN, bone,
            sides=28, planar=2.3, double=True)
    S.edge(m, [add(add(c, mul(AXE_D, 2.28 * math.cos(a))), add(mul(AXE_B, 2.28 * math.sin(a)), mul(side, .4)))
               for a in [2 * math.pi * k / 28 for k in range(29)]], .07, F_IRON, bone)


def giant_fish(m):
    """A giant fish held by the tail: a silver-green scaled body, orange fins, goggling eyes."""
    bone = "B_HAND_R"
    up = mul(AXE_B, -1)
    secs = []
    for t, hb, hw in ((-3.4, .35, .2), (-2.6, .8, .45), (-1.2, 1.3, .7), (.4, 1.5, .8), (1.9, 1.35, .74), (3.0, 1.0, .58),
                      (3.7, .55, .36), (4.0, .1, .08)):
        secs.append([add(_p(t), add(mul(up, hb * math.sin(a) + .1), mul(cross(AXE_D, AXE_B), hw * math.cos(a))))
                     for a in [2 * math.pi * k / 12 for k in range(12)]])
    m.loft(secs, F_SCALES, bone, uv=lambda k, i: (i / 12, k / 7))
    side = cross(AXE_D, AXE_B)
    m.slab([_p(-3.3), _p(-4.6, -1.5), _p(-4.2, 0), _p(-4.6, 1.5)], .1, side, F_FIN, bone, bevel=.02)
    m.slab([_p(-1.4, -1.25), _p(1.6, -1.45), _p(.6, -2.4), _p(-.8, -2.1)], .08, side, F_FIN, bone, bevel=.02)
    for w in (1, -1):
        eye = add(_p(3.05, -.35), mul(side, w * .55))
        ball(m, eye, .26, F_WHITE, bone, sides=8)
        ball(m, add(eye, add(mul(side, w * .18), mul(AXE_D, .06))), .14, F_BLACK, bone, sides=6)
        m.slab([_p(1.6, .3, w * .7), _p(2.4, .2, w * .65), _p(1.9, 1.0, w * .75)], .06, mul(side, w), F_FIN, bone, bevel=.02)


PINK_SHIELD = {S.DEVICE: F_PINKFACE, S.GOLD: F_PINKMETAL, S.STEEL: F_PINKGEM, S.HEXBRONZE: F_PINKMETAL, S.GEM: F_PINKGEM,
               S.PLANKS: F_PINK, S.LEATHER: F_PINK}
SMILEY_SHIELD = {S.DEVICE: F_SMILEY, S.GOLD: F_GOLD, S.STEEL: F_STEEL, S.HEXBRONZE: F_BLACK, S.GEM: F_BLACK,
                 S.PLANKS: F_OAK, S.LEATHER: F_OAK}
GOLD_PLATED = {S.BRONZEDOME: 29, S.CHEEK: 29, S.BRONZE: S.GOLD, S.RUNEBAND: 30}     # serious sheet, fixed colours
HOT_PINK = {S.BRONZEDOME: 31, S.CHEEK: 31, S.BRONZE: 31, S.RUNEBAND: 31}


def shield_smiley(m):
    """The Erebor shield's build with a grinning yellow face (its boss is the nose)."""
    S.shield_erebor(m)


FUN = {   # sub-object: (group, design, name, description, sheet, tile remap)
    "SKH_FUN_PARTY": ("CreateAHero_Helmet", hat_party, "Party Hat", "It is somebody's birthday.", "fun", None),
    "SKH_FUN_JESTER": ("CreateAHero_Helmet", hat_jester, "Jester's Cap", "Bells on.", "fun", None),
    "SKH_FUN_PLUME": ("CreateAHero_Helmet", hat_plume, "The Plume", "More plume than dwarf.", "fun", None),
    "SKH_FUN_POT": ("CreateAHero_Helmet", hat_pot, "Cooking Pot", "Still smells of stew.", "fun", None),
    "SKH_FUN_DUCK": ("CreateAHero_Helmet", hat_duck, "Duck Hat", "Quack.", "fun", None),
    "SKH_FUN_VIKING": ("CreateAHero_Helmet", hat_viking, "Mighty Horns", "Doorways are a problem.", "fun", None),
    "SKH_HLMT_ERG": ("CreateAHero_Helmet", S.helm_erebor, "Crown-helm, Gold-plated", "Thrain's own, polished.",
                     "serious", GOLD_PLATED),
    "SKH_HLMT_ERP": ("CreateAHero_Helmet", S.helm_erebor, "Crown-helm, Hot Pink", "Fabulous.", "serious", HOT_PINK),
    "SKH_FUN_PINKCAP": ("CreateAHero_ShoulderPlates", cape_pink, "Pink Cape", "Bright pink, with a bow.", "fun", None),
    "SKH_FUN_RAINBOW": ("CreateAHero_ShoulderPlates", cape_rainbow, "Rainbow Cloak", "Every colour at once.", "fun", None),
    "SKH_FUN_BOA": ("CreateAHero_ShoulderPlates", boa, "Feather Boa", "Fluffy and pink.", "fun", None),
    "SKH_FUN_PAN": ("CreateAHero_Weapon", frying_pan, "Frying Pan", "Fights as a dwarven axe.", "fun", None),
    "SKH_FUN_FISH": ("CreateAHero_Weapon", giant_fish, "Giant Fish", "Fights as a dwarven axe.", "fun", None),
    "SKH_FUN_PINKSH": ("CreateAHero_Shield", S.shield_erebor, "Glitter Shield", "Pink, with a heart.", "fun", PINK_SHIELD),
    "SKH_FUN_SMILEY": ("CreateAHero_Shield", shield_smiley, "Smiley Shield", "Have a nice day.", "fun", SMILEY_SHIELD),
}
