"""The Isengard siege works (IsengardSiegeWorks), pass 2 "the war-yard": EA's frame kept whole -
the six timber posts and their capped heads, the braced sides, the great awning with the White
Hand painted on it, the crates along the sides - and made Saruman's siege yard:

Pass 3 (the citadel's recipe, 2026-09-29): the war-yard's gate made the citadel's: each trident's middle is the
citadel's broad blade now (6.2 x 4.2, two fins a face, the White Hand in a pointed-arch slot on
its outer face) with fire grates in its saddle; a greater Hand shield on the chain; the half-built
siege tower stands outside the -Y edge, over the awning.

Pass 4 (2026-09-30, "the furnace towers look a lil stupid", Max): the tridents, their chain and
shield and the four needles out of the post heads went. Two low forge plinths flank the mouth
instead (silver coping, spikes, two fire grates each, the Hand in a slot between); the half-built
siege tower is the yard's one tall new mass.

    tridents   a blade tower between two leaning horns on a stone saddle, either side of the
               yard's mouth (+X, where the engines roll out), ember slits, a chain slung between
               them with the Hand on a shield, a brazier at each one's inner foot
    needles    iron needles with knife fins out of four post heads
    engines    under the awning, a half-built siege tower (iron-plated below, a drawbridge, a
               pointed roof frame) and a ram with an iron wedge head slung from two A-frames
    forge      under the awning's +Y side; knife fins clasp the posts; a half-built ladder on
               the +Y side, felled trunks stacked on the -Y side

EA's facts (world axes, `world_space`: IBSEIGEFRAME hangs on a bone moved (20.3, -0.3, 0.7)):
x -58.7..57.9, y -51.0..50.7, z -2.2..60.9 (932 triangles). The posts at (-45, +-42), (0, +-42)
and (42, +-42), heads to z 50..61; the awning at z 33..40 over x -45..42; crates along the sides
(x 3..37, |y| 43..51, to z 19). EA's own fire burns on the -X posts' heads (BN_FIRE05/06 at
(-44, -43, 58), (-44, 40, 57)). Kept clear: the mouth (units leave at (66.7, 0) for (130, 0):
x > 40, |y| < 22), the level-up tower (V2, V2A: x -81..-37, |y| < 26, to z 90), the walls
IBSEIGEWALLS (their own sheet, EA's), the night torch posts (N_WINDOW) at (60, -61), (60, 58).
"""
from sagekit.building import Building

from ..style import IsengardStyle

FIRE_POINTS = [
    (49.4, -39.1, 1.3, 'furnace'), (49.4, -24.9, 1.3, 'furnace'), (40.0, -28.0, 5.6, 'brazier'),
    (49.4, 24.9, 1.3, 'furnace'), (49.4, 39.1, 1.3, 'furnace'), (40.0, 28.0, 5.6, 'brazier'),
    (14.0, 33.0, 3.9, 'hearth'), (20.6, 29.7, 3.3, 'crucible')
]
# The fire budget (2026-10-04, docs/ART.md "Fire budget": at most 60 live particles): each forge plinth
# keeps one furnace and one flame (the sparks of one cover both), the forge's crucible (7 units off)
# merges into its hearth. 55.8 live (was 253).
FIRE_POINTS = [
    (49.4, -39.1, 1.3, 'furnace'), (49.4, -24.9, 1.3, 'flame'), (40.0, -28.0, 5.6, 'brazier'),
    (49.4, 24.9, 1.3, 'flame'), (49.4, 39.1, 1.3, 'furnace'), (40.0, 28.0, 5.6, 'brazier'),
    (14.0, 33.0, 3.9, 'hearth')
]

PYLONS = [(47.0, -32.0), (47.0, 32.0)]          # the forge plinths' centres, along y
PLINTH = (11.8, 2.1, 7.5)                       # half length (y), half width (x), height
SIEGE_TOWER = ((-14.0, -46.4), (1.0, 0.0), 7.0, 54.0)  # outside the awning's -Y edge, over it: foot, t, width, height
RAM = ((12.0, -20.0), (1.0, 0.0), 24.0, 9.0)
POSTS = [(-45.0, -42.5), (-45.0, 40.5), (0.0, -42.0), (0.0, 40.5), (42.0, -42.0), (42.0, 40.5)]
LADDER = ((-18.0, 48.5), 40.0)
LOGS = ((-34.0, -46.3), 13.0, 1.3)
FORGE = ((14.0, 33.0, 0.0), (-1.0, 0.0))        # under the awning's +Y side, facing in


class SiegeWorks(Building):
    style = IsengardStyle()
    source = "IBSeigeWork"
    target = "IBSEIGEFRAME"
    sheet = "IBSeigeWork.tga"
    sheet_normal = "IBSeigeWork_NRM.tga"
    own_textures = {"IBSeigeWork.tga": "IBSeigeWorH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    lifecycle = dict.fromkeys(("IBSeigeW_DRC", "IBSeigeW_DRCA", "IBSeigeW_DROA", "IBSeigeW_DSOP", "IBSeigeWork_DrA"), {
        "skip": "the mouth's doors and wheels: a Draw of their own (ModuleTag_02) painted from the walls' sheet "
                "(IBSeigeWall), which stays EA's; never on the healthy body"})
    # EA's damaged models drop and sag the awning: cut along them, our frame kept scraps (10-16% open
    # backs); filled, what remains are thin seams across the tarp the RTS renders do not show as holes
    lifecycle.update({
        "IBSeigeW_D1": {"fill": True, "backs": (0.05, "thin seams across the tarp where EA's pieces part, "
                                                     "4.4% past EA's; no hole in the RTS renders")},
        "IBSeigeW_D2": {"fill": True, "backs": (0.12, "the collapse's last frames, the cut posts' ends: 11.2% "
                                                     "past EA's; no hole in the RTS renders")},
        "IBSeigeW_D3": {"fill": True, "backs": (0.13, "mid-collapse, the tarp and posts' cut ends: 12.4% past "
                                                     "EA's with the blended poses (11.5% before them, the model "
                                                     "unchanged since 2026-10-01); no hole in the RTS renders")}})
    world_space = True                   # IBSEIGEFRAME's bone is moved (20.3, -0.3, 0.7): design and fire share world axes
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": an identity building, at most 20 live
    # particles): the two forge furnaces. 19.4 live (was 55.8).
    fire_points = [(49.4, -39.1, 1.3, 'furnace'), (49.4, 39.1, 1.3, 'furnace')]
    views = {
        "rts": ((0.0, 0.0, 29.3), 368, 50, -38, 50),
        "close": ((10.0, 0.0, 30.0), 230, 24, -30, 45),
        "ingame": ((-0.4, -0.2, 29.3), 836, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_industry import logged
        return logged(kit, self._pieces)

    def _pieces(self, kit):
        from mathutils import Vector as V
        out = self._pylons(kit, V)
        out += self._post_fins(kit, V)
        (lx, ly), h = LADDER
        out += kit.siege_ladder(V((lx, ly, 0.0)), V((1, 0, 0)), V((0, 1, 0)), h, w=4.4, rungs=14, built=0.6, lean=0.2)
        (gx, gy), length, r = LOGS
        out += kit.log_stack(V((gx, gy, 0.0)), V((1, 0, 0)), length, r, rows=3)
        from .. import shapes_industry as I
        from .. import shapes_industry_big as B
        c, t = FORGE
        out += I.forge_bay(kit, V(c), t, 1.5)
        (sx, sy), t, w, h = SIEGE_TOWER
        out += B.siege_tower(kit, V((sx, sy, 0.0)), t, w, h, built=0.78)
        (rx, ry), t, length, h = RAM
        out += B.ram(kit, V((rx, ry, 0.0)), t, length, h)
        return out

    @staticmethod
    def _pylons(kit, V):
        """Two forge plinths flanking the mouth (pass 4: the tridents on them went): a low battered
        stone block along the mouth's sides, a silver coping with iron spikes, two fire grates in
        its front, the White Hand in a pointed-arch slot between them; a brazier at each one's
        inner foot."""
        from .. import shapes_industry_big as B
        out = []
        for x, y in PYLONS:
            out += SiegeWorks._plinth(kit, V, B, x, y)
            out += kit.brazier(V((x - 7.0, y - (4.0 if y > 0 else -4.0), 0.0)), 1.9, 5.5)
        return out

    @staticmethod
    def _plinth(kit, V, B, x, y):
        from sagekit.blender.geometry import loft
        Lh, W, h = PLINTH
        ring = lambda z, gx, gy: [V((x - W - gx, y - Lh - gy, z)), V((x + W + gx, y - Lh - gy, z)),     # noqa: E731
                                  V((x + W + gx, y + Lh + gy, z)), V((x - W - gx, y + Lh + gy, z))]
        out = [loft([ring(-0.3, 0.9, 0.9), ring(h - 1.0, 0.0, 0.0), ring(h - 1.0, 0.4, 0.4), ring(h, 0.4, 0.4),
                     ring(h, -0.4, -0.4), ring(h + 0.8, -0.8, -0.8)], ["stoneA", "trim", "trim", "trim", "iron"],
                    cap0=("stoneA", False), cap1=("iron", True))]
        a, t, n = V((x + W + 0.4, y, 0)), V((0, 1, 0)), V((1, 0, 0))
        out += kit.spike_row(V((x, y, 0)), t, n, -Lh + 1.0, Lh - 1.0, h + 0.8, 3.2, 7, d=0.0, lean=0.0, r=0.42)
        for e in (-1, 1):                                   # fire grates in its front, either side of the Hand
            out += kit.fire_grate(V((x + W, y + e * Lh * 0.6, 0.0)), t, n, w=3.4, h=3.6, d=2.4)
        out += B.hand_slot(kit, a, t, n, 0.6, 3.6, h - 2.2, d0=-0.6, d1=0.6)
        return out

    @staticmethod
    def _post_fins(kit, V):
        """Knife-edge iron fins clasping each post below the awning, silver fronts, leaning out."""
        import math

        from .. import shapes_industry as I
        out = []
        for x, y in POSTS:
            sy = 1 if y > 0 else -1
            for ang in (90.0 * sy - 45.0, 90.0 * sy + 45.0):
                d = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
                out += I.fin(kit, V((x, y, 0)), d, 2.2, [(1.4, -0.3), (7.0, -0.3), (3.0, 34.0), (1.4, 27.0)], 0.9,
                             tag="iron")
        return out


def kit_profile():
    from ..shapes_spire import BROAD
    return BROAD
