"""Mordor barricade (MordorBarricade): stub from `sagekit new mordor`.

EA's MBBarcade (objects MordorBarricade; role bunker): body MBBARCADE, 923 triangles, painted
from MBBarcade.tga + MBBarcade_NRM.tga (DXT1).
In MBBARCADE mesh coordinates: x -45.32..47.70, y -35.83..35.83, z -0.10..78.71.
Lifecycle models in its Draw module: MBBarcade_A, MBBarcade_D1, MBBarcade_D2, MBBarcade_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure mordor/barricade` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/bunker (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class Barricade(Building):
    style = MordorStyle()
    source = "MBBarcade"
    target = "MBBARCADE"
    sheet = "MBBarcade.tga"
    sheet_normal = "MBBarcade_NRM.tga"
    own_textures = {"MBBarcade.tga": "MBBarcadH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCBarricade"
    views = {
        "rts": ((1.2, -0.0, 39.3), 311, 50, -38, 50),
        "close": ((1.2, -0.0, 39.3), 184, 24, -30, 45),
        "ingame": ((1.2, -0.0, 39.3), 707, 53, -62, 50),
    }

    def design(self, kit):
        return []
