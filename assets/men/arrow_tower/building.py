"""Men arrow tower (MenArrowTowerExpansion, build variation one; model GBFARTOWA, shipped as our
own GBFARTOWA2: Blue Mountains' tower draws GBFARTOWA too): EA's tower kept whole - the shaft with
its crest and diagonal buttresses, the lancet belfry, the steep slate dome - and crowned the
citadel's way (spire.py, shared with men/arrow_tower_b): a machicolated gallery with a black band
of silver stars and square merlons round the shaft top on its three outward faces, corbelled
bartizans with slate spirelets on the two front corners (standing on the buttresses' heads),
pilasters up the belfry's chamfers, a steel eave band and ribs on the dome, a lantern cupola, a
gilt orb and a steel spike; a moulded plinth; one house-colour banner.

EA's facts: body GBFARTOWA (218 triangles) on GBFortress1 (own copy GBFortressB); lifecycle
GBFARTOWA_A, _D2, _D3 (variation one: GBFARTOWB is men/arrow_tower_b's); no house model of
EA's (HOUSE_DRAW); no night meshes. Mesh coordinates (the model's origin at x 24.5, the bone);
measurements in spire.py.
"""
from sagekit.building import Building

from ..style import MenStyle


class ArrowTower(Building):
    style = MenStyle()
    source = "GBFARTOWA"
    target = "GBFARTOWA"
    own_model = "GBFARTOWA2"            # dwarves draws GBFARTOWA too (sagekit/ownership.py)
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressB.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCArrowTower"
    footprint_margin = 0.3              # the dome's eave lies on EA's footprint at -X: the ribs pass it
    views = {
        "rts": ((0.9, -0.0, 46.8), 228, 50, -38, 50),
        "close": ((0.9, -0.0, 54.0), 175, 24, -30, 45),
        "ingame": ((0.9, -0.0, 46.8), 519, 53, -62, 50),
    }

    def design(self, kit):
        from ..garrison_tower import pad
        from . import spire
        return spire.build(kit, spire.A) + pad.banner(kit, 0.0, -1, -3.2, shaft=spire.A.shaft, z_top=42.0, width=5.6,
                                                      length=20.0)

    def decals(self):
        from ..paint import men_layers
        from .spire import A
        return [men_layers()[2](zrange=A.gallery[1:3], pitch=3.2, r=0.9)]      # silver stars on the gallery's band

    def emphasis(self, c, n):
        if c.z > 42:
            return 1.35                       # gallery, bartizans, belfry and crown
        return 1.0
