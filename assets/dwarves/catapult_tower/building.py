"""Dwarven catapult tower fortress expansion (DwarvenCatapultExpansion): the fortress walls' solid
chevron parapet (bronze-banded coping on angular corbels, stepped-triangle slabs) round the rim of
the catapult platform, and a gold rune frieze along the side walls.

The platform (floor z 50.0, x -37.8..8.6, |y| 18.7; the P1 bone and plane the catapult stands on)
is kept clear: the parapet sits on the outer 2.2 of the 3.8-thick rim. The -X wall (x -41.5, plain,
against the fortress) keeps its rim as it is. All measurements in DBFCTOWER mesh coordinates, taken
from the original model."""
from sagekit.building import Building

from ..style import DwarvenStyle

# the rim's outer edge (walls' outer faces at the top, z 53.0), open at the fortress side
RIM = [(-41.5, -22.5), (3.5, -22.5), (12.7, 0.0), (3.5, 22.5), (-41.5, 22.5)]
CENTRE = (-15.0, 0.0)
# a lower version of the fortress walls' PARAPET (d outward from the wall face, z): corbel slope,
# bronze band, top; the buried bottom edge runs through the rim
COPING = [(0, 51.0), (1.2, 52.2), (1.2, 54.4), (0.8, 54.8), (-2.2, 54.8), (-2.2, 53.0)]
COPING_TAGS = ["trim", "stoneA", "trim", "top", "stoneA", None]
CHEVRON_DZ = 54.8 - 56.6                      # the fortress chevrons, standing on this coping
FRIEZE = [(0, 38.0), (0.6, 38.6), (0.6, 42.6), (0, 43.2)]   # rune frieze on the side walls
FRIEZE_TAGS = ["trim", "rune", "trim", None]


class CatapultTower(Building):
    style = DwarvenStyle()
    source = "DBFCTower"
    target = "DBFCTOWER"
    sheet = None                                                # the faction atlas DBFortress1
    own_textures = {"DBFortress1.tga": "DBFortressC.tga"}
    bake_hidden = ("P1",)                                       # the catapult's untextured platform plane
    views = {
        "rts": ((-14, -3, 28), 260, 50, -38, 50),
        "close": ((-8, -3, 34), 185, 26, -34, 45),
        "ingame": ((-18, 0, 25), 620, 53, -62, 50),
    }

    def design(self, kit):
        from sagekit.blender.geometry import sweep
        solids, segs = sweep(RIM, COPING, COPING_TAGS, center=CENTRE)      # 1. chevron parapet
        for a, b, t, n in segs:
            L = (b - a).length
            solids += kit.chevron_parapet(a, t, n, L, dz=CHEVRON_DZ)
            k = max(1, round(L / 8.6))
            for i in range(k):
                solids.append(kit.corbel(a, t, n, (i + 0.5) * L / k))
        for sy in (-1, 1):                                                   # 2. rune frieze
            path = [(-41.5, sy * 22.5), (3.5, sy * 22.5)]
            solids += sweep(path, FRIEZE, FRIEZE_TAGS, center=CENTRE)[0]
        return solids

    def emphasis(self, c, n):
        if c.z > 50:
            return 1.4                        # the parapet: what the RTS camera sees
        return 1.0
