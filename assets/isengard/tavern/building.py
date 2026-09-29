"""Isengard tavern (IsengardTavern): stub from `sagekit new isengard`.

EA's ibwildbld_skn (objects IsengardTavern; role economy): body BUILDING, 1848 triangles, painted
from ibwildbuilding.tga + ibwildbuilding_NRM.tga (missing).
In BUILDING mesh coordinates: x -42.87..42.87, y -33.67..36.78, z -8.51..63.52.
Other meshes (EA's, untouched): V2 744 (iu_banr_a.tga); V1 402 (ibwildbuilding.tga,
ibwildbuilding_NRM.tga); V3 392 (ibwildbuilding.tga, ibwildbuilding_NRM.tga); TORCHES 80
(ibwildbuilding_D.tga).
Lifecycle models in its Draw module: ibwildbld_D1, ibwildbld_D2, ibwildbld_bld.
House colour: MBHCOrcpit.
MBHCOrcpit is drawn by another faction too: the house step ships an own copy
(Building.own_house_copy).
EA's body measured: `python3 -m sagekit measure isengard/tavern` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/hearth (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class Tavern(Building):
    style = IsengardStyle()
    source = "ibwildbld_skn"
    target = "BUILDING"
    sheet = "ibwildbuilding.tga"
    sheet_normal = "ibwildbuilding_NRM.tga"
    own_textures = {"ibwildbuilding.tga": "ibwildbuildinH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((0.0, 1.6, 27.5), 291, 50, -38, 50),
        "close": ((0.0, 1.6, 27.5), 172, 24, -30, 45),
        "ingame": ((0.0, 1.6, 27.5), 662, 53, -62, 50),
    }

    def design(self, kit):
        return []
