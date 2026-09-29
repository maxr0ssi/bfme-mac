"""Isengard furnace (IsengardFurnace): stub from `sagekit new isengard`.

EA's MBFurnace_SKN (objects IsengardFurnace; role economy): body FURNACE, 1141 triangles, painted
from MBFurnace.tga + MBFurnace_NRM.tga (DXT1).
In FURNACE mesh coordinates: x -35.40..64.57, y -46.43..30.01, z -6.78..106.46.
Target ambiguous: V2 (415 triangles) could be the body too (the rule takes a normal-mapped mesh
standing on the ground, then the largest); set `target` to the mesh the design redesigns.
Other meshes (EA's, untouched): V2 415 (MBFurnace.tga, MBFurnace_NRM.tga); MUGBLNSLV 258
(MUOrcPorter2.tga); MUGBLNSLV1 258 (MUOrcPorter2.tga); MOLD 154 (MBFurnace.tga,
MBFurnace_NRM.tga); N_WINDOW 80 (WBCave.tga, WBCave_NRM.tga); LIQUIDMETAL1 80 (moltenMetal.tga);
INGOTS 48 (MBFurnace.tga, MBFurnace_NRM.tga); SHOVEL 46 (MBFurnace.tga, MBFurnace_NRM.tga).
Lifecycle models in its Draw module: MBFurnace_A, MBFurnace_D1, MBFurnace_D2, MBFurnace_D3.
House colour: MBHCFurnace.
EA's body measured: `python3 -m sagekit measure isengard/furnace` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/hearth (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class Furnace(Building):
    style = IsengardStyle()
    source = "MBFurnace_SKN"
    target = "FURNACE"
    sheet = "MBFurnace.tga"
    sheet_normal = "MBFurnace_NRM.tga"
    own_textures = {"MBFurnace.tga": "MBFurnacH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((18.1, -8.4, 50.2), 372, 50, -38, 50),
        "close": ((18.1, -8.4, 50.2), 220, 24, -30, 45),
        "ingame": ((18.1, -8.4, 50.2), 846, 53, -62, 50),
    }

    def design(self, kit):
        return []
