"""Isengard fortress wall hub (IsengardCastleWallHubExpansion): stub from `sagekit new isengard`.

EA's IBFWHub (objects IsengardCastleWallHubExpansion; role fortress_wall_hub): body IBFBALTOW01,
476 triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture
is DXT5).
In IBFBALTOW01 mesh coordinates: x -42.20..24.26, y -22.71..22.71, z -25.53..37.04.
Lifecycle models in its Draw module: IBFWHub_A, IBFWHub_D1, IBFWHub_D2, IBFWHub_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure isengard/fortress_wall_hub` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_wall_hub (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class FortressWallHub(Building):
    style = IsengardStyle()
    source = "IBFWHub"
    target = "IBFBALTOW01"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresB.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressWallHub"
    views = {
        "rts": ((-9.0, -0.0, 31.2), 224, 50, -38, 50),
        "close": ((-9.0, -0.0, 31.2), 133, 24, -30, 45),
        "ingame": ((-9.0, -0.0, 31.2), 510, 53, -62, 50),
    }

    def design(self, kit):
        return []
