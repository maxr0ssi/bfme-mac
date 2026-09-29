"""The Isengard furnace (IsengardFurnace), pass 2 "the smelter": EA's forge-mountain kept whole -
the rock mound with its two horns round the glowing crater, the chute that carries the melt down
to the mould, the ingots, the slab floor - and clasped by Isengard. A great blade-spire stack rises
out of the crater between the horns to z 128 (the new silhouette: lozenge shaft, knife fins up its
edges, ember slits, a crown of blades round its glowing mouth); knife-edge blades of black stone
lean on the mound's +Y flank and one under the level-up's deck on its front; a crown of iron
blades rings the crater; an iron hood with an ember throat over the tap; an iron gantry holds a
square crucible over the mould; a forge on the +Y yard, a rack of tongs and blades, ingots, a slag
heap and cart, braziers, a banner on an iron frame. Real fire in the spire, the tap, the mould,
the crucibles, the forge and the braziers (EA's furnace has none).

Pass 3 (the citadel's recipe, 2026-09-29): the smelter crowned: two matching blades out of the mound's top either side of the
crater in the RTS view (the citadel's pair; the left one's foot at z 86, above the level-up hut),
to z 128.5, the White Hand in a pointed-arch slot on each one's outer face, chains from them to
the great chimney, now a slimmer needle stack out of the crater (z 44 to 116, its crown of
blades); the crater's crown down to three blades.

EA's facts (world axes, `world_space`: FURNACE hangs on a bone moved (3.5, -0.2, 0.3)):
x -31.9..68.1, y -46.7..29.8, z -6.4..106.8 (1141 triangles). The mound centred about (2, -2),
its crater at (2.5, -4) sunk to z 46 between the horns (z 90..107); the chute on legs from the
mound at (12, 8, 45) down to the mould (MOLD, x 35..68, z 4..19); the melt LIQUIDMETAL1 and the
pool POOLOMETAL stay EA's. The level-up hut V2 (415) takes the -Y half above z 34 (x -32..22,
y -48..12) and a ladder up the mound's -X side (x -25..-11, y -8..4): nothing new there. EA's
night torch posts (N_WINDOW) at (-4, -57) and (33, 28). The porters work the yard in front.
"""
from sagekit.building import Building

from ..style import IsengardStyle

# the fire the design lights (x, y, z, kind), world axes; from the geometry log's FIRE_POINTS
FIRE_POINTS = [
    (2.5, -4.0, 110.4, 'chimney'), (15.0, 8.0, 42.0, 'furnace'), (50.0, 24.0, 7.2, 'hearth'),
    (57.0, 20.5, 6.5, 'crucible'), (64.0, 24.0, 8.6, 'brazier'), (64.0, -43.0, 8.6, 'brazier'),
    (20.0, -42.0, 8.6, 'brazier'), (57.0, 5.0, 15.0, 'crucible'), (52.0, 7.4, 22.3, 'crucible')
]

CRATER = (2.5, -4.0)
SPIRE = ((2.5, -4.0), 52.0, 5.0, 3.4, 44.0, 116.0)           # the great chimney out of the crater
# the pair (the citadel's): two blades out of the mound's top either side of the crater along the
# view, mirrored about it, the left one's foot above the level-up hut (V2, to z 84.6)
PAIR = ((-2.2, -0.3), 10.5, 6.4, 3.6, (86.0, 76.0), 128.5)
HAND = (95.0, 3.8, 14.0)
# buttresses on the mound's +Y flank (the right-hand silhouette in the RTS view): angle about the
# crater, back (in the rock), foot and point radii, the point's height
BUTTRESSES = [(45.0, 13.0, 33.0, 20.0, 74.0), (75.0, 13.0, 29.5, 20.0, 80.0), (105.0, 12.0, 28.5, 18.0, 74.0),
              (135.0, 11.0, 30.0, 16.0, 66.0), (-15.0, 19.0, 36.0, 26.0, 32.0)]   # the last under V2's deck (z 34)
CROWN = [(330.0, 11.0, 80.0), (0.0, 12.4, 80.0), (150.0, 11.5, 88.0)]      # the crater's rim: angle, radius, z
FORGE = ((50.0, 24.0, 3.0), (-1.0, 0.0))                     # hearth foot, t (the forge faces -Y)
BANNER = ((30.0, -40.0, 3.0), (-0.62, -0.79))                 # the cloth faces the RTS camera
BRAZIERS = [(64.0, 24.0), (64.0, -43.0), (20.0, -42.0)]


class Furnace(Building):
    style = IsengardStyle()
    source = "MBFurnace_SKN"
    target = "FURNACE"
    sheet = "MBFurnace.tga"
    sheet_normal = "MBFurnace_NRM.tga"
    own_textures = {"MBFurnace.tga": "MBFurnacH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    world_space = True                   # FURNACE's bone is moved (3.5, -0.2, 0.3): design and fire share world axes
    fire_points = FIRE_POINTS
    views = {
        "rts": ((18.1, -8.4, 50.2), 372, 50, -38, 50),
        "close": ((14.0, -2.0, 58.0), 300, 24, -30, 45),
        "ingame": ((18.1, -8.4, 50.2), 846, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_industry import logged
        return logged(kit, self._pieces)

    def _pieces(self, kit):
        from mathutils import Vector as V

        from .. import shapes_industry as I
        from .. import shapes_industry_big as B
        out = []
        c, axis, L, W, z0, z1 = SPIRE
        out += B.spire_stack(kit, c, axis, L, W, z0, z1, collar=0.62, crown=9.0)
        m, half, L, W, z0, z1 = PAIR
        solids, tops = B.blade_pair(kit, m, half, L, W, z0, z1, lean=1.2, hand=HAND, fins=1, fin_reach=1.1,
                                     slits=(0.3, 0.45, 0.6))
        out += solids
        for x, y in tops:                                    # chains from each blade to the great chimney's throat
            out += kit.chain(V((x + (m[0] - x) * 0.25, y + (m[1] - y) * 0.25, 112.0)), V((2.5, -4.0, 106.0)), link=1.8,
                             w=0.5)
        out += self._buttresses(kit, V, I)
        out += self._crown(kit, V)
        out += self._tap(kit, V)
        (fx, fy, fz), t = FORGE
        out += I.forge_bay(kit, V((fx, fy, fz)), t, 1.6)
        (bx, by, bz), t = BANNER
        out += I.banner_frame(kit, V((bx, by, bz)), t, 9.0, 20.0)
        for x, y in BRAZIERS:
            out += kit.brazier(V((x, y, 3.0)), 2.0, 5.5)
        out += kit.slag_heap(V((46.0, -38.0, 2.5)), 5.5, 4.5, seed=2)
        out += kit.slag_cart(V((38.0, -30.0, 3.0)), V((0.62, 0.79, 0)), 1.8)
        kit.fire(V((57.0, 5.0, 15.0)), "crucible")               # the mould's pool
        out += self._gantry(kit, V, B)
        out += I.blade_rack(kit, V((58.0, -30.0, 3.0)), (0.0, 1.0), 8.0, 4, 6.0)          # the mould's tongs and blades
        for x, y in ((40.0, -12.0), (45.0, -17.0)):
            out += kit.ingots(V((x, y, 3.0)), V((0.62, 0.79, 0)), 3, 1.5)
        return out

    @staticmethod
    def _gantry(kit, V, B):
        """Iron A-frames over the mould (pointed silver caps), a riveted beam, a trolley and a
        square crucible on its chain. Fire: crucible."""
        c, t, n = V((52.0, 4.0, 3.0)), V((0, 1, 0)), V((1, 0, 0))
        span, h = 23.0, 27.0
        out = []
        for e in (-1, 1):
            top = c + t * (e * span / 2) + V((0, 0, h))
            for s in (-1, 1):
                out.append(kit.beam(c + t * (e * span / 2) + n * (s * h * 0.3) - V((0, 0, 0.4)), top, 0.5, "iron"))
            out.append(kit.beam(top + V((0, 0, 0.8)), top + V((0, 0, 4.0)), 0.7, "trim", 0.0))
        a, b = c - t * (span / 2 + 0.8) + V((0, 0, h + 0.5)), c + t * (span / 2 + 0.8) + V((0, 0, h + 0.5))
        out.append(kit.beam(a, b, 0.7, "iron"))
        out.append(kit.beam(a + V((0, 0, 0.7)), b + V((0, 0, 0.7)), 0.3, "trim"))
        m = c + t * (span * 0.15) + V((0, 0, h - 0.4))
        out.append(kit.beam(m - t * 1.0, m + t * 1.0, 0.55, "iron"))
        out += kit.chain(m - V((0, 0, 0.6)), m - V((0, 0, 7.0)), link=1.6)
        out += B.square_crucible(kit, m - V((0, 0, 10.5)), 2.0, 3.2)
        return out

    @staticmethod
    def _buttresses(kit, V, I):
        """Layered knife-edge buttresses of black stone clasping the mound's +Y flank, their backs
        in the rock, ember slits in their faces."""
        import math
        out = []
        for ang, rb, rf, rt, zt in BUTTRESSES:
            d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
            out += I.layered_fin(kit, V((CRATER[0], CRATER[1], 0)), d, rb, rf, rt, zt, w=2.6)
        return out

    @staticmethod
    def _crown(kit, V):
        """Iron blades round the crater's rim, leaning out: the smelter's crown against the sky."""
        import math
        out = []
        for i, (ang, r, z) in enumerate(CROWN):
            d = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
            h = 16.0 if i % 2 == 0 else 11.0
            out += kit.blade(V((CRATER[0], CRATER[1], 0)) + d * (r - 1.0), d, z - 6.0, z + h * 0.6, 1.5, 4.5, w=1.1,
                             tip=h * 0.4, back=2.5, tag="iron", edge="trim")
        return out

    @staticmethod
    def _tap(kit, V):
        """An iron hood over the tap where the chute leaves the mound: a steep gable, an ember
        throat, spikes on its ridge. Fire: furnace."""
        a, t, n = V((13.5, 8.0, 0)), V((0, 1, 0)), V((1, 0, 0))
        out = kit.gable(a, t, n, -5.5, 5.5, 44.0, 12.0, th=5.0)
        out += kit.spike_row(a, t, n, -5.0, 5.0, 44.2, 3.5, 4, d=0.6, lean=0.4, r=0.4)
        kit.fire(V((15.0, 8.0, 42.0)), "furnace")
        return out
