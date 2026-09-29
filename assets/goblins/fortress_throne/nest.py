"""The dragon's nest (Blender side): EA's flared pedestal kept whole - its painted eye and scale
panels, the bowl at the top where the fire drake idles - and made a bone throne: an iron band
round its waist, great bleached tusks rising from the bowl's rim either side like a ribcage, fire
bowls on iron brackets under them, a horned troll skull nailed over the front, skull piles and
bones round its foot on the courtyard floor and in the bowl's corners.

EA's pedestal (WBFGTHRONE coordinates, measured): flared at the foot (x -20.6..22.1, |y| 18.8 at
z 2), narrowest at the waist (WAIST, z 36), flaring again to the bowl's rim (x -20..24, |y| 21.2 at
z 73; the rim's sides at |y| 20.3, z 70, RIM); the front face under the drake at x 15.9 (z 50) to
19.1 (z 60). P1 (x +-18.4, |y| 17.1, z 74.8) and B_DRAKE (12.8, 0, 74.5), the drake's perch, stay
clear: nothing new rises above the bowl inside the rim. In the citadel the throne stands in the
courtyard, whose floor rises from z 5 at the centre to 6.7 at r 28 (the walls' inner ring): the
foot's dressing stands on it, inside r 26.
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z

from .dragon import band
WAIST = [(-12.1, -10.75), (0.74, -11.55), (13.62, -10.78), (13.62, 10.78), (0.74, 11.55), (-12.1, 10.75)]
WAIST_Z = 36.0
# the tusks along each side of the rim: (x, |y| of the flare at z 66, length, radius)
RIM_TUSKS = [(-9.0, 17.0, 22.0, 1.9), (9.5, 16.9, 19.0, 1.7)]
BRAZIER = (0.8, 16.3, 57.0)                  # the bracket's foot on the flare (x, |y|, z)
TROPHY = (20.0, 0.0, 53.0, 7.6)              # the troll skull over the front (x, y, z, size)
# the foot's dressing on the courtyard floor: (x, y, skulls, skull size, seed)
PILES = [(25.0, 9.0, 4, 2.4, 1), (25.0, -9.5, 3, 2.2, 4), (-3.0, 21.0, 4, 2.3, 2), (-22.0, -15.5, 3, 2.3, 5),
         (-23.5, 12.5, 3, 2.2, 7)]
# the nest's lining: small skull heaps and bones in the bowl's front corners, beside the drake's
# perch (B_DRAKE, 12.8 units and more away): (x, |y|, skulls, size)
BOWL = [(17.8, 12.6, 3, 1.9), (8.0, 15.0, 2, 1.7)]
BONES = [((20.0, 17.0), (27.0, 13.5)), ((-14.0, -19.5), (-8.0, -22.0)), ((10.0, -20.5), (16.0, -18.0))]


def floor(x, y):
    """The citadel courtyard's floor height at (x, y)."""
    return 5.0 + 1.7 * min(math.hypot(x, y), 28.0) / 28.0


def build(kit):
    out = band(kit, WAIST, WAIST_Z, 3.4, th=0.85, inner=1.8, rivets=1, center=(0.8, 0.0))
    for e in (-1, 1):
        # the tusks rising off the rim either side, curving out and up like a ribcage
        for x, y, length, r in RIM_TUSKS:
            base = V((x, e * y, 66.0))
            out += kit.tusk(base, V((0.0, e * 0.55, 0.85)), V((0.08 * -math.copysign(1, x), -e * 0.35, 1.0)), length, r,
                            n=6, k=6, collar=True)
        # a fire bowl on an iron bracket out of each side of the flare
        bx, by, bz = BRAZIER
        foot = V((bx, e * by, bz))
        bowl = V((bx, e * (by + 4.6), bz + 1.0))
        out.append(kit.tube([foot - V((0, e * 1.0, 1.2)), foot + V((0, e * 1.6, -0.4)), bowl - Z * 1.2],
                            [0.55, 0.5, 0.45], "iron", k=4, cap0="iron", cap1="iron"))
        out += kit.brazier(bowl - Z * 2.4, 2.8, 2.6, legs=3)
        # the ring each shackle's chain runs to, bolted to the flare's front corner
        ring = V((18.9, e * 12.9, 63.0))
        n = V((0.62, e * 0.78, 0.0)).normalized()
        out.append(kit.tube([ring - n * 1.0, ring + n * 0.6], [1.1, 0.9], "iron", k=6, cap0="iron", cap1="iron"))
    # the troll skull nailed over the front, blood below it
    x, y, z, s = TROPHY
    out += kit.horned_skull(V((x, y, z)), (1, 0, 0), s, horn=1.25, detail=2)
    out += kit.spike(V((x + 1.2, 0, z + 1.3)) - V((4.0, 0, 0)), V((1, 0, 0.05)), 7.5, 0.5, k=4)
    # the foot: skull piles, bones and a few spikes on the courtyard floor
    for px, py, count, s, seed in PILES:
        c = V((px, py, floor(px, py) - 0.3))
        out += kit.skull_pile(c, 3.4, count, s, seed=seed, face=(math.copysign(1, px) * 0.7, math.copysign(0.7, py), 0))
    for e in (-1, 1):
        for i, (px, py, count, s) in enumerate(BOWL):
            out += kit.skull_pile(V((px, e * py, 74.4)), 2.4, count, s, seed=3 + i + e, face=(1, 0.4 * e, 0))
        out += kit.bone(V((20.5, e * 8.5, 75.0)), V((15.0, e * 10.5, 75.3)), 0.28)
    for (x0, y0), (x1, y1) in BONES:
        z = floor((x0 + x1) / 2, (y0 + y1) / 2) + 0.25
        out += kit.bone(V((x0, y0, z)), V((x1, y1, z + 0.3)), 0.32)
    return out


def gore_anchors():
    x, y, z, _ = TROPHY
    out = [(x + 1.0, y, z - 1.5, 3.2, 12.0)]
    for px, py, _, _, _ in PILES:
        out.append((px, py, floor(px, py) + 0.8, 2.8, 2.0))
    return out
