"""Mordor tavern (MordorTavern): stub from `sagekit new mordor`.

EA's MBTavern_SKN (objects MordorTavern; role economy): body MAINHOUSE, 528 triangles, painted
from MBTavern.tga + MBTavern_NRM.tga (DXT1).
In MAINHOUSE mesh coordinates: x -51.27..50.69, y -44.68..36.86, z -0.24..72.15.
Other meshes (EA's, untouched): MUCORSAIR 1406 (MUCorsair.tga); ALPHAOBJECTS 720
(MBTavernWD.tga); V1 272 (MBTavernWD.tga); FXGLOWCARDS 44 (EXLnzFlar1.tga, EXNoise01.tga);
FXFIRE02 32 (EXFireTorchSeq.tga).
Lifecycle models in its Draw module: MBTavern_ASKN, MBTavern_D1, MBTavern_D2, MBTavern_D3.
House colour: MBHCTavern.
Its sheet is drawn by isengard too: our own texture is pinned in own_textures.
EA's body measured: `python3 -m sagekit measure mordor/tavern` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/hearth (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class Tavern(Building):
    style = MordorStyle()
    source = "MBTavern_SKN"
    target = "MAINHOUSE"
    sheet = "MBTavern.tga"
    sheet_normal = "MBTavern_NRM.tga"
    own_textures = {"MBTavern.tga": "MBTaverH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-0.3, -3.9, 36.0), 328, 50, -38, 50),
        "close": ((-0.3, -3.9, 36.0), 194, 24, -30, 45),
        "ingame": ((-0.3, -3.9, 36.0), 746, 53, -62, 50),
    }

    def design(self, kit):
        return []
