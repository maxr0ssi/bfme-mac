"""The battle tower (Blender side), TOWER mesh coordinates (identity bone). EA's tower (sliced
2026-09-29): a battered plinth to z 48 (x -9.5..22, |y| < 13.5 at the foot, clawed corners), a
square shaft x 0..16.9, |y| < 8.45 from z 52 (a band at z 60..63, an X-braced panel z 62..77), the
archers' deck at z 97..99 (x -2.6..19, |y| < 9.8) on corner posts, and an upswept roof from eaves
at z 109..111 (x -7..24, |y| < 14.5) to its spike at z 126.

Kept clear: the archers (ARROWBONE01..12 inside the shaft at z 84..86 and 103..104), the garrison
flags (GARRISON01/02 at x 8.5, out to y +-20, z 83..103) and the door (x -28..-8 at the foot).

    fins      knife fins up the shaft's four corners, silver-edged, spurred at the plinth
    bands     riveted iron bands round the shaft over and under the panel
    hands     the White Hand in a pointed arch on the shaft's +X face (the side the camera sees)
    slits     ember arrow slits in the plinth's +X and -Y faces
    eaves     iron spikes along the roof's eaves, leaning out
    braziers  two on the archers' deck (real fire)"""
from mathutils import Vector as V

from .. import shapes_addons as A

X, Y = V((1, 0, 0)), V((0, 1, 0))
C = (8.45, 0.0)                           # the shaft's axis


def fins(kit):
    out = []
    for x, y in ((0.0, -8.45), (16.9, -8.45), (16.9, 8.45), (0.0, 8.45)):
        d = V((x - C[0], y - C[1], 0)).normalized()
        out += kit.blade(V((x, y, 0)) - d * 0.8, d, 50.5, 95.5, 1.6, 1.2, w=0.8, tip=3.5, back=1.4)
    return out


def bands(kit):
    out = []
    for z in (56.0, 88.5):
        out += kit.hoop(C, z, 11.95, h=1.6, th=0.5, inner=0.6, k=4, phase=0.785398, rivets=True, closed=True)
    return out


def hands(kit):
    return A.hand_arch(kit, V((16.9, 0, 0)), Y, X, 0.0, 79.5, 7.0, 13.5, -0.6, 0.6)


def slits(kit):
    """Two slits per face, on the plinth's battered faces (x 20.2 -> 19.3, y -11.7 -> -10.8 over
    z 27..48: leaning back 0.045 per unit)."""
    out = []
    for u in (-5.0, 5.0):
        out += A.ember_slit(kit, V((20.15, 0, 0)), Y, X, u, 30.0, 1.4, 9.0, d0=-1.2, d1=0.3, bat=0.045)
    for u in (3.0, 14.0):
        out += A.ember_slit(kit, V((0, -11.7, 0)), X, -Y, u, 30.0, 1.4, 9.0, d0=-1.2, d1=0.3, bat=0.045)
    return out


def eaves(kit):
    """Spikes along the roof's lower edges (z 110, the square x -6.5..23.5, |y| 14)."""
    out = []
    corners = [(-6.5, -13.4), (23.5, -13.4), (23.5, 13.4), (-6.5, 13.4)]
    for i, (x0, y0) in enumerate(corners):
        x1, y1 = corners[(i + 1) % 4]
        a, b = V((x0, y0, 0)), V((x1, y1, 0))
        t = (b - a).normalized()
        n = V((t.y, -t.x, 0))
        if n.dot((a + b) / 2 - V((C[0], C[1], 0))) < 0:
            n = -n
        out += kit.spike_row(a, t, n, 4.0, (b - a).length - 4.0, 110.2, 4.5, 4, d=-0.8, lean=0.35, r=0.45)
    return out


def braziers(kit):
    out = []
    for y in (-6.6, 6.6):
        out += kit.brazier(V((16.0, y, 99.1)), 1.1, 2.6)
    return out


def build(kit):
    return fins(kit) + bands(kit) + hands(kit) + slits(kit) + eaves(kit) + braziers(kit)
