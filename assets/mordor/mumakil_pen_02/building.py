"""Mordor mumakil pen 02 (MordorMumakilPen): stub from `sagekit new mordor`.

EA's MBMumkpenDSCL (objects MordorMumakilPen; role stable): body MUMAKILPEN_A, 224 triangles,
painted from MBMumkPen.tga + MBMumkPen_NRM.tga (DXT1).
In MUMAKILPEN_A mesh coordinates: x -43.18..35.57, y -23.23..23.79, z 44.29..50.34.
Lifecycle models in its Draw module: MBMumkpenDOP, MBMumkpen_DRA, MBMumkpen_DROCD.
House colour: MBHCMumkPen.
EA's body measured: `python3 -m sagekit measure mordor/mumakil_pen_02` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class MumakilPen02(Building):
    style = MordorStyle()
    source = "MBMumkpenDSCL"
    target = "MUMAKILPEN_A"
    sheet = "MBMumkPen.tga"
    sheet_normal = "MBMumkPen_NRM.tga"
    own_textures = {"MBMumkPen.tga": "MBMumkPeX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_02",)
    views = {
        "rts": ((-3.8, 0.3, 47.3), 202, 50, -38, 50),
        "close": ((-3.8, 0.3, 47.3), 119, 24, -30, 45),
        "ingame": ((-3.8, 0.3, 47.3), 460, 53, -62, 50),
    }

    def design(self, kit):
        return []
