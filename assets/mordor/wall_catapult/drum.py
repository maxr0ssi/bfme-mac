"""The wall catapult (Blender side): EA's spiked drum and its wall kept whole, the drum crowned as the
citadel's towers are and split by lava.

    crown       the family's claw on the drum's rim (pass 2): thirteen jagged spikes (the crowns' Horn,
                steel outer edge, a hook down, lava seams on the tall ones; no inner teeth) round its
                outer half (-90..90 degrees), rising from the parapet (r 21.2, z 52.5) and leaning in, to
                z 67 and 65; open in the middle over the catapult and clear of its swing
    baskets     two clawed fire baskets in the claw's gaps (+-52.5 degrees), orange fire ("brazier")
    cracks      forked cracks glowing from within up the drum's flat flute panels (z 24.5..39.5),
                between EA's fringe of spikes below and its spiked crown above
    embers      at the roots of the two front cracks

The catapult (EA's MordorFortressCatapult, model MBFWCatap, spawned at (-16, 0, 48) and turning to
its target; its animation MBFWCatap.MBFWCatap measured frame by frame, 2026-09-30): its frame sweeps
r 18.5 round (-16, 0) up to z 90; its arm and stone sweep out to r 41.4 but never come lower than z
57.9 between r 18 and 20 from that axis, 68.5 between 20 and 24, 62.2 beyond. Every face of ours
above z 57 stays 20 or more from the catapult's axis and under z 67.5 there (the check is in the
recipe's README). The top (EA's P1: the drum's octagon within r 19.4 of its axis and the wall walk)
stays clear.
"""
import math

from mathutils import Vector as V

from ..shapes_addons import claw, fissure, plane

AXIS = V((-14.8, 0.0, 0.0))
# (degrees round the axis, the panel's radius at z 26..38 on EA's mesh)
PANELS = ((0.0, 19.04), (15.0, 19.77), (-15.0, 19.77), (30.0, 19.6), (-30.0, 19.59), (90.0, 19.34), (-90.0, 19.34))
RIM, RIM_Z = 21.2, 52.5


def crown(kit):
    spikes = [(deg, RIM, 14.5 if k % 2 == 0 else 12.5, 20.6 if k % 2 == 0 else 20.7)
              for k, deg in enumerate(range(-90, 91, 15))]
    out = claw(kit, AXIS, RIM_Z, spikes, w=1.15, tall_at=14.0, inner=False)
    for s in (-1, 1):
        a = math.radians(52.5 * s)
        out += kit.fire_basket(AXIS + V((math.cos(a), math.sin(a), 0)) * 22.3 + V((0, 0, 54.0)), 1.4, 4.0)
    return out


def cracks(kit):
    out = []
    for i, (deg, r) in enumerate(PANELS):
        a0 = math.radians(deg)
        n = V((math.cos(a0), math.sin(a0), 0))
        t = V((-n.y, n.x, 0))
        out += fissure(kit, plane(AXIS + n * r, t, n), 0.0, 24.5, 15.0, w=0.9, seed=i * 2.3, segs=6, branches=1)
        if deg in (15.0, -15.0):
            kit.fire(AXIS + n * (r + 0.4) + V((0, 0, 25.5)), "embers")
    return out


def build(kit):
    return crown(kit) + cracks(kit)
