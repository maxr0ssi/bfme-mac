"""The Goblin citadel's gate (Blender side), on EA's +X front: the dragon's mouth.

EA's gate (WBFORTRESS coordinates): jambs at |y| 10.4..20.4 up to z 40, the opening |y| < 10.4
from the floor (z 7.5) to the dragon's lower jaw (z 41), the dragon's head above (x 25..58,
z 41..68), its horns rising at |y| 19..20 to z 67, the stone tongue of a ramp (x 45..70,
|y| < 16, z 0..6). The doors (WBFDoor) swing out through x 44.5..57.1, |y| <= 13.7, z 7.5..44.4
(the open animation, measured) and in to x 34.9 when damaged: nothing new stands there, and
nothing on the ramp where the units walk. What is added, in front of it:

    tusks      two great bleached tusks rising from the ground at |y| 19.5 and arching in over
               the dragon's head (clear of the doors: at z 44.4 they are still at |y| > 17),
               iron-collared, a hide hung from each on a hook
    jaws       rows of bone fangs standing along both sides of the tongue (|y| 14.4..16, x 57.6..68)
    trophies   a skull pile at each tusk's foot, an impaled skeleton beyond each
    braziers   an iron fire bowl on the front walk either side of the dragon
    banners    two ragged house-colour banners on bone spars either side of the gate
"""
from mathutils import Vector as V

A, T, N = V((0, 0, 0)), V((0, 1, 0)), V((1, 0, 0))            # the front face: u = y, d = x
TUSK = [(61.0, 19.5, 0.4), (61.8, 21.5, 29.0), (60.5, 17.5, 54.0), (55.5, 8.6, 60.5)]
PILE, IMPALED = (64.0, 26.5), (61.5, 32.0)
BANNER = (47.5, 27.2, 50.5, 7.4, 21.0)                         # x of the wall, |y|, z top, width, length


def bezier(ctrl, n):
    p0, p1, p2, p3 = (V(p) for p in ctrl)
    return [p0 * (1 - s) ** 3 + p1 * 3 * s * (1 - s) ** 2 + p2 * 3 * s * s * (1 - s) + p3 * s ** 3
            for s in (i / n for i in range(n + 1))]


def tusk_points(sy):
    return bezier([(x, sy * y, z) for x, y, z in TUSK], 9)


def build(kit):
    out = []
    for sy in (-1, 1):
        pts = tusk_points(sy)
        out.append(kit.tube(pts, kit.taper(3.1, len(pts) - 1, 0.7), "bone", k=8, cap0="bone", cap1=None))
        for i, r in ((1, 3.55), (3, 3.2)):                          # iron collars, riveted
            d = (pts[i + 1] - pts[i - 1]).normalized()
            out.append(kit.tube([pts[i] - d * 0.9, pts[i] + d * 0.9], [r, r], "iron", k=8, cap0="iron", cap1="iron"))
        hook = pts[5] + V((0.0, sy * 2.6, -1.0))
        out += kit.carcass(hook, 7.5, 1.7, facing=(1, 0, 0))
        # the jaws: fangs standing along the tongue's sides, outside the doors' sweep
        a = V((0, sy * 15.2, 0))
        out += kit.fangs(a, N, V((0, sy, 0)), 57.6, 68.0, 0.0, 7.0, 5, -0.8, 0.8, down=False, seed=3 + sy)
        out += kit.skull_pile(V((PILE[0], sy * PILE[1], 0.0)), 4.2, 3, 2.6, seed=2 + sy, face=(1, 0.3 * sy, 0))
        out += kit.impaled(V((IMPALED[0], sy * IMPALED[1], 0.0)), 21.0, 10.0, facing=(1, -0.25 * sy, 0))
        out += kit.brazier(V((39.5, sy * 27.0, 55.2)), 2.2, 3.2)
        x, y, zt, w, length = BANNER
        out += kit.banner(V((x, sy * y, 0)), T, N, 0.0, zt, w, length, d=1.6, mark="eye")
    return out


def gore_anchors():
    """(x, y, z, radius, run) of the gate's bleeding trophies, for the Gore paint layer."""
    out = []
    for sy in (-1, 1):
        out.append((IMPALED[0], sy * IMPALED[1], 21.0 - 4.0, 2.5, 10.0))
        out.append((PILE[0], sy * PILE[1], 0.8, 2.6, 2.0))
        tip = tusk_points(sy)[-2]
        out.append((tip.x, tip.y, tip.z, 2.2, 6.0))
    return out
