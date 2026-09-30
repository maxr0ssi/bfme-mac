"""Mordor troll cage (MordorTrollCage): stub from `sagekit new mordor`.

EA's MBTrollPit_SKN (objects MordorTrollCage; role stable): body MBTROLLPIT, 1064 triangles,
painted from MBTrollPit.tga + MBTrollPit_NRM.tga (DXT1).
In MBTROLLPIT mesh coordinates: x -44.39..84.08, y -46.15..48.36, z -2.18..57.59.
Other meshes (EA's, untouched): V2 1218 (MU_Banr_A.tga); TROLL_MESH 536 (MUCavTroll.tga); ORC 264
(MUOrcWarr.tga); CHAIN 212 (MBTrollPit.tga); N_WINDOW 120 (WBCave.tga, WBCave_NRM.tga);
CYLINDER01 40 (MBTrollPit.tga); N_FIRE 24 (EXFireTorchSeq.tga).
Lifecycle models in its Draw module: MBTrollPit_A, MBTrollPit_D1, MBTrollPit_D2, MBTrollPit_D3.
House colour: MBHCTrollPit.
EA's body measured: `python3 -m sagekit measure mordor/troll_cage` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class TrollCage(Building):
    style = MordorStyle()
    source = "MBTrollPit_SKN"
    target = "MBTROLLPIT"
    sheet = "MBTrollPit.tga"
    sheet_normal = "MBTrollPit_NRM.tga"
    own_textures = {"MBTrollPit.tga": "MBTrollPiH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_Draw",)
    views = {
        "rts": ((1.4, -1.0, 27.9), 375, 50, -38, 50),
        "close": ((1.4, -1.0, 27.9), 221, 24, -30, 45),
        "ingame": ((1.4, -1.0, 27.9), 852, 53, -62, 50),
    }

    def design(self, kit):
        return []
