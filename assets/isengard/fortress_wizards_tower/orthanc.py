"""Orthanc (Blender side): EA's octagonal tower kept whole and made the tower of the books and films,
"four mighty piers of many-sided stone welded into one, but near the summit they opened into gaping
horns". IBFWTOWER mesh coordinates (identity bone), z up, the tower's axis at the origin.

Kept clear, with every upgrade built: the excavations' chute (its rail at r 20.9..21.8 by the -X -Y
diagonal, z 29..34) and the A-frame's standing timber (r 21.9 by the +X -Y diagonal, z 34..41): the
piers stand 3.2 out there (a waist over the plinth's batter), 8 at the foot. The foot sinks into the pit's floor and the two north
spoil mounds' flanks (z 13..18), as EA's tower sinks into the floor.

EA's tower (sliced, 2026-09-29): an octagon, flat faces on the axes and the diagonals; the diagonal
faces' apothem A(z) below (a plinth to z 40, a steep batter z 20..30, the shaft tapering to z 135,
the crown flaring to r 21 on the axes at z 160: EA's four thin horn blades on the axes, a spike to
z 175.7). The lightning's FXBONE is at (0, 1.2, 184.1): nothing new near the axis above z 165.

    piers   one on each diagonal face, z 0..138: a pentagon in plan (back buried in the face, two
            cheeks, a silver arris), stepped at the plinth's top, ember windows up its cheeks
    horns   each pier opens at z 138 into a horn leaning out and curling back to a point at z 200
    door    a pointed doorway on the +X face (the gate side) with the White Hand above it
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, box

from .. import shapes_addons as A
from ..shapes_walls import bracket_brazier

# (z, diagonal apothem to sink the pier's back into, half-width, projection)
PIER = [(0.0, 20.8, 7.3, 8.0), (16.0, 19.4, 8.3, 7.6), (20.0, 19.0, 8.2, 3.6), (24.0, 17.6, 7.6, 3.2),
        (30.0, 15.9, 7.0, 3.2), (39.0, 15.8, 7.0, 3.4), (40.0, 15.8, 7.0, 5.6), (41.2, 15.8, 7.0, 5.6),
        (41.3, 15.0, 6.3, 5.4), (80.0, 11.6, 5.0, 5.2), (110.0, 10.1, 4.6, 4.9), (128.0, 9.0, 4.3, 5.0),
        (138.0, 8.6, 4.9, 5.6)]
HORN = (138.0, 200.0)
DIAGONALS = (45.0, 135.0, 225.0, 315.0)


def at(z):
    """(apothem, half-width, projection) of the pier at height z (linear between PIER's rows)."""
    for (z0, *a), (z1, *b) in zip(PIER, PIER[1:]):
        if z0 <= z <= z1:
            f = (z - z0) / max(z1 - z0, 1e-6)
            return [x + (y - x) * f for x, y in zip(a, b)]
    return PIER[-1][1:]


def frame(deg, apo):
    a = math.radians(deg)
    n = V((math.cos(a), math.sin(a), 0))
    return n * apo, n, V((-n.y, n.x, 0))


def piers(kit):
    out = []
    for deg in DIAGONALS:
        rings = []
        for z, apo, hw, proj in PIER:
            m, n, t = frame(deg, apo)
            rings.append(A.pier_ring(m, n, t, hw, proj, z))
        out += A.pier(kit, rings, cap=False)       # the horn stands on its top
        z0, z1 = HORN
        m, n, t = frame(deg, PIER[-1][1])
        out += A.horn(kit, m, n, t, z0, z1, PIER[-1][2], PIER[-1][3], lean=0.15, curl=0.12, flare=1.6)
    return out


def windows(kit):
    """Ember windows up each pier's two cheeks."""
    out = []
    for deg in DIAGONALS:
        for z in (56.0, 86.0, 116.0):
            apo, hw, proj = at(z + 2.5)
            m, n, t = frame(deg, apo)
            ring = A.pier_ring(m, n, t, hw, proj, 0.0)
            for s in (0, 1):
                p, q = (ring[3], ring[4]) if s == 0 else (ring[4], ring[5])
                tt = (q - p).normalized()
                nn = V((tt.y, -tt.x, 0))
                if nn.dot((p + q) / 2 - m) < 0:
                    nn = -nn
                out += A.ember_slit(kit, (p + q) / 2, tt, nn, 0.0, z, 1.1, 5.0, d0=-0.6, d1=0.15)
    return out


def door(kit):
    """A pointed doorway on the +X face (x 21.7 at the foot, battered 0.075 per unit up) and the
    Hand above it on the plinth's upright part (x 16.5 at z 30..39)."""
    out = A.arch_slot(kit, V((21.62, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), 0.0, 0.5, 8.0, 15.5, -0.6, 0.35, "iron",
                      "trim", 0.35, bat=0.075)
    out += A.hand_arch(kit, V((16.45, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), 0.0, 30.4, 5.6, 8.4, -0.5, 0.5)
    return out


def balcony(kit):
    """Saruman's balcony on the +X face over the door (EA's face at x 11.2, z 92..100): a ledge on
    two pointed corbels, a spiked iron railing, a pointed window behind it."""
    x = 11.1
    V3 = lambda px, py, pz: V((px, py, pz))                  # noqa: E731
    out = [box(x - 0.6, x + 4.6, -5.0, 5.0, 93.6, 94.8, "stoneA", ("stoneA", True), ("stoneB", True))]
    for y in (-3.6, 3.6):                                    # pointed corbels under it
        out += kit.blade(V3(x, y, 0), V((1, 0, 0)), 86.0, 93.6, 0.4, 4.4, w=1.0, tip=0.0, back=1.2)
    out.append(kit.beam(V3(x + 4.4, -5.0, 95.9), V3(x + 4.4, 5.0, 95.9), 0.22, "trim"))
    for y in (-4.8, -2.4, 0.0, 2.4, 4.8):
        out.append(kit.beam(V3(x + 4.4, y, 94.6), V3(x + 4.4, y, 97.8), 0.2, "iron", 0.0))
    for y in (-4.8, 4.8):
        out.append(kit.beam(V3(x + 4.4, y, 95.9), V3(x + 0.2, y, 95.9), 0.2, "iron"))
    out += A.arch_slot(kit, V3(x - 0.05, 0, 0), V((0, 1, 0)), V((1, 0, 0)), 0.0, 94.8, 4.0, 7.5, -0.6, 0.3, "ember",
                       "trim", 0.25)
    return out


def hands(kit):
    """The White Hand great in a pointed arch high on the three axis faces the balcony leaves free
    (-Y, +Y, -X; EA's faces at apothem 11.0 over z 100..118, 8 wide between the piers)."""
    out = []
    for deg in (270.0, 90.0, 180.0):
        m, n, t = frame(deg, 10.95)
        out += A.hand_arch(kit, m, t, n, 0.0, 101.0, 5.4, 16.0, -0.6, 1.0)
    return out


def fires(kit):
    """Braziers on iron brackets out of each pier's arris at z 78, between the windows, above the
    walls (13 or more clear of the excavations' A-frame and bucket over IBFExcavAN; at z 46 the
    A-frame's head passed within 1 of the +X -Y one), and two on the balcony."""
    out = []
    for deg in DIAGONALS:
        apo, hw, proj = at(78.0)
        m, n, t = frame(deg, apo)
        out += bracket_brazier(kit, m + n * (proj - 0.4) + Z * 78.0, n, reach=3.0, r=2.1)
    for y in (-3.4, 3.4):
        out += kit.brazier(V((14.0, y, 94.8)), 1.2, 2.6)
    return out


def build(kit):
    return piers(kit) + windows(kit) + door(kit) + balcony(kit) + hands(kit) + fires(kit)
