"""Isengard warg sentry (IsengardWargSentry): stub from `sagekit new isengard`.

EA's IBWargSent (objects IsengardWargSentry; role tower): body IBWARGSENT, 3013 triangles,
painted from IBWargSent.tga + IBWargSent_NRM.tga (DXT5).
In IBWARGSENT mesh coordinates: x -57.74..64.42, y -59.58..65.16, z -0.31..32.74.
Other meshes (EA's, untouched): N_WINDOW 80 (WBCave.tga, WBCave_NRM.tga); N_FIRE 16
(EXFireTorchSeq.tga).
Lifecycle models in its Draw module: IBWargSent_A, IBWargSent_D1, IBWargSent_D2, IBWargSent_D3.
House colour: IBHCWargSent.
EA's body measured: `python3 -m sagekit measure isengard/warg_sentry` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/sentry_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class WargSentry(Building):
    style = IsengardStyle()
    source = "IBWargSent"
    target = "IBWARGSENT"
    sheet = "IBWargSent.tga"
    sheet_normal = "IBWargSent_NRM.tga"
    own_textures = {"IBWargSent.tga": "IBWargSenH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((3.3, 2.8, 16.2), 391, 50, -38, 50),
        "close": ((3.3, 2.8, 16.2), 231, 24, -30, 45),
        "ingame": ((3.3, 2.8, 16.2), 888, 53, -62, 50),
    }

    def design(self, kit):
        return []
