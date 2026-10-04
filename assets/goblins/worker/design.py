"""Goblin-town labourer: EA's orc labourer in the scavenger's blood, iron and bone.

His fur and rags are dyed a dark crimson (the faction's primary) and his mail a gritty silver; EA's leather apron keeps the
player colour. He wears a headband with trailing rag tails in player colour, a necklace of teeth
with a small skull, a horned skull on the left shoulder, a scrap-iron bracer and a hide-rope belt
with a crimson rag. His hammer is a lump of rock lashed to a long bone; his axe a crude scrap
cleaver, notched and blood-stained. Ships as WUWorker_SKN; WildLaborer's Draw (its NoSelect and
Fortress children inherit it) is repointed to it. The cave, spider pit and mine shaft called Mordor's
workers: the archive adds GoblinLaborerNoSelect and GoblinFarmLaborerNoSelect, children of Mordor's
drawing WUWorker_SKN (sagekit/units/labourer.py `children`), which the Goblin pack names. Palette E (assets/goblins/style.py); the skull,
bone and rag shapes are the builder's kit. python3 -m sagekit unit goblins/worker --render.
"""
from assets.goblins.porter.kit import bone_shaft, rag, skull
from assets.goblins.style import PALETTE, GoblinStyle
from sagekit.units import Unit
from sagekit.units.cloth import HC
from sagekit.units.labourer import (ACCENT, AXE_BLADE, AXE_GRIP, BONE, DARK, ELBOW, GLOW, HAMMER_GRIP,
                                    HAMMER_HEAD, HEAD, IRON, PELVIS, ROPE, SPINE, STEEL, WRIST, Labourer,
                                    lerp, ring, slab, spike)

INI = "data\\ini\\object\\evilfaction\\units\\wild\\wildlaborer.ini"


def headband(m):
    ring(m, (.02, 0, 19.0), 1.6, 1.42, .2, HC, HEAD, n=14)
    rag(m, (-1.62, -.45, 19.05), (0, .9, 0), 2.6, HC, HEAD, sway=(-.9, 0, .3), strips=2, cut=(1, .75))


def necklace(m):
    pts = ring(m, (-.85, 0, 16.0), 1.72, 1.42, .07, ROPE, SPINE, n=16, saddle=.55)
    for p in pts[:5] + pts[-4:]:                                # teeth along the front
        if p[0] > -.6:
            spike(m, p, (p[0] + .1, p[1], p[2] - .5), .13, BONE, SPINE, sides=4)
    skull(m, (.95, 0, 15.15), .32, (1, 0, 0), BONE, DARK, SPINE)


def shoulder_skull(m):
    b = "BAT_UARML"
    slab(m, [(-2.1, 2.1, 16.6), (.1, 2.1, 16.6), (.2, 3.6, 15.6), (-2.2, 3.6, 15.6)], .2, DARK, b)   # hide pad
    skull(m, (-1.0, 3.0, 16.15), .62, (1, .35, 0), BONE, DARK, b, horns=(BONE, 1.6))


def bracer(m):
    e, w = (ELBOW[0], -ELBOW[1], ELBOW[2]), (WRIST[0], -WRIST[1], WRIST[2])
    a, b = lerp(e, w, .45), lerp(e, w, .88)
    m.tube(a, b, .8, IRON, "BAT_FARMR", sides=6)
    for t in (.15, .85):
        m.tube(lerp(a, b, t - .05), lerp(a, b, t + .05), .86, DARK, "BAT_FARMR", sides=6)
    c = lerp(a, b, .5)
    spike(m, c, (c[0], c[1], c[2] + 1.0), .18, STEEL, "BAT_FARMR")


def belt(m):
    ring(m, (-.1, 0, 10.95), 2.12, 2.36, .17, ROPE, PELVIS, n=18)
    ring(m, (-.1, 0, 10.6), 2.14, 2.38, .12, ROPE, PELVIS, n=18)
    rag(m, (.9, 1.6, 10.7), (-.9, .6, 0), 3.2, ACCENT, PELVIS, sway=(.2, .5, 0), strips=3)
    skull(m, (1.05, -1.75, 10.2), .34, (1, -.3, 0), BONE, DARK, PELVIS)


def rock_hammer(m):
    bone_shaft(m, lerp(HAMMER_GRIP[1], HAMMER_GRIP[0], 1.04), HAMMER_GRIP[1], .2, BONE)
    top, bottom = HAMMER_HEAD
    a, b = lerp(top, bottom, .12), lerp(top, bottom, .78)
    m.tube(a, b, .95, DARK, sides=5, r1=.8)                          # the rock
    m.tube(lerp(a, b, -.04), a, .7, DARK, sides=5)
    for t in (.4, .55):                                               # hide lashing
        m.tube(lerp(a, b, t - .04), lerp(a, b, t + .04), 1.04, ROPE, sides=5)


def scrap_cleaver(m):
    a, b = lerp(AXE_GRIP[1], AXE_GRIP[0], 1.03), lerp(AXE_GRIP[0], AXE_GRIP[1], 1.02)
    bone_shaft(m, a, b, .19, BONE)
    t0, e1, e2, tip, inner = AXE_BLADE
    notch = lerp(e1, e2, .5)
    notch = (notch[0] - .55, notch[1], notch[2] + .1)
    slab(m, [t0, e1, lerp(e1, e2, .35), notch, lerp(e1, e2, .65), e2, tip, inner], .2, IRON)
    slab(m, [lerp(t0, inner, .2), lerp(e1, inner, .25), lerp(e2, inner, .35), lerp(tip, inner, .3)], .23, GLOW)
    for p, q in ((t0, e1), (e2, tip)):
        m.tube(p, q, .1, STEEL, sides=4)
    for t in (.25, .55, .8):                                          # rivets on the scrap plate
        p = lerp(lerp(t0, tip, t), inner, .35)
        m.tube(p, (p[0], p[1] - .02, p[2] + .02), .16, DARK, sides=4)


class Worker(Labourer, Unit):           # (Unit: the framework's recipe scan looks for it)
    """WildLaborer's labourer, shipped under a name of its own."""
    own_model = "WUWorker_SKN"
    objects = {"WildLaborer": (INI, "ModuleTag_01")}
    children = GoblinStyle.workers          # the Goblin pack names them: installed before it, reverted after
    textures = {"MUOrcLabor.tga": "WUWorkCr.tga", "MUOrcWarr.tga": "WUWorkCr.tga"}
    house = {"WUWorkCr.tga": "HC_WUWorkCr.tga"}
    mask = ("HC_MUOrcLabor.tga", "HC_WUWorkCr.tga")
    archive = "!!!!!!!!!!!!sagekit-goblin-worker.big"
    labels = ("EA'S ORC LABOURER (GOBLINS)", "GOBLIN-TOWN LABOURER - REVIEW")
    palette = PALETTE
    DYE = [(0, (.02, .004, .006)), (.45, (.13, .02, .03)), (.8, (.30, .05, .06)), (1, (.46, .11, .11))]
    MAIL_DYE = PALETTE.ramps["iron"]
    SWATCHES = [("iron", .5), ("stone", .3), ("iron", .78), ("wood", .6), ("wood", .5), ("bone", .74),
                ("iron", .62), ("hide", .45), ("fire", .55), ("hide", .55), ("hide", .3), ("wood", .75),
                ("iron", .4), ("stone", .45), ("bone", .6), ("hide", .4)]
    SEED = 666

    def gear(self, body):
        headband(body)
        necklace(body)
        shoulder_skull(body)
        bracer(body)
        belt(body)

    def hammer(self, m):
        rock_hammer(m)

    def axe(self, m):
        scrap_cleaver(m)
