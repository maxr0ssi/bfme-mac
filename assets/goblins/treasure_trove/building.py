"""The Goblin treasure trove (WildTreasureTrove; WBTreaTrov_SKN): EA's carved dragon kept whole -
its head with open jaws at -Y, the body curled round the back, the great claw clutching the
hoard at +X, the crest spikes - lying on its rock bed (ROCK, EA's) round the heaped gold and
jewels (COIN01, JEWELS: EA's). Made the Goblins' prize, a dead dragon shackled on its hoard:

    horns      two great horns rising from the back of the head and sweeping back (crimson,
               bleached tips): the new silhouette
    nails      two iron spikes driven down through the skull, a goblin skull on each
    chains     the jaw chained at both corners to iron ring-stakes in the ground, heavy links
    bands      a spiked iron strap over the head, spiked iron collars on the horns
    plunder    iron-bound strongboxes along the +X front, a torch on a post among them
    trophies   skull piles by the jaws
    banner     one ragged house-colour banner on a post at the -Y front, by the head

EA's facts (world_space: the body hangs on a bone turned 243 degrees about z, so the design
works in model axes; sagekit measure: work/measure.json): WBTREATROVT in the model x
-42.5..56.4, y -69.6..48.7, z -9.38..51.84 (1585 triangles on WBTreaTrov). The head's top lies
at z 36-38 over x -10..18, y -40..-62, the jaws under it open at y -45..-60 (FX_MOUTH at -3.9,
-41.9, 19.8); the hoard (x 3..41, y -42..-3) and the two goblins who work it stay clear; the
level-up meshes stand on the -X+Y side (V1, the tower, x -54..-8, y -3..37, z 35..92, and its
rock V1A): nothing new there. Height limit +20 %: z 64.1.
"""
import math

from sagekit.building import Building

from ..style import GoblinStyle

HORNS = [((-6.5, -42.0, 35.0), (-0.28, 0.3, 1.0)), ((12.0, -44.0, 34.0), (0.28, 0.3, 1.0))]
NAILS = [(0.5, -52.0, 37.9), (9.0, -57.0, 36.8)]
CHAINS = [((-4.0, -57.5, 16.0), (-17.0, -62.0, 4.0)), ((15.5, -61.0, 20.0), (27.0, -63.0, 0.0))]
CHESTS = [((46.0, -26.0, 0.8), (1, -0.35), 5.4), ((50.5, -15.5, 0.5), (1, 0.1), 4.6), ((39.5, -38.5, 0.9), (0.7, -1), 4.2)]
TORCH = (51.5, -22.0, 0.6)
BANNER = ((30.0, -50.0, 3.0), 30.0, (0.8, -1.0))
# a riveted iron band strapped over the head between the horns and the nails, spiked along its
# top: [(x, y, surface z)] (the neck and body lie behind the head from the camera)
BANDS = [[(-17.5, -48.5, 29.0), (-16.5, -48.5, 35.5), (-12.0, -48.5, 35.0), (-8.0, -48.5, 36.3), (-4.0, -48.5, 37.2),
          (0.0, -48.5, 36.9), (4.0, -48.5, 35.9), (8.0, -48.5, 36.5), (12.0, -48.5, 37.7), (15.5, -48.5, 34.5),
          (17.3, -48.5, 29.0)]]
PILES = [(-12.0, -64.0, 4.2, 3, 1), (22.0, -54.0, 6.2, 3, 2)]
# The game's fire (sagekit/fire.py): the coal basket of the torch on its post among the strongboxes
# (TORCH, torch_bracket reach 1.2). EA's glow and smoke stay at the jaws (FX_MOUTH).
FIRE_POINTS = [(53.2, -22.0, 10.4, 'brazier')]


class TreasureTrove(Building):
    style = GoblinStyle()
    source = "WBTreaTrov_SKN"
    target = "WBTREATROVT"
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): none. 0.0 live (was 6.0).
    fire_points = []
    sheet = "WBTreaTrov.tga"
    sheet_normal = "WBTreaTrov_NRM.tga"
    own_textures = {"WBTreaTrov.tga": "WBTreaTroH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    world_space = True                      # WBTREATROVT hangs on a bone turned about z
    facet_islands = 8                       # the unwrap overlapped (0.58%): seams at EA's islands and 8-degree turns
    bake_hidden = ("V1", "V1A", "N_WINDOW", "N_FIRE")
    lifecycle = {"WBTreaTrov_ASKN": {"fill": True},     # EA's build model is a remodel, not a cut (sagekit/lifecycle.py)
                 "WBTreaTrov_R": {"skip": "the ruin left on the ground after the collapse (POST_RUBBLE): rubble of "
                                          "its own, no piece on the healthy body"}}
    views = {
        "rts": ((6.9, -10.5, 21.2), 365, 50, -38, 50),
        "close": ((6.9, -10.5, 21.2), 216, 24, -30, 45),
        "head": ((5.0, -52.0, 30.0), 110, 18, -60, 45),
        "ingame": ((6.9, -10.5, 21.2), 830, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from ..cave import motifs as M
        out = []
        for base, d0 in HORNS:
            out += kit.horn(V(base), V(d0), V((d0[0] * 1.1, 1.0, 0.1)), 40.0, 3.3, n=8, k=7, tip_from=0.5)
            out += kit.hoop((base[0], base[1]), base[2] + 2.0, 3.1, h=1.6, th=0.6, inner=1.4, k=7, rivets=2)
            for i in range(5):                                  # the horn's collar is spiked
                a = 2 * math.pi * i / 5 + 0.3
                rad = V((math.cos(a), math.sin(a), 0))
                out += kit.spike(V(base) + rad * 3.5 + V((0, 0, 2.0)), rad + V((0, 0, 0.35)), 3.2, 0.42, k=4)
        for x, y, z in NAILS:
            out += kit.skull_on_spike(V((x, y, z - 0.6)), 10.0, 3.0, facing=(0.4, -1, 0))
            out.append(kit.tube([V((x, y, z - 1.0)), V((x, y, z + 0.4))], [1.1, 0.9], "iron", k=6, cap0="iron", cap1="iron"))
        for jaw, anchor in CHAINS:
            out += M.ring_stake(kit, V(anchor), r=0.8, height=2.6, ring=1.8)
            a = V(anchor) + V((0, 0, 2.5))
            out += kit.chain(V(jaw), a, link=2.4, w=0.95, th=0.4)
            out.append(kit.tube([V(jaw) - V((0, 0, 0.8)), V(jaw) + V((0, 0, 0.8))], [1.2, 1.2], "iron", k=6, cap0="iron",
                                cap1="iron"))
        out += self._bands(kit)
        for c, facing, w in CHESTS:
            out += M.chest(kit, V(c), facing, w=w, d=w * 0.66, h=w * 0.55)
        out += M.post(kit, V(TORCH), 7.0, 0.55, point=False)
        out += M.torch_bracket(kit, V(TORCH) + V((0.5, 0, 6.0)), (1, 0), reach=1.2, length=3.0)
        foot, h, facing = BANNER
        out += M.pole_banner(kit, V(foot), h, facing, 6.6, 15.5, mark="fangs", top="skull", side=1)
        for px, py, pz, count, seed in PILES:
            out += kit.skull_pile(V((px, py, pz - 0.3)), 3.0, count, 2.1, seed=seed, face=(0.4, -1, 0))
        return out

    @staticmethod
    def _bands(kit):
        """Flat riveted iron straps laid over the neck and the body, an iron spike standing out of
        every other point along the top."""
        from mathutils import Vector as V
        out = []
        for path in BANDS:
            pts = [V(p) for p in path]
            off = []
            for i, p in enumerate(pts):
                t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
                n = V((-t.z, 0.0, t.x)) if t.x >= 0 else V((t.z, 0.0, -t.x))       # square to the path, outward
                if n.z < 0:
                    n = -n
                off.append((p + n * 0.7, n))
            line = [p for p, _ in off]
            out.append(kit.tube(line, [1.4] * len(line), "iron", k=4, cap0="iron", cap1="iron", phase=0.785,
                                squash=0.35))
            for i, (p, n) in enumerate(off[1:-1], 1):
                if i % 2 == 0 and p.z > 12:
                    out += kit.spike(p + n * 0.3, n + V((0, -0.15, 0)), 4.2, 0.5, k=4, tip="bone" if i % 4 else "gore")
        return out

    def decals(self):
        from ..paint import goblin_layers
        anchors = [(x, y, z + 10.0, 1.8, 10.0) for x, y, z in NAILS]
        anchors += [(px, py, pz + 0.8, 2.6, 2.0) for px, py, pz, _, _ in PILES]
        return [goblin_layers()["Gore"](anchors)]

    def emphasis(self, c, n):
        if c.y < -38 and c.z > 25:
            return 1.3                        # the head: horns, nails, skulls
        return 1.0
