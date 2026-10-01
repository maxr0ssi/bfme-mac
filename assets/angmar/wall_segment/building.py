"""Angmar wall segment (AngmarWallSegmentSmall, AngmarWallPosternGateSmall): stub from `sagekit new
angmar`.

EA's KBWallN (objects AngmarWallSegmentSmall, AngmarWallPosternGateSmall; role wall_segment):
body KBWALL01, 380 triangles, painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out
alpha: our texture is DXT5).
In KBWALL01 mesh coordinates: x -10.47..10.34, y -19.00..19.00, z -0.06..81.93.
Other meshes (EA's, untouched): ICEWALL 8 (EXFortressIce.tga, EXIceRefraction01.tga).
Lifecycle models in its Draw module: KBWallN_A, KBWallN_CUR, KBWallN_D1, KBWallN_D2, KBWallN_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/wall_segment` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/wall_segment (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class WallSegment(Building):
    style = AngmarStyle()
    source = "KBWallN"
    target = "KBWALL01"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressD.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallSegment"
    views = {
        "rts": ((-0.1, -0.0, 40.9), 204, 50, -38, 50),
        "close": ((-0.1, -0.0, 40.9), 121, 24, -30, 45),
        "ingame": ((-0.1, -0.0, 40.9), 464, 53, -62, 50),
    }

    def design(self, kit):
        return []
