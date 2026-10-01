"""Angmar hallof twilight (AngmarHallofTwilight): stub from `sagekit new angmar`.

EA's KBTemple (objects AngmarHallofTwilight; role barracks): body BASE, 784 triangles, painted
from KBTemple.tga + KBTemple_NRM.tga (DXT1).
In BASE mesh coordinates: x -59.31..57.20, y -65.15..53.81, z -11.19..43.76.
Target ambiguous: ROCKS_1 (202 triangles), V1 (1499 triangles) could be the body too (the rule
takes a normal-mapped mesh standing on the ground, then the largest); set `target` to the mesh
the design redesigns.
Other meshes (EA's, untouched): V2 1753 (KBTemple.tga, KBTemple_NRM.tga); V1 1499 (KBTemple.tga,
KBTemple_NRM.tga); TOP_1 474 (KBTemple.tga, KBTemple_NRM.tga); RUNEGLOWV2 204
(EXTemple_Runes.tga); ROCKS_1 202 (KBTemple.tga, KBTemple_NRM.tga); N_WINDOW 4
(GBNightWIndows.tga).
Lifecycle models in its Draw module: KBTemple_A, KBTemple_D1, KBTemple_D2, KBTemple_D3.
House colour: KBHCTemple.
EA's body measured: `python3 -m sagekit measure angmar/hallof_twilight` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class HallofTwilight(Building):
    style = AngmarStyle()
    source = "KBTemple"
    target = "BASE"
    sheet = "KBTemple.tga"
    sheet_normal = "KBTemple_NRM.tga"
    own_textures = {"KBTemple.tga": "KBTemplH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-1.1, -5.7, 16.3), 386, 50, -38, 50),
        "close": ((-1.1, -5.7, 16.3), 228, 24, -30, 45),
        "ingame": ((-1.1, -5.7, 16.3), 877, 53, -62, 50),
    }

    def design(self, kit):
        return []
