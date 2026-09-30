"""Mordor siege works (MordorSiegeWorks): stub from `sagekit new mordor`.

EA's MBSeigeWork (objects MordorSiegeWorks; role siege): body SEIGEWORK2, 667 triangles, painted
from MBSeigeWork2.tga + MBSeigeWork2_NRM.tga (DXT5, cut-out alpha: our texture is DXT5).
In SEIGEWORK2 mesh coordinates: x -78.99..35.08, y -56.26..58.57, z -2.95..54.57.
Other meshes (EA's, untouched): V2 1512 (MU_Banr_A.tga); SEIGEWORK1 520 (MBSeigeWork1.tga,
MBSeigeWork1_NRM.tga); N_WINDOW 120 (WBCave.tga, WBCave_NRM.tga); N_FIRE 24 (EXFireTorchSeq.tga).
Lifecycle models in its Draw module: MBSeigeW_D1, MBSeigeW_D2, MBSeigeW_D3, MBSeigeWork_A.
House colour: MBHCSeigeWork.
EA's body measured: `python3 -m sagekit measure mordor/siege_works` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/siege_works (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class SiegeWorks(Building):
    style = MordorStyle()
    source = "MBSeigeWork"
    target = "SEIGEWORK2"
    sheet = "MBSeigeWork2.tga"
    sheet_normal = "MBSeigeWork2_NRM.tga"
    own_textures = {"MBSeigeWork2.tga": "MBSeigeWorkH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-22.0, 1.2, 25.9), 378, 50, -38, 50),
        "close": ((-22.0, 1.2, 25.9), 223, 24, -30, 45),
        "ingame": ((-22.0, 1.2, 25.9), 859, 53, -62, 50),
    }

    def design(self, kit):
        return []
