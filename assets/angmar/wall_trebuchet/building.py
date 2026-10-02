"""Angmar wall trebuchet (AngmarWallCatapultSmall; model KBTrlSlingWall): EA's troll-sling bastion
kept whole - the oval drum on its plinth, the platform at z 47.4 where the troll slinger stands,
the parapet ring with its two gaps facing the field, the blade spurs over the wall's joints at
+-x - and given the walls' frozen dress:

- Carn Dum merlons round the parapet ring (none on the spurs, none in the two gaps);
- a corbel with icicles hanging under it round the drum just below the parapet;
- ice drifts on the plinth's ledge up the drum's four diagonal faces;
- two sorcerers' cold braziers on the platform's rim, on opposite diagonals ("coldflame"), clear of
  the slinger in the middle and of the gaps.

No peak and no banners: the troll and its sling are the bastion's story.

EA's facts (KBTROLLWALLSLIN mesh coordinates = model, identity bone; measured 2026-10-01, ray
casts): the drum an oval round (-0.8, 0.5), battered from (x 29, y 27) at z 20 to (27, 24.6) at the
parapet's top, z 53; the plinth to z ~11-12.6 out to x -39.6..38.1, y -27.89..28.98 (the
footprint); the platform at z 47.4 inside the ring (oval ~22 x 20); the ring's gaps at x 0 (|x| < 3.5,
z 47.6) on both y faces; the spurs at |x| 25..33 to z 59.3 on the x axis, where the wall joins.
ICEWALL (Ice Walls, 48 triangles, EXFortressIce): a shell round the drum and plinth (x -35.2..34.3,
y -28.6..29.9) to z 33.04: the ice drifts stand inside it on the plinth, as EA's plinth does. The
Ice Walls sheet gets our own copy (KBFortressJ_Ice). Lifecycle models in its Draw module:
KBTrSlgWl_A, KBTrSlgWl_D1, KBTrSlgWl_D2, KBTrSlgWl_D3. House colour: none.
"""
import math

from sagekit.building import Building

from ..style import AngmarStyle

C = (-0.8, 0.5)                      # the drum's centre
RING = (27.0, 24.6, 53.0)            # the parapet's outer line at its top: semi-axes x, y; z
SKIP = [(-14.0, 14.0), (76.0, 104.0), (166.0, 194.0), (256.0, 284.0)]    # spurs (0, 180), gaps (90, 270)
CORBEL_Z = 50.6
PITCH = 8.5                          # the walls' merlons, spaced wider round the drum (fewer, not a fence)
ICE = ((40.0, 140.0, 220.0, 320.0), (28.6, 26.4, 11.2))   # bearings; the drum's foot line (a, b) and the ledge z
BRAZIERS = [(130.0, 19.0, 17.0), (310.0, 19.0, 17.0)]     # bearing, the platform's rim (a, b)
BRAZIER = (47.4, 2.6, 9.0)           # z, r, h


def _pt(deg, a, b):
    t = math.radians(deg)
    return C[0] + a * math.cos(t), C[1] + b * math.sin(t)


def _normal(deg, a, b):
    t = math.radians(deg)
    nx, ny = math.cos(t) / a, math.sin(t) / b
    m = math.hypot(nx, ny)
    return nx / m, ny / m


def _fire_points():
    z, r, h = BRAZIER
    return [(round(x, 1), round(y, 1), round(z + h * 0.62, 1), "coldflame")
            for x, y in (_pt(d, a, b) for d, a, b in BRAZIERS)]


class WallTrebuchet(Building):
    style = AngmarStyle()
    source = "KBTrlSlingWall"
    target = "KBTROLLWALLSLIN"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressJ.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    # EA's build-up is a remodel: cut, 3.6% open backs (sagekit/lifecycle.py `fill`)
    lifecycle = {"KBTrSlgWl_A": {"fill": True}}
    HOUSE_DRAW = "ModuleTag_Draw_HCWallTrebuchet"
    bake_hidden = ("ICEWALL",)        # the Ice Walls shell: shown in game with its upgrade, out of the bakes
    house_tags = ()
    fire_points = _fire_points()
    views = {
        "rts": ((-0.7, 0.5, 30.9), 252, 50, -38, 50),
        "close": ((-0.7, 0.5, 30.9), 149, 24, -30, 45),
        "ingame": ((-0.7, 0.5, 30.9), 572, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from ..shapes_walls import corbel, foot_ice, merlons
        a, b, z = RING
        out = []
        steps = 720                                          # merlons a pitch apart along the ring
        pts = [V(_pt(360.0 * i / steps, a, b) + (0.0,)) for i in range(steps + 1)]
        arc, last, k = 0.0, None, 0
        for i in range(1, steps + 1):
            arc += (pts[i] - pts[i - 1]).length
            deg = 360.0 * i / steps
            if arc >= PITCH and not any(lo <= deg <= hi for lo, hi in SKIP):
                n = V(_normal(deg, a, b) + (0.0,))
                out += merlons(kit, pts[i], V((-n.y, n.x, 0)), n, [0.0], z, d0=-2.0, d1=0.3, phase=k)
                arc, k = 0.0, k + 1
            elif any(lo <= deg <= hi for lo, hi in SKIP):
                arc = PITCH * 0.5
        for lo, hi in zip([s[1] for s in SKIP], [s[0] for s in SKIP[1:]] + [SKIP[0][0] + 360.0]):
            k = max(1, int(round((hi - lo) / 12.0)))         # straight runs of the corbel between the skips
            for j in range(k):
                d0, d1 = lo + (hi - lo) * j / k, lo + (hi - lo) * (j + 1) / k
                p, q = V(_pt(d0, a, b) + (0.0,)), V(_pt(d1, a, b) + (0.0,))
                t = (q - p).normalized()
                n = V((t.y, -t.x, 0))
                if n.dot(p - V((C[0], C[1], 0))) < 0:
                    n = -n
                out += corbel(kit, p, t, n, 0.0, (q - p).length, CORBEL_Z, out=1.2, h=2.2, length=5.0, seed=d0,
                              ends=(j == 0, j == k - 1))
        degs, (fa, fb, fz) = ICE
        for i, deg in enumerate(degs):
            n = V(_normal(deg, fa, fb) + (0.0,))
            out += foot_ice(kit, V(_pt(deg, fa, fb) + (0.0,)), V((-n.y, n.x, 0)), n, 0.0, w=8.0, h=14.0, reach=2.2,
                            floor=fz, seed=i * 2.7)
        zb, r, h = BRAZIER
        for i, (deg, ba, bb) in enumerate(BRAZIERS):
            x, y = _pt(deg, ba, bb)
            out += kit.cold_brazier((x, y, zb), r=r, h=h, seed=i + 0.7)
        return kit.retag(out)
