"""Elven floodgate (ElvenFloodgateExpansion, model EBFFGate): the Bruinen's flood-tower on the
fortress's pad - three rearing stone horses on a water basin, pouring the flood from their mouths,
over a drum of pointed bays whose niches the flood doors (elves/floodgate_doors) close.

EA's body (EBFFGATE1, 1645 triangles), in its mesh coordinates: the drum (centre about (2, 0)) of
pointed bays between buttress piers whose fronts (2.45 wide) run from the ground to 38.81, a
faceted crown over them (to 46.22) and the basin's rim on top, its outer edge at 49.1 (the
14-sided RIM below); the horses on a round plinth in the basin (heads at 80.4). The arm reaches
back to the fortress as an aqueduct: walls at |y| 6.03 up to 52.1 carrying the water, a block at
the fortress end (to 55.31) and the expansions' arch (axis x -29.31; floodgate/pad.py). The water
(EBFFGATE3/5/6: the streams, the basin, the splash) and the ground ring (EBFFGATE4) are EA's and
untouched; the streams fall within 17.6 of the drum's axis, inside the rim.

The redesign: a moulded silver coping round the rim with a crown of lancet merlons, the same
coping along the aqueduct's walls, the pointed silver frame round the arch, and a leaf banner in
the player's colour down every buttress pier - so the horses rise from an Elven crown and the
drum carries the house's colours all round. The horses, the water and the bays stay EA's."""
import math

from sagekit.building import Building

from . import pad
from ..style import ElvenStyle

CENTRE = (2.0, 0.0)
# the rim's outer edge at z 49.1, from the aqueduct's -y wall round the front to its +y wall
_HALF = [(-16.76, -6.03), (-13.92, -11.43), (-9.66, -15.8), (-4.2, -18.5), (1.81, -19.53), (7.83, -18.5),
         (13.29, -15.8), (17.55, -11.43), (20.39, -6.03)]
RIM = _HALF + [(21.27, 0.0)] + [(x, -y) for x, y in reversed(_HALF)]
COPING_Z = 49.5                    # our coping's top: 0.4 over the rim, nosed 0.8 out over the crown
MERLON = dict(h=4.0, w=1.8, gap=1.5, d0=-1.3, d1=0.3)
# the buttress piers' fronts (ground to 38.81), each chord listed going round (-y side, then +y)
_PIERS = [((20.33, -10.83), (21.47, -8.66)), ((3.99, -21.37), (6.39, -20.96)), ((-14.21, -14.27), (-12.5, -16.02))]
PIERS = _PIERS + [((a[0], -a[1]), (b[0], -b[1])) for a, b in _PIERS]
BANNER = (38.4, 2.6, 17.5, 0.02)   # z_top (under the crown: the cloth lies on the pier), width, length, d
ARM_FACES = [(-6.03, -1), (6.03, 1)]
ARCH_X = -29.31
ARM_COPING = (-39.35, -16.76, 52.6)    # from the fortress end block to the drum; the walls' top is 52.1


class Floodgate(Building):
    style = ElvenStyle()
    source = "EBFFGate"
    target = "EBFFGATE1"
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresF.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_Draw",)
    HOUSE_DRAW = "ModuleTag_Draw_HCFloodgate"
    # the piers' fronts are the footprint's edge (y +-21.37, x 21.55 at the crown): the banners' gilt
    # rods, hung 38.4-39 up, stand up to 0.85 past it; nothing new reaches past it at the ground
    footprint_margin = 0.9
    facet_islands = True            # the horses: every EA face its own UV island (the angle-based unwrap folded them)
    views = {
        "rts": ((-14.0, 0.0, 40.2), 254, 50, -38, 50),
        "close": ((-14.0, 0.0, 40.2), 150, 24, -30, 45),
        "ingame": ((-14.0, 0.0, 40.2), 578, 53, -62, 50),
    }

    def design(self, kit):
        solids = pad.coping_sweep(RIM, COPING_Z, 0.8, -1.6, CENTRE)
        for a, t, n, L in self.segments(RIM):
            solids += kit.lancet_parapet(a, t, n, L, COPING_Z, **MERLON)
        solids += self.banners(kit)
        solids += pad.arch(kit, ARCH_X, ARM_FACES)
        x0, x1, z = ARM_COPING
        solids += pad.coping(kit, x0, x1, ARM_FACES, z)
        return solids

    @staticmethod
    def segments(path):
        """(a, t, n, length) of each side of a path going round counter-clockwise: n outward."""
        from mathutils import Vector as V
        out = []
        for p, q in zip(path, path[1:]):
            a, b = V((p[0], p[1], 0)), V((q[0], q[1], 0))
            t = (b - a).normalized()
            out.append((a, t, V((t.y, -t.x, 0)), (b - a).length))
        return out

    @staticmethod
    def banners(kit):
        """A leaf banner hung from the crown down each pier's front, lying on it."""
        from mathutils import Vector as V
        z_top, width, length, d = BANNER
        out = []
        for p, q in PIERS:
            m = V(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, 0))
            n = V((q[1] - p[1], -(q[0] - p[0]), 0)).normalized()
            if n.dot(m - V((CENTRE[0], CENTRE[1], 0))) < 0:
                n = -n
            t = V((-n.y, n.x, 0))
            # the kit's banner less its two leaf-bud rod ends (the last two solids): on the piers they
            # would reach 1.3 past the footprint
            out += kit.leaf_banner(m, t, n, 0.0, z_top, width, length, d=d)[:-2]
        return out

    def emphasis(self, c, n):
        if c.z > 47 and math.hypot(c.x - CENTRE[0], c.y - CENTRE[1]) > 18:
            return 1.3                        # the crown of merlons: what the RTS camera sees
        return 1.0
