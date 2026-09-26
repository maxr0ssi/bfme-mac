"""Motifs the Elven production buildings (barracks, forge, green pasture) share, built from the
Elven kit (assets/elves/shapes.py); Blender side (mathutils). Conventions as the kit's wall-face
pieces: an anchor `a`, the face's direction `t`, its outward normal `n` (t x n = -z), u along t,
z absolute, d along n.

    face            (a, t, n) of a wall face given as a point and an outward normal
    lancet_window   a pointed window: EA's lattice glass slab in a silver frame on a sill
    barge_board     a silver barge board with an enamel soffit along a gable's pointed outline
    coronet         a ring of gilt leaf blades (upright, facing out; smaller ones leaning out between)
    hanging_lantern a crystal lantern hanging on a gilt rod (where EA hung its night lanterns)
    crystal_light   the night light of a kit crystal lantern: a pane on its crystal, facing the camera
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import prism_uz


def face(point, normal):
    """(a, t, n) for a vertical wall face through `point` (x, y) with outward normal (nx, ny)."""
    n = V((normal[0], normal[1], 0)).normalized()
    return V((point[0], point[1], 0)), V((-n.y, n.x, 0)), n


def lancet_window(kit, a, t, n, u, half, z0, spring, apex, w=0.7, d=0.5, finial=True, k=6):
    """A pointed (lancet) window at u: EA's arched lattice window ("window": opaque glass) on a slab
    0.12 proud of the face, framed by the kit's pointed arch (silver front, enamel reveal) standing
    `d` proud, on a silver sill; a small gilt leaf over the tip. Pointed, not ogee: the glass slab
    is one convex polygon."""
    inner = kit.arch_outline(half, spring, apex, 0.0, k)
    poly = [(u - half, z0), (u + half, z0)] + [(u + x, z) for x, z in inner[:-1]] + \
           [(u, apex)] + [(u - x, z) for x, z in reversed(inner[:-1])]
    out = [prism_uz(a, t, n, poly, -0.3, 0.12, [None] * len(poly), "window", None)]
    out += kit.arch(a, t, n, u, half, z0, spring, apex, w=w, d0=0.0, d1=d, ogee=0.0, k=k, finial=finial)
    s = half + w + 0.35
    out.append(prism_uz(a, t, n, [(u - s, z0 - 0.55), (u + s, z0 - 0.55), (u + s, z0), (u - s, z0)], -0.2, d + 0.3,
                        [None, "trim", "top", "trim"], "trim", None))
    return out


def barge_board(kit, a, t, n, u, left, w=0.9, d0=0.0, d1=0.8):
    """A barge board over a gable whose outline is `left`: [(du, z)] from the eave (du > 0: the
    distance from the gable's axis at u) up to the apex (0, z), mirrored to the other side. Silver
    front and top edge, enamel soffit underneath (the outline's side); the back shows too (the
    board stands proud of the roof's outline). The joints between pieces are buried."""
    outer = kit._offset(left, w)
    out = []
    for s in (1, -1):
        for i in range(len(left) - 1):
            q = [(u + s * left[i][0], left[i][1]), (u + s * left[i + 1][0], left[i + 1][1]),
                 (u + s * outer[i + 1][0], outer[i + 1][1]), (u + s * outer[i][0], outer[i][1])]
            tags = ["enamel", None, "trim", "trim" if i == 0 else None]     # inner, joint, outer, joint
            out.append(prism_uz(a, t, n, q, d0, d1, tags, "trim|a", "trim"))
    return out


def coronet(kit, cx, cy, r, z, n=6, height=8.0, width=2.6, phase=0.0, small=True):
    """A crown of gilt leaf blades round (cx, cy) at radius r standing on z: n upright blades facing
    out (in the tangent plane), and n smaller ones between them leaning out (in the radial plane)."""
    out = []
    for i in range(n):
        ang = phase + 2 * math.pi * i / n
        rad = V((math.cos(ang), math.sin(ang), 0))
        tan = V((-rad.y, rad.x, 0))
        c = V((cx, cy, 0)) + rad * r
        out.append(kit.leaf_blade(c, tan, rad, 0.0, z - 0.3, height, width, thick=0.22))
        if small:
            ang2 = ang + math.pi / n
            rad2 = V((math.cos(ang2), math.sin(ang2), 0))
            tan2 = V((-rad2.y, rad2.x, 0))
            out.append(kit.leaf_blade(V((cx, cy, 0)), rad2, -tan2, r * 0.97, z - 0.3, height * 0.6, width * 0.7,
                                      lean=0.35, thick=0.2))
    return out


# the RTS camera's azimuth (the views' -38 degrees): lights on round things face it
CAMERA = (0.788, -0.616)


def hanging_base(z_top, h, rod):
    """The z a hanging_lantern's crystal_lantern stands on."""
    return z_top - rod - 0.93 * h


def hanging_lantern(kit, x, y, z_top, h=5.0, r=1.2, rod=1.5):
    """A crystal lantern whose cap hangs `rod` under z_top (a branch, a bracket) on a gilt rod."""
    from ..shapes import turned
    base = hanging_base(z_top, h, rod)
    out = [turned(x, y, [(0.1, z_top - rod - 0.1), (0.1, z_top + 0.3)], ["gilt"], 6, cap0=("gilt", True),
                  cap1=("gilt", True))]
    return out + kit.crystal_lantern(x, y, base, h=h, r=r, finial=False)


def lantern_glow(x, y, z, h, name, size=24.0):
    """The warm spill EA hung round each of its night lanterns (a flat 24-unit glow card), round the
    crystal of kit.crystal_lantern(x, y, z, h): a free-hanging glow (sagekit/nightlights.py
    Light.glow) at the crystal's fattest part, so our lanterns light the air round them as EA's did."""
    from sagekit.nightlights import Light
    return Light.glow((x, y, z + 0.52 * h), size, name=name + " glow")


def crystal_light(x, y, z, h, r, name, halo=False):
    """The night light of kit.crystal_lantern(x, y, z, h, r): a pane over the crystal's camera side
    (the crystal is widest, 0.85 r, at z + 0.5 h). No halo by default: a crystal this small has no
    surface round it for one to lie on (it would hang in the air, off the night checks' tolerance)."""
    from sagekit.nightlights import Light
    nx, ny = CAMERA
    w, hz, zc = min(0.4 * r, 0.4), min(0.12 * h, 0.8), z + 0.52 * h     # the crystal's fattest part: a pane
    return Light.rect((x, y, 0.0), (-ny, nx, 0.0), (nx, ny, 0.0), -w, w, zc - hz, zc + hz,     # there stays
                      kind="window", halo=halo, reach=r + 0.4, name=name)                    # on its facets
