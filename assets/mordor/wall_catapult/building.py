"""Mordor wall catapult (MordorWallCatapultExpansion): stub from `sagekit new mordor`.

EA's MBFWCTow (objects MordorWallCatapultExpansion; role catapult_tower): body MBFWCTOW, 962
triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In MBFWCTOW mesh coordinates: x -65.18..9.20, y -22.69..22.69, z -0.00..70.00.
Other meshes (EA's, untouched): P1 8.
Lifecycle models in its Draw module: MBFWCTow_A, MBFWCTow_D2, MBFWCTow_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure mordor/wall_catapult` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/catapult_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class WallCatapult(Building):
    style = MordorStyle()
    source = "MBFWCTow"
    target = "MBFWCTOW"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresG.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallCatapult"
    views = {
        "rts": ((-28.0, -0.0, 35.0), 246, 50, -38, 50),
        "close": ((-28.0, -0.0, 35.0), 145, 24, -30, 45),
        "ingame": ((-28.0, -0.0, 35.0), 559, 53, -62, 50),
    }

    def design(self, kit):
        return []
