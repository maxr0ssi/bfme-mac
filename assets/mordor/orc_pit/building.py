"""Mordor orc pit (MordorOrcPit): stub from `sagekit new mordor`.

EA's MBOrcpit_SKN (objects MordorOrcPit; role barracks): body ORCPIT, 257 triangles, painted from
MBBStone.tga + MBBStone_NRM.tga (DXT1).
In ORCPIT mesh coordinates: x -58.92..55.38, y -41.92..56.72, z 0.00..32.83.
Other meshes (EA's, untouched): V2 1512 (MU_Banr_A.tga); ORC 264 (MUOrcWarr.tga); V1HIDE02 178
(MBOrcpit_mud.tga); V1HIDE01 178 (MBOrcpit_mud.tga); V1HIDE00 178 (MBOrcpit_mud.tga); V1C 178
(MBOrcpit_mud_V3.tga); V1B 178 (MBOrcpit_mud_V3.tga); V1D 178 (MBOrcpit_mud_V3.tga).
Lifecycle models in its Draw module: MBOrcpit_A, MBOrcpit_D1, MBOrcpit_D2, MBOrcpit_D3.
House colour: MBHCOrcpit.
MBHCOrcpit is drawn by another faction too: the house step ships an own copy
(Building.own_house_copy).
EA's body measured: `python3 -m sagekit measure mordor/orc_pit` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class OrcPit(Building):
    style = MordorStyle()
    source = "MBOrcpit_SKN"
    target = "ORCPIT"
    sheet = "MBBStone.tga"
    sheet_normal = "MBBStone_NRM.tga"
    own_textures = {"MBBStone.tga": "MBBStonH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-1.8, 7.4, 16.4), 340, 50, -38, 50),
        "close": ((-1.8, 7.4, 16.4), 201, 24, -30, 45),
        "ingame": ((-1.8, 7.4, 16.4), 773, 53, -62, 50),
    }

    def design(self, kit):
        return []
