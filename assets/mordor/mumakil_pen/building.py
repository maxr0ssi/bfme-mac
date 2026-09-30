"""Mordor mumakil pen (MordorMumakilPen): stub from `sagekit new mordor`.

EA's MBMumkpen (objects MordorMumakilPen; role stable): body MUMAKILPEN, 1472 triangles, painted
from MBMumkPen.tga + MBMumkPen_NRM.tga (DXT1).
In MUMAKILPEN mesh coordinates: x -58.81..50.62, y -46.24..46.97, z -3.02..66.62.
Other meshes (EA's, untouched): V1 506 (MBMumkPen_V1.tga, MBMumkPen_V1_NRM.tga); BANNERS 384
(Haradrim_Banr.tga); N_WINDOW 120 (WBCave.tga, WBCave_NRM.tga); V2 99 (MBMumkPen.tga,
MBMumkPen_NRM.tga); N_FIRE 24 (EXFireTorchSeq.tga).
Lifecycle models in its Draw module: MBMUMKPEN_D1, MBMumkPen_D2, MBMumkPen_D3, MBMumkpen_A.
House colour: MBHCMumkPen.
EA's body measured: `python3 -m sagekit measure mordor/mumakil_pen` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class MumakilPen(Building):
    style = MordorStyle()
    source = "MBMumkpen"
    target = "MUMAKILPEN"
    sheet = "MBMumkPen.tga"
    sheet_normal = "MBMumkPen_NRM.tga"
    own_textures = {"MBMumkPen.tga": "MBMumkPeH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-4.1, 0.4, 31.8), 351, 50, -38, 50),
        "close": ((-4.1, 0.4, 31.8), 208, 24, -30, 45),
        "ingame": ((-4.1, 0.4, 31.8), 799, 53, -62, 50),
    }

    def design(self, kit):
        return []
