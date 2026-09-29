"""The Goblin lumber mill (WildLumberMill; EA's Mordor mill MBLumMill_SKN, shipped as our own
WBLumMill_SKN): EA's yard kept whole - the lean-to shed of spiked posts and its log stacks, the
chopping stumps, the great log on its sawhorses, the fire pit, the slab floor - and made a
Goblin wood-camp:

    shed       a horned troll skull on the shed's front beam, a bleached tusk rising from
               each end of it, two crimson hides hung under it, painted
    crane      a lashed tripod over the great log's +X end (the new silhouette), a chain from
               its head with a hook and a skull
    totem      a totem at the yard's -Y front corner (horned skull, crossbar, ribcage)
    palisades  great sharpened logs along the back (+Y) and behind the shed (-X), skulls on some,
               two crimson hides hung on the back one's inner face
    saw        a frame saw standing over a log on two tall lashed trestles in the -Y yard
    piles      two stacked log piles, pinned by stakes
    frame      a hide drying frame by the fire pit
    banner     one ragged house-colour banner on a tall post at the +Y front corner

Ownership: Isengard and Mordor draw MBLumMill_* too; the redesign ships as WBLumMill_SKN (own
model), on our own sheet MBLumberMilH.tga, with our own house copy of MBHCLumberMill.

EA's facts (LUMBERMILL = model coordinates; sagekit measure: work/measure.json): x
-66.93..53.07, y -56.71..57.42, z -4.40..45.61 (1204 triangles); the floor slab at z -3.1; the
shed on the -X side under its front beam (x -38..-16, y -31..56, z 34..40), its roof falling to
z 19 at x -61; the great log x 0..48, |y| < 20, z 5..16.4 on X sawhorses; the fire pit (FIRE01,
EA's card) at (20, 33). The orcs work the stumps (x -35..-7, y -53..-19) and the log: the yard
between them stays clear. The level-up watchtower (V2, x -56..-22, y -51..-16, z -6..81)
stands on the -X-Y corner: nothing new there. Height limit +20 %: z 55.6.
"""
from sagekit.building import Building

from ..style import GoblinStyle

FLOOR = -3.1
BEAM = (-24.5, 40.0)                        # the shed's front beam: x, top z
TROPHY = (-23.5, 12.0, 42.5, 5.0)           # the troll skull on the beam (x, y, z, size)
BEAM_TUSKS = [(-24.0, -30.0), (-22.0, 52.0)]
HIDES = [(-6.0, "claw"), (30.0, "eye")]     # y of each hide under the beam, its mark
CRANE = [(36.5, -13.0), (50.8, -3.5), (40.0, 15.0)]   # the tripod's feet
CRANE_TOP = (43.0, 0.0, 42.0)
TOTEM = (40.0, -32.0)
PALISADES = [([(-14.0, 53.3), (14.0, 53.0), (44.0, 52.5)], (0.0, 0.1, 0)),          # along the back (+Y)
             ([(-63.2, -30.0), (-63.2, 8.0), (-63.2, 48.0)], (-0.05, 0.0, 0))]       # behind the shed (-X)
PALISADE_HIDES = [(6.0, "claw"), (31.0, "hand")]      # x of each hide on the back palisade, its mark
SAW = (18.0, -34.0)                         # the saw frame's centre (its log runs along x)
PILES = [((40.0, -46.0), 16.0, 4), ((40.0, 42.5), 14.0, 3)]   # log piles: centre, log length, bottom row
FRAME = (9.5, 47.0)                         # clear of EA's night torch post at (-2..0.8, 44..51)
BANNER = ((42.0, 32.0, FLOOR), 36.0, (1.0, -0.4))


class LumberMill(Building):
    style = GoblinStyle()
    source = "MBLumMill_SKN"
    target = "LUMBERMILL"
    own_model = "WBLumMill_SKN"            # isengard, mordor draws MBLumMill_SKN too (sagekit/ownership.py)
    sheet = "MBLumberMill.tga"
    sheet_normal = "MBLumberMill_NRM.tga"
    own_textures = {"MBLumberMill.tga": "MBLumberMilH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the unwrap overlapped (0.16%): seams at EA's islands and 8-degree turns
    bake_hidden = ("V2", "N_WINDOW", "N_FIRE", "FIRE01")
    views = {
        "rts": ((-6.9, 0.4, 20.6), 381, 50, -38, 50),
        "close": ((-6.9, 0.4, 20.6), 225, 24, -30, 45),
        "ingame": ((-6.9, 0.4, 20.6), 865, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from ..cave import motifs as M
        out = []
        x, y, z, s = TROPHY
        out += kit.horned_skull(V((x, y, z)), (1, 0, -0.1), s, horn=1.4, detail=2)
        for bx, by in BEAM_TUSKS:
            e = 1 if by > 10 else -1
            out += kit.tusk(V((bx, by, BEAM[1] - 2.5)), V((0.3, e * 0.6, 1.0)), V((0.1, e * 0.1, 1.0)), 12.0, 1.3, n=5,
                            k=5, collar=True)
        a, t, n = V((BEAM[0] + 1.0, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        for u, mark in HIDES:
            out += kit.hide_panel(a, t, n, u, BEAM[1] - 5.5, 7.5, 11.0, d=0.5, mark=mark)
        top = V(CRANE_TOP)
        feet = [V((fx, fy, FLOOR)) for fx, fy in CRANE]
        for f in feet:
            d = (top - f).normalized()
            out += kit.pole(f - d * 1.0, top + d * 2.5, 1.05, k=6)
        out += kit.lashing(top, V((0, 0, 1)), 1.6, turns=2, w=0.45)
        hook = top - V((0, 0, 17.0))
        out += kit.chain(top - V((0, 0, 1.2)), hook, link=1.5, w=0.55)
        out.append(kit.tube([hook, hook - V((0, 0, 1.4)), hook - V((-0.9, 0, 2.4)), hook - V((-1.6, 0, 1.6))],
                            [0.3, 0.3, 0.3, 0.26], "iron", k=4, cap0="iron", cap1="iron"))
        out += kit.skull(hook - V((0.4, 0, 3.6)), (1, -0.6, 0), 2.4, detail=1, tusks=True)
        out += kit.totem(V((TOTEM[0], TOTEM[1], FLOOR - 1.0)), 22.0, 4.2, facing=(1, -0.6, 0), skulls=2)
        for feet, lean in PALISADES:
            out += M.stakes(kit, [(x, y, FLOOR) for x, y in feet], 19.0, r=1.2, lean=lean, pitch=3.0,
                            skulls=(4, 11) if feet[0][0] > -20 else (6,), skull=2.6, seed=3)
        a, t, n = V((0, 51.6, 0)), V((1, 0, 0)), V((0, -1, 0))      # crimson hides on the back palisade's inner face
        for u, mark in PALISADE_HIDES:
            out += kit.hide_panel(a, t, n, u, FLOOR + 15.0, 7.0, 10.0, d=0.2, mark=mark)
        out += self._saw(kit, M)
        for (px, py), length, rows in PILES:
            out += self._pile(kit, V((px, py, FLOOR + 0.6)), length, rows)
        out += M.hide_frame(kit, V((FRAME[0], FRAME[1], FLOOR)), (0.5, -1), 8.0, 11.0, mark="hand")
        foot, h, facing = BANNER
        out += M.pole_banner(kit, V(foot), h, facing, 7.0, 17.0, mark="eye", top="skull", side=-1)
        return out

    @staticmethod
    def _saw(kit, M):
        """A frame saw over a log on two tall trestles: the log lashed on, a standing frame of two
        posts and two bars round a toothed iron blade through the log's end."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        cx, cy = SAW
        out = []
        for e in (-1, 1):
            m = V((cx + e * 6.0, cy, FLOOR))
            out += M.lashed_x(kit, m + V((0, 3.0, -0.6)), m + V((0, -0.8, 13.5)), m + V((0, -3.0, -0.6)),
                              m + V((0, 0.8, 13.5)), 0.55)
        log = [V((cx - 11.0, cy, FLOOR + 14.0)), V((cx + 11.0, cy, FLOOR + 14.0))]
        out.append(kit.tube(log, [2.1, 2.0], "timber", k=8, cap0="timber", cap1="timber"))
        for e in (-1, 1):
            out += kit.lashing(V((cx + e * 6.0, cy, FLOOR + 14.0)), V((1, 0, 0)), 2.0, turns=2, w=0.5)
        x = cx + 3.0                                            # the frame: across the log, blade vertical
        z0, z1 = FLOOR + 5.0, FLOOR + 24.0
        for e in (-1, 1):
            out += kit.pole(V((x, cy + e * 4.5, z0)), V((x, cy + e * 4.5, z1)), 0.55)
        for z in (z0 + 0.6, z1 - 0.6):
            out += kit.pole(V((x, cy - 5.6, z)), V((x, cy + 5.6, z)), 0.5)
        a, t, n = V((x, cy, 0)), V((0, 1, 0)), V((1, 0, 0))
        teeth = [(-0.7, z0 + 0.9)] + [(0.7 if i % 2 else 1.25, z0 + 0.9 + i * 0.9) for i in range(int((z1 - z0 - 1.8) / 0.9))]
        blade = [(-0.7, z0 + 0.9), (0.7, z0 + 0.9), (0.7, z1 - 0.9), (-0.7, z1 - 0.9)]
        out.append(prism_uz(a, t, n, blade, -0.12, 0.12, ["iron"] * 4, "iron", "iron"))
        for i in range(1, int((z1 - z0 - 1.8) / 1.2)):
            z = z0 + 0.9 + i * 1.2
            out.append(prism_uz(a, t, n, [(0.65, z - 0.5), (1.4, z - 0.1), (0.65, z + 0.3)], -0.1, 0.1, ["iron"] * 3,
                                "iron", "iron"))
        for z in (z0 + 1.2, z1 - 1.2):                          # the blade's pins through the bars
            out.append(kit.tube([V((x - 0.8, cy, z)), V((x + 0.8, cy, z))], [0.35, 0.35], "iron", k=4, cap0="iron",
                                cap1="iron"))
        return out

    @staticmethod
    def _pile(kit, c, length, rows):
        """Logs stacked in a pyramid along x: `rows` at the bottom, one fewer each course, pinned at
        the ends by two stakes a side."""
        from mathutils import Vector as V
        out = []
        r = 1.7
        for course in range(rows):
            n = rows - course
            z = c.z + r + course * r * 1.72
            for i in range(n):
                y = c.y + (i - (n - 1) / 2) * r * 2.02
                j = 0.4 * ((i + course) % 3 - 1)
                out.append(kit.tube([V((c.x - length / 2 + j, y, z)), V((c.x + length / 2 + j, y, z))], [r, r * 0.95],
                                    "timber", k=7, cap0="timber", cap1="timber"))
        half = rows * r + 0.8
        for e in (-1, 1):
            for f in (-1, 1):
                out += kit.stake(V((c.x + e * length * 0.3, c.y + f * half, c.z - 1.0)),
                                 V((c.x + e * length * 0.3, c.y + f * (half + 0.4), c.z + rows * r * 1.6)), 0.5)
        return out

    def decals(self):
        from ..paint import goblin_layers
        x, y, z, s = TROPHY
        anchors = [(x + 1.0, y, z - 1.5, 2.8, 9.0), (CRANE_TOP[0], CRANE_TOP[1], CRANE_TOP[2] - 20.5, 1.8, 3.0),
                   (TOTEM[0], TOTEM[1], FLOOR + 21.0, 2.4, 8.0)]
        return [goblin_layers()["Gore"](anchors)]

    def emphasis(self, c, n):
        if c.z > 30:
            return 1.3                        # the beam's trophies and the crane
        return 1.0
