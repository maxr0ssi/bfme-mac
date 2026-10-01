"""Angmar battle tower (AngmarBattleTowerExpansion): stub from `sagekit new angmar`.

EA's KBArrowTower (objects AngmarBattleTowerExpansion; role tower_expansion): body ARROWTOWER,
1168 triangles, painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our
texture is DXT5).
In ARROWTOWER mesh coordinates: x -41.86..17.37, y -19.08..18.70, z 0.54..126.59.
Other meshes (EA's, untouched): ICEWALL 18 (EXFortressIce.tga, EXIceRefraction01.tga).
Lifecycle models in its Draw module: KBArwTow_A, KBArwTow_D1, KBArwTow_D2, KBArwTow_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/battle_tower` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/erebor_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class BattleTower(Building):
    style = AngmarStyle()
    source = "KBArrowTower"
    target = "ARROWTOWER"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCBattleTower"
    views = {
        "rts": ((-12.2, -0.2, 63.6), 317, 50, -38, 50),
        "close": ((-12.2, -0.2, 63.6), 188, 24, -30, 45),
        "ingame": ((-12.2, -0.2, 63.6), 722, 53, -62, 50),
    }

    def design(self, kit):
        return []
