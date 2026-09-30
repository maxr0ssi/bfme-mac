"""The barricade (Blender side): EA's wall and square tower kept whole, the tower crowned as the
citadel's towers are.

    crown       inside the tower's open top (its floor at z 111.1, EA's merlons to z 120.8) a claw of
                eight jagged, hooked spikes (the crowns' Horn: steel outer edge, teeth, a hook, lava
                seams on the tall four) leaning in round a real fire ("brazier"), to z 128 (EA's tower tops at 120.8)
    the Eye     the Lidless Eye in the pointed window on each of the tower's broad faces (y +-7.87,
                z 75.3..94.3), where EA has a shallow recess
    lava        forked cracks glowing from within up the tower's broad faces and the wall's outer end,
                from the top of EA's base plate (BIB, z 9.45) up (shapes_addons.fissure)
    the arch    the barbed bottom of a raised portcullis in the wall's arch (both faces)

Kept clear: the walk on the wall (EA's P1, z 50, |y| < 7.5, x -65.75..8.4) and its archers' bones
(ARROW_01..04, z 51), the base plate BIB (EA's, z 0..9.45).
"""
from mathutils import Vector as V

from ..shapes_addons import arch_teeth, claw, fissure, plane, ring

X, Y, Z = V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))
AXIS = V((-19.25, 0.0, 0.0))                   # the tower's axis (x -28.79..-9.62)
TOP = 111.1                                    # the floor inside its open top
LOWER = 9.59                                   # the tower's broad faces below z 71
UPPER = 7.87                                   # the broad faces of its upper part, with the windows
WALL = 7.52                                    # the wall's faces


def crown(kit):
    out = claw(kit, AXIS, TOP - 1.8, ring(8, 22.5, 7.2, 18.7, 4.2, 0.7), w=1.0)
    out.append(kit.facet_lump(AXIS + Z * (TOP + 0.9), 1.9, "ember"))
    kit.fire(AXIS + Z * (TOP + 1.8), "brazier")
    return out


def eyes(kit):
    out = []
    for a, t, n, u in ((V((0, -UPPER, 0)), X, -Y, -19.07), (V((0, UPPER, 0)), -X, Y, 19.34)):
        out += kit.eye(a, t, n, u, 76.2, 7.2, 17.4, d=-0.1)
    return out


def lava(kit):
    """Forked cracks glowing from within up the tower's broad faces and the wall's outer end, from
    the top of EA's base plate (z 9.45)."""
    out = []
    for a, t, n, runs in ((V((0, -LOWER, 0)), X, -Y, [(-24.5, 30.0, 1.3), (-14.0, 24.0, 1.1)]),
                          (V((0, LOWER, 0)), -X, Y, [(24.5, 24.0, 1.1), (14.0, 30.0, 1.3)]),
                          (V((0, -WALL, 0)), X, -Y, [(1.5, 22.0, 1.1)]),
                          (V((0, WALL, 0)), -X, Y, [(-1.5, 22.0, 1.1)])):
        for i, (u, h, w) in enumerate(runs):
            out += fissure(kit, plane(a, t, n), u, 9.45, h, w=w, seed=u * 0.7 + i, segs=8, branches=2)
    return out


def build(kit):
    return crown(kit) + eyes(kit) + lava(kit) + arch_teeth(kit, -52.5, -41.0, WALL, 33.5, 38.5, teeth=6, r=0.55,
                                                           length=1.3)
