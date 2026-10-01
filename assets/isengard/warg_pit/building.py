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

Pass 4 (2026-09-30, "the furnace towers look a lil stupid", Max): the pair and the needle chimney
went, and the gatehouse's blade towers became heavy gate posts (a battered stone foot, an iron
shaft with riveted bands past the lintel, a fire basket on each: the chimney's fire). Gnawed bones
heaped against the palisade and chain stakes with collars in the dirt, the yard's middle clear.

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
    (21.0, -47.3, 45.7, 'brazier'), (21.0, -26.6, 45.7, 'brazier'), (-36.0, 17.0, 4.7, 'brazier'),
    (27.0, 17.0, 4.7, 'brazier')
]

RING = [(-41.0, -5.0), (-46.0, 21.5), (0.0, 47.5), (37.0, 21.5), (33.5, -5.0)]    # the palisade's corners
# pass 4 (2026-09-30): the pair and the needle chimney went; bone heaps and chain stakes round the
# yard's edge instead (its middle stays clear for the wargs), fire baskets on the gate posts
BONES = [((-32.0, 29.0), 7.0, 0.4), ((21.0, 29.0), 6.0, 2.2), ((-6.0, 40.0), 5.5, 3.9)]
TETHERS = [((8.0, 40.0), 3, 0.5), ((-38.0, 8.0), 3, 1.7), ((27.0, 4.0), 2, 2.9)]
# the gatehouse over the run, inside the door (the leaf shut: x 31..36, y -46..-28; swung open:
# x 33..37, y -30..-13): two blade towers on the run's walls and a pointed lintel between them
GATE_X = 21.0
GATE = [(-47.3, 2.1), (-26.6, 2.6)]           # the towers' y and half-width across the run's walls
LINTEL = (-45.6, -29.4, 33.0, 43.0)          # y0, y1, underside z, apex z
POST_TOP = 41.0                                # the gate posts' tops, their fire baskets on them
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
        from .. import shapes_trades as T
        out = self._gatehouse(kit, V, I)
        for (x, y), r, seed in BONES:                # gnawed bones heaped against the palisade
            out += T.bone_heap(kit, V((x, y, 0.0)), r, seed=seed)
        for (x, y), n, seed in TETHERS:              # chain stakes, collars lying in the dirt
            out += T.tether(kit, V((x, y, 0.0)), 6.5, n, seed=seed)
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
        from sagekit.blender.geometry import loft
        out = []
        for y, w in GATE:                              # heavy gate posts: a battered stone foot, a riveted iron
            c = V((GATE_X, y, 0))                      # shaft past the lintel, a fire basket on top
            sq = lambda hx, hy, z: [c + V((-hx, -hy, z)), c + V((hx, -hy, z)), c + V((hx, hy, z)), c + V((-hx, hy, z))]  # noqa: E731
            out.append(loft([sq(4.2, w, -0.3), sq(3.4, w, 8.0), sq(3.6, w, 8.0), sq(3.6, w, 9.2),     # never wider
                             sq(2.8, w - 0.3, 9.2), sq(2.5, w - 0.3, POST_TOP), sq(3.2, w, POST_TOP),   # than the old
                             sq(3.2, w, POST_TOP + 1.0), sq(2.2, w - 0.6, POST_TOP + 1.0)],              # towers across the run
                            ["stoneA", "trim", "iron", "iron", "iron", "trim", "iron", "iron"], cap0=("stoneA", False),
                            cap1=("iron", True)))
            for f in (0.35, 0.62):                     # riveted iron bands, proud along x only (the run is along y)
                z = 9.2 + (POST_TOP - 9.2) * f
                out.append(loft([sq(2.2, w - 0.3, z - 0.7), sq(2.9, w, z - 0.6), sq(2.9, w, z + 0.6), sq(2.2, w - 0.3, z + 0.7)],
                                ["iron"] * 3, cap0=("iron", False), cap1=("iron", False)))
                for e in (-1, 1):
                    out += kit.rivets(c + V((2.9, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), [(e * w * 0.5, z)], 0.0, 0.3)
            out += kit.brazier(V((GATE_X, y, POST_TOP + 1.0)), 1.8, 3.6)
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
