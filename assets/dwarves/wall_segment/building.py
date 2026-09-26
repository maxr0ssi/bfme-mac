"""Dwarven wall segment (DwarvenWallSegmentSmall, and the wall half of DwarvenWallPosternGateSmall:
model DBWallN). The fortress's walls on EA's segment: a bronze-banded coping and the solid chevron
parapet on both faces over the rune band, a corbel table under the band, a battered plinth along
the foot, and a narrow Erebor-blue banner in each bay beside the relief niche.

The segment tiles: its ends (y = +-19) meet the next segment, a hub or a gate end to end, and the
engine may stretch it along y. So nothing is added at the ends but runs that continue into the
neighbour (coping, chevron slabs, which divide the length evenly) and every solid stays inside
EA's footprint (x +-8.3, y +-19). The wall is symmetric in x (either face may face the enemy):
every motif is built on both faces. All measurements in DBWALLN mesh coordinates, taken from the
original model.

EA's segment (per face, s = +-1): the wall body's face at |x| 6.0 (z 0..44); the relief niche
recessed to |x| 4.0 (|y| <= 5.4, jambs splaying to |y| 6.6 at |x| 6, pointed top z 31..36.9);
a stepped half-buttress at each end (|x| 7.3 for |y| >= 10.5, |x| 8.3 for |y| >= 11.4, tops
ramping up from z 33.3 to 41 at the end); the rune band at |x| 8.0 (z 44..51.1, underside from
|x| 6 to 8 at z 44); its top slopes to the walkway, flat at z 53.0 for |x| <= 6."""
from sagekit.building import Building

from ..style import DwarvenStyle

# ---- the wall profile every Dwarven wall piece shares (write-up in README.md) ----
BAND = (44.0, 51.1)               # the rune band (EA's), face at |x| 8.0
WALK_Z = 53.0                     # walkway (EA's flat top), |x| <= 6
COPING_X = 7.0                    # coping path; d is measured out of it
# coping over the rune band: a bronze drip band 0.3 proud of the rune band, the coping face (d 1.2,
# flush with the chevron slabs' fronts), a bronze chamfer, the top at z 57 (the fortress's), the
# walkway side down to the walk; the bottom edge runs buried through the band and the walk
COPING = [(1.0, 50.4), (1.3, 50.7), (1.3, 51.9), (1.2, 52.0), (1.2, 56.6), (0.8, 57.0), (-2.2, 57.0),
          (-2.2, 52.8)]
COPING_TAGS = ["trim", "trim", "trim", "stoneA", "trim", "top", "stoneA", None]
HALF = 19.0                       # the segment's half length (its ends meet the neighbours)
# battered plinth along the wall face (d out of |x| 6): its foot flush with the buttress faces
# (|x| 8.3); its back runs to |x| 3.95, behind the niche, so it fills the niche's foot
PLINTH = [(-2.05, 0.0), (2.3, 0.0), (2.3, 0.8), (0.8, 5.8), (0.0, 6.3), (-2.05, 6.3)]
PLINTH_TAGS = [None, "stoneB", "stoneA", "top", "top", None]
PLINTH_Y = 11.4                   # to the outer buttress layer, which buries its ends
WALL_X = 6.0
# corbel table under the band's overhang (|x| 6 -> 8): wedges from z 40.6 at the wall face to the
# underside (z 44), 1.9 out; over the bays and the niche's head, clear of the buttresses (|y| 10.5)
CORBEL_U = (-8.4, -4.2, 0.0, 4.2, 8.4)
CORBEL = (40.6, 1.9, 0.75)        # z at the wall, depth, half width
# a banner in each bay between the niche jamb (|y| 6.6) and the buttress (|y| 10.5), hung under
# the corbels: (u centre, z_top, width, length)
BANNER = (8.65, 39.6, 2.6, 13.0)


class WallSegment(Building):
    style = DwarvenStyle()
    source = "DBWallN"
    target = "DBWALLN"
    sheet = None                                                # the faction atlas DBFortress1
    own_textures = {"DBFortress1.tga": "DBFortressW.tga"}       # taken: B C E F G H J K M P Q S V
    # the banner cloth goes to a house-colour model of our own (DBHCWallN), shown by a Draw module
    # added to every object drawing DBWallN - the postern gate object too, which also gets the
    # postern's own (DBHCWallPGN). The framework's shared default tag would make the second
    # add_draw a silent no-op there, so this model's module gets a tag of its own
    HOUSE_DRAW = "ModuleTag_Draw_HCWallN"
    views = {
        "rts": ((0, 0, 30), 205, 48, -24, 50),
        "close": ((0, 0, 34), 140, 20, -18, 45),
        "ingame": ((0, 0, 26), 430, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft, sweep
        solids = []
        for s in (1, -1):
            n = V((s, 0, 0))
            t = V((0, 1, 0))
            # 1. coping and chevron parapet (the fortress's), each face
            path = [(s * COPING_X, -HALF), (s * COPING_X, HALF)]
            ss, segs = sweep(path, COPING, COPING_TAGS)
            solids += ss
            a = V((s * COPING_X, -HALF, 0))
            solids += kit.chevron_parapet(a, t, n, 2 * HALF)
            # 2. battered plinth between the end buttresses
            path = [(s * WALL_X, -PLINTH_Y), (s * WALL_X, PLINTH_Y)]
            solids += sweep(path, PLINTH, PLINTH_TAGS, cap_start=False, cap_end=False)[0]
            # 3. corbel table under the rune band
            z0, dep, hw = CORBEL
            for u in CORBEL_U:
                def ring(y):
                    return [V((s * WALL_X, y, z0)), V((s * (WALL_X + dep), y, BAND[0])), V((s * WALL_X, y, BAND[0]))]
                solids.append(loft([ring(u - hw), ring(u + hw)], [["stoneB", None, None]],
                                   cap0=("stoneB", True), cap1=("stoneB", True)))
            # 4. a banner in each bay
            u, z_top, width, length = BANNER
            wall = V((s * WALL_X, 0, 0))
            for sy in (1, -1):
                solids += kit.banner(wall, t, n, sy * u, z_top, width, length, d=0.05)
        return solids

    def emphasis(self, c, n):
        if c.z > 50:
            return 1.4                        # parapet and coping: what the RTS camera sees
        return 1.0
