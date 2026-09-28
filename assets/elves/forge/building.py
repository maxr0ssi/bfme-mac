"""Elves forge (EregionForge): EA's Eregion forge kept whole - a hexagonal furnace tower, an arched
hearth where the elf smith works, a mallorn growing from a stone planter (its trunk and branches are
part of the body) and a weapon rack - crowned the citadel's way in silver and gold:

- the chimney, the forge's silhouette, gets a crown: a silver-rimmed hexagonal collar on EA's rim
  round the open flue, and on it a coronet of six tall gilt leaf blades at the corners with six
  smaller ones leaning out between them; a leaf banner hangs on its camera-side face;
- the main shaft gets a lancet window in a silver frame on each of its six faces;
- the hearth gets a silver barge board with an enamel soffit along its pointed gable, a gilt leaf
  finial on the apex and a leaf banner on its camera-side wall (the forge's two banners);
- the planter gets three crystal lanterns on its front rim;
- the mallorn carries three crystal lanterns hung on gilt rods where EA hung its night lanterns;
- the weapon rack's upturned beam gets a gilt leaf finial on each end.

Cloth leaves the body for EBHCForge and takes the player's colour. EA's tree (trunk and branches in
the body, LEAVES, V2 upgrades) stays EA's: foliage is not stone.

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
  rack      posts (-5.6, 29.45) and (5.9, 43.15) to z 46.8 under a curved beam, its ends upturned to z 49.1
            round (-6.05, 28.6) and (6.65, 43.75)
  lanterns  EA's night lanterns (N_WINDOW, night only) hang in the tree at (22.1, -32.4) z 49.7..59.8,
            (6.8, -6.0) z 50.7..60.7 and (-3.4, -46.7) z 54.9..65.0
Footprint x -41.32..24.03, y -45.94..46.98 unchanged; height 91.4 (+20 % allowed: top 109.0)."""
import math

from sagekit.building import Building

from ..style import ElvenStyle

TOWER = (-27.17, 0.65)
SHAFT_APOTHEM, UPPER_APOTHEM = 10.34, 8.0
HEARTH_FRONT = -1.4
# the hearth's front gable, half outline from its axis (u 0.8): eave to apex
GABLE_AXIS = 0.8
GABLE = [(7.9, 13.9), (6.1, 19.9), (3.5, 22.6), (0.0, 24.0)]
PLANTER_RIM = [(-140, 12.35), (-90, 11.6), (-40, 12.5)]       # (degrees, R) on the rim's middle
PLANTER_C, RIM_Z = (7.0, -33.0), 21.2
RACK_ENDS = [(-6.05, 28.6), (6.65, 43.75)]
RACK_TOP = 49.1
# the chimney's crown: a hexagonal collar on EA's rim (vertex radius CROWN_R, its inner face just
# outside the flue's mouth), (d, z) profile along the hexagon's faces; the coronet stands on it
CROWN_R = 6.2
CROWN = [(-0.95, 74.7), (0.95, 74.7), (1.1, 75.3), (1.1, 76.6), (0.85, 77.2), (-0.95, 77.2)]
CROWN_TAGS = [None, "trim", "stoneA", "trim", "trim", "stoneB"]
CROWN_TOP = 77.2
CORONET = dict(height=11.5, width=3.3)
# EA's night lanterns in the tree (N_WINDOW): our crystal lanterns hang there, (x, y, branch z); the
# third one moved in from y -46.7 to stay inside the footprint
TREE_LANTERNS = [(22.1, -32.4, 59.8), (6.8, -6.0, 60.7), (-3.4, -44.4, 65.0)]
TREE_H, TREE_R, TREE_ROD = 5.2, 1.1, 1.2
HEARTH_BACK = -15.6                     # the hearth's back wall (y -4.0..5.4, z 4.7..14.5)


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
        "chimney": ((-27.2, 0.7, 73.0), 100, 28, 160, 45),      # from behind: include the whole coronet
        "hearth": ((-4.0, -3.0, 13.0), 75, 20, -25, 45),
    }

    @property
    def sheet_atlas(self):
        """EA's forge sheet with mask hints (upscale pixels): the mallorn's bark (the sheet's bottom
        quarter) is bark, not stone; the anvil's rust-red plate is grey steel (the rock ramp), not
        stone flecked with gold nor teal glass; the copper knotwork band is a knotwork band (silver
        on enamel)."""
        a = super().sheet_atlas
        anvil = [(256, 0, 640, 780)]
        a.mask_hints = {"rock": [(0, 1536, 2048, 2048)] + anvil, "stone": anvil, "rune": [(0, 800, 800, 920)]}
        return a

    def design(self, kit):
        s = []
        s += self._chimney(kit)                 # 1. the crown, its banner
        s += self._shaft(kit)                   # 2. lancet windows
        s += self._hearth(kit)                  # 3. barge board, finial, banner
        s += self._planter(kit)                 # 4. rim lanterns
        s += self._rack(kit)                    # 5. finials on the beam's ends
        s += self._tree_lanterns(kit)           # 6. lanterns in the mallorn
        return s

    # ------------------------------------------------------------------ 1. chimney
    @staticmethod
    def _chimney(kit):
        """The crown on EA's rim: a hexagonal collar (silver lip and cornice round an ivory band, its
        inner face lining the flue's mouth) and the coronet, tall blades at the corners; the flue
        stays open for the smoke. A leaf banner on the upper shaft's face toward -60."""
        from sagekit.blender.geometry import sweep
        from ..barracks.motifs import coronet, face
        cx, cy = TOWER
        out = sweep(hexagon(TOWER, CROWN_R), CROWN, CROWN_TAGS, center=TOWER)[0]
        out += coronet(kit, cx, cy, CROWN_R * 0.93, CROWN_TOP, n=6, phase=math.radians(30), **CORONET)
        nx, ny = math.cos(math.radians(-60)), math.sin(math.radians(-60))
        a, t, n = face((cx + UPPER_APOTHEM * nx, cy + UPPER_APOTHEM * ny), (nx, ny))
        return out + kit.leaf_banner(a, t, n, 0.0, 67.8, 3.8, 11.0, d=0.05)

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
        return out

    # ------------------------------------------------------------------ 3. hearth
    @staticmethod
    def _hearth(kit):
        from mathutils import Vector as V
        from ..barracks.motifs import barge_board
        a, t, n = V((HEARTH_FRONT, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        out = barge_board(kit, a, t, n, GABLE_AXIS, GABLE, w=0.8, d0=-0.1, d1=0.85)
        out += kit.leaf_finial(HEARTH_FRONT + 0.35, GABLE_AXIS, GABLE[-1][1] + 1.3, 4.6, 1.6)
        south = (V((0, -7.1, 0)), V((1, 0, 0)), V((0, -1, 0)))
        return out + kit.leaf_banner(*south, -7.6, 12.6, 3.6, 9.4, d=0.2)

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
        out = []
        for x, y in RACK_ENDS:
            out += kit.leaf_finial(x, y, RACK_TOP - 0.3, 3.4, 1.2)
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
        """Starlight where EA's night lanterns glowed (our three lanterns in the tree), the planter's
        crystals, the hearth's back wall and the six lancet windows of the shaft."""
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
            return 1.5                          # the chimney's crown
        if c.y < -22 and c.z < 22:
            return 1.3                          # the planter at the front
        return 1.0
