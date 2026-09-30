"""The Gorgoroth spire (Blender side): EA's tower of the Eye kept whole (the keep, its skirt of
wedges, the shaft, the crown, the horned Eye) and set burning as the citadel's crowns burn.

    claws       on each corner of the keep's roof (z 75.2, where EA's skirt of wedges meets it) a
                claw of five jagged, hooked spikes (the crowns' Horn, a steel outer edge) round a real
                fire ("brazier"), to z 92: four fires round the foot of the shaft
    (a claw inside EA's crown round the Eye's stem was tried in pass 1 and cut: EA's crescent fills the
    crown, the spikes read as sticks poking into the Eye)
    seams       forked cracks glowing from within (shapes_addons.fissure; pass 1's seams read as painted
                flames) up the round shaft (z 84..100, four, on the diagonals) and up the keep's four
                buttresses (z 40..66, over the courtyard's walls, where the RTS camera sees them)
"""
import math

from mathutils import Vector as V

from ..shapes_addons import claw, cylinder, fissure, plane

Z = V((0, 0, 1))
CORNER = 13.6                                   # the claws' axes on the keep's roof corners (+-, +-)
ROOF = 75.2
SHAFT = 8.9                                     # the round shaft's radius (z 79..101)
BUTTRESS = 15.78                                # the buttresses' fronts on the keep's faces (|u| < 5.47, z 0..67)


def claws(kit):
    out = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = V((sx * CORNER, sy * CORNER, 0))
            base = math.degrees(math.atan2(sy, sx))
            spikes = [(base + 180 + d, 3.4, h, rt) for d, h, rt in
                      ((-72, 17.0, 1.5), (0, 12.0, 1.9), (72, 17.0, 1.5), (144, 12.5, 1.9), (-144, 12.5, 1.9))]
            out += claw(kit, c, ROOF - 0.6, spikes, w=0.8, tall_at=16.0)
            out.append(kit.facet_lump(c + Z * (ROOF + 0.9), 1.6, "ember"))
            kit.fire(c + Z * (ROOF + 2.0), "brazier")
    return out


def seams(kit):
    out = []
    for k in range(4):                               # up the round shaft, on the diagonals
        P = cylinder((0, 0), SHAFT, 45 + 90 * k)
        out += fissure(kit, P, 0.0, 84.0, 16.0, w=0.9, seed=k * 2.0, segs=6, branches=1, spread=0.45)
    X, Y = V((1, 0, 0)), V((0, 1, 0))
    B = BUTTRESS
    for k, (a, t, n) in enumerate(((V((B, 0, 0)), Y, X), (V((0, -B, 0)), X, -Y), (V((-B, 0, 0)), -Y, -X),
                                   (V((0, B, 0)), -X, Y))):
        out += fissure(kit, plane(a, t, n), -0.6, 40.0, 26.0, w=1.1, seed=k * 3.0 + 1.0, segs=8, branches=2)
    return out


def build(kit):
    return claws(kit) + seams(kit)
