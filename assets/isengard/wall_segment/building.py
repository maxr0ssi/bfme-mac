"""Isengard wall segment (IsengardCastleWallSegment; model IBWallN): EA's curtain kept whole - the
battered face, the knife fins, the corbelled parapet, the gabled ridge with its three pyramids and
the fork plates at the ends - and given the wall profile every Isengard wall piece shares
(assets/isengard/shapes_walls.py):

- on each face: two short knife fins between EA's (layered faces), EA's middle fin carried up to
  the lip as a buttress blade, four pointed ember slits low in the bays;
- a silver edge along both lips and the ridge, eight iron spikes leaning out of each lip;
- lozenge needles out of EA's pyramids: the middle one to z 66, the others to 57.5, over the
  forks (59.2) at the ends: the crest reads fork, needle, NEEDLE, needle, fork down a long wall;
- silver on the fork horns' outer edges.

No fire and no banners: segments repeat many times along a wall (the gate and the towers carry
them). The segment tiles (EA's IBWALLN, identity bone: mesh coordinates are model coordinates;
x +-8.32, y +-19, z 0..59.24): its ends meet the next segment, a hub, the gate or a wall end and
the engine may stretch it along y, so only the lip and ridge runs reach the ends and everything
stays inside EA's footprint. Both faces alike (either may face the enemy).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class WallSegment(Building):
    style = IsengardStyle()
    source = "IBWallN"
    target = "IBWALLN"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresC.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallSegment"
    house_tags = ()                 # no banners: segments repeat many times along a wall
    views = {
        "rts": ((0.0, 0.0, 29.6), 159, 50, -38, 50),
        "close": ((0.0, 0.0, 29.6), 94, 24, -30, 45),
        "ingame": ((0.0, 0.0, 29.6), 362, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_walls import run
        return run(kit, 0.0)

    def emphasis(self, c, n):
        if c.z > 36:
            return 1.35                       # the crest: what the RTS camera sees
        return 1.0
