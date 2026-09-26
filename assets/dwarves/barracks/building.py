"""Dwarven barracks (DwarfBarracks, dwarfbarracks.ini): EA's hall of warriors - a gate cut into a
rock under a seated stone dwarf, between two stair wings whose prows point at the camera - made a
Dwarven war-hall:

- the gate becomes a monumental door: a deep stepped pointed portal (triangle-frieze rings, bronze
  reveals) round EA's doorway with a gold rune tympanum, a rune lintel, a bronze cornice with two
  gilded pinnacles and a stepped frontispiece (triangle tier, bronze tier, stone gable) crowned by
  a gilded finial; an Erebor-blue banner hangs on each jamb;
- each wing's prow gets a keel buttress on its nose, a gold rune cornice band with a bronze corbel
  and coping round its rim, solid chevron parapets with gilded tips, and five piers with rune belts
  and gilded points - the nose pier a tall diamond one flying a small banner.

The banner cloth leaves the body for EBHCBarracks and takes the player's colour in game.

The model (EBBarracks_SKN, skeleton EBBarracks_SKL) is the body EBBARRAKA (the target; rigid, at
the origin), the ROCK, the level-2 seated dwarf V1 and level-3 watch tower V2, the weapon racks,
the torches (EBBARRAKFIREA), the night windows and an animated dwarf. All numbers are EBBARRAKA
coordinates measured on the original. The building faces the diagonal (1, -1): here
u = (x + y)/sqrt 2 runs across the front (to the camera's right) and d = (x - y)/sqrt 2 towards
the camera.
  gate: axis u -0.2; EA's doorway |u| <= 4.6 up to z 14.7, shoulders to a flat head at z 20.4;
    its stepped frame's front d 32.3..33, |u| <= 10.2 (13.1 at the foot), point z 24.9
  torch pedestals: |u| 7.6..11.8, d 36.8..40.8 (fires to z 10.4) - the portal stays behind d 36.3
  night windows in the rock: |u| 13..22, d 29..35, z 9..18 - nothing new there below z 19
  racks: |u| 11..28, d 33..43 (pikes to z 36.5 at |u| 16..26) - the yard stays empty
  V1 (level 2): its lap and forearms reach d 31 at z 28..32, d 33 at z 32..36, d 35 at 36..40
    (|u| <= 5): the crown stands in front of those planes
  wing A (x 6..67, y -7.5..26.6; wing B is its mirror in the line y = -x): a battered prow (base
    to the nose x 66.9 at y 8.7; walls with panels z 2.6..12.5) round a sunken stair well (floor
    z 9.6, x 48..56, |y - 8.7| <= 6.2), its rim top z 15.7 along (44, -0.6) (53, -0.5) (59.3, 8.7)
    (53, 17.3) (44, 17.5); the stair climbs from the well into the rock to a walkway at z 25
Footprint x -38.61..66.91, y -67.23..38.08 unchanged; height 41.16 (+20 % allowed: 49.4)."""
import math

from sagekit.building import Building

from ..style import DwarvenStyle
from . import fixes

fixes.apply()

R2 = math.sqrt(2.0)
GATE_U = -0.2                                   # the gate's axis
ARCH = [(5.2, 0.0), (5.2, 15.0), (3.6, 20.2), (0.0, 23.4)]     # half outline from the axis
PORTAL_BACK, PORTAL_FRONTS, PORTAL_DEPTHS = 31.5, (34.2, 35.2, 36.2), (0.0, 1.6, 3.2)
PORTAL_U, LINTEL = 12.4, 29.0
# the prow rim (wing A) and the band round it: (d out of the rim line, z)
RIM = [(44.0, -0.6), (53.0, -0.5), (59.3, 8.7), (53.0, 17.3), (44.0, 17.5)]
RIM_CENTRE = (47.0, 8.6)
BAND = [(1.6, 10.8), (2.5, 11.6), (2.5, 12.2), (2.2, 12.2), (2.2, 15.0), (2.6, 15.0), (2.6, 16.0),
        (-1.6, 16.0), (-1.6, 15.2)]
BAND_TAGS = ["stoneB", "trim", "trim", "rune", "trim", "trim", "top", "stoneB", "stoneB"]
BAND_TOP = 16.0
NOSE = (59.6, 8.7)                              # the diamond nose pier's centre
AXIS_Y = 8.7                                    # wing A's axis


def mirror(solids):
    """Wing A's solids as wing B's: reflected in the line y = -x, re-oriented."""
    from mathutils import Vector as V
    for s in solids:
        for poly in s.polys:
            poly[0] = [V((-p.y, -p.x, p.z)) for p in poly[0]]
        s.orient()
    return solids


def chevrons(a, t, n, L, z, d0, d1, w=7.0, g=(1.0, 2.0), tip="trim"):
    """A solid parapet of stepped-triangle slabs along u = 0..L: z = (foot, slab top, step 1,
    step 2, point); d0..d1 its thickness along n."""
    from sagekit.blender.geometry import prism_uz
    z0, zb, z1, z2, za = z
    k = max(1, round(L / w))
    w = L / k
    g1, g2 = g
    out = []
    for i in range(k):
        u0, u1 = i * w, (i + 1) * w
        out.append(prism_uz(a, t, n, [(u0, z0), (u1, z0), (u1, zb), (u0, zb)], d0, d1,
                            [None, "stoneB", "top", "stoneB"], "stoneB", "stoneA", bat=0.03))
        out.append(prism_uz(a, t, n, [(u0 + g1, zb), (u1 - g1, zb), (u1 - g1, z1), (u0 + g1, z1)], d0 + 0.2, d1 - 0.3,
                            [None, "stoneB", "top", "stoneB"], "stoneA", "stoneA"))
        out.append(prism_uz(a, t, n, [(u0 + g2, z1), (u1 - g2, z1), (u1 - g2, z2), (u0 + g2, z2)], d0 + 0.4, d1 - 0.5,
                            [None, "stoneB", "top", "stoneB"], "trim", "stoneA"))
        out.append(prism_uz(a, t, n, [(u0 + g2, z2), (u1 - g2, z2), ((u0 + u1) / 2, za)], d0 + 0.4, d1 - 0.5,
                            [None, tip, tip], "stoneA", "stoneA"))
    return out


def pyramid(ring, apex, tag="trim"):
    from mathutils import Vector as V
    from sagekit.blender.geometry import loft
    return loft([ring, [V(apex)] * len(ring)], [tag], cap0=("top", False), cap1=("top", False))


def gate_frame():
    """(anchor on the gate axis, t across the front, n towards the camera): t x n = -z."""
    from mathutils import Vector as V
    t, n = V((1 / R2, 1 / R2, 0)), V((1 / R2, -1 / R2, 0))
    return t * GATE_U, t, n


class Barracks(Building):
    style = DwarvenStyle()
    source = "EBBarracks_SKN"
    target = "EBBARRAKA"
    sheet = "EBBarracks.tga"                    # own texture EBBarrackH.tga (+ _NRM, _Snow)
    tri_budget = 15000
    # the animated dwarf and his gear stand at the origin in the rest pose (inside the rock); the
    # torches and the night windows are light, not stone: none of them should shade the sheet
    bake_hidden = ("DWARF", "AXE", "SHIELD", "SHOULDER", "EBBARRAKFIREA", "N_WINDOW", "N_GLOW")
    views = {
        "rts": ((14, -14, 22), 330, 50, -38, 50),
        "close": ((22, -22, 20), 200, 24, -40, 45),
        "ingame": ((14, -14, 20), 760, 53, -62, 50),
        "gate": ((26, -27, 20), 95, 12, -45, 40),
        "prow": ((56, 4, 14), 80, 22, -30, 45),
    }

    def design(self, kit):
        s = []
        s += self._portal(kit)                  # 1. the stepped pointed portal
        s += self._tympanum_and_lintel()        # 2. rune tympanum, rune lintel, cornice
        s += self._crown()                      # 3. stepped frontispiece, gilded finial, pinnacles
        s += self._gate_banners(kit)            # 4. banners on the jambs
        wing = self._wing(kit)                  # 5. prow: keel, rune band, parapets, piers, banner
        s += wing
        s += mirror(self._wing(kit))
        return s

    # ------------------------------------------------------------------ 1. portal
    def _portal(self, kit):
        """Rings following ARCH, each from PORTAL_BACK (inside EA's frame) out to its own front;
        the inner rings carry the triangle frieze, the reveals are bronze (the innermost stone);
        the outer ring fills out to |u| 12.4 and up to the lintel. Its outer sides show (the
        rock face there is further back)."""
        from sagekit.blender.geometry import loft
        a, t, n = gate_frame()
        out = []

        def P(u, d, z):
            return a + t * u + n * d + type(a)((0, 0, z))

        def piece(poly, d1, tags, front):
            for side in (1, -1):
                r0 = [P(side * u, PORTAL_BACK, z) for u, z in poly]
                r1 = [P(side * u, d1, z) for u, z in poly]
                out.append(loft([r0, r1], [tags], cap0=("stoneB", True), cap1=(front, True)))
        for i, d1 in enumerate(PORTAL_FRONTS):
            inner = kit.arch_offset(ARCH, PORTAL_DEPTHS[i])
            rv = "stoneA" if i == 0 else "trim|a"
            if i < len(PORTAL_FRONTS) - 1:
                outer = kit.arch_offset(ARCH, PORTAL_DEPTHS[i + 1])
                for k in range(3):
                    piece([inner[k], outer[k], outer[k + 1], inner[k + 1]], d1, [None, None, None, rv], "tri|a")
            else:
                j0, j1, sh, ap = inner
                piece([j0, (PORTAL_U, 0.0), (PORTAL_U, j1[1]), j1], d1, [None, "stoneB", None, rv], "stoneB")
                piece([j1, (PORTAL_U, j1[1]), (PORTAL_U, LINTEL), (sh[0], LINTEL), sh], d1,
                      [None, "stoneB", None, None, rv], "stoneB")
                piece([sh, (sh[0], LINTEL), (0.0, LINTEL), ap], d1, [None, None, None, rv], "stoneB")
        # a stepped plinth at each jamb's foot (in front of the ring, behind the torch pedestals)
        from sagekit.blender.geometry import prism_uz
        j0 = kit.arch_offset(ARCH, PORTAL_DEPTHS[-1])[0]
        for side in (1, -1):
            u0, u1 = sorted((side * (j0[0] - 0.2), side * (PORTAL_U + 0.2)))
            out.append(prism_uz(a, t, n, [(u0, 0.0), (u1, 0.0), (u1, 2.4), (u0, 2.4)], PORTAL_BACK + 1.0, 36.6,
                                [None, "stoneB", "top", "stoneB"], "stoneB", "stoneB"))
            out.append(prism_uz(a, t, n, [(u0 + 0.2, 2.4), (u1 - 0.2, 2.4), (u1 - 0.2, 3.1), (u0 + 0.2, 3.1)],
                                PORTAL_BACK + 1.0, 36.45, [None, "trim", "top", "trim"], "trim", "stoneB"))
        return out

    # ------------------------------------------------------------------ 2. tympanum, lintel
    @staticmethod
    def _tympanum_and_lintel():
        from sagekit.blender.geometry import prism_uz
        a, t, n = gate_frame()
        hw = 3.6 - 3.6 * (20.4 - 20.2) / 3.2
        out = [prism_uz(a, t, n, [(-hw, 20.4), (hw, 20.4), (0.0, 23.4)], PORTAL_BACK - 0.3, 33.6,
                        ["trim", None, None], "rune", "stoneB")]
        # rune lintel block over the rings, then the bronze cornice (its back clear of V1's lap)
        out.append(prism_uz(a, t, n, [(-PORTAL_U, LINTEL), (PORTAL_U, LINTEL), (PORTAL_U, 31.6), (-PORTAL_U, 31.6)],
                            PORTAL_BACK, 36.6, [None, "stoneB", "top", "stoneB"], "rune", "stoneB"))
        out.append(prism_uz(a, t, n, [(-13.4, 31.6), (13.4, 31.6), (13.4, 32.4), (-13.4, 32.4)],
                            33.4, 37.4, ["trim", "trim", "top", "trim"], "trim", "trim"))
        return out

    # ------------------------------------------------------------------ 3. crown
    @staticmethod
    def _crown():
        """A stepped frontispiece standing on the cornice, thin enough to stay in front of V1's
        forearms (d <= 35 at z 36..40): triangle tier, bronze tier, stone gable, gilded finial;
        a gilded pinnacle on each end of the cornice."""
        from sagekit.blender.geometry import prism_uz
        a, t, n = gate_frame()
        out = []
        for poly, d0, d1, tags, front in (
                ([(-10.8, 32.4), (10.8, 32.4), (10.8, 35.0), (-10.8, 35.0)], 34.2, 37.0,
                 [None, "stoneB", "top", "stoneB"], "tri"),
                ([(-8.2, 35.0), (8.2, 35.0), (8.2, 37.6), (-8.2, 37.6)], 35.6, 36.8,
                 [None, "trim", "top", "trim"], "trim"),
                ([(-6.2, 37.6), (6.2, 37.6), (0.0, 43.0)], 35.6, 36.8, [None, "top", "top"], "stoneA")):
            out.append(prism_uz(a, t, n, poly, d0, d1, tags, front, "stoneB"))
        out.append(prism_uz(a, t, n, [(-0.9, 41.6), (0.9, 41.6), (0.9, 43.4), (-0.9, 43.4)], 35.5, 36.9,
                            ["stoneB", "trim", "top", "trim"], "trim", "trim"))
        out.append(prism_uz(a, t, n, [(-0.9, 43.4), (0.9, 43.4), (0.0, 46.0)], 35.5, 36.9,
                            [None, "trim", "trim"], "trim", "trim"))
        for side in (1, -1):
            u0, u1 = sorted((side * 11.6, side * 13.2))
            out.append(prism_uz(a, t, n, [(u0, 32.4), (u1, 32.4), (u1, 34.6), (u0, 34.6)], 33.8, 36.8,
                                [None, "stoneB", "top", "stoneB"], "stoneA", "stoneB"))
            out.append(prism_uz(a, t, n, [(u0, 34.6), (u1, 34.6), ((u0 + u1) / 2, 37.4)], 33.8, 36.8,
                                [None, "trim", "trim"], "trim", "trim"))
        return out

    # ------------------------------------------------------------------ 4. gate banners
    @staticmethod
    def _gate_banners(kit):
        """One banner on each jamb front, under the rune lintel and above the torches (z 10.4)."""
        a, t, n = gate_frame()
        j = (5.2 + 3.2 + PORTAL_U) / 2
        s = []
        for u in (-j, j):
            s += kit.banner(a, t, n, u, 27.6, 3.0, 13.8, d=PORTAL_FRONTS[-1])
        return s

    # ------------------------------------------------------------------ 5. a wing's prow
    def _wing(self, kit):
        s = []
        s += self._keel()
        s += self._band()
        s += self._parapets()
        s += self._piers()
        s += self._nose_pier(kit)
        return s

    @staticmethod
    def _keel():
        """A buttress on the prow's nose: a wedge (front at 45 degrees) whose back is buried in the
        prow: plinth, battered body, bronze step, sloped top under the rune band."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        back = 58.5

        def ring(xt, w, z):
            y = AXIS_Y
            return [V((xt, y, z)), V((xt - w, y + w, z)), V((back, y + w, z)), V((back, y - w, z)), V((xt - w, y - w, z))]
        rings = [ring(66.8, 2.6, 0.0), ring(66.8, 2.6, 1.3), ring(65.8, 2.2, 1.3), ring(65.0, 2.2, 9.2),
                 ring(65.4, 2.4, 9.2), ring(65.4, 2.4, 10.0), ring(65.0, 2.2, 10.0), ring(63.4, 2.2, 11.4)]
        tags = ["stoneB", "top", "stoneA", "trim", "trim", "top", "top"]
        return [loft(rings, tags, cap0=("stoneB", False), cap1=("top", True))]

    @staticmethod
    def _band():
        """Round the rim's outer edge: a bronze corbel, the gold rune band, a bronze coping and a
        walk-top over EA's rim (open ends: the end piers stand on them)."""
        from sagekit.blender.geometry import sweep
        return sweep(RIM, BAND, BAND_TAGS, cap_start=False, cap_end=False, center=RIM_CENTRE)[0]

    @staticmethod
    def _parapets():
        """Chevron parapets between the piers, on the band's walk-top (d -0.6..1.6 of the rim line)."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import sweep
        _, segs = sweep(RIM, BAND, BAND_TAGS, center=RIM_CENTRE)
        s = []
        gaps = [(2.0, 2.0), (2.0, 3.0), (3.0, 2.0), (2.0, 2.0)]        # clear of the piers
        for (a, b, t, n), (g0, g1) in zip(segs, gaps):
            L = (b - a).length
            a3 = V((a.x + t.x * g0, a.y + t.y * g0, 0))
            s += chevrons(a3, t, n, L - g0 - g1, (BAND_TOP - 0.05, 17.9, 18.9, 19.9, 21.6), -0.6, 1.6, w=6.0,
                          g=(0.8, 1.6))
        return s

    @staticmethod
    def _piers():
        """Square piers on the rim's two corners and back ends: shaft, bronze belts round a gold
        rune belt, bronze cap, gilded point."""
        from sagekit.blender.geometry import box_rings, loft
        s = []
        for cx, cy in ((53.0, -0.5), (53.0, 17.3), (44.1, -0.7), (44.1, 17.7)):
            def R(z, h):
                return box_rings((cx - h, cx + h), (cy - h, cy + h), z, 0.35)
            rings = [R(14.6, 1.7), R(21.2, 1.7), R(21.2, 2.0), R(21.8, 2.0), R(21.8, 1.8), R(23.6, 1.8),
                     R(23.6, 2.05), R(24.3, 2.05), R(24.3, 1.5)]
            s.append(loft(rings, ["stoneA", "trim", "trim", "top", "rune", "trim", "trim", "top"],
                          cap0=("stoneB", False), cap1=("top", True)))
            s.append(pyramid(box_rings((cx - 1.5, cx + 1.5), (cy - 1.5, cy + 1.5), 24.3, 0.3), (cx, cy, 28.2)))
        # the back piers' feet close the band's open ends (its profile is not convex, so not capped)
        for y0, y1 in ((-3.5, 1.3), (15.8, 20.4)):
            s.append(loft([box_rings((42.9, 45.5), (y0, y1), 10.5, 0), box_rings((42.9, 45.5), (y0, y1), 16.3, 0)],
                          ["stoneB"], cap0=("stoneB", False), cap1=("top", True)))
        return s

    @staticmethod
    def _nose_pier(kit):
        """The prow's crown: a diamond pier over the nose (square 3.8 turned 45 degrees), rune belt,
        bronze cap and a tall gilded point, flying a small banner on its camera-side face."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft, rect_ring
        t, n = (1 / R2, 1 / R2), (1 / R2, -1 / R2)

        def R(z, h, ch=0.3):
            return rect_ring(NOSE, t, n, -h, h, -h, h, z, ch)
        rings = [R(14.8, 1.9), R(23.2, 1.9), R(23.2, 2.2), R(23.8, 2.2), R(23.8, 2.0), R(25.8, 2.0),
                 R(25.8, 2.25), R(26.4, 2.25), R(26.4, 1.7)]
        s = [loft(rings, ["stoneA", "trim", "trim", "top", "rune", "trim", "trim", "top"],
                  cap0=("stoneB", False), cap1=("top", True)),
             pyramid(R(26.4, 1.7, 0.3), (NOSE[0], NOSE[1], 31.6))]
        a = V((NOSE[0], NOSE[1], 0))
        s += kit.banner(a, V((t[0], t[1], 0)), V((n[0], n[1], 0)), 0.0, 22.4, 2.6, 5.8, d=1.9)
        return s

    night_surfaces = ("ROCK",)                  # EA's night windows are in the rock

    @staticmethod
    def night_lights(kit):
        """The gate (EA's doorway inside our portal) and EA's four windows in the rock, two either
        side of the gate behind the racks, one on each flank."""
        from sagekit.nightlights import Light
        a, t, n = gate_frame()
        door = [(-5.2, 0.2), (5.2, 0.2), (5.2, 15.0), (3.8, 19.5), (-3.8, 19.5), (-5.2, 15.0)]     # our portal's
        # jambs up to EA's doorway head (z 19.5, under the tympanum)
        out = [Light(tuple(a + n * 32.3), tuple(t), tuple(n), door, kind="door", reach=5.0, name="gate")]
        for u in (-17.5, 17.3):
            out.append(Light.rect(tuple(n * 31.5), tuple(t), tuple(n), u - 2.3, u + 2.3, 10.8, 16.6, reach=4.0,
                                  name="front %+.0f" % u))
        out.append(Light.rect((-33.0, -27.3, 0), (0, 1, 0), (-1, 0, 0), -2.3, 2.3, 6.1, 11.9, reach=4.0, name="west"))
        out.append(Light.rect((29.1, 33.0, 0), (1, 0, 0), (0, 1, 0), -2.3, 2.3, 6.1, 11.9, reach=4.0, name="north"))
        return out

    def emphasis(self, c, n):
        u, d = (c.x + c.y) / R2, (c.x - c.y) / R2
        if abs(u - GATE_U) < 14 and d > 30:
            return 1.5                          # the gate front and its crown
        if c.z > 14 and (c.x > 40 or c.y < -40):
            return 1.4                          # the prow crowns
        return 1.0
