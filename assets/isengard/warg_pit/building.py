"""The Isengard warg pit (IsengardWargPit), pass 2 "the kennels": EA's pit kept whole - the
palisade ring round the yard, the bones in it, the kennel hut and its walled run to the door -
and bound in Isengard iron. Lozenge blade pylons with silver collars stand at the ring's three
outer corners; a gatehouse stands over the run inside the door (two blade gate towers on the
run's walls, a pointed lintel between them with the White Hand on a shield); iron bands girdle
the palisade; a rail of meat hooks at the back of the yard; braziers in the yard's corners. EA's house-colour
banner stays the pit's only one. Real fire in the braziers.

Pass 3 (the citadel's recipe, 2026-09-29): the kennels flanked: the three thin corner pylons became the citadel's pair,
two matching blades either side of the pit in the RTS view (one on the palisade's front, one
outside its back, to z 55.5, the White Hand in pointed-arch slots), and a needle chimney behind
the pit on the view's axis.

EA's facts (IPWARGPIT on an identity bone): x -46.8..39.6, y -50.3..49.4, z -2.0..46.5 (3224
triangles). The palisade ring (stakes to z 20..29) round the yard (x -45..37, y -8..48), its
corners at (0, 48), (37, 21), (-46, 21); the kennel hut (x -20..2, y -50..-28, roof z 36..46)
and the walled run from it along y -37 to the door (IBWARGPIT_DRC, its own Draw module and model,
EA's: x 31..36, y -46..-28). Kept clear: the run (wargs are made at (0, -37) and leave for
(70, -37): x -5..40, y -46..-29 below z 30); the yard's middle, where the wargs roam; the level-up
watchtower on the hut (V2: x -29..9, y -52..-22, to z 78); the night torch posts (N_WINDOW) at
(-54, 6), (21, -59), (36, 35). Height limit +20 %: z 56.
"""
from sagekit.building import Building

from ..style import IsengardStyle

FIRE_POINTS = [
    (-23.7, 35.4, 46.2, 'chimney'), (-36.0, 17.0, 4.7, 'brazier'), (27.0, 17.0, 4.7, 'brazier')
]

RING = [(-41.0, -5.0), (-46.0, 21.5), (0.0, 47.5), (37.0, 21.5), (33.5, -5.0)]    # the palisade's corners
PAIR = [(-19.8, -5.8), (17.2, 41.5)]           # blades either side of the pit in the RTS view (its centre -+ 30 along it):
                                               # one on the palisade's front, one outside its back
PAIR_SIZE = (4.6, 2.9, 0.0, 55.5)
PAIR_HAND = (30.0, 2.8, 12.0)
STACK = ((-23.7, 35.4), 52.0, 3.6, 2.9, 0.0, 50.0)  # a needle chimney on the palisade behind the pit, on the view's axis
# the gatehouse over the run, inside the door (the leaf shut: x 31..36, y -46..-28; swung open:
# x 33..37, y -30..-13): two blade towers on the run's walls and a pointed lintel between them
GATE_X = 21.0
GATE = [(-47.3, 2.1), (-26.6, 2.6)]           # the towers' y and half-width across the run's walls
LINTEL = (-45.6, -29.4, 33.0, 43.0)          # y0, y1, underside z, apex z
BANDS = (9.0, 17.0)                   # the bands' heights on the palisade
HOOKS = ((-14.0, 36.0, 13.0), (10.0, 38.0, 13.0))
BRAZIERS = [(-36.0, 17.0), (27.0, 17.0)]


class WargPit(Building):
    style = IsengardStyle()
    source = "IBWARGPIT"
    target = "IPWARGPIT"
    sheet = "IBWargPit.tga"
    sheet_normal = "IBWargPit_NRM.tga"
    own_textures = {"IBWargPit.tga": "IBWargPiH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_Draw",)
    fire_points = FIRE_POINTS
    views = {
        "rts": ((-3.6, -0.5, 22.2), 309, 50, -38, 50),
        "close": ((0.0, 0.0, 20.0), 200, 26, -30, 45),
        "ingame": ((-3.6, -0.5, 22.2), 702, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_industry import logged
        return logged(kit, self._pieces)

    def _pieces(self, kit):
        from mathutils import Vector as V

        from .. import shapes_industry as I
        from .. import shapes_industry_big as B
        L, W, z0, z1 = PAIR_SIZE                     # the pair (the citadel's) either side of the pit
        out = B.blades_at(kit, PAIR, L, W, z0, z1, lean=1.4, hand=PAIR_HAND, fins=2, slits=(0.35, 0.5, 0.65))
        c, axis, L, W, z0, z1 = STACK                # the kennels' chimney on the axis, behind the pit
        out += kit.needle_stack(c, axis, L, W, z0, z1, collar=0.55)
        out += self._gatehouse(kit, V, I)
        out += self._bands(kit, V)
        p, q = HOOKS
        out += I.hook_rail(kit, V(p), V(q), 4, drop=2.0)
        for x, y in BRAZIERS:
            out += kit.brazier(V((x, y, 0.0)), 1.6, 4.6)
        return out

    @staticmethod
    def _gatehouse(kit, V, I):
        """Two blade gate towers on the run's walls (broad faces to the camera, flared feet, fins,
        ember slits, needles to z 56) and a pointed stone lintel between them over the run, the
        White Hand on a shield on its +X face, spikes along its top."""
        from sagekit.blender.geometry import prism_uz
        from ..shapes_spire import BROAD
        out = []
        for y, w in GATE:
            out += kit.blade_tower((GATE_X, y), 0.0, 7.5, w, 0.0, 56.0, flare=1.0, fins=1, spurs=False,
                                   slits=(0.4, 0.58), profile=BROAD, slit_w=1.0)
        y0, y1, zb, za = LINTEL
        ym = (y0 + y1) / 2
        a, t, n = V((GATE_X, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        out.append(prism_uz(a, t, n, [(y0, zb), (y1, zb), (y1, zb + 4.0), (ym, za), (y0, zb + 4.0)], -1.6, 1.6,
                            ["stoneA", "trim", "trim", "trim", "trim"], "stoneA", "stoneA"))
        out += kit.spike_row(a, t, n, y0 + 1.0, y1 - 1.0, zb + 4.3, 3.0, 5, d=0.0, lean=0.0, r=0.4)
        out += kit.shield(a, t, n, ym, zb - 9.5, 8.5, d=1.6)
        for e in (-1, 1):                              # chains from the lintel to the shield's shoulders
            out += kit.chain(V((GATE_X + 1.8, ym + e * 2.8, zb)), V((GATE_X + 2.1, ym + e * 2.4, zb - 2.0)), link=1.0)
        return out

    @staticmethod
    def _pylon(kit, V, x, y, h, reach=3.6, sc=1.0):
        """A lozenge blade pylon: a flared stone foot, an iron shaft with a silver collar, knife
        fins on its four arrises, a needle top."""
        from sagekit.blender.geometry import loft

        from .. import shapes_industry as I
        c = V((x, y, 0))
        lz = lambda s, z: [c + V((s * sc * 1.9, 0, z)), c + V((0, s * sc * 1.3, z)), c + V((-s * sc * 1.9, 0, z)),  # noqa: E731
                           c + V((0, -s * sc * 1.3, z))]
        f = 1.7 if reach > 3 else 1.35
        out = [loft([lz(f, -0.3), lz(f * 0.9, 3.0), lz(1.0, 4.0), lz(0.8, h * 0.72), lz(0.5, h * 0.8), [c + V((0, 0, h))] * 4],
                    ["stoneA", "trim", "iron", "iron", "iron"], cap0=("stoneA", False), cap1=("iron", False))]
        out.append(loft([lz(0.75, h * 0.55 - 0.6), lz(1.2, h * 0.55 - 0.3), lz(1.2, h * 0.55 + 0.3), lz(0.75, h * 0.55 + 0.6)],
                        ["trim"] * 3, cap0=("trim", False), cap1=("trim", False)))
        for k in range(4):
            v = lz(1.0, 0)[k]
            d = (v - c).normalized()
            out += I.fin(kit, c, d, 1.2, [(0.6 * sc, 3.0), (reach, 3.0), (1.3 * sc, h * 0.5), (0.6 * sc, h * 0.45)], 0.45 * sc,
                         tag="iron")
        return out

    @staticmethod
    def _bands(kit, V):
        """Iron bands girdling the palisade outside its stakes, riveted at the corners."""
        out = []
        ctr = V((-3.0, 18.0, 0))
        clamp = lambda p: V((min(max(p.x, -46.2), 39.0), min(max(p.y, -49.8), 48.8), 0))       # noqa: E731
        pts = [V((x, y, 0)) for x, y in RING]
        for a, b in zip(pts, pts[1:]):
            for z in BANDS:
                oa, ob = (clamp(p + (V((p.x, p.y, 0)) - ctr).normalized() * 1.6) for p in (a, b))
                out.append(kit.beam(oa + V((0, 0, z)), ob + V((0, 0, z)), 0.4, "iron"))
        return out
