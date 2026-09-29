"""The excavations (Blender side), IBFEXCAV mesh coordinates (identity bone; the citadel's frame).
EA's pit (sliced 2026-09-29): a terraced drum r 54.2 filling the courtyard, its rim at z 20.8, a
floor at z 13 from r 21.8 (round the wizard's tower) to r 43; three shaft mounds on the floor
(base r 10 at z 13, rim r 5.2..6.6 at z 22.8, the shaft open to z 2); a winding tower at y 40..57
and the animated A-frame derrick (IBFEXCAVAT2.., x -9..42, y -34..9), both EA's.

The pits of Isengard: fire and smoke out of every shaft (real fire; on the south shaft a glowing
grate across its mouth and a ring of iron stakes round its rim - the two north shafts stay open for
EA's rising bucket and rope), spoil, logs and a loaded ore cart on the free north-east floor,
lanterns on posts, iron spikes along the upper terrace leaning in over the pit. Kept clear: the A-frame's
and the bucket's swing, the winding tower, the wizard's tower (r < 29), the burning forges
(x < -22, |y| < 22) and the excavations' destructible chute and ladders."""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z

FLOOR = 13.0
SHAFTS = [(-18.5, 27.5), (16.8, 27.5), (-0.2, -31.8)]   # the mounds' centres; rim r 6.6 at z 22.8, mouth r 4.3
OPEN = 2                                # the two north shafts stay open: EA's bucket (IBFEXCAVAT5) and its
                                        # rope (AT2, skinned) rise out of them and swing across, within r 9
                                        # above z 18, all through IBFExcavAN (swept every 2nd frame)


def shaft(kit, c):
    """The south shaft made the pit's furnace flue: the citadel's needle chimney out of its mound
    (flange on the rim at z 21, a glowing throat at z 50, its crown under the A-frame's pulley, whose swing
    comes no lower than z 58.8 over it), iron stakes round the rim."""
    cx, cy = c
    out = kit.needle_stack((cx, cy), 45.0, 5.0, 3.6, 21.0, 50.0, collar=0.45)     # corners clear of the skip
    for i in range(6):                                  # stakes round the rim, leaning out
        a = 2 * math.pi * (i + 0.5) / 6
        d = V((math.cos(a), math.sin(a), 0))
        p = V((cx, cy, 22.4)) + d * 7.4
        out.append(kit.beam(p - Z * 1.2, p + (d * 0.35 + Z).normalized() * 5.5, 0.34, "iron", 0.0))
        out.append(kit.beam(p + Z * 1.5, p + Z * 1.5 + d * 0.6, 0.22, "trim"))
    return out


def yard(kit):
    """The north-east floor: a loaded ore cart, spoil, a log stack; lanterns on posts."""
    out = kit.slag_cart(V((36.0, 17.0, FLOOR)), V((0.35, 0.94, 0)), 1.2)
    out += kit.slag_heap(V((33.0, 8.5, FLOOR)), 3.6, 3.0, seed=2, embers=2)
    out += kit.log_stack(V((40.5, 5.0, FLOOR)), V((0.2, 0.98, 0)), 7.0, 0.8, rows=2)
    for p in ((28.5, 19.0), (-24.0, 37.5), (4.0, -41.0)):
        out += kit.post_lantern(V((p[0], p[1], FLOOR)), 5.0)
    return out


ARCS = [(25.0, 60.0), (118.0, 150.0), (222.0, 240.0), (300.0, 335.0)]    # clear of the winding tower,
                                        # the ladders, the burning forges and the A-frame's swing


def rim(kit, r=41.5, z=17.5):
    """Iron spikes along the pit's upper terrace (r 41.5; EA's rim r 54 runs under the citadel's
    wedge towers, whose inner faces stand at r 44), leaning in over the pit, in four arcs."""
    out = []
    for a0, a1 in ARCS:
        n = max(3, int((a1 - a0) / 5.0))
        for i in range(n):
            a = math.radians(a0 + (a1 - a0) * (i + 0.5) / n)
            d = V((math.cos(a), math.sin(a), 0))
            base = d * r + Z * (z - 0.6)
            L = 5.0 + 1.6 * math.sin(i * 2.3)
            out.append(kit.tube([base, base + (Z - d * 0.35).normalized() * L * 0.6, base + (Z - d * 0.35).normalized() * L],
                                [0.55, 0.3, 0.0], "iron", k=4, cap0="iron", cap1=None, phase=math.pi / 4))
    return out


def build(kit):
    out = []
    for i, c in enumerate(SHAFTS):
        if i < OPEN:
            kit.fire(V((c[0], c[1], 21.0)), "chimney")
        else:
            out += shaft(kit, c)
    return out + yard(kit) + rim(kit)
