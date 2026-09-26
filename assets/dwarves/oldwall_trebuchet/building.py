"""Dwarven castle-wall trebuchet platform (DwarvenCastleWallCatapult): the old castle wall's
catapult upgrade as a Dwarven bastion. EA's object draws Gondor's placeholder GBWallTreb, which Men
and Arnor draw too, so ours ships as a model of its own, DBWallTreb2 (sagekit/owncopy.py; EA's
unused DBWallTreb is filed in BFME2's asset cache with another layout, so that name is not free).

The piece is the old castle wall's section (oldwall_segment/upgrade.py) along |y| <= 99.5 with a
Dwarven stair down EA's ramp at each end, and in the middle a bastion across the wall in the same
profile: battered plinth, three-step corbels, the rune band with Erebor-blue enamel, the bronze drip
band and coping 4.33 out of its faces (x +-38.02 .. +-42.35, EA's middle block), chevrons on its rim
and returns, a stepped pyramid with a gilded point on each outer corner, two banners on each front.
Its top is an open platform at EA's walkway height (53.59) for the catapult the object creates at
(0, 0, 52) (OCL_DwarvenCatapultUpgrade): nothing new stands on x +-38, y +-24.

EA's GBWALLUPGRD (the section with the middle block) is taken over by our target GBWALLGATE (EA's
core and ramps) and dropped from our copy; P1, R1, R2 (wall-bounds and ramp cards) stay EA's.
All numbers are model coordinates (GBWALLGATE's bone is the identity)."""
from sagekit.building import Building

from ..style import DwarvenStyle

HY = 24.0                         # the bastion's half length along the wall (EA's parapet gap: -25.2 .. 26.6)


class OldWallTrebuchet(Building):
    style = DwarvenStyle()
    source = "GBWallTreb"
    own_model = "DBWallTreb2"
    replaces = ("GBWALLUPGRD",)
    target = "GBWALLGATE"
    sheet = "GBWall.tga"                                # Gondor's placeholder; no face samples it
    sheet_normal = None
    own_textures = {"GBWall.tga": "DBWalC.tga"}
    bake_hidden = ("P1", "R1", "R2")                    # EA's hidden cards: not drawn by the game
    tri_budget = 12000
    views = {
        "rts": ((0, 0, 35), 480, 50, -38, 50),
        "close": ((0, 0, 45), 230, 22, -28, 45),
        "ingame": ((0, 0, 35), 950, 53, -62, 50),
    }

    def design(self, kit):
        from ..oldwall_segment.upgrade import bastion, flanks
        from ..oldwall_segment.wall import clear_target
        clear_target(self.target)
        return bastion(kit, HY) + flanks(kit, HY)

    def emphasis(self, c, n):
        if c.z < -2:
            return 0.15
        return 1.4 if c.z > 50 else 1.0
