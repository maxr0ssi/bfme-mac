"""Angmar wall postern (AngmarWallPosternGateSmall; model KBPostGateN): EA's postern kept whole -
two gabled porches standing out of the wall's faces, each a pointed arch recess in a stone frame,
EA's ice-crystal sculptures on blocks either side - and given the gate's language at its own small
scale:

- a barbed iron portcullis raised in each porch's arch (shapes_walls.grille: five bars, barbed
  steel teeth, a riveted top beam set into the frame), the gate's portcullis in little;
- the gable's two slopes crusted with rime, icicles hanging along both eaves.

No merlons (the porches have no walk), no fire, no banners; EA's crystal sculptures are the ice at
its feet. The wall segment it stands in (AngmarWallPosternGateSmall also draws KBWallN) carries
the walk's dress.

EA's facts (POSTERN GATE mesh coordinates = model, identity bone; measured 2026-10-01, ray casts):
the porches at |x| 9..15.88 either side of the wall (|x| < 8.5 open: the segment's body), each
|y| < 9 to its eaves at z 31.3, the gable rising to z 43.63 at y 0; the arch recess 3.8 deep (its
back at |x| 12.1) and |y| < 7 wide to z 32, pointed to z ~40; the blocks |y| 9..15.8 to z 5.5
with EA's crystals on them at (+-13, +-12.5) to z 17.8. Footprint x -15.77..15.88,
y -15.82..15.24. No Ice Walls mesh; the Ice Walls sheet gets our own copy (KBFortressF_Ice).
Lifecycle models in its Draw module: KBPostGat_D2, KBPostGat_D3, KBPostGateN_A, KBPostGateN_D1.
House colour: none.
"""
from sagekit.building import Building

from ..style import AngmarStyle

PORCH = (8.9, 15.75)                 # |x| of the porch: the wall side, the front (inside EA's footprint)
EAVES, RIDGE, HALF = 31.3, 43.6, 9.1
ARCH = (13.8, 6.4, 26.0, 32.6)       # the portcullis: |x| of its plane, half width, z0 (teeth to 22.8), z1


class WallPostern(Building):
    style = AngmarStyle()
    source = "KBPostGateN"
    target = "POSTERN GATE"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressF.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallPostern"
    house_tags = ()
    views = {
        "rts": ((0.1, -0.3, 21.8), 137, 50, -38, 50),
        "close": ((0.1, -0.3, 21.8), 81, 24, -30, 45),
        "ingame": ((0.1, -0.3, 21.8), 311, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz

        from ..shapes_walls import grille
        out = []
        o, t, y_ = V((0, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        for sx in (1, -1):
            d0, d1 = sorted((sx * PORCH[0], sx * PORCH[1]))
            for sy in (1, -1):                              # rime along the gable's slope, icicles under the eave
                poly = [(sy * (HALF + 0.3), EAVES - 0.3), (0.0, RIDGE - 0.3), (0.0, RIDGE + 0.35),
                        (sy * (HALF + 0.3), EAVES + 0.35)]
                out.append(prism_uz(o, t, y_, poly, d0, d1, ["rime"] * 4, "rime", "rime"))
                out += kit.icicles(V((0, sy * HALF, 0)), V((1, 0, 0)), V((0, sy, 0)), d0 + 0.5, d1 - 0.5, EAVES - 0.4,
                                   5.0, 3, d=0.5, crust=0.9, w=1.2, seed=sx + 2 * sy)
            x, w, z0, z1 = ARCH
            out += grille(kit, V((sx * x, 0, 0)), V((0, 1, 0)), V((sx, 0, 0)), -w, w, z0, z1, bars=5, rails=(0.5,),
                          r=0.5, teeth=3.2, ext=0.8)
        return kit.retag(out)
