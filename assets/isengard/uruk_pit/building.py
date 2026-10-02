"""The Isengard uruk pit (IsengardUrukPit), pass 2 "the breeding pits": EA's mound kept whole - the
two lobes of rock, the pit's octagonal mouth on the main lobe, the timber ramp, the ladders and
decks, the cave mouth in the +X lobe - and made the place where the Uruk-hai are pulled from the
mud. An iron birthing-frame crowns the pit: six knife ribs rise from a riveted band on its rim to
a needle at z 70, bound by a ring hung with meat hooks, a great hook on a chain down into the pit;
two needle stacks rise from the main lobe either side of it; furnace mouths glow in the lobe's -Y
face; a fan of layered stone fins clasps the +X lobe over the cave mouth; a birthing pit, Uruk
harness on stands and a blade rack on the +Y yard; braziers and a banner on an iron frame at the
-X foot. Real fire in the pit, the stacks, the furnace mouths, the birthing pit and the braziers.

Pass 3 (the citadel's recipe, 2026-09-29): the breeding pits flanked: two matching blades either side of the pit in the
RTS view (to z 77.5, the White Hand in pointed-arch slots), and the birthing-frame made pointed:
four knife ribs on a square turned to the view, bound by four iron bars (pass 2's six ribs and
ring read round); the chimneys behind.

Pass 4 (2026-09-30, "the furnace towers look a lil stupid", Max): the pair and both needle stacks
went. The birthing mud instead, on the free ground at the -X-Y front: a pool of wet black mud in a
soot kerb under an iron gantry (a winch, a chain to a great hook in the mud), braziers either side
(the stacks' fire); a corner brazier moved to (-42, -17).

EA's facts (IBURUKPIT_NEW on an identity bone): x -48.9..72.8, y -41.5..53.1, z -0.5..64.9 (1087
triangles). The pit's mouth at (-2, 3), r ~10, its rim at z 42..46 (the Uruk-hai and the hook
HOOK animate in it, z 0..17); the ramp from (-5, 30) to (35, 0) at z 40..54; the cave mouth in
the +X lobe's -Y side. Kept clear: the units' way out (created at (46, -10), rallying to
(41, -70)); the level-up (V2: the tower and banner at (-32..13, 27..47) to z 92, and two banner
poles flanking the cave mouth at (26..44, -37..-29) and (53..70, -43..-35)); EA's night torch
posts (N_WINDOW) at (-37, -16), (45, 26), (80, -28). Height limit +20 %: z 78.
"""
from sagekit.building import Building

from ..style import IsengardStyle

FIRE_POINTS = [
    (-2.0, 3.0, 40.0, 'grate'), (-40.5, -28.5, 4.5, 'brazier'), (-20.5, -36.5, 4.5, 'brazier'),
    (-18.9, -10.8, 1.5, 'furnace'), (-4.0, -22.3, 1.5, 'furnace'), (28.0, 27.0, 1.0, 'embers'),
    (-42.0, -17.0, 5.1, 'brazier'), (17.0, -38.0, 5.1, 'brazier')
]

PIT = (-2.0, 3.0, 44.0)                          # the mouth's centre and rim height
# pass 4 (2026-09-30): the pair and the two needle stacks went; the birthing mud and its gantry on
# the free ground at the -X-Y front instead, braziers either side
MUD = ((-31.5, -30.5), 6.3)
MUD_GANTRY = ((0.62, 0.79), 15.0, 19.0)        # t (the view's horizontal: broadside to the camera), span, height
MUD_BRAZIERS = [(-40.5, -28.5), (-20.5, -36.5)]
MOUTHS = [((-19.0, -10.5, 0.0), (1.0, 0.25)), ((-4.0, -22.0, 0.0), (1.0, -0.1))]   # furnace mouths: foot, t
BIRTH = ((28.0, 27.0, 0.0), 5.0)
LOBE = (48.0, -15.0)                             # the +X lobe's centre: a fan of fins on its +X flank
FINS = [(330.0, 9.0, 24.0, 12.0, 44.0), (0.0, 10.0, 21.0, 12.0, 50.0), (30.0, 9.0, 24.0, 12.0, 44.0)]
BANNER = ((-40.0, -6.0, 0.0), (-0.62, -0.79))
BRAZIERS = [(-42.0, -17.0), (17.0, -38.0)]


class UrukPit(Building):
    style = IsengardStyle()
    source = "IBUrukPit_SKN"
    target = "IBURUKPIT_NEW"
    sheet = "iburukpit.tga"
    facet_islands = 8                       # the unwrap overlapped a little: seams at EA's islands and 8-degree turns
    sheet_normal = "iburukpit_nrm.tga"
    own_textures = {"iburukpit.tga": "iburukpiH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    # EA remodelled the really damaged pit (cut: 8.5% open backs, slivers); one post foot of ours rides
    # EA's dent 0.6 below the healthy floor, under the ground
    lifecycle = {"IBUrukPit_D2": {"fill": True, "deep": (0.7, "one post foot at (-3, -19) rides EA's dent to "
                                                              "z -1.1, under the ground; EA's lowest -0.5")}}
    fire_points = FIRE_POINTS
    views = {
        "rts": ((12.0, 5.8, 32.2), 368, 50, -38, 50),
        "close": ((8.0, 2.0, 34.0), 230, 26, -30, 45),
        "ingame": ((12.0, 5.8, 32.2), 837, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_industry import logged
        return logged(kit, self._pieces)

    def _pieces(self, kit):
        from mathutils import Vector as V

        from .. import shapes_industry as I
        from .. import shapes_industry_big as B
        px, py, pz = PIT
        out = kit.hoop((px, py), pz - 0.6, 10.5, h=1.8, th=0.7, inner=1.4, k=12, rivets=3, tag="iron", closed=True)
        out += B.birth_spire(kit, V((px, py, 0)), 10.5, pz, 70.0, 12.5, 56.0, w=2.0)
        kit.fire(V((px, py, pz - 4.0)), "grate")
        from .. import shapes_trades as T
        (mx, my), r = MUD                              # the birthing mud at the front, its gantry over it
        out += T.mud_pool(kit, V((mx, my, 0.0)), r, seed=0.9)
        t, span, h = MUD_GANTRY
        out += T.pit_gantry(kit, V((mx, my, 0.0)), t, span, h, drop=h * 0.62, hook=3.4)
        for x, y in MUD_BRAZIERS:
            out += kit.brazier(V((x, y, 0.0)), 1.5, 4.4)
        for c, t in MOUTHS:
            n = V((t[1], -t[0], 0))                   # facing -Y, out of the lobe
            out += kit.fire_grate(V(c), V((t[0], t[1], 0)), n, w=5.0, h=4.2, d=4.0)
        import math
        for ang, rb, rf, rt, zt in FINS:
            d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
            out += I.layered_fin(kit, V((LOBE[0], LOBE[1], 0)), d, rb, rf, rt, zt, w=2.2)
        (bx, by, bz), r = BIRTH
        out += I.birth_pit(kit, V((bx, by, bz)), r)
        for c in ((36.0, 36.0, 0.0), (40.0, 30.0, 0.0)):              # fresh Uruk harness by the birthing pit
            out += I.armour_stand(kit, V(c), (-0.62, -0.79), 2.0)
        out += I.blade_rack(kit, V((20.0, 40.0, 0.0)), (1.0, 0.0), 8.0, 4, 6.0)
        c, t = BANNER
        out += I.banner_frame(kit, V(c), t, 8.0, 17.0)
        for x, y in BRAZIERS:
            out += kit.brazier(V((x, y, 0.0)), 1.7, 5.0)
        return out
