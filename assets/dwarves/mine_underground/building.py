"""Dwarven underground mine (DwarvenMineShaftForUndermine, dwarvenmineshaft.ini): the bare boulder
round the magic door becomes an Erebor gate cut into the rock - a deep stepped pointed portal
standing out of the rock face round the door, a gold rune tympanum over it, two king pillars with
the dwarf-statue relief flanking the gate (Erebor's guardians), and a rune lintel with a bronze
cornice and a stepped gable crown on the rock's brow.

The model (DBUndrMine, its own hierarchy) is the rock shell OBJPOLYSURFACE1 (the target, painted
from DBStoneA) and the two magic-door leaves OBJOBJPOLYSURFA / OBJPOLYSURFACE8 (untouched: nothing
new covers them). The shell is hollow behind the door.

All numbers are OBJPOLYSURFACE1 mesh coordinates measured on the original (the gate faces +X):
  door leaves: x -3.9..-0.13, |y| <= 13.2, jambs to z 21.2, round head through (10.3, 28.0),
    (7.3, 31.1), (3.7, 32.6) to 33.2 on the axis
  rock face over the door: x ~ -3.5..-5.9 from z 30 to its brow at ~36-38.6; no rock in front of
    the door; the rock's cheeks beside it stand out to x 0..5 (|y| 15..18) and 2..8 (|y| 21..24)
Footprint x -61.83..17.64, y -32.88..34.21; height -0.23..40.47 (limit +20 %: top 48.61).

The W3D add-on cannot import this model as it ships (a door leaf's second material pass names
texture 2 of 4 while the leaf has 2 vertex materials: IndexError in material_import.py line 68);
`_clamp_importer` below works round it for every Blender step (see README).
"""
from sagekit.building import Building

from ..style import DwarvenStyle

DOOR = [(13.2, 21.2), (10.3, 28.0), (7.3, 31.1), (3.7, 32.6), (0.0, 33.2)]     # half outline, jamb top on
ARCH = [(13.25, 0.0), (13.25, 21.4), (9.7, 31.2), (0.0, 35.8)]                  # the portal's inner outline
PORTAL_BACK, PORTAL_OUT, LINTEL = -4.5, 24.0, 40.6
# the rock's cave-mouth lip stands out to x 8.2 beside the lower jambs (|y| 13.5..17, z < 8) and
# 6.1 above: every ring's front is in front of it, or the lip cuts through the frieze strips
PORTAL_FRONTS, PORTAL_DEPTHS = (8.6, 9.8, 11.0), (0.0, 1.6, 3.2)
FRONT = PORTAL_FRONTS[-1]
# banner poles outside the king pillars (capitals |y| <= 23.6), in front of the rock skirt there
# (x <= ~12); rods end at x 17.0 (footprint 17.64) and span |y| 24.4..30.6
BANNER_X, BANNER_Y = 15.4, 27.5
TYMPANUM = (-4.2, 0.4)                    # x range: from inside the rock lip to just proud of the door
PILLAR = (17.2, 23.2)                     # king pillars' |y| range, standing on the outer ring's front


def portal(kit, arch, axis, back, fronts, depths, outer_u, lintel_z):
    """A stepped pointed portal on a wall facing +X: rings following `arch` (half outline from the
    axis, jamb foot to point), each from the plane `back` (inside the rock) out to its own front -
    inner rings recessed, carrying the triangle frieze, with bronze reveals - the last ring filling
    out to +-outer_u and up to lintel_z (its top is left for the lintel to cover)."""
    from mathutils import Vector as V

    from sagekit.blender.geometry import loft
    out = []

    def piece(poly, x1, tags, front):
        for side in (1, -1):
            r0 = [V((back, axis + side * u, z)) for u, z in poly]
            r1 = [V((x1, axis + side * u, z)) for u, z in poly]
            out.append(loft([r0, r1], [tags], cap0=("stoneB", True), cap1=(front, True)))
    for i, x1 in enumerate(fronts):
        inner = kit.arch_offset(arch, depths[i])
        if i < len(fronts) - 1:
            outer = kit.arch_offset(arch, depths[i + 1])
            for k in range(3):
                piece([inner[k], outer[k], outer[k + 1], inner[k + 1]], x1, [None, None, None, "trim|a"], "tri|a")
        else:
            j0, j1, sh, ap = inner
            piece([j0, (outer_u, 0.0), (outer_u, j1[1]), j1], x1, [None, "stoneB", None, "trim|a"], "stoneB")
            piece([j1, (outer_u, j1[1]), (outer_u, lintel_z), (sh[0], lintel_z), sh], x1,
                  [None, "stoneB", None, None, "trim|a"], "stoneB")
            piece([sh, (sh[0], lintel_z), (0.0, lintel_z), ap], x1, [None, None, None, "trim|a"], "stoneB")
    return out


def along(poly, y):
    """z of a half outline [(|y|, z), ...] (|y| descending) at |y| = y."""
    for (y0, z0), (y1, z1) in zip(poly, poly[1:]):
        if y1 <= y <= y0:
            return z0 + (z1 - z0) * (y0 - y) / (y0 - y1)
    raise ValueError(y)


def _clamp_importer():
    """The W3D add-on (io_mesh_w3d 0.7.1) indexes a mesh's Blender materials (one per vertex
    material) with the TEXTURE id of each material pass's first stage; the door leaves have 2
    vertex materials and passes on textures 2 and 3, so the import dies. Clamp the ids to the
    vertex materials before the add-on builds its preview materials - only Blender's preview
    shading of the leaves changes; the pipeline ships the target mesh alone and EA's bytes for
    the rest."""
    import importlib
    import sys
    if "io_mesh_w3d" not in sys.modules:          # the add-on is not enabled: nothing to patch
        return
    mi = importlib.import_module("io_mesh_w3d.common.utils.mesh_import")    # imported lazily by the add-on
    orig = mi.create_vertex_material
    if getattr(orig, "sagekit_clamped", False):
        return

    def clamped(context, principleds, structure, mesh, b_mesh, name, triangles, mesh_ob):
        n = len(structure.vert_materials)
        if n and not (len(structure.material_passes) == 1 and len(structure.textures) > 1):
            for mp in structure.material_passes:
                for st in mp.tx_stages:
                    st.tx_ids = [[min(i, n - 1) for i in ids] for ids in st.tx_ids]
        return orig(context, principleds, structure, mesh, b_mesh, name, triangles, mesh_ob)
    clamped.sagekit_clamped = True
    mi.create_vertex_material = clamped


try:
    import bpy  # noqa: F401  (inside Blender: every job imports this model)
except ImportError:
    pass
else:
    _clamp_importer()
    from .layout_fix import patch as _split_rock_islands     # the rock's unwrap overlaps itself: README
    _split_rock_islands()


class MineUnderground(Building):
    style = DwarvenStyle()
    source = "DBUndrMine"
    target = "OBJPOLYSURFACE1"
    sheet = "DBStoneA.tga"                    # own texture DBStoneH.tga (+ _NRM, _D1, _Snow)

    def design(self, kit):
        s = []
        s += portal(kit, ARCH, 0.0, PORTAL_BACK, PORTAL_FRONTS, PORTAL_DEPTHS, PORTAL_OUT, LINTEL)  # 1. portal
        s += self._tympanum()                                                                     # 2. tympanum
        s += self._crown()                                                                        # 3. lintel, crown
        for sy in (1, -1):                                                                        # 4. king pillars
            y0, y1 = sorted((sy * PILLAR[0], sy * PILLAR[1]))
            s += kit.king_pillar(PORTAL_FRONTS[-1], y0, y1)
        s += self._banners(kit)                                                                   # 5. banners
        return s

    @staticmethod
    def _banners(kit):
        """Two Erebor-blue banner poles flanking the portal, like the mine's gate."""
        from mathutils import Vector as V
        return [solid for sy in (1, -1) for solid in
                kit.banner_pole(V((BANNER_X, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), sy * BANNER_Y, 37.0, 4.4, 18.0)]

    @staticmethod
    def _tympanum():
        """A gold rune panel filling the gap between the door's round head and the portal's pointed
        one, from inside the rock lip to just proud of the door: one strip per door-outline segment
        (and at the arch's shoulder), so every piece is convex."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz
        cuts = sorted({y for y, _ in DOOR} | {ARCH[2][0]}, reverse=True)
        out = []
        for sy in (1, -1):
            a, t, n = V((0.0, 0.0, 0)), V((0, sy, 0)), V((1, 0, 0))
            for yh, yl in zip(cuts, cuts[1:]):
                poly = [(yh, along(DOOR, yh)), (yl, along(DOOR, yl)), (yl, along(ARCH[1:], yl)), (yh, along(ARCH[1:], yh))]
                tags = ["stoneB", None, None, "stoneB" if yh == cuts[0] else None]
                out.append(prism_uz(a, t, n, poly, TYMPANUM[0], TYMPANUM[1], tags, "rune|a", "stoneB"))
        return out

    @staticmethod
    def _crown():
        """On the rock's brow: a rune lintel across the portal and pillars, a bronze cornice, and a
        stepped gable crown (triangle-frieze slab, bronze tier, stone gable)."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import box_rings, loft, prism_uz

        def R(x0, x1, hy, z):
            return box_rings((x0, x1), (-hy, hy), z, 0)
        out = [
            loft([R(-5.0, FRONT + 0.4, PORTAL_OUT, LINTEL), R(-5.0, FRONT + 0.4, PORTAL_OUT, 43.0)],
                 [["stoneB", "rune", "stoneB", "stoneB"]], cap0=("stoneB", True), cap1=("top", False)),
            loft([R(-5.4, FRONT + 1.0, PORTAL_OUT + 0.7, 43.0), R(-5.4, FRONT + 1.0, PORTAL_OUT + 0.7, 43.8)], ["trim"],
                 cap0=("trim", True), cap1=("top", True)),
        ]
        a, t, n = V((0.0, 0.0, 0)), V((0, 1, 0)), V((1, 0, 0))
        for poly, d0, d1, tags, front in (
                ([(-15.0, 43.8), (15.0, 43.8), (15.0, 45.2), (-15.0, 45.2)], -3.6, FRONT - 0.2, [None, "stoneB", "top", "stoneB"], "tri"),
                ([(-10.0, 45.2), (10.0, 45.2), (10.0, 46.3), (-10.0, 46.3)], -2.8, FRONT - 0.8, [None, "trim", "top", "trim"], "trim"),
                ([(-10.0, 46.3), (10.0, 46.3), (0.0, 48.5)], -2.8, FRONT - 0.8, [None, "top", "top"], "stoneA")):
            out.append(prism_uz(a, t, n, poly, d0, d1, tags, front, "stoneA"))
        return out

    def emphasis(self, c, n):
        if c.x > -5.5 and abs(c.y) < 25.0 and c.z > -0.1:
            return 1.5                        # the gate: portal, pillars, tympanum, crown
        return 1.0
