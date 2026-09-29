"""Isengard wall end (IsengardWallCliffCap): stub from `sagekit new isengard`.

EA's IBWallNE (objects IsengardWallCliffCap; role wall_end): body IBWALLN, 822 triangles, painted
from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is DXT5).
In IBWALLN mesh coordinates: x -8.32..8.32, y -19.00..57.00, z -46.17..59.24.
Lifecycle models in its Draw module: IBWallNE_A, IBWallNE_D1, IBWallNE_D2, IBWallNE_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure isengard/wall_end` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/wall_end (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class WallEnd(Building):
    style = IsengardStyle()
    source = "IBWallNE"
    target = "IBWALLN"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresF.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallEnd"
    views = {
        "rts": ((-0.0, -19.0, 6.5), 288, 50, -38, 50),
        "close": ((-0.0, -19.0, 6.5), 170, 24, -30, 45),
        "ingame": ((-0.0, -19.0, 6.5), 655, 53, -62, 50),
    }

    def design(self, kit):
        return []
