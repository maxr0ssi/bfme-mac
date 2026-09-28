"""The wall walk out of GBFARTOWB's -X side (Blender side; measurements in building.py's
docstring): stepped buttresses down both faces, a black band with the citadel's silver stars on
each parapet's face and square merlons on its top."""
from mathutils import Vector as V

from sagekit.blender.geometry import prism_uz, sweep

X0, X1 = -34.7, -8.22                    # the straight run
FACE, PARAPET, Z_TOP = 10.7, 11.04, 56.0
BAND = (52.8, 55.4)
BUTTRESSES = (-30.4, -21.2, -12.0)


def build(kit):
    t = V((1, 0, 0))
    out = []
    for sy in (-1, 1):
        n = V((0, sy, 0))
        out += sweep([(X0, sy * PARAPET), (X1 - 0.3, sy * PARAPET)], [(-0.5, BAND[0]), (0.6, BAND[0]), (0.6, BAND[1]), (-0.5, BAND[1])],
                     ["stoneB", "enamel", "top", None], center=(-20.0, 0.0))[0]
        out += kit.merlons(V((X0, sy * PARAPET, 0)), t, n, 0.35, X1 - X0 - 0.6, Z_TOP, -1.85, -0.1, w=2.3, gap=1.7, h=2.6, cap=0.5)
        for x in BUTTRESSES:
            b = V((x, sy * FACE, 0))
            out.append(prism_uz(b, t, n, [(-1.3, 0.0), (1.3, 0.0), (1.3, 34.0), (-1.3, 34.0)], -0.3, 1.9,
                                [None, "stoneB", None, "stoneB"], "stoneA", None))
            out.append(prism_uz(b, t, n, [(-1.5, 0.0), (1.5, 0.0), (1.5, 2.4), (-1.5, 2.4)], -0.3, 2.3,
                                [None, "stoneB", "top", "stoneB"], "course", None))
            out.append(prism_uz(b, t, n, [(-1.3, 34.0), (1.3, 34.0), (1.3, 38.5), (-1.3, 38.5)], -0.3, 1.9,
                                ["stoneB", "stoneB", None, "stoneB"], "stoneA", None, bat=1.9 / 4.5))
    return out
