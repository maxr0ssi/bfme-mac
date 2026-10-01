"""The mine launcher expansion (Blender side), IBFMLAUNCH mesh coordinates (identity root). EA's
launcher (sliced 2026-09-29): a back tower x -35.4..-17.2, |y| < 9.7 (its +X face at x -17.2 for
|y| < 4.2, its sides at |y| 7.7..8.4 to z 60, overhanging to 9.7 above) to z 67 with three spikes to z 74.7; the body's roof
sloping from the tower (z 45) to the loading star (z 28..36); the crew's platform at z 36
(x -26.6..-6.0, y 2.8..24.9, the Uruk at (-16.3, 13.9)); three ramps out to lips at the launch
bones B_FX1..3 ((28.0, -28.5), (36.7, 0.2), (28.8, 28.9), z 19.6).

Kept clear: EA's pointed doorway in the tower's +X face (z 48..58.5), the Uruk's spot (r 5), the
launch paths. Pointed merlons along the front walls' cornice and knife fins up their corners, a White Hand in a pointed arch and ember slits on each of the tower's sides, knife
fins up its corners, iron jaws flanking each ramp's lip, and on the crew's platform a pyramid of
orcfire mines, a brazier and a firebox (real fire). Pass 3's blade pair flanking the tower went in
pass 4 (2026-09-30); the Hands are back on the tower's own sides."""
from mathutils import Vector as V

from .. import shapes_addons as A

X, Y = V((1, 0, 0)), V((0, 1, 0))
LIPS = [(28.0, -28.5, 19.6), (36.7, 0.2, 19.2), (28.8, 28.9, 19.7)]


HAND = (40.5, 6.0, 15.0)                        # the side arches: foot z, width, height


def tower(kit):
    """Pass 4 (2026-09-30): pass 3's blade pair went. EA's tower keeps its own spikes; the White Hand
    in a pointed arch on each of its sides, knife fins up its front corners."""
    out = []
    for y, n in ((-6.8, -Y), (6.8, Y)):              # the Hand on each side, proud of its ribs (y +-6.4..8.4)
        out += A.hand_arch(kit, V((-26.3, y, 0)), X, n, 0.0, HAND[0], HAND[1], HAND[2], d0=-0.5, d1=2.0)
    for (x, y), d in (((-19.0, -7.6), (0.5, -0.87)), ((-19.0, 7.6), (0.5, 0.87))):     # the tower's front corners
        out += kit.blade(V((x, y, 0)) - V((d[0], d[1], 0)) * 0.6, V((d[0], d[1], 0)), 44.0, 62.5, 1.2, 0.5, w=0.9,
                         tip=3.0, back=1.2)
    return out


def jaws(kit):
    """Two leaning iron blades either side of each ramp's lip, clear of the path out."""
    out = []
    for x, y, z in LIPS:
        d = V((x - 6.0, y, 0)).normalized()
        t = V((-d.y, d.x, 0))
        for s in (-1, 1):
            p = V((x, y, 0)) - d * 2.0 + t * (s * 5.0)
            out += kit.blade(p, t * s, z - 3.0, z + 4.0, 1.0, 2.0, w=0.7, tip=3.0, back=1.0)
    return out


def platform(kit):
    out = []
    base = V((-18.6, 21.4, 36.0))                   # a pyramid of orcfire mines
    for i, (dx, dy, dz) in enumerate(((-1.2, -1.2, 0), (1.2, -1.2, 0), (-1.2, 1.2, 0), (1.2, 1.2, 0), (0, 0, 1.5))):
        out += A.cauldron(kit, base + V((dx, dy, dz)), 0.85, 1.5, k=6, spikes=i == 4, legs=False)
    out += kit.brazier(V((-9.4, 21.6, 36.0)), 1.3, 3.0)
    out += kit.fire_grate(V((-9.0, 6.0, 36.0)), Y, -X, w=3.6, h=3.0, d=2.4)
    return out


FRONT = [(6.3, -26.7), (15.9, -10.2), (15.9, 10.2), (6.3, 26.7)]    # the front walls' tops, z 41.3


def front(kit):
    """Pointed merlons along the front walls' cornice (z 41.3, between EA's corner blades) and
    knife fins up the four front corners."""
    out = A.crown_blades(kit, FRONT, 41.0, 6.5, per_edge=3, w=0.6, lean=0.0, corners=False, width=2.4,
                         closed=False, centre=(0.0, 0.0))
    for x, y in ((15.9, -10.2), (15.9, 10.2), (6.3, -26.7), (6.3, 26.7)):
        d = V((x - 3.0, y, 0)).normalized()
        out += kit.blade(V((x, y, 0)) - d * 0.8, d, 17.5, 40.5, 1.4, 0.8, w=0.9, tip=0.0, back=1.2)
    return out


def build(kit):
    return tower(kit) + front(kit) + jaws(kit) + platform(kit)
