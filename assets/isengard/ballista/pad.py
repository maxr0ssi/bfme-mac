"""The ballista expansion (Blender side), IBFBALTOW mesh coordinates (identity bone). EA's pad
(sliced 2026-09-29): a pentagon in plan - the back x -35 (y +-17), the long sides y +-17 to x 4.1,
two faces meeting in a prow at (17.6, 0) - on a finned foot to z 25 (fins to y +-20.2), two
bands (z 25..26.4, 35.7..36.7), plain upper walls, a cornice to y +-18.1 at z 48.1..51 and a flat
top where the ballista stands (P1 at z 48.9, x -26.4..6, |y| < 15.5).

Enriched in the citadel's language, the top kept clear: pointed merlons along the cornice, a White
Hand in a pointed arch on each long side, ember arrow loops in the upper walls, a blade up the
prow, knife fins on the upper walls' corners, and braziers at the top's front corners (real fire).
Pass 3: the citadel's pair, two blades against the long walls' back halves to needles at z 68.5
(max_z_growth 0.35, Max's OK pending), and a taller crown of merlons."""
from mathutils import Vector as V

from sagekit.blender.geometry import Z

from .. import shapes_addons as A

TOP = 51.0
# the pair: two blades against the long walls' back halves from the foot to needles at z 61, behind
# the ballista as the camera sees it (its turntable, P1, x -26.4..6, |y| < 15.5, stays clear above the top)
BR = ((-27.2, -16.1), 0.0, 7.6, 3.4, 0.0, 68.5, (0.0, 0.8), 1.1)
BL = ((-27.2, 16.1), 0.0, 7.6, 3.4, 0.0, 68.5, (0.0, -0.8), 1.1)
# stockier than the citadel's BROAD: the pad is low, so the blades keep their mass above its top and
# taper to the needle over the last eighth
STOCKY = [(0.0, None), (0.04, 1.0), (0.3, 0.96), (0.302, 0.9), (0.62, 0.86), (0.622, 0.79), (0.86, 0.64), (1.0, 0.03)]
RIM = [(-34.6, -17.8), (4.1, -17.8), (17.5, 0.0), (4.1, 17.8), (-34.6, 17.8)]     # the cornice, just inside


def blades(kit):
    out = A.blade_pair(kit, (BR, BL), fins=3, fin_reach=1.2, spurs=False, slits=(0.34, 0.5, 0.66), slit_w=1.0,
                       profile=STOCKY)
    for b in (BR, BL):
        out += A.foot_spurs(kit, b, which=(0,), length=3.0)
    out += A.blade_hand(kit, BR, 3, 24.0, 12.0, 5.2, profile=STOCKY)
    out += A.blade_hand(kit, BL, 0, 24.0, 12.0, 5.2, profile=STOCKY)
    return out


def crown(kit):
    """Pointed merlons along the cornice: the front run from the blades round the prow, and the back
    edge between the blades."""
    front = [(-21.0, -17.8), (4.1, -17.8), (17.5, 0.0), (4.1, 17.8), (-21.0, 17.8)]
    out = A.crown_blades(kit, front, TOP - 0.4, 9.6, per_edge=2, w=0.7, lean=0.0, corners=False, width=2.6,
                         closed=False, centre=(-8.0, 0.0))
    return out + A.crown_blades(kit, [(-34.6, 17.8), (-34.6, -17.8)], TOP - 0.4, 9.6, per_edge=3, w=0.7, lean=0.0,
                                corners=False, width=2.6, closed=False, centre=(-8.0, 0.0))


def sides(kit):
    """The long sides (y +-17.0 between the bands): a Hand in the middle, arrow loops either side."""
    out = []
    for s in (-1, 1):
        a, n = V((0, s * 16.95, 0)), V((0, s, 0))
        t = V((1, 0, 0)) if s < 0 else V((-1, 0, 0))
        out += A.hand_arch(kit, a, t, n, -15.0 * (1 if s < 0 else -1), 37.4, 7.0, 10.2, -0.6, 0.6)
        for u in (-6.0, 0.0):
            uu = u if s < 0 else -u
            out += A.ember_slit(kit, a, t, n, uu, 27.6, 1.2, 6.2, d0=-0.6, d1=0.2)
            out += A.ember_slit(kit, a, t, n, uu, 38.0, 1.2, 7.4, d0=-0.6, d1=0.2)
    return out


def prow(kit):
    """A knife blade up the prow's edge (x 17.1 at z 10, 16.8 above the bands), to the cornice; on
    each prow face (4.1, +-17) .. (16.8, 0) a knife fin between two ember arrow loops."""
    out = kit.blade(V((16.4, 0, 0)), V((1, 0, 0)), 0.0, 46.0, 1.4, 1.0, w=1.4, tip=3.0, back=2.0, edge="stoneB")
    for s in (-1, 1):
        a, b = V((4.1, s * 17.0, 0)), V((16.8, 0, 0))
        t = (b - a).normalized()
        n = V((t.y, -t.x, 0))
        if n.x < 0:
            n = -n
        L = (b - a).length
        out += kit.blade(a + t * (L * 0.5) - n * 0.4, n, 26.6, 47.6, 2.0, 0.9, w=1.0, tip=2.0, back=1.0)
        for u in (L * 0.26, L * 0.74):
            out += A.ember_slit(kit, a, t, n, u, 38.0, 1.2, 7.4, d0=-0.6, d1=0.2)
    return out


def corners(kit):
    """Knife fins on the upper walls' corners (between the bands and the cornice), EA's 7-degree lean."""
    out = []
    for (x, y), d in (((4.1, -17.0), (0.6, -0.8)), ((4.1, 17.0), (0.6, 0.8))):
        out += kit.blade(V((x, y, 0)) - V((d[0], d[1], 0)) * 0.6, V((d[0], d[1], 0)), 26.4, 47.8, 1.0, 0.4, w=1.0,
                         tip=0.0, back=1.2)
    for s in (-1, 1):                      # the long walls' buttress fins, between the Hand and the loops
        for x in (-19.2, -9.6, -3.0):
            out += kit.blade(V((x, s * 16.6, 0)), V((0, s, 0)), 26.6, 47.6, 2.0, 0.9, w=1.0, tip=2.0,
                             back=1.0)
    return out


def braziers(kit):
    out = []
    for y in (-12.0, 12.0):                # the top's front corners, clear of the turntable
        out += kit.brazier(V((6.5, y, TOP - 0.3)), 1.3, 3.0)
    return out


def build(kit):
    return blades(kit) + crown(kit) + sides(kit) + prow(kit) + corners(kit) + braziers(kit)
