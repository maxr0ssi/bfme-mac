"""The ballista expansion (Blender side), IBFBALTOW mesh coordinates (identity bone). EA's pad
(sliced 2026-09-29): a pentagon in plan - the back x -35 (y +-17), the long sides y +-17 to x 4.1,
two faces meeting in a prow at (17.6, 0) - on a finned foot to z 25 (fins to y +-20.2), two
bands (z 25..26.4, 35.7..36.7), plain upper walls, a cornice to y +-18.1 at z 48.1..51 and a flat
top where the ballista stands (P1 at z 48.9, x -26.4..6, |y| < 15.5).

Enriched in the citadel's language, the top kept clear: pointed merlons along the cornice, a White
Hand in a pointed arch on each long side, ember arrow loops in the upper walls, a blade up the
prow, knife fins on the upper walls' corners, and braziers at the top's back corners (real fire)."""
from mathutils import Vector as V

from sagekit.blender.geometry import Z

from .. import shapes_addons as A

TOP = 51.0
RIM = [(-34.6, -17.8), (4.1, -17.8), (17.5, 0.0), (4.1, 17.8), (-34.6, 17.8)]     # the cornice, just inside


def crown(kit):
    return A.crown_blades(kit, RIM, TOP - 0.4, 7.5, per_edge=3, w=0.7, lean=0.0, corners=False, width=2.6)


def sides(kit):
    """The long sides (y +-17.0 between the bands): a Hand in the middle, arrow loops either side."""
    out = []
    for s in (-1, 1):
        a, n = V((0, s * 16.95, 0)), V((0, s, 0))
        t = V((1, 0, 0)) if s < 0 else V((-1, 0, 0))
        out += A.hand_arch(kit, a, t, n, -15.0 * (1 if s < 0 else -1), 37.4, 7.0, 10.2, -0.6, 0.6)
        for u in (-30.0, -24.0, -6.0, 0.0):
            uu = u if s < 0 else -u
            out += A.ember_slit(kit, a, t, n, uu, 27.6, 1.2, 6.2, d0=-0.6, d1=0.2)
            out += A.ember_slit(kit, a, t, n, uu, 38.0, 1.2, 7.4, d0=-0.6, d1=0.2)
    return out


def prow(kit):
    """A knife blade up the prow's edge (x 17.1 at z 10, 16.8 above the bands), to the cornice."""
    return kit.blade(V((16.4, 0, 0)), V((1, 0, 0)), 0.0, 46.0, 1.4, 1.0, w=1.4, tip=3.0, back=2.0, edge="stoneB")


def corners(kit):
    """Knife fins on the upper walls' corners (between the bands and the cornice), EA's 7-degree lean."""
    out = []
    for (x, y), d in (((4.1, -17.0), (0.6, -0.8)), ((4.1, 17.0), (0.6, 0.8)), ((-35.0, -17.0), (-0.7, -0.7)),
                      ((-35.0, 17.0), (-0.7, 0.7))):
        out += kit.blade(V((x, y, 0)) - V((d[0], d[1], 0)) * 0.6, V((d[0], d[1], 0)), 26.4, 47.8, 1.0, 0.4, w=1.0,
                         tip=0.0, back=1.2)
    return out


def braziers(kit):
    out = []
    for y in (-14.8, 14.8):
        out += kit.brazier(V((-31.8, y, TOP - 0.3)), 1.3, 3.0)
    return out


def build(kit):
    return crown(kit) + sides(kit) + prow(kit) + corners(kit) + braziers(kit)
