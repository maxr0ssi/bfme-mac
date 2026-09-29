"""The Isengard citadel's foundry tower (Blender side), pass 3: EA's back wedge tower (-X, +Y) built
up in EA's own Gothic language, in black stone with silver edges.

    undercroft  z 0..24: a solid back half, and on the courtyard side four piers, pointed arches
                at the ends and tier 1 overhanging the middle (the excavations upgrade's posts,
                rails and derrick, z 0..23, stand under it; furnace mouths glow in the back wall)
    tier 1      z 24..50: an octagon, lancet slits with ember light, the piers rising as stepped
                buttresses to spiked pinnacles, merlons with spikes on its ledge
    tier 2      z 50..80, set back: lancets, the White Hand in a pointed-arch panel on the
                courtyard face, merlons and spikes and a pinnacle on every corner of its roof
    the roof    z 80, open: the orcfire upgrade's cauldron (-37.4, 37.7, z 80.2..93.7, fire to
                110) stands on it and EA's own tower top (the spire, z 80..91.4) rises out of it
    on it       the great stack on the back corner, a crane boom rising diagonally over the
                courtyard with a crucible on its chain, a bellows house on the +Y walk

Measured (EA's IBFORTRESS): the wedge tower needs an apothem of 17-20 about C up to z 80 on the
courtyard faces; the excavations' posts stand 11-13 from C on the courtyard side, z 0..20.8; the
burning forges' body reaches 21.5 from C on the 247.5-degree face at z 32.
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz

C = V((-43.0, 43.0, 0.0))
NORMALS = [22.5 + 45.0 * i for i in range(8)]       # face i's normal (degrees); vertex i between faces i, i+1
T1 = [22.5, 22.5, 22.5, 22.5, 22.5, 20.5, 22.5, 22.5]   # tier 1 apothems (the 247.5 face held in: the forges)
T2 = [20.3] * 8                                      # tier 2 (the wedge tower needs 20 at z 72..80)
Z0, Z1, Z2, TOP = 0.0, 24.0, 50.0, 80.0
FRONT = (4, 5, 7, 0)                                 # piers on the courtyard side: 225, 270, 0, 45 degrees; none at
                                                     # 315, where the excavations' derrick (z 20..23) and rails (z 13) stand
HAND_FACE, BELLOWS_FACE = 7, 0                       # faces 337.5 and 22.5
STACK = ((-53.5, 53.5), 6.0, TOP, 118.0)


def nrm(i):
    a = math.radians(NORMALS[i % 8])
    return V((math.cos(a), math.sin(a), 0))


def vertex(aps, i, z):
    """The corner between faces i and i+1 of the octagon with apothems aps, at height z."""
    n0, n1 = nrm(i), nrm(i + 1)
    a0, a1 = aps[i % 8], aps[(i + 1) % 8]
    det = n0.x * n1.y - n0.y * n1.x
    x = (a0 * n1.y - a1 * n0.y) / det
    y = (n0.x * a1 - n1.x * a0) / det
    return C + V((x, y, z))


def ring(aps, z, grow=0.0):
    return [vertex([a + grow for a in aps], i, z) for i in range(8)]


def face(aps, i):
    """(anchor at the ground under face i's middle, t along it, n out)."""
    n = nrm(i)
    return C + n * aps[i], V((-n.y, n.x, 0)), n


def tiers(kit):
    out = []
    back = [vertex(T1, i, 0) for i in (0, 1, 2, 3, 4)]           # 45 .. 225 degrees: the undercroft's solid half
    out.append(loft([[p + Z * 0.0 - Z * 0.05 for p in back], [p + Z * Z1 for p in back]],
                    [["stoneA", "stoneA", "stoneA", "stoneA", "stoneB"]], cap0=("stoneA", False), cap1=("stoneA", False)))
    out.append(loft([ring(T1, Z1), ring(T1, Z2)], ["stoneA"], cap0=("stoneB", True), cap1=("stoneA", True)))
    out.append(loft([ring(T2, Z2 - 0.5), ring(T2, TOP)], ["stoneA"], cap0=("stoneA", False), cap1=("stoneB", True)))
    for aps, z in ((T1, Z1 + 0.9), (T1, Z2 - 1.6), (T2, TOP - 1.6)):  # silver string courses, open ends buried
        out.append(loft([ring(aps, z - 0.5, -0.4), ring(aps, z - 0.1, 0.9), ring(aps, z + 0.5, 0.9), ring(aps, z + 0.8, -0.4)],
                        ["trim", "trim", "trim"], cap0=("trim", False), cap1=("trim", False)))
    return out


def arcade(kit):
    """Pointed arches between the courtyard piers, z 0..24, silver-edged."""
    out = []
    for i in (4, 7):                                   # between the piers at 225-270 and 0-45 degrees
        p0, p1 = vertex(T1, i, 0), vertex(T1, i + 1, 0)
        t = (p1 - p0).normalized()
        n = nrm(i + 1)
        a, b = p0 + t * 2.2, p1 - t * 2.2
        spring, apex = 15.5, Z1 - 0.6
        m = (a + b) / 2
        for s, e in ((a, m), (b, m)):
            pts = [s + Z * spring, s.lerp(e, 0.45) + Z * (spring + (apex - spring) * 0.8), e + Z * apex]
            out.append(kit.tube(pts, [0.9, 0.85, 0.8], "stoneA", k=4, cap0="stoneA", cap1="stoneA", phase=math.pi / 4))
            out.append(kit.tube([p + n * 0.9 + Z * 0.5 for p in pts], [0.3, 0.3, 0.3], "trim", k=4, cap0="trim", cap1="trim"))
    return out


CORBELLED = {5: 15.5}                                # pier 5 hangs from z 15.5: the excavations' rails run under it (z 13)


def buttress(kit, i):
    """A stepped buttress on vertex i from the ground (or corbelled out from CORBELLED[i]): three
    stages set back, a spiked pinnacle."""
    v = vertex(T1, i, 0)
    d = (v - C).normalized()
    s = V((-d.y, d.x, 0))
    out = []
    foot = CORBELLED.get(i)
    if foot is not None:                                # a corbel: tapering down to a point
        base = [v - d * 3.0 + s * 2.0, v + d * 3.8 + s * 2.0, v + d * 3.8 - s * 2.0, v - d * 3.0 - s * 2.0]
        out.append(loft([[v - d * 1.5 + Z * (foot - 2.5)] * 4, [p + Z * foot for p in base]], ["stoneA"],
                        cap0=("stoneA", False), cap1=("stoneA", False)))
    for z0, z1, depth, w in ((foot if foot is not None else Z0 - 0.05, Z1, 3.8, 2.0), (Z1, 38.0, 3.0, 1.75),
                             (38.0, Z2 + 3.0, 2.2, 1.5)):
        ring0 = [v - d * 3.0 + s * w, v + d * depth + s * w, v + d * depth - s * w, v - d * 3.0 - s * w]
        top = [p + Z * z1 for p in ring0]
        top[1], top[2] = top[1] - Z * min(1.6, depth * 0.5), top[2] - Z * min(1.6, depth * 0.5)   # a weathered slope
        out.append(loft([[p + Z * z0 for p in ring0], top], ["stoneA", "trim", "stoneA", "stoneA"],
                        cap0=("stoneA", False), cap1=("stoneA", True)))
    c = v + d * 1.2 + Z * (Z2 + 2.4)
    out.append(kit.beam(c, c + Z * 5.5, 1.0, "stoneA"))
    out.append(kit.beam(c + Z * 5.5, c + Z * 12.5, 1.05, "stoneA", 0.0))
    out.append(kit.beam(c + Z * 5.3, c + Z * 6.1, 1.25, "trim"))
    return out


def pinnacles(kit):
    """A spiked pinnacle on every corner of tier 2's roof, merlons with spikes between them."""
    out = []
    for i in range(8):
        v = vertex(T2, i, TOP)
        d = (v - C).normalized()
        c = v - d * 0.6
        out.append(kit.beam(c - Z * 0.5, c + Z * 5.0, 1.1, "stoneA"))
        out.append(kit.beam(c + Z * 5.0, c + Z * 12.0, 1.15, "stoneA", 0.0))
        out.append(kit.beam(c + Z * 4.8, c + Z * 5.6, 1.35, "trim"))
        out.append(kit.beam(c + Z * 10.5, c + Z * 13.5, 0.35, "trim", 0.0))
    for aps, z, h in ((T1, Z2, 3.4), (T2, TOP, 4.2)):
        for i in range(8):
            a, t, n = face(aps, i)
            if aps is T1 and i in (1, 2, 3):
                continue                                # the back: hidden, and the walls run in there
            half = (vertex(aps, i - 1, 0) - vertex(aps, i, 0)).length / 2
            for u in (-half * 0.45, half * 0.45):
                poly = [(u - 1.3, z - 0.3), (u + 1.3, z - 0.3), (u + 1.3, z + h), (u - 1.3, z + h)]
                inset = 0.0
                out.append(prism_uz(a + n * (-inset), t, n, poly, -1.2, 0.3, ["stoneA"] * 4, "trim", "stoneA"))
                if aps is T1:                           # tier 2's merlons have the pinnacles beside them
                    p = a + t * u + n * (-inset - 0.45) + Z * (z + h - 0.2)
                    out.append(kit.beam(p, p + (Z + n * 0.25).normalized() * 3.2, 0.4, "iron", 0.0))
    return out


def shafts(kit):
    """Silver shafts up tier 2's corners that the camera sees (EA's towers are ribbed)."""
    out = []
    for i in (4, 5, 6, 7, 0):
        v = vertex(T2, i, 0)
        d = (v - C).normalized()
        out.append(kit.beam(v + d * 0.25 + Z * Z2, v + d * 0.25 + Z * (TOP - 2.2), 0.42, "trim"))
    return out


def lancet(kit, aps, i, u, z, w, h, depth=0.9):
    """A lancet: a pointed ember slit in a silver frame standing `depth` proud of face i."""
    a, t, n = face(aps, i)
    poly = [(u - w / 2, z), (u + w / 2, z), (u + w / 2, z + h - w * 0.9), (u, z + h), (u - w / 2, z + h - w * 0.9)]
    out = [prism_uz(a, t, n, poly, -0.8, 0.15, ["ember"] * 5, "ember", None)]
    fw = 0.5
    edges = list(zip(poly, poly[1:] + poly[:1]))
    for (u0, z0), (u1, z1) in edges:
        p, q = a + t * u0 + Z * z0 + n * (depth * 0.5), a + t * u1 + Z * z1 + n * (depth * 0.5)
        out.append(kit.beam(p, q, fw * 0.6, "trim"))
    return out


def hand(kit):
    """The White Hand in a pointed-arch panel on tier 2's courtyard face, z 56..74."""
    a, t, n = face(T2, HAND_FACE)
    w, z0, h = 9.5, 55.5, 18.0
    poly = [(-w / 2, z0), (w / 2, z0), (w / 2, z0 + h - w * 0.8), (0, z0 + h), (-w / 2, z0 + h - w * 0.8)]
    out = [prism_uz(a, t, n, poly, -0.6, 1.1, ["trim"] * 5, "stoneB", None)]
    for (u0, z1), (u1, z2) in zip(poly, poly[1:] + poly[:1]):
        out.append(kit.beam(a + t * u0 + Z * z1 + n * 1.2, a + t * u1 + Z * z2 + n * 1.2, 0.35, "trim"))
    out += kit.hand(a, t, n, 0.0, z0 + 2.6, 7.6, 1.1, th=0.35, back="mark")
    return out


def windows(kit):
    out = []
    for i in (5, 6, 0):                                  # tier 1: the faces the camera sees
        out += lancet(kit, T1, i, -2.4, 30.0, 1.7, 12.0) + lancet(kit, T1, i, 2.4, 30.0, 1.7, 12.0)
    for i in (5, 6, 0):                                  # tier 2 (the Hand has face 7)
        out += lancet(kit, T2, i, 0.0, 58.0, 2.2, 15.0)
    return out


def undercroft(kit):
    """Two furnace mouths in the undercroft's back wall, glowing through the arches."""
    out = []
    p0, p1 = vertex(T1, 4, 0), vertex(T1, 0, 0)          # the back wall: the chord from 225 to 45 degrees
    t = (p1 - p0).normalized()
    n = V((t.y, -t.x, 0))                                # toward the courtyard (315 degrees)
    for f in (0.3, 0.7):
        out += kit.fire_grate(p0.lerp(p1, f) + n * 1.2 + Z * 0.3, t, n, w=6.0, h=7.0, d=2.6)
    return out


def crane(kit):
    """A crane boom from the roof's +X corner rising diagonally over the courtyard (the silhouette
    against the sky), a backstay to an A-frame on the roof, a crucible on its hoist chain."""
    root = vertex(T2, 7, TOP + 1.0) - V((1.0, 0, 0))     # the corner at 0 degrees
    tip = root + V((17.0, 0, 18.0))
    t = V((0, 1, 0))
    out = []
    for s in (-1, 1):
        out.append(kit.beam(root + t * (s * 0.9), tip + t * (s * 0.3), 0.62, "iron"))
    for f in (0.25, 0.5, 0.75):
        out.append(kit.beam(root.lerp(tip, f) - t * 0.8, root.lerp(tip, f) + t * 0.8, 0.22, "trim"))
    mast = root - V((6.0, 0, 0))
    for s in (-1, 1):
        out.append(kit.beam(mast + t * (s * 2.2), mast + V((0.8, 0, 9.0)), 0.35, "iron"))
    out += kit.chain(mast + V((0.8, 0, 9.0)), tip, link=2.2)
    out.append(kit.tube([tip - t * 0.7, tip + t * 0.7], [1.0, 1.0], "iron", k=8, cap0="trim", cap1="trim"))
    out += kit.chain(tip - Z * 1.0, tip - Z * 7.0)
    for s in (-1, 1):
        out += kit.chain(tip - Z * 7.0, tip - Z * 9.0 + t * (s * 1.9), link=1.2)
    out += kit.crucible(tip - Z * 12.4, 2.1, 3.2)
    return out


def bellows_house(kit):
    """A timber-and-iron house on the +Y walk against tier 1, a great bellows on its roof, a fire
    grate in its end; its pipe runs along the walk to the side stack (yard.py)."""
    a, t, n = face(T1, BELLOWS_FACE)
    base = a + Z * 48.5
    P = lambda u, d, z: base + t * u + n * d + Z * z          # noqa: E731
    w, dp, h, u0 = 8.0, 8.0, 7.5, 2.5
    rings = [[P(u0 - w / 2, -1.0, z), P(u0 + w / 2, -1.0, z), P(u0 + w / 2, dp, z), P(u0 - w / 2, dp, z)] for z in (-0.5, h)]
    out = [loft(rings, ["stoneA"] * 4, cap0=("stoneA", False), cap1=("iron", True))]
    for u in (u0 - w / 2, u0 + w / 2):
        for d in (-1.0, dp):
            out.append(kit.beam(P(u, d, -0.5), P(u, d, h + 0.2), 0.4, "trim"))
    out += kit.fire_grate(P(u0, dp + 0.2, 0.2), t, n, w=3.2, h=2.6, d=1.4)
    out += kit.bellows(P(u0, dp * 0.45, h), -n, 2.1)
    return out


def stack(kit):
    (x, y), r, z0, z1 = STACK
    return kit.chimney((x, y), r, z0 - 2.0, z1, k=8, bands=3, foot=z0 + 12.0, collar=z0 + 26.0)


def build(kit):
    out = tiers(kit) + arcade(kit) + pinnacles(kit) + shafts(kit) + windows(kit) + hand(kit) + undercroft(kit)
    for i in FRONT:
        out += buttress(kit, i)
    return out + crane(kit) + bellows_house(kit) + stack(kit)
