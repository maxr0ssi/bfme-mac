"""The Goblin cave (GoblinCave; WBCave_SKN): EA's rock mound kept whole - the black rock
(WBCAVE_STONE, EA's WBStone mesh), the five crimson claws of horn clutching over the mouth, the
horn spikes and the crooked stalks round it, the rubble at its foot - and made the gate of
Goblin-town, a hole in the mountain that spits out warriors:

    gate       a frame of lashed timber in the mouth under the claws' tips, bone fangs hanging
               from its lintel, a skull on each post's point and a torch on an iron arm
    tusks      two great bleached tusks rising either side of the mouth and arching in over it
    trophy     a horned troll skull nailed to the middle claw over the mouth
    summit     a totem on the rock's summit behind the claws (a horned skull over a bone
               crossbar and a ribcage: the new silhouette) in a ring of black horns with
               bleached tips, and a skull on an iron spike either side
    flanks     sharpened stakes along the front flanks, an impaled skeleton and a hide drying
               frame on the -Y side (the camera's), skull piles by the rubble
    banners    two ragged house-colour banners on tall posts either side of the mouth

EA's facts (WBCAVE and WBCAVE_STONE share the model frame; sagekit measure: work/measure.json):
WBCAVE x -53.22..56.83, y -48.64..42.81, z -5.73..53.52 (505 triangles on wbcave.tga); the
claws run from the summit (x 8..20, z 44) down to their tips over the mouth (the middle one to
x 55, z 27.8; the side ones end by x 48 at z ~31); the mouth is open from x 30 to the front,
|y| < 20, its floor at z 0.1..3; the rock (WBCAVE_STONE, EA's) peaks at z 43 at (12, -14) and
is ~33 behind the claws at (-2, -9). The sword-guard (GOBLIN, skinned) paces the mouth: the
opening under z 23, |y| < 15, stays clear. The level-up meshes stand on the -X side: V1 (the
tower, x -54..-8, y -3..37, z 35..92, its archers' bones at z 53) and V1A (its rock, x
-56..-7, y -7..39): nothing new there. Height limit +20 %: z 65.4.
"""
from sagekit.building import Building

from ..style import GoblinStyle

MOUTH_X = 48.0                              # the gate frame's face (the mouth's lip)
GATE = (-12.0, 12.0, 23.5)                  # post u (= y) and the lintel's height
TUSK = [(52.5, 24.0, 0.0), (53.8, 25.0, 13.0), (52.0, 21.0, 27.0), (48.5, 15.0, 34.0)]
TROPHY = (48.0, 0.0, 38.2, 6.0)             # the horned skull on the middle claw (x, y, z, size)
TOTEM = (-2.0, -9.0, 32.0, 21.5, 5.4)       # foot (x, y, z), height, skull size
SPIKES = [((2.0, -20.0, 34.5), 13.0, 3.0), ((10.0, 16.0, 26.5), 14.0, 3.0)]
BANNERS = [((38.0, -33.0, 0.2), 37.0, (1, -0.45), "eye", -1), ((37.0, 29.0, 0.0), 35.0, (1, 0.25), "hand", 1)]
IMPALED = (21.0, -40.0, 0.0)
PILES = [(44.0, -24.0, 1.4, 4, 1), (44.0, 22.0, 1.4, 3, 2)]
# The game's fire (sagekit/fire.py): the coal baskets of the two torches on iron arms off the gate
# posts (torch_bracket at y +-12.4, z 17.5), outside the sword-guard's walk (|y| < 12). EA's own
# glow and embers burn deep in the mouth (FXBONE, 18, -0.4, 10).
FIRE_POINTS = [(50.4, 13.3, 21.6, 'brazier'), (50.4, -13.3, 21.6, 'brazier')]


class Cave(Building):
    style = GoblinStyle()
    source = "WBCave_SKN"
    target = "WBCAVE"
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): the mouth's two braziers a torch flame each. 6.0 live (was 11.9).
    fire_points = [(50.4, 13.3, 21.6, 'torch'), (50.4, -13.3, 21.6, 'torch')]
    sheet = "wbcave.tga"
    sheet_normal = "wbcave_nrm.tga"
    own_textures = {"wbcave.tga": "wbcavH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    bake_hidden = ("V1", "V1A", "N_WINDOW", "N_FIRE")   # level 1: the level-up meshes are drawn later
    lifecycle = {"WBCave_ASKN": {"fill": True}}     # EA's build model is a remodel, not a cut (sagekit/lifecycle.py)
    views = {
        "rts": ((1.8, -2.9, 23.9), 341, 50, -38, 50),
        "close": ((1.8, -2.9, 23.9), 201, 24, -30, 45),
        "mouth": ((46.0, 0.0, 20.0), 120, 12, -20, 45),
        "ingame": ((1.8, -2.9, 23.9), 774, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from . import motifs as M
        out = []
        a, t, n = V((MOUTH_X, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        u0, u1, zt = GATE
        out += M.gate_frame(kit, a, t, n, u0, u1, 0.3, zt, r=1.1, fangs=5, fang=2.8)
        for u in (u0, u1):
            s = 1 if u > 0 else -1
            out += M.torch_bracket(kit, V((MOUTH_X + 0.9, u + s * 0.4, 17.5)), (1, s * 0.6), reach=1.8, length=3.4)
        for e in (-1, 1):
            pts = _bezier([(x, e * y, z) for x, y, z in TUSK], 9)
            out.append(kit.tube(pts, kit.taper(2.5, len(pts) - 1, 0.7), "bone", k=7, cap0="bone", cap1=None))
            for i, r in ((1, 2.95), (3, 2.6)):
                d = (pts[i + 1] - pts[i - 1]).normalized()
                out.append(kit.tube([pts[i] - d * 0.8, pts[i] + d * 0.8], [r, r], "iron", k=7, cap0="iron", cap1="iron"))
        x, y, z, s = TROPHY
        out += kit.horned_skull(V((x, y, z)), (1, 0, -0.1), s, horn=1.3, detail=2)
        out += kit.spike(V((x - 3.0, y, z + 1.4)), V((1, 0, 0.1)), 7.0, 0.45, k=4)
        (fx, fy, fz), h, s = TOTEM[:3], TOTEM[3], TOTEM[4]
        out += kit.totem(V((fx, fy, fz - 1.0)), h + 1.0, s, facing=(1, -0.55, 0), skulls=2)
        out += kit.horn_crown((fx, fy), fz + 0.5, 2.6, 5, 14.0, 1.6, rise=0.75, lean=0.25, phase=0.3, k=5, n=4,
                              root="rock", tip_from=0.45)
        for base, h, s in SPIKES:
            out += kit.skull_on_spike(V(base), h, s, facing=(1, -0.4 if base[1] < 0 else 0.4, 0))
        for foot, h, facing, mark, side in BANNERS:
            out += M.pole_banner(kit, V(foot), h, facing, 7.6, 19.0, mark=mark, top="skull", side=side)
        out += M.stakes(kit, [(55.5, -31.0, 0.3), (47.0, -40.0, 0.3), (40.0, -45.5, 0.3)], 6.5, r=0.6,
                        lean=(0.2, -0.2, 0), pitch=2.3, skulls=(3,), skull=2.0, seed=3)
        out += M.stakes(kit, [(53.5, 30.5, 0.0), (46.0, 36.5, 0.0)], 6.0, r=0.6, lean=(0.2, 0.15, 0), pitch=2.3,
                        skulls=(2,), skull=2.0, seed=5)
        out += kit.impaled(V(IMPALED), 19.0, 9.0, facing=(0.4, -1, 0))
        out += M.hide_frame(kit, V((6.0, -42.5, 0.0)), (0.3, -1), 8.0, 11.0, mark="claw")
        for px, py, pz, count, seed in PILES:
            out += kit.skull_pile(V((px, py, pz - 0.3)), 3.2, count, 2.2, seed=seed, face=(1, 0.3 * (1 if py > 0 else -1), 0))
        return out

    def decals(self):
        from ..paint import goblin_layers
        x, y, z, s = TROPHY
        fx, fy, fz, h, ts = TOTEM
        anchors = [(x + 1.0, y, z - 1.5, 3.0, 9.0), (fx, fy, fz + h + 0.2, 2.6, 8.0),
                   (IMPALED[0], IMPALED[1], 19.0 - 4.0, 2.5, 10.0)]
        anchors += [(b[0], b[1], b[2] + h - 0.6, 1.8, 6.0) for b, h, _ in SPIKES]
        anchors += [(px, py, pz + 0.8, 2.6, 2.0) for px, py, pz, _, _ in PILES]
        return [goblin_layers()["Gore"](anchors)]

    def emphasis(self, c, n):
        if c.x > 40:
            return 1.3                        # the mouth: gate, tusks, trophy
        return 1.0


def _bezier(ctrl, n):
    from mathutils import Vector as V
    p0, p1, p2, p3 = (V(p) for p in ctrl)
    return [p0 * (1 - s) ** 3 + p1 * 3 * s * (1 - s) ** 2 + p2 * 3 * s * s * (1 - s) + p3 * s ** 3
            for s in (i / n for i in range(n + 1))]
