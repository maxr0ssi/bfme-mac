"""The Angmar citadel's walks and faces (Blender side): the Witch-king's hold kept - sorcerers'
braziers of cold fire on the walk, iron gibbets off the wall towers, Angmar's banners in the
player's colour.

The walk is at z 51.85 from r 50.5 to the parapet (r ~67); the curtain's top lip at z 56.6, r 69.4.
The wall towers stand at (+-17, -72) and (-72, +-17), coned from r 84 at the foot to z 77 (r 72.8
at z 60). Kept clear: the bastions (the diagonals: their arrow bones, the Ice Munitions horns and
mist, the blue torch cards), the gate (+X, |y| < 25), the crown's tines (r < 45).

    braziers    four sorcerers' braziers on the walk (r 59), the cold fire in each ("coldflame")
    gibbets     an iron gibbet off each -Y wall tower's outer face, a cage hanging over the foot
    gate        icicles off the gate's lintel like a frozen portcullis' teeth
    banners     two heavy banners from the curtain's lip, diagonally opposite (between the -Y face's
                wall tower and the SE bastion, and between the +Y face's and the NW bastion), clear of
                EA's night windows and of a battle tower on every pad: the cloth in the player's
                colour (the house model), the iron frame ours
"""
from mathutils import Vector as V

WALK = 51.85
BRAZIERS = [-62.0, -118.0, 62.0, 152.0]
GIBBETS = [(-76.8, 60.0), (-103.2, 60.0)]
# (degrees, width, length): where the curtain has no night window and no battle tower stands on any pad
# (pass 4 hung them at -90 and 90, where a tower on the S or N pad runs its wing into the curtain): one
# between the -Y face's wall tower and the SE bastion, facing the RTS camera, the other opposite it
BANNERS = [(-63.5, 13.0, 30.0), (115.5, 13.0, 30.0)]
LIP_Z, LIP_R = 56.6, 69.4


def braziers(kit):
    out = []
    for i, deg in enumerate(BRAZIERS):
        out += kit.cold_brazier(kit.polar((0, 0), 59.0, deg, WALK), r=2.8, h=8.5, seed=i + 0.5)
    return out


def gibbets(kit):
    out = []
    for deg, z in GIBBETS:
        a = kit.polar((0, 0), 72.0, deg, 0.0)
        out += kit.gibbet(a, a.normalized(), z, reach=6.5, drop=5.0, h=7.5, w=2.4)
    return out


def banners(kit):
    out = []
    for deg, w, L in BANNERS:
        p = kit.polar((0, 0), LIP_R, deg, 0.0)
        n = V((p.x, p.y, 0)).normalized()
        t = V((-n.y, n.x, 0))
        out += kit.banner(p, t, n, 0.0, LIP_Z - 0.5, w, L, d=2.6, mark=False)
    return out


def gate(kit):
    """Icicles hanging like a portcullis' teeth off the front of the gate's lintel (x 76.5, z 40),
    their points above z 32 (the doorway below stays clear)."""
    return kit.icicles(V((76.0, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), -8.5, 8.5, 40.2, 6.5, 9, d=0.6, crust=1.8, w=1.5,
                       seed=7.0)


def build(kit):
    return braziers(kit) + gibbets(kit) + banners(kit) + gate(kit)
