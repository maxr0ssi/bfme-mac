"""The Angmar citadel's crown (Blender side): the Witch-king's crown rising out of the courtyard
well from a ring cairn of black stone and ice, the cold fire burning in craters in the ring.

EA's well (KBFORTRESS mesh coordinates, measured 2026-10-01): the inner face of the ring at r 46.5
(z 0..39.4), a corbel at r 44 (z 40.4..42.2), the inner parapet at r 49.2 (z 44.1..56.8), the walk
at z 51.85 from r 50.5 out; the floor a shallow cone from r 46.5 at z 0 to z 9.9 at the centre.
EA's four great spires spring from the bastions (r 58..75 at z 86) and curve in over the well to
their tips at r 42, z 143.6: the crown stands under them and inside their reach.

Kept clear (pass 5, measured on EA's models in the citadel's coordinates, every model each upgrade
draws: healthy, the build-up rising out of the ground, damaged, rubble):
- the sanctum (UPGRADE_IVORY_TOWER, KBFSanctum: rises out of the middle of the well): r <= 20.3
  round the axis from the floor to z 175.4 (plinth r 17.3 z 0..12, shaft r 15.9, six ribs r 18.1 at
  z 42..74, skirt r 20 at z 78 to r 11.6 at z 98, fins, crown). Nothing of ours inside r 22.
- the House of Lamentation (UPGRADE_HOUSE_OF_HEALING, KBFHoLa, over the gate): its drum's back at
  r 39.2 on the gate's axis (z 90..104; the build-up raises it through every height below), r 42.2
  at z 40..50, its wing's well side r >= 44.6 (corners at (34.2, +-28.7), z 55..71). The +X tine
  keeps r < 38 on the axis.

    tines       four forged iron tines on the building's axes (r 30 at the floor, flaring out a
                little) to z 120, widest (19 across) just above the walk: a raised spine, steel
                edges, barbs hooking up off both edges, two riveted bands above the walk, a rune
                groove glowing cold blue up the spine, and from z 95 the point cased in ice -
                a rime collar, crystals growing out of it, icicles off the barbs (shapes_tine.py)
    ring        a ring cairn of black stone and ice shards round the sanctum's ground (r 23..36):
                a heap round each tine's root, a cairn on each diagonal between them with a crater
                in its top; the middle left open (the sanctum rises there when built)
    fire        the cold fire out of the four craters (SagekitColdFire, ice-blue to white, and a
                blue-black plume: "coldfire" on the NE and SW diagonals, the fire alone, "coldflame",
                on the SE and NW)
"""
import math

from mathutils import Vector as V

# the tines (pass 4, Max: "reduce a few ... just 4 more detailed ones", "ice cold tips, like frozen style"):
# keys [(z, r, half width, half depth)], tip (r, z); barbs [(z, edge, depth)]; riveted bands; the rune's run;
# the frost line. Pass 5: the ring drawn in by IN (pass 4 stood at r 38 to the tip at 42, where the +X
# tine's frozen point met the House of Lamentation's drum), the tines themselves unchanged.
IN = 7.0
KEYS = [(z, r - IN, W, D) for z, r, W, D in
        [(0.5, 38.0, 5.0, 2.4), (40.0, 37.6, 7.0, 2.8), (64.0, 38.2, 9.6, 3.0), (82.0, 39.4, 8.0, 2.7),
         (98.0, 40.8, 4.8, 2.1)]]
TIP = (42.0 - IN, 120.0)
BARBS = [(68.0, 1, 0.6), (74.0, -1, 0.6), (84.0, 1, 0.6), (90.0, -1, 0.6), (100.0, 1, 0.65), (106.0, -1, 0.65),
         (112.0, 1, 0.55)]
BANDS = [58.5, 62.5]
RUNE = (66.0, 92.0)
FROST = 95.0
# on the building's axes (the gate +X): EA's bastion windows on the well side (35..55 degrees round each
# diagonal) look out between them
TINES = [0.0, 90.0, 180.0, 270.0]

# the ring cairn (pass 5): nothing inside KEEP (the sanctum, r 20.3, and a margin); a heap round each tine's
# root and a crater cairn on each diagonal: (degrees, r of its centre, spread, height, shards, crater fire)
KEEP = 22.5
ROOTS = [(deg, 31.5, 5.0, 24.0, 9, None) for deg in TINES]
CRATERS = [(45.0, 29.0, 6.0, 52.0, 11, "coldfire"), (135.0, 29.0, 6.0, 52.0, 11, "coldflame"),
           (225.0, 29.0, 6.0, 52.0, 11, "coldfire"), (315.0, 29.0, 6.0, 52.0, 11, "coldflame")]
OUTER = 40.0                     # no shard's point beyond this (EA's well wall at 46.5, the House's drum at 39.2)


def floor(r):
    """The well's floor at r: a shallow cone from z 9.9 at the centre to 0 at r 46.5."""
    return 9.9 * max(0.0, 1.0 - r / 46.5)


def _hash(*xs):
    v = math.sin(sum(x * (12.9898 + 7.233 * i) for i, x in enumerate(xs))) * 43758.5453
    return v - math.floor(v)


def heap(kit, c, spread, h, n, seed, hollow=0, thick=0.18, lean=0.5):
    """Black stone and ice shards heaped at c (a point on the ring, on the well's floor), the tallest
    (h) in the middle, shorter ones toward its edge leaning out; never in toward the crown's middle
    (the sanctum's ground): an inward lean or offset is folded back, and a shard's foot keeps its
    width outside KEEP. The feet go into the floor but not below z 0 (EA's courtyard piece goes no
    deeper: the damaged models' lifecycle checks hold ours to it)."""
    c = V((c[0], c[1], 0.0))
    ec = c.normalized()
    out = []
    for i in range(n):
        f = (i + hollow) / max(n - 1 + hollow, 1)
        a = 2 * math.pi * (i * 0.382 + _hash(seed, i) * 0.15)
        e = V((math.cos(a), math.sin(a), 0))
        rad = spread * (0.15 + 0.85 * f) * (0.7 + 0.3 * _hash(i, seed + 1))
        off = e * rad
        if off.dot(ec) < 0:
            off -= ec * (off.dot(ec) * 0.6)
        li = lean * (0.25 + 0.75 * f) * (0.8 + 0.4 * _hash(seed + 2, i))
        dh = e - ec * min(0.0, e.dot(ec))                        # no lean inward
        d = (V((0, 0, 1)) + dh * li + ec * 0.1).normalized()
        L = h * (1.0 - 0.55 * f) * (0.8 + 0.25 * _hash(seed + 3, i))
        w = max(0.6, L * thick * (0.8 + 0.4 * _hash(i, seed + 4)))
        p = c + off
        r = p.length
        if r - w < KEEP:
            p = p * ((KEEP + w) / r)
        p = V((p.x, p.y, floor(p.length)))
        tip = p + d * L
        if V((tip.x, tip.y, 0)).length > OUTER:                 # leaning out too far: stand it up
            d = (V((0, 0, 1)) + dh * li * 0.3).normalized()
        tag = "rock" if i % 3 == 2 else ("ice" if i % 2 else "rock")
        out += kit.shard(p, d, L, w, k=4 + (i % 3), seed=seed + i, tag=tag, bury=max(1.0, w), floor=0.0)
    return out


def ring(kit):
    """The ring cairn: a heap round each tine's root and a crater cairn on each diagonal, the cold fire
    in each crater (its rim: shards leaning out round the fire)."""
    out = []
    for i, (deg, r, spread, h, n, _) in enumerate(ROOTS):
        out += heap(kit, kit.polar((0, 0), r, deg, 0.0), spread, h, n, seed=11.0 + i * 3.7, lean=0.35)
    for i, (deg, r, spread, h, n, kind) in enumerate(CRATERS):
        c = kit.polar((0, 0), r, deg, 0.0)
        out += heap(kit, c, spread, h, n, seed=3.0 + i * 5.3, hollow=2)
        top = floor(r) + h * 0.9
        for j in range(5):                                   # the crater's rim: shards leaning out
            p = kit.polar(c, 3.2, j * 72.0 + 20.0 + 9.0 * i, top - 5.0)
            e = V((p.x - c.x, p.y - c.y, 0)).normalized()
            if e.dot(c.normalized()) < -0.3:                 # the inner side: lean along the ring, not in
                e = (e - c.normalized() * e.dot(c.normalized())).normalized()
            out += kit.shard(p, V((0, 0, 1)) + e * 0.5, 8.0 + 3.0 * ((j * 5 + i) % 3), 1.8, k=5, seed=i * 7 + j,
                             tag="ice" if (i + j) % 2 else "rock", bury=3.0)
        kit.fire(V((c.x, c.y, top + 1.0)), kind)
    return out


def tines(kit):
    out = []
    for i, deg in enumerate(TINES):
        e = V((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0))
        h = kit.CrownTine([(z, tuple((e * r)[:2]), (W, D)) for z, r, W, D in KEYS], e, e * TIP[0] + V((0, 0, TIP[1])))
        out += kit.forged_tine(h, BARBS, BANDS, RUNE, FROST + (-2.0, 1.5, -1.0, 2.0)[i], seed=i * 2.3)
    return out


def build(kit):
    return tines(kit) + ring(kit)
