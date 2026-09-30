"""The mumakil pen (Blender side), MUMAKILPEN mesh coordinates (identity bone). EA's pen (measured
2026-09-30): a pit (|y| < 18, x -40..38, its floor at z -3) between two decks at z 44 (|y| 20..30),
each with a log rail along its outer edge (y +-33, z 51, x -44..42) on posts (x -40.8, -18.8,
-1.6, 15.9, 37.9; heads z 54..58); outside the decks sloping berms of hide and earth (from z 27 at
y +-35 down to z 15 at y +-44); at -X a hide wall and slope (x -42..-58) with tall posts (-50, 26)
to z 66 and (-47.6, -24.5) to z 60; the +X end open (x 38..50), two posts at (44, +-22) to z 47;
tusks on the corners (tips at z 24..30).

Kept clear:
- the door (mumakil_pen_02, EA's, animated): a lid over the pit hinged at x -41.5, z 50.3. Its
  swing measured over every frame of its animations (sagekit/formats/w3dpose.py, 2026-09-30):
  MBMumkpenDOP (opening) x -43.2..35.6, |y| < 23.8, z 44.3..80.2; MBMumkpen_DROCD (damaged)
  x -43.2..36.9, |y| < 23.8, z 35.1..80.2; the widest swing lifts the far end 29 (about 24
  degrees). Nothing of ours in x -44..37.5, |y| < 24.5, z 35..81;
- the pit and the open +X end (|y| < 20): the mumakil's way, and EA's deck beams' ends past it
  (|y| 19..24, z 44..48, to x 50);
- EA's BANNERS, V1 and V2 (shown from levels 2 and 3), the house banner (MBHCMumkPen, its pole at
  (29.8, 22.3)), N_FIRE and N_WINDOW (the night lights).

    arch      pass 2's new mass over the open +X end (x 45.8): a stepped basalt plinth with a fire bowl
              each side, from each two ivory tusks rising over the mumakil's way (z 58 over |y| 20)
              and crossing at the crown (z 72) like sabres, a basalt saddle there with a fire bowl on
              it (orange fire and a heavy dark plume, to z 83), the Harad sun on a war-paint plate
              hung under it facing out, chains with hooks hanging from the tusks
    claws     on each berm between the rail's posts (x 7): a stepped basalt plinth, a fire bowl with a
              brass lip (orange fire, dark smoke), six ivory tusks bowing out and turning in over it
    howdahs   a spiked howdah frame on each deck (x -21, |y| 24.9..30.3, outside the door's swing):
              charred timber walls and deck, brass rails, a pointed canopy of the player's colour,
              steel spikes jutting out over the berm
    banners   two banners of the player's colour on the -Y rail (x -10 and 27), the sun and serpent
              in brass on each
    lava      open lava along the foot of the -Y berm (y -44.8), a basalt kerb on its berm side
"""
import math

from mathutils import Vector as V

from .. import shapes_harad as H

X, MY = V((1, 0, 0)), V((0, -1, 0))


# the berm claws: (x, y, the berm's z there)
CLAWS = [(7.0, -38.6, 23.0), (7.0, 38.6, 23.0)]
ARCH_X = 45.8                                   # the arch's plane, past EA's deck beams' ends (x < 50.6)
# one tusk of the arch in (y, z), from its foot on the -Y plinth over the lane to its point past the middle
# (a cubic Bezier): 2 or more over EA's deck beams' ends (|y| 19..24, z 44..48), z 58 over |y| 20
ARCH = [(-30.0, 5.0), (-32.5, 60.0), (-12.0, 80.0), (16.0, 70.0)]


def claws(kit):
    """On each berm between the rail's posts: a stepped basalt plinth, a fire bowl with a brass lip,
    six ivory tusks bowing out and turning in over the fire, the Harad sun on the plinth's face."""
    out = []
    for i, (x, y, zg) in enumerate(CLAWS):
        c = V((x, y, 0))
        out += H.stepped_plinth(kit, (x, y), zg - 7.0, [(4.3, zg + 3.0), (3.4, zg + 6.5)], seed=1.1 + i)
        out += H.jag_bowl(kit, (x, y), zg + 6.0, zg + 10.8, 3.9, kind="furnace", smoke=True, seed=2.0 + i, teeth=0, lip=H.BRASS)
        for j in range(6):
            a = math.radians(15.0 + 30 * i + 60.0 * j)
            e = V((math.cos(a), math.sin(a), 0))
            tall = j % 2 == 0
            out += H.tusk_through(kit, c + e * 3.6 + V((0, 0, zg + 1.5)), c + e * (2.4 if tall else 3.0) +
                                  V((0, 0, zg + (21.0 if tall else 16.5))), e, bulge=0.1, r=1.25 if tall else 1.05,
                                  bands=2 if tall else 1)
    return out


def _bezier(pts, n):
    p0, p1, p2, p3 = pts
    return [tuple(p0[k] * (1 - s) ** 3 + p1[k] * 3 * s * (1 - s) ** 2 + p2[k] * 3 * s * s * (1 - s) + p3[k] * s ** 3
                  for k in range(2)) for s in (i / n for i in range(n + 1))]


def arch(kit):
    """The great tusk arch over the open +X end: a stepped basalt plinth with a fire bowl each side,
    and from each two ivory tusks rising over the mumakil's way and crossing at the crown (z 72) like
    sabres; a basalt saddle on the crossing with a fire bowl on it (orange fire, a heavy dark plume),
    the Harad sun on an iron plate hung under it facing out, chains hanging from the tusks."""
    out = []
    for sy in (-1, 1):
        out += H.stepped_plinth(kit, (ARCH_X, sy * 32.0), -2.8, [(3.6, 4.0), (2.9, 8.0)], seed=3.0 + sy)
        out += H.jag_bowl(kit, (ARCH_X, sy * 33.0), 7.5, 12.0, 2.9, kind="furnace", smoke=True, seed=4.0 + sy, teeth=5, lip=H.BRASS)
        for dx in (-1.3, 1.3):                           # a pair of tusks, crossing the other side's pair
            pts = [V((ARCH_X + dx, sy * y, z)) for y, z in _bezier(ARCH, 12)]
            out += H.tusk_path(kit, pts, 2.6, bands=3)
        for yy in (14.0, 21.0):                          # chains with hooks hanging from the tusks
            y, z = min(_bezier(ARCH, 40), key=lambda q: abs(q[0] + yy))
            out += kit.hook(V((ARCH_X + 1.3, sy * y, z - 1.8)), 2.4, chain=5.0 + 2.0 * (yy > 15))
    out += H.stepped_plinth(kit, (ARCH_X, 0.0), 69.5, [(3.6, 72.8), (3.0, 74.3)], seed=5.0, seam=False)
    out += H.jag_bowl(kit, (ARCH_X, 0.0), 73.8, 78.2, 3.8, kind="furnace", smoke=False, seed=5.5, teeth=7, lip=H.BRASS)
    kit.fire(V((ARCH_X, 0.0, 81.0)), "plume")
    out += H.sun_plate(kit, V((ARCH_X + 1.8, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), 0.0, 62.5, 10.0)
    return out


def howdahs(kit):
    """A spiked howdah frame on each deck (outside the door's swing, |y| > 24), its spikes jutting
    out over the berm."""
    out = []
    for sy in (-1, 1):
        out += H.howdah(kit, V((-21.0, sy * 27.6, 43.8)), V((1, 0, 0)) if sy < 0 else V((-1, 0, 0)), w=15.0, d=5.4,
                        h=11.0, spike_sides=(-1,), walls=True, canopy=True)
    return out


def banners(kit):
    out = []
    for u in (-10.0, 27.0):
        out += H.harad_banner(kit, V((0, -33.4, 0)), X, MY, u, 50.4, 8.0, 13.5, d=1.0)
    return out


def lava(kit):
    out = kit.lava_channel([(-44.0, -44.8, 0.0), (-10.0, -44.9, 0.0), (22.0, -44.7, 0.0), (40.0, -44.8, 0.0)], w=0.9,
                           kerb=0.3, h=0.9, seed=3.0, sides=(1,), pitch=4.5)
    for x in (-26.0, 12.0):
        kit.fire(V((x, -44.8, 0.4)), "embers")
    return out


def build(kit):
    return claws(kit) + arch(kit) + howdahs(kit) + banners(kit) + lava(kit)
