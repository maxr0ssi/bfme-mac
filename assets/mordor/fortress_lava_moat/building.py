"""Mordor fortress lava moat (MordorFortressLavaMoat): stub from `sagekit new mordor`.

EA's MBFLavaMoat (objects MordorFortressLavaMoat; role fortress_addon): body MBFLAVAMOAT, 630
triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In MBFLAVAMOAT mesh coordinates: x -96.57..93.61, y -93.48..95.19, z 0.00..16.93.
Other meshes (EA's, untouched): MBFLAVAMEFF 96 (MinasMorgulFX2.tga, MinasMorgulFX3.tga);
MBFLAVAMALPH 64 (MBFortress.tga); OBJECT01 60 (S3_Lava.tga).
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure mordor/fortress_lava_moat` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_monument (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class FortressLavaMoat(Building):
    style = MordorStyle()
    source = "MBFLavaMoat"
    target = "MBFLAVAMOAT"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresE.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressLavaMoat"
    views = {
        "rts": ((-1.5, 0.9, 8.5), 591, 50, -38, 50),
        "close": ((-1.5, 0.9, 8.5), 349, 24, -30, 45),
        "ingame": ((-1.5, 0.9, 8.5), 1342, 53, -62, 50),
    }

    def design(self, kit):
        return []
