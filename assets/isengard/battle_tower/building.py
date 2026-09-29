"""Isengard battle tower (IsengardBattleTower): EA's tower kept whole; corner fins, iron bands, the
White Hand, arrow slits, eaves spikes, braziers on the archers' deck (tower.py).

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


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in the target's
# coordinates, collected from the design (kit.flames / kit.fire record them when the kit has a
# `fire_log` list); run again after moving a fire.
FIRE_POINTS = [
    (16.0, -6.6, 101.8, 'brazier'), (16.0, 6.6, 101.8, 'brazier')
]


class BattleTower(Building):
    style = IsengardStyle()
    fire_points = FIRE_POINTS
    source = "IBBtlTwr"
    target = "TOWER"
    sheet = "IBBtlTwr.tga"
    sheet_normal = "IBBtlTwr_NRM.tga"
    own_textures = {"IBBtlTwr.tga": "IBBtlTwH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((8.1, 0.2, 63.8), 292, 50, -38, 50),
        "close": ((8.1, 0.2, 85.0), 120, 24, -30, 45),
        "foot": ((8.1, 0.2, 30.0), 110, 24, -30, 45),
        "ingame": ((8.1, 0.2, 63.8), 664, 53, -62, 50),
    }

    def design(self, kit):
        from . import tower
        return tower.build(kit)
