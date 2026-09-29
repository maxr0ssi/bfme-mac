"""The burning forges' tower (Blender side), IBFBFORGES mesh coordinates (identity bone; the
citadel's frame). EA's forge (sliced 2026-09-29): a battered block over the -X walk, x -62..-22,
y -22..21, to a platform at z 62 (x -58.4..-34, y -18.6..20.4) split by the wheel's slot (|y| < 3.8);
a round stack at (-37.7, -13.0), r 4.8, open at z 85.3; a timber frame on four posts at x -52 / -34,
y +-6.5 to a roof at z 112.4 with a cage of spikes under it (z 96..111) and corner spikes to z 124;
a chute down the +X face from (y -14.7, z 75.7) to (y 8, z 40.8); pikes and a rag on the -Y side.

Kept clear: the wheel (a disc r 16.4 about (-42.06, 4.52, 66.22) turning about y, y -6.2..15.2,
its hub drum at y 9..15), the forge worker at B_URUKALIGN (-50.8, 12.8, 63.4), the wizard's tower
(r < 21.8 about the origin, its piers to r 28.8 on the diagonals) and the excavations' drum
(r < 54.2, z < 20.8).

    stack     EA's round stack carried on as the citadel's needle chimney to z 138, its fire
    beacon    a faceted fire-pot on the frame's roof, pointed merlons along the roof's edges
    forge     a hearth, an anvil with glowing work and a bellows on the platform's -Y half
    chute     molten metal running down EA's chute into a glowing pool
    face      three knife fins and two ember vents on the -Y face, above the excavations' disc
"""
from mathutils import Vector as V

from sagekit.blender.geometry import Z

from .. import shapes_addons as A

STACK = ((-37.7, -13.0), 4.8, 85.3)
ROOF = ([(-52.0, -7.0), (-34.0, -7.0), (-34.0, 7.0), (-52.0, 7.0)], 112.4)


def stack(kit):
    """EA's round stack carried on as the citadel's needle chimney: a lozenge flange over its rim
    (z 84), the shaft past the frame's roof (112.4) to a crown of blades round a glowing throat at
    z 138. (A pair of blades on the block's -X corners, tried first, stood beside the citadel's own
    pair and read as a bundle of needles; one tall stack reads as the forge.)"""
    (cx, cy), r, top = STACK
    return kit.needle_stack((cx, cy), 0.0, 5.6, 5.0, top - 1.3, 138.0, collar=0.3)


def beacon(kit):
    pts, z = ROOF
    out = A.cauldron(kit, V((-43.0, 0.0, z - 0.2)), 3.0, 3.6, legs=False)
    kit.fire(V((-43.0, 0.0, z + 3.2)), "brazier")
    out += A.crown_blades(kit, pts, z, 4.0, per_edge=2, w=0.6, lean=0.0, corners=False, width=3.0)
    return out


def forge(kit):
    y, x = V((0, 1, 0)), V((1, 0, 0))
    out = kit.hearth(V((-54.0, -12.5, 62.0)), y, x, w=5.0, d=3.4, h=2.4, hood=4.0)
    anvil = V((-48.5, -15.5, 62.0))
    out += kit.anvil(anvil, x, 1.0) + kit.glowing_work(anvil + Z * 2.8, x, 1.0)
    kit.fire(anvil + Z * 3.3, "embers")
    out += kit.bellows(V((-54.0, -16.8, 62.4)), x, 0.9)
    out += kit.ingots(V((-49.0, -9.8, 62.0)), y, 2, 0.8)
    return out


def chute(kit):
    pts = [V((-27.4, -13.8, 75.5)), V((-27.4, -4.0, 53.2)), V((-28.3, 7.9, 41.6))]
    out = kit.runnel(pts, 0.8)
    out.append(kit.facet_lump(V((-28.4, 9.4, 41.0)), 1.6, "ember"))
    kit.fire(V((-28.4, 9.4, 41.8)), "crucible")
    return out


def face(kit):
    """Knife fins on the -Y face (y -20.2 .. -22.2, bowed) above the excavations' drum (its rim at
    z 20.8), and ember vents between them."""
    out = []
    a0, n = V((0, -19.2, 0)), V((0, -1, 0))
    for xx in (-55.0, -45.5, -36.0):
        out += kit.blade(a0 + V((xx, 0, 0)), n, 21.5, 57.0, 4.0, 4.0, w=1.3, tip=5.0, back=2.0)
    for xx in (-50.2, -40.8):
        out += kit.vent(V((xx, -22.4, 0)), V((1, 0, 0)), n, 0.0, 34.0, 3.0, 6.0, 0.0, bars=3)
    return out


def build(kit):
    return stack(kit) + beacon(kit) + forge(kit) + chute(kit) + face(kit)
