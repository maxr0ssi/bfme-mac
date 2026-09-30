"""Mordor battle tower (MordorBattleTower): stub from `sagekit new mordor`.

EA's MBSentry (objects MordorBattleTower; role tower): body CYLINDER01, 680 triangles, painted
from DolGolGate.tga + DolGolGate_NRM.tga (DXT1).
In CYLINDER01 mesh coordinates: x -15.31..15.56, y -15.30..15.57, z -0.08..122.77.
Lifecycle models in its Draw module: MBSentry_A, MBSentry_D1, MBSentry_D2, MBSentry_D3.
House colour: MBHCSentry.
Its sheet is drawn by angmar too: our own texture is pinned in own_textures.
EA's body measured: `python3 -m sagekit measure mordor/battle_tower` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/sentry_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class BattleTower(Building):
    style = MordorStyle()
    source = "MBSentry"
    target = "CYLINDER01"
    sheet = "DolGolGate.tga"
    sheet_normal = "DolGolGate_NRM.tga"
    own_textures = {"DolGolGate.tga": "DolGolGatH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((0.0, 0.0, 61.3), 287, 50, -38, 50),
        "close": ((0.0, 0.0, 61.3), 169, 24, -30, 45),
        "ingame": ((0.0, 0.0, 61.3), 652, 53, -62, 50),
    }

    def design(self, kit):
        return []
