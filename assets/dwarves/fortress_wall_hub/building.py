"""Dwarven fortress wall hub (DwarvenWallHubSmallExpansion, model DBGFWHub): the bastion the
fortress raises at a corner of its own when the wall-hub expansion is bought. EA's mesh
(DBWALLRMPRTN, 178 triangles) is the wall hub's hexagon (DBWallRmprtN, dwarves/wall_hub) with a
short wall run out of its west corner into the fortress and a rock bank along that run's foot.

The hexagon takes the wall hub's design whole (coping and chevron parapet round the rim, stepped
corner blocks, stepped crown, banners), so a fortress corner and the free-standing hubs read as
one wall. The west run takes the wall segments' coping and chevron parapet on both faces, at their
heights, and an Erebor-blue banner on each face over the rock bank.

EA's west run (mesh coordinates): faces at |y| 8.0 from x -45.03 (where it meets the fortress) to
the hexagon's west corner (-25.49, 0), up to z 50.53, a chamfer to a flat walk at z 52.21 for
|y| <= 4.92; the rock bank rises from the ground at |y| 12..16 to a ridge inside the wall (|y| 7,
z 18..28); the bank's ground line reaches x -56.52 (the footprint's west edge)."""
from sagekit.building import Building

from ..style import DwarvenStyle
from ..wall_hub.building import WallHub
from ..wall_segment.building import COPING, COPING_TAGS, COPING_X

RUN = (-45.03, -20.66)            # the west run: fortress end, and where its faces meet the hexagon's
RUN_FACE = 8.02
# the segments' coping, its inner foot dropped to bury it in the run's walk (z 52.21, 0.6 under
# the segments' walkway)
RUN_COPING = COPING[:-1] + [(COPING[-1][0], 52.0)]
PARAPET_END = -21.8               # the chevron slabs stop at the hexagon's own parapet
# a banner on each face of the run, over the rock bank's ridge (z <= 28): (x centre, z top, width, length)
RUN_BANNER = (-33.5, 42.4, 5.0, 14.0)
# the hexagon's banners on the two slanted faces beside the west corner move along the face,
# away from the run (their middle would put the cloth's edge on the run's face)
BANNER_SHIFT = {2: -2.5, 3: 2.5}


class FortressWallHub(WallHub):
    style = DwarvenStyle()
    source = "DBGFWHub"
    target = "DBWALLRMPRTN"
    sheet = None                                                # the faction atlas DBFortress1
    own_textures = {"DBFortress1.tga": "DBFortressL.tga"}       # taken: B C E F G H J K M N P Q R S V W
    HOUSE_DRAW = "ModuleTag_Draw_HCGFWHub"
    views = {
        "rts": ((-15, 0, 30), 330, 48, -24, 50),
        "close": ((-15, 0, 34), 215, 20, -18, 45),
        "west": ((-32, 0, 44), 190, 55, 205, 45),
        "ingame": ((-15, 0, 26), 660, 53, -62, 50),
    }

    def design(self, kit):
        return (self.parapet(kit) + self.corner_blocks() + self._crown() + self.banners(kit, BANNER_SHIFT)
                + self.run(kit))

    @staticmethod
    def run(kit):
        """The west run: the segments' coping and chevron parapet on both faces, a banner each."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import sweep
        x0, x1 = RUN
        centre = ((x0 + x1) / 2, 0)
        solids = []
        for s in (1, -1):
            n, t = V((0, s, 0)), V((1, 0, 0))
            solids += sweep([(x0, s * COPING_X), (x1, s * COPING_X)], RUN_COPING, COPING_TAGS, center=centre)[0]
            solids += kit.chevron_parapet(V((x0, s * COPING_X, 0)), t, n, PARAPET_END - x0)
            u, z_top, width, length = RUN_BANNER
            solids += kit.banner(V((x0, s * RUN_FACE, 0)), t, n, u - x0, z_top, width, length, d=0.05)
        return solids
