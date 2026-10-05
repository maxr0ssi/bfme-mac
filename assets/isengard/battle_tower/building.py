"""Isengard battle tower (IsengardBattleTower): EA's tower kept whole; the citadel's pair of blades
through its roof to z 150, iron bands, the White Hand, arrow slits, eaves spikes, braziers
(tower.py).

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
    (4.0, -5.6, 101.8, 'brazier'), (4.0, 5.6, 101.8, 'brazier'), (22.2, -6.0, 43.2, 'brazier'),
    (22.2, 6.0, 43.2, 'brazier')
]


class BattleTower(Building):
    style = IsengardStyle()
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): the top's two braziers a torch flame each. 6.0 live (was 23.9).
    fire_points = [(4.0, -5.6, 101.8, 'torch'), (4.0, 5.6, 101.8, 'torch')]
    source = "IBBtlTwr"
    target = "TOWER"
    sheet = "IBBtlTwr.tga"
    sheet_normal = "IBBtlTwr_NRM.tga"
    own_textures = {"IBBtlTwr.tga": "IBBtlTwH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    # EA's really damaged tower drops a few shards, its body bent: cut and bent along it, slivers and
    # 2.9% open backs; filled on our own (unbent) faces, 2.8%, seams no RTS render shows
    lifecycle = {"IBBtlTwr_D2": {"fill": True, "bend": False,
                                 "backs": (0.03, "thin seams between the tower's plates where EA's shards part, "
                                                 "2.8% past EA's; no hole in the RTS renders")}}
    views = {
        "rts": ((8.1, 0.2, 63.8), 292, 50, -38, 50),
        "close": ((10.0, 0.0, 100.0), 175, 24, -30, 45),
        "foot": ((8.1, 0.2, 30.0), 110, 24, -30, 45),
        "ingame": ((8.1, 0.2, 63.8), 664, 53, -62, 50),
    }

    def design(self, kit):
        from . import tower
        return tower.build(kit)
