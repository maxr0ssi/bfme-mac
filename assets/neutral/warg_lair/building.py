"""Neutral warg lair (DireWolfLair, WargLair, WargLairRealShadowInFog, UAWargLair): stub from
`sagekit new neutral`.

EA's NBWargLair (objects DireWolfLair, WargLair, WargLairRealShadowInFog, UAWargLair; role
other): body WARGLAIR, 985 triangles, painted from NBWargLair.tga + NBWargLair_NRM.tga (DXT1).
In WARGLAIR mesh coordinates: x -46.50..60.04, y -48.30..58.95, z -3.06..47.11.
Lifecycle models in its Draw module: NBWargLair_A, NBWargLair_D1, NBWargLair_D2, NBWargLair_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure neutral/warg_lair` -> work/measure.json.

No Dwarven recipe plays this role.

Its bone is moved (3.9, 3.5): world_space, every number in world axes.

Ours: a gnawed kill on the den's mound, a ribcage, a skull pile and bones; two warg skulls on stakes
at its foot marking the pack's ground.
"""
from sagekit.building import Building

from ..style import NeutralStyle


class WargLair(Building):
    style = NeutralStyle()
    source = "NBWargLair"
    target = "WARGLAIR"
    sheet = "NBWargLair.tga"
    sheet_normal = "NBWargLair_NRM.tga"
    own_textures = {"NBWargLair.tga": "NBWargLaiH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    world_space = True
    house_tags = ()                     # a creep lair: nobody's colour
    facet_islands = True                # every face its own island: the rock's smooth shells unwrap onto themselves
    views = {
        "rts": ((10.7, 8.8, 22.3), 350, 50, -38, 50),
        "close": ((10.7, 8.8, 22.3), 207, 24, -30, 45),
        "ingame": ((10.7, 8.8, 22.3), 796, 53, -62, 50),
    }

    def design(self, kit):
        from ..lairs import larder, trophy
        out = larder((12.0, 6.0, 20.6), (-0.7, -0.7, 0), 10.0, skulls=5)
        out += larder((-20.0, -32.0, 0.0), (0.3, -0.95, 0), 8.0, skulls=4)
        out += trophy((24.0, -38.0, 0.0), 12.0, 4.6, (0.2, -1, 0))
        out += trophy((-36.0, -14.0, 0.0), 11.0, 4.4, (-1, -0.2, 0))
        return out
