"""Mordor fortress magma cauldrons (MordorFortressCitadel): stub from `sagekit new mordor`.

EA's MBFMCauld (objects MordorFortressCitadel; role fortress_upgrade): body MBFMCAULD, 780
triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In MBFMCAULD mesh coordinates: x -52.74..52.74, y -52.74..52.74, z 0.00..98.92.
Lifecycle models in its Draw module: MBFMCauld_A, MBFMCauld_D2, MBFMCauld_D3.
House colour: MBHCFortress.
EA's body measured: `python3 -m sagekit measure mordor/fortress_magma_cauldrons` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_barrels (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class FortressMagmaCauldrons(Building):
    style = MordorStyle()
    source = "MBFMCauld"
    target = "MBFMCAULD"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresC.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawMagmaCauldrons",)
    views = {
        "rts": ((0.0, 0.0, 49.5), 394, 50, -38, 50),
        "close": ((0.0, 0.0, 49.5), 233, 24, -30, 45),
        "ingame": ((0.0, 0.0, 49.5), 895, 53, -62, 50),
    }

    def design(self, kit):
        return []
