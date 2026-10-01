"""Angmar wall gate (AngmarWallGateSmall): stub from `sagekit new angmar`.

EA's KBAngwGN_OP (objects AngmarWallGateSmall; role wall_gate): body TOWERS, 1036 triangles,
painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our texture is DXT5).
In TOWERS mesh coordinates: x -13.79..13.79, y -68.41..68.41, z -0.03..129.17.
Other meshes (EA's, untouched): BONE_DOOR 01 236 (KBFortressB.tga, KBFortressB_NRM.tga).
Lifecycle models in its Draw module: KBAngwGN_A, KBAngwGN_D1, KBAngwGN_D2, KBAngwGN_D3CLS,
KBAngwGN_D3OPN.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/wall_gate` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/wall_gate (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class WallGate(Building):
    style = AngmarStyle()
    source = "KBAngwGN_OP"
    target = "TOWERS"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressE.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallGate"
    views = {
        "rts": ((0.0, 0.0, 64.6), 418, 50, -38, 50),
        "close": ((0.0, 0.0, 64.6), 247, 24, -30, 45),
        "ingame": ((0.0, 0.0, 64.6), 951, 53, -62, 50),
    }

    def design(self, kit):
        return []
