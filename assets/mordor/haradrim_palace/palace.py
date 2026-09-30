"""The Haradrim palace (Blender side), MBHRDPLC mesh coordinates (on the root bone), pass 2. EA's palace
(measured 2026-09-30): a great tent in a cross. The X arm's walls stand at y +-12.6..14.7 from
x -25 to 20 (a porch at x 19.9..26 before the +X door, |y| < 7.7); the Y arm's at x +-9.6..12 from
|y| 13 to its ends at y +-31 (its roof ends at y +-34). The roofs: the X arm's ridge at z 38.7..41
out to x +-30.7, its eaves at y +-20 (z 24..25); the Y arm's ridge at z 29.5..32.6; the peak at
z 47.2 (the origin), the roof round it at r 10 z 37..43, at r 17 z 30..40. Corner posts (heads at
x +-17..32, y +-19..24, z 33.8..34.4).

Kept clear (their own vertices, 2026-09-30):
- V1 (level 2, "ShowWalls"): the tusk ring: arcs rooted in the inner corners (x, y +-18..30, z 0..9)
  over the X ends (x +-30..36, z to 40), arches off the Y ends (x ~0, y +-33..51, z to 39).
- V2A (level 3, "ShowFlagsAndTower"): a howdah tower on the peak (its floor z 53..54 over x -15..9,
  |y| < 12; walls to z 67; four posts at (-18, +-16) and (10, +-16) to z 79) and a frame before the
  +X door (x 39..42, z to 48).
- EA's bonfire and its flame card (BONFIRE, FIRE: x 16..27, y -33..-23), the house banner's pole
  (17.2, -19.7), the lancer (MUHARALNCR, LANCE), BANNER_HARAD01 (x -17..14, z 32.8..69.5), the arrow
  bones ARROW_01..08 (the four arm ends, z 12.6 and 16.2).

    crown     the family motif on the peak: a stepped basalt plinth round the tent's top, a great
              fire bowl with a brass lip on it (orange fire and a heavy dark plume), and eight ivory
              tusks rising from the roof round it (r 19) and bowing in over it, tips to z 64. They stand
              between V2A's posts and clear of its walls: at level 3 they close round EA's tower
    claws     either side of the -Y door, on the ground: a stepped basalt plinth, a fire bowl
              with a brass lip (orange fire, dark smoke), six ivory tusks rising round it
    suns      the Harad sun in brass on a pointed war-paint plate: under the X arms' gable ends (s 11) and
              over the -Y door (s 10)
    banners   two banners of the player's colour hung from the X arm's -Y eave (8 x 16), the sun and
              serpent in brass on each
    bonfire   EA's bonfire gets real fire ("hearth"); its flame card is left out of the bakes
"""
import math

from mathutils import Vector as V

from .. import shapes_harad as H

Z = V((0, 0, 1))
X, Y = V((1, 0, 0)), V((0, 1, 0))
MX, MY = V((-1, 0, 0)), V((0, -1, 0))
PEAK = 47.2
# the crown's tusks: (angle, root r, root z (on the roof, less 2), tip r, tip z, root radius); between
# V2A's posts (at 58, 138, 222 and 302 degrees) and 1.5 or more clear of its walls (x -15..12, |y| < 13)
CROWN = [(0.0, 19.0, 37.5, 14.8, 64.0, 1.9), (30.0, 19.0, 31.0, 15.6, 61.0, 1.6), (90.0, 19.0, 30.0, 15.2, 64.0, 1.9),
         (160.0, 19.5, 31.5, 16.9, 61.0, 1.6), (180.0, 19.5, 37.0, 16.8, 64.0, 1.9), (200.0, 19.5, 31.5, 16.9, 61.0, 1.6),
         (270.0, 19.0, 30.0, 15.2, 64.0, 1.9), (330.0, 19.0, 31.0, 15.6, 61.0, 1.6)]
# the ground claws either side of the -Y door (the +Y door has no room: its eaves reach the box)
DOORS = [(-11.0, -36.1), (11.0, -36.1)]


def crown(kit):
    out = H.stepped_plinth(kit, (0.0, 0.0), 36.0, [(9.0, 44.0), (7.0, 47.5)], seed=0.3)
    out += H.jag_bowl(kit, (0.0, 0.0), 47.0, 52.6, 6.2, kind="furnace", smoke=False, seed=0.9, teeth=7, lip=H.BRASS)
    kit.fire(V((0.0, 0.0, 55.5)), "plume")              # the heavy dark plume over the crown's fire
    for deg, rb, zb, rt, zt, r in CROWN:
        a = math.radians(deg)
        e = V((math.cos(a), math.sin(a), 0))
        out += H.tusk_through(kit, e * rb + V((0, 0, zb)), e * rt + V((0, 0, zt)), e, bulge=0.12, r=r,
                              bands=2 if r > 1.7 else 1)
    return out


def claws(kit):
    out = []
    for i, (x, y) in enumerate(DOORS):
        c = V((x, y, 0))
        out += H.stepped_plinth(kit, (x, y), -3.5, [(4.4, 3.0), (3.5, 6.5)], seed=1.1 + i)
        out += H.jag_bowl(kit, (x, y), 6.0, 10.8, 3.9, kind="furnace", smoke=True, seed=2.0 + i, teeth=0, lip=H.BRASS)
        for j in range(6):                               # six tusks bowing out and turning in over the fire
            a = math.radians(30.0 * i + 60.0 * j)
            e = V((math.cos(a), math.sin(a), 0))
            tall = j % 2 == 0
            out += H.tusk_through(kit, c + e * 3.7 + V((0, 0, 1.5)), c + e * (2.4 if tall else 3.0) +
                                  V((0, 0, 22.0 if tall else 17.5)), e, bulge=0.1, r=1.25 if tall else 1.05,
                                  bands=2 if tall else 1)
    return out


def suns(kit):
    out = []
    for sx in (1, -1):                                   # under the X arms' gable ends
        out += H.sun_plate(kit, V((29.4 * sx, 0, 0)), Y if sx > 0 else MY, X if sx > 0 else MX, 0.0, 30.0, 11.0)
    out += H.sun_plate(kit, V((0, -35.0, 0)), X, MY, 0.0, 21.5, 10.0)      # over the -Y door
    return out


def banners(kit):
    """Two banners from the X arm's -Y eave (z 24.5 at y -20), the sun and serpent on each (the cloth
    leaves for the house-colour model)."""
    out = []
    for u in (-24.0, 26.5):
        out += H.harad_banner(kit, V((0, -20.2, 0)), X, MY, u, 23.8, 8.0, 16.0, d=0.8)
    return out


def bonfire(kit):
    kit.fire(V((21.5, -28.0, 2.0)), "hearth")
    return []


def build(kit):
    return crown(kit) + claws(kit) + suns(kit) + banners(kit) + bonfire(kit)
