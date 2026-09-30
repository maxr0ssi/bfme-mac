"""The Mordor citadel's crowns (Blender side), pass 7: Max on pass 6 ("put the spikes and flames
inside, rather than outside and then much smaller"). Each tower's crown holds a crown of thorns
rising from INSIDE EA's crown ring, out of the pyre bowl: eight jagged spikes on the crown's walk,
leaning in and hooking over the fire that burns among them - a claw closing round the flame from
within. Small: the tall spikes rise 7 above EA's crown rim on the corner towers, 11 on the back
tower (the Eye's, tips to z 150), whose spikes are also a little heavier. EA's crowns, pyres and flame cards
stay whole and in sight round them.

EA's crowns (every tower alike, measured 2026-09-30): the crown's walk at z 121.1 inside the
parapet (r 13 at the ribs' angles, z 119.5..132.7), six spike heads (r 9.5..10.3) to z 139.6,
the pyre (MBFDPYRES, r < 10.5) to z 149.9. EA's flame cards are two crossed planes on the tower's
axes (x = axis and y = axis, +- 14.2 wide, z 139.8..168) and a glow plane (x = axis + 1.1): the
spikes stand at 22.5 + 45k degrees, between the planes, their tips at least 1.5 clear of them.

    spikes      Horn (shapes_horn.py): a knife-edged section, the outer edge steel, teeth hooking
                up the inner edge, a hook down the outer; from the walk (z 121) at r 7.4, leaning
                in to tips over the fire. Tall ones on the diagonals' sides (22.5 + 90k) with a lava
                seam up their outer face, short ones between (67.5 + 90k)
    fire        green witch-fire among the spikes, just over the parapet ("witchfire": our copy of
                EA's furnaceFire in Morgul green and a modest dark plume, sagekit/fire_systems.py); the
                back tower a second green flame ("witchflame"). EA's pyres and their orange flame cards
                show only once the Doom Pyres upgrade is bought (EA's SubObjectsUpgrade): they stay EA's
"""
import math

from mathutils import Vector as V

TOWERS = {"back": (-41.75, 42.5), "left": (-41.75, -42.5), "front": (41.75, -42.5), "right": (41.75, 42.5)}
WALK = 121.0                                 # EA's crown walk
# a spike: [(z, r from the tower's axis, (outer reach, inner reach, half depth))], (tip r, tip z)
SPIKES = {
    "back": {"tall": ([(WALK - 0.5, 7.6, (1.5, 1.2, 1.1)), (132.0, 7.4, (1.4, 1.1, 1.0)), (141.0, 6.5, (1.1, 0.9, 0.8)),
                       (146.0, 5.2, (0.7, 0.6, 0.5))], (3.9, 150.0)),
             "short": ([(WALK - 0.5, 7.6, (1.1, 0.9, 0.8)), (132.0, 7.3, (0.9, 0.8, 0.7)), (139.0, 6.3, (0.5, 0.45, 0.4))],
                       (5.2, 143.0))},
    "corner": {"tall": ([(WALK - 0.5, 7.5, (1.2, 1.0, 0.9)), (132.0, 7.3, (1.1, 0.9, 0.8)), (139.0, 6.4, (0.8, 0.7, 0.6)),
                         (143.5, 5.2, (0.5, 0.45, 0.4))], (4.2, 147.0)),
               "short": ([(WALK - 0.5, 7.5, (0.9, 0.8, 0.7)), (131.0, 7.2, (0.7, 0.6, 0.55)), (136.5, 6.3, (0.4, 0.35, 0.3))],
                         (5.3, 139.5))},
}
TEETH = {"tall": [(134.0, 0.6), (139.0, 0.6)], "short": [(133.0, 0.5)]}
HOOKS = {"tall": [(137.0, 0.35)], "short": [(134.0, 0.3)]}
# (x, y offset from the tower's axis, z, kind) of the witch-fire among the spikes: diagonal, clear of the
# cards' planes, just over the crown's parapet (z 132.7) so it burns down in the ring; the back tower a second
# flame without a second plume (sagekit/fire.py "witchflame")
FIRES = {"back": [(1.5, -1.5, 135.0, "witchfire"), (-1.5, 1.5, 138.0, "witchflame")],
         "corner": [(1.5, -1.5, 134.5, "witchfire")]}


def spike(kit, T, deg, spec):
    """A spike at `deg` round the tower's axis: its outer edge faces out (e), its faces tangential (f)."""
    keys, (rt, zt) = spec
    a = math.radians(deg)
    e = V((math.cos(a), math.sin(a), 0))
    f = V((-e.y, e.x, 0))
    t = V((T[0], T[1], 0))
    return kit.Horn([(z, tuple((t + e * r)[:2]), sec) for z, r, sec in keys], e, f, t + e * rt + V((0, 0, zt)))


def seam(kit, h, z0, z1, n=4):
    """A lava seam up the spike's outer-front face (between its steel arris and its front face),
    wandering across it."""
    pts = []
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n
        Wo, _, D = h.section(z)
        s = (0.35, 0.6, 0.4, 0.65, 0.5)[i % 5]
        pts.append(h.point(z, Wo * (1 - 0.6 * s), D * s))
    return kit.face_crack(pts, h.e, w=0.55, depth=0.25)


def crown(kit, name, T):
    kind = "back" if name == "back" else "corner"
    out = []
    for k in range(8):
        deg = 22.5 + 45.0 * k
        size = "tall" if k % 2 == 0 else "short"
        h = spike(kit, T, deg, SPIKES[kind][size])
        out += kit.horn(h, teeth=TEETH[size], hooks=HOOKS[size], outer="steel", edge="stoneB", tag="stoneA")
        if size == "tall":
            out += seam(kit, h, WALK + 3.0, SPIKES[kind][size][1][1] - 6.0)
    for dx, dy, z, fire in FIRES[kind]:
        kit.fire(V((T[0] + dx, T[1] + dy, z)), fire)
    return out


def build(kit):
    out = []
    for name, T in TOWERS.items():
        out += crown(kit, name, T)
    return out
