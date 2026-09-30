"""The Mordor battle tower (Blender side), CYLINDER01 mesh coordinates (the bone is the root, 0.1
off the axis). EA's tower (measured 2026-09-30): an eight-pointed star shaft on the axis (0.12,
0.13); a foot with four spurs (r 15.3 at 0, 80, 170, 270 degrees, z 0..10); the shaft r 7..9.2
(z 20..45) flaring to a spiked collar (r 13.8, z 51), a neck r 6.5..7.9 (z 55..73), then the head
flaring to r 12.3 (points at 0, 40, 80, 130, 170, 220, 270, 310 degrees, valleys r 9 between them)
up to its roof at z 112.4; round the roof a crown of spikes (r 11.4..12.5) to z 122.8; inside it a
shallow four-lobed dish (z 112.4 at the axis, its lobes' points at z 116..118).

Kept clear: the archers' bones ARROW_01..16 (r 7..8.3, z 89.2 and 91.7, inside the head).

    claw      eight jagged spikes rising from inside the roof's dish (r 7, z 111), leaning in round a
              fire bowl: four tall (tips z 137) on the diagonals with lava seams, four short (z 129)
    bowl      a jagged seven-sided iron bowl with a brass lip on the dish (z 112..119, r 4), orange
              fire ("furnace") and a dark smoke column
    eye       the Lidless Eye in the head's valley facing the camera (330 degrees, z 94..107)
    lava      lava welling out along the four diagonals from the foot (r 10..19.5), a seam up the
              shaft on the camera side
"""
import math

from mathutils import Vector as V

from .. import shapes_harad as H

C = (0.12, 0.13)                               # the shaft's axis
ROOF = 112.4
SPIKES = {"tall": ([(111.0, 7.2, (1.7, 1.3, 1.1)), (120.0, 7.9, (1.5, 1.2, 1.0)), (127.0, 7.1, (1.1, 0.9, 0.75)),
                    (132.0, 5.3, (0.7, 0.55, 0.45))], (2.3, 136.0)),
          "short": ([(111.0, 7.0, (1.3, 1.0, 0.9)), (118.5, 7.5, (1.0, 0.85, 0.7)), (124.0, 6.3, (0.6, 0.5, 0.45))],
                    (3.9, 128.0))}


def at(deg, r, z=0.0):
    a = math.radians(deg)
    return V((C[0] + r * math.cos(a), C[1] + r * math.sin(a), z))


def crown(kit):
    out = H.claw(kit, C, SPIKES, count=8, phase=0.0)
    out += H.jag_bowl(kit, C, ROOF - 0.4, ROOF + 9.6, 5.4, kind="furnace", smoke=True, seed=0.4)
    return out


def eye(kit):
    deg = 330.0
    n = V((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0))
    t = V((-n.y, n.x, 0))
    return kit.eye(at(deg, 9.1), t, n, 0.0, 94.0, 4.4, 12.5, d=0.0)


def lava(kit):
    out = []
    for i, deg in enumerate((315.0, 45.0, 225.0, 135.0)):
        out += kit.lava_channel([at(deg, 9.8), at(deg + 3.0, 14.0), at(deg - 2.0, 18.0)], w=1.5, kerb=0.7, h=1.2,
                                seed=i + 0.5, sides=(-1, 1), rafts=False, pitch=3.5)
        kit.fire(at(deg, 15.0, 0.4), "embers")
    # a seam up the shaft's camera side (its rib at 320 degrees: r 10.6 at the foot to 8.5 at z 45)
    pts = [at(320.0 + dd, r, z) for dd, r, z in ((0, 10.7, 0.5), (1.5, 10.3, 8.0), (-1.0, 9.7, 17.0), (1.0, 9.35, 26.0),
                                                   (-0.5, 8.8, 36.0), (0.5, 8.4, 43.0))]
    out += kit.face_crack(pts, (math.cos(math.radians(320)), math.sin(math.radians(320)), 0), w=1.0, depth=0.3)
    return out


def build(kit):
    return crown(kit) + eye(kit) + lava(kit)
