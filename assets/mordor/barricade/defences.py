"""The Mordor barricade (Blender side), MBBARCADE mesh coordinates (identity bone). EA's barricade
(measured 2026-09-30): an L of three blocks and a keep, their fronts to -Y and +X (the camera's
sides). The low block x -37.7..-14.7 (roof z 33.3), the keep x -14.7..13.9 (roof z 65.8, four
corner spikes to z 78), their shared front at y -28.4; the +X block x 13.9..43.35, y -32.4..-0.6
(roof z 45.4), its +X face at x 43.35 with the gate's arch (y -26..-6, to z 27); the +Y wing
x 19.9..40.3, y -0.6..33.4 (roof z 42). Every back face is at y -0.6. The footprint runs to
y -35.8 and x 47.7: a strip of ground before the fronts.

Kept clear: the archers' bones ARCHER_01 (30.0, 17.4, 43.1), _02 (29.1, -16.1, 46.0), _03 (0.0,
-13.6, 66.8), _04 (-26.6, -14.0, 33.6): nothing within 5 of them.

    lava      open lava along the foot of every front (y -30.4 before the low block and the keep,
              y -34 before the +X block, x 45.5 across the gate as a moat, x 42.5 before the wing),
              a basalt kerb on its outer side; glowing cracks up the fronts
    gate      the raised portcullis' barbed steel teeth in the gate's arch
    stakes    crooked barbed stakes in a row before the low block and the keep, leaning out
    spikes    steel spikes leaning out along every roof's outer lips
    keep      a claw of eight jagged spikes rising from inside the keep's parapet, leaning in (tips
              to z 85.5, 6 or more from ARCHER_03)
    eye       the Lidless Eye on the keep's front (z 46..61)
    baskets   two fire baskets on the low block's and the wing's roofs
"""
from mathutils import Vector as V

from .. import shapes_harad as H

X, Y = V((1, 0, 0)), V((0, 1, 0))
MX, MY = V((-1, 0, 0)), V((0, -1, 0))
# cracks: (u, z) polylines from the foot up
CRACKS = {
    "A": [(0.0, 0.3), (0.9, 3.5), (-0.4, 6.5), (1.4, 9.5), (0.8, 12.5), (2.2, 15.5)],
    "B": [(0.0, 0.3), (-1.1, 3.0), (-0.3, 6.0), (-1.8, 9.0), (-1.0, 12.0), (-2.4, 14.0)],
    "C": [(0.0, 0.3), (0.8, 2.8), (-0.6, 5.5), (0.6, 8.5), (-0.4, 10.5)],
}
BRANCH = {"A": [(-0.4, 6.5), (-2.2, 8.5), (-3.0, 11.0)], "B": [(-0.3, 6.0), (1.7, 7.5), (2.4, 10.0)],
          "C": [(-0.6, 5.5), (-2.4, 6.8), (-3.0, 8.8)]}


def lava(kit):
    out = kit.lava_channel([(-37.0, -30.4, 0.0), (-12.0, -30.5, 0.0), (13.2, -30.3, 0.0)], w=1.3, kerb=0.8, h=1.1,
                           seed=1.0, sides=(-1,), pitch=5.0)
    out += kit.lava_channel([(14.0, -34.2, 0.0), (29.0, -34.1, 0.0), (44.8, -34.1, 0.0)], w=1.0, kerb=0.6, h=1.0,
                            seed=2.0, sides=(-1,), pitch=5.0)
    out += kit.lava_channel([(45.6, -32.0, 0.0), (45.6, -16.0, 0.0), (45.5, -1.5, 0.0)], w=1.4, kerb=0.6, h=1.0,
                            seed=3.0, sides=(-1,), pitch=5.0)
    out += kit.lava_channel([(42.6, 1.0, 0.0), (42.7, 17.0, 0.0), (42.6, 33.0, 0.0)], w=1.2, kerb=0.6, h=1.0,
                            seed=4.0, sides=(-1,), pitch=5.0)
    faces = [(V((0, -28.4, 0)), X, MY, [(-17.5, "C", 1.2), (-6.0, "B", 1.4), (8.0, "A", 1.2)]),
             (V((0, -32.4, 0)), X, MY, [(18.5, "B", 1.1), (37.0, "A", 1.0)]),
             (V((43.35, 0, 0)), Y, X, [(-28.5, "C", 0.9), (-3.0, "C", 0.8)]),
             (V((40.3, 0, 0)), Y, X, [(9.0, "A", 1.0), (25.0, "C", 1.1)])]
    for a, t, n, cracks in faces:
        for u, k, sc in cracks:
            pts = [(u + x * sc, 0.4 + z * sc) for x, z in CRACKS[k]]
            out += kit.lava_crack(a, t, n, pts, w=1.6)
            pts = [(u + x * sc, 0.4 + z * sc) for x, z in BRANCH[k]]
            out += kit.lava_crack(a, t, n, pts, w=0.9)
    for p in ((-24.0, -30.4, 0.4), (4.0, -30.4, 0.4), (30.0, -34.1, 0.4), (45.6, -16.0, 0.4), (42.6, 20.0, 0.4)):
        kit.fire(p, "embers")
    for p in ((-10.0, -30.6, 0.8), (45.6, -24.0, 0.8)):
        kit.fire(p, "smoke")
    return out


def gate(kit):
    return kit.portcullis(V((43.35, 0, 0)), Y, X, -24.5, -7.5, 13.0, 21.0, teeth=6, d=-0.6, r=0.55, length=1.1)


def stakes(kit):
    out = []
    for i, x in enumerate((-35.0, -27.5, -19.0, -9.0, 1.0, 10.0)):
        d = V((0.12 * (1 if i % 2 else -1), -0.17, 1.0)).normalized()
        out += kit.stake(V((x, -32.8, 0.7)), d, 11.0 + 2.0 * (i % 2), r=0.6, barbs=2, seed=i)
    return out


# the roofs' outer lips: (anchor, along, out, u0, u1, z of the roots, count, length, lean out)
LIPS = [(V((0, -28.6, 0)), X, MY, -37.0, -16.5, 33.3, 6, 8.0, 0.5),            # the low block
        (V((-37.9, 0, 0)), MY, MX, 2.0, 27.0, 33.3, 6, 8.0, 0.5),
        (V((0, -28.6, 0)), X, MY, -12.5, 12.0, 65.8, 5, 10.0, 0.5),            # the keep
        (V((14.1, 0, 0)), Y, X, -26.5, -3.5, 65.8, 5, 10.0, 0.5),
        (V((0, -32.6, 0)), X, MY, 16.0, 42.0, 45.8, 7, 7.5, 0.3),              # the +X block
        (V((43.5, 0, 0)), Y, X, -31.0, -2.0, 45.8, 7, 7.5, 0.3),
        (V((40.5, 0, 0)), Y, X, 1.5, 32.5, 42.2, 7, 7.5, 0.5)]                # the wing


def spikes(kit):
    out = []
    for a, t, n, u0, u1, z, count, L, lean in LIPS:
        out += kit.spike_row(a, t, n, u0, u1, z, L, count, d=-0.3, lean=lean, r=0.85, tag="steel")
    return out


KEEP = (-0.35, -14.55)                     # the keep roof's middle (x -12.7..12, y -26.6..-2.5, z 65.8)
CLAW = {"tall": ([(64.5, 10.0, (1.5, 1.2, 1.0)), (72.0, 10.3, (1.3, 1.05, 0.9)), (78.0, 9.2, (0.9, 0.75, 0.6)),
                  (82.0, 7.6, (0.55, 0.45, 0.4))], (6.3, 85.5)),
        "short": ([(64.5, 9.6, (1.1, 0.9, 0.8)), (70.5, 9.8, (0.85, 0.7, 0.6)), (75.5, 8.6, (0.5, 0.45, 0.4))],
                  (7.2, 79.0))}


def keep(kit):
    """A claw of jagged spikes rising from inside the keep's parapet and leaning in over its roof,
    the tips 6 or more from the archer in its middle (ARCHER_03)."""
    return H.claw(kit, KEEP, CLAW, count=8, phase=0.0)


def eye(kit):
    return kit.eye(V((0, -28.4, 0)), X, MY, 0.0, 46.0, 7.0, 15.0, d=0.0)


def baskets(kit):
    return kit.fire_basket(V((-33.0, -24.0, 33.3)), 2.2, 6.0) + kit.fire_basket(V((35.5, 28.0, 42.0)), 2.2, 6.0)


def build(kit):
    return lava(kit) + gate(kit) + stakes(kit) + spikes(kit) + keep(kit) + eye(kit) + baskets(kit)
