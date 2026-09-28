"""Men fortress wall hub (MenWallHubSmallExpansion, model GBGFWHub): the hexagonal wall tower the
citadel raises where its wall expansion joins the walls. EA's OBJECT03 is the free-standing hub's
mesh vertex for vertex (men/wall_hub, GBWallRmprtN), so the recipe is the wall hub's design whole,
imported from men/wall_hub (EA's body kept; a flush parapet with a black band of silver stars and
square merlons round the rim, six corbelled bartizans with slate spirelets, pilasters and
round-arched window frames on the drum, a steel eave band and ribs on the dome, a lantern cupola, a
gilt orb and a spike; no banners): the citadel's corner and the free-standing hubs read as one wall.

BOX01 (EA's, untouched) is the wall stub toward the citadel: model x -39.0..-1.0, |y| <= 7.45, to
z 49.5, entering the hub at its -X corner (the hub hangs on a bone at z 80.79, turned 60 degrees:
its corners lie on the model's x axis). That corner's bartizan rises from the stub's top.

EA paints OBJECT03 here from the faction sheet GBFortress1 but with the wall's normal map
GBWall_NRM (the free hub uses GBFortress1_NRM): `sheet_atlas` is the faction atlas with that
normal map, so the body keeps EA's relief and new faces take the faction sheet's (the framework's
plain-sheet atlas covers a different sheet only). Our copy of that normal map is GBWalK_NRM.tga:
W3D patches names in place, so it keeps GBWall_NRM.tga's length (GBFortressK_NRM would not).
"""
from ..wall_hub.building import WallHub


class FortressWallHub(WallHub):
    source = "GBGFWHub"
    target = "OBJECT03"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBWall_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressK.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressWallHub"
    views = {
        "rts": ((-8.0, 0.0, 49.1), 260, 50, -38, 50),              # model space (z up from the ground)
        "close": ((-4.0, 0.0, 62.0), 150, 24, -30, 45),
        "ingame": ((-8.0, 0.0, 49.1), 600, 53, -62, 50),
    }

    OWN_NORMAL = "GBWalK_NRM.tga"

    def texture_names(self):
        out = super().texture_names()
        out[self.sheet_normal] = self.OWN_NORMAL
        return out

    @property
    def sheet_atlas(self):
        a = getattr(self, "_atlas", None)
        if a is None:
            import copy
            a = self._atlas = copy.copy(self.style.atlas)
            a.normal = self.sheet_normal
        return a
