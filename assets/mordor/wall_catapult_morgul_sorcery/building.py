"""Mordor wall catapult morgul sorcery (MordorWallCatapultExpansion): stub from `sagekit new
mordor`.

EA's MBCatSorc (objects MordorWallCatapultExpansion; role catapult_tower): body MBFLAVAMEFF, 124
triangles, painted from MinasMorgulFX2.tga, no normal map (DXT1).
In MBFLAVAMEFF mesh coordinates: x -56.47..34.49, y -28.58..28.15, z -2.39..131.65.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure mordor/wall_catapult_morgul_sorcery` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/catapult_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class WallCatapultMorgulSorcery(Building):
    style = MordorStyle()
    source = "MBCatSorc"
    target = "MBFLAVAMEFF"
    sheet = "MinasMorgulFX2.tga"
    sheet_normal = None
    own_textures = {"MinasMorgulFX2.tga": "MinasMorgulFXC.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawMorgulSorcery",)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallCatapultMorgulSorcery"
    views = {
        "rts": ((-30.2, -0.2, 64.6), 378, 50, -38, 50),
        "close": ((-30.2, -0.2, 64.6), 223, 24, -30, 45),
        "ingame": ((-30.2, -0.2, 64.6), 858, 53, -62, 50),
    }

    def design(self, kit):
        return []
