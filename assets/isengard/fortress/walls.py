"""The Isengard citadel's curtain and towers (Blender side), pass 2: iron spikes along the curtain's
lip and the wedge towers' top edges, and two heavy banners on the front towers. Pass 1's plates,
vents and gear wheels pasted on the curtain's faces are gone (Max: they read as flat rectangles);
the story pieces stand free on the walks and the ground instead (yard.py).

The curtain (IBFORTRESS mesh coordinates): a 16-gon, faces at 11.25 + 22.5k degrees, apothem
69.2 at mid height (a battered plinth from r 72.8 at the ground to 69 at z 13.7), z 0..45; the
lip at r 72.9, z 52; the walk z 48..50 between r 54 and 67.5. Faces at 11.25 and 348.75 degrees
are the gatehouse's; 33.75 + 90k and 56.25 + 90k run into the wedge towers.
"""
import math

from mathutils import Vector as V

APOTHEM, LIP, LIP_Z = 69.2, 72.9, 52.0
LIP_FACES = (78.75, 101.25, 258.75, 281.25, 33.75, 326.25)     # the faces the RTS camera sees
# the wedge towers' outer top edges (z 85.7): (inner corner, point), signs applied per tower
EDGES = [((38.5, 19.9), (58.5, 58.5)), ((19.9, 38.5), (58.5, 58.5))]
SPIKED = [(1, 1), (1, -1), (-1, -1)]         # every tower but the foundry's
TOWER_FACES = [((38.5, 19.9), (59.7, 58.3)), ((38.5, -19.9), (59.7, -58.3))]
BANNER = (22.0, 79.0, 8.0, 21.0)            # u along the face, top, width, length


def frame(deg):
    a = math.radians(deg)
    n = V((math.cos(a), math.sin(a), 0))
    t = V((-math.sin(a), math.cos(a), 0))
    return n * APOTHEM, t, n


def lip_spikes(kit):
    out = []
    for deg in LIP_FACES:
        a, t, n = frame(deg)
        out += kit.spike_row(a + n * (LIP - APOTHEM), t, n, -9.0, 9.0, LIP_Z - 0.5, 6.5, 4, d=-1.2, lean=0.12, r=0.55)
    return out


def tower_spikes(kit):
    """Iron spikes along the wedge towers' outer top edges, leaning out."""
    out = []
    for sx, sy in SPIKED:
        for (x0, y0), (x1, y1) in EDGES:
            p0, p1 = V((sx * x0, sy * y0, 0)), V((sx * x1, sy * y1, 0))
            t = (p1 - p0).normalized()
            n = V((t.y, -t.x, 0))
            if n.dot(p0.lerp(p1, 0.5) - V((sx * 38.8, sy * 38.8, 0))) < 0:
                n = -n                              # away from the tower top's centroid
            out += kit.spike_row(p0, t, n, 6.0, (p1 - p0).length - 7.0, 85.4, 5.5, 4, d=-0.7, lean=0.45, r=0.5)
    return out


def banners(kit):
    """The two front towers' banners, on their faces toward the gate."""
    out = []
    u, top, w, length = BANNER
    for (x0, y0), (x1, y1) in TOWER_FACES:
        p0, p1 = V((x0, y0, 0)), V((x1, y1, 0))
        t = (p1 - p0).normalized()
        n = V((t.y, -t.x, 0)) if y0 > 0 else V((-t.y, t.x, 0))
        out += kit.banner(p0, t, n, u, top, w, length, d=1.6)
    return out


def build(kit, spikes=True):
    return lip_spikes(kit) + (tower_spikes(kit) if spikes else []) + banners(kit)
