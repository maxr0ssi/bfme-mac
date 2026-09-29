"""Isengard wall hub (IsengardCastleWallHub): stub from `sagekit new isengard`.

EA's IBWallRmprtN (objects IsengardCastleWallHub; role wall_hub): body IBFBALTOW01, 258
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFBALTOW01 mesh coordinates: x -24.26..24.26, y -22.71..22.71, z -25.53..37.04.
Lifecycle models in its Draw module: IBWallRmprtN_A, IBWallRmprtN_D1, IBWallRmprtN_D2,
IBWallRmprtN_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure isengard/wall_hub` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/wall_hub (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class WallHub(Building):
    style = IsengardStyle()
    source = "IBWallRmprtN"
    target = "IBFBALTOW01"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresD.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallHub"
    views = {
        "rts": ((0.0, -0.0, 31.2), 201, 50, -38, 50),
        "close": ((0.0, -0.0, 31.2), 119, 24, -30, 45),
        "ingame": ((0.0, -0.0, 31.2), 456, 53, -62, 50),
    }

    def design(self, kit):
        return []
