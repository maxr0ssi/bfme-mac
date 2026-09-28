"""Men arrow tower b (MenArrowTowerExpansion, build variation two; model GBFARTOWB, shipped as our
own GBFARTOWB2: Blue Mountains' tower draws GBFARTOWB too): EA's tall tower, the wall walk out of
its -X side and the little stair-house on the walk kept whole. The tower is crowned as variation
one (men/arrow_tower/spire.py): the machicolated gallery with its band of silver stars and
merlons, here all the way round (the wall leaves the -X side free), four corbelled bartizans,
pilasters up the belfry's chamfers, the steel-ribbed dome, lantern, orb and spike, a moulded
plinth and the one house-colour banner. On the wall: stepped buttresses down both faces, a black
band with silver stars and square merlons on both parapets; on the stair-house (as the trebuchet
tower's, men/trebuchet/drum.py): an archivolt with quoins, imposts and a keystone crest round its
door, corner pinnacles and White Tree shields.

EA's facts: body GBFARTOWB (368 triangles) on GBFortress1 (own copy GBFortressR); lifecycle
GBFARTOWB_A, _D2, _D3 (variation two: GBFARTOWA is men/arrow_tower's); no house model of EA's
(HOUSE_DRAW); no night meshes. The wall (mesh coordinates): x -34.7..-8.22 (then widening into the
tower), faces |y| 10.7 to 44; parapets from the walk (48, |y| <= 9.12) to 56, their faces 11.46 out
at 50 and 11.04 at 56; the stair-house x -25.11..-17.09, y -7.24..7.4, its door |y| <= 5.4.
"""
from sagekit.building import Building

from ..style import MenStyle


class ArrowTowerB(Building):
    style = MenStyle()
    source = "GBFARTOWB"
    target = "GBFARTOWB"
    own_model = "GBFARTOWB2"            # dwarves draws GBFARTOWB too (sagekit/ownership.py)
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressR.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCArrowTowerB"
    views = {
        "rts": ((1.6, 0.0, 61.5), 325, 50, -38, 50),
        "close": ((1.6, 0.0, 64.0), 240, 24, -30, 45),
        "ingame": ((1.6, 0.0, 61.5), 738, 53, -62, 50),
    }

    def design(self, kit):
        from ..garrison_tower import pad
        from ..trebuchet import drum
        from . import wall
        from ..arrow_tower import spire
        out = spire.build(kit, spire.B)
        out += pad.banner(kit, 0.0, -1, 0.0, shaft=spire.B.shaft, z_top=67.8, width=6.4, length=26.0)
        out += wall.build(kit)
        return out + drum.stair_house(kit, -17.09, -25.11, (-7.24, 7.4), 7.3, 5.4, 48.0, shield=(2.3, 7.2, 55.0))

    def decals(self):
        from ..paint import men_layers
        from ..arrow_tower.spire import B
        from .wall import BAND
        star = men_layers()[2]
        return [star(zrange=B.gallery[1:3], pitch=3.2, r=0.9), star(zrange=BAND, pitch=3.2, r=0.9)]

    def emphasis(self, c, n):
        if c.z > 47:
            return 1.35                       # the walk, the stair-house and the tower's crown
        return 1.0
