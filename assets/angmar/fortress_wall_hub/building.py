"""Angmar fortress wall hub (AngmarWallHubSmallExpansion): stub from `sagekit new angmar`.

EA's KBHTow (objects AngmarWallHubSmallExpansion; role fortress_wall_hub): body HUBTOWER, 436
triangles, painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our texture
is DXT5).
In HUBTOWER mesh coordinates: x -42.35..27.75, y -32.19..22.16, z 0.05..96.12.
Other meshes (EA's, untouched): ICEWALL 18 (EXFortressIce.tga, EXIceRefraction01.tga).
Lifecycle models in its Draw module: KBHTow_A, KBHTow_D1, KBHTow_D2, KBHTow_D3, kkbhtow_a.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/fortress_wall_hub` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_wall_hub (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class FortressWallHub(Building):
    style = AngmarStyle()
    source = "KBHTow"
    target = "HUBTOWER"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressM.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressWallHub"
    views = {
        "rts": ((-7.3, -5.0, 48.1), 288, 50, -38, 50),
        "close": ((-7.3, -5.0, 48.1), 170, 24, -30, 45),
        "ingame": ((-7.3, -5.0, 48.1), 654, 53, -62, 50),
    }

    def design(self, kit):
        return []
