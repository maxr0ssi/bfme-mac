"""The Isengard siege works (IsengardSiegeWorks), pass 2 "the war-yard": EA's frame kept whole -
the six timber posts and their capped heads, the braced sides, the great awning with the White
Hand painted on it, the crates along the sides - and made Saruman's siege yard:

Pass 3 (the citadel's recipe, 2026-09-29): the war-yard's gate made the citadel's: each trident's middle is the
citadel's broad blade now (6.2 x 4.2, two fins a face, the White Hand in a pointed-arch slot on
its outer face) with fire grates in its saddle; a greater Hand shield on the chain; the half-built
siege tower stands outside the -Y edge, over the awning.

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
    (49.4, -40.1, 1.2, 'furnace'), (49.4, -23.9, 1.2, 'furnace'), (40.0, -28.0, 5.6, 'brazier'),
    (49.4, 23.9, 1.2, 'furnace'), (49.4, 40.1, 1.2, 'furnace'), (40.0, 28.0, 5.6, 'brazier'),
    (14.0, 33.0, 3.9, 'hearth'), (20.6, 29.7, 3.3, 'crucible')
]

PYLONS = [(47.0, -32.0), (47.0, 32.0)]          # the tridents' centres; their horns along y
SIEGE_TOWER = ((-14.0, -46.4), (1.0, 0.0), 7.0, 54.0)  # outside the awning's -Y edge, over it: foot, t, width, height
RAM = ((12.0, -20.0), (1.0, 0.0), 24.0, 9.0)
# iron needles out of the middle and +X posts' heads (the -X heads carry EA's fire): centre, foot z
NEEDLES = [((0.6, -41.5), 46.0), ((0.7, 39.6), 44.0), ((43.9, -40.4), 52.0), ((44.4, 37.9), 50.0)]
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
    world_space = True                   # IBSEIGEFRAME's bone is moved (20.3, -0.3, 0.7): design and fire share world axes
    fire_points = FIRE_POINTS
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
        for (nx, ny), z0 in NEEDLES:
            out += I.blade_post(kit, V((nx, ny, 0.0)), 72.5 - z0, w=0.9, z0=z0)
            for k in range(4):                             # knife fins round each needle's foot
                d = ((1, 0), (0, 1), (-1, 0), (0, -1))[k]
                out += I.fin(kit, V((nx, ny, 0.0)), d, 0.6, [(0.5, z0), (2.6, z0 + 1.0), (1.0, z0 + 9.0), (0.5, z0 + 8.0)],
                             0.45, tag="iron")
        return out

    @staticmethod
    def _pylons(kit, V):
        """Two trident towers flanking the mouth (a blade tower between two leaning horns on a
        stone saddle), a chain slung between their collars, a brazier at each one's inner foot."""
        from .. import shapes_industry as I
        from .. import shapes_industry_big as B
        out = []
        collars = []
        for x, y in PYLONS:
            out += SiegeWorks._trident(kit, V, B, x, y)
            collars.append(V((x - 0.75, y - (2.2 if y > 0 else -2.2), 52.0)))          # the inner edge at z 52
            out += kit.brazier(V((x - 7.0, y - (4.0 if y > 0 else -4.0), 0.0)), 1.9, 5.5)
        low = V((48.0, 0.0, 46.0))                   # high over the mouth: the engines roll out under it
        out += kit.chain(collars[0], low, link=2.2, w=0.6, th=0.25)
        out += kit.chain(low, collars[1], link=2.2, w=0.6, th=0.25)
        out += kit.shield(V((48.0, 0.0, 0.0)), V((0, 1, 0)), V((1, 0, 0)), 0.0, 33.0, 11.0, d=0.2)
        return out

    @staticmethod
    def _trident(kit, V, B, x, y):
        """A trident at the mouth, the citadel's blade in the middle: a broad lozenge blade tower
        (two fins a face, the Hand between them, silver edges, ember slits, a needle) to z 72.5 between two
        leaning horn blades on a stone saddle; the White Hand in a pointed-arch slot on its outer
        face (mirrored about the mouth's axis)."""
        from ..shapes_spire import BROAD
        L, W, h = 6.2, 4.2, 72.5
        out = kit.blade_tower((x, y), 90.0, L, W, 0.0, h, flare=1.2, fins=2, slits=(0.42, 0.54, 0.66), profile=BROAD,
                              fin_reach=1.3, slit_w=1.1)
        side = 1 if y > 0 else -1
        p, t, n = B.blade_face((x, y), 90.0, L, W, 0.0, h, (0.0, 0.0), 35.0, side)
        out += B.hand_slot(kit, p, t, n, 26.0, 3.8, 17.0)
        for e in (-1, 1):                                   # the horns, leaning out along the axis
            c = V((x, y + e * L * 1.9, 0))
            out += kit.blade_tower((c.x, c.y), 90.0, L * 0.55, W * 0.62, 0.0, h * 0.68, lean=(0.0, e * 2.4), flare=1.3,
                                   fins=1, spurs=False, slits=(0.5,), profile=BROAD, slit_w=0.8)
        from sagekit.blender.geometry import loft
        ring = lambda z: [V((x - W * 0.5, y - L * 1.9, z)), V((x + W * 0.5, y - L * 1.9, z)),    # noqa: E731
                          V((x + W * 0.5, y + L * 1.9, z)), V((x - W * 0.5, y + L * 1.9, z))]
        out.append(loft([ring(-0.3), ring(h * 0.16)], ["stoneA"], cap0=("stoneA", False), cap1=("trim", True)))
        for e in (-1, 1):                                   # fire grates in the saddle's front, either side of the blade
            out += kit.fire_grate(V((x + W * 0.5, y + e * L * 1.3, 0.0)), V((0, 1, 0)), V((1, 0, 0)), w=3.2, h=3.4, d=2.4)
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
