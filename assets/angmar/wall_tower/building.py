"""Angmar wall tower (AngmarWallTowerSmall): stub from `sagekit new angmar`.

EA's KBArrwWal (objects AngmarWallTowerSmall; role wall_tower): body ARROWTOWER, 1287 triangles,
painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our texture is DXT5).
In ARROWTOWER mesh coordinates: x -19.35..19.60, y -19.25..19.20, z -0.07..111.61.
Lifecycle models in its Draw module: KBArrwWal_A, KBArrwWal_D1, KBArrwWal_D2, KBArrwWal_D3,
KBArwWal_A.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/wall_tower` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/wall_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class WallTower(Building):
    style = AngmarStyle()
    source = "KBArrwWal"
    target = "ARROWTOWER"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressG.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallTower"
    views = {
        "rts": ((0.1, -0.0, 55.8), 274, 50, -38, 50),
        "close": ((0.1, -0.0, 55.8), 162, 24, -30, 45),
        "ingame": ((0.1, -0.0, 55.8), 622, 53, -62, 50),
    }

    def design(self, kit):
        return []
