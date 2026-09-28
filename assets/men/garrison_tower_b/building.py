"""Men garrison tower b (MenGarrisonTowerExpansion, build variation two; model GBFDOTOWB): EA's
gate tower and the wall run out of its -X side kept whole, the tower crowned as variation one
(men/garrison_tower/pad.py, the same tower shifted 6.18 along -x): the machicolated gallery with
its band of silver stars and merlons, the gate's archivolt, quoins and portcullis, pinnacles on
the buttresses and the belfry, window hoods (on the -X face too: the wall leaves it free), the
steel-ribbed dome, lantern, orb and spike. On the wall: stepped buttresses down both faces, a
crest of square merlons along its ridge, and the one house-colour banner on its outward face.

EA's facts: body GBFDOTOWB (466 triangles) on GBFortress1 (own copy GBFortressS); lifecycle
GBFDOTOWB_A, _D2, _D3 (variation two: GBFDOTOWA is men/garrison_tower's); no house model of EA's
(HOUSE_DRAW); no night meshes. The wall (mesh coordinates): x -36.05..-9.57, |y| 2.8 to 45.6, a
coping out to 2.92 at 49.7 and its ridge at 51.74; from -9.57 it widens into the tower's -X
chamfer.
"""
from sagekit.building import Building

from ..style import MenStyle


class GarrisonTowerB(Building):
    style = MenStyle()
    source = "GBFDOTOWB"
    target = "GBFDOTOWB"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressS.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCGarrisonTowerB"
    views = {
        "rts": ((0.3, 0.0, 41.5), 256, 50, -38, 50),
        "close": ((0.3, 0.0, 41.5), 151, 24, -30, 45),
        "ingame": ((0.3, 0.0, 41.5), 582, 53, -62, 50),
    }

    def design(self, kit):
        from ..garrison_tower import pad
        return pad.build(kit, pad.DX_B) + self._wall(kit)

    @staticmethod
    def _wall(kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz
        out = []
        a, t = V((-36.05, -0.08, 0)), V((1, 0, 0))
        out += kit.merlons(a, t, V((0, 1, 0)), 0.3, 26.2, 50.6, -1.15, 1.15, w=2.3, gap=1.7, h=2.6, cap=0.5)
        for sy in (-1, 1):
            n = V((0, sy, 0))
            f = V((0, -2.82 if sy < 0 else 2.66, 0))
            for x in (-31.0, -22.3, -13.6):
                b = f + V((x, 0, 0))
                out.append(prism_uz(b, t, n, [(-1.3, 0.0), (1.3, 0.0), (1.3, 30.0), (-1.3, 30.0)], -0.3, 1.9,
                                    [None, "stoneB", None, "stoneB"], "stoneA", None))
                out.append(prism_uz(b, t, n, [(-1.5, 0.0), (1.5, 0.0), (1.5, 2.4), (-1.5, 2.4)], -0.3, 2.3,
                                    [None, "stoneB", "top", "stoneB"], "course", None))
                out.append(prism_uz(b, t, n, [(-1.3, 30.0), (1.3, 30.0), (1.3, 34.5), (-1.3, 34.5)], -0.3, 1.9,
                                    ["stoneB", "stoneB", None, "stoneB"], "stoneA", None, bat=1.9 / 4.5))
        out += kit.banner(V((-17.95, -2.82, 0)), t, V((0, -1, 0)), 0.0, 43.4, 5.8, 23.0, d=1.0)   # between two buttresses
        return out

    def decals(self):
        from ..paint import men_layers
        from ..garrison_tower.pad import Z_SLAB, Z_WALK
        return [men_layers()[2](zrange=(Z_SLAB, Z_WALK), pitch=3.2, r=0.9)]      # silver stars on the gallery's band

    def emphasis(self, c, n):
        if c.z > 43:
            return 1.35                       # gallery, belfry, crown and the wall's crest
        if c.x > 31 and abs(c.y) < 13:
            return 1.25                       # the gate
        return 1.0
