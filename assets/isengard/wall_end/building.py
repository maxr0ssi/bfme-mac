"""Isengard wall end (IsengardWallCliffCap; model IBWallNE): the piece a wall run ends in where it
meets a cliff. EA's IBWALLN here is two wall segments end to end (y -19..57, the fork plates at
-19, 19 and 57), their faces carried on below the ground (to z -46.17 under the first, rising to
the ground at the cut end y 57 under the second) for the falling ground at the cliff's foot.

EA's body is kept whole. Both segments take the walls' shared profile (shapes_walls.run), so the
joint with the next segment is exact: short knife fins (run on down the cliff face), buttress
blades to the lip, ember slits, the silver lip and ridge, lip spikes, needles out of the pyramids,
silver fork edges. At the cut end a blade tower stands on the parapet (its flared foot at z 39.5,
buried in the roof) to a needle at z 80: a lozenge along the wall, three layered fins a face, silver edges front and
back, ember slits, a collar - the end of the wall seen from the field. The crest's spikes and
needles stop short of it (EA's third pyramid, y 50.67, is inside it).

No fire and no banners: the gate and the towers carry them. IBWALLN hangs under a bone turned
180 degrees about z (model = (-x, -y, z) of the mesh); the design is in mesh coordinates. Height:
EA's -46.17..59.24 (105.4) may grow to 126.5; the tower's needle reaches 80 (+19.7 %).
"""
from sagekit.building import Building

from ..style import IsengardStyle

SEAM, END = 19.0, 57.0
TOWER = ((0.0, 49.2), 90.0, 6.0, 4.4, 39.5, 80.0)     # centre, axis, half length, half width, z0, z1
FLARE = 1.15
CREST_STOP = 42.5                                     # spikes, needles and the ridge line end here


def cliff_foot(y):
    """Where EA's faces end below the ground: z -46.17 under the first segment, rising to 0 at the
    cut end under the second (measured: -23.03 at y 38, -1.96 at 55.34)."""
    return -46.17 if y <= SEAM else -46.17 * (END - y) / (END - SEAM)


class WallEnd(Building):
    style = IsengardStyle()
    source = "IBWallNE"
    target = "IBWALLN"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresF.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallEnd"
    house_tags = ()                 # no banners on the wall pieces but the gate and the towers
    views = {                                                # model space: the cut end at y = -57
        "rts": ((-0.0, -19.0, 6.5), 288, 50, -38, 50),
        "close": ((-0.0, -19.0, 6.5), 170, 24, -30, 45),
        "end": ((0.0, -40.0, 45.0), 130, 24, -30, 45),
        "ingame": ((-0.0, -19.0, 6.5), 655, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_walls import run
        out = run(kit, 0.0, foot=cliff_foot) + run(kit, 2 * SEAM, foot=cliff_foot, stop=CREST_STOP)
        c, axis, L, W, z0, z1 = TOWER
        out += kit.blade_tower(c, axis, L, W, z0, z1, flare=FLARE, fins=3, spurs=False, slits=(0.42, 0.56),
                               collar=0.5, slit_w=0.9)
        return out

    def emphasis(self, c, n):
        if c.z > 36:
            return 1.35                       # crest and tower: what the RTS camera sees
        return 1.0
