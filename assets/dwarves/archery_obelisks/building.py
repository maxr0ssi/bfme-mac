"""Dwarven archery range, level-2 obelisks (V1): EA's two square timber obelisks at the yard's
south corners, shown with the yard walls at Upgrade_StructureLevel2.

Each becomes a Dwarven stele: a battered stone plinth with a bronze course, a stone sleeve over
EA's shaft with a gold rune belt and a bronze band, and the fortress's stepped corner pyramid with
a gilded point over EA's timber point. EA's south faces lie exactly on the model's footprint edge
(y -54.14), so nothing can wrap them inside it: footprint_margin lets the stone pass it by 1.5 (the
game's collision comes from the INI's geometry, not the mesh).

V1 mesh coordinates, measured on EA's model: obelisk shafts x -34.1..-27.6 and 18.5..25.0,
y -54.1..-47.3, from z -0.2 to 59.0, points to z 65.0. Chained on the yard walls (base)."""
from sagekit.building import Building

from ..archery_range.building import NOT_BAKED
from ..style import DwarvenStyle

CENTRES = ((-30.85, -50.7), (21.75, -50.7))
SHAFT = 3.3                                 # EA's shaft half width
SLEEVE, PLINTH = 3.9, 4.7                   # our half widths
SHAFT_TOP = 58.6                            # the sleeve ends under the stepped pyramid


class ArcheryObelisks(Building):
    style = DwarvenStyle()
    base = "dwarves/archery_walls"
    source = "DBArchRnge_SKN"
    target = "V1"
    sheet = "dbarchrnge.tga"
    own_textures = {"dbarchrnge.tga": "DBArchRngO.tga"}
    house_tags = ()                         # V1 shows per upgrade level; the house model is always drawn
    footprint_margin = 1.5
    bake_hidden = NOT_BAKED
    views = {
        "rts": ((-4, -50, 25), 260, 50, -128, 50),
        "close": ((-30.85, -50.7, 32), 95, 18, -120, 45),
        "ingame": ((10, 0, 35), 850, 53, -62, 50),
    }

    def design(self, kit):
        s = []
        for cx, cy in CENTRES:
            s += self._stele(kit, cx, cy)
        return s

    @staticmethod
    def _stele(kit, cx, cy):
        from sagekit.blender.geometry import box_rings, loft

        def ring(h, z, ch=0.3):
            return box_rings((cx - h, cx + h), (cy - h, cy + h), z, ch)
        out = [
            # plinth: battered, a bronze course on top
            loft([ring(PLINTH, -0.1), ring(PLINTH, 1.0), ring(PLINTH - 0.6, 4.4)], ["stoneB", "stoneB"],
                 cap0=("stoneB", False), cap1=("top", True)),
            loft([ring(PLINTH - 0.4, 4.4), ring(PLINTH - 0.4, 5.4)], ["trim"], cap0=("top", False), cap1=("top", True)),
            # sleeve over EA's shaft, rune belt and bronze band proud of it
            loft([ring(SLEEVE, 5.4), ring(SLEEVE, SHAFT_TOP)], ["stoneA"], cap0=("stoneA", False), cap1=("top", False)),
            loft([ring(SLEEVE + 0.35, 28.0), ring(SLEEVE + 0.35, 28.6), ring(SLEEVE + 0.35, 32.4), ring(SLEEVE + 0.35, 33.0)],
                 ["trim", "rune", "trim"], cap0=("top", True), cap1=("top", True)),
            loft([ring(SLEEVE + 0.3, 50.0), ring(SLEEVE + 0.3, 51.4)], ["trim"], cap0=("top", True), cap1=("top", True)),
        ]
        # the fortress's stepped corner pyramid (tiers 110.8..123 at the fortress) on the sleeve
        out += kit.step_pyramid(cx, cy, dz=SHAFT_TOP - 110.8)
        return out
