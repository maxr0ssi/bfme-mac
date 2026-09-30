"""Mordor siege works (MordorSiegeWorks), pass 2 "the war-forge": EA's stockade kept whole - the
braced timber walls, the spiked rails along their tops, the great corner and gate posts - and made
the citadel's: a great jagged forge stack of black basalt rises from the yard's back corner over the
walls, its mouth opening into a claw of hooked spikes round real orange fire and a dark plume;
furnace mouths at its foot feed a lava runnel; a half-built siege tower stands at the mouth on its
scaffold; an orc crane swings a boulder over a catapult; fire baskets and stakes outside.

    forge       claw_stack at (-44, 24): r 9 at its foot (eight-sided), iron bands, ember slits and
                a lava seam, its mouth at z 46, seven spikes to z 61: "furnace" fire and a "plume";
                three barred furnace mouths at its foot toward the yard ("forge")
    tower       a half-built siege tower at (8, 14) facing the mouth: raking timber posts to z 56,
                iron plates up the front and sides, a raised drawbridge with barbed teeth, the top
                storey bare frame, a scaffold by it (off the forge's line of sight from the camera)
    runnel      open lava from the forge's mouths across the yard, embers and a thin smoke
    crane       a braced timber crane at (-14, 29) swinging a boulder over the catapult (-28, 2)
    mouth       fire baskets and impaling stakes either side of the open +X side

EA's MBSeigeWork (object MordorSiegeWorks; role siege): body SEIGEWORK2, 667 triangles, painted from
MBSeigeWork2.tga + MBSeigeWork2_NRM.tga (DXT5, cut-out alpha: our texture is DXT5). In SEIGEWORK2
mesh coordinates (its bone moved (0, 0, 0.14)): x -78.99..35.08, y -56.26..58.57, z -2.95..54.57.
Other meshes (EA's, untouched): V2 1512 (the level 3 banners on poles at (-19.3, 44.2),
(23.3, -39.6), (-65, -16.8), z 49.6..96); SEIGEWORK1 520 (MBSeigeWork1.tga: the spiked rails and
braces); N_WINDOW 120, N_FIRE 24 (EA's flame card). Lifecycle models in its Draw module:
MBSeigeW_D1, MBSeigeW_D2, MBSeigeW_D3, MBSeigeWork_A. House colour: MBHCSeigeWork.

EA's facts (measured 2026-09-30, work/measure.json and the preview stage): a square stockade x
-64..24, y -42..42, its walls to z 40..47 with spiked rails, braced on the -X side (braces at y
+-9 to z 45); corner and middle posts to z 47..54.7 at (-64, +-42), (-19, +-42), (24, +-40); the +X
side open for |y| < 24 (the engines' way out; units are made at (120, 0)); the yard's floor at z
-2 under the terrain. Kept clear: the mouth (|y| < 22 from x -5 out), the banners (V2), the rails.
Height limit +20 %: z 66.
"""
from sagekit.building import Building

from ..style import MordorStyle

FORGE = ((-44.0, 24.0), 9.0, 46.0, 15.0)                     # (x, y), foot r, mouth z, claw H
MOUTHS = [-60.0, -20.0, 20.0]                                   # the furnace mouths: degrees off +X round the base
RUNNEL = [(-35.0, 19.5), (-27.0, 13.0), (-17.0, 12.0), (-8.0, 6.0)]
CRANE = ((-14.0, 29.0), (-0.5, -0.87), 42.0, 16.0, 16.0)         # foot, jib direction, mast h, reach, drop
CATAPULT = ((-28.0, 2.0), (1.0, 0.0))
TOWER = ((8.0, 14.0), (1.0, 0.0), 7.0, 56.0, 0.62)       # foot, facing, half width, height, plated to
SCAFFOLD = ((2.0, -0.5), 12.0, 6.0, 34.0)
BASKETS = [(31.0, -21.0), (31.0, 21.0)]
STAKES = [((28.0, -30.0), (0.25, -0.3, 1.0)), ((28.0, 30.0), (0.25, 0.3, 1.0)), ((29.0, -12.0), (0.3, -0.1, 1.0)),
          ((29.0, 12.0), (0.3, 0.1, 1.0))]

# real fire and smoke (the game's particle systems on bones of the rig), from the design's log
FIRE_POINTS = [
    (-44.0, 24.0, 46.2, 'furnace'), (-44.0, 24.0, 56.5, 'plume'), (-39.4, 15.9, 3.5, 'forge'), (-35.3, 20.8, 3.5, 'forge'),
    (-35.3, 27.2, 3.5, 'forge'), (-17.0, 12.0, 0.4, 'embers'), (-10.0, 7.0, 1.0, 'smoke'), (31.0, -21.0, 5.5, 'brazier'),
    (31.0, 21.0, 5.5, 'brazier')
]


class SiegeWorks(Building):
    style = MordorStyle()
    source = "MBSeigeWork"
    target = "SEIGEWORK2"
    sheet = "MBSeigeWork2.tga"
    sheet_normal = "MBSeigeWork2_NRM.tga"
    own_textures = {"MBSeigeWork2.tga": "MBSeigeWorkH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    bake_hidden = ("V2", "N_WINDOW", "N_FIRE")
    fire_points = FIRE_POINTS
    views = {
        "rts": ((-22.0, 1.2, 25.9), 378, 50, -38, 50),
        "close": ((-22.0, 1.2, 25.9), 223, 24, -30, 45),
        "ingame": ((-22.0, 1.2, 25.9), 859, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        return logged(kit, lambda k: k.retag(self._pieces(k)))

    @staticmethod
    def _pieces(kit):
        import math

        from mathutils import Vector as V

        from .. import shapes_production as P
        from .. import shapes_production_big as PB
        (fx, fy), rb, rim, H = FORGE                    # the forge: a basalt stack from the ground, clawed
        out = PB.claw_stack(kit, (fx, fy), rb, rim, H, n=7, s=2.0, kind="furnace", smoke="plume", seed=0.5, k=8)
        for deg in MOUTHS:                                                        # furnace mouths toward the yard
            a = math.radians(deg)
            n = V((math.cos(a), math.sin(a), 0))
            t = V((-n.y, n.x, 0))
            base = V((fx, fy, 0)) + n * (rb * 0.9)
            out += kit.vent(base, t, n, 0.0, 2.5, 4.2, 5.0, 0.0, bars=3)
            kit.fire(base + n * 1.2 + V((0, 0, 3.5)), "forge")
        out += kit.lava_channel([(x, y, 0.0) for x, y in RUNNEL], w=1.3, kerb=0.7, h=0.9, seed=0.8, pitch=4.0)
        kit.fire(V((-17.0, 12.0, 0.4)), "embers")
        kit.fire(V((-10.0, 7.0, 1.0)), "smoke")
        (cx, cy), d, h, reach, drop = CRANE
        t = V((d[0], d[1], 0)).normalized()
        out += kit.crane(V((cx, cy, 0.3)), t, h=h, reach=reach, drop=drop, cage=False)
        tip = V((cx, cy, 0.3)) + V((0, 0, h)) + t * reach + V((0, 0, reach * 0.35))
        out.append(kit.facet_lump(tip - V((0, 0, drop + 2.2)), 2.6, "rock"))       # the boulder on the chain
        (kx, ky), t = CATAPULT
        out += P.catapult(kit, (kx, ky, 0.0), t, 1.0)
        (tx, ty), t, w, h, built = TOWER               # the half-built siege tower at the mouth
        out += PB.siege_tower(kit, (tx, ty, 0.0), t, w, h, built)
        (sx, sy), w, dd, sh = SCAFFOLD
        out += kit.scaffold(V((sx, sy, 0.3)), V((1, 0, 0)), V((0, 1, 0)), w, dd, sh, levels=3)
        for x, y in BASKETS:
            out += kit.fire_basket(V((x, y, 0.0)), 1.8, 5.2)
        for i, ((x, y), dv) in enumerate(STAKES):
            out += kit.stake(V((x, y, 0.95)), V(dv), 12.0, r=0.6, barbs=1, seed=i + 1.0)
        return out
