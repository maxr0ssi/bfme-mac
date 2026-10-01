"""The Angmar citadel's walls (Blender side): frost on the ring - ice growing out of the feet,
icicles under the parapet's lip.

EA's curtain (KBFORTRESS mesh coordinates, ray-cast 2026-10-01): a ring; between the bastions its
plinth at r 73.8 to z 10, the wall battered from r 72 (z 20) to r 69.4 (z 56), its top at z ~57.
The bastions on the diagonals stand to r 94 at the foot (91.8 at z 56), the wall towers at
(+-17, +-72) and (-72, +-17) to r 84 at the foot, coned to z 77; the gate along +X (the ramp
|y| < 22 out to x 107.6). The Ice Walls upgrade's shell (ICEWALL) lies 1.5..3 outside the curtain
(r 75..76.4 at the foot, 70.6..71.2 at z 56): the icicles hang outside it, the clusters stand
on the ground beyond it.

    clusters    angular ice-crystal clusters on the ground beyond it, a few black stone shards
                among them: a great one on each side of the gate's ramp (r ~106, to z ~26), smaller
                ones in the gaps the add-ons leave at the wall feet; small ones on the parapet's top
    icicles     rows of icicles under a rime crust along the curtain's top lip, on the faces the
                RTS camera sees (r 72)
    fissures    open cold glow welling out of the ground beside the gate's ramp, from the wall foot
                out toward each great cluster, a black stone kerb and ice shards breaking out of it
                (the cold counterpart of Mordor's lava)

Pass 5: the ground round the walls is the add-ons' (measured on EA's models, every model each draws:
healthy, the build-up rising out of the ground, damaged, rubble). The Spikes (AngmarFortressSpikes,
KBFSpike) stand 26 clumps at r 80..108 all round but the gate; a battle tower (KBArrowTower) on each
of the seven pads (EA's bases\fortress_angmar: the sides at r 110, the corners at (+-77, +-77)) runs
its wing back into the curtain or the bastion, so a corner pad's tower stands over the bastion's
point. Pass 4's clusters at the bastions' points (inside the corner towers), in the corners where
the bastions meet the curtain and its fissures along the -Y and gate-side feet (among the spikes'
clumps) moved to where none of them stands: the two great clusters to the gate's flanks (clear
ground beside the ramp), the small ones into the gaps between the clumps, the fissures beside the
ramp. The footprint stays inside EA's (x -83.1..107.6, y -83.3..83.1).
"""

from mathutils import Vector as V

LIP_Z = 56.6                     # the curtain's top lip
LIP_R = 69.4
# (degrees, r, spread, height): clear of the spikes' clumps and the battle towers on every pad
GREAT = [(29.0, 106.5, 6.5, 30.0), (-28.5, 106.5, 6.5, 30.0)]
CLUSTERS = [(68.5, 82.5, 3.0, 17.0), (114.0, 84.0, 2.8, 16.0), (158.5, 82.5, 3.0, 17.0), (147.0, 94.0, 2.2, 13.0),
            (-147.0, 83.0, 2.2, 13.0), (-123.5, 80.0, 1.6, 11.0), (-60.5, 92.0, 1.8, 12.0),
            (-26.0, 100.5, 2.5, 15.0)]
# (clear of EA's night windows in the curtain, r 71..72.7, z 21.9..49.2, and the wall towers; the banners
# hang at -63.5 and 115.5 degrees, yard.py)
ICICLE_ARCS = [(-120.5, -114.5), (-156.0, -149.5), (-30.5, -24.5), (24.5, 30.5), (59.5, 65.5), (149.5, 156.0)]
PARAPET = [-100.0, -116.0, -154.0, 64.0, 124.0, 154.0]
# cold glow fissures beside the gate's ramp, from the wall foot out toward each great cluster:
# ([(deg, r)], half width); the -Y side's broken by a spike clump at r 90 (a narrower run each side of it)
FISSURES = [([(31.5, 80.0), (31.0, 84.5), (30.0, 89.0), (29.0, 93.5), (28.5, 98.5)], 1.6),
            ([(-30.0, 80.5), (-29.8, 84.0), (-29.8, 87.5)], 1.2),
            ([(-28.0, 93.5), (-28.0, 98.5)], 1.6)]


def clusters(kit):
    out = []
    for i, (deg, r, spread, h) in enumerate(GREAT):
        c = kit.polar((0, 0), r, deg, 0.0)
        out += kit.ice_cluster(c, spread, h, n=13, seed=20.0 + i, lean=0.38, thick=0.17, stone="rock", floor=-0.6)
    for i, (deg, r, spread, h) in enumerate(CLUSTERS):
        c = kit.polar((0, 0), r, deg, 0.0)
        out += kit.ice_cluster(c, spread, h, n=7 if spread > 2.5 else 5, seed=i * 1.7, lean=0.4, thick=0.2,
                               stone="rock", floor=-0.6)
    for i, deg in enumerate(PARAPET):                        # small clusters on the parapet's top
        c = kit.polar((0, 0), 68.4, deg, 56.4)
        out += kit.ice_cluster(c, 1.8, 7.0, n=5, seed=40.0 + i, lean=0.55, thick=0.22)
    return out


def icicles(kit, a0, a1, step=8.0):
    """Icicle rows along the lip from a0 to a1 degrees, in straight runs of about `step` degrees."""
    out = []
    k = max(1, int(round((a1 - a0) / step)))
    for i in range(k):
        b0, b1 = a0 + (a1 - a0) * i / k, a0 + (a1 - a0) * (i + 1) / k
        p, q = kit.polar((0, 0), LIP_R, b0, 0.0), kit.polar((0, 0), LIP_R, b1, 0.0)
        t = (q - p).normalized()
        n = V((t.y, -t.x, 0))
        if n.dot(p) < 0:
            n = -n
        L = (q - p).length
        out += kit.icicles(p, t, n, 0.0, L, LIP_Z, 7.0, max(3, int(L / 2.2)), d=2.8, crust=2.4, w=1.6, seed=b0)
    return out


def fissures(kit):
    """Open cold glow ("flame") welling out of the ground beside the gate's ramp, a jagged kerb of
    black stone on the side away from the ramp, a few ice shards breaking out of it."""
    out = []
    for i, (run, w) in enumerate(FISSURES):
        pts = [kit.polar((0, 0), r, deg, 0.0) for deg, r in run]
        side = -1 if run[0][0] > 0 else 1                    # the kerb away from the ramp
        out += kit.lava_channel([tuple(p) for p in pts], w=w, kerb=0.7 * w / 1.6, h=0.9, seed=i + 1.0, sides=(side,),
                                rafts=False, pitch=4.0)
        for j in range(1, len(pts)):
            p = pts[j - 1].lerp(pts[j], 0.5)
            t = (pts[j] - pts[j - 1]).normalized()
            n = V((-t.y, t.x, 0)) * (1 if side < 0 else -1)          # (the left normal; the kerb side)
            out += kit.ice_cluster(p + n * (w + 0.4), 1.0, 6.0, n=3, seed=i * 3 + j, lean=0.3, thick=0.22, floor=-0.6)
    return out


def build(kit):
    out = clusters(kit) + fissures(kit)
    for a0, a1 in ICICLE_ARCS:
        out += icicles(kit, a0, a1)
    return out
