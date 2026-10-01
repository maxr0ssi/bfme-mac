"""Angmar wall end (AngmarWallCliffCap): stub from `sagekit new angmar`.

EA's Dwarf (objects AngmarWallCliffCap; role wall_end): body DWARF, 1099 triangles, painted from
KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our texture is DXT5).
In DWARF mesh coordinates: x -10.46..10.35, y -57.00..19.00, z -43.71..73.49.
Other meshes (EA's, untouched): ICEWALL 8 (EXFortressIce.tga, EXIceRefraction01.tga).
Lifecycle models in its Draw module: Dwarf_A, Dwarf_D1, Dwarf_D2, Dwarf_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/wall_end` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/wall_end (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class WallEnd(Building):
    style = AngmarStyle()
    source = "Dwarf"
    target = "DWARF"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressK.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallEnd"
    views = {
        "rts": ((-0.1, -19.0, 14.9), 311, 50, -38, 50),
        "close": ((-0.1, -19.0, 14.9), 184, 24, -30, 45),
        "ingame": ((-0.1, -19.0, 14.9), 706, 53, -62, 50),
    }

    def design(self, kit):
        return []
