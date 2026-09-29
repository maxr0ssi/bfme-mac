"""Isengard fortress burning forges (IsengardFortressCitadel): stub from `sagekit new isengard`.

EA's IBFBForges (objects IsengardFortressCitadel; role fortress_upgrade): body IBFBFORGESA, 957
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFBFORGESA mesh coordinates: x -16.37..16.37, y -10.72..10.72, z -16.37..16.37.
Lifecycle models in its Draw module: IBFBForges_A.
House colour: IBHCFortress.
EA's body measured: `python3 -m sagekit measure isengard/fortress_burning_forges` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_statues (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class FortressBurningForges(Building):
    style = IsengardStyle()
    source = "IBFBForges"
    target = "IBFBFORGESA"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresL.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawBurningForges",)
    views = {
        "rts": ((-42.1, 4.5, 66.2), 112, 50, -38, 50),
        "close": ((-42.1, 4.5, 66.2), 66, 24, -30, 45),
        "ingame": ((-42.1, 4.5, 66.2), 255, 53, -62, 50),
    }

    def design(self, kit):
        return []
