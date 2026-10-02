"""Angmar wall tower (AngmarWallTowerSmall; model KBArrwWal): EA's arrow tower kept whole - the
round barrel on the wall line, the corbelled parapet, the pointed keep in the middle with its
three horns gathered into a crown to z 111.6, the hooks on the parapet - and made the wall's
watch-tower:

- the peak: EA's three horns frozen from z 95 to their points (shapes_walls.freeze: an ice casing
  with a ragged frost line, rime toward the points, crystals growing out), the citadel tines'
  frozen tips on the crown EA already gave the tower: no new spike;
- two sorcerers' cold braziers on the walk round the keep, between EA's arrow bones (the tower's
  fire, "coldflame");
- the walls' frozen dress: Carn Dum merlons round the parapet's top (none at EA's hooks), icicles
  under the parapet's flare all round, ice drifts up the barrel's foot on the four diagonals.

No banners. The wall's own run through the tower (|y| 16..19) is left as EA's: the segments
beside it carry the walk's dress.

EA's facts (ARROWTOWER mesh coordinates = model, identity bone; measured 2026-10-01, ray casts):
the barrel r 12.4..16.8 round the axis to z 54, its parapet flaring out to r 14..16 at its top,
z 62..63.6, over the walk at z 59.9; the wall's run along y (|y| 16..19.25, its top z 53.1); the
keep r < 9.6 from the walk to ~z 80, its three horns from (-3.6, 6.6), (6.6, 0.5), (-3.2, -5.6) at
z 95 curving in to their points at z 111.6 (sections ~2 across at z 95); EA's hooks on the
parapet at 0, 90 and 270 degrees (r 18, z 56..60); the arrow bones ARROW01..04 at r 8.6, z 67
(bearings 38, 136, 216, 309 degrees): kept clear. Footprint x -19.35..19.6, y +-19.25. No Ice
Walls mesh on this model; the Ice Walls sheet gets our own copy (KBFortressG_Ice). EA's body
carries six loose vertices and a zero-area face: design() drops the vertices (the Men forge's
drop_loose), the face is EA's. Lifecycle
models in its Draw module: KBArrwWal_A, KBArrwWal_D1, KBArrwWal_D2, KBArrwWal_D3, KBArwWal_A.
House colour: none.
"""
from sagekit.building import Building

from ..style import AngmarStyle

# EA's three horns from z 95 to their points (centres measured by slicing the mesh), the casing's radii
HORNS = [[(-3.6, 6.6, 95.0), (-3.2, 6.0, 98.0), (-2.9, 5.5, 101.0), (-2.6, 4.9, 104.0), (-2.2, 4.2, 107.0),
          (-1.6, 3.2, 110.0), (-1.3, 2.6, 111.6)],
         [(6.6, 0.5, 95.0), (6.0, 0.4, 98.0), (5.4, 0.4, 101.0), (4.9, 0.4, 104.0), (4.1, 0.4, 107.0),
          (3.0, 0.4, 110.0), (2.4, 0.3, 111.6)],
         [(-3.2, -5.6, 95.0), (-3.0, -5.1, 98.0), (-2.7, -4.5, 101.0), (-2.5, -4.0, 104.0), (-2.2, -3.3, 107.0),
          (-1.7, -2.4, 110.0), (-1.4, -1.9, 111.6)]]
CASING = [3.0, 2.7, 2.2, 2.0, 1.6, 1.1, 0.6]
WALK, PARAPET_TOP, PARAPET_R, FLARE = 59.9, 63.6, 15.2, (56.2, 13.2)    # the flare's foot: z, r
MERLONS = [22.5 * i for i in range(16) if i not in (0, 4, 8, 12)]       # none at EA's hooks (0, 90, 270)
BRAZIERS = [(-2.0, 11.6, 2.4, 9.0), (-2.0, -11.6, 2.4, 9.0)]            # x, y on the walk, r, h: the claws show over the merlons
ICE = (30.0, 150.0, 210.0, 330.0)


def _fire_points():
    return [(x, y, round(WALK + h * 0.62, 1), "coldflame") for x, y, r, h in BRAZIERS]


class WallTower(Building):
    style = AngmarStyle()
    source = "KBArrwWal"
    target = "ARROWTOWER"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressG.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    # EA's build-up is a remodel: cut, our shell kept scraps and 3% open backs (sagekit/lifecycle.py `fill`)
    lifecycle = {"KBArrwWal_A": {"fill": True},
                 "KBArwWal_A": {"skip": "never seen: awaiting construction, its animation (KBArwWal_ASKL.KBArrwWal_A) is "
                                        "not in EA's files, so the tower stands at rest, wholly under the ground (z -120..-8)"}}
    HOUSE_DRAW = "ModuleTag_Draw_HCWallTower"
    house_tags = ()
    fire_points = _fire_points()
    views = {
        "rts": ((0.1, -0.0, 55.8), 274, 50, -38, 50),
        "close": ((0.1, -0.0, 55.8), 162, 24, -30, 45),
        "ingame": ((0.1, -0.0, 55.8), 622, 53, -62, 50),
    }

    def design(self, kit):
        import math

        from mathutils import Vector as V

        from assets.men.stable.pieces import drop_loose

        from ..shapes_walls import foot_ice, freeze, merlons
        drop_loose(self.target)             # EA's six loose vertices (the checks allow none on the target)
        out = []
        for i, path in enumerate(HORNS):
            out += freeze(kit, path, CASING, seed=2.0 + i * 1.7, crystals=3)
        for x, y, r, h in BRAZIERS:
            out += kit.cold_brazier((x, y, WALK), r=r, h=h, seed=x + y)
        for i, deg in enumerate(MERLONS):
            n = V((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0))
            out += merlons(kit, n * PARAPET_R, V((-n.y, n.x, 0)), n, [0.0], PARAPET_TOP, w=3.6, h=6.0, d0=-2.0,
                           d1=0.2, phase=i)
        z, r = FLARE
        for k in range(16):                                 # icicles under the flare, a short straight run a bearing
            if k in (0, 4, 12):
                continue
            n = V((math.cos(math.radians(22.5 * k)), math.sin(math.radians(22.5 * k)), 0))
            out += kit.icicles(n * r, V((-n.y, n.x, 0)), n, -2.2, 2.2, z, 5.5, 2, d=0.6, crust=0.9, w=1.2, seed=k)
        for i, deg in enumerate(ICE):
            n = V((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0))
            out += foot_ice(kit, n * 13.6, V((-n.y, n.x, 0)), n, 0.0, w=7.0, h=13.0, reach=2.8, floor=-0.07, seed=i * 1.9)
        return kit.retag(out)
