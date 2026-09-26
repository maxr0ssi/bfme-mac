"""Dwarven castle-wall segment (DwarvenCastleWallSegment, model DBWallRamp2): the old castle wall
map makers placed on Erebor, Withered Heath, Fornost and Helm's Deep, in the new Dwarven walls'
profile (wall_segment): a battered plinth, stepped corbels under a rune band with Erebor-blue
enamel, a bronze-banded coping and the fortress's chevron parapet on both faces, a statue
pilaster and two banners on each face, and a Dwarven stair (treads between sloping side walls,
gilded newels) down each of EA's two end ramps.

EA's model is an unfinished stand-in (one mesh GBWALLRAMP2, 106 triangles, painted from a 256
placeholder sheet that reads "Dwarven Wall"): a core block x +-23.77, y +-20.91 from z -47.61
(it stands on any slope) to the walkway at z 51.91, a 4.33 overhang on both faces (z 44.69 ->
51.91) under solid parapets (x 23.77..28.1, to z 63.92), and a ramp from the walkway down to the
ground at each end (y 20.91 -> 62.93, x +-21.66). Its faces are removed and every volume rebuilt
on the faction atlas (wall.clear_target): same footprint (x +-28.1, y +-62.93), same ends, same
walkway; the parapet's top is 63.6 (the new walls' chevron points) against EA's 63.92.

All numbers are GBWALLRAMP2 mesh coordinates (its pivot is the identity)."""
from sagekit.building import Building

from ..style import DwarvenStyle

HALF = 20.91                      # the core's half length; the ramps run on to RAMP_END
RAMP_END = 62.93
RAMP_HALF = 19.46                 # stair treads |x| <= 19.46, side walls to EA's ramp edge 21.66
STEPS = 18
PITCH = 2 * HALF / 5              # chevron slab width (5 per face); corbels under slab centres
CORBELS = tuple(PITCH * (i - 2) for i in range(5))
BANNERS = ((-12.55, 38.2, 4.4, 17.0), (12.55, 38.2, 4.4, 17.0))


class OldWallSegment(Building):
    style = DwarvenStyle()
    source = "DBWallRamp2"
    target = "GBWALLRAMP2"
    sheet = "DBWall.tga"                                # EA's placeholder; no face samples it (see wall.py)
    sheet_normal = None                                 # DBWall has no normal map
    own_textures = {"DBWall.tga": "DBWalS.tga"}         # the three old walls share DBWall: S, R, G
    tri_budget = 6000
    views = {
        "rts": ((0, 0, 20), 300, 48, -30, 50),
        "close": ((0, -10, 30), 170, 20, -24, 45),
        "ingame": ((0, 0, 20), 620, 53, -62, 50),
    }

    def design(self, kit):
        from .wall import WALK, clear_target, run, stair
        clear_target(self.target)
        s = run(kit, -HALF, HALF, WALK, corbels=CORBELS, banners=BANNERS, relief=0.0)
        s += stair(HALF, RAMP_END, WALK, RAMP_HALF, STEPS)
        s += stair(-HALF, -RAMP_END, WALK, RAMP_HALF, STEPS)
        return s

    def emphasis(self, c, n):
        if c.z < -2:
            return 0.15                       # below the ground on level terrain
        if c.z > 50:
            return 1.4                        # coping and parapet: what the RTS camera sees
        return 1.0
