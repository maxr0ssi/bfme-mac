"""Isengard Uruk labourer: EA's orc labourer at the forges of Orthanc, in black and silver.

His fur and rags are dyed charcoal like the builder's robe and his mail iron; EA's leather apron
keeps the player colour. He wears an Uruk skullcap with a silver brim and ridge and the White
Hand on its brow, a back cloth in player colour bearing the White Hand, studded leather bracers
and a silver-buckled belt. His hammer is a square forge hammer with silver bands; his axe a broad
machined blade with a silver edge. Palette A (assets/isengard/style.py); the White Hand is the
builder's (kit.white_hand). Ships as IUWorker_SKN.

Isengard has no worker object: its buildings call MordorWorkerNoSelect. The archive adds two
(`ini_files`): IsengardWorkerNoSelect and IsengardFortressWorkerNoSelect, children of Mordor's,
each with MordorWorkerNoSelect's Draw module drawing IUWorker_SKN, in a file that sorts after
Mordor's worker.ini (the engine reads INIs in sorted order and a child needs its parent first).
The Isengard pack's structures name them (IsengardStyle.workers, composed by sagekit/install.py),
so this unit installs before that pack and reverts after it (`defines`; both refuse otherwise).
No upgrades.
python3 -m sagekit unit isengard/worker --render (docs/UNITS.md, sagekit/units/labourer.py).
"""
from assets.isengard.porter.kit import plane, white_hand
from assets.isengard.style import PALETTE, IsengardStyle
from sagekit.units import Unit
from sagekit.units.cloth import HC, drape
from sagekit.units.labourer import (AXE_BLADE, AXE_GRIP, BONE, DARK, ELBOW, HAMMER_GRIP, HAMMER_HEAD, HEAD,
                                    IRON, LEATHER, PELVIS, SPINE, STEEL, TRIM, WOOD, WRIST, Labourer, haft,
                                    lerp, ring, slab, spike)

CHARCOAL = [(0, (.012, .012, .013)), (.45, (.07, .07, .075)), (.8, (.17, .17, .18)), (1, (.30, .30, .32))]


def skullcap(m):
    dome = [(18.85, 1.8), (19.55, 1.72), (20.1, 1.45), (20.5, 1.0), (20.72, .35)]   # (z, radius)
    for (z0, r0), (z1, r1) in zip(dome, dome[1:]):
        m.tube((-.03 * (z0 - 18.85), 0, z0), (-.03 * (z1 - 18.85), 0, z1), r0, IRON, HEAD, sides=12, r1=r1)
    ring(m, (0, 0, 18.88), 1.82, 1.82, .16, TRIM, HEAD, n=16)                       # silver brim
    crest = [(1.82, 18.95), (1.7, 19.6), (1.45, 20.15), (1.0, 20.58), (.0, 20.84), (-1.0, 20.55),
             (-1.47, 20.1), (-1.75, 19.55), (-1.83, 18.95)]                         # the ridge, nose to nape
    for (x0, z0), (x1, z1) in zip(crest, crest[1:]):
        m.tube((x0, 0, z0), (x1, 0, z1), .17, TRIM, HEAD, sides=5)
    for s in (-1, 1):                                                               # cheek plates
        slab(m, [(.9, s * 1.55, 18.95), (-.4, s * 1.75, 18.95), (-.2, s * 1.6, 17.6), (.7, s * 1.4, 17.9)],
             .14, IRON, HEAD)
    for s in (-1, 1):                                       # the White Hand on both temples
        at = plane((.55, s * 1.73, 19.3), (0, s, 0))
        white_hand(m, at, .42, .05, BONE, (0, s, 0), HEAD)


def back_cloth(m):
    def row(z, x, half, cols=7):
        return [(x + .07 * y * y, y, z) for y in [-half + 2 * half * i / (cols - 1) for i in range(cols)]]
    rows = [(SPINE, row(15.9, -2.72, 1.45)), (SPINE, row(14.4, -3.0, 1.65)), (SPINE, row(12.8, -2.95, 1.75)),
            (PELVIS, row(11.0, -2.6, 1.8)), (PELVIS, row(9.0, -2.7, 1.85))]
    drape(m, rows, HC, depth=.12)
    hem = row(9.0, -2.82, 1.85)
    for a, b in zip(hem, hem[1:]):
        m.tube(a, b, .07, TRIM, PELVIS, sides=5)
    at = plane((-3.0, 0, 13.9), (-1, 0, 0))
    white_hand(m, at, .78, .05, BONE, (-1, 0, 0), SPINE, outline=DARK)


def bracers(m):
    for s, fore in ((-1, "BAT_FARMR"), (1, "BAT_FARML")):
        e, w = (ELBOW[0], s * ELBOW[1], ELBOW[2]), (WRIST[0], s * WRIST[1], WRIST[2])
        a, b = lerp(e, w, .4), lerp(e, w, .88)
        m.tube(a, b, .8, LEATHER, fore, sides=8)
        for t in (.08, .92):
            m.tube(lerp(a, b, t - .04), lerp(a, b, t + .04), .85, TRIM, fore, sides=8)
    ring(m, (-.1, 0, 10.95), 2.12, 2.36, .26, LEATHER, PELVIS, n=18)
    m.box((1.98, -.48, 10.55), (2.26, .48, 11.35), TRIM, PELVIS)


def forge_hammer(m):
    haft(m, HAMMER_GRIP, WOOD, r=.22, cap=TRIM)
    top, bottom = HAMMER_HEAD
    a, b = lerp(top, bottom, .12), lerp(top, bottom, .88)
    m.tube(a, b, .82, IRON, sides=4)
    for t in (.0, .3, .7, 1.0):
        m.tube(lerp(a, b, t - .03), lerp(a, b, t + .03), .88, TRIM, sides=4)


def broad_axe(m):
    haft(m, AXE_GRIP, WOOD, r=.2, cap=TRIM)
    t0, e1, e2, tip, inner = AXE_BLADE
    slab(m, [t0, e1, e2, tip, inner], .2, IRON)
    for p, q in ((t0, e1), (e1, e2), (e2, tip)):                    # the silver edge
        m.tube(lerp(p, q, -.03), lerp(p, q, 1.03), .13, STEEL, sides=4)
    back = lerp(AXE_GRIP[0], AXE_GRIP[1], .97)
    spike(m, back, (back[0] - .4, back[1] + 1.3, back[2] + .9), .3, IRON, sides=4)


class Worker(Labourer, Unit):           # (Unit: the framework's recipe scan looks for it)
    """Isengard's labourer under a name of its own, drawn by worker objects of its own."""
    own_model = "IUWorker_SKN"
    textures = {"MUOrcLabor.tga": "IUWorkCr.tga", "MUOrcWarr.tga": "IUWorkCr.tga"}
    house = {"IUWorkCr.tga": "HC_IUWorkCr.tga"}
    mask = ("HC_MUOrcLabor.tga", "HC_IUWorkCr.tga")
    archive = "!!!!!!!!!!!!sagekit-isengard-worker.big"
    children = IsengardStyle.workers        # the Isengard pack names them: installed before it, reverted after
    labels = ("EA'S ORC LABOURER (ISENGARD)", "ISENGARD URUK LABOURER - REVIEW")
    palette = PALETTE
    DYE = CHARCOAL
    MAIL_DYE = PALETTE.ramps["iron"]
    SWATCHES = [("iron", .45), ("iron", .18), ("silver", .72), ("hide", .55), ("wood", .55), ("mark", .92),
                ("silver", .6), ("cloth", .3), ("fire", .7), ("silver", .85), ("hide", .35), ("wood", .7),
                ("iron", .35), ("stone", .4), ("rock", .45), ("soot", .5)]
    SEED = 1418

    def gear(self, body):
        skullcap(body)
        back_cloth(body)
        bracers(body)

    def hammer(self, m):
        forge_hammer(m)

    def axe(self, m):
        broad_axe(m)
