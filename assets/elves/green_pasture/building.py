"""Elves green pasture (ElvenGreenPasture): EA's stable kept whole - two hip-roofed wings with
four pointed stall arches on each side, either side of a square pavilion under EA's blue lattice
dome, beside a fenced paddock (the fence: elves/green_pasture_fence) - and crowned the citadel's
way in silver and gold:

- EA's dome stays in view, ringed at its foot by a silver collar and crowned by a small lantern
  cupola on its apex: a gilt collar, four silver colonnettes round a starlight crystal, a swept
  slate cap and a gilt leaf finial (the pasture's one new stage, as the citadel's gatehouse flèche);
- the pavilion's cornice gets a crystal lantern on a silver post at each corner, and a tall leaf
  banner hangs on each of the gateway's flanking piers (the only two banners);
- each wing's ridge gets a silver cap and a gilt leaf finial on its middle.

The banners' cloth leaves the body for EBHCStable and takes the player's colour. EA's trees (V1,
V1A) and the level-2 crown (V2) stay EA's.

Its bone is tilted 90 degrees: world_space, every number in model (world) axes, measured on EA's
model. The paddock side faces +x, towards the camera:
  wings     y -58.7..-14 and 14..57.8, x -63..-32.35; east wall x -32.35 up to z 27.9, eave soffit
            z 27.89 out to x -30.47; roofs rising 1:1 to ridge beams (x -46.5..-45.2,
            top z 43.4) along the wings, EA's horns on blocks at their ends (|y| 55.3..58.7, z 44.5)
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
PAVILION_X, GATE_U, GATE_HALF, GATE_SPRING = -28.81, -0.6, 7.8, 27.3
PAVILION_PIERS = (-11.8, 10.65)
CORNICE_TOP = 43.8
# the cornice's chamfered corners (front x -27.6 at |y| 14.2, sides at y -16.4 / 15.3): lanterns on them
CORNER_LANTERNS = [(-29.6, -14.9), (-29.6, 13.9), (-62.0, -14.9), (-62.0, 13.9)]
PORTAL_BACK = -32.3                      # the gateway's recess: its back wall
DOME_C = (-45.9, -0.55)
DOME_FOOT = (17.1, 14.6, 44.4)           # the dome's base ellipse (rx, ry) and z, on the ring cornice
DOME_APEX = 59.04
# the cupola on the dome's apex (the dome is 5.8 x 4.1 at z 57.6): collar, lantern, cap
CUPOLA_Z0, CUPOLA_FLOOR, CUPOLA_TOP = 57.9, 59.7, 63.5
CUPOLA_POSTS, CUPOLA_ROOF = 1.75, (2.9, 3.6)          # posts' radius; the cap's eave radius and height
CRYSTAL = (CUPOLA_FLOOR + 0.1, 3.4, 1.0)              # z, h, r
RIDGE_X, RIDGE_Z = -45.85, 43.4                       # EA's ridge beams (x -46.5..-45.2) along the wings
RIDGES = [(16.5, 55.3), (-16.5, -56.4)]               # from the pavilion's cornice to the end horns' blocks
RIDGE_FINIALS = (35.4, -36.5)                         # at the beams' middle joints
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
        s += self._dome(kit)                    # 1. the dome's silver collar and its lantern cupola
        s += self._pavilion(kit)                # 2. corner lanterns, the gateway's two banners
        s += self._ridges(kit)                  # 3. silver ridges, gilt finials at the hips
        return s

    # ------------------------------------------------------------------ 1. the dome
    @staticmethod
    def _dome(kit):
        """A silver collar round the dome's foot (its inner face buried in the dome), and the cupola
        on the apex: its gilt collar's foot inside the dome, a lantern of four silver colonnettes
        round a starlight crystal, a silver cornice, a swept slate cap with a gilt leaf finial."""
        import math
        from sagekit.blender.geometry import loft, sweep
        from ..shapes import ring, turned
        cx, cy = DOME_C
        rx, ry, z = DOME_FOOT
        foot = [(p.x, p.y) for p in ring(cx, cy, rx, 0.0, 32, ry=ry)]
        prof = [(-0.4, z - 0.7), (0.55, z - 0.7), (0.7, z - 0.1), (0.5, z + 0.6), (-0.4, z + 0.9)]
        out = sweep(foot + foot[:1], prof, [None, "trim", "trim", "trim", None], center=DOME_C)[0]
        out.append(turned(cx, cy, [(2.3, CUPOLA_Z0), (2.3, CUPOLA_FLOOR - 0.9), (2.6, CUPOLA_FLOOR - 0.5),
                                   (2.6, CUPOLA_FLOOR)], ["gilt", "gilt", "trim"], 12, cap0=("gilt", False),
                          cap1=("top", True)))
        for i in range(4):
            ang = math.pi / 4 + i * math.pi / 2
            px, py = cx + CUPOLA_POSTS * math.cos(ang), cy + CUPOLA_POSTS * math.sin(ang)
            out.append(turned(px, py, [(0.24, CUPOLA_FLOOR - 0.05), (0.2, CUPOLA_TOP - 0.3), (0.3, CUPOLA_TOP)],
                              ["trim", "trim"], 6, cap0=("top", False), cap1=("top", True)))
        out += kit.crystal_lantern(cx, cy, CRYSTAL[0], h=CRYSTAL[1], r=CRYSTAL[2], finial=False)
        out.append(loft([ring(cx, cy, 2.2, CUPOLA_TOP - 0.1, 12), ring(cx, cy, 2.6, CUPOLA_TOP + 0.3, 12),
                         ring(cx, cy, 2.6, CUPOLA_TOP + 0.6, 12)], ["trim", "trim"], cap0=("trim", True),
                        cap1=("top", True)))
        r, h = CUPOLA_ROOF
        return out + kit.swept_roof(cx, cy, r, CUPOLA_TOP + 0.5, h, k=8, per_side=2, upturn=0.6, lip=0.3,
                                    sweep_pow=1.4, finial=True, phase=math.pi / 8)

    # ------------------------------------------------------------------ 2. the pavilion
    @staticmethod
    def _pavilion(kit):
        """A starlight crystal in a gilt cup on a slender silver post on each corner of the ring
        cornice (as the citadel's ring lanterns), and a tall leaf banner on each of the gateway's
        flanking piers; EA's round-headed gateway and its carved leaf ornament stay in view."""
        from mathutils import Vector as V
        from ..shapes import turned
        z = CORNICE_TOP - 0.1
        out = []
        for cx, cy in CORNER_LANTERNS:
            out.append(turned(cx, cy, [(1.1, z), (1.1, z + 0.45), (0.75, z + 0.8), (0.5, z + 1.4), (0.42, z + 4.0),
                                       (0.85, z + 4.5)], ["trim"] * 5, 10, cap0=("trim", False), cap1=("trim", True)))
            out += kit.crystal_lantern(cx, cy, z + 4.4, h=5.2, r=1.05)
        a, t, n = V((PAVILION_X, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        for p in PAVILION_PIERS:
            out += kit.leaf_banner(a, t, n, p, 37.0, 3.3, 15.5, d=0.05)
        return out

    # ------------------------------------------------------------------ 3. ridges
    @staticmethod
    def _ridges(kit):
        """A silver cap astride each wing's ridge beam from the pavilion's cornice to the blocks under
        EA's end horns (its underside sunk into the beam), a gilt leaf finial on its middle joint."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        out = []
        for y0, y1 in RIDGES:
            a, t = V((RIDGE_X, 0, 0)), V((0, 1 if y1 > y0 else -1, 0))
            n = V((t.y, -t.x, 0))
            u0, u1 = abs(y0), abs(y1)
            q = [(u0, RIDGE_Z - 0.45), (u1, RIDGE_Z - 0.45), (u1, RIDGE_Z + 0.45), (u0, RIDGE_Z + 0.45)]
            out.append(prism_uz(a, t, n, q, -0.85, 0.85, [None, "trim", "trim", "trim"], "trim", "trim"))
        for y in RIDGE_FINIALS:
            out += kit.leaf_finial(RIDGE_X, y, RIDGE_Z + 0.35, 4.6, 1.6)
        return out

    @staticmethod
    def night_lights(kit):
        """The four stalls on the paddock side (EA's doors), the gateway, the cupola's crystal and
        the pavilion's corner lanterns, and EA's two glow cards at the wings' end horns (its night lanterns hung
        there, outside the footprint our geometry keeps to: the glow stays, free)."""
        from sagekit.nightlights import Light
        from ..motifs import crystal_light, lantern_glow
        cx, cy = DOME_C
        z, h, r = CRYSTAL
        out = [crystal_light(cx, cy, z, h, r, "cupola"), lantern_glow(cx, cy, z, h, "cupola", size=12.0)]
        out += [crystal_light(x, y, CORNICE_TOP + 4.3, 5.2, 1.05, "corner %+.0f %+.0f" % (x, y))
                for x, y in CORNER_LANTERNS if x > -40]
        out.append(Light.rect((PORTAL_BACK, 0, 0), (0, 1, 0), (1, 0, 0), GATE_U - GATE_HALF + 0.4, GATE_U + GATE_HALF - 0.4,
                              GROUND + 0.2, GATE_SPRING - 1.2, kind="door", halo=False, reach=1.5, name="portal"))
        out += [Light.arch((EAST_X, 0, 0), (0, 1, 0), (1, 0, 0), u, STALL_HALF - 0.6, GROUND + 0.2, STALL_SPRING,
                           STALL_APEX - 0.8, kind="door", reach=4.5, name="stall %+.0f" % u) for u in STALLS]
        return out + [Light.glow(c, 24.0, name="horn glow %+.0f" % c[1]) for c in HORN_GLOWS]

    def emphasis(self, c, n):
        if c.z > 43:
            return 1.4                          # the dome's crown and the ridges
        if c.x > -34 and c.z < 30:
            return 1.3                          # the paddock side
        return 1.0
