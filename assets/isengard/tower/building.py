"""Isengard tower (IsengardTowerExpansion): stub from `sagekit new isengard`.

EA's IBFITower (objects IsengardTowerExpansion; role tower_expansion): body IBFITOWER, 848
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFITOWER mesh coordinates: x -32.67..16.26, y -15.57..15.57, z -0.06..130.48.
Other meshes (EA's, untouched): IBFITOWERB 38 (IBFortress.tga).
Lifecycle models in its Draw module: IBFITower_A, IBFITower_D2, IBFITower_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure isengard/tower` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/erebor_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class Tower(Building):
    style = IsengardStyle()
    source = "IBFITower"
    target = "IBFITOWER"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresQ.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCTower"
    views = {
        "rts": ((-8.2, -0.0, 65.2), 314, 50, -38, 50),
        "close": ((-8.2, -0.0, 65.2), 186, 24, -30, 45),
        "ingame": ((-8.2, -0.0, 65.2), 714, 53, -62, 50),
    }

    def design(self, kit):
        return []
