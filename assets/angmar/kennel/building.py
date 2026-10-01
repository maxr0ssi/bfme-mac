"""Angmar kennel (AngmarKennelExpansion): stub from `sagekit new angmar`.

EA's KBFKennel (objects AngmarKennelExpansion; role hall_expansion): body KBFKENNEL, 645
triangles, painted from KBFortressX.tga + KBFortressX_NRM.tga (DXT1).
In KBFKENNEL mesh coordinates: x -37.09..37.09, y -32.11..32.11, z -34.15..34.15.
Other meshes (EA's, untouched): ICEWALL 28 (EXFortressIce.tga, EXIceRefraction01.tga).
Lifecycle models in its Draw module: KBFKennel_A, KBFKennel_D1, KBFKennel_D2, KBFKennel_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/kennel` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/hall (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class Kennel(Building):
    style = AngmarStyle()
    source = "KBFKennel"
    target = "KBFKENNEL"
    sheet = "KBFortressX.tga"
    sheet_normal = "KBFortressX_NRM.tga"
    own_textures = {"KBFortressX.tga": "KBFortressR.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCKennel"
    views = {
        "rts": ((-3.3, -1.0, 34.1), 263, 50, -38, 50),
        "close": ((-3.3, -1.0, 34.1), 155, 24, -30, 45),
        "ingame": ((-3.3, -1.0, 34.1), 598, 53, -62, 50),
    }

    def design(self, kit):
        return []
