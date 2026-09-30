"""Mordor fortress gorgoroth spire (MordorFortressCitadel): stub from `sagekit new mordor`.

EA's MBFEWEye (objects MordorFortressCitadel; role fortress_upgrade): body MBFEWEYE, 1060
triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In MBFEWEYE mesh coordinates: x -19.15..19.15, y -23.32..23.32, z -0.00..174.75.
Lifecycle models in its Draw module: MBFEWEye_A, MBFEWEye_D2, MBFEWEye_D3.
House colour: MBHCFortress.
EA's body measured: `python3 -m sagekit measure mordor/fortress_gorgoroth_spire` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_statues (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class FortressGorgorothSpire(Building):
    style = MordorStyle()
    source = "MBFEWEye"
    target = "MBFEWEYE"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresD.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawGorgorothSpire",)
    views = {
        "rts": ((0.0, 0.0, 87.4), 407, 50, -38, 50),
        "close": ((0.0, 0.0, 87.4), 240, 24, -30, 45),
        "ingame": ((0.0, 0.0, 87.4), 924, 53, -62, 50),
    }

    def design(self, kit):
        return []
