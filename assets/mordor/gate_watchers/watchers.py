"""The Silent Watchers (Blender side): EA's gate and its three-headed Watcher kept whole; the
Watchers wake.

    eyes        each of the three vulture heads' eyes an almond of Morgul witch-light (tag "witch"):
                the only green on the expansions, the Watchers' malice (the one accent)
    the arch    the barbed bottom of a raised portcullis in the gate's arch (both faces)
    fire        two clawed fire baskets on the gate's wall top (z 32), orange fire ("brazier")

The heads (EA's vertices): the statue's axis at (-20.5, 0); three identical heads a quarter turn
apart facing +X, +Y and -Y, each from the skull (8.5 out, z 59) to the beak's tip (17.4 out, z 55);
the eye socket a ring of four vertices 9.3 out, 3.05 to each side, z 56.0..57.3.
"""
import math

from mathutils import Vector as V

from ..shapes_addons import arch_teeth, witch_eye

X, Y, Z = V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))
AXIS = V((-20.5, 0.0, 0.0))
HEADS = (0.0, 90.0, -90.0)                      # the heads' facings
WALL = 7.52                                     # the gate wall's faces (x -65.75..-30.49, z 0..32)


def eyes(kit):
    out = []
    for deg in HEADS:
        f = V((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0))
        s = V((-f.y, f.x, 0))
        for side in (-1, 1):
            p = AXIS + f * 9.6 + s * (side * 2.95) + Z * 56.7
            out += witch_eye(kit, p, f, s * side + f * 0.35, length=2.3, height=1.15, depth=0.45)
    return out


def baskets(kit):
    out = []
    for x in (-48.0, -36.5):
        out += kit.fire_basket(V((x, 0.0, 32.0)), 1.9, 5.0)
    return out


def build(kit):
    return eyes(kit) + baskets(kit) + arch_teeth(kit, -52.0, -41.5, WALL, 16.5, 21.0, teeth=6, r=0.5, length=1.1)
