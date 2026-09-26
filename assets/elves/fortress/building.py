"""The Elven fortress (ElvenCitadel, ElvenFortress): EA's citadel kept whole - the ring of arcades
with its frieze, filigree lattice windows and carved leaf gables, the four mallorn trees and their
tree-houses, the gatehouse under its traceried roof and the pointed gate - and crowned the Elven
way in silver and gold: a silver coping round the ring, gilt leaf finials on EA's gables and
crystal lanterns between them, silver ridges on the tree-houses, a flèche astride the gatehouse
roof (spire.py) and two lantern towers at the gate. Four banners: two at the gate, two on the
flèche. The paint does the rest: EA's tan frames and tracery become gold (style.py Repaint).

EA's body (EBFORTRESS1, 5326 triangles; measured in its mesh coordinates, which are the model's):
  - the ring: a 16-sided wall, outer face at apothem 52.57 (faces toward 0, 22.5, 45, ... degrees),
    z 0..53.63, a chamfered cap in to 51.68 at z 55.13, its top 1.8 wide over the walk (z 53, from
    apothem 49.89). The faces toward +-22.5, +-67.5, +-112.5, +-157.5 carry EA's leaf gables (apex
    z 64.27 at radial 51.1); the face toward 0 is the gatehouse's; the other seven are plain.
  - the gatehouse wing: x 46..75.5, side walls at |y| 16.1, the gate front at x 69.2 with the arch
    frame to x 75.5; its roof a pointed section, ridge 82.2 (x 53.4) to 84.4 (x 74.4); the ramp
    x 69..93.5, |y| < 8.9.
  - the tree-houses on the mallorn trees: ridges along the diagonals, centred at (+-26.3, +-23.8),
    sagging from z 120.2 at 11.9 either side to 118.4 in the middle; the swept horns at their ends
    to z 122.89 (the body's top).
The upgrades draw at the same origin: the mystic fountains hang on the ring faces toward +-45,
+-67.5, +-112.5, +-157.5 (to z 31.5), the enchanted anvil stands on the face toward 180 (its
platform x -50.3..-33 at z 53, to z 106), the eagle's nest in the courtyard's middle (|x|, |y| <=
14.4, to z 141)."""
import math

from sagekit.building import Building
from sagekit.taxonomy import Tier

from ..style import ElvenStyle

RING = 52.57                                  # the ring's outer faces (apothem)
CORNER = RING / math.cos(math.radians(11.25))
GABLE_FACES = (22.5, 67.5, 112.5, 157.5, -22.5, -67.5, -112.5, -157.5)
GABLE_APEX = (51.1, 64.27)                    # radial, z of EA's leaf gables' tips
LANTERN_FACES = (45, 90, 135, -45, -90, -135)  # the plain faces but the anvil's (180)
WING_Y = 16.1                                 # the gatehouse wing's side walls
# the coping on the ring's cap, (d from the outer face, z): its underside buried in EA's chamfer,
# a silver nose 0.55 proud, a silver top 3.3 wide over the cap (out to the walk's edge)
COPING = [(-2.7, 55.0), (0.0, 53.5), (0.4, 53.5), (0.55, 54.0), (0.55, 55.2), (0.3, 55.75), (-2.7, 55.75)]
COPING_TAGS = [None, "trim", "trim", "trim", "trim", "trim", "trim"]
COPING_TOP = 55.75
HOUSES = [(26.3, 23.8, 118.37), (-26.2, 23.8, 118.36), (26.3, -24.2, 118.28), (-26.45, -24.2, 118.22)]
RIDGE_SAG = (11.9, 1.8)                       # the tree-house ridge rises 1.8 at 11.9 from its middle
GATE_RIDGE = [(53.4, 82.2), (58.0, 82.5), (65.0, 83.0), (67.1, 83.1), (74.4, 84.4)]   # (x, z) of the rail's top
GATE_TOWERS = [(72.4, -20.6), (72.4, 20.6)]   # beside the gate, clear of the ramp and the wing's walls


def ring_path():
    """The ring's outer line from the wing's wall on the face toward 22.5 round the back to the wing's
    wall on the face toward -22.5 (the gatehouse's face, 0, has none)."""
    def on_face(deg, y):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        return ((RING - y * s) / c, y)
    pts = [on_face(22.5, WING_Y)]
    for i in range(15):
        a = math.radians(33.75 + 22.5 * i)
        pts.append((CORNER * math.cos(a), CORNER * math.sin(a)))
    pts.append(on_face(-22.5, -WING_Y))
    return pts


class Fortress(Building):
    style = ElvenStyle()
    source = "EBFortress"
    target = "EBFORTRESS1"
    facet_islands = 20                  # EA's organic mallorn wood: seams at EA's islands and 20-degree turns
    tier = Tier.HERO
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    tri_budget = 15000
    views = {
        "rts": ((19.6, 0.0, 61.3), 486, 50, -38, 50),
        "close": ((19.6, 0.0, 61.3), 287, 24, -30, 45),
        "ingame": ((19.6, 0.0, 61.3), 1104, 53, -62, 50),
        "gate": ((70.0, -6.0, 40.0), 150, 14, -24, 45),
        "crown": ((20.0, -20.0, 110.0), 120, 30, -40, 45),
    }

    def design(self, kit):
        from sagekit.blender.geometry import sweep

        from . import spire
        out = sweep(ring_path(), COPING, COPING_TAGS, center=(0, 0))[0]   # 1. the silver coping
        for deg in GABLE_FACES:                                     # 2. gilt leaf finials on EA's gables
            a = math.radians(deg)
            r, z = GABLE_APEX
            out += kit.leaf_finial(r * math.cos(a), r * math.sin(a), z - 0.4, 6.4, 2.3)
        for deg in LANTERN_FACES:                                   # 3. crystal lanterns between them
            out += self._ring_lantern(kit, deg)
        for cx, cy, z in HOUSES:                                    # 4. silver ridges on the tree-houses
            out += self._house_ridge(kit, cx, cy, z)
        out += self._gate_ridge()                                   # 5. the gatehouse ridge and its flèche
        out += spire.build(kit)
        for cx, cy in GATE_TOWERS:                                  # 6. lantern towers at the gate
            out += self._gate_tower(kit, cx, cy)
        return out

    @staticmethod
    def _ring_lantern(kit, deg):
        """A starlight crystal in a gilt cup on a slender silver post, on the coping over the middle
        of a plain ring face: its gilt tip level with the gables' finials."""
        from ..shapes import turned
        a = math.radians(deg)
        cx, cy = 51.2 * math.cos(a), 51.2 * math.sin(a)
        z = COPING_TOP - 0.1
        out = [turned(cx, cy, [(1.35, z), (1.35, z + 0.5), (0.9, z + 0.9), (0.6, z + 1.6), (0.5, z + 4.6), (1.0, z + 5.2)],
                      ["trim", "trim", "trim", "trim", "trim"], 10, cap0=("trim", False), cap1=("trim", True))]
        return out + kit.crystal_lantern(cx, cy, z + 5.1, h=6.4, r=1.25)

    @staticmethod
    def _house_ridge(kit, cx, cy, z_mid):
        """A silver cap along a tree-house's ridge, following its sag between the horns, and a gilt
        leaf finial where the dormers' ridges meet it."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz
        L = math.hypot(cx, cy)
        t = V((cx / L, cy / L, 0))                   # along the ridge (it runs out from the courtyard)
        n = V((t.y, -t.x, 0))                        # t x n = -z, as the kit's faces
        a = V((cx, cy, 0))
        s0, rise = RIDGE_SAG

        def zr(s):
            return z_mid + rise * (s / s0) ** 2
        ss = [-11.4 + 22.8 * i / 8 for i in range(9)]
        out = []
        for sa, sb in zip(ss, ss[1:]):
            q = [(sa, zr(sa) - 0.4), (sb, zr(sb) - 0.4), (sb, zr(sb) + 0.45), (sa, zr(sa) + 0.45)]
            # every face kept, joints and underside too: where a dormer's roof buries one side, the other
            # side's back must not look through the cap into EA's open roof shell
            out.append(prism_uz(a, t, n, q, -0.55, 0.55, ["trim"] * 4, "trim", "trim"))
        return out + kit.leaf_finial(cx, cy, z_mid + 0.3, 4.2, 1.6)

    @staticmethod
    def _gate_ridge():
        """A silver cap along the gatehouse roof's ridge rail, from the roof's back arch to its front."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz
        a, t, n = V((0, 0, 0)), V((1, 0, 0)), V((0, -1, 0))
        out = []
        for i, ((xa, za), (xb, zb)) in enumerate(zip(GATE_RIDGE, GATE_RIDGE[1:])):
            q = [(xa, za - 0.3), (xb, zb - 0.3), (xb, zb + 0.5), (xa, za + 0.5)]
            tags = [None, "trim" if i == len(GATE_RIDGE) - 2 else None, "trim", "trim" if i == 0 else None]
            out.append(prism_uz(a, t, n, q, -0.85, 0.85, tags, "trim", "trim"))
        return out

    @staticmethod
    def _gate_tower(kit, cx, cy):
        """A slender lantern tower beside the gate: a moulded plinth, a leaf-capital column, an open
        lantern stage of four colonnettes round a crystal, a swept slate needle with a gilt leaf tip,
        and a leaf banner hung on the column's front, facing down the ramp."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import loft

        from ..shapes import ring, turned
        out = [turned(cx, cy, [(3.4, 0.0), (3.4, 1.4), (3.0, 1.8), (2.8, 2.8), (2.4, 3.2)],
                      ["stoneB", "coping", "course", "trim"], 12, cap0=("stoneB", False), cap1=("top", True))]
        out += kit.column(cx, cy, 3.1, 44.0, r=1.9, k=12, leaves=6)
        z0 = 44.0                                                   # the lantern stage on the abacus
        out.append(loft([ring(cx, cy, 3.5, z0, 12), ring(cx, cy, 3.5, z0 + 0.8, 12), ring(cx, cy, 3.1, z0 + 1.1, 12)],
                        ["trim", "trim"], cap0=("stoneB", False), cap1=("top", True)))
        for i in range(4):
            ang = math.pi / 4 + i * math.pi / 2
            px, py = cx + 2.55 * math.cos(ang), cy + 2.55 * math.sin(ang)
            out.append(turned(px, py, [(0.34, z0 + 1.0), (0.3, z0 + 7.2)], ["trim"], 6, cap0=("top", False),
                              cap1=("top", False)))
        out += kit.crystal_lantern(cx, cy, z0 + 1.1, h=5.6, r=1.3, finial=False)
        out += kit.swept_roof(cx, cy, 3.9, z0 + 7.2, 13.0, k=8, per_side=3, upturn=1.1, lip=0.45, sweep_pow=1.5)
        n, t = V((1, 0, 0)), V((0, 1, 0))
        out += kit.leaf_banner(V((cx, 0, 0)), t, n, cy, 39.0, 5.4, 19.0, d=2.05, free=True)
        return out

    def emphasis(self, c, n):
        if c.z > 86 or (c.x > 66 and abs(c.y) > 17):
            return 1.4                        # the flèche, the tree-house crowns, the gate towers
        return 1.15 if c.z > 44 else 1.0
