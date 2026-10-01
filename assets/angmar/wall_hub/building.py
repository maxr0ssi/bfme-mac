"""Angmar wall hub (AngmarWallHubSmall): stub from `sagekit new angmar`.

EA's KBWallHubN (objects AngmarWallHubSmall; role wall_hub): body WALL HUB, 352 triangles,
painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our texture is DXT5).
In WALL HUB mesh coordinates: x -27.14..27.14, y -27.88..27.88, z -48.03..48.03.
Lifecycle models in its Draw module: KBWalHubN_A, KBWalHubN_D3, KBWallHubN_D1, KBWallHubN_D2.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/wall_hub` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/wall_hub (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class WallHub(Building):
    style = AngmarStyle()
    source = "KBWallHubN"
    target = "WALL HUB"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressC.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallHub"
    views = {
        "rts": ((-0.1, -5.0, 48.1), 272, 50, -38, 50),
        "close": ((-0.1, -5.0, 48.1), 161, 24, -30, 45),
        "ingame": ((-0.1, -5.0, 48.1), 618, 53, -62, 50),
    }

    def design(self, kit):
        return []
