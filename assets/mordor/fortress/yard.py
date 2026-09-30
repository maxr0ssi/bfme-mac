"""The Mordor citadel's walks (Blender side): the orcs' war-works up where the RTS camera sees them.

The walk is at z 51 between 32.1 and 48.1 from the centre on every side. Kept clear: the magma
cauldrons on the -X walk (y < 22), the fire arrows on the gatehouse (x 32.6..51.6, |y| < 9.5, from
z 60), the tower bases in the corners.

    +Y walk     a forge (a stone hearth with its fire, an anvil with white-hot work, a great
                bellows), a jagged forge flue to z 97 behind it (its orange fire, "chimney", and over
                it EA's heavy dark plume alone, "plume"), two fire baskets, an ash heap
                (seen across the courtyard, faces to the camera; the +X walk hides its props behind
                EA's parapet spikes)
    -Y walk     an orc crane swinging a cage out over the -Y face (z 62..69, outside the wall), two
                fire baskets, an ash heap
"""
from mathutils import Vector as V

WALK = 51.0
X, Y = V((1, 0, 0)), V((0, 1, 0))


def plus_y(kit):
    c = V((0.0, 40.5, WALK))
    out = kit.hearth(c, X, -Y, w=6.5, d=4.2, h=2.8, hood=5.0)
    anvil = V((1.5, 35.4, WALK))
    out += kit.anvil(anvil, X, 1.4) + kit.glowing_work(anvil + V((0, 0, 3.9)), X, 1.4)
    out += kit.bellows(V((-7.2, 41.0, WALK)), X, 1.4)
    out += kit.flue((13.5, 45.0), 0.0, 4.6, 3.2, WALK - 0.5, 97.0, lean=(-1.2, -0.6))
    kit.fire(V((12.3, 44.4, 101.0)), "plume")       # the forge's heavy smoke, over the flue's fire
    for x in (-19.0, 22.0):
        out += kit.fire_basket(V((x, 34.6, WALK)), 1.8, 5.2)
    out += kit.ash_heap(V((23.5, 43.0, WALK)), 3.4, 2.6, seed=2)
    return out


def minus_y(kit):
    out = kit.crane(V((-6.0, -41.0, WALK)), -Y, h=29.0, reach=13.6, drop=12.5)
    for x in (-20.0, 17.0):
        out += kit.fire_basket(V((x, -34.6, WALK)), 1.8, 5.2)
    out += kit.ash_heap(V((10.0, -43.5, WALK)), 3.2, 2.4, seed=5)
    return out


def build(kit):
    return plus_y(kit) + minus_y(kit)
