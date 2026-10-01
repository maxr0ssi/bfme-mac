"""Angmar den (AngmarDen): stub from `sagekit new angmar`.

EA's KBDen (objects AngmarDen; role barracks): body BASE, 2256 triangles, painted from KBDen.tga
+ KBDen_NRM.tga (DXT1).
In BASE mesh coordinates: x -64.92..63.64, y -67.13..69.70, z -1.48..80.15.
Other meshes (EA's, untouched): BROWNWOLF01 594 (KUDireWolf.tga); V1 323 (KBDen.tga,
KBDen_NRM.tga); OBJDEFAULT 308 (KUOrcWar.tga); DUMMYMAN 305 (Dummy.tga); V2 298 (KBDen.tga,
KBDen_NRM.tga); STICK 12 (KBDen.tga, KBDen_NRM.tga); ROPE 8 (Dummy.tga).
Lifecycle models in its Draw module: KBDen_A, KBDen_D1, KBDen_D2, KBDen_D3.
House colour: KBHCDen.
EA's body measured: `python3 -m sagekit measure angmar/den` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class Den(Building):
    style = AngmarStyle()
    source = "KBDen"
    target = "BASE"
    sheet = "KBDen.tga"
    sheet_normal = "KBDen_NRM.tga"
    own_textures = {"KBDen.tga": "KBDeH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-0.6, 1.3, 39.3), 450, 50, -38, 50),
        "close": ((-0.6, 1.3, 39.3), 266, 24, -30, 45),
        "ingame": ((-0.6, 1.3, 39.3), 1024, 53, -62, 50),
    }

    def design(self, kit):
        return []
