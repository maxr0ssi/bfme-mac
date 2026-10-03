"""Neutral moriar goblin lair (MoriarGoblinLair, MoriarGoblinLairRealShadowInFog,
MoriarGoblinLairSnow, UAMoriarGoblinLair): stub from `sagekit new neutral`.

EA's NBGoblinLair (objects MoriarGoblinLair, MoriarGoblinLairRealShadowInFog,
MoriarGoblinLairSnow, UAMoriarGoblinLair; role other): body GOBLINLAIR, 1145 triangles, painted
from NBGoblinLair.tga + NBGoblinLair_NRM.tga (DXT1).
In GOBLINLAIR mesh coordinates: x -34.43..35.51, y -38.19..38.92, z -5.77..34.78.
Lifecycle models in its Draw module: NBGoblinLair_A, NBGoblinLair_D1, NBGoblinLair_D2,
NBGoblinLair_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure neutral/moriar_goblin_lair` -> work/measure.json.

No Dwarven recipe plays this role.

Ours: a goblin war totem crowning the rock, a horned skull over a bone crossbar, and the Goblin
kit's skulls on spikes at the foot, with a heap of skulls by the burrows.
"""
from sagekit.building import Building

from ..style import NeutralStyle


class MoriarGoblinLair(Building):
    style = NeutralStyle()
    source = "NBGoblinLair"
    target = "GOBLINLAIR"
    sheet = "NBGoblinLair.tga"
    sheet_normal = "NBGoblinLair_NRM.tga"
    own_textures = {"NBGoblinLair.tga": "NBGoblinLaiH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    world_space = True
    house_tags = ()                     # a creep lair: nobody's colour
    facet_islands = True                # every face its own island: the rock's smooth shells unwrap onto themselves
    views = {
        "rts": ((0.5, 0.1, 15.0), 246, 50, -38, 50),
        "close": ((0.5, 0.1, 15.0), 145, 24, -30, 45),
        "ingame": ((0.5, 0.1, 15.0), 559, 53, -62, 50),
    }

    def design(self, kit):
        from ..dress import retag_base
        from ..lairs import _kit, trophy
        k = _kit()
        out = retag_base(k.totem(kit.V((0.0, 0.0, 32.0)), 6.5, 2.6, facing=(0.6, -0.8, 0)), "x")
        out += trophy((26.0, -26.0, 0.0), 8.0, 2.6, (0.6, -0.8, 0))
        out += trophy((-28.0, -22.0, 0.0), 7.0, 2.4, (-0.6, -0.8, 0))
        out += retag_base(k.skull_pile(kit.V((22.0, 26.0, 0.0)), 4.0, 6, 1.9), "x")
        return out
