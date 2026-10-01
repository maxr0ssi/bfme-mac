"""Angmar hallof twilight v1 (AngmarHallofTwilight): stub from `sagekit new angmar`.

EA's KBTemple (objects AngmarHallofTwilight; role barracks): body V1, 1499 triangles, painted
from KBTemple.tga + KBTemple_NRM.tga (DXT1).
In V1 mesh coordinates: x -65.44..64.90, y -59.54..64.55, z -24.30..86.04.
Target ambiguous: ROCKS_1 (202 triangles), V1 (1499 triangles) could be the body too (the rule
takes a normal-mapped mesh standing on the ground, then the largest); set `target` to the mesh
the design redesigns.
Other meshes (EA's, untouched): V2 1753 (KBTemple.tga, KBTemple_NRM.tga); BASE 784 (KBTemple.tga,
KBTemple_NRM.tga); TOP_1 474 (KBTemple.tga, KBTemple_NRM.tga); RUNEGLOWV2 204
(EXTemple_Runes.tga); ROCKS_1 202 (KBTemple.tga, KBTemple_NRM.tga); N_WINDOW 4
(GBNightWIndows.tga).
Lifecycle models in its Draw module: KBTemple_A, KBTemple_D1, KBTemple_D2, KBTemple_D3.
House colour: KBHCTemple.
EA's body measured: `python3 -m sagekit measure angmar/hallof_twilight_v1` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
A second body of KBTemple: chained on angmar/hallof_twilight (`base`), built after it.
"""
from sagekit.building import Building

from ..style import AngmarStyle


class HallofTwilightV1(Building):
    style = AngmarStyle()
    source = "KBTemple"
    target = "V1"
    base = "angmar/hallof_twilight"
    sheet = "KBTemple.tga"
    sheet_normal = "KBTemple_NRM.tga"
    own_textures = {"KBTemple.tga": "KBTemplX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-0.3, 2.5, 30.9), 464, 50, -38, 50),
        "close": ((-0.3, 2.5, 30.9), 274, 24, -30, 45),
        "ingame": ((-0.3, 2.5, 30.9), 1055, 53, -62, 50),
    }

    def design(self, kit):
        return []
