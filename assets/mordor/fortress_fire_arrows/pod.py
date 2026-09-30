"""The fire arrows' pod (Blender side): the citadel's crown in small over the gate.

    claw        six jagged spikes (the crowns' Horn: steel outer edge, teeth hooking up, a hook
                down, a lava seam on the tall three) from inside the rim (r 4.4, z 79) between EA's
                twelve, leaning in over the fire: the tall to z 95.5 (EA's pod tops at 89.8)
    embers      a heap of embers on EA's bed, a real fire in it ("brazier": EA's FireTorch and a black
                smoke; EA's own flame cards burn above it)
    legs        a hooked barb off each of EA's eight legs, halfway up
"""
import math

from mathutils import Vector as V

from ..shapes_addons import claw, leg_barb

AXIS = V((42.1, 0.0, 0.0))                      # the pod's axis (its rim is centred here, not on EA's bone)
FOOT = V((43.12, 0.06, 60.0))                   # the legs' feet are centred on EA's bone
GAPS = (17.0, 85.0, 141.0, -167.0, -113.0, -52.0)     # between EA's rim spikes
LEGS = ((0, 8.2), (50, 7.8), (97, 9.4), (140, 9.3), (180, 10.0), (-140, 9.3), (-97, 9.4), (-50, 7.8))


def build(kit):
    spikes = [(deg, 4.4, 16.0 if i % 2 == 0 else 11.5, 2.9 if i % 2 == 0 else 3.4) for i, deg in enumerate(GAPS)]
    out = claw(kit, AXIS, 79.0, spikes, w=0.85)
    out.append(kit.facet_lump(AXIS + V((0, 0, 81.2)), 2.2, "ember"))
    kit.fire(AXIS + V((0, 0, 82.0)), "brazier")
    for deg, r in LEGS:
        d = V((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0))
        p = FOOT + d * r
        q = AXIS + d * 4.8 + V((0, 0, 73.5))
        out += leg_barb(kit, p, q, 0.5, d * 0.7 + V((0, 0, 0.7)), 3.4, r=0.42)
    return out
