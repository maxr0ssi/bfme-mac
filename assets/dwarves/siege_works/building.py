"""Dwarven siege works (DwarvenSiegeWorks, model DBForge): the forge hall and its great chimney
behind a walled pit whose floor is the two-leaf hatch the siege engines rise through.

All numbers are DWARFBUILDING mesh coordinates, measured from EA's model. The mesh hangs from bone
DWARFBUILDING at (27.71, 38.31, 49.08), so the ground is at z = -49.1 here, not 0 - which is why the
kit's wall motifs are called with a `dz` (and its talus, which has none, is re-made below).

    pit / hatch      x -52.5..-2.9, y -71.0..-11.9, rim top z -43.9. The hatch leaves (DBForgeDr)
                     hinge on x = -52.5 and x = -2.7 and stand up to z ~ -19.7 when open: nothing
                     new goes over the pit or inside x -54..-1.
    exit ramp        x -53.9..-1.5, y -75.2..-91.2 (the grille), toward the rally point at -Y
    side curbs       walkways x -64.2..-58.4 and 2.8..8.8, top z -38.3; stairs x 8.8..22.5,
                     y -45.6..-24.1 on the +X side
    slab pairs       x -65.3..-53.9 and -0.8..10.6, y -23.7..-12.7, tops z -29.4
    hall             roof z -26.5 over x -47.5..-7.8, y -5.4..7.9; the anvil stands on it
                     (x -35.4..-20.1); the left block overhangs its roof west of x -40
    chimney          shaft x -4.8..4.95, y -5.2..4.55 (z 8.5..20.7); cap octagon z 20.8..24.6;
                     flue rim +-3.8 at z 26 with the smoke bone SMOKE01 at its centre
"""
from sagekit.building import Building

from ..style import DwarvenStyle

GROUND = -49.1
HALL_ROOF = -26.5
CURB_TOP = -38.3
CAP_TOP = 24.6
# the chimney cap's octagon (its outer edge at z 24.6), closed
CAP = [(-7.1, -4.8), (-4.8, -7.3), (4.6, -7.3), (7.0, -4.9), (7.0, 4.5), (4.6, 6.9), (-4.8, 6.9), (-7.1, 4.6),
       (-7.1, -4.8)]
FLUE = (-0.05, -0.2)
# crown ring on the cap: bronze band, battered hexagon frieze, walk top, inner reveal (d outward)
CROWN = [(-2.6, 24.6), (0.35, 24.6), (0.35, 25.5), (0.05, 25.8), (-0.25, 28.4), (-2.0, 28.4), (-2.6, 27.8)]
CROWN_TAGS = [None, "trim", "top", "hex", "top", "stoneB", "stoneA"]
CROWN_TOP = 28.4
SHAFT = (-4.8, 4.95, -5.2, 4.55)             # chimney shaft box, z 8.5..20.7
# low battered plinth (d outward, z) for walls standing on this building's ground
TALUS = [(0, GROUND - 0.3), (3.0, GROUND - 0.3), (3.0, GROUND + 0.5), (1.0, GROUND + 4.6), (0.0, GROUND + 5.0)]
TALUS_TAGS = [None, "stoneB", "stoneA", "top", None]
PIT_CENTRE = (-27.7, -40.0)


class SiegeWorks(Building):
    style = DwarvenStyle()
    source = "DBForge"
    target = "DWARFBUILDING"
    sheet = "DBforge.tga"
    bake_hidden = ("N_GLOW", "FIRE CARDS")   # effect cards: no occlusion, no opaque placeholder in renders
    views = {                          # the automatic framing, pinned so before/after match exactly
        "rts": ((6.3, -2.35, 34.4), 345.0, 50, -38, 50),
        "close": ((6.3, -2.35, 34.4), 204.0, 24, -30, 45),
        "ingame": ((6.3, -2.35, 34.4), 784.0, 53, -62, 50),
        "top": ((6.3, -2.35, 30.0), 300.0, 89.5, -90, 50),
        "hall": ((0.0, 30.0, 40.0), 150.0, 30, -75, 45),
        "chimney": ((27.7, 38.3, 70.0), 90.0, 35, -45, 45),
        "anvil": ((2.7, 40.0, 31.0), 60.0, 30, -60, 45),   # the roof anvil: EA's Elven sheet vs our copy
    }

    def design(self, kit):
        solids = []
        solids += self._chimney_crown(kit)                                   # 1. the chimney
        solids += self._parapet(kit, [(-47.5, -5.4), (-8.0, -5.4)], HALL_ROOF,  # 2. hall roofline
                                [(0, 8.0, 39.5)], centre=(-27.7, 10.0))
        right = [(8.8, -45.6), (8.8, -64.8), (-1.5, -75.2)]                   # 3. curb parapets
        left = [(-64.0, -25.0), (-64.0, -64.9), (-53.9, -75.2)]
        for path in (right, left):
            solids += self._parapet(kit, path, CURB_TOP, [(0, 0.0, None), (1, 2.2, None)], centre=PIT_CENTRE)
        from sagekit.blender.geometry import sweep
        solids += sweep(right, TALUS, TALUS_TAGS, center=PIT_CENTRE)[0]      # 4. battered plinth
        for x0, x1 in ((-63.4, -55.8), (0.9, 8.9)):                         # 5. slab-pair caps
            solids += self._slab_cap(x0, x1, -24.4, -12.0, -29.7)
        solids += self._curb_friezes()                                       # 6. rune friezes
        for x0, x1 in ((-61.2, -54.8), (-0.6, 5.8)):                         # 7. exit pylons
            solids += self._pylon(x0, x1, -83.6, -76.0)
        solids += self._banners(kit)                                         # 8. Erebor-blue banners
        return solids

    # ------------------------------------------------------------------ banners
    @staticmethod
    def _banners(kit):
        """Erebor-blue banners on the camera-facing (+X, -Y) sides only:
        - the chimney: one down each of its +X and -Y sides, hung from the crown ring under the
          stepped gable and falling free in front of the cap, the corbels and the rune belt;
        - the hall front (y -5.4): one on each end pier (x -47.5..-43.3 and -12.2..-7.8, the
          stretches without openings: the forge's fire cards glow through the others), hung under
          the parapet's corbels;
        - the exit pylons: one on each pylon's -Y face under its rune belt, the rods clear of the
          exit ramp (x -53.9..-1.5).
        Nothing over the pit (x -54..-1 on the pit side), nothing in the siege engines' path."""
        from mathutils import Vector as V
        s = []
        fx, fy = FLUE
        s += kit.banner(V((CAP[3][0], 0, 0)), V((0, 1, 0)), V((1, 0, 0)), fy, 27.0, 5.0, 16.0, d=0.5, free=True)
        s += kit.banner(V((0, CAP[1][1], 0)), V((1, 0, 0)), V((0, -1, 0)), fx, 27.0, 5.0, 16.0, d=0.5, free=True)
        hall = (V((0, -5.4, 0)), V((1, 0, 0)), V((0, -1, 0)))
        for u in (-45.3, -10.0):
            s += kit.banner(*hall, u, -30.3, 3.6, 11.5, free=True)   # rods overhang the pier edges: closed
        exit_ = (V((0, -82.8, 0)), V((1, 0, 0)), V((0, -1, 0)))  # the pylons' -Y face at the top of the batter
        for u in (-58.0, 2.6):
            s += kit.banner(*exit_, u, -35.4, 3.8, 10.4, d=0.75, free=True)
        return s

    # ------------------------------------------------------------------ walls
    @staticmethod
    def _parapet(kit, path, top, runs, centre):
        """Coping swept along `path` on a wall whose top is at z `top` (the kit's PARAPET, lifted so
        its inner foot sits on the walk), with chevron slabs and corbels on `runs`: (segment, u0, u1)
        stretches of a segment (u1 None = to its end)."""
        from sagekit.blender.geometry import sweep
        from ..shapes import PARAPET, PARAPET_TAGS, lifted
        dz = top - 52.0
        solids, segs = sweep(path, lifted(PARAPET, dz), PARAPET_TAGS, center=centre)
        for si, u0, u1 in runs:
            a, b, t, n = segs[si]
            L = (b - a).length if u1 is None else u1
            a0 = a + t * u0
            L -= u0
            solids += kit.chevron_parapet(a0, t, n, L, dz=dz)
            k = max(1, round(L / 8.6))
            for i in range(k):
                solids.append(kit.corbel(a0, t, n, (i + 0.5) * L / k, dz=dz))
        return solids

    @staticmethod
    def _curb_friezes():
        """Rune friezes on the curbs' pit-side faces, between the slab pairs and the corners."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        out = []
        for x, nx in ((-58.4, 1), (2.8, -1)):
            a, t, n = V((x, -25.0, 0)), V((0, -1, 0)), V((nx, 0, 0))
            out.append(prism_uz(a, t, n, [(0, -42.9), (35.5, -42.9), (35.5, -39.3), (0, -39.3)], -0.3, 0.3,
                                ["stoneB", "stoneB", "top", "stoneB"], "rune", None))
            out.append(prism_uz(a, t, n, [(0, -39.3), (35.5, -39.3), (35.5, -38.7), (0, -38.7)], -0.3, 0.45,
                                ["stoneB", "trim", "top", "trim"], "trim", None))
        return out

    # ------------------------------------------------------------------ blocks
    @staticmethod
    def _slab_cap(x0, x1, y0, y1, z0):
        """A stepped hip cap binding a pair of slabs into one pier: bronze band, two battered
        steps and a ridge."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft
        xm = (x0 + x1) / 2

        def R(e, z, ch=0.3):
            return box_rings((x0 + e, x1 - e), (y0 + e, y1 - e), z, ch)
        rings = [R(0.0, z0), R(0.0, z0 + 1.3), R(0.5, z0 + 1.3), R(0.7, z0 + 3.1), R(1.3, z0 + 3.1),
                 R(1.5, z0 + 4.4)]
        body = loft(rings, ["trim", "top", "stoneB", "top", "stoneA"], cap0=("stoneB", True), cap1=("top", False))
        A, B = V((xm, y0 + 3.4, z0 + 7.2)), V((xm, y1 - 3.4, z0 + 7.2))     # ridge ends
        roof = loft([rings[-1], [A, A, A, B, B, B, B, A]],
                    [["stoneA", "stoneA", "tri|a", "stoneA", "stoneA", "stoneA", "tri|a", "stoneA"]],
                    cap0=("top", False), cap1=("top", False))
        return [body, roof]

    @staticmethod
    def _pylon(x0, x1, y0, y1):
        """A squat battered pylon flanking the exit ramp: stepped plinth, rune belt, corbelled
        triangle frieze and a stepped cap ending in a point (the fortress gate pylons, small)."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft
        z = GROUND - 0.5

        def R(e, zz, ch=0.5):
            return box_rings((x0 - e, x1 + e), (y0 - e, y1 + e), zz, ch)
        rings = [R(0.8, z), R(0.8, z + 2.4), R(0.3, z + 2.4), R(0.3, z + 3.6), R(0.0, z + 3.6),   # plinth
                 R(-0.8, z + 15.0), R(-0.4, z + 15.0), R(-0.4, z + 17.6), R(-0.8, z + 17.6),        # rune belt
                 R(-0.1, z + 18.4), R(-0.1, z + 20.4), R(-0.5, z + 20.8),                           # cornice
                 R(-1.4, z + 20.8), R(-1.6, z + 22.4), R(-2.3, z + 22.4), R(-2.4, z + 23.4, 0.3)]   # steps
        tags = ["stoneB", "top", "stoneB", "top", "stoneA", "top", "rune", "top", "trim", "tri", "trim",
                "top", "stoneB", "top", "stoneA"]
        out = [loft(rings, tags, cap0=("top", False), cap1=("top", False))]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        out.append(loft([R(-2.4, z + 23.4, 0.3), [V((cx, cy, z + 26.2))] * 8], ["trim"],
                        cap0=("top", False), cap1=("top", False)))
        return out

    # ------------------------------------------------------------------ chimney
    def _chimney_crown(self, kit):
        """Corbels under the cap, a rune belt on the shaft, and on the cap a battered crown ring
        (hexagon frieze) with stepped-pyramid corners and stepped gables, the flue left open."""
        from sagekit.blender.geometry import box_rings, loft, sweep
        out = []
        ss, segs = sweep(CAP, CROWN, CROWN_TAGS, center=FLUE)
        out += ss
        for i, (a, b, t, n) in enumerate(segs):
            L = (b - a).length
            if i % 2 == 0:                                   # chamfers: a stepped pyramid
                m = (a + b) / 2 - n * 1.0
                out += self._mini_pyramid(m.x, m.y, CROWN_TOP, 1.4)
            else:                                            # sides: a stepped gable
                out += self._mini_gable(a, t, n, L / 2, CROWN_TOP)
        xa, xb, ya, yb = SHAFT                               # rune belt on the shaft
        rings = []
        for e, zz in ((0.0, 11.0), (0.65, 11.0), (0.65, 11.6), (0.4, 11.6), (0.4, 14.2), (0.65, 14.2),
                      (0.65, 14.8), (0.0, 15.2)):
            rings.append(box_rings((xa - e, xb + e), (ya - e, yb + e), zz, 0.0))
        out.append(loft(rings, ["top", "trim", "top", "rune", "top", "trim", "top"],
                        cap0=("top", False), cap1=("top", False)))
        for u0, u1, v, axis, sgn, cap in ((xa, xb, ya, "y", -1, -7.3), (xa, xb, yb, "y", 1, 6.9),
                                          (ya, yb, xa, "x", -1, -7.1), (ya, yb, xb, "x", 1, 7.0)):
            reach = abs(cap - v)
            for s in (-0.3, 0.0, 0.3):
                u = (u0 + u1) / 2 + s * (u1 - u0)
                out.append(self._corbel(u, v, axis, sgn, reach, 17.6, 20.8))
        return out

    @staticmethod
    def _corbel(u, v, axis, sgn, reach, z0, z1, half=0.7):
        """A wedge from a shaft face (at `v` on `axis`) out by `reach` under an overhang at z1."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft

        def P(uu, d, z):
            w = v + sgn * d
            return V((uu, w, z)) if axis == "y" else V((w, uu, z))

        def ring(uu):
            return [P(uu, -0.2, z0), P(uu, reach, z1), P(uu, -0.2, z1)]
        return loft([ring(u - half), ring(u + half)], [["stoneB", None, None]],
                    cap0=("stoneB", True), cap1=("stoneB", True))

    @staticmethod
    def _mini_pyramid(cx, cy, z0, h):
        """The kit's step_pyramid at chimney scale: `h` is the lowest tier's half width."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft
        k = h / 3.9
        out = []
        tiers = [(3.9, 3.5, 0.0, 3.2, "stoneB"), (2.9, 2.7, 3.2, 4.6, "trim"), (1.9, 1.8, 4.6, 5.6, "stoneA")]
        for i, (h0, h1, a, b, tg) in enumerate(tiers):
            r0 = box_rings((cx - h0 * k, cx + h0 * k), (cy - h0 * k, cy + h0 * k), z0 + a, 0.12)
            r1 = box_rings((cx - h1 * k, cx + h1 * k), (cy - h1 * k, cy + h1 * k), z0 + b, 0.12)
            out.append(loft([r0, r1], [tg], cap0=("stoneB", i == 0), cap1=("top", True)))
        r0 = box_rings((cx - 1.8 * k, cx + 1.8 * k), (cy - 1.8 * k, cy + 1.8 * k), z0 + 5.6, 0.1)
        out.append(loft([r0, [V((cx, cy, z0 + 7.4))] * len(r0)], ["trim"], cap0=("top", False), cap1=("top", False)))
        return out

    @staticmethod
    def _mini_gable(a, t, n, s, z0):
        """The kit's step_gable at chimney scale, standing on the crown's walk top."""
        from sagekit.blender.geometry import prism_uz
        z = [z0, z0 + 0.8, z0 + 1.6, z0 + 3.4]
        out = []
        for poly, tags, front in (
                ([(s - 2.4, z[0]), (s + 2.4, z[0]), (s + 2.4, z[1]), (s - 2.4, z[1])], [None, "stoneB", "top", "stoneB"], "trim"),
                ([(s - 1.5, z[1]), (s + 1.5, z[1]), (s + 1.5, z[2]), (s - 1.5, z[2])], [None, "stoneB", "top", "stoneB"], "stoneA"),
                ([(s - 1.5, z[2]), (s + 1.5, z[2]), (s, z[3])], [None, "top", "top"], "stoneA")):
            out.append(prism_uz(a, t, n, poly, -1.9, -0.25, tags, front, "stoneA"))
        return out

    night_surfaces = ("ROCK",)                  # EA's night windows are in the rock

    @staticmethod
    def night_lights(kit):
        """EA's two windows in the rock either side of the works (world (-39, 38.6, 23.4) facing
        west, (40.6, 45.3, 23.4) facing east), in DWARFBUILDING coordinates."""
        from sagekit.nightlights import Light
        z = 23.4 + GROUND
        return [Light.rect((-65.7, 0.29, 0), (0, 1, 0), (-1, 0, 0), -2.4, 2.4, z - 2.9, z + 2.9, reach=4.0, name="west"),
                Light.rect((11.9, 6.99, 0), (0, 1, 0), (1, 0, 0), -2.4, 2.4, z - 2.9, z + 2.9, reach=4.0, name="east")]

    def emphasis(self, c, n):
        if c.z > 8:
            return 1.5                        # the chimney crown and belt
        if c.z > -30 and -48 < c.x < -7 and c.y > -8:
            return 1.3                        # the hall parapet
        return 1.1 if c.z > -40 else 1.0
