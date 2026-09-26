"""Elves green pasture (ElvenGreenPasture): EA's stable - a long stable of two hip-roofed wings,
four pointed stall arches on each side, either side of a square pavilion under a low blue dome,
beside a fenced paddock (the fence: elves/green_pasture_fence) - made a Rivendell stable:

- the pavilion's dome disappears inside an Elven crossing tower: a sixteen-sided drum with a
  ring of lancet windows between a silver base ring and a coping, under a slate spire whose eave turns
  up at every other corner (swan-neck eaves) over a gilt lip and birch soffit, a gilt leaf finial
  on top; no dome shows any more;
- the pavilion's round-headed gateway becomes a pointed portal: a silver frame with an enamel
  reveal and a slight leaf tip, a silver lintel at the springing and a tympanum of gilt leaf-lancet
  tracery over it, and a tall leaf banner on each of its flanking piers;
- the four stall arches on the paddock side get pointed silver frames with enamel reveals;
- the paddock side's piers carry leaf banners in the player's colour;
- each wing's ridge gets a crest of gilt leaf finials.

The banners' cloth leaves the body for EBHCStable and takes the player's colour. EA's trees (V1,
V1A) and the level-2 crown (V2) stay EA's.

Its bone is tilted 90 degrees: world_space, every number in model (world) axes, measured on EA's
model. The paddock side faces +x, towards the camera:
  wings     y -58.7..-14 and 14..57.8, x -63..-32.35; east wall x -32.35 up to z 27.9, eave soffit
            z 27.89 out to x -30.47; hip roofs rising 1:1 to ridges along x -45.9 at z 44.2
  stalls    east arches at y -40.59, -24.09, 22.91, 39.41: 11.5 wide, jambs to z 21.23, apex 26.73,
            recessed 3.0; piers between them y -34.84..-29.84, 28.66..33.66, outer piers
            -50.34..-46.34 and 45.16..49.23
  pavilion  x -62.9..-28.81, y -14.1..13.0 (centre y -0.55), walls to z 40.7; its east face
            x -28.81 with a round-headed gateway y -8.4..7.2 (jambs to z 27.3, crown z 34.3), recessed to
            x -32.3; ring cornice z 41.3..43.8 out to x -64.3..-29.2, y -16.2..15.1; the dome an
            ellipsoid round (-45.9, -0.55): base z 44.4 (rx 17.1, ry 14.6), 48.5 (16.1, 13.6), 53.1
            (12.5, 10.9), 56.0 (10.2, 8.4), 57.6 (5.8, 4.1), apex 59.04
Footprint x -67.95..-27.48, y -58.72..57.76 unchanged; height 58.3 (+20 % allowed: top 70.7)."""
from sagekit.building import Building

from ..style import ElvenStyle

EAST_X = -32.35
STALLS = (-40.59, -24.09, 22.91, 39.41)
STALL_HALF, STALL_SPRING, STALL_APEX, GROUND = 5.75, 21.23, 26.73, 0.75
PIERS = (-32.34, 31.16)                 # the outer piers stay bare: the end stalls' halos spill there
PAVILION_X, GATE_U, GATE_HALF, GATE_SPRING, GATE_APEX = -28.81, -0.6, 7.8, 27.3, 38.3
PAVILION_PIERS = (-11.8, 10.65)
PORTAL_BACK = -32.3                      # the gateway's recess: its back wall
DOME_C = (-45.9, -0.55)
DRUM_RX, DRUM_RY, DRUM_Z0, DRUM_Z1 = 17.9, 15.6, 43.7, 51.6     # on the ring cornice, round the dome
DRUM_WINDOW = (1.5, 45.3, 47.6, 50.0)                             # half, sill, springing, apex
ROOF_R, ROOF_EAVE, ROOF_H = 18.7, 51.75, 14.5      # the eave just over the drum's top: not coplanar
RIDGE_X, RIDGE_Z = -45.9, 44.2
HORN_GLOWS = [(-45.8, 60.95, 40.5), (-46.05, -61.55, 40.5)]     # EA's N_GLOW cards' centres (model axes)


class GreenPasture(Building):
    style = ElvenStyle()
    source = "EBStable_SKN"
    target = "EBBSTABLES"
    sheet = "EBStable.tga"
    sheet_normal = "EBStable_NRM.tga"
    own_textures = {"EBStable.tga": "EBStablH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    world_space = True                  # its bone is tilted 90 degrees
    tri_budget = 15000
    bake_hidden = ("P_ARWEN_C", "N_WINDOW", "N_GLOW")
    views = {
        "rts": ((-47.7, -0.5, 29.9), 300, 50, -38, 50),
        "close": ((-47.7, -0.5, 29.9), 177, 24, -30, 45),
        "ingame": ((-47.7, -0.5, 29.9), 682, 53, -62, 50),
        "stalls": ((-32.0, 0.0, 18.0), 110, 14, -5, 45),
        "roof": ((-45.9, -0.5, 52.0), 80, 30, -30, 45),
    }

    def design(self, kit):
        s = []
        s += self._crossing_roof(kit)           # 1. the roof over the dome
        s += self._portal(kit)                  # 1b. the pavilion's pointed portal
        s += self._stalls(kit)                  # 2. stall arch frames
        s += self._banners(kit)                 # 3. leaf banners on the piers
        s += self._ridges(kit)                  # 4. ridge crests
        return s

    # ------------------------------------------------------------------ 1. crossing roof
    @staticmethod
    def _crossing_roof(kit):
        """The drum: an ellipse (17.9 x 15.6, sides' middles 0.98 of that) on the ring cornice, clear of
        the dome's base (17.1 x 14.6) and closed top and bottom. The spire over it, slightly concave,
        clear of the dome everywhere (along x: at z 53.1 its radius is 16.9 against the dome's 12.5;
        at 56, 13.1 against 10.2; at 59, the dome's apex, 9.0). A side's middle faces +x (phase), so
        drum and eave stop at x -27.56, inside the footprint; the finial's tip is at z 70.2."""
        import math
        from sagekit.blender.geometry import loft
        from ..shapes import ring
        cx, cy = DOME_C
        ph = math.pi / 16

        def R(e, z):
            return ring(cx, cy, DRUM_RX + e, z, 16, ry=DRUM_RY + e, phase=ph)
        rings = [R(0.35, DRUM_Z0), R(0.35, DRUM_Z0 + 0.6), R(0.0, DRUM_Z0 + 0.6), R(0.0, DRUM_Z1 - 0.7),
                 R(0.3, DRUM_Z1 - 0.7), R(0.3, DRUM_Z1)]
        out = [loft(rings, ["trim", "top", "stoneA", "top", "coping"], cap0=("stoneB", True), cap1=("top", True))]
        from ..barracks.motifs import lancet_window
        for a, t, n in GreenPasture.drum_faces():
            out += lancet_window(kit, a, t, n, 0.0, *DRUM_WINDOW, w=0.45, d=0.3, finial=False, k=5)
        return out + kit.swept_roof(cx, cy, ROOF_R, ROOF_EAVE, ROOF_H, k=16, per_side=2, upturn=1.2, lip=0.35,
                                    sweep_pow=1.15, finial=True, phase=ph)

    @staticmethod
    def _portal(kit):
        """A pointed frame round EA's gateway, its intrados passing over EA's round head; the lunette
        between the springing and our point closed by a tympanum of gilt leaf-lancet tracery on a
        silver lintel (the passage below keeps its full width and 26.5 of its height); a tall leaf
        banner on each flanking pier."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        a, t, n = V((PAVILION_X, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        u, h = GATE_U, GATE_HALF
        out = kit.arch(a, t, n, u, h, GROUND, GATE_SPRING, GATE_APEX, w=1.1, d0=0.0, d1=1.0, ogee=0.25, k=8,
                       finial=False)
        tip = kit.arch_outline(h, GATE_SPRING, GATE_APEX, 0.0, 8)
        poly = [(u - h, GATE_SPRING), (u + h, GATE_SPRING)] + [(u + x, z) for x, z in tip[1:-1]] + \
               [(u, GATE_APEX)] + [(u - x, z) for x, z in reversed(tip[1:-1])]
        out.append(prism_uz(a, t, n, poly, -0.3, 0.15, [None] * len(poly), "lancet", None))
        out.append(prism_uz(a, t, n, [(u - h, GATE_SPRING - 0.9), (u + h, GATE_SPRING - 0.9), (u + h, GATE_SPRING + 0.1),
                                      (u - h, GATE_SPRING + 0.1)], -0.3, 0.55, [None, None, "top", None], "trim", None))
        for p in PAVILION_PIERS:
            out += kit.leaf_banner(a, t, n, p, 37.0, 3.3, 15.5, d=0.05)
        return out

    @staticmethod
    def drum_faces():
        """(a, t, n) of the drum's faces on the camera's side (outward normal x > -0.2)."""
        import math
        from mathutils import Vector as V
        from ..shapes import ring
        pts = ring(DOME_C[0], DOME_C[1], DRUM_RX, 0.0, 16, ry=DRUM_RY, phase=math.pi / 16)
        out = []
        for p, q in zip(pts, pts[1:] + pts[:1]):
            t = (q - p).normalized()
            n = V((t.y, -t.x, 0))
            if n.x > -0.2:
                out.append(((p + q) / 2, t, n))
        return out

    # ------------------------------------------------------------------ 2. stalls
    @staticmethod
    def _stalls(kit):
        from mathutils import Vector as V
        a, t, n = V((EAST_X, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        out = []
        for u in STALLS:
            out += kit.arch(a, t, n, u, STALL_HALF, GROUND, STALL_SPRING, STALL_APEX, w=0.75, d0=0.0, d1=0.7,
                            ogee=0.2, k=8, finial=False)
        return out

    # ------------------------------------------------------------------ 3. banners
    @staticmethod
    def _banners(kit):
        from mathutils import Vector as V
        a, t, n = V((EAST_X, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        out = []
        for u in PIERS:
            out += kit.leaf_banner(a, t, n, u, 25.4, 3.0, 12.5, d=0.05)
        return out

    # ------------------------------------------------------------------ 4. ridges
    @staticmethod
    def _ridges(kit):
        out = []
        for y in (-44.0, -34.0, -24.0, 22.0, 32.0, 42.0):
            out += kit.leaf_finial(RIDGE_X, y, RIDGE_Z - 0.3, 3.0 if abs(y) > 30 else 2.4, 1.0)
        return out

    @staticmethod
    def night_lights(kit):
        """The four stalls on the paddock side (EA's doors inside our frames), the portal, the drum's
        windows on the camera's side, and EA's two glow cards at the wings' end horns (its night
        lanterns hung there, outside the footprint our geometry keeps to: the glow stays, free)."""
        from sagekit.nightlights import Light
        h, z0, sp, ap = DRUM_WINDOW
        drum = [Light.arch(tuple(a), tuple(t), tuple(n), 0.0, h - 0.3, z0 + 0.3, sp, ap - 0.5, halo=False, reach=1.0,
                           name="drum %d" % i) for i, (a, t, n) in enumerate(GreenPasture.drum_faces())]
        return drum + [Light.rect((PORTAL_BACK, 0, 0), (0, 1, 0), (1, 0, 0), GATE_U - GATE_HALF + 0.4, GATE_U + GATE_HALF - 0.4,
                           GROUND + 0.2, GATE_SPRING - 1.2, kind="door", halo=False, reach=1.5, name="portal")] + [Light.arch((EAST_X, 0, 0), (0, 1, 0), (1, 0, 0), u, STALL_HALF - 0.6, GROUND + 0.2, STALL_SPRING,
                           STALL_APEX - 0.8, kind="door", reach=4.5, name="stall %+.0f" % u) for u in STALLS] + [
            Light.glow(c, 24.0, name="horn glow %+.0f" % c[1]) for c in HORN_GLOWS]

    def emphasis(self, c, n):
        if c.z > 43:
            return 1.4                          # the crossing roof and the ridge crests
        if c.x > -34 and c.z < 30:
            return 1.3                          # the paddock side
        return 1.0
