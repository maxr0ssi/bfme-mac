"""Angmar sentry tower (AngmarSentryTower): stub from `sagekit new angmar`.

EA's KBBtlTwr (objects AngmarSentryTower; role tower): body BASE, 1527 triangles, painted from
KBBtlTwr.tga + KBBtlTwr_Nrm.tga (DXT1).
In BASE mesh coordinates: x -28.15..25.11, y -30.92..32.06, z -0.08..128.53.
Other meshes (EA's, untouched): N_WINDOW 4 (GBNightWIndows.tga).
Lifecycle models in its Draw module: KBBtlTwr_A, KBBtlTwr_D1, KBBtlTwr_D2, KBBtlTwr_D3.
House colour: KBHCBtlTwr.
EA's body measured: `python3 -m sagekit measure angmar/sentry_tower` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/sentry_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class SentryTower(Building):
    style = AngmarStyle()
    source = "KBBtlTwr"
    target = "BASE"
    sheet = "KBBtlTwr.tga"
    sheet_normal = "KBBtlTwr_Nrm.tga"
    own_textures = {"KBBtlTwr.tga": "KBBtlTwH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-1.5, 0.6, 64.2), 336, 50, -38, 50),
        "close": ((-1.5, 0.6, 64.2), 199, 24, -30, 45),
        "ingame": ((-1.5, 0.6, 64.2), 764, 53, -62, 50),
    }

    def design(self, kit):
        return []
