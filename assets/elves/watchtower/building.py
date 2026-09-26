"""Elven watchtower (ElvenWatchtowerExpansion, model EBFWTower): the tallest of the fortress's pad
buildings, a slender lantern tower on a square base.

EA's body (EBFWTOWER, 476 triangles), in its mesh coordinates, round the axis (-5.8, 0): a square
base (x -18.2..6.46, |y| 12.2, to 45.75) with a pointed door recess on each flank (x -11.98..0.25,
jambs to 33.93, point 41.5) and a carved relief on the +x front; a knotwork cornice flaring out
to 52.31 (half 13.54) and sloping in to the shaft (57.82); the shaft tapering from half 9.88 to
5.72 (101.5); the lantern head from 104.75 (four dormer bays, 4.2 wide, standing 2.7 out: their
ledges are the head's underside) to its gabled scale roof, whose four ridges sweep up into horns
(137.1) round a steep square pyramid (corners on the axes, 11.9 out at 134.2) ending at 151.88.
The eight ARROW bones fire from the dormers at 121.76: nothing new is near them. The arm reaches
back to the fortress over the expansions' arch (axis x -30.02; floodgate/pad.py).

The redesign: the pyramid runs on into a needle spire with swan-neck eaves (the horns' own sweep)
and a gilt leaf finial; a leaf banner in the player's colour hangs under each dormer down the
shaft; crystal lanterns on the cornice's corners; pointed silver frames round the flank doors
and the arm's arch. EA's head, roof and knotwork stay as they are."""
from sagekit.building import Building

from ..floodgate import pad
from ..style import ElvenStyle

AXIS = (-5.8, 0.0)
# the needle: from where the pyramid is 4.0 out at its corners (z 146), eaves a little wider
SPIRE = dict(r=4.8, z=146.0, h=23.0, k=4, per_side=3, upturn=0.9, lip=0.35, sweep_pow=1.5)
# banners under the dormers: the plane 7.2 out of the axis (the shaft is 5.72..6.7 out over the
# banner's length), rod just under the ledge (104.75)
BANNER = (7.2, 104.2, 3.6, 24.0)       # d from the axis, z_top, width, length
# the cornice's corners at 52.31; each lantern stands on a plinth 0.9 in from the corner
CORNERS = [(7.71, -13.54), (7.71, 13.54), (-19.36, 13.54), (-19.36, -13.54)]
DOOR = dict(half=6.12, z0=0.0, spring=33.93, apex=41.5)
DOOR_X = -5.87
FLANKS = [(-12.25, -1), (12.22, 1)]     # the base's flank faces (y, side)
ARM_FACES = [(-4.58, -1), (4.58, 1)]
ARCH_X = -30.02


class Watchtower(Building):
    style = ElvenStyle()
    source = "EBFWTower"
    target = "EBFWTOWER"
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresP.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWatchtower"
    views = {
        "rts": ((-14.9, 0.0, 80.0), 380, 50, -38, 50),
        "close": ((-8.0, 0.0, 95.0), 230, 24, -30, 45),
        "ingame": ((-14.9, 0.0, 80.0), 829, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V
        cx, cy = AXIS
        solids = kit.swept_roof(cx, cy, **SPIRE)
        # its soffit (the flat birch cap) lies inside EA's pyramid, out of sight: buried
        next(p for p in solids[0].polys if p[1] == "birch" and max(q.z for q in p[0]) - min(q.z for q in p[0]) < 1e-6)[2] = False
        d, z_top, width, length = BANNER
        for n in (V((1, 0, 0)), V((0, -1, 0)), V((-1, 0, 0)), V((0, 1, 0))):
            t = V((-n.y, n.x, 0))
            a = V((cx + n.x * d, cy + n.y * d, 0))
            solids += kit.leaf_banner(a, t, n, 0.0, z_top, width, length, d=0.0, free=True)
        for x, y in CORNERS:
            solids += self._corner_lantern(kit, x - 0.9 * (1 if x > cx else -1), y - 0.9 * (1 if y > 0 else -1))
        for y, side in FLANKS:
            a, t, n = pad.face(y, side)
            solids += kit.arch(a, t, n, -side * DOOR_X, w=0.9, d0=0.0, d1=0.7, ogee=pad.OGEE, **DOOR)
        solids += pad.arch(kit, ARCH_X, ARM_FACES)
        return solids

    @staticmethod
    def _corner_lantern(kit, x, y):
        """A crystal lantern on a small square plinth at a corner of the cornice."""
        from sagekit.blender.geometry import box_rings, loft
        out = [loft([box_rings((x - 0.9, x + 0.9), (y - 0.9, y + 0.9), 52.0, 0.2),
                     box_rings((x - 0.9, x + 0.9), (y - 0.9, y + 0.9), 54.6, 0.2),
                     box_rings((x - 1.1, x + 1.1), (y - 1.1, y + 1.1), 54.9, 0.25),
                     box_rings((x - 1.1, x + 1.1), (y - 1.1, y + 1.1), 55.3, 0.25)],
                    ["stoneA", "coping", "trim"], cap0=("stoneB", False), cap1=("top", True))]
        out += kit.crystal_lantern(x, y, 55.3, h=7.6, r=1.45)
        return out

    def emphasis(self, c, n):
        if c.z > 140:
            return 1.4                        # the spire
        if 78 < c.z < 105:
            return 1.2                        # the banners
        return 1.0
