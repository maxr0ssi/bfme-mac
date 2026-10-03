"""Neutral cave troll lair (CaveTrollLair, CaveTrollLairRealShadowInFog, HillTrollLair,
SnowTrollLair, CaveTrollLairSnow, UACaveTrollLair, HillTrollLairSnow, SnowTrollLairSnow): stub
from `sagekit new neutral`.

EA's NBTrollLair (objects CaveTrollLair, CaveTrollLairRealShadowInFog, HillTrollLair,
SnowTrollLair, CaveTrollLairSnow, UACaveTrollLair, HillTrollLairSnow, SnowTrollLairSnow; role
other): body TROLLLAIR_00, 1148 triangles, painted from NBTrollLair.tga + NBTrollLair_NRM.tga
(DXT1).
In TROLLLAIR_00 mesh coordinates: x -51.28..52.23, y -61.60..50.51, z -4.35..65.66.
Lifecycle models in its Draw module: NBTrollLair_A, NBTrollLair_D1, NBTrollLair_D2,
NBTrollLair_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure neutral/cave_troll_lair` -> work/measure.json.

No Dwarven recipe plays this role.

Ours: the troll's larder at the lair's foot, a great ribcage with a skull pile and long bones
beside it, a troll's club studded with iron spikes leaning on the logs, and a beast skull on a stake.
"""
from sagekit.building import Building

from ..style import NeutralStyle


class CaveTrollLair(Building):
    style = NeutralStyle()
    source = "NBTrollLair"
    target = "TROLLLAIR_00"
    sheet = "NBTrollLair.tga"
    sheet_normal = "NBTrollLair_NRM.tga"
    own_textures = {"NBTrollLair.tga": "NBTrollLaiH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    house_tags = ()                     # a creep lair: nobody's colour
    facet_islands = True                # every face its own island: the rock's smooth shells unwrap onto themselves
    views = {
        "rts": ((0.5, -5.5, 30.7), 369, 50, -38, 50),
        "close": ((0.5, -5.5, 30.7), 218, 24, -30, 45),
        "ingame": ((0.5, -5.5, 30.7), 839, 53, -62, 50),
    }

    def design(self, kit):
        from ..lairs import club, larder, trophy
        out = larder((24.0, -47.0, 0.0), (-0.6, 0.8, 0), 12.0, skulls=7)
        out += club((-46.0, -44.0, 0.2), (-32.0, -31.0, 30.0), 2.2)
        out += trophy((42.0, -42.0, 0.0), 14.0, 5.0, (-0.7, -0.7, 0))
        return out
