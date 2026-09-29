"""Isengard fortress excavations destructibles (IsengardFortressCitadel): stub from `sagekit new
isengard`.

EA's IBFExcavB (objects IsengardFortressCitadel; role fortress_upgrade): body IBFEXCAVB, 374
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFEXCAVB mesh coordinates: x -35.04..15.15, y -56.80..29.66, z 10.00..66.36.
Lifecycle models in its Draw module: IBFExcavB_A, IBFExcavB_D3.
House colour: IBHCFortress.
EA's body measured: `python3 -m sagekit measure isengard/fortress_excavations_destructibles` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_barrels (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class FortressExcavationsDestructibles(Building):
    style = IsengardStyle()
    source = "IBFExcavB"
    target = "IBFEXCAVB"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresK.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawExcavationsDestructibles",)
    views = {
        "rts": ((-9.9, -13.6, 38.2), 252, 50, -38, 50),
        "close": ((-9.9, -13.6, 38.2), 149, 24, -30, 45),
        "ingame": ((-9.9, -13.6, 38.2), 574, 53, -62, 50),
    }

    def design(self, kit):
        return []
