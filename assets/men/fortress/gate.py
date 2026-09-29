"""The Gondor gatehouse front (Blender side), on EA's gate (the +X face, GBFORTRESS coordinates).

EA's gate: a stone frame x 47.7..55.6, |y| <= 17.8, top 41.9 at the jambs and 48.4 at the crown;
its opening |y| < 11.8 (14.5 at the splayed front), crown 39.1 behind and 42.4 at the front.
The doors (GBFDoor, outward-swinging) sweep x 51.7..~66, |y| <= 15.4 (at x 57.5), z 0..40.9, so
nothing new stands there. The oil upgrade's
outlets sit on the wall at x 48.8..49.6, |y| 19.5..24.4, z 26..38.9; the healing house's front is
x 48.8 above the walk (z 48+). What is added, in front of them:

    pilasters   at |y| 15.75..19.3 from a plinth to moulded capitals at 41.5 (clear of the doors'
                sweep and the oil outlets; the capitals widen only above the oil and the doors)
    archivolt   eleven voussoirs springing from the capitals (inner curve crown 47.1, never below
                41.5), a keystone standing out to the frieze, stone backing up to the architrave
    portcullis  its teeth showing under the archivolt: steel bars in front of EA's frame, their
                points at 41.35, above the doors' top
    entablature an architrave, a black frieze with the seven gilt stars, a moulded cornice
    pediment    a black tympanum with the White Tree, raking cornices, a winged-helm crest on the
                apex and pinnacles on the corners
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import box, box_rings, loft, prism_uz

X_BACK, X_FRAME = 49.4, 55.6
PIL_Y, PIL_X = (15.75, 19.3), 57.8
SPRING = 41.5
INNER, OUTER = (15.6, 5.6, SPRING), (19.4, 10.2, SPRING)       # (half, rise, spring)
Z_ARCH, Z_FRIEZE, Z_CORNICE, Z_PED = 51.8, 53.0, 55.6, 57.5
ENT_Y = 21.2
PED_Y, PED_APEX = 19.0, 65.3
A, T, N = V((0, 0, 0)), V((0, 1, 0)), V((1, 0, 0))             # u = y, d = x


def z_inner(y):
    h, r, s = INNER
    return s + r * math.sqrt(max(0.0, 1 - (y / h) ** 2))


def build(kit):
    out = []
    for sy in (-1, 1):
        out += _pilaster(sy)
    out += kit.voussoirs(V((X_FRAME - 0.1, 0, 0)), T, N, INNER, OUTER, 0.0, 1.8, count=11, key=(1.7, 53.3, 0.8))
    out += _backing()
    out += _portcullis()
    out += _entablature(kit)
    out += _pediment(kit)
    return out


def _pilaster(sy):
    def ys(a, b):
        return tuple(sorted((sy * a, sy * b)))
    y0, y1 = PIL_Y
    out = [box(X_BACK - 0.1, 58.3, *ys(y0 - 0.1, y1 + 0.1), 0.0, 3.0, "stoneB"),
           box(X_BACK - 0.1, PIL_X, *ys(y0, y1), 3.0, 39.4, "stoneA", cap1=("top", False)),
           box(PIL_X - 0.2, PIL_X + 0.35, *ys(y0 + 0.8, y1 - 0.8), 6.0, 36.4, ["stoneB", "stoneB", "stoneB", None], cap0=("stoneB", True))]
    rings = [box_rings((X_BACK - 0.1, x), ys(ya, yb), z, 0) for x, ya, yb, z in
             ((PIL_X, y0, y1, 39.4), (58.15, y0 - 0.05, y1 + 0.5, 40.1), (58.35, y0 - 0.1, y1 + 1.0, 40.9), (58.35, y0 - 0.1, y1 + 1.0, SPRING))]
    out.append(loft(rings, ["course", "stoneB", "course"], cap0=("stoneB", False), cap1=("top", True)))
    return out


def _backing():
    """Stone from the archivolt's inner curve up to the architrave, behind the voussoirs, in strips
    (each convex), and the spandrels out to the entablature's ends."""
    out = []
    h = INNER[0]
    ys = [-h + 2 * h * i / 14 for i in range(15)]
    for i, (ya, yb) in enumerate(zip(ys, ys[1:])):
        poly = [(ya, z_inner(ya)), (yb, z_inner(yb)), (yb, Z_ARCH), (ya, Z_ARCH)]
        tags = ["stoneB", "stoneB" if i == 13 else None, None, "stoneB" if i == 0 else None]
        out.append(prism_uz(A, T, N, poly, X_BACK, 56.0, tags, "stoneA", "stoneB"))
    for sy in (-1, 1):
        y0, y1 = sorted((sy * h, sy * ENT_Y))
        out.append(box(X_BACK, 56.0, y0, y1, SPRING, Z_ARCH, "stoneA", cap0=("stoneB", True), cap1=("top", False)))
    return out


def _portcullis():
    out = []
    for i in range(11):
        y = -11.0 + 2.2 * i
        top = z_inner(y) + 0.3
        out.append(prism_uz(A, T, N, [(y - 0.22, 42.0), (y + 0.22, 42.0), (y + 0.22, top), (y - 0.22, top)], 55.62, 56.0,
                            [None, "iron", None, "iron"], "iron", None))
        out.append(prism_uz(A, T, N, [(y - 0.3, 42.0), (y + 0.3, 42.0), (y, 41.35)], 55.62, 56.05, ["iron", "iron", "iron"], "iron", None))
    for z in (43.2, 45.2):
        out.append(prism_uz(A, T, N, [(-11.4, z - 0.25), (11.4, z - 0.25), (11.4, z + 0.25), (-11.4, z + 0.25)], 55.95, 56.3,
                            ["iron"] * 4, "iron", None))
    return out


def _entablature(kit):
    out = [box(X_BACK, 57.6, -ENT_Y, ENT_Y, Z_ARCH, Z_FRIEZE, "course", cap0=("stoneB", True), cap1=("top", True)),
           box(X_BACK, 57.2, -ENT_Y, ENT_Y, Z_FRIEZE, Z_CORNICE, ["stoneB", "enamel", "stoneB", "stoneB"], cap1=("top", False))]
    rings = [box_rings((X_BACK, x), (-ENT_Y - e, ENT_Y + e), z, 0) for x, e, z in
             ((57.2, 0.0, Z_CORNICE), (58.35, 0.6, Z_CORNICE + 0.7), (58.35, 0.6, Z_PED - 0.2), (58.0, 0.4, Z_PED))]
    out.append(loft(rings, ["stoneB", "course", "top"], cap0=("stoneB", False), cap1=("top", True)))
    for i in range(7):
        out += kit.star(A, T, N, -9.9 + 3.3 * i, 54.3, 0.95, 57.1, 57.5)
    for sy in (-1, 1):                           # consoles over the pilasters, a steel boss on each
        y0, y1 = sorted((sy * 16.3, sy * 18.8))
        out.append(box(57.0, 57.9, y0, y1, Z_FRIEZE, Z_CORNICE, ["stoneB", "stoneA", "stoneB", None], cap1=("top", False)))
        out.append(prism_uz(A, T, N, [(sy * 17.55 - 0.5, 53.8), (sy * 17.55 + 0.5, 53.8), (sy * 17.55 + 0.5, 54.8),
                                      (sy * 17.55 - 0.5, 54.8)], 57.8, 58.25, ["trim"] * 4, "trim", None))
    return out


def _pediment(kit):
    out = [prism_uz(A, T, N, [(-PED_Y, Z_PED), (PED_Y, Z_PED), (0, PED_APEX)], 50.4, 57.2, [None, "stoneB", "stoneB"], "enamel", "stoneB")]
    for e in (-1, 1):                            # raking cornices
        poly = [(0, PED_APEX), (e * PED_Y, Z_PED), (e * (PED_Y + 1.6), Z_PED), (0, PED_APEX + 1.6)]
        out.append(prism_uz(A, T, N, poly, 50.2, 58.2, ["stoneB", "stoneB", "slate", None], "course", "stoneB"))
    out += kit.white_tree(A, T, N, 0.0, 57.9, 6.4, 57.3, r=0.2)
    out += kit.winged_crest(A, T, N, 0.0, PED_APEX + 1.3, 55.6, 57.8, s=1.1)
    for sy in (-1, 1):
        out += kit.pinnacle(56.4, sy * (PED_Y + 0.6), Z_PED, Z_PED + 2.2, half=1.0, spire=3.6)
    return out
