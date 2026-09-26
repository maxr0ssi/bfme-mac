"""The fortress's crystal moat (ElvenFortressCrystalMoat): EA's ring of water round the fortress,
dressed as a Lórien water-garden - a moulded moonstone coping on the parapet, a knotwork band of
silver on sea-green enamel along its outer face, clusters of starlight crystals rising from the
water, and a leaf drape in the player's colour over the middle of every face.

EA's model (EBFCMOAT1, 158 triangles, its own object at the fortress's origin; mesh coordinates): a
16-sided ring open toward +x (the gate's face; the ring runs over the other 15 faces, its ends at the
corners toward +-11.25 degrees): an inner kerb at apothem 48.69 (z 0.14..2.0), the floor at z 2.0,
the parapet from apothem 69.45 (its inner face, z 2..5) to 71.63 (its outer face, z 0..5), its top
at z 5.0; EA's water (EBFCMOAT2) at z 3.3. The fortress's ring stands inside at 52.5.

Height: z 5.0 -> 6.0 at most (the 20 % default). The drapes' gilt rods stand 0.78 and the knotwork
band 0.45 proud of the outer face (footprint_margin 0.8: the moat's collision comes from the INI)."""
import math

from sagekit.building import Building

from ..style import ElvenStyle

INNER, OUTER, TOP = 69.45, 71.63, 5.0
MID = (INNER + OUTER) / 2
CORNERS = [11.25 + 22.5 * k for k in range(16)]          # 11.25 .. 348.75: the ring's corners
FACES = [22.5 * k for k in range(1, 16)]                 # the 15 faces (0 is the gate's gap)
# crystal clusters in the water: (u along the face, radial) of each cluster's heart; each grows four
# shards leaning out from it (the tallest to z 5.9, under the 6.0 limit)
CLUSTERS = [(-5.0, 61.5), (5.4, 65.4)]
SHARDS = [(0.0, 0.0, 3.9, 0.85, 0.0), (1.1, 0.5, 2.9, 0.65, 0.35), (-0.9, 0.9, 2.5, 0.6, 0.4),
          (0.3, -1.1, 2.2, 0.55, 0.45)]          # (du, dr, height, radius, lean)


def ring_point(deg, r):
    a = math.radians(deg)
    return (r * math.cos(a), r * math.sin(a))


class FortressCrystalMoat(Building):
    style = ElvenStyle()
    source = "EBFCMoat"
    target = "EBFCMOAT1"
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresM.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressCrystalMoat"
    footprint_margin = 0.8
    tri_budget = 6000
    views = {
        "rts": ((0.0, 0.0, 2.5), 446, 50, -38, 50),
        "close": ((49.0, -49.0, 3.0), 60, 22, -40, 45),
        "ingame": ((0.0, 0.0, 2.5), 1013, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V
        from sagekit.blender.geometry import sweep
        out = []
        # 1. the coping: a moulded moonstone cap over the parapet, its nose over the outer face
        c = [ring_point(d, MID / math.cos(math.radians(11.25))) for d in CORNERS]
        h = (OUTER - INNER) / 2
        prof = [(-h - 0.02, TOP - 0.3), (h - 0.02, TOP - 0.3), (h - 0.02, TOP + 0.25), (h - 0.25, TOP + 0.6),
                (-h + 0.25, TOP + 0.6), (-h - 0.35, TOP + 0.3), (-h - 0.35, TOP)]
        out += sweep(c, prof, [None, "trim", "coping", "top", "coping", "trim", None], center=(0, 0))[0]
        # 2. the knotwork band along the outer face, between gilt beads
        band = [ring_point(d, OUTER / math.cos(math.radians(11.25))) for d in CORNERS]
        out += kit.filigree_band(band, 0.7, 1.7, d=0.25, center=(0, 0))
        for deg in FACES:
            a = math.radians(deg)
            n, t = V((math.cos(a), math.sin(a), 0)), V((-math.sin(a), math.cos(a), 0))
            # 3. a leaf drape over the coping's nose, down the outer face to just over the band
            out += kit.leaf_banner(n * OUTER, t, n, 0.0, TOP - 0.05, 7.6, 3.05, d=0.08, free=True)
            # 4. starlight crystals rising from the water in two clusters
            for u, r in CLUSTERS:
                for du, dr, ht, rad, lean in SHARDS:
                    out.append(self._shard(n * (r + dr) + t * (u + du), n * dr + t * du, ht, rad, lean))
        return out

    @staticmethod
    def _shard(p, away, ht, rad, lean):
        """A hexagonal crystal from the moat's floor (z 1.9): a prism narrowing to a point, its tip
        leaning `lean` (units per unit of height) away from the cluster's heart."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        from ..shapes import ring
        off = away.normalized() * lean if away.length > 1e-6 else V((0, 0, 0))
        z0 = 1.9
        rings = [ring(p.x, p.y, rad, z0, 6), ring(p.x + off.x * 0.6 * ht, p.y + off.y * 0.6 * ht, rad * 0.8, z0 + 0.62 * ht, 6)]
        tip = V((p.x + off.x * ht, p.y + off.y * ht, z0 + ht))
        return loft(rings + [[tip] * 6], ["crystal", "crystal"], cap0=("crystal", False), cap1=("crystal", False))

    def emphasis(self, c, n):
        return 1.4
