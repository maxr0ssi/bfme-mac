"""Angmar thrall: EA's orc labourer hauling stone for Carn Dum, in cold slate and rime.

His fur and rags are dyed the builder's cold slate wool and his mail blue-black iron; EA's leather
apron keeps the player colour. Over his shoulders lies a collar of rime-white fur on an iron ring,
with a short cape in player colour behind it and a cold-fire charm at the throat; iron arm rings.
His hammer is a frost-rimed iron maul; his axe a bearded Hill-men axe with a pale ice edge. Ships
as KUWorker_SKN; AngmarWorker's Draw (its NoSelect and Fortress children inherit it) is repointed
to it. The Hall of Twilight and the mill called Mordor's workers: the archive adds
AngmarLaborerNoSelect and AngmarFarmLaborerNoSelect, children of Mordor's drawing KUWorker_SKN
(sagekit/units/labourer.py `children`), which the Angmar pack names. Palette A2 (assets/angmar/style.py). python3 -m sagekit unit angmar/worker --render.
"""
import math

from assets.angmar.style import PALETTE, AngmarStyle
from sagekit.units import Unit
from sagekit.units.cloth import HC, drape
from sagekit.units.labourer import (ACCENT, AXE_BLADE, AXE_GRIP, DARK, ELBOW, GLOW, HAMMER_GRIP, HAMMER_HEAD,
                                    HIDE, IRON, PELVIS, SPINE, STEEL, WOOD, WRIST, Labourer, haft, lerp, ring,
                                    slab, spike)

INI = "data\\ini\\object\\evilfaction\\units\\angmar\\angmarworker.ini"
WOOL = [(0, (.02, .025, .036)), (.4, (.09, .11, .145)), (.75, (.22, .26, .32)), (1, (.40, .45, .53))]


def cape_row(z, x, half, cols=7):
    return [(x + .07 * y * y, y, z) for y in [-half + 2 * half * i / (cols - 1) for i in range(cols)]]


def cape(m):
    rows = [(SPINE, cape_row(16.05, -2.7, 1.55)), (SPINE, cape_row(14.6, -3.0, 1.85)),
            (SPINE, cape_row(12.9, -2.95, 2.0)), (PELVIS, cape_row(11.2, -2.6, 2.1)),
            (PELVIS, cape_row(9.5, -2.75, 2.25))]
    drape(m, rows, HC, depth=.12)


def fur_collar(m):
    ring(m, (-.95, 0, 16.15), 1.68, 1.38, .3, IRON, SPINE, n=14, saddle=.6)
    for k in range(22):                                         # rime-white tufts, outward and down
        a = k * math.tau / 22
        base = (-.95 + 1.75 * math.cos(a), 1.48 * math.sin(a), 16.25 + .6 * math.sin(a) ** 2)
        out = (math.cos(a), math.sin(a) * 1.15, 0)
        if out[0] > .55:
            continue                                            # the throat stays open for the charm
        tip = (base[0] + out[0] * .95, base[1] + out[1] * .95, base[2] - .55 - .2 * (k % 3))
        spike(m, base, tip, .42 + .08 * (k % 2), HIDE, SPINE, sides=5)
    # The cold-fire charm: a pale shard in an iron claw at the throat.
    m.tube((.72, 0, 16.05), (.9, 0, 15.2), .2, IRON, SPINE, sides=5)
    spike(m, (.95, 0, 15.25), (1.1, 0, 14.15), .3, GLOW, SPINE, sides=4)
    spike(m, (.95, 0, 15.25), (.9, 0, 15.85), .3, GLOW, SPINE, sides=4)


def arm_rings(m):
    for s, fore in ((-1, "BAT_FARMR"), (1, "BAT_FARML")):
        e, w = (ELBOW[0], s * ELBOW[1], ELBOW[2]), (WRIST[0], s * WRIST[1], WRIST[2])
        for t in (.62, .78):
            m.tube(lerp(e, w, t - .04), lerp(e, w, t + .04), .82, IRON, fore, sides=8)
    ring(m, (-.1, 0, 10.95), 2.12, 2.36, .24, DARK, PELVIS, n=18)                 # belt
    m.box((1.98, -.42, 10.6), (2.24, .42, 11.3), STEEL, PELVIS)


def frost_maul(m):
    haft(m, HAMMER_GRIP, WOOD, r=.22, cap=IRON)
    top, bottom = HAMMER_HEAD
    a, b = lerp(top, bottom, .15), lerp(top, bottom, .85)
    m.tube(a, b, .78, IRON, sides=8)
    for t in (0, 1):                                            # rime-white faces
        p = lerp(a, b, t)
        m.tube(p, lerp(a, b, t + (-.05 if t else .05)), .82, ACCENT, sides=8)
    m.tube(lerp(a, b, .45), lerp(a, b, .55), .86, STEEL, sides=8)
    c = lerp(a, b, .5)
    spike(m, c, (c[0] + .3, c[1], c[2] + 1.3), .2, GLOW, sides=4)


def bearded_axe(m):
    haft(m, AXE_GRIP, WOOD, r=.2, cap=IRON)
    t0, e1, e2, tip, inner = AXE_BLADE
    beard = (tip[0] - .4, tip[1] + .2, tip[2] - .5)
    neck = lerp(t0, inner, .55)
    slab(m, [t0, e1, e2, beard, lerp(inner, beard, .5), neck], .22, IRON)
    for p, q in ((t0, e1), (e1, e2), (e2, beard)):              # the pale ice edge
        m.tube(lerp(p, q, -.03), lerp(p, q, 1.03), .14, ACCENT, sides=4)
    for k in range(3):                                          # a few icicles on the haft
        p = lerp(AXE_GRIP[0], AXE_GRIP[1], .55 + .12 * k)
        spike(m, p, (p[0], p[1], p[2] - .55 - .15 * k), .1, GLOW, sides=4)


class Worker(Labourer, Unit):           # (Unit: the framework's recipe scan looks for it)
    """AngmarWorker's labourer, shipped under a name of its own."""
    own_model = "KUWorker_SKN"
    objects = {"AngmarWorker": (INI, "ModuleTag_01")}
    children = AngmarStyle.workers          # the Angmar pack names them: installed before it, reverted after
    textures = {"MUOrcLabor.tga": "KUWorkCr.tga", "MUOrcWarr.tga": "KUWorkCr.tga"}
    house = {"KUWorkCr.tga": "HC_KUWorkCr.tga"}
    mask = ("HC_MUOrcLabor.tga", "HC_KUWorkCr.tga")
    archive = "!!!!!!!!!!!!sagekit-angmar-worker.big"
    labels = ("EA'S ORC LABOURER (ANGMAR)", "ANGMAR THRALL - REVIEW")
    palette = PALETTE
    DYE = WOOL
    MAIL_DYE = PALETTE.ramps["iron"]
    SWATCHES = [("iron", .5), ("iron", .22), ("trim", .7), ("wood", .35), ("planks", .42), ("ice", .8),
                ("trim", .6), ("roof", .4), ("fire", .85), ("ice", .92), ("timber", .8), ("wood", .55),
                ("iron", .4), ("stone", .45), ("rock", .5), ("rust", .5)]
    SEED = 1975

    def gear(self, body):
        cape(body)
        fur_collar(body)
        arm_rings(body)

    def hammer(self, m):
        frost_maul(m)

    def axe(self, m):
        bearded_axe(m)
