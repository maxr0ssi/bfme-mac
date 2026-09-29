"""The Isengard citadel's foundry (Blender side), pass 7: two matching blades flank EA's back wedge
tower (-X, +Y) - the triangle in the middle of the RTS view - mirrored about the tower's axis in
that view (Max: "whatever you put on either side of that triangle, so have 2").

EA's tower stays whole and in sight: its arcaded faces, its triangular top and the orcfire
upgrade's cauldron on it ((-37.4, 37.7), z 80.2..93.7, fire cards to z 110 over x -51.4..-23.3,
y 23.5..51.8). The blades are lozenges in plan (sharp edges front and back, EA's wedge) with a
flared, spurred foot, two set-back steps, three layered fins on every face, silver edges, ember
slits and a needle tip (shapes_spire.py):

    BL, BR  the pair: axis along the view's horizontal (52 degrees), broad faces to the camera,
            to z 120, the White Hand in a pointed-arch slot on each one's outer face; BL on the
            -X wall's foot (-62, 39), clear of the burning forges (|y| < 29), BR its mirror
            (-44.6, 61.3) on the +Y wall's foot. A mirror of pass 6's single blade would have
            stood inside the burning forges.
    B3      a lesser blade clasping the tower's courtyard corner from a corbel at z 24 (over the
            excavations upgrade's rails and derrick, z 13..23), to z 84: a small Hand in a
            pointed-arch slot, the crane boom off its front edge
    the great chimney out of EA's tower's own point, on the tower's axis in the view, to z 108

Nothing above z 80 enters the fire cards' box; no upgrade's vertex lies inside the new solids.
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz

from ..shapes_spire import BROAD, scale

# (centre, axis degrees, half-length, half-width, z0, z1, lean at the top, flare)
VIEW = 52.0                                          # the RTS view's horizontal (camera azimuth -38)
BL = ((-62.0, 39.0), VIEW, 9.0, 4.5, 0.0, 120.0, (2.0, 0.0), 1.2)
BR = ((-44.6, 61.3), VIEW, 9.0, 4.5, 0.0, 120.0, (0.0, -2.0), 1.2)     # BL mirrored about the tower's axis
B3 = ((-17.5, 40.5), 0.0, 8.5, 5.0, 24.0, 84.0, (-1.2, 0.8), 1.12)
CHIMNEY = ((-60.6, 60.6), 135.0, 4.4, 3.0, 0.0, 108.0)


def blades(kit):
    out = []
    for c, axis, L, W, z0, z1, lean, flare in (BL, BR):
        out += kit.blade_tower(c, axis, L, W, z0, z1, lean=lean, flare=flare, fins=3, slits=(0.42, 0.52, 0.62, 0.72),
                               profile=BROAD, fin_reach=1.3, slit_w=1.1)
    c, axis, L, W, z0, z1, lean, flare = B3
    out += kit.blade_tower(c, axis, L, W, z0, z1, lean=lean, flare=flare, fins=3, slits=(0.5, 0.62), slit_w=1.0)
    foot = kit.lozenge(c, axis, L * flare, W * flare, z0)          # the corbel it springs from
    out.append(loft([[V((c[0] + L * 0.4, c[1], z0 - 3.2))] * 4, foot], ["stoneA"], cap0=("stoneA", False),
                    cap1=("stoneA", False)))
    c, axis, L, W, z0, z1 = CHIMNEY
    out += kit.needle_stack(c, axis, L, W, z0, z1, collar=0.62)
    return out


def b3_face(z):
    """(point on B3's face toward the camera at height z, t along it, n out): the face from its
    front vertex (+X) to its -Y vertex."""
    c, axis, L, W, z0, z1, lean, flare = B3
    f = (z - z0) / (z1 - z0)
    s = scale(f)
    ctr = V((c[0] + lean[0] * f, c[1] + lean[1] * f, 0))
    a, b = ctr + V((L * s, 0, 0)), ctr + V((0, -W * s, 0))
    t = (b - a).normalized()
    n = V((t.y, -t.x, 0))
    if n.dot((a + b) / 2 - ctr) < 0:
        n = -n
    return (a + b) / 2, t, n


def hand(kit):
    """The White Hand in a pointed-arch slot on B3's face to the camera, z 36..54."""
    m, t, n = b3_face(45.0)
    w, z0, h = 5.6, 36.0, 18.0
    head = (w / 2) / math.tan(math.radians(35.0) / 2) * 0.5
    poly = [(-w / 2, z0), (w / 2, z0), (w / 2, z0 + h - head), (0, z0 + h), (-w / 2, z0 + h - head)]
    out = [prism_uz(m, t, n, poly, -1.2, 0.9, ["trim"] * 5, "stoneB", None)]
    for (u0, za), (u1, zb) in zip(poly, poly[1:] + poly[:1]):
        out.append(kit.beam(m + t * u0 + Z * za + n * 1.0, m + t * u1 + Z * zb + n * 1.0, 0.3, "trim"))
    out += kit.hand(m, t, n, 0.0, z0 + 2.4, 5.4, 0.9, th=0.3, back="mark")
    return out


def blade_face(blade, z, side):
    """(point on a blade's face to the camera at height z, t, n): side +1 the face from its front
    vertex to its +axis end, -1 to its -axis end."""
    c, axis, L, W, z0, z1, lean, flare = blade
    f = (z - z0) / (z1 - z0)
    s = scale(f, BROAD)
    a = math.radians(axis)
    d, p = V((math.cos(a), math.sin(a), 0)), V((-math.sin(a), math.cos(a), 0))
    ctr = V((c[0] + lean[0] * f, c[1] + lean[1] * f, 0))
    front, end = ctr - p * W * s, ctr + d * (side * L * s)
    t = (end - front).normalized()
    n = V((t.y, -t.x, 0))
    if n.dot((front + end) / 2 - ctr) < 0:
        n = -n
    return (front + end) / 2, t, n


def big_hands(kit):
    """The White Hand in a pointed-arch slot on each blade's outer face, z 70..94, above the
    walls where the RTS camera sees it."""
    out = []
    for blade, side in ((BL, -1), (BR, 1)):
        m, t, n = blade_face(blade, 82.0, side)
        w, z0, h = 6.2, 70.0, 24.0
        head = (w / 2) / math.tan(math.radians(35.0) / 2) * 0.5
        poly = [(-w / 2, z0), (w / 2, z0), (w / 2, z0 + h - head), (0, z0 + h), (-w / 2, z0 + h - head)]
        out.append(prism_uz(m, t, n, poly, -0.9, 1.6, ["trim"] * 5, "stoneB", None))   # not through the thin blade
        for (u0, za), (u1, zb) in zip(poly, poly[1:] + poly[:1]):
            out.append(kit.beam(m + t * u0 + Z * za + n * 1.7, m + t * u1 + Z * zb + n * 1.7, 0.35, "trim"))
        out += kit.hand(m, t, n, 0.0, z0 + 3.0, 6.0, 1.6, th=0.4, back="mark")
    return out


def molten_fall(kit):
    """A furnace hearth on the +Y walk, a runnel to the walk's inner edge and molten metal pouring
    down the wall's inner face into a glowing pool (clear of the excavations)."""
    hearth = V((-24.5, 57.2, 48.5))
    out = kit.hearth(hearth, V((1, 0, 0)), V((0.34, -0.94, 0)), w=4.4, d=3.2, h=2.4, hood=3.8)
    lip = V((-19.0, 53.6, 48.9))
    out += kit.runnel([hearth + V((1.6, -1.8, 0.4)), lip], 0.7)
    out.append(kit.tube([lip + Z * 0.3, V((-18.8, 52.6, 30.0)), V((-18.6, 52.0, 1.0))], [0.55, 0.7, 0.9], "ember", k=4,
                        cap0="ember", cap1="ember"))
    out += kit.floor_grate(V((-18.4, 51.2, 0.7)), V((1, 0, 0)), 3.2, 2.6)
    return out


def crane(kit):
    """A crane boom off B3's front edge at z 68 rising over the courtyard (the diagonal against
    the sky), a pointed head, a crucible on its chain (clear of the excavations, z 68)."""
    c, axis, L, W, z0, z1, lean, flare = B3
    f = (68.0 - z0) / (z1 - z0)
    s = scale(f)
    root = V((c[0] + lean[0] * f + L * s - 0.4, c[1] + lean[1] * f, 68.0))
    tip = root + V((16.0, 0.0, 17.0))
    t = V((0, 1, 0))
    out = []
    for sgn in (-1, 1):
        out.append(kit.beam(root + t * (sgn * 0.8), tip + t * (sgn * 0.3), 0.55, "iron"))
    for q in (0.3, 0.6, 0.85):
        out.append(kit.beam(root.lerp(tip, q) - t * 0.7, root.lerp(tip, q) + t * 0.7, 0.2, "trim"))
    out.append(kit.beam(tip, tip + V((1.6, 0, 2.6)), 0.8, "trim", 0.0))
    stay = V((c[0] + lean[0] * 0.9, c[1] + lean[1] * 0.9, z1 - 7.0))
    out += kit.chain(stay, tip, link=2.4)
    out += kit.chain(tip - Z * 1.0, tip - Z * 6.0)
    for sgn in (-1, 1):
        out += kit.chain(tip - Z * 6.0, tip - Z * 8.0 + t * (sgn * 1.8), link=1.2)
    out += kit.crucible(tip - Z * 11.2, 2.0, 3.0)
    return out


def slots(kit):
    """Glowing pits in the gaps between the blades' feet."""
    out = []
    for x, y, ang in ((-68.5, 46.5, 142.0), (-47.0, 68.0, 128.0)):
        out += kit.floor_grate(V((x, y, 0.7)), V((math.cos(math.radians(ang + 90)), math.sin(math.radians(ang + 90)), 0)),
                               3.2, 2.4)
    return out


def bellows_house(kit):
    """A house on the +Y walk, a steep gabled roof, a great bellows on its ridge, a fire grate in
    its end; its pipe runs to the side stack (yard.py)."""
    base = V((-17.5, 57.5, 48.5))
    x = V((1, 0, 0))
    y = V((0, 1, 0))
    w, dp, h = 6.5, 7.0, 6.0
    P = lambda u, d, z: base + y * u + x * d + Z * z          # noqa: E731
    rings = [[P(-w / 2, -1.0, z), P(w / 2, -1.0, z), P(w / 2, dp, z), P(-w / 2, dp, z)] for z in (-0.5, h)]
    out = [loft(rings, ["stoneA"] * 4, cap0=("stoneA", False), cap1=("stoneA", False))]
    ridge = h + (w / 2) / math.tan(math.radians(35.0) / 2) * 0.6
    out.append(loft([[P(-w / 2 - 0.4, -1.4, h), P(w / 2 + 0.4, -1.4, h), P(0, -1.4, ridge)],
                     [P(-w / 2 - 0.4, dp + 0.4, h), P(w / 2 + 0.4, dp + 0.4, h), P(0, dp + 0.4, ridge)]],
                    [["iron", "iron", "iron"]], cap0=("stoneA", True), cap1=("stoneA", True)))
    out.append(kit.beam(P(0, -1.4, ridge + 0.2), P(0, dp + 0.4, ridge + 0.2), 0.3, "trim"))
    for d in (-1.4, dp + 0.4):
        out.append(kit.beam(P(0, d, ridge), P(0, d, ridge + 3.0), 0.3, "trim", 0.0))
    out += kit.fire_grate(P(0, dp + 0.2, 0.2), y, x, w=3.0, h=2.6, d=1.4)
    out += kit.bellows(P(0, dp * 0.5, ridge - 1.2), -x, 1.5)
    return out


def build(kit):
    return blades(kit) + hand(kit) + big_hands(kit) + molten_fall(kit) + crane(kit) + slots(kit) + bellows_house(kit)
