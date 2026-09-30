"""Mordor troll cage module tag 03 (MordorTrollCage): stub from `sagekit new mordor`.

EA's MBTrollPit_AFDE (objects MordorTrollCage; role stable): body LCHAIN01, 212 triangles,
painted from MBTrollPit.tga, no normal map (DXT1).
In LCHAIN01 mesh coordinates: x -34.15..-11.43, y -17.21..16.19, z 12.05..29.67.
Other meshes (EA's, untouched): TROLL_MESH01 536 (MUCavTroll_alpha.tga); ORC01 264
(MUOrcWarr_Alpha.tga); CYLINDER02 40 (MBTrollPit.tga).
House colour: MBHCTrollPit.
EA's body measured: `python3 -m sagekit measure mordor/troll_cage_module_tag_03` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class TrollCageModuleTag03(Building):
    style = MordorStyle()
    source = "MBTrollPit_AFDE"
    target = "LCHAIN01"
    sheet = "MBTrollPit.tga"
    sheet_normal = None
    own_textures = {"MBTrollPit.tga": "MBTrollPiB.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("DrawModuleTag_03",)
    views = {
        "rts": ((-35.8, -3.5, 20.9), 97, 50, -38, 50),
        "close": ((-35.8, -3.5, 20.9), 57, 24, -30, 45),
        "ingame": ((-35.8, -3.5, 20.9), 220, 53, -62, 50),
    }

    def design(self, kit):
        return []
