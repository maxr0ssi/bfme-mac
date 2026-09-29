"""Isengard ballista (IsengardBallistaExpansion): stub from `sagekit new isengard`.

EA's IBFBalTow (objects IsengardBallistaExpansion; role catapult_tower): body IBFBALTOW, 234
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFBALTOW mesh coordinates: x -35.67..18.13, y -20.32..20.32, z -0.06..51.00.
Other meshes (EA's, untouched): IBFBALTOWB 24 (IBFortress.tga); P1 2 (IBFortress.tga).
Lifecycle models in its Draw module: IBFBalTow_A, IBFBalTow_D2, IBFBalTow_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure isengard/ballista` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/catapult_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class Ballista(Building):
    style = IsengardStyle()
    source = "IBFBalTow"
    target = "IBFBALTOW"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCBallista"
    views = {
        "rts": ((-8.8, -0.0, 25.5), 186, 50, -38, 50),
        "close": ((-8.8, -0.0, 25.5), 110, 24, -30, 45),
        "ingame": ((-8.8, -0.0, 25.5), 423, 53, -62, 50),
    }

    def design(self, kit):
        return []
