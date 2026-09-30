"""Mordor slaughter house (MordorSlaughterHouse): stub from `sagekit new mordor`.

EA's MBSltrHs_SKN (objects MordorSlaughterHouse; role economy): body MBSLTRHS, 832 triangles,
painted from MBSltrHs.tga + MBSltrHs_NRM.tga (DXT1).
In MBSLTRHS mesh coordinates: x -53.42..37.54, y -71.42..51.34, z -3.36..63.67.
Target ambiguous: V2 (794 triangles) could be the body too (the rule takes a normal-mapped mesh
standing on the ground, then the largest); set `target` to the mesh the design redesigns.
Other meshes (EA's, untouched): V2 794 (MBSltrHs.tga, MBSltrHs_NRM.tga); HOOKWHEEL 512
(MBSltrHs.tga, MBSltrHs_NRM.tga); ORCPORTER 258 (MUOrcPorter2.tga); ORCPORTER_STR 258
(MUOrcPorter2.tga); RHYNOE_STR 228 (MBSltrHs.tga); N_WINDOW 120 (WBCave.tga, WBCave_NRM.tga);
MEAT10 80 (MBSltrHs.tga, MBSltrHs_NRM.tga); MEAT09 80 (MBSltrHs.tga, MBSltrHs_NRM.tga).
Lifecycle models in its Draw module: MBSltrHs_A, MBSltrHs_D1, MBSltrHs_D2, MBSltrHs_D3.
House colour: MBHCSltrHs.
EA's body measured: `python3 -m sagekit measure mordor/slaughter_house` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/hearth (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class SlaughterHouse(Building):
    style = MordorStyle()
    source = "MBSltrHs_SKN"
    target = "MBSLTRHS"
    sheet = "MBSltrHs.tga"
    sheet_normal = "MBSltrHs_NRM.tga"
    own_textures = {"MBSltrHs.tga": "MBSltrHH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-7.9, -10.0, 30.2), 367, 50, -38, 50),
        "close": ((-7.9, -10.0, 30.2), 217, 24, -30, 45),
        "ingame": ((-7.9, -10.0, 30.2), 834, 53, -62, 50),
    }

    def design(self, kit):
        return []
