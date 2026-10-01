"""Angmar wall trebuchet (AngmarWallCatapultSmall): stub from `sagekit new angmar`.

EA's KBTrlSlingWall (objects AngmarWallCatapultSmall; role wall_trebuchet): body KBTROLLWALLSLIN,
503 triangles, painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our
texture is DXT5).
In KBTROLLWALLSLIN mesh coordinates: x -39.60..38.11, y -27.89..28.98, z -0.02..61.85.
Other meshes (EA's, untouched): ICEWALL 48 (EXFortressIce.tga, EXIceRefraction01.tga).
Lifecycle models in its Draw module: KBTrSlgWl_A, KBTrSlgWl_D1, KBTrSlgWl_D2, KBTrSlgWl_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/wall_trebuchet` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/wall_trebuchet (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class WallTrebuchet(Building):
    style = AngmarStyle()
    source = "KBTrlSlingWall"
    target = "KBTROLLWALLSLIN"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressJ.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallTrebuchet"
    views = {
        "rts": ((-0.7, 0.5, 30.9), 252, 50, -38, 50),
        "close": ((-0.7, 0.5, 30.9), 149, 24, -30, 45),
        "ingame": ((-0.7, 0.5, 30.9), 572, 53, -62, 50),
    }

    def design(self, kit):
        return []
