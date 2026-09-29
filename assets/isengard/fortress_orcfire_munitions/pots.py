"""The orcfire munitions (Blender side), IBFORCFIRE mesh coordinates (identity bone; the citadel's
frame). EA's five fire-pots (probed 2026-09-29): an eight-sided drum with four curved fins crossed
through it, EA's fire cards (MBFDPF, MBFDPFG) and smoke on GLOWBONE01..05 above each:

    the four tower tops   drums r 3.6 at (+-37.5, +-37.4), z 80.2..89.9, fins on the diagonals to z 93.7
    the gatehouse         a drum r 4.2 at (61.0, 0.0), z 52.7..66.6, fins on the axes to z 71

Each pot made a war-engine's fire-pot: a riveted iron rim, a silver lip and iron spikes round the
drum's mouth, an
ember band, four knife blades between the fins, and orcfire jars (small iron-bound pots) stacked at
its foot; real fire at each mouth. Kept clear: EA's fire cards (they stand over the mouths), the
citadel's spikes along the tower tops' edges (9 from the pots) and its collars on the points."""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z

from .. import shapes_addons as A

# (centre, drum radius, foot z, mouth z, fin axis degrees, scale)
POTS = [((37.5, 37.4), 3.6, 80.2, 89.9, 45.0, 1.0), ((37.5, -37.4), 3.6, 80.2, 89.9, 45.0, 1.0),
        ((-37.5, 37.4), 3.6, 80.2, 89.9, 45.0, 1.0), ((-37.5, -37.4), 3.6, 80.2, 89.9, 45.0, 1.0),
        ((61.0, 0.0), 4.2, 52.7, 66.6, 0.0, 1.2)]


def pot(kit, c, r, z0, z1, fins, s):
    cx, cy = c
    out = kit.hoop((cx, cy), z1 - 0.5, r + 0.05, h=1.3, th=0.55, inner=0.8, k=8, rivets=2, tag="iron", closed=True)
    out += kit.hoop((cx, cy), z1 + 0.25, r + 0.05, h=0.3, th=0.7, inner=0.8, k=8, rivets=False, tag="trim", closed=True)
    out += kit.hoop((cx, cy), z0 + (z1 - z0) * 0.42, r + 0.05, h=0.9, th=0.3, inner=0.8, k=8, rivets=False, tag="ember", closed=True)
    for i in range(8):                                  # spikes round the mouth
        a = math.radians(fins + 22.5 + 45.0 * i)
        d = V((math.cos(a), math.sin(a), 0))
        out += A.spur(kit, V((cx, cy, 0)) + d * (r + 0.5), d, z1 + 0.1, 1.6 * s, r=0.2 * s, lean=1.6)
    for i in range(4):                                  # blades between the fins, jars at the foot
        a = math.radians(fins + 45.0 + 90.0 * i)
        d = V((math.cos(a), math.sin(a), 0))
        out += kit.blade(V((cx, cy, 0)) + d * (r - 0.4), d, z1 - 5.0 * s, z1 + 1.0 * s, 1.0 * s, 1.8 * s, w=0.45 * s,
                         tip=2.6 * s, back=0.8)
        j = V((cx, cy, z0)) + d * (r + 0.9 * s)
        out += A.cauldron(kit, j, 0.7 * s, 1.4 * s, k=6, spikes=False, legs=False)
    kit.fire(V((cx, cy, z1 + 0.3)), "brazier")
    return out


def build(kit):
    out = []
    for c, r, z0, z1, fins, s in POTS:
        out += pot(kit, c, r, z0, z1, fins, s)
    return out
