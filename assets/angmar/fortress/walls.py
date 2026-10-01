"""The Angmar citadel's walls (Blender side): frost on the ring - ice growing out of the feet,
icicles under the parapet's lip.

EA's curtain (KBFORTRESS mesh coordinates, ray-cast 2026-10-01): a ring; between the bastions its
plinth at r 73.8 to z 10, the wall battered from r 72 (z 20) to r 69.4 (z 56), its top at z ~57.
The bastions on the diagonals stand to r 94 at the foot (91.8 at z 56), the wall towers at
(+-17, +-72) and (-72, +-17) to r 84 at the foot, coned to z 77; the gate along +X (the ramp
|y| < 22 out to x 107.6). The Ice Walls upgrade's shell (ICEWALL) lies 1.5..3 outside the curtain
(r 75..76.4 at the foot, 70.6..71.2 at z 56): the icicles hang outside it, the clusters stand
on the ground beyond it.

    clusters    angular ice-crystal clusters in the re-entrant corners where the bastions meet the
                curtain (r 80, 20 degrees either side of each bastion), a few black stone shards
                among them
                and a great cluster against each bastion's point (r 99, to z ~26); small ones on the
                parapet's top
    icicles     rows of icicles under a rime crust along the curtain's top lip, on the faces the
                RTS camera sees (r 72)
    fissures    open cold glow welling along the -Y and gate-side wall feet, a black stone kerb and
                ice shards breaking out of it (the cold counterpart of Mordor's lava)
"""

from mathutils import Vector as V

LIP_Z = 56.6                     # the curtain's top lip
LIP_R = 69.4
CLUSTERS = [(b + s * 21.0, 80.0, 9.0 + 2.0 * (k % 2)) for k, b in enumerate((45.0, 135.0, 225.0, 315.0))
            for s in (-1, 1)]
# (clear of EA's night windows in the curtain, r 71..72.7, z 21.9..49.2, and the wall towers)
ICICLE_ARCS = [(-71.0, -56.0), (-120.5, -114.5), (-156.0, -149.5), (-30.5, -24.5), (24.5, 30.5), (59.5, 65.5),
               (114.5, 120.5), (149.5, 156.0)]
PARAPET = [-100.0, -64.0, -116.0, -154.0, 64.0, 116.0]
# cold glow fissures along the feet the RTS camera sees: (from, to degrees, r of the run)
FISSURES = [(-113.0, -67.0, 79.0), (-41.0, -21.0, 77.4), (21.0, 41.0, 77.4)]


def clusters(kit):
    out = []
    for i, (deg, r, h) in enumerate(CLUSTERS):
        c = kit.polar((0, 0), r, deg, 0.0)
        out += kit.ice_cluster(c, 5.5, h * 1.9, n=8, seed=i * 1.7, lean=0.6, thick=0.2, stone="rock", floor=-0.6)
    for i, deg in enumerate((45.0, 135.0, 225.0, 315.0)):   # a great cluster against each bastion's point
        c = kit.polar((0, 0), 99.0, deg, 0.0)
        out += kit.ice_cluster(c, 8.0, 26.0, n=11, seed=20.0 + i, lean=0.5, thick=0.17, stone="rock", floor=-0.6)
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
    """Open cold glow ("flame") welling out of the ground along the wall feet, a jagged kerb of
    black stone on the outer side, a few ice shards breaking out of it; the glow runs up the
    plinth in frost cracks."""
    out = []
    for i, (a0, a1, r) in enumerate(FISSURES):
        k = max(2, int(round((a1 - a0) / 6.0)))
        pts = [kit.polar((0, 0), r + 0.5 * ((j * 7) % 3 - 1), a0 + (a1 - a0) * j / k, 0.0) for j in range(k + 1)]
        out += kit.lava_channel([tuple(p) for p in pts], w=2.4, kerb=0.8, h=1.0, seed=i + 1.0, sides=(-1,), rafts=False,
                                pitch=5.0)                  # (-1: right of a counter-clockwise run, outside)
        for j in range(1, k, 2):
            p = pts[j]
            n = (p - V((0, 0, 0))).normalized()
            out += kit.ice_cluster(p + n * 2.4, 1.3, 7.0, n=4, seed=i * 3 + j, lean=0.3, thick=0.22, floor=-0.6)
    return out


def build(kit):
    out = clusters(kit) + fissures(kit)
    for a0, a1 in ICICLE_ARCS:
        out += icicles(kit, a0, a1)
    return out
