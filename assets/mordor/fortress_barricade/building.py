"""Mordor fortress barricade (MordorFortressBarricadeExpansion): stub from `sagekit new mordor`.

EA's MBFBarric (objects MordorFortressBarricadeExpansion; role hall_expansion): body MBFBARRIC,
1199 triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our
texture is DXT5).
In MBFBARRIC mesh coordinates: x -65.75..9.99, y -13.19..13.19, z 0.00..120.82.
Other meshes (EA's, untouched): BIB 92 (MBFortress.tga); P1 2.
Lifecycle models in its Draw module: MBFBarric_A, MBFBarric_D2, MBFBarric_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure mordor/fortress_barricade` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/hall (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class FortressBarricade(Building):
    style = MordorStyle()
    source = "MBFBarric"
    target = "MBFBARRIC"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressBarricade"
    views = {
        "rts": ((-27.9, -0.0, 60.4), 319, 50, -38, 50),
        "close": ((-27.9, -0.0, 60.4), 189, 24, -30, 45),
        "ingame": ((-27.9, -0.0, 60.4), 725, 53, -62, 50),
    }

    def design(self, kit):
        return []
