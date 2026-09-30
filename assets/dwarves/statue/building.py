"""The Dwarven statue (DwarvenStatue, dwarfstatue.ini): EA's king in armour on a plain grey block
raised onto a grand Erebor plinth - EA's octagonal base squared off by four corner buttresses
(plinth, bronze step, gold rune belt between bronze bands, corbel), a hexagon-chain cornice with a
bronze coping, four corner piers (the front two carrying gold braziers, the back two bronze banner
poles with gilded points flying Erebor-blue banners) and a rune-belted cornice with gold trim under
the statue's feet. The banner cloth leaves the body for DBHCStatue and takes the player's colour
in game.

EA's STATUEHOLDER (mesh coordinates = the model's, one bone, the statue faces +X) is an octagonal
block filling the footprint x -7.76..11.66, |y| <= 9.71 (corners chamfered 3.4) up to z 9.7 (with
gold rune plaques on its chamfers, 1 proud) and a cornice sloping in from there, then an octagonal
upper die x -4.81..8.71, |y| <= 6.76 (chamfer 2.7) from 11.8, a square cap 21.7..22.9 and a small
plate at 23.5 under the feet. Each face of the upper die holds a niche with a gold hexagon emblem
(z 13.6..19.9): they stay in view. The figure stands from z 23.3 (its cloak hem at 23.28 out to
|y| 8.3, x -5.44..6.14); its shield (SHIELD) hangs on the die's front x 8.71..9.42, |y| <= 6.9, z
11.9..26.9 - nothing new passes x 8.66 inside |y| 7.0 there. Footprint unchanged; the new piers
rise to z 31 (+31 %; the figure itself stands to 57.3, so the holder does not set the height)."""
from sagekit.building import Building

from ..style import DwarvenStyle

X0, X1, Y1 = -7.75, 11.65, 9.70              # just inside EA's footprint (-7.76..11.66, |y| <= 9.71)
FRONT_PIERS = ((9.25, 11.35), (7.25, 9.35))   # x range, |y| range
BACK_PIERS = ((-7.45, -5.15), (7.15, 9.45))
POLE_X, POLE_Y = -6.3, 8.3
BRAZIER_BED = 26.4                           # the front braziers' fire bed (the bowl's top)


def faces(tag, other):
    """Chamfered ring: the four faces (even sides) get `tag`, the chamfers `other`."""
    return [tag if k % 2 == 0 else other for k in range(8)]


def square(x0, x1, y0, y1, z, ch):
    from sagekit.blender.geometry import box_rings
    return box_rings((x0, x1), (y0, y1), z, ch)


def _fire_points():
    """The two front piers' brazier bowls, just above their fire beds (the gilded flame point stands
    inside the flame)."""
    (x0, x1), (a, b) = FRONT_PIERS
    return [(round((x0 + x1) / 2, 1), round(sy * (a + b) / 2, 1), round(BRAZIER_BED + 0.1, 1), "brazier")
            for sy in (1, -1)]


class Statue(Building):
    style = DwarvenStyle()
    source = "DBStatue"
    target = "STATUEHOLDER"
    sheet = "dbstatue.tga"                    # lower case, as the model names it (see README)
    sheet_normal = None                       # EA's statue sheet has no normal map
    own_textures = {"dbstatue.tga": "DBStatuH.tga"}
    fire_points = _fire_points()      # braziers on the front piers' bowls: (10.3, +-8.3, 26.5)
    tri_budget = 4000
    max_z_growth = 0.35
    views = {
        "rts": ((2, 0, 24), 200, 50, -38, 50),
        "close": ((3, 0, 20), 105, 22, -32, 45),
        "ingame": ((2, 0, 22), 520, 53, -62, 50),
        "side": ((2, 0, 12), 70, 10, -32, 45),
    }

    def design(self, kit):
        s = []
        s += self._base()                     # 1. corner buttresses, hexagon cornice, walk-top
        s += self._top_cornice()              # 2. the cornice under the statue's feet
        for sy in (1, -1):
            s += self._brazier_pier(sy)       # 3. front piers with gold braziers
            s += self._banner_pole(kit, sy)   # 4. back banner poles
        return s

    # ------------------------------------------------------------------ 1. base
    @staticmethod
    def _base():
        """EA's octagonal block fills the footprint up to 9.7 (its flat faces are the footprint's
        edges, so nothing can wrap them): a buttress fills each of its chamfered corners (burying
        EA's chamfer plaques) - plinth, bronze step, shaft with a gold rune belt between bronze
        bands, corbel - turning the block into a square with corner towers; over it a
        hexagon-chain cornice with a bronze coping and a walk-top sloping in over EA's cornice to
        the upper die. The buttresses carry the corner piers."""
        from sagekit.blender.geometry import loft
        out = []
        for (xa, xb), (ya, yb) in (((8.25, X1), (-Y1, -6.3)), ((8.25, X1), (6.3, Y1)),
                                   ((X0, -4.35), (-Y1, -6.3)), ((X0, -4.35), (6.3, Y1))):
            ox = 1 if xb == X1 else -1               # the corner's outward sides
            oy = 1 if yb == Y1 else -1

            def R(e, z):                             # inset e on the two outer sides only
                x0, x1 = (xa, xb - e) if ox > 0 else (xa + e, xb)
                y0, y1 = (ya, yb - e) if oy > 0 else (ya + e, yb)
                return square(x0, x1, y0, y1, z, 0.0)
            rings = [R(0.0, -0.1), R(0.0, 1.4), R(0.15, 1.4), R(0.15, 2.1), R(0.4, 2.1), R(0.4, 3.9),
                     R(0.25, 3.9), R(0.25, 4.4), R(0.3, 4.4), R(0.3, 6.8), R(0.25, 6.8), R(0.25, 7.3),
                     R(0.4, 7.3), R(0.4, 8.7), R(0.0, 9.65)]
            # box_rings sides: 0 y0, 1 +x, 2 y1, 3 -x; the two inner sides lie inside EA's block
            outer = {0 if oy < 0 else 2, 1 if ox > 0 else 3}

            def side(tag):
                return [tag if k in outer else None for k in range(4)]
            tags = [side("stoneB"), side("top"), side("trim"), side("top"), side("stoneA"), side("trim"),
                    side("trim"), side("trim"), side("rune"), side("trim"), side("trim"), side("trim"),
                    side("stoneA"), side("stoneB")]
            out.append(loft(rings, tags, cap0=("stoneB", False), cap1=("top", True)))

        def C(z):
            return square(X0, X1, -Y1, Y1, z, 0.6)
        rings = [C(9.55), C(10.4), C(10.95), square(-5.5, 9.4, -7.45, 7.45, 11.95, 1.9)]
        out.append(loft(rings, [faces("hex", "stoneB"), "trim", "top"], cap0=("stoneB", True), cap1=("top", True)))
        return out

    # ------------------------------------------------------------------ 2. top cornice
    @staticmethod
    def _top_cornice():
        """Round EA's square cap: a bronze corbel, a gold rune belt on the sides and back, a bronze
        coping with a walk-top under the cloak's hem (z 23.2 < 23.28). Its front stops at x 8.66,
        behind the face of EA's die: the shield hangs there."""
        from sagekit.blender.geometry import loft
        xf = 8.66
        rings = [square(-4.95, xf, -6.9, 6.9, 20.3, 0.5), square(-5.6, xf, -7.55, 7.55, 20.95, 0.5),
                 square(-5.6, xf, -7.55, 7.55, 22.4, 0.5), square(-6.0, xf, -7.95, 7.95, 22.4, 0.5),
                 square(-6.0, xf, -7.95, 7.95, 23.2, 0.5)]
        # chamfered ring sides from y0: 0 -y, 2 +x (front, behind the shield), 4 +y, 6 -x
        belt = ["rune", "trim", "trim", "trim", "rune", "trim", "rune", "trim"]
        return [loft(rings, ["stoneB", belt, "trim", "trim"], cap0=("stoneB", False), cap1=("top", True))]

    # ------------------------------------------------------------------ 3. braziers
    @staticmethod
    def _brazier_pier(sy):
        """A front corner pier on the cornice: shaft, rune belt, bronze capital, a gold brazier bowl
        and a gilded flame point. Clear of the shield (|y| >= 7.25 > 6.9)."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        (x0, x1), (a, b) = FRONT_PIERS
        y0, y1 = sorted((sy * a, sy * b))

        def R(e, z, ch=0.3):
            return square(x0 - e, x1 + e, y0 - e, y1 + e, z, ch)
        rings = [R(0.0, 10.3), R(0.0, 18.6), R(0.25, 18.6), R(0.25, 19.1), R(0.1, 19.1), R(0.1, 21.2),
                 R(0.25, 21.2), R(0.25, 21.7), R(0.0, 21.7), R(0.0, 23.4), R(0.3, 23.4), R(0.3, 24.2),
                 R(-0.3, 24.2)]
        tags = ["stoneA", "trim", "trim", "top", "rune", "trim", "trim", "top", "stoneA", "trim", "trim", "top"]
        out = [loft(rings, tags, cap0=("stoneB", False), cap1=("top", True))]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        bowl = [square(cx - 0.7, cx + 0.7, cy - 0.7, cy + 0.7, 24.2, 0.2),
                square(cx - 1.25, cx + 1.25, cy - 1.25, cy + 1.25, 26.0, 0.35),
                square(cx - 1.25, cx + 1.25, cy - 1.25, cy + 1.25, BRAZIER_BED, 0.35)]
        out.append(loft(bowl, ["trim", "trim"], cap0=("trim", False), cap1=("trim", True)))
        top = square(cx - 0.95, cx + 0.95, cy - 0.95, cy + 0.95, BRAZIER_BED, 0.25)
        out.append(loft([top, [V((cx, cy, 28.6))] * len(top)], ["trim"], cap0=("trim", False), cap1=("trim", False)))
        return out

    # ------------------------------------------------------------------ 4. banner poles
    @staticmethod
    def _banner_pole(kit, sy):
        """A back corner pier becoming a bronze banner pole with a gilded point; its banner hangs
        from an arm beside the die's flank (in the plane |y| ~8.7, x -5.15..-1.65), clear of the
        flank's hexagon niche (x >= -1.3) and of the cloak (|y| <= 8.3)."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        (x0, x1), (a, b) = BACK_PIERS
        y0, y1 = sorted((sy * a, sy * b))

        def R(e, z, ch=0.3):
            return square(x0 - e, x1 + e, y0 - e, y1 + e, z, ch)
        rings = [R(0.0, 10.3), R(0.0, 17.2), R(0.25, 17.2), R(0.25, 17.7), R(0.1, 17.7), R(0.1, 19.8),
                 R(0.25, 19.8), R(0.25, 20.4), R(-0.3, 20.4)]
        out = [loft(rings, ["stoneA", "trim", "trim", "top", "rune", "trim", "trim", "top"],
                    cap0=("stoneB", False), cap1=("top", True))]
        px, py = POLE_X, sy * POLE_Y
        pole = [square(px - 0.45, px + 0.45, py - 0.45, py + 0.45, z, 0.1) for z in (20.4, 28.4)]
        out.append(loft(pole, ["trim"], cap0=("trim", False), cap1=("trim", True)))
        top = square(px - 0.8, px + 0.8, py - 0.8, py + 0.8, 28.4, 0.2)
        out.append(loft([top, [V((px, py, 30.8))] * len(top)], ["trim"], cap0=("trim", False), cap1=("trim", False)))
        # the banner: t x n = -z, n outward (away from the die)
        t, n = V((-sy * 1.0, 0, 0)), V((0, sy * 1.0, 0))
        anchor = V((0, py, 0))
        out += kit.banner(anchor, t, n, sy * 3.4, 26.6, 3.0, 12.0, d=0.35, free=True)
        return out

    def emphasis(self, c, n):
        return 1.3 if c.z > 8.5 else 1.0
