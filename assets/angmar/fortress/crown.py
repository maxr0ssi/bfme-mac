"""The Angmar citadel's crown (Blender side): the Witch-king's crown rising out of the courtyard
well, round a cold fire burning out of a cairn of black stone and ice.

EA's well (KBFORTRESS mesh coordinates, measured 2026-10-01): the inner face of the ring at r 46.5
(z 0..39.4), a corbel at r 44 (z 40.4..42.2), the inner parapet at r 49.2 (z 44.1..56.8), the walk
at z 51.85 from r 50.5 out; the floor a shallow cone from r 46.5 at z 0 to z 9.9 at the centre.
EA's four great spires spring from the bastions (r 58..75 at z 86) and curve in over the well to
their tips at r 42, z 143.6: the crown stands under them and inside their reach.

    tines       four forged iron tines on the building's axes (r 38 at the floor, flaring out a
                little) to z 120, widest (19 across) just above the walk: a raised spine, steel
                edges, barbs hooking up off both edges, two riveted bands above the walk, a rune
                groove glowing cold blue up the spine, and from z 95 the point cased in ice -
                a rime collar, crystals growing out of it, icicles off the barbs (shapes_tine.py)
    cairn       a cairn of black stone and ice shards in the middle (to z ~60), a crater in its top
    fire        the cold fire out of the crater (SagekitColdFire, ice-blue to white, and a blue-black
                plume: "coldfire"), more cold flames round it ("coldflame")
"""
import math

from mathutils import Vector as V

# the tines (pass 4, Max: "reduce a few ... just 4 more detailed ones", "ice cold tips, like frozen style"):
# keys [(z, r, half width, half depth)], tip (r, z); barbs [(z, edge, depth)]; riveted bands; the rune's run;
# the frost line
KEYS = [(0.5, 38.0, 5.0, 2.4), (40.0, 37.6, 7.0, 2.8), (64.0, 38.2, 9.6, 3.0), (82.0, 39.4, 8.0, 2.7),
        (98.0, 40.8, 4.8, 2.1)]
TIP = (42.0, 120.0)
BARBS = [(68.0, 1, 0.6), (74.0, -1, 0.6), (84.0, 1, 0.6), (90.0, -1, 0.6), (100.0, 1, 0.65), (106.0, -1, 0.65),
         (112.0, 1, 0.55)]
BANDS = [58.5, 62.5]
RUNE = (66.0, 92.0)
FROST = 95.0
# on the building's axes (the gate +X): EA's bastion windows on the well side (35..55 degrees round each
# diagonal) look out between them
TINES = [0.0, 90.0, 180.0, 270.0]
CAIRN = V((0.0, 0.0, 9.9))


def cairn(kit):
    """Black stone and ice shards heaped in the middle of the well, a ring of tall ones round a
    crater at the top where the fire burns."""
    out = kit.ice_cluster(CAIRN, 17.0, 42.0, n=14, seed=3.0, lean=0.45, thick=0.22, tag="rock", stone="ice",
                          hollow=2)
    for i in range(7):                                       # the crater's rim: shards leaning out
        p = kit.polar(CAIRN, 6.5, i * 360.0 / 7 + 10.0, CAIRN.z + 38.0)
        d = (p - V((0, 0, p.z))).normalized() * 0.55 + V((0, 0, 1))
        out += kit.shard(p, d, 12.0 + 4.0 * ((i * 5) % 3), 2.6, k=5, seed=i, tag="ice" if i % 2 else "rock",
                         bury=4.0)
    return out


def fire(kit):
    top = CAIRN.z + 42.0
    kit.fire(V((0.0, 0.0, top)), "coldfire")
    for i in range(4):
        kit.fire(kit.polar((0, 0), 3.2, 45.0 + 90.0 * i, top - 1.0), "coldflame")


def tines(kit):
    out = []
    for i, deg in enumerate(TINES):
        e = V((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0))
        h = kit.CrownTine([(z, tuple((e * r)[:2]), (W, D)) for z, r, W, D in KEYS], e, e * TIP[0] + V((0, 0, TIP[1])))
        out += kit.forged_tine(h, BARBS, BANDS, RUNE, FROST + (-2.0, 1.5, -1.0, 2.0)[i], seed=i * 2.3)
    return out


def build(kit):
    out = tines(kit)
    out += cairn(kit)
    fire(kit)
    return out
