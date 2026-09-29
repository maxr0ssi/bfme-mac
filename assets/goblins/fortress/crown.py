"""The Goblin citadel's four spire towers (Blender side): EA's plated columns and horn-scaled
hoods kept whole, crowned with iron and bone.

EA's tower (WBFORTRESS mesh coordinates, centres (+-44.2, +-44.2)): an octagonal column of riveted
plates flaring from about 3 across at the ground to 11 at z 54 (its ribs at the octagon's
corners, toward the axes and the diagonals), a star collar with spikes on those corners to r 21 at
z 48-59, the black band of the glowing eyes (EYES, r 12.9, z 59.6-69.7: nothing may stand in
front of it), the hood's spikes (r 19 at z 68-70, at 22.5 + 45k degrees), the hood itself (half
14.1 at z 72, 10.3 at 76, 8.55 at 80, 5.9 at 88, 4.5 at 96) curving to its forked tip at z
111.6-115.9, each tower leaning its own way (AXES, measured). What is added:

    hoops      riveted iron bands round the hood (z 80) and round the column (z 42)
    horns      four great black horns from the hood at z 84 sweeping out and up to white tips
    tusks      four small bleached tusks between the great horns (z 76)
    spike      an iron spike rising from the hood's tip to z 136, a skull driven onto it
    trophy     a skull on an iron spike out of each column's outer corner, blood below it
    gibbet     the front towers: an iron arm out of the hood with a cage hung on a chain, a
               skeleton slumped inside; the back towers: a flayed hide hung on a hook
"""
import math

from mathutils import Vector as V

# the hood's half-width by height (its octagon faces toward the axes)
HOOD = [(72, 14.1), (76, 10.3), (80, 8.55), (84, 7.2), (88, 5.9), (92, 5.2), (96, 4.5), (100, 4.0), (104, 3.4),
        (108, 3.1)]
# where each tower's hood leans: {tower centre: [(z, cx, cy)]} (measured; the centre below)
AXES = {(44.2, -44.2): [(88, 44.1, -43.8), (96, 43.5, -44.9), (104, 42.7, -46.2), (108, 41.4, -47.5)],
        (44.2, 44.2): [(80, 45.1, 44.2), (88, 45.2, 44.0), (96, 44.0, 43.2), (104, 42.9, 42.1), (108, 43.7, 41.1)],
        (-44.2, 44.2): [(76, -45.6, 44.2), (88, -45.9, 44.3), (96, -46.4, 44.2), (104, -46.9, 44.1), (108, -47.1, 44.1)],
        (-44.2, -44.2): [(88, -43.9, -44.1), (96, -42.5, -43.5), (104, -41.1, -42.9), (108, -41.0, -43.6)]}
TOWERS = list(AXES)
# the column's corner radius by height (octagon corners toward the axes and diagonals)
COLUMN = [(0, 2.8), (5, 3.3), (20, 5.0), (35, 7.0), (45, 9.2), (50, 9.6), (54, 11.0)]
SPIKE_TOP, SKULL_Z, SKULL_S = 137.0, 121.5, 5.4
HORN_Z, HORN_LEN, HORN_R = 84.0, 18.5, 2.0
TUSK_Z = 75.6
GIBBET_Z = 88.0


def lerp_table(table, z):
    """Linear interpolation in a [(z, value...)] table, clamped at its ends."""
    if z <= table[0][0]:
        return table[0][1:] if len(table[0]) > 2 else table[0][1]
    for (z0, *a), (z1, *b) in zip(table, table[1:]):
        if z <= z1:
            f = (z - z0) / (z1 - z0)
            v = [x + (y - x) * f for x, y in zip(a, b)]
            return v if len(v) > 1 else v[0]
    return table[-1][1:] if len(table[-1]) > 2 else table[-1][1]


def axis(c, z):
    """The hood's centre at height z (the tower's own centre below the measured lean)."""
    table = [(0, c[0], c[1]), (84, c[0], c[1])] + AXES[c] if AXES[c][0][0] > 84 else [(0, c[0], c[1])] + AXES[c]
    x, y = lerp_table(table, z)
    return V((x, y, z))


def outward(c):
    """The tower's outward diagonal (away from the courtyard)."""
    return V((math.copysign(1, c[0]), math.copysign(1, c[1]), 0)).normalized()


def spike_path(c):
    a0, a1, a2 = axis(c, 96), axis(c, 104), axis(c, 108)
    lean = V(((a2 - a0).x, (a2 - a0).y, 0)) * 0.25
    mid = V((a2.x, a2.y, 0)) + lean + V((0, 0, SKULL_Z))
    return [a0, a1, a2 + V((0, 0, 3.0)), mid, V((mid.x, mid.y, SPIKE_TOP)) + lean * 0.2]


def skull_centre(c):
    return spike_path(c)[3]


def build(kit, c):
    front = c[0] > 0
    out = []
    # riveted hoops round the hood and the column
    for z in (80.0,):
        half = lerp_table(HOOD, z)
        out += kit.hoop(axis(c, z), z, (half + 0.1) / math.cos(math.pi / 8), h=1.9, th=0.75, inner=1.5, rivets=2)
    for z in (42.0,):
        out += kit.hoop(c, z, lerp_table(COLUMN, z) + 0.15, h=1.7, th=0.7, inner=1.4, phase=0.0)
    # the great horns and the ring of small tusks
    ca = axis(c, HORN_Z)
    out += kit.horn_crown(ca, HORN_Z, lerp_table(HOOD, HORN_Z) - 0.9, 4, HORN_LEN, HORN_R, rise=0.9, lean=0.35,
                          phase=0.0, k=5, n=4, root="rock", tip_from=0.5)
    ct = axis(c, TUSK_Z)
    for i in range(4):
        a = math.pi / 4 + math.pi / 2 * i
        rad = V((math.cos(a), math.sin(a), 0))
        base = ct + rad * (lerp_table(HOOD, TUSK_Z) - 0.5)
        out += kit.tusk(base, rad + V((0, 0, 0.55)), rad * 0.4 + V((0, 0, 1)), 6.5, 0.8, n=3, k=4, collar=False)
    # the spire's iron spike and its skull
    path = spike_path(c)
    out.append(kit.tube(path, [2.0, 1.7, 1.35, 1.0, 0.0], "iron", k=6, cap0="iron", cap1=None))
    for z in (114.5, 127.0):
        p = path[3] if z < SKULL_Z else path[3].lerp(path[4], (z - SKULL_Z) / (SPIKE_TOP - SKULL_Z))
        p = V((p.x, p.y, z))
        r = 1.28 if z < SKULL_Z else 0.95
        out.append(kit.tube([p - V((0, 0, 0.6)), p + V((0, 0, 0.6))], [r + 0.35, r + 0.3], "iron", k=6, cap0="iron", cap1="iron"))
    out += kit.skull(skull_centre(c), outward(c) + V((0.3 if front else -0.3, 0, 0)), SKULL_S, detail=2)
    # a trophy skull on a spike out of the column's outer corner
    d = outward(c)
    base = V((c[0], c[1], 33.0)) + d * (lerp_table(COLUMN, 33.0) - 0.6)
    out += kit.spike(base, d + V((0, 0, 0.3)), 8.5, 0.5, k=4, tip="gore")
    out += kit.skull(base + (d + V((0, 0, 0.3))).normalized() * 4.6 + V((0, 0, 0.3)), d, 3.4, detail=1)
    # the gibbet (front) or the hook with a flayed hide (back)
    cg = axis(c, GIBBET_Z)
    root = cg + d * (lerp_table(HOOD, GIBBET_Z) - 1.0)
    tip = V((c[0], c[1], GIBBET_Z + 1.5)) + d * 20.5
    out.append(kit.tube([root, root + d * 5 + V((0, 0, 1.2)), tip], [0.55, 0.5, 0.42], "iron", k=4, cap0="iron", cap1="iron"))
    out += kit.lashing(root + d * 1.2, d, 0.55, turns=2, w=0.35)
    hang = tip - V((0, 0, 0.3))
    if front:
        out += kit.cage(hang - V((0, 0, 5.5)), 7.5, 2.4, facing=-d, chain=5.5)
    else:
        out += kit.chain(hang, hang - V((0, 0, 3.5)))
        out += kit.carcass(hang - V((0, 0, 3.5)), 8.0, 1.9, facing=d)
    return out


def gore_anchors(c):
    """Where the crown's trophies bleed (for the Gore paint layer): (x, y, z, radius, run)."""
    s = skull_centre(c)
    d = outward(c)
    t = V((c[0], c[1], 33.0)) + d * (lerp_table(COLUMN, 33.0) + 4.0)
    return [(s.x, s.y, s.z - 1.5, 2.2, 9.0), (t.x, t.y, t.z - 1.0, 2.6, 12.0)]
