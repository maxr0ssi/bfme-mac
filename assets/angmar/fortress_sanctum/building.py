"""Angmar fortress sanctum (AngmarFortressCitadel): stub from `sagekit new angmar`.

EA's KBFSanctum (objects AngmarFortressCitadel; role fortress_upgrade): body KBFSANCTUM, 1452
triangles, painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our texture
is DXT5).
In KBFSANCTUM mesh coordinates: x -19.09..19.09, y -20.33..20.33, z 0.00..175.38.
Lifecycle models in its Draw module: KBFSanctum_A, KBFSanctum_D1, KBFSanctum_D2, KBFSanctum_D3.
House colour: KBHCFortress.
EA's body measured: `python3 -m sagekit measure angmar/fortress_sanctum` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_monument (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class FortressSanctum(Building):
    style = AngmarStyle()
    source = "KBFSanctum"
    target = "KBFSANCTUM"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressP.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_SanctumDraw",)
    views = {
        "rts": ((0.0, -0.0, 87.7), 405, 50, -38, 50),
        "close": ((0.0, -0.0, 87.7), 239, 24, -30, 45),
        "ingame": ((0.0, -0.0, 87.7), 920, 53, -62, 50),
    }

    def design(self, kit):
        return []
