"""The Mordor citadel's walls and gate (Blender side): the black land split by lava, the gate with
barbed teeth under the Eye, impaling stakes at the ramp, an orc scaffold.

EA's curtain (MBFORTRESS mesh coordinates, measured 2026-09-30): the outer faces at 52.8 on the
ground battered to 51.8 at z 45 (the parapet to z 70), iron spikes along their foot (48.6..52.8,
z 0..24.5); the walk at z 51 from 48.1 in to 32.1; the courtyard's floor at z 1 inside the inner
faces at 29.04 (the +-X ones to z 69, the +-Y ones to z 43, battered 2.6 degrees). The gatehouse
runs out along +X (|y| < 12, x 27.9..57, z 0..60): the door recess at x 56.9 (|y| < 7.4, to z
45), the outer arch at x 64.1 (jambs |y| 8.5 to z 24.6, head to 50.9), the frontispiece at x 57.3
(|y| < 12.9, its point z 73, horns to 82); the ramp on out to x 113 at z 1.

Kept clear: the Gorgoroth spire (|x| < 19.15, |y| < 23.3, the courtyard's middle), the magma
cauldrons' base on the -X inner face (x -44.2..-23.4, |y| < 8.9, z 0..66) and their spouts on
the outer faces (z 25.3..37.3), the fire arrows over the gatehouse (x 32.6..51.6), the door on the
courtyard side (x 27.94, |y| < 6), the ramp (|y| < 14), EA's box (y +-57.26).

    lava        broad open lava (5.8 wide) welling from under the foot of the -Y face and the +X
                face's -Y half, a basalt kerb on its outer side; a channel round the courtyard at
                26.4 (broken at the cauldrons and the door); broad seams up those outer faces; two thin
                smoke columns off the lava at the wall feet
    the gate    the raised portcullis' seven barbed teeth in the outer arch (x 60.8, down to z 26);
                the Lidless Eye in a pointed slot on the frontispiece (z 57..72); pass 6's horns
                over it went with the towers' (pass 7)
    parapet     steel spikes leaning out along the curtain's outer lip (z 68.5, 9.5 long), clear of
                the gatehouse
    the ramp    crooked impaling stakes on the ground either side
    scaffold    an orc scaffold against the +X face's +Y half (y 17..30, to z 44)
"""
from mathutils import Vector as V

X, Y = V((1, 0, 0)), V((0, 1, 0))
BAT = 1.0 / 45.0                           # the outer faces lean in 1.0 over 45
COURT = 26.4                               # the courtyard channel's line
# cracks: (u, z) polylines from the foot up, jagged; branches start part way up a crack
CRACKS = {
    "A": [(0.0, 0.3), (1.0, 3.5), (-0.3, 6.5), (1.6, 9.5), (1.0, 12.5), (2.6, 16.0)],
    "B": [(0.0, 0.3), (-1.2, 3.0), (-0.4, 6.0), (-2.0, 9.0), (-1.2, 12.0), (-2.8, 14.5)],
    "C": [(0.0, 0.3), (0.8, 2.8), (-0.6, 5.5), (0.6, 8.5), (-0.4, 10.5)],
}
BRANCHES = {                                # forks off the cracks, sideways: a network, not a flame
    "A": [[(-0.3, 6.5), (-2.4, 8.5), (-3.2, 11.5), (-5.2, 13.0)], [(1.6, 9.5), (3.6, 10.5), (5.0, 9.8)]],
    "B": [[(-0.4, 6.0), (1.8, 7.5), (2.6, 10.5), (4.4, 12.0)], [(-2.0, 9.0), (-4.2, 9.8)]],
    "C": [[(-0.6, 5.5), (-2.6, 6.8), (-3.4, 9.0)]],
}


def crack(kit, a, t, n, u, shape, scale=1.0, bat=0.0, w=0.9, z=0.0):
    pts = [(u + x * scale, z + 0.6 + zz * scale) for x, zz in shape]
    return kit.lava_crack(a, t, n, pts, w=w, bat=bat)


def lava(kit):
    """Broad open lava welling out from under the -Y face and the +X face's -Y half into basalt-kerbed
    channels, a channel round the courtyard, and a few broad seams up the outer faces."""
    out = kit.lava_channel([(-31.0, -53.8, 0.0), (-11.0, -53.9, 0.0), (9.0, -53.7, 0.0), (31.0, -53.8, 0.0)], w=2.8,
                           kerb=0.4, h=1.1, seed=1.0, sides=(-1,), pitch=6.0)
    out += kit.lava_channel([(54.3, -35.0, 0.0), (54.4, -25.0, 0.0), (54.2, -15.0, 0.0)], w=3.0, kerb=0.6, h=1.1,
                            seed=2.0, sides=(-1,), pitch=6.0)
    for pts in ([(COURT, -8.0, 1.0), (COURT, -COURT, 1.0), (-COURT, -COURT, 1.0), (-COURT, -10.5, 1.0)],
                [(-COURT, 10.5, 1.0), (-COURT, COURT, 1.0), (COURT, COURT, 1.0), (COURT, 8.0, 1.0)]):
        out += kit.lava_channel(pts, w=1.5, kerb=0.8, seed=pts[0][1], sides=(-1,), rafts=False, pitch=7.0)
    faces = [(V((0, -52.8, 0)), X, V((0, -1, 0)), [(-24.0, "A", 1.1), (-9.0, "C", 1.3), (6.0, "B", 1.15),
                                                     (21.0, "A", 0.9)]),                    # the -Y face
             (V((52.8, 0, 0)), Y, V((1, 0, 0)), [(-29.0, "B", 1.0), (-19.5, "A", 0.85)])]    # the +X face's -Y half
    for a, t, n, cracks in faces:
        for u, k, sc in cracks:
            out += crack(kit, a, t, n, u, CRACKS[k], sc, bat=BAT, w=2.2, z=0.0)
            out += crack(kit, a, t, n, u, BRANCHES[k][0], sc, bat=BAT, w=1.3, z=0.0)
    for p in ((-31.0, -53.8, 0.4), (31.0, -53.8, 0.4), (54.3, -35.0, 0.4), (-COURT, COURT, 1.4), (COURT, -COURT, 1.4)):
        kit.fire(p, "embers")
    for p in ((-12.0, -54.0, 1.0), (54.3, -25.0, 1.0)):   # thin smoke columns off the lava at the wall feet
        kit.fire(p, "smoke")
    return out


# the spiked parapet: (anchor on the outer lip, along, out, [(u0, u1, count)]) per side, z of the roots
PARAPET_Z = 68.5
PARAPET = [(V((0, -51.2, 0)), X, V((0, -1, 0)), [(-26.0, 26.0, 11)]),
           (V((0, 51.2, 0)), X, V((0, 1, 0)), [(-26.0, 26.0, 11)]),
           (V((-51.2, 0, 0)), Y, V((-1, 0, 0)), [(-26.0, 26.0, 11)]),
           (V((51.2, 0, 0)), Y, V((1, 0, 0)), [(-27.0, -14.5, 3), (14.5, 27.0, 3)])]


def gate(kit):
    out = kit.portcullis(V((60.8, 0, 0)), Y, X, -6.4, 6.4, 33.0, 40.5, teeth=7, r=0.6, length=1.4)
    out += kit.eye(V((57.3, 0, 0)), Y, X, 0.0, 57.0, 8.0, 15.0, d=0.0)
    return out


def parapet(kit):
    """Steel spikes along the curtain's outer lip, leaning out (EA's own spike cards behind them)."""
    out = []
    for a, t, n, runs in PARAPET:
        for u0, u1, count in runs:
            out += kit.spike_row(a, t, n, u0, u1, PARAPET_Z, 9.5, count, d=0.0, lean=0.45, r=0.7, tag="steel")
    return out


def ramp(kit):
    """Crooked impaling stakes either side of the ramp, leaning out."""
    out = []
    for sy in (-1, 1):
        for i, (x, y, lx, ly, L) in enumerate(((62.5, 20.0, 0.4, 0.3, 13.0), (69.0, 23.5, 0.55, 0.35, 12.0))):
            d = V((lx, ly * sy, 1.0)).normalized()
            out += kit.stake(V((x, sy * y, 1.3)), d, L, r=0.65, barbs=1, seed=i + sy)
    return out


def scaffold(kit):
    out = kit.scaffold(V((53.2, 17.0, 0.7)), Y, X, 13.0, 4.2, 44.0, levels=4)
    return out


def build(kit):
    return lava(kit) + gate(kit) + parapet(kit) + ramp(kit) + scaffold(kit)
