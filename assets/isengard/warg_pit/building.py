"""Isengard warg pit (IsengardWargPit): stub from `sagekit new isengard`.

EA's IBWARGPIT (objects IsengardWargPit; role stable): body IPWARGPIT, 3224 triangles, painted
from IBWargPit.tga + IBWargPit_NRM.tga (DXT5, cut-out alpha: our texture is DXT5).
In IPWARGPIT mesh coordinates: x -46.78..39.56, y -50.33..49.36, z -2.00..46.46.
Other meshes (EA's, untouched): WARG_B 954 (IUWarg_A.tga); V2 446 (IBWargPit.tga,
IBWargPit_NRM.tga); N_WINDOW 120 (WBCave.tga, WBCave_NRM.tga); FUR_ALPHA_B 55 (IUWargFur_A.tga);
N_FIRE 24 (EXFireTorchSeq.tga).
Lifecycle models in its Draw module: IBWargPit_A, IBWargPit_D1, IBWargPit_D2, IBWargPit_D3.
House colour: IBHCWargPit.
EA's body measured: `python3 -m sagekit measure isengard/warg_pit` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class WargPit(Building):
    style = IsengardStyle()
    source = "IBWARGPIT"
    target = "IPWARGPIT"
    sheet = "IBWargPit.tga"
    sheet_normal = "IBWargPit_NRM.tga"
    own_textures = {"IBWargPit.tga": "IBWargPiH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_Draw",)
    views = {
        "rts": ((-3.6, -0.5, 22.2), 309, 50, -38, 50),
        "close": ((-3.6, -0.5, 22.2), 183, 24, -30, 45),
        "ingame": ((-3.6, -0.5, 22.2), 702, 53, -62, 50),
    }

    def design(self, kit):
        return []
