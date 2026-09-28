"""Men garrison tower (MenGarrisonTowerExpansion, build variation one; model GBFDOTOWA): EA's
gate tower kept whole - the shaft with its gate and crest, the diagonal buttresses, the belfry
and its windows, the slate dome - and crowned the citadel's way (pad.py, shared with
men/garrison_tower_b, and the shared tower top men/wall_hub/dome.py): a machicolated gallery with a
black band of silver stars and square merlons round the shaft top, a voussoir archivolt with
quoins, imposts and portcullis teeth on the gate, pinnacles on the buttresses and the belfry's
chamfers, hoods and sills on the belfry windows, a steel-ribbed dome under a lantern cupola, a
gilt orb and a steel spike. One house-colour banner.

EA's facts: body GBFDOTOWA (430 triangles) on GBFortress1 (own copy GBFortressN); lifecycle
GBFDOTOWA_A, _D2, _D3 (variation one: GBFDOTOWB is men/garrison_tower_b's); no house model of
EA's (HOUSE_DRAW, a model of our own); no night meshes. Mesh coordinates, the model's origin at
x 24.5 (the bone). Measurements in pad.py.
"""
from sagekit.building import Building

from ..style import MenStyle


class GarrisonTower(Building):
    style = MenStyle()
    source = "GBFDOTOWA"
    target = "GBFDOTOWA"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressN.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCGarrisonTower"
    footprint_margin = 0.55             # the belfry's -X face lies on EA's footprint: the eave band and ribs
    views = {
        "rts": ((2.2, 0.0, 41.5), 212, 50, -38, 50),
        "close": ((2.2, 0.0, 50.0), 175, 24, -30, 45),
        "ingame": ((2.2, 0.0, 41.5), 482, 53, -62, 50),
    }

    def design(self, kit):
        from . import pad
        return pad.build(kit) + pad.banner(kit, u=-3.8, width=6.4, length=22.0)

    def decals(self):
        from ..paint import men_layers
        from .pad import Z_SLAB, Z_WALK
        return [men_layers()[2](zrange=(Z_SLAB, Z_WALK), pitch=3.2, r=0.9)]      # silver stars on the gallery's band

    def emphasis(self, c, n):
        if c.z > 43:
            return 1.35                       # gallery, belfry and crown
        if c.x > 37 and abs(c.y) < 13:
            return 1.25                       # the gate
        return 1.0
