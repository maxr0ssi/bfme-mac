"""Elven wall segment (ElvenCastleWallSegment, model EBWallN): EA's slender lancet wall kept whole -
its two lancet windows a face with their lattice glass, the pointed hoods with EA's gold leaf
emblems, the V cornice - and given the walls' crown: over EA's cornice a filigree band (silver
knots between gilt beads), a mithril coping (the citadel's ring coping) and a light cresting of
gold-edged leaf merlons on each face. No banners: segments repeat many times along a wall.

The segment tiles: its ends (y = +-19) meet the next segment, a hub, the gate or a wall end, and
the engine may stretch it along y. Only the crown reaches the ends (its runs continue into the
neighbour's; the merlons divide the length evenly, half a gap at each end), and everything stays
inside EA's footprint (x +-4.9, y +-19). Both faces are the same (either may face the enemy). The
shared profile and its write-up: wall.py (every Elven wall piece imports it).

EA's segment (EBWALLN, mesh coordinates = model space), per face: the wall face at |x| 3.06;
piers to |x| 4.9 for |y| <= 1.26 and >= 17.72 (chamfered back to the face at 2.67 / 16.23) up to
38.81; the lancet windows recessed to |x| 0.96 about y = +-9.73 (9.8 wide at the face, jambs to
30.81, apex 37.1); pointed hoods over them and a V cornice between (42.0 -> 4.45 at 46.22 -> the
face at 49.1); a low ridge to z 51.2."""
from sagekit.building import Building

from ..style import ElvenStyle

HALF = 19.0                        # the segment's half length (its ends meet the neighbours)


class WallSegment(Building):
    style = ElvenStyle()
    source = "EBWallN"
    target = "EBWALLN"
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresB.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallSegment"
    house_tags = ()                 # no banners: segments repeat many times along a wall
    # the placement cursor: EA's segment on the same bone and box (checked by the derive step)
    also_derived = ("EBWallN_CUR",)
    views = {
        "rts": ((0, 0, 30), 150, 48, -24, 50),
        "close": ((0, 0, 31), 112, 22, -18, 45),
        "ingame": ((0, 0, 26), 330, 53, -62, 50),
    }

    def design(self, kit):
        from .wall import straight_crown
        return straight_crown(kit, -HALF, HALF)

    def emphasis(self, c, n):
        if c.z > 48:
            return 1.4                        # the crown: what the RTS camera sees
        return 1.0
