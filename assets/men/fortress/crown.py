"""A Gondor tower crown (Blender side), the same on EA's four towers.

EA's tower (GBFORTRESS mesh coordinates, about its centre): a shaft of chamfered-square section
(half 13.05, chamfer 3.7) to z 75.9, a cornice in to the belfry (half 10.75, chamfer 3.05) at
79.5, the belfry to 92.45, an eave lip (half 11.1) and a chamfered-square slate dome: half 10.75
at 92.5, 7.8 at 98.7, 4.4 at 102.0, its point at 103.7 and EA's finial (the banner-upgrade flag
pole) to 110.8..116.6. What stands on it here:

    gallery    a machicolated gallery round the shaft top: two-step corbels (from z 73.8, above
               the flame upgrade's hardware, which ends at 73.5 on the middle of the outward
               faces) under a slab 2 out, a parapet and square merlons with capstones
    bartizans  four corner turrets on the chamfers, corbelled out, slit windows, slate spirelets
    pilasters  up the chamfers from EA's corner buttress (outer) or the wall walk (sides) into
               the bartizans' corbels
    dome       a steel eave band, twelve steel ribs, a lantern cupola whose gilt cap ends at 105.3
               (the banner upgrade's pennant, GBFFLAG, flies from the pole at z 105.1..111.6), a
               steel mast through the pennant's hoist, a gilt orb above it and a spike to 129
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import box_rings, prism_uz, sweep

HALF, CH = 13.05, 3.7                       # the shaft
Z_CORBEL, Z_SLAB, Z_WALK, Z_PARAPET = 73.8, 77.4, 79.9, 81.6
OUT = 2.0                                   # the gallery's front, out of the shaft faces
EAVE = (11.1, 3.1)
DOME = [(92.55, 10.75, 3.05), (98.7, 7.8, 2.4), (102.0, 4.4, 1.2)]
LANTERN_Z, LANTERN_R, LANTERN_TOP = 101.4, 4.5, 105.3
ORB_Z, TIP = 113.5, 129.0
BARTIZAN_R, BARTIZAN_Z = 16.3, 72.6         # turret centres out along the diagonals, corbel foot
SLAB = [(-2.5, 79.2), (0.0, Z_SLAB), (OUT, Z_SLAB), (OUT, Z_WALK), (-2.5, Z_WALK)]
SLAB_TAGS = ["stoneB", "stoneB", "enamel", "top", None]     # the front: a black band, silver stars (paint)
PARAPET = [(0.6, Z_WALK - 0.1), (OUT - 0.15, Z_WALK - 0.1), (OUT - 0.15, Z_PARAPET), (0.6, Z_PARAPET)]
PARAPET_TAGS = [None, "stoneA", "top", "stoneA"]
EAVE_BAND = [(-0.5, 92.0), (0.25, 92.0), (0.25, 93.0), (-0.5, 93.3)]
CORBELS = (-8.0, -4.8, -1.6, 1.6, 4.8, 8.0)  # along each long face, from its middle
CUT = 44.3                                  # the front towers' galleries stop here (gallery_path)


def octagon(cx, cy, half, ch):
    ring = box_rings((cx - half, cx + half), (cy - half, cy + half), 0.0, ch)
    return [(p.x, p.y) for p in ring] + [(ring[0].x, ring[0].y)]


def gallery_path(cx, cy, cut=None):
    """The shaft outline the gallery follows: closed, or (cut: x) open where it would meet the
    healing house - on the front towers' face toward y = 0 the healing house's corner block and its
    spirelet stand at x 45.3..48.8, 1.5 in front of the face, up to z 90."""
    path = octagon(cx, cy, HALF, CH)[:-1]
    if cut is None:
        return path + [path[0]]
    yf = cy - math.copysign(HALF, cy)
    j = next(k for k, (x, y) in enumerate(path) if abs(y - yf) < 1e-3 and x > cx)      # the face's outer end
    i = next(k for k, (x, y) in enumerate(path) if abs(y - yf) < 1e-3 and x < cx)      # its inner end
    step = 1 if (j - i) % 8 == 7 else -1                                                # walk away from j
    out = [(cut, yf)]
    k = i
    while k != j:
        out.append(path[k])
        k = (k + step) % 8
    return out + [path[j]]


def build(kit, cx, cy):
    out = []
    cut = CUT if cx > 0 else None
    path = gallery_path(cx, cy, cut)
    # an open ring's end passes the belfry's chamfer: its inner face is kept there (closed solid)
    slab, segs = sweep(path, SLAB, SLAB_TAGS[:-1] + ["stoneB" if cut else None], center=(cx, cy))
    out += slab
    out += sweep(path, PARAPET, PARAPET_TAGS, center=(cx, cy))[0]
    for a, b, t, n in segs:
        L = (b - a).length
        if L < 10:
            continue                        # a chamfer: its bartizan stands there
        a3 = V((a.x, a.y, 0))
        mid = (V((cx, cy)) - a).dot(t)      # the face's middle (a cut face is shorter)
        for u in CORBELS:
            if 0.6 < mid + u < L - 0.6:
                out += kit.corbel(a3, t, n, mid + u, Z_CORBEL)
        out += kit.merlons(a3, t, n, 0.15, L - 0.15, Z_PARAPET, 0.6, OUT - 0.15, w=2.4, gap=1.75, h=2.8)
    sx, sy = math.copysign(1, cx), math.copysign(1, cy)
    for dx, dy in ((sx, sy), (sx, -sy), (-sx, sy), (-sx, -sy)):
        ang = math.atan2(dy, dx)
        r = BARTIZAN_R / math.sqrt(2)
        inner = (dx, dy) == (-sx, -sy)       # the courtyard corner (the healing house backs onto it)
        z0 = BARTIZAN_Z + (1.0 if inner else 0.0)
        out += kit.bartizan(cx + dx * r, cy + dy * r, z0, facing=ang)
        if not inner:
            out += _pilaster(cx, cy, dx, dy, 46.4 if (dx, dy) == (sx, sy) else 50.0, z0 + 0.4)
    out += sweep(octagon(cx, cy, *EAVE), EAVE_BAND, ["trim", "trim", "trim", None], center=(cx, cy))[0]
    out += kit.ribs(cx, cy, DOME)
    out += kit.lantern(cx, cy, LANTERN_Z, r=LANTERN_R, top=LANTERN_TOP)
    out += kit.finial(cx, cy, LANTERN_TOP - 0.1, ORB_Z, TIP)
    return out


def _pilaster(cx, cy, dx, dy, z0, z1):
    """A flat pilaster up a chamfer face (dx, dy the diagonal), a moulded base at z0."""
    c = HALF - CH / 2                       # the chamfer face's middle, along each axis
    n = V((dx, dy, 0)).normalized()
    t = V((-n.y, n.x, 0))
    a = V((cx + dx * c, cy + dy * c, 0))
    return [prism_uz(a, t, n, [(-1.55, z0), (1.55, z0), (1.55, z0 + 1.4), (-1.55, z0 + 1.4)], -0.3, 1.25,
                     ["stoneB", "stoneB", "top", "stoneB"], "course", None),
            prism_uz(a, t, n, [(-1.2, z0 + 1.4), (1.2, z0 + 1.4), (1.2, z1), (-1.2, z1)], -0.3, 0.9,
                     [None, "stoneB", "top", "stoneB"], "stoneA", None)]
