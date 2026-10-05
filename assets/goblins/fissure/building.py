"""The Goblin fissure (GoblinFissure; WBFissure): EA's horseshoe of rock (CYLINDER01, painted
from WBStone) round a crack in the ground (PLANE01, WBFissure) kept whole, and made a vent the
Goblins worship and work:

    idol       a great horned troll skull nailed to the overhang at the crack's head, looking
               down the fissure, blood run from it
    crests     a horn crown and a skull on an iron spike on the tall back peak (the new
               silhouette), a pair of bleached tusks rising from each arm's crest
    climb      a lashed ladder up the -Y arm (the camera's side) to its crest, where the banner
               stands on a tall post beside a fire bowl
    ridges     iron spikes along both arms' ridges, leaning out, their points bloodied or bone
    gate       a jaw gate over the crack's mouth: a timber tower on each lip (troll skulls on
               their corners), a plank bridge between their decks high over the floor with bone
               teeth hanging from its front and a skull on a chain (the new silhouette), a tall
               totem before the -Y tower
    palisades  tall sharpened stakes running back from each tower along the arms' feet,
               skulls on some; skull piles

EA's facts (CYLINDER01 mesh coordinates: model minus (1.6, 8.06); sagekit measure:
work/measure.json): x -56.11..52.52, y -56.98..62.45, z -4.01..47.93 (230 triangles). The back
peak (x -36..-31, y 3) reaches z 48; the arms wrap round the crack's head, +Y at y 23..38 (crest
z 44 at x -21), -Y at y -27..-37 (crest z 36 at x -16..-6); the overhang at the crack's head
(x -26..-30, y +-10) hangs from z 32 down to 20. The floor (PLANE01, x -36..64, y -33..21, z
0.3..8) and the steam bone over it (STEAM01, x -3, y 0) stay open: nothing new stands on it or
over it. Height limit +20 %: z 58.3.
"""
from sagekit.building import Building

from ..style import GoblinStyle

IDOL = (-25.5, 0.0, 29.5, 6.5)             # x, y, z, size
PEAK = (-33.5, 3.0, 46.0)
TUSKS = [((-21.0, 25.0, 42.5), (0.0, 1.0)), ((-15.0, 27.5, 40.5), (0.3, 1.0)),
         ((-16.0, -30.5, 34.5), (0.0, -1.0)), ((-7.0, -31.5, 34.0), (0.3, -1.0))]
BANNER = ((-11.5, -31.0, 34.5), 15.0, (0.6, -1.0))
BRAZIER = (-3.0, -29.5, 33.5)              # a fire bowl on the -Y crest by the ladder's top
LADDER = ((10.0, -44.5, 1.0), (-1.5, -33.5, 29.0))
FENCES = [([(37.5, -45.5, 0.3), (27.0, -44.5, 0.6), (16.0, -48.0, 0.6)], (0.05, -0.2, 0), (2,)),
          ([(40.0, 32.5, 3.5), (32.0, 36.0, 4.0), (24.0, 40.0, 4.0)], (0.05, 0.2, 0), (1,))]
# iron spikes along both arms' ridges: (x, y, rock z), leaning out along (ox, oy)
RIDGES = [([(-16.0, 28.0, 40.2), (-8.0, 33.0, 37.5), (0.0, 33.0, 38.1), (8.0, 31.0, 35.4), (14.0, 30.0, 32.5)], (0.0, 1.0)),
          ([(-31.0, -12.0, 35.2), (-28.0, -20.0, 34.3), (-1.0, -33.0, 31.9), (5.0, -33.0, 25.1)], (0.0, -1.0))]
GATE = [((42.0, -41.0, 0.3), (0.3, -1, 0)), ((44.5, 28.5, 2.4), (0.3, 1, 0))]   # the gate towers on the mouth's lips
DECK = 20.0                                 # their decks and the bridge between them
TOTEM = ((36.0, -48.0, 0.3), 31.0, 5.6)     # foot, height, skull size
PILES = [(34.0, -43.0, 0.0, 3, 1), (47.0, 37.0, 0.5, 3, 2)]
# The game's fire (sagekit/fire.py), in model space (CYLINDER01 + (1.6, 8.06)): the coals of the
# fire bowl on the -Y crest (BRAZIER, kit.brazier h 2.6). EA's STEAM01/FXBONE01 steam the floor.
FIRE_POINTS = [(-1.4, -21.4, 36.4, 'brazier')]


class Fissure(Building):
    style = GoblinStyle()
    source = "WBFissure"
    target = "CYLINDER01"
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): its brazier a torch flame. 3.0 live (was 6.0).
    fire_points = [(-1.4, -21.4, 36.4, 'torch')]
    sheet = "WBStone.tga"
    sheet_normal = "WBStone_NRM.tga"
    own_textures = {"WBStone.tga": "WBStonH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    lifecycle = {"WBFissure_R": {"skip": "the ruin a separate object (WildFissureHole) leaves on the ground once the fissure is "
                                        "gone: rubble of its own, no piece on the healthy body"}}
    facet_islands = 8                       # the unwrap overlapped (3.4%): seams at EA's islands and 8-degree turns
    bake_hidden = ("N_WINDOW", "N_FIRE")
    views = {
        "rts": ((-0.2, 10.8, 22.0), 373, 50, -38, 50),
        "close": ((-0.2, 10.8, 22.0), 220, 24, -30, 45),
        "head": ((-20.0, 0.0, 28.0), 110, 20, -10, 45),
        "ingame": ((-0.2, 10.8, 22.0), 848, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from ..cave import motifs as M
        out = []
        x, y, z, s = IDOL
        out += kit.horned_skull(V((x, y, z)), (1, 0, -0.2), s, horn=1.35, detail=2)
        out += kit.spike(V((x - 3.5, y, z + 1.2)), V((1, 0, 0.05)), 7.0, 0.5, k=4)
        px, py, pz = PEAK
        out += kit.horn_crown((px, py), pz - 1.0, 2.2, 4, 10.0, 1.3, rise=0.8, lean=0.3, phase=0.4, k=5, n=4,
                              root="rock", tip_from=0.45)
        out += kit.skull_on_spike(V(PEAK), 6.5, 3.6, facing=(1, -0.3, 0))
        for base, (ox, oy) in TUSKS:
            out += kit.tusk(V(base), V((ox * 0.5, oy * 0.55, 1.0)), V((-ox * 0.2, -oy * 0.25, 1.0)), 11.0, 1.2, n=5,
                            k=5, collar=True)
        foot, h, facing = BANNER
        out += M.pole_banner(kit, V(foot), h, facing, 6.5, 15.0, mark="claw", top="horned", skull=2.8, side=0)
        out += kit.brazier(V(BRAZIER), 2.1, 2.6)
        f, t = LADDER
        out += M.ladder(kit, V(f), V(t), width=3.0, pitch=2.4)
        for feet, lean, skulls in FENCES:
            out += M.stakes(kit, feet, 10.0, r=0.9, lean=lean, pitch=2.6, skulls=skulls, skull=2.4, seed=len(feet))
        for pts, (ox, oy) in RIDGES:
            for i, (rx, ry, rz) in enumerate(pts):
                out += kit.spike(V((rx, ry, rz - 0.6)), V((ox * 0.45, oy * 0.45, 1.0)), 6.5 + 1.5 * (i % 2), 0.55, k=4,
                                 kink=0.06, tip="bone" if i % 2 else "gore")
        out += self._gate(kit, M)
        (tx, ty, tz), th, ts = TOTEM
        out += kit.totem(V((tx, ty, tz - 1.0)), th + 1.0, ts, facing=(1, -0.6, 0), skulls=2)
        for px, py, pz, count, seed in PILES:
            out += kit.skull_pile(V((px, py, pz - 0.3)), 3.0, count, 2.1, seed=seed, face=(1, -0.3, 0))
        return out

    @staticmethod
    def _gate(kit, M):
        """The jaw gate over the crack's mouth: a timber tower on each lip, a bridge of two logs and
        planks between their decks across the mouth (high over the floor, which stays open), bone
        teeth hanging from its front like a jaw, rope rails, a skull hung under its middle."""
        from mathutils import Vector as V
        out, decks = [], []
        for (x, y, z), facing in GATE:
            solids, deck = M.watchtower(kit, (x, y, z), 3.5, DECK, braces=((0, 1), (1, 2)) if y < 0 else ((0, 1), (3, 0)))
            out += solids
            decks.append(deck)
            e = -1 if y < 0 else 1
            out += kit.horned_skull(V((x + 3.2, y + e * 3.2, DECK + 6.8)), facing, 3.4, horn=1.3, detail=1)
        a = V((0.5 * (decks[0][2].x + decks[0][3].x), decks[0][2].y, DECK))       # the -Y deck's +Y edge
        b = V((0.5 * (decks[1][0].x + decks[1][1].x), decks[1][0].y, DECK))       # the +Y deck's -Y edge
        d = (b - a).normalized()
        s = V((d.y, -d.x, 0))                                                       # toward +X
        for e in (-1, 1):
            out += kit.pole(a - d * 3.0 + s * e * 2.0 - V((0, 0, 0.5)), b + d * 3.0 + s * e * 2.0 - V((0, 0, 0.5)), 0.7)
        n = int((b - a).length / 1.6) + 1
        for i in range(n + 1):
            m = a.lerp(b, i / n) + V((0, 0, 0.3))
            out.append(kit.tube([m - s * 2.8, m + s * 2.8], [0.32, 0.32], "timber", k=4, cap0="timber", cap1="timber",
                                phase=0.785, squash=2.0))
        for e in (-1, 1):                                      # rope rails on posts
            posts = [a.lerp(b, f) + s * e * 2.6 for f in (0.0, 0.25, 0.5, 0.75, 1.0)]
            for p in posts[1:-1]:
                out += kit.stake(p - V((0, 0, 0.6)), p + V((0, 0, 4.2)), 0.35)
            out.append(kit.tube([p + V((0, 0, 3.2)) for p in posts], [0.16] * len(posts), "rope", k=3, cap0="rope",
                                cap1="rope"))
        teeth = 7                                               # the jaw: bone teeth hanging off the front
        for i in range(teeth):
            f = (i + 0.5) / teeth
            edge = abs(f - 0.5) * 2
            base = a.lerp(b, f) + s * 2.6 - V((0, 0, 0.2))
            out += kit.tusk(base, V((0, 0, -1)), s * 0.35 + V((0, 0, -1)), 5.0 + 4.5 * edge ** 1.5, 0.95, n=4, k=5,
                            collar=False, sink=0.4)
        mid = a.lerp(b, 0.5) + s * 1.0
        out += kit.chain(mid - V((0, 0, 0.8)), mid - V((0, 0, 4.0)))
        out += kit.skull(mid - V((0, 0, 5.8)), (1, -0.4, 0), 2.8, detail=1, tusks=True)
        return out

    def decals(self):
        from ..paint import goblin_layers
        x, y, z, s = IDOL
        px, py, pz = PEAK
        anchors = [(x + 1.0, y, z - 2.0, 3.2, 14.0), (px, py, pz + 6.0, 1.8, 6.0)]
        anchors += [(px, py, pz + 0.8, 2.4, 2.0) for px, py, pz, _, _ in PILES]
        return [goblin_layers()["Gore"](anchors)]

    def emphasis(self, c, n):
        if c.z > 30 or c.x < -20:
            return 1.3                        # the idol and the crests
        return 1.0
