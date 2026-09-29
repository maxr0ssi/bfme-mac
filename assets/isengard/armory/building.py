"""The Isengard armory (IsengardArmory), pass 2 "the Uruk armoury": EA's yard kept whole - the
raised deck behind its spiked fence, the shed, the grindstone, the treadwheel - and made the
forge where the Uruk-hai are harnessed. The shed becomes an iron hall (the new silhouette): a
steep pointed roof (42 degrees at the apex) to a ridge at z 45.5 with a crest of blades, stone
gables, the White Hand great in a pointed-arch slot in the +X gable over the opening, layered
fins at its corners, a lozenge needle stack up through its -Y slope; a forge (hearth, anvil,
bellows, square crucible, quench trough, tools) in the open yard; three Uruk harnesses on stands;
racks of shields, pikes and cleavers on the deck; a banner on an iron frame; braziers. Real fire
in the forge, the stack and the braziers (EA's sparks at the grindstone stay).

EA's facts (IBARMORY on an identity bone; work/measure.json is the treadwheel's, stale):
x -27.5..40.0, y -39.1..50.1, z -1.6..45.3 (468 triangles). The deck x -25..0, y -20..40 at
z 25, its fence along x -25 to z 45, a cluster of spikes at (-3, 20..40) to z 44; the shed
x 0..20, y 25..45, its roof at z 25; the slab floor at z 0. Kept clear: the treadwheel
(IBARMORYWHEEL1, y -42..-18) and the grindstone (IBARMORYWHEEL2, x 15..31, y -21..0; the
sparks at (28, -4, 16), the slave who works it about (0, 0)); the level-up tower (V1A, V2:
x -26..9, y -51..-9, to z 104); EA's night torch posts (N_WINDOW) at (-1, -61) and (26, 53).
"""
from sagekit.building import Building

from ..style import IsengardStyle

FIRE_POINTS = [
    (6.0, 29.0, 45.8, 'chimney'), (25.5, 15.0, 4.7, 'hearth'), (29.5, 22.9, 4.0, 'crucible'),
    (37.5, 45.0, 4.7, 'brazier'), (37.5, 26.0, 4.7, 'brazier'), (-8.0, -6.0, 29.7, 'brazier')
]

HALL = (-2.0, 23.5, 21.5, 48.5, 17.0, 45.5)      # x0, x1, y0, y1, eaves z, ridge z: the iron hall over the shed
SHED_TOP = 25.0
FORGE = ((25.5, 15.0, 0.0), (0.0, -1.0))         # hearth foot, t: the forge faces +X
STACK = ((6.0, 29.0), 0.0, 3.6, 2.4, 24.0, 47.5)         # up through the hall's -Y slope
STANDS = [((35.5, -12.0, 0.0), (-0.62, -0.79)), ((35.5, -2.0, 0.0), (-0.62, -0.79)), ((35.5, 8.0, 0.0), (-0.62, -0.79))]
BANNER = ((31.0, 37.0, 0.0), (-0.62, -0.79))
BRAZIERS = [(37.5, 45.0), (37.5, 26.0), (-8.0, -6.0, 25.0)]


class Armory(Building):
    style = IsengardStyle()
    source = "IBArmory_SKN"
    target = "IBARMORY"
    sheet = "IBArmory.tga"
    sheet_normal = "IBArmory_NRM.tga"
    own_textures = {"IBArmory.tga": "IBArmorH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    fire_points = FIRE_POINTS
    views = {
        "rts": ((8.0, 4.0, 24.0), 330, 50, -38, 50),
        "close": ((12.0, 8.0, 20.0), 190, 26, -32, 45),
        "ingame": ((6.2, 5.5, 21.9), 606, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_industry import logged
        return logged(kit, self._pieces)

    def _pieces(self, kit):
        from mathutils import Vector as V

        from .. import shapes_industry as I
        out = self._roof(kit, V, I)
        c, axis, L, W, z0, z1 = STACK
        out += kit.needle_stack(c, axis, L, W, z0, z1, collar=0.45)
        (fx, fy, fz), t = FORGE
        out += I.forge_bay(kit, V((fx, fy, fz)), t, 1.8)
        for c, t in STANDS:
            out += I.armour_stand(kit, V(c), t, 2.0)
        out += self._deck(kit, V, I)
        c, t = BANNER
        out += I.banner_frame(kit, V(c), t, 8.0, 17.0)
        for b in BRAZIERS:
            out += kit.brazier(V((b[0], b[1], b[2] if len(b) > 2 else 0.0)), 1.6, 4.6)
        return out

    @staticmethod
    def _roof(kit, V, I):
        """The iron hall over the shed: a steep pointed roof (42 degrees at the apex) from eaves at
        z 17 beyond the shed's walls to a ridge at z 45.5, silver eaves and ridge, a crest of
        blades; its gables stone with silver edges, the +X one over the shed's opening carrying
        a great White Hand in a pointed-arch slot; layered stone fins buttress its +X corners."""
        from sagekit.blender.geometry import loft, prism_uz
        x0, x1, y0, y1, ez, rz = HALL
        ym = (y0 + y1) / 2
        th = 1.2
        slope = lambda y, z: [V((x0, y, z)), V((x1, y, z)), V((x1, ym, rz)), V((x0, ym, rz))]   # noqa: E731
        out = []
        for ye in (y0, y1):
            top = [V((x0, ye, ez)), V((x1, ye, ez)), V((x1, ym, rz)), V((x0, ym, rz))]
            bot = [p - V((0, 0, th)) for p in top]
            out.append(loft([top, bot] if ye == y0 else [bot, top], [["trim", "iron", "iron", "iron"]], cap0=("iron", True),
                            cap1=("iron", True)))
        t, n = V((0, 1, 0)), V((1, 0, 0))
        h = rz - ez
        for x, front in ((x1 - 0.3, True), (x0 + 1.6, False)):
            a = V((x, 0, 0))
            hw = (y1 - ym) * (1 - (SHED_TOP - 0.5 - ez) / h)
            out.append(prism_uz(a, t, n, [(ym - hw, SHED_TOP - 0.5), (ym + hw, SHED_TOP - 0.5), (ym, rz - 0.8)],
                                -1.4, 0.0, ["stoneA", "trim", "trim"], "stoneB", "stoneA"))
            out.append(kit.beam(V((x + 0.6, ym, rz - 2.0)), V((x + 0.6, ym, rz + 7.5)), 0.6, "trim", 0.0))
            if front:                                   # the Hand in a pointed-arch slot
                w, zb, hh = 6.0, SHED_TOP + 0.6, 13.5
                head = 3.0
                poly = [(-w / 2, zb), (w / 2, zb), (w / 2, zb + hh - head), (0, zb + hh), (-w / 2, zb + hh - head)]
                m = V((x, ym, 0))
                out.append(prism_uz(m, t, n, [(u + 0.0, z) for u, z in poly], -0.5, 0.35, ["trim"] * 5, "stoneB", None))
                out += kit.hand(m, t, n, 0.0, zb + 1.4, 5.8, 0.35, th=0.4)
        out += I.roof_crest(kit, V((x0, ym, rz)), V((x1, ym, rz)), 5, 7.0, w=0.5, d=2.0)
        for y, e in ((y0, -1), (y1, 1)):                # layered fins at the +X corners
            out += I.fin(kit, V((x1 - 1.0, y - e * 1.0, 0)), (1.0, 0.0), 0.8,
                         [(-1.0, -0.4), (5.5, -0.4), (1.5, ez + 4.0), (-1.0, ez + 1.0)], 1.4, slits=((2.4, 6.0, 12.0),))
        return out

    @staticmethod
    def _deck(kit, V, I):
        """On the deck (z 25): a rack of Uruk shields and a rack of cleavers facing the yard, pikes
        along the fence."""
        z = 25.0
        out = kit.shield_rack(V((-10.0, 30.0, z)), V((0, -1, 0)), V((1, 0, 0)), 10.0, 3, 6.0)
        out += I.blade_rack(kit, V((-10.0, 12.0, z)), V((0, 1, 0)), 9.0, 4, 6.0)
        out += kit.pike_rack(V((-21.5, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), 2.0, z, 8.0, 9.0, d=1.2, pikes=5)
        return out
