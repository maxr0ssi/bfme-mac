"""The fortress's crystal moat (ElvenFortressCrystalMoat): EA's ring of water round the fortress,
dressed as the citadel's outer ring - the citadel's silver coping on the parapet, a knotwork band of
silver on sea-green between gilt beads along its outer face, the citadel's crystal lanterns on
short silver posts on the parapet's sixteen corners (two of them flanking the gate's gap), and a
cluster of starlight crystals rising from the water in the middle of every face. No cloth: the
first pass's fifteen drapes are gone.

EA's model (EBFCMOAT1, 158 triangles, its own object at the fortress's origin; mesh coordinates): a
16-sided ring open toward +x (the gate's face; the ring runs over the other 15 faces, its ends at the
corners toward +-11.25 degrees): an inner kerb at apothem 48.69 (z 0.14..2.0), the floor at z 2.0,
the parapet from apothem 69.45 (its inner face, z 2..5) to 71.63 (its outer face, z 0..5), its top
at z 5.0; EA's water (EBFCMOAT2) at z 3.3. The fortress's ring stands inside at 52.57, so the water
shows from there to the parapet.

Height: z 5.0 -> 7.5 at most (max_z_growth 0.5, the lanterns' tips): under the 20 % default (z 6.0)
nothing on the moat reads from the RTS camera. The coping's nose and the band stand 0.45 at most
proud of the outer face (footprint_margin 0.5: the moat's collision comes from the INI)."""
import math

from sagekit.building import Building

from ..style import ElvenStyle

INNER, OUTER, TOP = 69.45, 71.63, 5.0
MID = (INNER + OUTER) / 2
H = (OUTER - INNER) / 2
CORNERS = [11.25 + 22.5 * k for k in range(16)]          # 11.25 .. 348.75: the ring's corners
FACES = [22.5 * k for k in range(1, 16)]                 # the 15 faces (0 is the gate's gap)
# the coping, (d from the parapet's middle, z): a silver nose 0.3 proud over either face, its
# underside's middle buried in the parapet's top
COPING = [(-H - 0.3, TOP), (-H, TOP - 0.35), (H, TOP - 0.35), (H + 0.3, TOP), (H + 0.3, TOP + 0.3), (H + 0.05, TOP + 0.6),
          (-H - 0.05, TOP + 0.6), (-H - 0.3, TOP + 0.3)]
COPING_TAGS = ["trim", None, "trim", "trim", "trim", "trim", "trim", "trim"]
COPING_TOP = TOP + 0.6
CLUSTER = 61.0                                           # the crystals' heart (radial), mid-water
# (du, dr, height, radius, lean) of each shard from the cluster's heart; from the floor (z 1.9) the
# tallest reaches 7.4
SHARDS = [(0.0, 0.0, 5.5, 0.95, 0.0), (1.2, 0.6, 3.9, 0.7, 0.3), (-1.1, 0.8, 3.3, 0.65, 0.35),
          (0.3, -1.2, 2.9, 0.6, 0.4), (-0.6, -0.9, 2.2, 0.5, 0.45)]


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
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressCrystalMoat"      # unused while the moat has no cloth
    footprint_margin = 0.5
    max_z_growth = 0.5
    tri_budget = 6000
    views = {
        "rts": ((0.0, 0.0, 2.5), 446, 50, -38, 50),
        "close": ((49.0, -49.0, 3.0), 60, 22, -40, 45),
        "ingame": ((0.0, 0.0, 2.5), 1013, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import sweep
        k = 1 / math.cos(math.radians(11.25))
        out = sweep([ring_point(d, MID * k) for d in CORNERS], COPING, COPING_TAGS, center=(0, 0))[0]   # 1.
        band = [ring_point(d, OUTER * k) for d in CORNERS]                                            # 2.
        out += kit.filigree_band(band, 0.7, 1.7, d=0.25, center=(0, 0))
        for deg in CORNERS:                                                                           # 3.
            out += self._lantern(kit, *ring_point(deg, MID * k))
        for deg in FACES:                                                                             # 4.
            a = math.radians(deg)
            n, t = V((math.cos(a), math.sin(a), 0)), V((-math.sin(a), math.cos(a), 0))
            for du, dr, ht, rad, lean in SHARDS:
                out.append(self._shard(n * (CLUSTER + dr) + t * du, n * dr + t * du, ht, rad, lean))
        return out

    @staticmethod
    def _lantern(kit, cx, cy):
        """The citadel's ring lantern, small: a starlight crystal in a gilt cup on a short silver
        post on the coping (its tip at z 7.43)."""
        from ..shapes import turned
        z = COPING_TOP - 0.05
        out = [turned(cx, cy, [(0.75, z), (0.75, z + 0.18), (0.5, z + 0.3)], ["trim"] * 2, 8,
                      cap0=("trim", False), cap1=("trim", True))]
        return out + kit.crystal_lantern(cx, cy, z + 0.25, h=1.75, r=0.62, k=6, finial=False)

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
