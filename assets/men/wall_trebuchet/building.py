"""Men wall trebuchet (MenWallTrebuchetSmall, and Arnor's; model GBWallTrebN): EA's bastion kept
whole - the ten-sided ashlar drum, the corbelled flare under the rim, the parapet ring with its
painted arcade and ironwork, the open platform (P1, the trebuchet's bone: nothing stands on it) -
and given the citadel's crown on the rim (men/wall_hub/dome.py):

- a moulded coping along the parapet's top and square merlons with capstones round the rim,
  their fronts facing the field and their backs the platform;
- a pinnacle with a steel orb on each of the rim's ten corners;
- a black enamel band of silver stars round the parapet ring (the citadel's gallery front);
- a steel-framed shield with the White Tree on each long face; arrow slits in stone surrounds.

No banners (ROLLOUT.md: 0).

EA's GBFTRTOWA (mesh coordinates = model coordinates): the drum's outline (x, y) (+-25.16, 0),
(+-22.89, +-13), (+-11.46, +-21) (a rib out to x +-26.62 on the x axis) from 0 to 44, the flare out
to (+-24.21, +-13.71), (+-11.88, +-22) at 50, the parapet ring 1 thick from 50 to the walk at 56
(outer outline as the drum's, inner (+-23.81, 0), (+-21.67, +-13), (+-11, +-20)); P1 (the
platform) at the walk inside it. The footprint: x +-26.62, y +-22.
"""
from sagekit.building import Building

from ..style import MenStyle

RIM = [(25.16, 0.0), (22.89, 13.0), (11.46, 21.0), (-11.46, 21.0), (-22.89, 13.0), (-25.16, 0.0),
       (-22.89, -13.0), (-11.46, -21.0), (11.46, -21.0), (22.89, -13.0)]
WALK = 56.0
COPING = (55.5, 56.45)
MERLONS = dict(w=2.1, gap=1.7, h=2.5, cap=0.5)
BAND = (52.2, 54.4, 0.85)          # a black band of silver stars round the parapet ring (front d)
SHIELD = (26.0, 2.3, 7.2)          # point z, half width, height on the long faces (y +-21)
SLITS = (18.0, 26.5)


class WallTrebuchet(Building):
    style = MenStyle()
    source = "GBWallTrebN"
    target = "GBFTRTOWA"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressF.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallTrebuchet"
    house_tags = ()
    views = {
        "rts": ((0.0, 0.0, 30.0), 210, 50, -38, 50),
        "close": ((0.0, 0.0, 40.0), 130, 26, -30, 45),
        "ingame": ((0.0, 0.0, 28.0), 445, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import sweep

        from ..wall_hub import dome as D
        from ..wall_segment.wall import FACE, slit
        sec = D.Outline(RIM, 1.0)
        z0, z1 = COPING
        prof = [(-1.25, z0), (0.2, z0), (0.2, z1 - 0.2), (0.0, z1), (-1.2, z1)]
        out = sweep(sec.path(1.0), prof, ["stoneB", "course", "course", "top", "course"], center=(0, 0))[0]
        za, zb, df = BAND
        out += sweep(sec.path(1.0), [(0.2, za), (df, za), (df, zb), (0.2, zb)], ["stoneB", "enamel", "top", None],
                     center=(0, 0))[0]
        pins = []
        for a, t, n, L in sec.faces(1.0):
            a3 = V((a.x, a.y, 0))
            out += kit.merlons(a3, t, n, 1.7, L - 1.7, z1, -1.1, 0.0, **MERLONS)
            if L > 20:                                # the long faces: a shield, two slits
                zp, half, height = SHIELD
                out += kit.shield(a3, t, n, L / 2, zp, half, height, d=-0.3)
                for u in (L / 2 - 6.5, L / 2 + 6.5):
                    out += slit(a3 - n * FACE, t, n, u, *SLITS)
            else:
                out += slit(a3 - n * FACE, t, n, L / 2, *SLITS)
            c = V((a.x, a.y, 0)) * 0.955
            pins += kit.pinnacle(c.x, c.y, z1 - 0.1, z1 + 2.3, half=0.95, spire=3.2)
        return out + pins

    def decals(self):
        from ..paint import men_layers
        from ..wall_segment.paintwall import wall_layers
        return [men_layers()[2](zrange=BAND[:2], pitch=3.0, r=0.85), wall_layers()()]

    def emphasis(self, c, n):
        if c.z > 38:
            return 1.35                       # the rim: what the RTS camera sees
        return 1.0
