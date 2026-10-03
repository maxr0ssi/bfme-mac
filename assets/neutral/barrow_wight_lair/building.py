"""Neutral barrow wight lair (BarrowWightLair, BarrowWightLairRealShadowInFog, UABarrowWightLair):
stub from `sagekit new neutral`.

EA's NBWightLair (objects BarrowWightLair, BarrowWightLairRealShadowInFog, UABarrowWightLair;
role other): body NBARROWCREEP_DO, 930 triangles, painted from NBWightLairS2.tga +
NBWightLairS2_NRM.tga (DXT5).
In NBARROWCREEP_DO mesh coordinates: x -41.55..42.59, y -40.33..53.93, z -0.08..53.67.
Other meshes (EA's, untouched): NBARROWCREEP 385 (NBWightLairS.tga, NBWightLairS_NRM.tga).
Lifecycle models in its Draw module: NBWightLair_A, NBWightLair_D1, NBWightLair_D2,
NBWightLair_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure neutral/barrow_wight_lair` -> work/measure.json.

No Dwarven recipe plays this role.

Ours: great standing stones flanking the barrow's door and guarding its south side (the mound fills
the rest of the footprint), the grave goods spilled before the door, gold and bone, and a skull pile
at the threshold.
"""
from sagekit.building import Building

from ..style import NeutralStyle


class BarrowWightLair(Building):
    style = NeutralStyle()
    source = "NBWightLair"
    target = "NBARROWCREEP_DO"
    sheet = "NBWightLairS2.tga"
    sheet_normal = "NBWightLairS2_NRM.tga"
    own_textures = {"NBWightLairS2.tga": "NBWightLairSH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    house_tags = ()                     # a creep lair: nobody's colour
    facet_islands = True                # every face its own island: the rock's smooth shells unwrap onto themselves
    views = {
        "rts": ((0.5, 6.8, 26.8), 302, 50, -38, 50),
        "close": ((0.5, 6.8, 26.8), 178, 24, -30, 45),
        "ingame": ((0.5, 6.8, 26.8), 687, 53, -62, 50),
    }

    def design(self, kit):
        from ..dress import retag_base
        from ..lairs import _kit, hoard, menhir
        out = []
        for i, (x, y, h) in enumerate(((39.0, -14.0, 23.0), (39.0, 34.0, 24.0), (22.0, -33.0, 17.0), (5.0, -35.0, 14.0))):
            out += menhir((x, y, 0.0), h, 6.0, lean=(0.02 * (i % 2), 0.0), seed=i)
        out += hoard((33.0, 7.0, 0.0), 6.0, 3.6, facing=(1, 0, 0))
        out += retag_base(_kit().skull_pile(kit.V((28.0, -6.0, 0.9)), 3.2, 5, 1.7), "x")
        return out
