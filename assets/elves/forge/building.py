"""Elves forge (EregionForge): EA's Eregion forge - a hexagonal furnace tower, an arched hearth
where the elf smith works, a mallorn growing from a stone planter (its trunk and branches are part
of the body) and a weapon rack - made a Rivendell smithy:

- the furnace's chimney gets a gilt leaf coronet round its open flue, six small crystal lanterns on
  the rim between the leaves, a knotwork band (silver knots on sea-green enamel) under the cap and a
  leaf banner under it on each of its two camera-side faces (seen over the canopy);
- the main shaft gets a lancet window in a silver frame on each of its six faces and a knotwork
  band under its flare;
- the hearth gets a silver barge board with an enamel soffit along its pointed gable, a leaf finial
  on the apex, knotwork bands along its side walls and two leaf banners on the camera-side wall;
- the planter gets three crystal lanterns on its front rim;
- the mallorn carries three crystal lanterns hung on gilt rods where EA hung its night lanterns;
- the weapon rack flies a leaf pennant from a gilt pole over each post.

Cloth (banners, pennants) leaves the body for EBHCForge and takes the player's colour. EA's tree
(trunk and branches in the body, LEAVES, V2 upgrades) stays EA's: foliage is not stone.

All numbers are BOX01 coordinates (the mesh sits at the model's origin), measured on EA's model:
  tower     hexagon centred (-27.17, 0.65), vertices at 30 + 60k degrees: base R 15.5 (z 0..14),
            collar to z 32.6, main shaft R 11.9 (apothem 10.34) z 32.6..50.7, flare to 55.2,
            upper shaft R 9.2 (apothem 8.0) z 58.8..69.5, cap R 8.5 at 71.2 and 7.1 at its rim
            z 75.0; the flue is open: R 5.0 at the rim, floor 69.7. FXSMOKE at (-24.3, 0.1, 60.5)
            under the flue: nothing covers it
  hearth    walls x -13.7..-1.4, y -7.1..8.4 to z 13.9, a pointed vault over it: front gable
            outline (y, z) (-7.1, 13.9) (-5.3, 19.9) (-2.7, 22.6) (0.8, 24.0) (4.2, 23.3) (6.7, 19.9)
            (8.4, 13.9); the arched passage y -4.0..5.4, apex z 20.6, its ring out to x -0.5.
            FXFIRE at (-8.2, -0.7, 7.1) inside; the smith at x -1.1..5.9 (hammer bone y -7, z 10):
            nothing new in front of the hearth below z 17
  planter   a basin round (7, -33), its soil at z 17.0 and its rim's top at z 21.2 (inner edge R 10.3..11.2,
            outer 12.9..13.8); the front corners at -140, -90 and -40 degrees
  rack      posts (-5.6, 29.45) and (5.9, 43.15) to z 46.8 under a curved beam (ends z 49.1)
  lanterns  EA's night lanterns (N_WINDOW, night only) hang in the tree at (22.1, -32.4) z 49.7..59.8,
            (6.8, -6.0) z 50.7..60.7 and (-3.4, -46.7) z 54.9..65.0
Footprint x -41.32..24.03, y -45.94..46.98 unchanged; height 91.4 (+20 % allowed: top 109.0)."""
import math

from sagekit.building import Building

from ..style import ElvenStyle

TOWER = (-27.17, 0.65)
SHAFT_APOTHEM, UPPER_APOTHEM = 10.34, 8.0
CAP_TOP, FLUE_R, RIM_R = 75.0, 5.0, 7.1
HEARTH_FRONT = -1.4
# the hearth's front gable, half outline from its axis (u 0.8): eave to apex
GABLE_AXIS = 0.8
GABLE = [(7.9, 13.9), (6.1, 19.9), (3.5, 22.6), (0.0, 24.0)]
PLANTER_RIM = [(-140, 12.35), (-90, 11.6), (-40, 12.5)]       # (degrees, R) on the rim's middle
PLANTER_C, RIM_Z = (7.0, -33.0), 21.2
RACK = [(-5.6, 29.45), (5.9, 43.15)]
# EA's night lanterns in the tree (N_WINDOW): our crystal lanterns hang there, (x, y, branch z); the
# third one moved in from y -46.7 to stay inside the footprint
TREE_LANTERNS = [(22.1, -32.4, 59.8), (6.8, -6.0, 60.7), (-3.4, -44.4, 65.0)]
TREE_H, TREE_R, TREE_ROD = 5.2, 1.1, 1.2
HEARTH_BACK = -15.6                     # the hearth's back wall (y -4.0..5.4, z 4.7..14.5)
RACK_T = (0.642, 0.766)                 # along the rack, from the first post to the second


def hexagon(c, r, phase=30.0):
    """Closed path of a hexagon's vertices (radius r) round c."""
    pts = [(c[0] + r * math.cos(math.radians(phase + 60 * i)), c[1] + r * math.sin(math.radians(phase + 60 * i)))
           for i in range(6)]
    return pts + [pts[0]]


class Forge(Building):
    style = ElvenStyle()
    source = "EBForge_SKN"
    target = "BOX01"
    sheet = "ebforge.tga"
    sheet_normal = "ebforge_nrm.tga"
    own_textures = {"ebforge.tga": "ebforgH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    tri_budget = 15000
    # the smith and his gear stand in the hearth in the rest pose; the night meshes are light
    bake_hidden = ("ELF", "HAMMER", "FORGED_BLADE", "EULORWAR", "N_WINDOW", "N_GLOW")
    views = {
        "rts": ((-8.6, 0.5, 45.0), 321, 50, -38, 50),
        "close": ((-8.6, 0.5, 45.0), 190, 24, -30, 45),
        "ingame": ((-8.6, 0.5, 45.0), 729, 53, -62, 50),
        "chimney": ((-27.2, 0.7, 68.0), 75, 28, 160, 45),       # from behind: the tree hides it from the front
        "hearth": ((-4.0, -3.0, 13.0), 75, 20, -25, 45),
    }

    @property
    def sheet_atlas(self):
        """EA's forge sheet with mask hints (upscale pixels): the mallorn's bark (the sheet's bottom
        quarter) is bark, not stone; the anvil's rust-red plate is dark steel (iron), not stone
        flecked with gold; the copper knotwork band is a knotwork band (silver on enamel)."""
        a = super().sheet_atlas
        anvil = [(256, 0, 640, 780)]
        a.mask_hints = {"rock": [(0, 1536, 2048, 2048)], "stone": anvil, "grille": anvil, "rune": [(0, 800, 800, 920)]}
        return a

    def design(self, kit):
        s = []
        s += self._chimney(kit)                 # 1. coronet, lanterns, band
        s += self._shaft(kit)                   # 2. lancet windows, band
        s += self._hearth(kit)                  # 3. barge board, finial, bands, banners
        s += self._planter(kit)                 # 4. rim lanterns
        s += self._rack(kit)                    # 5. poles and pennants
        s += self._tree_lanterns(kit)           # 6. lanterns in the mallorn
        return s

    # ------------------------------------------------------------------ 1. chimney
    @staticmethod
    def _chimney(kit):
        from ..barracks.motifs import coronet
        cx, cy = TOWER
        out = coronet(kit, cx, cy, (FLUE_R + RIM_R) / 2 + 0.2, CAP_TOP, n=6, height=7.5, width=2.4,
                      phase=math.radians(30))
        for i in range(6):                      # lanterns on the rim over the face middles
            ang = math.radians(60 * i)
            r = (FLUE_R + RIM_R) / 2 - 0.2
            out += kit.crystal_lantern(cx + r * math.cos(ang), cy + r * math.sin(ang), CAP_TOP - 0.1, h=3.0, r=0.5)
        out += kit.filigree_band(hexagon(TOWER, UPPER_APOTHEM / math.cos(math.radians(30))), 64.4, 66.8,
                                 d=0.3, center=TOWER)
        from ..barracks.motifs import face
        for deg in (0, -60):                    # leaf banners on the camera-side faces of the upper shaft
            nx, ny = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            a, t, n = face((cx + UPPER_APOTHEM * nx, cy + UPPER_APOTHEM * ny), (nx, ny))
            out += kit.leaf_banner(a, t, n, 0.0, 63.6, 3.6, 9.5, d=0.05)
        return out

    # ------------------------------------------------------------------ 2. main shaft
    @staticmethod
    def _shaft(kit):
        from ..barracks.motifs import face, lancet_window
        cx, cy = TOWER
        out = []
        for i in range(6):
            ang = math.radians(60 * i)
            nx, ny = math.cos(ang), math.sin(ang)
            a, t, n = face((cx + SHAFT_APOTHEM * nx, cy + SHAFT_APOTHEM * ny), (nx, ny))
            out += lancet_window(kit, a, t, n, 0.0, 2.3, 36.4, 42.4, 46.2, w=0.75, d=0.5)
        out += kit.filigree_band(hexagon(TOWER, SHAFT_APOTHEM / math.cos(math.radians(30))), 48.9, 50.3,
                                 d=0.3, center=TOWER)
        return out

    # ------------------------------------------------------------------ 3. hearth
    @staticmethod
    def _hearth(kit):
        from mathutils import Vector as V
        from ..barracks.motifs import barge_board
        a, t, n = V((HEARTH_FRONT, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        out = barge_board(kit, a, t, n, GABLE_AXIS, GABLE, w=0.8, d0=-0.1, d1=0.85)
        out += kit.leaf_finial(HEARTH_FRONT + 0.35, GABLE_AXIS, GABLE[-1][1] + 1.3, 3.4)
        for y, sgn in ((-7.1, -1), (8.4, 1)):   # knotwork along each side wall's top
            out += kit.filigree_band([(-13.7, y), (HEARTH_FRONT, y)], 12.0, 13.3, d=0.3, center=(-7.5, 0.6))
        south = (V((0, -7.1, 0)), V((1, 0, 0)), V((0, -1, 0)))
        for u in (-11.0, -5.0):                 # leaf banners on the camera-side wall
            out += kit.leaf_banner(*south, u, 11.2, 3.2, 8.4, d=0.2)
        return out

    # ------------------------------------------------------------------ 4. planter
    @staticmethod
    def _planter(kit):
        out = []
        for ang, r in PLANTER_RIM:
            x, y = PLANTER_C[0] + r * math.cos(math.radians(ang)), PLANTER_C[1] + r * math.sin(math.radians(ang))
            out += kit.crystal_lantern(x, y, RIM_Z - 0.05, h=3.8, r=0.7)
        return out

    # ------------------------------------------------------------------ 5. rack
    @staticmethod
    def _rack(kit):
        from mathutils import Vector as V
        from ..shapes import turned
        out = []
        t = V((RACK_T[0], RACK_T[1], 0))
        n = V((t.y, -t.x, 0))                   # towards the camera (+x, -y)
        for (x, y), sgn in zip(RACK, (-1, 1)):
            out.append(turned(x, y, [(0.32, 46.4), (0.26, 49.8), (0.2, 55.0)], ["gilt", "gilt"], 8,
                              cap0=("gilt", False), cap1=("gilt", True)))
            out += kit.leaf_finial(x, y, 54.9, 2.4, 0.9)
            tt = t * sgn
            out += kit.pennant(V((x, y, 0)), tt, n * sgn, 0.25, 54.2, 9.0, 2.2)
        return out

    # ------------------------------------------------------------------ 6. tree lanterns
    @staticmethod
    def _tree_lanterns(kit):
        from ..barracks.motifs import hanging_lantern
        out = []
        for x, y, z in TREE_LANTERNS:
            out += hanging_lantern(kit, x, y, z, h=TREE_H, r=TREE_R, rod=TREE_ROD)
        return out

    night_surfaces = ()

    @staticmethod
    def night_lights(kit):
        """Starlight where EA's night lanterns glowed (our three lanterns in the tree), the planter's and
        the chimney's crystals, the hearth's back wall and the six lancet windows of the shaft."""
        from sagekit.nightlights import Light
        from ..barracks.motifs import crystal_light, hanging_base, lantern_glow
        cx, cy = TOWER
        out = [crystal_light(x, y, hanging_base(z, TREE_H, TREE_ROD), TREE_H, TREE_R, "tree %d" % i)
               for i, (x, y, z) in enumerate(TREE_LANTERNS)]
        out += [lantern_glow(x, y, hanging_base(z, TREE_H, TREE_ROD), TREE_H, "tree %d" % i)    # EA's glow
                for i, (x, y, z) in enumerate(TREE_LANTERNS)]                                  # cards' place
        for ang, r in PLANTER_RIM:
            x, y = PLANTER_C[0] + r * math.cos(math.radians(ang)), PLANTER_C[1] + r * math.sin(math.radians(ang))
            out.append(crystal_light(x, y, RIM_Z - 0.05, 3.8, 0.7, "planter %d" % ang, halo=False))
        r = (FLUE_R + RIM_R) / 2 - 0.2
        for i in (0, 5):                        # the chimney crystals facing the camera
            ang = math.radians(60 * i)
            out.append(crystal_light(cx + r * math.cos(ang), cy + r * math.sin(ang), CAP_TOP - 0.1, 3.0, 0.5,
                                     "chimney %d" % (60 * i), halo=False))
        out.append(Light.rect((HEARTH_BACK, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), -3.4, 4.8, 5.1, 14.1,
                              kind="door", reach=1.0, name="hearth"))
        for i in range(6):
            ang = math.radians(60 * i)
            nx, ny = math.cos(ang), math.sin(ang)
            a = (cx + SHAFT_APOTHEM * nx, cy + SHAFT_APOTHEM * ny, 0.0)
            out.append(Light.arch(a, (-ny, nx, 0.0), (nx, ny, 0.0), 0.0, 1.9, 36.8, 42.4, 45.6, reach=1.5,
                                  name="shaft %d" % (60 * i)))
        return out

    def emphasis(self, c, n):
        if c.z > 60:
            return 1.5                          # the chimney crown, seen over the canopy
        if c.y < -22 and c.z < 22:
            return 1.3                          # the planter at the front
        return 1.0
