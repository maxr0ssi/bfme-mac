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

The redesign, the citadel's recipe on the flood-tower: EA's body kept whole (the horses, the bays,
EA's gold swirls over them), and a handful of additions - a mithril coping round the rim with a
silver-railed ivory balustrade on it (a Rivendell terrace round the horses, not a castle's
merlons), a crystal lantern on a newel over each of the six buttress piers (the citadel's ring
lanterns), the same coping along the aqueduct's walls and the pointed silver frame round the arch.
Two banners, on the front piers either side of the flood. The horses, the water and the bays stay
EA's."""
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
RAIL_IN = 0.55                     # the balustrade and the newels: this far in from the rim's outer edge
RAIL_H = 2.8
NEWEL = 0.75                       # the newels' half width: 17.8..19.4 from the axis, clear of the streams
                                   # (at 0 and +-120 degrees, 15..16.8 out) and inside the coping's top
# the buttress piers' fronts (ground to 38.81), each chord listed going round (-y side, then +y)
_PIERS = [((20.33, -10.83), (21.47, -8.66)), ((3.99, -21.37), (6.39, -20.96)), ((-14.21, -14.27), (-12.5, -16.02))]
PIERS = _PIERS + [((a[0], -a[1]), (b[0], -b[1])) for a, b in _PIERS]
BANNER = (38.4, 2.6, 17.5, 0.02)   # z_top (under the crown: the cloth lies on the pier), width, length, d
BANNER_PIERS = (0, 3)              # the two front piers, either side of the flood (+-27 degrees)
ARM_FACES = [(-6.03, -1), (6.03, 1)]
ARCH_X = -29.31
ARM_COPING = (-39.35, -16.76, 52.6)    # from the fortress end block to the drum; the walls' top is 52.1


def pier_angle(p, q):
    return math.atan2((p[1] + q[1]) / 2 - CENTRE[1], (p[0] + q[0]) / 2 - CENTRE[0])


def rail_line():
    """The rim's outline pulled RAIL_IN towards the axis: the balustrade's line."""
    cx, cy = CENTRE
    out = []
    for x, y in RIM:
        r = math.hypot(x - cx, y - cy)
        f = (r - RAIL_IN) / r
        out.append((cx + (x - cx) * f, cy + (y - cy) * f))
    return out


def on_line(path, ang):
    """Where the ray from the axis at `ang` (radians) crosses the path."""
    cx, cy = CENTRE
    dx, dy = math.cos(ang), math.sin(ang)
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        ex, ey = x1 - x0, y1 - y0
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        s = ((x0 - cx) * ey - (y0 - cy) * ex) / den      # along the ray
        u = ((x0 - cx) * dy - (y0 - cy) * dx) / den      # along the segment
        if s > 0 and -1e-9 <= u <= 1 + 1e-9:
            return (x0 + ex * u, y0 + ey * u)
    raise ValueError("no crossing at %.1f degrees" % math.degrees(ang))


def rail_runs(path, cuts, gap):
    """The path (going round counter-clockwise, never through 180 degrees) split into runs between
    the newels at angles `cuts`, each run stopping `gap` short of a newel's axis."""
    cx, cy = CENTRE
    events = [(math.atan2(y - cy, x - cx), (x, y), None) for x, y in path]
    for c in cuts:
        r = math.hypot(*(a - b for a, b in zip(on_line(path, c), CENTRE)))
        events += [(c - gap / r, on_line(path, c - gap / r), "stop"), (c + gap / r, on_line(path, c + gap / r), "start")]
    events.sort(key=lambda e: e[0])
    runs, cur = [], []
    for _, p, kind in events:
        if kind == "stop":
            runs.append(cur + [p])
            cur = None
        elif kind == "start":
            cur = [p]
        elif cur is not None:
            cur.append(p)
    return runs + [cur]


class Floodgate(Building):
    style = ElvenStyle()
    source = "EBFFGate"
    target = "EBFFGATE1"
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresF.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_Draw",)
    HOUSE_DRAW = "ModuleTag_Draw_HCFloodgate"
    # Construction's paired internal break faces sit near the intact drum. Match only its exact
    # surface, so those caps stay EA's instead of being mistaken for healthy wall faces.
    lifecycle = {"EBFFGate_A": {"surface": 0.05}}
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
        cuts = [pier_angle(p, q) for p, q in PIERS]
        line = rail_line()
        solids = pad.coping_sweep(RIM, COPING_Z, 0.8, -1.6, CENTRE)             # 1. the mithril coping
        for run in rail_runs(line, cuts, NEWEL - 0.1):                           # 2. its balustrade
            solids += kit.balustrade(run, COPING_Z, height=RAIL_H, pitch=1.5, center=CENTRE, r=0.24)
        for ang in cuts:                                                        # 3. lanterns over the piers
            x, y = on_line(line, ang)
            solids += pad.lantern_newel(kit, x, y, COPING_Z, ang, half=NEWEL, newel=RAIL_H + 0.9, crystal=5.4, r=1.0)
        solids += self.banners(kit)                                             # 4. two banners
        solids += pad.arch(kit, ARCH_X, ARM_FACES)                              # 5. the aqueduct
        x0, x1, z = ARM_COPING
        solids += pad.coping(kit, x0, x1, ARM_FACES, z)
        return solids

    @staticmethod
    def banners(kit):
        """A leaf banner hung from the crown down each front pier, lying on it."""
        from mathutils import Vector as V
        z_top, width, length, d = BANNER
        out = []
        for i in BANNER_PIERS:
            p, q = PIERS[i]
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
        if c.z > 47 and math.hypot(c.x - CENTRE[0], c.y - CENTRE[1]) > 17:
            return 1.3                        # the crown: coping, balustrade and lanterns, what the RTS camera sees
        return 1.0
