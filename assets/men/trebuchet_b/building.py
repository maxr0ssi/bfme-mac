"""Men trebuchet tower b (MenTrebuchetExpansion, build variation two; model GBFTRTOWB): EA's drum,
the platform block behind it and the little arched stair-house on the block kept whole, the
platform clear for the trebuchet (P1, EA's, untouched), and dressed as variation one
(men/trebuchet/drum.py, the same drum shifted 0.25 along x): plinth, pilasters, arrow slits,
White Tree shields, the parapet banded black with silver stars under square merlons, now all the
way round the drum and along the block, pinnacles over the prow, the drum's shoulders and the
block's end; on the stair-house, a voussoir archivolt with quoins, imposts and a keystone crest
round its door, pinnacles on its corners and White Tree shields on its sides. No banners.

EA's facts: body GBFTRTOWB (206 triangles) on GBFortress1 (own copy GBFortressT); lifecycle
GBFTRTOWB_A, _D2, _D3 (variation two: GBFTRTOWA is men/trebuchet's); no house model of EA's
(HOUSE_DRAW); no night meshes. The block: x -36.07..-10.4, |y| 13.7 at the ground, its parapet
(|y| 13..14.1) from 50 to 56; the stair-house x -26.16..-16.72, |y| <= 8.6, to 69.9 at its
corners and 74.65 at its barrel's crown; its door on the +X face, |y| <= 6.4, springing at 68.06,
crown 72.0.
"""
from sagekit.building import Building

from ..style import MenStyle


class TrebuchetB(Building):
    style = MenStyle()
    source = "GBFTRTOWB"
    target = "GBFTRTOWB"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressT.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCTrebuchetB"
    house_tags = ()                     # no banners
    lifecycle = {"GBFTRTOWB_D2": {"match": "rest", "tolerance": 3.0}}
    views = {
        "rts": ((1.3, 0.0, 37.3), 252, 50, -38, 50),
        "close": ((1.3, 0.0, 40.0), 190, 24, -30, 45),
        "ingame": ((1.3, 0.0, 37.3), 572, 53, -62, 50),
    }

    def design(self, kit):
        from ..trebuchet import drum as D
        dx = D.DX_B
        c = (D.CENTRE[0] + dx, 0.0)
        out = D.body(kit, dx, c)
        drum_top = [(1.09, -21.0)] + D.shift(D.PARAPET, dx)
        ring = [(-36.0, -14.1), (-10.41, -14.1)] + drum_top
        ring = ring + [(x, -y) for x, y in ring[::-1][1:]]
        out += D.band(ring, c)
        for sy in (-1, 1):
            half = [(-36.0, -13.7)] + D.shift(D.BODY, dx)[1:-1]
            out += D.plinth([(x, sy * -y) for x, y in half], c)
            out += D.merlons(kit, [(-36.0, sy * 14.1), (-10.41, sy * 14.1)], c, trim0=1.9, trim1=1.8)
            out += D.merlons(kit, [(-10.41, sy * 14.1)] + [(x, sy * -y) for x, y in drum_top], c, trim0=1.8, trim1=1.7)
            out += kit.pinnacle(-10.0, sy * 13.55, D.Z_TOP - 0.4, D.Z_TOP + 2.8, half=1.0, spire=4.0)
            out += kit.pinnacle(-34.7, sy * 13.55, D.Z_TOP - 0.4, D.Z_TOP + 2.8, half=1.0, spire=4.0)
        out += kit.pinnacle(36.2 + dx, 0.0, D.Z_TOP - 0.4, D.Z_TOP + 2.8, half=1.1, spire=4.2)
        return out + D.stair_house(kit, -16.72, -26.16, (-8.55, 8.69), 8.6, 6.4, 50.0)

    def decals(self):
        from ..paint import men_layers
        from ..trebuchet.drum import BAND
        return [men_layers()[2](zrange=BAND, pitch=3.2, r=0.9)]         # silver stars on the parapet's band

    def emphasis(self, c, n):
        if c.z > 44:
            return 1.35                       # the parapet and the stair-house
        return 1.0
