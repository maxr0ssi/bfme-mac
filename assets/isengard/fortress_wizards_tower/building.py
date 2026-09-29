"""Isengard fortress wizards tower (IsengardFortressCitadel): stub from `sagekit new isengard`.

EA's IBFWTower (objects IsengardFortressCitadel; role fortress_upgrade): body IBFWTOWER, 1572
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFWTOWER mesh coordinates: x -21.79..21.79, y -21.79..21.79, z -0.00..175.69.
Lifecycle models in its Draw module: IBFWTower_A, IBFWTower_D1, IBFWTower_D2, IBFWTower_D3.
House colour: IBHCFortress.
EA's body measured: `python3 -m sagekit measure isengard/fortress_wizards_tower` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_monument (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class FortressWizardsTower(Building):
    style = IsengardStyle()
    source = "IBFWTower"
    target = "IBFWTOWER"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresN.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawWizardsTower",)
    views = {
        "rts": ((-0.0, 0.0, 87.8), 410, 50, -38, 50),
        "close": ((-0.0, 0.0, 87.8), 242, 24, -30, 45),
        "ingame": ((-0.0, 0.0, 87.8), 931, 53, -62, 50),
    }

    def design(self, kit):
        return []
