"""Angmar wall postern (AngmarWallPosternGateSmall): stub from `sagekit new angmar`.

EA's KBPostGateN (objects AngmarWallPosternGateSmall; role wall_postern): body POSTERN GATE, 422
triangles, painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our texture
is DXT5).
In POSTERN GATE mesh coordinates: x -15.77..15.88, y -15.82..15.24, z -0.08..43.63.
Lifecycle models in its Draw module: KBPostGat_D2, KBPostGat_D3, KBPostGateN_A, KBPostGateN_D1.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/wall_postern` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/wall_postern (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class WallPostern(Building):
    style = AngmarStyle()
    source = "KBPostGateN"
    target = "POSTERN GATE"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressF.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallPostern"
    views = {
        "rts": ((0.1, -0.3, 21.8), 137, 50, -38, 50),
        "close": ((0.1, -0.3, 21.8), 81, 24, -30, 45),
        "ingame": ((0.1, -0.3, 21.8), 311, 53, -62, 50),
    }

    def design(self, kit):
        return []
