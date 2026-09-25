"""Dwarven bunker (DwarvenBunker): the squat guard tower keeps its body, its shield-panel head and
its corner fins; it gains a Dwarven crown (hex-frieze parapet slabs with stepped gables, stepped
pyramids on the corner fins, a stepped rune crown on the roof), a two-ring pointed arch around the
door, a rune belt around the octagonal shaft and a battered plinth on the long side.

All numbers are DBBBUNKER mesh coordinates measured on the original: centre line y = 1.05, door
facing +X, head core x +-13.34 / y -13.45..15.55 with its top at z 60.24, roof slope from the
ledge (x +-12.27 / y -12.2..14.3) up to the flat top (x +-8.5 / y -8.4..10.49) at z 65.73.
"""
from sagekit.building import Building

from ..style import DwarvenStyle

CY = 1.05                         # the building's centre line (x = 0, y = CY)
HEAD_TOP = 60.24
ROOF_TOP = 65.73
# head sides between the corner fins: (anchor, along, outward, length, back d, front d)
#   the slab runs fin-centre to fin-centre; its back meets the roof slope, its front overhangs the
#   shield panels by 0.95 (inside the original footprint: x +-14.37, y -14.54..16.63)
FIN = (11.3, 12.35)               # corner-pyramid centres: x +-11.3, y CY +- 12.35
# door: frame x 13.03..14.64, |y - CY| <= 9.17, canopy gable to z 28.34 at x 11.9..13.34
DOOR_ARCH = [(9.35, 0.0), (9.35, 24.3), (0.0, 30.0)]
# octagonal shaft (z 28.4..38.2): x +-11.01, y -10.94..13.04, 45-degree corners
OCTAGON = [(11.01, -5.47), (11.01, 7.57), (5.5, 13.04), (-5.5, 13.04), (-11.01, 7.57), (-11.01, -5.47),
           (-5.5, -10.94), (5.5, -10.94), (11.01, -5.47)]
BELT = [(0.0, 35.0), (0.6, 35.4), (0.6, 37.8), (0.0, 38.2), (-0.5, 38.2), (-0.5, 35.0)]
BELT_TAGS = ["trim", "rune", "trim", None, None, None]


class Bunker(Building):
    style = DwarvenStyle()
    source = "DBBunker"
    target = "DBBBUNKER"
    sheet = "DBBunker.tga"
    bake_hidden = ("DBBBUNKERG",)    # far-off ground patch (DBStoneA, not extracted): out of bakes and renders

    def design(self, kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import sweep
        solids = []
        fx, fy = FIN
        # 1. crown parapet: a hex-frieze slab on each head side with a stepped gable in its middle
        sides = [  # (anchor, along, outward, length, d0, d1)
            (V((13.34, CY - fy)), V((0, 1)), V((1, 0)), 2 * fy, -1.07, 0.95),
            (V((-13.34, CY + fy)), V((0, -1)), V((-1, 0)), 2 * fy, -1.07, 0.95),
            (V((fx, CY + 14.5)), V((-1, 0)), V((0, 1)), 2 * fx, -1.25, 0.95),
            (V((-fx, CY - 14.5)), V((1, 0)), V((0, -1)), 2 * fx, -1.25, 0.95),
        ]
        for a, t, n, L, d0, d1 in sides:
            solids += crest(V((a.x, a.y, 0)), t, n, L, 2.73, HEAD_TOP, d0, d1)
        # 2. stepped pyramids on the four corner fins
        for sx in (-1, 1):
            for sy in (-1, 1):
                solids += corner_pyramid(sx * fx, CY + sy * fy, HEAD_TOP, 0.7)
        # 3. a stepped rune crown on the flat roof, ending in a gilded point
        solids += roof_crown()
        # 4. the door: two pointed rings stepping forward around the original frame and canopy
        solids += pointed_frame(kit, DOOR_ARCH, CY, 13.2, [(0.0, 0.8, 14.9, "tri|a"), (0.8, 2.0, 15.8, "rune|a")])
        # 5. a rune belt round the octagonal shaft, under the flared corners
        solids += sweep(OCTAGON, BELT, BELT_TAGS, center=(0, CY))[0]
        # 6. a battered plinth along the long -Y side (the RTS camera's side), flush with the door wall
        solids += plinth()
        return solids

    def emphasis(self, c, n):
        if c.z > 58:
            return 1.5                        # the crown
        if c.x > 12.5 and c.z < 34:
            return 1.4                        # the door
        return 1.1 if c.z > 34 else 1.0


# ---------------------------------------------------------------------- helpers (candidates for shapes.py)
def crest(a, t, n, L, end, z0, d0, d1):
    """A parapet slab along a side (u 0..L from `a` along `t`, d0..d1 along `n`) carrying the hexagon
    frieze, with a stepped triangle gable over its visible middle; `end` = the length hidden in the
    corner blocks at each end."""
    from sagekit.blender.geometry import prism_uz
    out = []
    z1, z2, z3, z4 = z0 + 2.3, z0 + 4.2, z0 + 5.8, z0 + 10.2
    out.append(prism_uz(a, t, n, [(0, z0), (L, z0), (L, z1), (0, z1)], d0, d1,
                        [None, "stoneB", "top", "stoneB"], "hex", "stoneA"))
    u0, u1 = end + 2.2, L - end - 2.2
    out.append(prism_uz(a, t, n, [(u0, z1), (u1, z1), (u1, z2), (u0, z2)], d0 + 0.15, d1 - 0.35,
                        [None, "stoneB", "top", "stoneB"], "stoneA", "stoneA"))
    u0, u1 = u0 + 2.0, u1 - 2.0
    out.append(prism_uz(a, t, n, [(u0, z2), (u1, z2), (u1, z3), (u0, z3)], d0 + 0.3, d1 - 0.6,
                        [None, "trim", "top", "trim"], "trim", "stoneA"))
    out.append(prism_uz(a, t, n, [(u0, z3), (u1, z3), ((u0 + u1) / 2, z4)], d0 + 0.3, d1 - 0.6,
                        [None, "top", "top"], "stoneA", "stoneA"))
    return out


def corner_pyramid(cx, cy, z0, s):
    """The fortress's stepped corner pyramid (shapes.step_pyramid) at scale s, standing on z0."""
    from mathutils import Vector as V

    from sagekit.blender.geometry import box_rings, loft
    out = []
    z = z0
    for h0, h1, dz, tg in ((3.9, 3.5, 6.0, "stoneB"), (2.9, 2.7, 2.4, "stoneA"), (1.9, 1.8, 1.7, "stoneA")):
        r0 = box_rings((cx - h0 * s, cx + h0 * s), (cy - h0 * s, cy + h0 * s), z, 0.3)
        r1 = box_rings((cx - h1 * s, cx + h1 * s), (cy - h1 * s, cy + h1 * s), z + dz * s, 0.3)
        out.append(loft([r0, r1], [tg], cap0=("top", False), cap1=("top", True)))
        z += dz * s
    r0 = box_rings((cx - 1.8 * s, cx + 1.8 * s), (cy - 1.8 * s, cy + 1.8 * s), z, 0.25)
    out.append(loft([r0, [V((cx, cy, z + 2.1 * s))] * len(r0)], ["trim"], cap0=("top", False), cap1=("top", False)))
    return out


def roof_crown():
    """Three battered tiers on the flat roof (rune belt, bronze cornice, triangle frieze) and a
    gilded pyramid point: the roof becomes one stepped pyramid."""
    from mathutils import Vector as V

    from sagekit.blender.geometry import box_rings, loft

    def ring(hx, hy, z, ch):
        return box_rings((-hx, hx), (CY - hy, CY + hy), z, ch)
    z0 = ROOF_TOP
    out = [loft([ring(7.0, 7.6, z0, 0.9), ring(6.7, 7.3, z0 + 2.7, 0.9)], ["rune"], cap0=("top", False), cap1=("top", True)),
           loft([ring(7.1, 7.7, z0 + 2.7, 0.9), ring(7.1, 7.7, z0 + 3.3, 0.9), ring(6.6, 7.2, z0 + 3.6, 0.8)],
                ["trim", "trim"], cap0=("trim", True), cap1=("top", True)),
           loft([ring(5.2, 5.7, z0 + 3.6, 0.7), ring(4.9, 5.4, z0 + 5.8, 0.7)], ["tri"], cap0=("top", False), cap1=("top", True)),
           loft([ring(3.6, 3.9, z0 + 5.8, 0.5), ring(3.4, 3.7, z0 + 7.4, 0.5)], ["stoneA"], cap0=("top", False), cap1=("top", True))]
    r = ring(2.6, 2.8, z0 + 7.4, 0.4)
    out.append(loft([r, [V((0, CY, z0 + 10.6))] * len(r)], ["trim"], cap0=("top", False), cap1=("top", False)))
    return out


def pointed_frame(kit, arch, axis_y, x0, rings, zfoot=0.15):
    """Pointed rings around a door facing +X: arch = half outline from the axis (jamb foot, ...,
    point on the axis); each ring (offset in, offset out, front x, front tag) runs from x0 (the wall)
    to its front, outer rings standing further forward; inner reveals bronze, the outermost ring's
    outside plain stone. Unlike shapes.pointed_arch, no rectangular fill: the frame stays pointed."""
    from mathutils import Vector as V

    from sagekit.blender.geometry import loft
    out = []
    for i, (o0, o1, x1, front) in enumerate(rings):
        inner, outer = kit.arch_offset(arch, o0), kit.arch_offset(arch, o1)
        inner[0], outer[0] = (inner[0][0], zfoot), (outer[0][0], zfoot)
        last = i == len(rings) - 1
        for k in range(len(arch) - 1):
            quad = [inner[k], outer[k], outer[k + 1], inner[k + 1]]
            tags = [None, "stoneB" if last else None, None, "trim|a"]
            for side in (1, -1):
                r0 = [V((x0, axis_y + side * y, z)) for y, z in quad]
                r1 = [V((x1, axis_y + side * y, z)) for y, z in quad]
                out.append(loft([r0, r1], [tags], cap0=("stoneB", True), cap1=(front, True)))
    return out


def plinth():
    """A battered plinth along the -Y side from wall corner to wall corner (x +-13.34), its back in
    the body (y -9.42), foot 4 out, with a bronze string course."""
    from mathutils import Vector as V

    from sagekit.blender.geometry import prism_uz
    a, t, n = V((0, -9.42, 0)), V((0, -1, 0)), V((1, 0, 0))
    prof = [(0, 0.15), (3.9, 0.15), (3.9, 1.3), (2.1, 6.2), (0, 6.2)]
    course = [(0, 6.2), (2.3, 6.2), (2.3, 7.0), (1.9, 7.4), (0, 7.4)]
    return [prism_uz(a, t, n, prof, -13.34, 13.34, [None, "stoneB", "stoneA", "top", None], "stoneB", "stoneB"),
            prism_uz(a, t, n, course, -13.34, 13.34, [None, "trim", "trim", "top", None], "trim", "trim")]
