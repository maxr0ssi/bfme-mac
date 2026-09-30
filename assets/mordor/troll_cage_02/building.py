"""Mordor troll cage 02 (MordorTrollCage): stub from `sagekit new mordor`.

EA's MBTrollPit_DSCL (objects MordorTrollCage; role stable): body DOOR, 106 triangles, painted
from MBTrollPit.tga + MBTrollPit_NRM.tga (DXT1).
In model (world_space) coordinates: x 16.21..51.43, y -18.94..-15.81, z 6.76..47.32.
Its bone is tilted 90 degrees from upright: world_space, every number in world axes.
Lifecycle models in its Draw module: MBTrollPit_DCL, MBTrollPit_DOP, MBTrollPit_DSOP,
MBTrollPit_DrA.
House colour: MBHCTrollPit.
EA's body measured: `python3 -m sagekit measure mordor/troll_cage_02` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class TrollCage02(Building):
    style = MordorStyle()
    source = "MBTrollPit_DSCL"
    target = "DOOR"
    sheet = "MBTrollPit.tga"
    sheet_normal = "MBTrollPit_NRM.tga"
    own_textures = {"MBTrollPit.tga": "MBTrollPiX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_02",)
    world_space = True                  # its bone is tilted 90 degrees
    views = {
        "rts": ((33.8, -17.4, 27.0), 118, 50, -38, 50),
        "close": ((33.8, -17.4, 27.0), 70, 24, -30, 45),
        "ingame": ((33.8, -17.4, 27.0), 269, 53, -62, 50),
    }

    def design(self, kit):
        return []
