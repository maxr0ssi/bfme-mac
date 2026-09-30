"""Mordor fortress fire arrows (MordorFortressCitadel): stub from `sagekit new mordor`.

EA's MBFFArrows (objects MordorFortressCitadel; role fortress_upgrade): body MBFFARROWS, 376
triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In MBFFARROWS mesh coordinates: x 32.60..51.58, y -9.49..9.49, z 59.96..89.84.
Other meshes (EA's, untouched): FLAMES 8 (EXFireTorchSeq.tga); FIREGLOW 4 (PG02.tga).
Lifecycle models in its Draw module: MBFFArrows_A, MBFFArrows_D1, MBFFArrows_D2, MBFFArrows_D3.
House colour: MBHCFortress.
EA's body measured: `python3 -m sagekit measure mordor/fortress_fire_arrows` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_barrels (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class FortressFireArrows(Building):
    style = MordorStyle()
    source = "MBFFArrows"
    target = "MBFFARROWS"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresB.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawFireArrows",)
    views = {
        "rts": ((42.1, -0.0, 74.9), 88, 50, -38, 50),
        "close": ((42.1, -0.0, 74.9), 52, 24, -30, 45),
        "ingame": ((42.1, -0.0, 74.9), 201, 53, -62, 50),
    }

    def design(self, kit):
        return []
