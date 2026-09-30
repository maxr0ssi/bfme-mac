"""Mordor haradrim palace (MordorHaradrimPalace): stub from `sagekit new mordor`.

EA's MBHrdPlc_SKN (objects MordorHaradrimPalace; role other): body MBHRDPLC, 1106 triangles,
painted from MBHrdPlc.tga + MBHrdPlc_NRM.tga (DXT1).
In MBHRDPLC mesh coordinates: x -34.43..34.41, y -41.94..38.16, z -3.83..47.20.
Target ambiguous: V2A (426 triangles), V1 (340 triangles) could be the body too (the rule takes a
normal-mapped mesh standing on the ground, then the largest); set `target` to the mesh the design
redesigns.
Other meshes (EA's, untouched): BANNER_HARAD01 736 (Haradrim_Banr.tga); V2A 426 (MBHrdPlc.tga,
MBHrdPlc_NRM.tga); V1 340 (MBHrdPlc.tga, MBHrdPlc_NRM.tga); MUHARALNCR 308 (MUHaraLncr.tga);
BONFIRE 207 (PCampFire.tga); LANCE 152 (MUHaraLncr_Lance.tga); FIRE 8 (EXFireSeq.tga).
Lifecycle models in its Draw module: MBHrdPlc_A, MBHrdPlc_D1, MBHrdPlc_D2, MBHrdPlc_D3.
House colour: MBHCHrdPlc.
EA's body measured: `python3 -m sagekit measure mordor/haradrim_palace` -> work/measure.json.

No Dwarven recipe plays this role.
"""
from sagekit.building import Building

from ..style import MordorStyle


class HaradrimPalace(Building):
    style = MordorStyle()
    source = "MBHrdPlc_SKN"
    target = "MBHRDPLC"
    sheet = "MBHrdPlc.tga"
    sheet_normal = "MBHrdPlc_NRM.tga"
    own_textures = {"MBHrdPlc.tga": "MBHrdPlH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-0.0, -1.9, 21.7), 258, 50, -38, 50),
        "close": ((-0.0, -1.9, 21.7), 152, 24, -30, 45),
        "ingame": ((-0.0, -1.9, 21.7), 586, 53, -62, 50),
    }

    def design(self, kit):
        return []
