"""The magma cauldrons (Blender side): the magma's road made visible. EA's pieces stay whole (the
cauldron tower on the -X inner face, its two horns and the tipping cauldron, the pan on the -X walk,
the eight spouts on the outer faces); ours show where the magma comes from and where it goes.

    furnace     a furnace mouth at the tower's foot in the courtyard (x -26.47, |y| < 5.8, to z 17.4,
                pass 2: larger): a pointed arch of glowing coals in an iron frame, a hooked barb clawing
                up each side, a real fire in it ("furnace"); two forked cracks glow up the tower's
                courtyard face from it (shapes_addons.fissure)
    spouts      each spout's mouth brims with lava (a flame sill in EA's recess) and seven of them pour
                it down the wall in a kinked runnel (z 25 to 12..19.5; the +X face's +Y spout stands
                over the citadel's scaffold and keeps only its sill); embers at the three the RTS
                camera sees

The footprint is EA's (+-52.74): the runnels stand 0.13 proud of the battered faces and stop at z 12,
where the face comes within that of the limit. They stay clear of the citadel's own cracks on the
-Y and +X faces (fortress/walls.py: the -Y face's crack at x -24 tops out at z 18.2, 2 to the
side of the runnel there, which ends at z 19.5 above it).
"""
from mathutils import Vector as V

from sagekit.blender.geometry import prism_uz

from ..shapes_addons import fissure, plane, runnel

X, Y, Z = V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))
FACE = 52.8                                     # the curtain's outer faces on the ground (battered)
BAT = 1.0 / 45.0
# EA's spouts (MAGMABONE01..08, z 27.42): (face anchor, along, out, u of the spout, the runnel's lowest z or None)
SPOUTS = [(V((FACE, 0, 0)), Y, X, 23.84, None),                 # 01: over the citadel's scaffold
          (V((FACE, 0, 0)), Y, X, -23.76, 15.0),                # 02: over the citadel's crack branch (z 11.7)
          (V((0, -FACE, 0)), X, -Y, 23.8, 16.5),                # 03: over the citadel's crack (z 15)
          (V((0, -FACE, 0)), X, -Y, -23.86, 19.5),              # 04: over the citadel's crack (z 18.2)
          (V((-FACE, 0, 0)), -Y, -X, 23.87, 12.0),              # 05 (u = -y)
          (V((-FACE, 0, 0)), -Y, -X, -23.84, 12.0),             # 06
          (V((0, FACE, 0)), -X, Y, 23.99, 12.0),                # 07 (u = -x)
          (V((0, FACE, 0)), -X, Y, -23.94, 12.0)]               # 08
SEEN = (1, 2, 3)                                # the spouts the RTS camera sees: embers


def spouts(kit):
    out = []
    for i, (a, t, n, u, low) in enumerate(SPOUTS):
        sill = [(u - 2.45, 26.35), (u + 2.45, 26.35), (u + 2.2, 27.35), (u - 2.2, 27.35)]
        out.append(prism_uz(a, t, n, sill, -2.3, -0.1, ["flame"] * 4, "flame", "flame"))
        if low is not None:
            out += runnel(kit, plane(a - n * 0.05, t, n, BAT), u, 25.4, low, w=0.75, seed=i, depth=0.18)
        if i in SEEN:
            kit.fire(a + t * u + n * (-1.2) + Z * 27.6, "embers")
    return out


def furnace(kit):
    a, t, n = V((-26.47, 0, 0)), Y, X
    arch = kit.pointed(9.6, 1.0, 14.0, 0.55)
    out = [prism_uz(a, t, n, arch, -1.2, 0.35, ["ember"] * 5, "ember", None)]
    frame = kit.pointed(11.6, 1.0, 16.4, 0.55)
    for (u0, z0), (u1, z1) in zip(frame, frame[1:] + frame[:1]):
        if z0 < 1.5 and z1 < 1.5:
            continue
        out.append(kit.beam(a + t * u0 + Z * z0 + n * 0.6, a + t * u1 + Z * z1 + n * 0.6, 0.6, "iron"))
    for s in (-1, 1):                               # a hooked barb clawing up each side of the mouth
        p = a + t * (s * 5.9) + n * 0.5 + Z * 8.0
        out += kit.barb(p, (t * (s * 0.35) + n * 0.5 + Z).normalized(), 8.5, 0.6)
    out.append(kit.beam(a + n * 0.5 + Z * 17.6, a + n * 3.4 + Z * 16.2, 0.55, "steel", 0.0))    # the keystone spike
    P = plane(a, t, n)
    out += fissure(kit, P, -1.6, 18.2, 24.0, w=1.0, seed=3.0, segs=8, branches=2)
    out += fissure(kit, P, 2.2, 18.2, 17.0, w=0.8, seed=6.0, segs=6, branches=1)
    kit.fire(a + n * 1.0 + Z * 2.5, "furnace")
    return out


def build(kit):
    return furnace(kit) + spouts(kit)
