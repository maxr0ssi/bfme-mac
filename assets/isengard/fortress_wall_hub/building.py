"""Isengard fortress wall hub (IsengardCastleWallHubExpansion; model IBFWHub): the hexagonal wall
tower the citadel raises where its walls join a wall run. EA's IBFBALTOW01 here is the wall hub's
mesh with a wall stub toward the citadel (x -42.2..-18.94, the walls' profile 25.47 lower, entering
the hub's -X corner). The hexagon takes the wall hub's blade cluster whole (shapes_walls.hub: a
needle stack between two lozenge blades on the roof to model 84, the walls' needles on the
parapet's corners, spikes, silver arrises, ember slits), so a citadel corner and the
free-standing hubs read as one wall. The stub takes the walls' profile (shapes_walls.stub: short
fins, a buttress blade, slits, the silver lip and ridge, spikes, needles out of its three
pyramids), turned onto its run.

No fire and no banners (the gate and the towers carry them). The mesh hangs on a bone at z 25.47
(model z = mesh z + 25.47); the design is in mesh coordinates.
"""
from sagekit.building import Building

from ..style import IsengardStyle


class FortressWallHub(Building):
    style = IsengardStyle()
    source = "IBFWHub"
    target = "IBFBALTOW01"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresB.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressWallHub"
    house_tags = ()                 # no banners: the hub's crown is the free hubs'
    max_z_growth = 0.35             # the hub's blade cluster to model 84 (+35 %), as the citadel's
    views = {
        "rts": ((-9.0, -0.0, 40.0), 245, 50, -38, 50),
        "close": ((-9.0, -0.0, 56.0), 160, 24, -30, 45),
        "stub": ((-30.0, 0.0, 45.0), 90, 30, -80, 45),
        "ingame": ((-9.0, -0.0, 31.2), 510, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_walls import FWHUB_STUB, hub, stub
        return hub(kit) + stub(kit, **FWHUB_STUB)

    def emphasis(self, c, n):
        if c.z > 12:
            return 1.35                       # the crown and the stub's crest
        return 1.0
