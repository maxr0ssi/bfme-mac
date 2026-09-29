"""Isengard wall segment (IsengardCastleWallSegment): stub from `sagekit new isengard`.

EA's IBWallN (objects IsengardCastleWallSegment; role wall_segment): body IBWALLN, 376 triangles,
painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is DXT5).
In IBWALLN mesh coordinates: x -8.32..8.32, y -19.00..19.03, z -0.06..59.24.
Lifecycle models in its Draw module: IBWallN_A, IBWallN_D1, IBWallN_D2, IBWallN_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure isengard/wall_segment` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/wall_segment (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class WallSegment(Building):
    style = IsengardStyle()
    source = "IBWallN"
    target = "IBWALLN"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresC.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallSegment"
    views = {
        "rts": ((0.0, 0.0, 29.6), 159, 50, -38, 50),
        "close": ((0.0, 0.0, 29.6), 94, 24, -30, 45),
        "ingame": ((0.0, 0.0, 29.6), 362, 53, -62, 50),
    }

    def design(self, kit):
        return []
