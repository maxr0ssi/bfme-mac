"""Isengard battle tower (IsengardBattleTower): stub from `sagekit new isengard`.

EA's IBBtlTwr (objects IsengardBattleTower; role tower): body TOWER, 541 triangles, painted from
IBBtlTwr.tga + IBBtlTwr_NRM.tga (DXT1).
In TOWER mesh coordinates: x -9.52..25.66, y -14.84..15.19, z 1.53..126.12.
Other meshes (EA's, untouched): GARRISON02 40 (FlagPole.tga); GARRISON01 22 (EXGARFLAG.tga); DOOR
12 (IBBtlTwr.tga, IBBtlTwr_NRM.tga).
Lifecycle models in its Draw module: IBBtlTwr_A, IBBtlTwr_D1, IBBtlTwr_D2.
House colour: IBHCBtlTwr.
EA's body measured: `python3 -m sagekit measure isengard/battle_tower` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/sentry_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class BattleTower(Building):
    style = IsengardStyle()
    source = "IBBtlTwr"
    target = "TOWER"
    sheet = "IBBtlTwr.tga"
    sheet_normal = "IBBtlTwr_NRM.tga"
    own_textures = {"IBBtlTwr.tga": "IBBtlTwH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((8.1, 0.2, 63.8), 292, 50, -38, 50),
        "close": ((8.1, 0.2, 63.8), 173, 24, -30, 45),
        "ingame": ((8.1, 0.2, 63.8), 664, 53, -62, 50),
    }

    def design(self, kit):
        return []
