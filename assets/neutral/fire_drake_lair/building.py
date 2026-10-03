"""Neutral fire drake lair (FireDrakeLair, FireDrakeLairRealShadowInFog, UAFireDrakeLair): stub from
`sagekit new neutral`.

EA's NBDrakeLair (objects FireDrakeLair, FireDrakeLairRealShadowInFog, UAFireDrakeLair; role
other): body WDCAVE_NEW, 692 triangles, painted from WBStone.tga + WBStone_NRM.tga (DXT1).
In WDCAVE_NEW mesh coordinates: x -47.40..60.11, y -59.69..41.11, z -0.82..70.47.
Other meshes (EA's, untouched): WDCAVE_LAVA01 137 (S3_Lava.tga); FXBONE02 12.
Lifecycle models in its Draw module: NBDrakeLair_A, NBDrakeLair_D1, NBDrakeLair_D2,
NBDrakeLair_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
Its sheet is drawn by elves, goblins, mordor too: our own texture is pinned in own_textures.
EA's body measured: `python3 -m sagekit measure neutral/fire_drake_lair` -> work/measure.json.

No Dwarven recipe plays this role.

Its bone is turned 90 degrees about z: world_space, every number in world axes.

The palette clash fixed: EA paints the healthy lair from WBStone, a sheet the Goblins, Elves and
Mordor draw too (the Goblins' sheets step left it EA's) and its damaged states from WBStone_D1,
which only Goblin models draw (recoloured). Ours paints the healthy body from its own WBStonX and
every state from variants of it (own_variant_name), so the lair matches itself in every state.

Ours: the drake's hoard spilling out of its lair's mouth, a heap of gold with a chest, a sword driven in
and a shield, and scorched bones and skulls of those who came for it.
"""
from sagekit.building import Building

from ..style import NeutralStyle


class FireDrakeLair(Building):
    style = NeutralStyle()
    source = "NBDrakeLair"
    target = "WDCAVE_NEW"
    sheet = "WBStone.tga"
    sheet_normal = "WBStone_NRM.tga"
    own_textures = {"WBStone.tga": "WBStonX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    world_space = True
    house_tags = ()                     # a creep lair: nobody's colour
    facet_islands = True                # every face its own island: the rock's smooth shells unwrap onto themselves
    views = {
        "rts": ((9.3, 6.4, 34.8), 360, 50, -38, 50),
        "close": ((9.3, 6.4, 34.8), 213, 24, -30, 45),
        "ingame": ((9.3, 6.4, 34.8), 819, 53, -62, 50),
    }

    def design(self, kit):
        from ..dress import retag_base
        from ..lairs import _kit, hoard
        k = _kit()
        out = hoard((34.0, -30.0, 0.0), 9.0, 7.0, facing=(1, -0.4, 0))      # at the lair's mouth: the hollow is EA's lava
        out += retag_base(k.skull_pile(kit.V((-8.0, 4.0, 30.0)), 3.0, 4, 1.8), "x")
        out += retag_base(k.ribcage(kit.V((20.0, -24.0, 3.8)), kit.V((0.6, -0.8, 0)), 6.0, pairs=3), "x")
        return out
