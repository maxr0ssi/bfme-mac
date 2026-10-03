"""Neutral spider lair (SpiderLair, SpiderLairRealShadowInFog, UASpiderLair): stub from `sagekit new
neutral`.

EA's NBSpiderL_SKN (objects SpiderLair, SpiderLairRealShadowInFog, UASpiderLair; role other):
body SPIDERLAIR, 728 triangles, painted from NBSpiderLair02.tga + NBSpiderLair02_NRM.tga (DXT5,
cut-out alpha: our texture is DXT5).
In model (world_space) coordinates: x -29.20..39.05, y -46.49..44.41, z -5.40..41.67.
Its bone is tilted 14 degrees from upright: world_space, every number in world axes.
Other meshes (EA's, untouched): SHELOB01 966 (MUGntSpdr.tga); SHELOB 966 (MUGntSpdr.tga); WEBBING
30 (NBSpiderLair02.tga).
Lifecycle models in its Draw module: NBSpiderLair_A, NBSpiderLair_D1, NBSpiderLair_D2,
NBSpiderLair_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure neutral/spider_lair` -> work/measure.json.

No Dwarven recipe plays this role.

Ours: the spider's work, two great webs strung across the lair's mouth and flank, cocooned victims
on the ground and hung in the webs, and a clutch of egg sacs.
"""
from sagekit.building import Building

from ..style import NeutralStyle


class SpiderLair(Building):
    style = NeutralStyle()
    source = "NBSpiderL_SKN"
    target = "SPIDERLAIR"
    sheet = "NBSpiderLair02.tga"
    sheet_normal = "NBSpiderLair02_NRM.tga"
    own_textures = {"NBSpiderLair02.tga": "NBSpiderLair0H.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    world_space = True                  # its bone is tilted 14 degrees
    house_tags = ()                     # a creep lair: nobody's colour
    facet_islands = 20                  # the rock's smooth shells unwrap onto themselves otherwise
    views = {
        "rts": ((4.9, -1.0, 18.1), 271, 50, -38, 50),
        "close": ((4.9, -1.0, 18.1), 160, 24, -30, 45),
        "ingame": ((4.9, -1.0, 18.1), 615, 53, -62, 50),
    }

    def design(self, kit):
        from ..lairs import cocoon, eggs, web
        out = web((0.0, -36.0, 12.0), (1, 0, 0), (0, 0.25, 1), 11.0)
        out += web((24.0, 14.0, 13.0), (0, 1, 0), (-0.3, 0, 1), 9.0, spokes=7)
        out += cocoon((-6.0, -40.0, 0.6), (1, 0.3, 0), 7.0, 1.5)
        out += cocoon((10.0, -40.0, 0.6), (-0.4, 1, 0.1), 6.0, 1.3)
        out += cocoon((3.0, -36.5, 19.0), (0.2, 0, -1), 5.5, 1.2)
        out += eggs((-20.0, -26.0, 0.0), 4.5, 7)
        return out
