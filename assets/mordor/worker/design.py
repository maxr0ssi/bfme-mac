"""Mordor slave-labourer: EA's orc labourer in the slave-driver's ash and iron.

His fur and rags are dyed ash-black like the builder's robe; EA's leather apron keeps the player
colour. He wears an iron slave collar with a hanging chain, manacles, a jagged iron pauldron with
hooked spikes and the Red Eye, a studded belt, and a ragged back cloth in player colour. His
hammer is a black iron maul with a hooked pick; his axe a notched, hooked cleaver with a bright
steel edge. Ships as MUWorker_SKN; MordorWorker and MordorWorkerNoSelect (whose Farm and Fortress
children inherit its Draw) are repointed to it, so EA's labourer stays for the cinematics.
python3 -m sagekit unit mordor/worker --render (docs/UNITS.md, sagekit/units/labourer.py).
"""
import math

from assets.mordor.style import PALETTE
from sagekit.units import Unit
from sagekit.units.cloth import HC, drape
from sagekit.units.labourer import (AXE_BLADE, AXE_GRIP, DARK, GLOW, HAMMER_GRIP, HAMMER_HEAD, IRON, LEATHER,
                                    PELVIS, SPINE, STEEL, TRIM, ELBOW, WRIST, Labourer, haft, lerp, ring,
                                    slab, spike)

INI = "data\\ini\\object\\evilfaction\\units\\mordor\\worker.ini"
RAG = [(0, (.02, .018, .017)), (.4, (.10, .085, .075)), (.75, (.24, .21, .19)), (1, (.40, .36, .32))]


def collar(m):
    pts = ring(m, (-.95, 0, 16.1), 1.62, 1.32, .26, IRON, SPINE, n=14, saddle=.6)
    for p in pts[1::2]:                                         # rivets
        m.tube(p, lerp((-.95, 0, p[2]), p, 1.22), .1, STEEL, SPINE, sides=4)
    # A ring at the throat and a chain hanging from it down the chest.
    m.tube((.72, -.2, 16.0), (.72, .2, 16.0), .4, DARK, SPINE, sides=8)
    z = 15.55
    for k in range(4):
        y = .14 if k % 2 else -.14
        m.tube((.95 + k * .1, y, z), (1.02 + k * .1, -y, z - .55), .11, IRON, SPINE, sides=5)
        z -= .5


def pauldron(m):
    """Three iron lames cascading down the left shoulder, hooked spikes, the Red Eye on the top."""
    b = "BAT_UARML"
    for k, (y0, z0, y1, z1, w) in enumerate([(1.9, 16.75, 3.0, 16.3, 1.35), (2.6, 16.45, 3.75, 15.55, 1.45),
                                             (3.3, 15.85, 4.3, 14.75, 1.4)]):
        x = -1.0
        slab(m, [(x - w, y0, z0), (x + w, y0, z0), (x + w * .95, y1, z1), (x, y1 + .35, z1 - .2),
                 (x - w * .95, y1, z1)], .2, IRON if k != 1 else DARK, b)
    for base, tip in [((-1.7, 2.5, 16.75), (-2.5, 2.9, 18.1)), ((-.4, 2.5, 16.75), (-.1, 3.0, 18.0)),
                      ((-1.05, 3.3, 16.3), (-1.2, 4.0, 17.5))]:
        spike(m, base, tip, .27, STEEL, b)
    # The lidless Eye on the middle lame, facing out and up toward the camera.
    c = (-1.0, 3.25, 16.12)
    slab(m, [(c[0] - .55, c[1], c[2] + .25), (c[0], c[1] - .1, c[2] + .38), (c[0] + .55, c[1], c[2] + .25),
             (c[0], c[1] + .1, c[2] + .12)], .1, GLOW, b)
    slab(m, [(c[0] - .04, c[1] - .02, c[2] + .4), (c[0] + .04, c[1] - .02, c[2] + .4),
             (c[0] + .04, c[1] + .08, c[2] + .2), (c[0] - .04, c[1] + .08, c[2] + .2)], .06, DARK, b)


def manacles(m):
    for s, fore in ((-1, "BAT_FARMR"), (1, "BAT_FARML")):
        e, w = (ELBOW[0], s * ELBOW[1], ELBOW[2]), (WRIST[0], s * WRIST[1], WRIST[2])
        a, b = lerp(e, w, .62), lerp(e, w, .86)
        m.tube(a, b, .82, IRON, fore, sides=8)
        m.tube(lerp(a, b, .42), lerp(a, b, .58), .88, STEEL, fore, sides=8)
    # A broken chain end swinging from the left manacle.
    p = lerp(ELBOW, WRIST, .74)
    p = (p[0] - .2, p[1], p[2] - .8)
    for k in range(3):
        q = (p[0] + .1, p[1] + (.12 if k % 2 else -.12), p[2] - .55)
        m.tube(p, q, .1, IRON, "BAT_FARML", sides=5)
        p = q


def belt_and_cloth(m):
    pts = ring(m, (-.1, 0, 10.95), 2.1, 2.35, .3, LEATHER, PELVIS, n=18)
    for p in pts[1::3]:
        m.tube(p, lerp((-.1, 0, 10.95), p, 1.14), .16, STEEL, PELVIS, sides=4)
    m.box((1.95, -.45, 10.55), (2.25, .45, 11.35), IRON, PELVIS)
    # A ragged back cloth in player colour, its hem torn to uneven points.
    cols = 7
    rows = []
    for z, lift in ((10.85, 0), (9.2, .12), (7.6, .25)):
        row = []
        for i in range(cols):
            y = -1.75 + 3.5 * i / (cols - 1)
            zz = z - (.0 if z > 8 else (.9 if i % 2 else 0) + .3 * math.sin(i * 2.3))
            row.append((-2.2 - lift - .04 * y * y, y, zz))
        rows.append((PELVIS, row))
    drape(m, rows, HC, depth=.1)


def maul(m):
    """Black iron maul along EA's head axis: a hexagonal head, a hooked pick on its far face."""
    haft(m, HAMMER_GRIP, DARK, r=.22, cap=IRON)
    top, bottom = HAMMER_HEAD
    a, b = lerp(top, bottom, .18), lerp(top, bottom, .62)
    m.tube(a, b, .8, IRON, sides=6)
    m.tube(lerp(a, b, -.06), a, .7, STEEL, sides=6)                 # the striking face
    for t in (.3, .5):
        m.tube(lerp(a, b, t - .03), lerp(a, b, t + .03), .86, DARK, sides=6)
    c = lerp(top, bottom, 1.12)
    spike(m, b, c, .55, IRON)
    spike(m, lerp(b, c, .6), (c[0] - .8, c[1] - .2, c[2] + .2), .22, STEEL)


def cleaver(m):
    haft(m, AXE_GRIP, DARK, r=.2, cap=IRON)
    t0, e1, e2, tip, inner = AXE_BLADE
    hook = (tip[0] - .9, tip[1] - .2, tip[2] + .8)
    slab(m, [t0, e1, e2, tip, hook, inner], .22, IRON)
    # Notches along the back and a bright steel edge.
    for p, q in ((t0, e1), (e1, e2), (e2, tip)):
        m.tube(lerp(p, q, -.02), lerp(p, q, 1.02), .13, STEEL, sides=4)
    for k in (.3, .6):
        n = lerp(t0, inner, k)
        spike(m, n, (n[0] - .6, n[1] + .25, n[2] + .25), .2, IRON)
    m.tube(lerp(AXE_GRIP[0], AXE_GRIP[1], .92), lerp(AXE_GRIP[0], AXE_GRIP[1], 1.0), .3, TRIM, sides=6)


class Worker(Labourer, Unit):           # (Unit: the framework's recipe scan looks for it)
    """MordorWorker's labourer, shipped under a name of its own."""
    own_model = "MUWorker_SKN"
    objects = {"MordorWorker": (INI, "ModuleTag_01"), "MordorWorkerNoSelect": (INI, "ModuleTag_01")}
    textures = {"MUOrcLabor.tga": "MUWorkCr.tga", "MUOrcWarr.tga": "MUWorkCr.tga"}
    house = {"MUWorkCr.tga": "HC_MUWorkCr.tga"}
    mask = ("HC_MUOrcLabor.tga", "HC_MUWorkCr.tga")
    archive = "!!!!!!!!!!!!sagekit-mordor-worker.big"
    labels = ("EA'S ORC LABOURER (MORDOR)", "MORDOR SLAVE-LABOURER - REVIEW")
    palette = PALETTE
    DYE = RAG
    MAIL_DYE = PALETTE.ramps["iron"]
    SWATCHES = [("iron", .5), ("iron", .22), ("steel", .62), ("hide", .5), ("wood", .5), ("bone", .7),
                ("trim", .55), ("cloth", .3), ("fire", .78), ("warpaint", .5), ("hide", .3), ("hide", .65),
                ("iron", .4), ("stone", .4), ("rock", .5), ("soot", .4)]
    SEED = 1937

    def gear(self, body):
        collar(body)
        pauldron(body)
        manacles(body)
        belt_and_cloth(body)

    def hammer(self, m):
        maul(m)

    def axe(self, m):
        cleaver(m)
