"""Angmar barracks (AngmarBarracks): stub from `sagekit new angmar`.

EA's KBHall (objects AngmarBarracks; role barracks): body BASE, 918 triangles, painted from
KBHall.tga + KBHall_Normal.tga (DXT5, cut-out alpha: our texture is DXT5).
In BASE mesh coordinates: x -42.75..42.75, y -56.30..48.72, z -0.00..92.69.
Target ambiguous: V2 (642 triangles), V1 (488 triangles) could be the body too (the rule takes a
normal-mapped mesh standing on the ground, then the largest); set `target` to the mesh the design
redesigns.
Other meshes (EA's, untouched): V2 642 (KBHall.tga, KBHall_Normal.tga); V1 488 (KBHall.tga,
KBHall_Normal.tga); DARKDUNEDAIN 444 (KUDarkDune.tga); N_WINDOW 16 (GBNightWIndows.tga);
DOOR_LEFT 11 (KBHall.tga, KBHall_Normal.tga); DOOR_RIGHT 11 (KBHall.tga, KBHall_Normal.tga).
Lifecycle models in its Draw module: KBHall_A, KBHall_D1, KBHall_D2, KBHall_D3.
House colour: KBHCHall.
EA's body measured: `python3 -m sagekit measure angmar/barracks` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class Barracks(Building):
    style = AngmarStyle()
    source = "KBHall"
    target = "BASE"
    sheet = "KBHall.tga"
    sheet_normal = "KBHall_Normal.tga"
    own_textures = {"KBHall.tga": "KBHalH.tga",      # free in EA's files and every recipe (sagekit/names.py)
                    "KBHall_Normal.tga": "KBHalH_Normal.tga"}    # EA named its normal map off the _NRM pattern
    views = {
        "rts": ((0.0, -3.8, 46.9), 361, 50, -38, 50),
        "close": ((0.0, -3.8, 46.9), 213, 24, -30, 45),
        "ingame": ((0.0, -3.8, 46.9), 821, 53, -62, 50),
    }

    def design(self, kit):
        return []
