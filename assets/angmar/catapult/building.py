"""Angmar catapult (AngmarCatapultExpansion): stub from `sagekit new angmar`.

EA's KBTrollSlingTo (objects AngmarCatapultExpansion; role catapult_tower): body KBTROLLSLINGTOW,
397 triangles, painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our
texture is DXT5).
In KBTROLLSLINGTOW mesh coordinates: x -41.84..43.08, y -39.25..39.18, z -0.02..61.85.
Other meshes (EA's, untouched): ICEWALL 24 (EXFortressIce.tga, EXIceRefraction01.tga).
Lifecycle models in its Draw module: KBTrlSgTw_A, KBTrlSgTw_D1, KBTrlSgTw_D2, KBTrlSgTw_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/catapult` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/catapult_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class Catapult(Building):
    style = AngmarStyle()
    source = "KBTrollSlingTo"
    target = "KBTROLLSLINGTOW"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressL.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCCatapult"
    views = {
        "rts": ((0.6, -0.0, 30.9), 288, 50, -38, 50),
        "close": ((0.6, -0.0, 30.9), 170, 24, -30, 45),
        "ingame": ((0.6, -0.0, 30.9), 656, 53, -62, 50),
    }

    def design(self, kit):
        return []
