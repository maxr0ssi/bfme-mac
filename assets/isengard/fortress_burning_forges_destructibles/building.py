"""Isengard fortress burning forges destructibles (IsengardFortressCitadel): stub from `sagekit new
isengard` (folder renamed from EA's tag spelling, ModuleTag_DrawBurningForgesDescrutbiles).

EA's IBFBForgB (objects IsengardFortressCitadel; role fortress_upgrade): body IBFBFORGES, 971
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFBFORGES mesh coordinates: x -70.40..-19.33, y -29.45..25.43, z -0.00..124.03.
Other meshes (EA's, untouched): P1 2.
Lifecycle models in its Draw module: IBFBForgB_A, IBFBForgB_D2, IBFBForgB_D3.
House colour: IBHCFortress.
EA's body measured: `python3 -m sagekit measure isengard/fortress_burning_forges_destructibles` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_statues (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class FortressBurningForgesDescrutbiles(Building):
    style = IsengardStyle()
    source = "IBFBForgB"
    target = "IBFBFORGES"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresM.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawBurningForgesDescrutbiles",)
    views = {
        "rts": ((-44.9, -2.0, 62.0), 319, 50, -38, 50),
        "close": ((-44.9, -2.0, 62.0), 188, 24, -30, 45),
        "ingame": ((-44.9, -2.0, 62.0), 725, 53, -62, 50),
    }

    def design(self, kit):
        return []
