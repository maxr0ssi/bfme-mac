"""Isengard wall gate (IsengardCastleWallGate): stub from `sagekit new isengard`.

EA's IBWallGateN_SKN (objects IsengardCastleWallGate; role wall_gate): body IBGATE, 200
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBGATE mesh coordinates: x -25.09..25.09, y -59.19..59.19, z 0.00..76.85.
Target ambiguous: IBGATEDOOR02 (712 triangles), IBGATEDOOR01 (712 triangles) could be the body
too (the rule takes a normal-mapped mesh standing on the ground, then the largest); set `target`
to the mesh the design redesigns.
Other meshes (EA's, untouched): IBGATEDOOR02 712 (IBFortress.tga, IBFortress_NRM.tga);
IBGATEDOOR01 712 (IBFortress.tga, IBFortress_NRM.tga).
Lifecycle models in its Draw module: IBWallGateN_D1, IBWallGateN_D2, IBWallGateN_D3,
IBWallGateN_D4.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure isengard/wall_gate` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/wall_gate (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class WallGate(Building):
    style = IsengardStyle()
    source = "IBWallGateN_SKN"
    target = "IBGATE"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresE.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallGate"
    views = {
        "rts": ((-0.0, -0.0, 38.4), 330, 50, -38, 50),
        "close": ((-0.0, -0.0, 38.4), 195, 24, -30, 45),
        "ingame": ((-0.0, -0.0, 38.4), 749, 53, -62, 50),
    }

    def design(self, kit):
        return []
