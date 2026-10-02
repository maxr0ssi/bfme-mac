"""Mordor tavern (MordorTavern; EA's mbtavern, map-placed), pass 2 "the black hearth": EA's timber
hall kept whole - the long steep roof, the front wing and its door, the shutters and awnings, the
crow's nest - and made the citadel's: a great jagged chimney stack of black basalt rises from the
ground against the hall's front wall past the eaves, its mouth opening into a claw of hooked spikes
round real orange fire and chimney smoke; steel spikes crest the ridge; a gibbet cage hangs off the
front gable over the door; fire baskets flank the door; lava runs along the front; bones heaped.

    stack       claw_stack at (-24, -35) against the front wall: r 7.2 at its foot, leaning 3 toward
                the roof, iron bands, ember slits and a lava seam, its mouth at z 74, seven spikes
                to z 84; "chimney" fire and a "plume" (pass 1's stack on the ridge is gone)
    ridge       steel spikes up out of the ridge in two runs (x -42..-30 and -12..16), clear of the
                crow's nest (V1, x 25..45)
    gibbet      an iron arm off the front wing's gable apex (25.5, -37.5, z 48), a chain and a cage
    door        fire baskets either side of the door (x 18..34, y -38)
    lava        an open lava channel along the hall's front foot east of the stack; a bone heap

EA's MBTavern_SKN (object MordorTavern): body MAINHOUSE, 528 triangles, painted from MBTavern.tga +
MBTavern_NRM.tga (DXT1); Isengard draws mbtavern too: our own texture pinned as MBTaverH.tga. In
MAINHOUSE mesh coordinates (identity bone): x -51.27..50.69, y -44.68..36.86, z -0.24..72.15. Other
meshes (EA's, untouched): MUCORSAIR 1406 (the corsair); ALPHAOBJECTS 720 (MBTavernWD.tga: shutters,
awnings, flags); V1 272 (the crow's nest on its pole over the ridge's +X end, x 25..45, |y| < 10,
z 61..118); FXGLOWCARDS 44 (window glows), FXFIRE02 32 (EA's torch flame cards). Lifecycle models
in its Draw module: MBTavern_ASKN, MBTavern_D1, MBTavern_D2, MBTavern_D3. House colour: MBHCTavern.

EA's facts (measured 2026-09-30, work/measure.json and the preview stage): the hall's ridge along x
at y 0 from z 65.1 (x 0) up to its flared gables at z 69.5..70.6 (x -50, 50), the roof falling to z
39 at y +-30; the front wing's ridge along y at x 25.5, z 51..53 (y -20..-40), its door frame at
y -38 (x 18..34, to z 25); a small chimney box on the back slope at (-2.5, 33). Kept clear: the door
and the way out in front of it, the crow's nest, EA's torch cards. Height limit +20 %: z 86.6.
"""
from sagekit.building import Building

from ..style import MordorStyle

STACK = ((-24.0, -35.0), 7.2, 74.0, 11.5)       # (x, y), foot r, mouth z, claw H: grounded against the front wall
RIDGE_SPIKES = [(-42.0, 68.6), (-38.0, 68.0), (-34.0, 67.5), (-30.0, 67.1), (-12.0, 65.5), (-8.0, 65.4), (-4.0, 65.3),
                (0.0, 65.1), (4.0, 65.4), (8.0, 65.9), (12.0, 66.4), (16.0, 66.8)]
GIBBET = ((25.5, -37.5), 48.0)
BASKETS = [(13.0, -41.0), (39.0, -41.0)]
CHANNEL = [(-15.0, -37.0), (-4.0, -38.0), (7.0, -37.0)]
BONES = (-46.0, -39.0)

# real fire and smoke (the game's particle systems on bones of the rig), from the design's log
FIRE_POINTS = [
    (-24.0, -32.0, 74.2, 'chimney'), (-24.0, -32.0, 82.1, 'plume'), (13.0, -41.0, 5.8, 'brazier'), (39.0, -41.0, 5.8, 'brazier'),
    (-4.0, -38.0, 0.4, 'embers'), (5.0, -37.2, 1.0, 'smoke')
]


class Tavern(Building):
    style = MordorStyle()
    source = "MBTavern_SKN"
    target = "MAINHOUSE"
    sheet = "MBTavern.tga"
    sheet_normal = "MBTavern_NRM.tga"
    own_textures = {"MBTavern.tga": "MBTaverH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    # EA's build-up is a remodel: cut, our shell kept scraps and 6% open backs (sagekit/lifecycle.py `fill`)
    lifecycle = {"MBTavern_ASKN": {"fill": True}}
    bake_hidden = ("MUCORSAIR", "FXGLOWCARDS", "FXFIRE02", "V1")
    fire_points = FIRE_POINTS
    views = {
        "rts": ((-0.3, -3.9, 36.0), 328, 50, -38, 50),
        "close": ((-0.3, -3.9, 36.0), 194, 24, -30, 45),
        "ingame": ((-0.3, -3.9, 36.0), 746, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        from assets.men.stable.pieces import drop_loose
        drop_loose(self.target)                 # EA's two loose vertices (the checks allow none on the target)
        return logged(kit, lambda k: k.retag(self._pieces(k)))

    @staticmethod
    def _pieces(kit):
        from mathutils import Vector as V

        from .. import shapes_production as P
        from .. import shapes_production_big as PB
        (sx, sy), r, z1, H = STACK                  # the chimney stack from the ground up the front wall, clawed
        out = PB.claw_stack(kit, (sx, sy), r, z1, H, z0=0.3, n=7, s=1.8, kind="chimney", smoke="plume", seed=0.3,
                            lean=(0.0, 3.0))
        for i, (x, z) in enumerate(RIDGE_SPIKES):                                      # the ridge's steel crest
            L = 5.5 if i % 2 else 7.0
            out.append(kit.tube([V((x, 0, z - 1.5)), V((x, 0, z + L * 0.6)), V((x + 0.4, 0, z + L))],
                                [0.55, 0.32, 0.0], "steel", k=4, cap0="steel", cap1=None, phase=0.785))
        (gx, gy), gz = GIBBET
        out += kit.gibbet(V((gx, gy, 0)), (0, -1), gz, reach=3.5, drop=3.0, h=6.5, w=1.9)
        for x, y in BASKETS:
            out += kit.fire_basket(V((x, y, 0.25)), 1.8, 5.2)
        out += kit.lava_channel([(x, y, 0.0) for x, y in CHANNEL], w=1.6, kerb=0.6, h=0.9, seed=0.6, sides=(-1,),
                                pitch=5.0)
        kit.fire(V((-4.0, -38.0, 0.4)), "embers")
        kit.fire(V((5.0, -37.2, 1.0)), "smoke")
        out += P.bone_heap(kit, (BONES[0], BONES[1], 0.3), 3.2, seed=0.9)
        return out
