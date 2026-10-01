"""The Hall of Twilight's horns frozen at the tips, on each upgrade level's piece (Blender side).

EA's horns are not on BASE: they belong to the level pieces, one shown at each level (TOP_1 at 1,
V1 at 2, V2 at 3), so each piece is a recipe of its own chained on the one before
(hallof_twilight -> _top -> _v1 -> _v2) and freezes its own horns here with the walls group's
`freeze` (the citadel tines' frozen tips: an ice casing toward the point, a ragged frost line,
rime at the tip, crystals growing out). EA's horns stay whole inside.

Measured 2026-10-01 by slicing EA's KBTemple (model space = mesh space, identity bones):
- the tower's crown: three horns on the shrine's roof, 120 degrees apart round (0, -10.62), the
  same shape on every piece, only higher: TOP_1 z 57.0..78.74, V1 +4.32, V2 +9.43;
- the great horns (V1, V2): three, round the same axis, from the dais's sides up past the crown,
  V1's to z 86.04, V2's (larger, leaning further in) to z 107.45.
V2's three small horns from the dais (to z 46.1) stay EA's: the menhirs stand 3 or less from them
up to z 39. Each path runs from the frost line to EA's point (the first horn's centres; the others
are it turned 120 and 240 degrees), the radii are the casing's (1.2 x the horn's half width + 0.3).
"""
import math

AXIS = (0.0, -10.62)
LIFT = {"TOP_1": 0.0, "V1": 4.32, "V2": 9.43}               # the crown's rise at each level

# the crown's horn over the shrine's front (bearing -90), TOP_1 heights: frozen from z 64 (the upper 2/3)
CROWN = ([(0.01, -26.13, 64.0), (0.02, -26.15, 66.0), (0.03, -26.17, 68.0), (0.04, -26.19, 70.0),
          (0.04, -25.66, 72.0), (0.04, -25.04, 74.0), (0.03, -24.11, 76.0), (0.02, -23.25, 77.5),
          (0.01, -22.54, 78.74)],
         [3.0, 2.7, 2.4, 2.1, 1.75, 1.4, 1.0, 0.6, 0.45])
# the great horn at the back (bearing 90), frozen over its upper 40 %
GREAT = {
    "V1": ([(-0.08, 41.62, 52.0), (-0.06, 40.68, 60.0), (-0.05, 39.99, 65.0), (-0.04, 38.88, 70.0),
            (-0.03, 37.71, 75.0), (0.0, 35.8, 80.0), (0.02, 34.64, 83.0), (0.04, 33.47, 86.04)],
           [5.75, 4.55, 3.8, 2.95, 2.1, 1.3, 0.8, 0.45]),
    "V2": ([(-0.10, 38.51, 70.0), (-0.07, 35.77, 80.0), (-0.06, 34.14, 85.0), (-0.05, 32.35, 90.0),
            (-0.04, 30.22, 95.0), (-0.01, 27.59, 100.0), (0.02, 25.17, 104.0), (0.04, 23.08, 107.45)],
           [6.65, 5.0, 4.25, 3.4, 2.55, 1.65, 0.9, 0.45]),
}


def turned(path, deg, dz=0.0):
    """A horn's path turned `deg` round the Hall's axis and lifted dz."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    ax, ay = AXIS
    return [(ax + c * (x - ax) - s * (y - ay), ay + s * (x - ax) + c * (y - ay), z + dz) for x, y, z in path]


def frozen(kit, piece):
    """Every horn of a level piece ("TOP_1", "V1", "V2") frozen at the tip."""
    from ..shapes_walls import freeze
    out = []
    path, radii = CROWN
    for k in range(3):
        out += freeze(kit, turned(path, 120.0 * k, LIFT[piece]), radii, seed=1.3 + 1.7 * k, crystals=3)
    if piece in GREAT:
        path, radii = GREAT[piece]
        for k in range(3):
            out += freeze(kit, turned(path, 120.0 * k), radii, seed=4.1 + 2.3 * k, crystals=4)
    return kit.retag(out)
