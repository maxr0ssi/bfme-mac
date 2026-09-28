"""The Houses of Healing (UPGRADE_HOUSE_OF_HEALING, Draw ModuleTag_HouseOfHealingDraw of
MenFortressCitadel): EA's hall on the gate's wall walk kept whole - the arcaded front, the stepped
gable with its six robed statues, the knotwork and the White Tree shield in its niche, the slate
barrel vault behind - and dressed in the citadel's language (fortress_ivory_tower/citadel_motifs.py):
a black frieze of silver stars under a new moulded cornice across the front (it frames the
citadel's winged crest, which stands in front of the lower arcade), a raised coping up every
step of the gable, the seven stars of Elendil in gilt over the niche, a steel-and-gilt finial on
the apex, steel ribs over the vault with a crest of steel spikes along its ridge, and a lantern
flèche on the ridge - an arcaded lantern under a slate spire, a gilt orb and a steel spike.

EA's GBFHEAL (552 triangles, drawn at the fortress's origin; mesh = fortress coordinates): the
front x 48.16 (z 49.19..73.04, the arcade's arches up to about 70), a ledge to x 48.75 at z
73.04..74.56; the gable's front x 48.21 over a field at 47.61, its outline (y >= 0, mirrored)
(28.55, 79.59) (23.01, 79.59) (19.35, 82.21) (19.35, 87.3) (14.6, 87.3) (11.59, 90.66)
(11.59, 97.19) (7.85, 97.19) (0, 106.88); statues on the treads at |y| 25.3, 16.8, 9.25 (x
46.2..48.0, heads to 90.0, 97.7, 107.67); the niche |y| <= 4.2 up to 92.47 (x 46.85); the barrel
vault x 29.4..45.27, section (0, 92.11) (5.75, 90.15) (11.51, 86.18) (16.01, 80.22) (20.51, 73.04);
flat roofs at 73.04 beside it. The citadel's front towers' faces are at |y| 26.75 (EA's sides
run on inside them), so everything here stays within |y| < 26.7. The citadel's gate pediment
stands in front at x 50.2..58.35 (|y| <= 21.8, up to its crest at about 72.8): the cornice's nose
stops at x 49.7 (footprint_margin 1.0; the house stands inside the citadel's footprint).
Height 59.67, +20 % allowed (z 119.6): the finials end at 118.5 and 116.
"""
import math

from sagekit.building import Building

from ..style import MenStyle

HALF = 26.7                                                   # the visible front, between the towers
X_FRONT, X_GABLE, X_FIELD = 48.16, 48.21, 47.61
FRIEZE = (71.0, 73.0)                                          # the black star frieze
GABLE = [(HALF, 79.59), (23.01, 79.59), (19.35, 82.21), (19.35, 87.3), (14.6, 87.3), (11.59, 90.66),
         (11.59, 97.19), (7.85, 97.19), (0.0, 106.88)]
VAULT = [(0.0, 92.11), (5.75, 90.15), (11.51, 86.18), (16.01, 80.22), (20.51, 73.04)]
RIBS_X = (31.2, 34.0, 40.5, 43.3)
FLECHE = (37.25, 0.0)
APEX = (0.0, 106.88)


class FortressHouseOfHealing(Building):
    style = MenStyle()
    source = "GBFHeal"
    target = "GBFHEAL"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressM.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_HouseOfHealingDraw",)
    footprint_margin = 1.0
    tri_budget = 6000
    views = {
        "rts": ((38.7, 0.0, 80.0), 190, 50, -38, 50),
        "close": ((42.0, 0.0, 88.0), 95, 18, -25, 45),
        "front": ((46.0, 0.0, 88.0), 80, 8, 0, 45),
        "ingame": ((38.7, 0.0, 77.8), 425, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from ..fortress_ivory_tower import citadel_motifs as M
        a, t, n = V((X_FRONT, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        out = self._front(kit, M, a, t, n)
        out += self._gable(kit, M, t, n)
        out += self._vault(kit, M)
        out += self._fleche(kit, M)
        return out

    @staticmethod
    def _front(kit, M, a, t, n):
        """The frieze (black, silver stars painted) under a new cornice over EA's ledge."""
        from sagekit.blender.geometry import prism_uz
        z0, z1 = FRIEZE
        return [prism_uz(a, t, n, [(-HALF, z0 - 0.5), (HALF, z0 - 0.5), (HALF, z0), (-HALF, z0)], -0.2, 0.85,
                         ["stoneB", "stoneB", "top", "stoneB"], "course", None),
                prism_uz(a, t, n, [(-HALF, z0), (HALF, z0), (HALF, z1), (-HALF, z1)], -0.2, 0.65,
                         [None, "stoneB", None, "stoneB"], "enamel", None),
                prism_uz(a, t, n, [(-HALF, z1), (HALF, z1), (HALF, 74.1), (-HALF, 74.1)], -0.2, 1.05,
                         ["stoneB", "stoneB", None, "stoneB"], "course", None),
                prism_uz(a, t, n, [(-HALF, 74.1), (HALF, 74.1), (HALF, 75.0), (-HALF, 75.0)], -0.2, 1.5,
                         ["stoneB", "stoneB", "top", "stoneB"], "course", None)]

    @staticmethod
    def _gable(kit, M, t, n):
        """A raised coping up every step of the gable (both halves), the seven stars over the niche
        and a finial on the apex."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz
        a = V((0, 0, 0))
        outline = [(-u, z) for u, z in GABLE] + [(u, z) for u, z in reversed(GABLE[:-1])]
        out = M.coping(a, t, n, outline, X_FIELD + 0.1, X_GABLE + 0.95, w=0.95, inner=0.4)
        out += M.stars_arc(kit, a, t, n, 0.0, 87.6, 7.3, X_FIELD - 0.1, X_FIELD + 0.55, r=0.9)
        u, z = APEX
        out.append(prism_uz(a, t, n, [(u - 1.5, z - 1.8), (u + 1.5, z - 1.8), (u + 1.5, z + 1.6), (u - 1.5, z + 1.6)],
                            X_FIELD - 1.0, X_GABLE + 1.0, ["stoneB", "stoneB", "top", "stoneB"], "stoneA", "stoneB"))
        out.append(prism_uz(a, t, n, [(u - 1.8, z + 1.6), (u + 1.8, z + 1.6), (u + 1.8, z + 2.3), (u - 1.8, z + 2.3)],
                            X_FIELD - 1.3, X_GABLE + 1.3, ["stoneB", "course", "top", "course"], "course", "stoneB"))
        cx = (X_FIELD + X_GABLE) / 2
        out += M.finial(kit, cx, u, z + 2.2, z + 5.4, 118.5, collar=(1.0, z + 2.1, z + 3.0))
        return out

    @staticmethod
    def _vault(kit, M):
        """Steel ribs over the barrel vault and a crest of steel spikes along its ridge."""
        from mathutils import Vector as V

        from ..shapes import beam, rail
        sec = [(-y, z) for y, z in reversed(VAULT[1:])] + VAULT
        out = []
        for x in RIBS_X:
            pts = []
            for i, (y, z) in enumerate(sec):
                y0, z0 = sec[max(i - 1, 0)]
                y1, z1 = sec[min(i + 1, len(sec) - 1)]
                ny, nz = -(z1 - z0), (y1 - y0)
                L = math.hypot(ny, nz)
                if nz < 0:
                    ny, nz = -ny, -nz
                pts.append(V((x, y + ny / L * 0.22, z + nz / L * 0.22)))
            out.append(rail(pts, 0.3, "trim", 0.3))
        z = VAULT[0][1]
        out.append(beam((30.0, 0, z + 0.25), (44.9, 0, z + 0.25), 0.35, "trim"))
        for k in range(8):
            x = 30.8 + 1.9 * k
            if abs(x - FLECHE[0]) < 3.2:
                continue
            out.append(beam((x, 0, z + 0.5), (x, 0, z + 2.3), 0.22, "trim", 0.0))
        return out

    @staticmethod
    def _fleche(kit, M):
        """A lantern flèche astride the ridge: an octagonal stone base, the kit's arcaded lantern,
        a slate spire, the citadel's finial."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import loft

        from ..shapes import ring, turned
        cx, cy = FLECHE
        out = [turned(cx, cy, [(2.7, 88.5), (2.7, 94.0), (3.05, 94.3), (3.05, 94.9)], ["stoneA", "course", "course"],
                      cap0=("stoneB", False), cap1=("top", True))]
        out += kit.lantern(cx, cy, 94.8, r=2.3, top=101.2)
        out.append(loft([ring(cx, cy, 2.45, 100.9), [V((cx, cy, 108.4))] * 8], ["slate"], cap0=("slate", True), cap1=("top", False)))
        out += M.finial(kit, cx, cy, 107.2, 110.4, 116.0)
        return out

    def decals(self):
        from ..fortress_ivory_tower.citadel_motifs import star_band
        return [star_band((FRIEZE[0] + 0.1, FRIEZE[1] - 0.1), pitch=2.5, r=0.8)]

    def emphasis(self, c, n):
        return 1.35 if c.x > 45 else 1.0
