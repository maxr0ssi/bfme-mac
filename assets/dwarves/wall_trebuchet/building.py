"""Dwarven wall trebuchet bastion (DwarvenWallCatapultSmall, model DBWallTrebN): the elongated
octagonal bastion a wall segment is upgraded to, carrying the Iron Hills trebuchet (a separate
object that stands on the round platform). EA's bastion keeps its carved panels, its triangle-frieze
band and the round platform; its rim gains the fortress's crown: chevron merlons (stepped-triangle
tops, a bronze step) along the four angled faces and the outer ends of the two wall faces, and a
stepped pyramid with a gilded point on each of the two prow tips; and Erebor-blue banners hang in
pairs on the four angled faces, under the band.

All numbers are DBWALLTREBN mesh coordinates measured on the original. Plan: the wall faces
y = +-22.5 (x +-22.5), angled faces from (+-22.5, +-22.5) to the prow tips (+-31.7, 0); rim coping at
z 53.1 flush with the faces; the platform (z 50.1) inside (+-27.6, 0), (+-20, +-18.7). The wall runs
along Y and meets the wall faces at x +-8.3 up to z 53: nothing is added there, and nothing enters
the platform, so the trebuchet keeps its floor and swing.
"""
from sagekit.building import Building

from ..style import DwarvenStyle

RIM = 53.1
CORNER, TIP = (22.5, 22.5), 31.7
MERLON_W, MERLON_S = 7.0, 0.85
ANGLED_U = (6.5, 14.5)          # merlon centres along an angled face, from its corner
PIER_X = 9.4                    # half width of the piers over the wall joins
WALL_FACE_X = 16.25             # merlon centre (|x|) on each wall face, clear of the join (x +-8.3)
BANNER_U, BANNER = 5.5, (43.0, 3.6, 19.0, 0.8)     # (z_top, width, length, d), pairs round the face middle


class WallTrebuchet(Building):
    style = DwarvenStyle()
    source = "DBWallTrebN"
    target = "DBWALLTREBN"
    own_textures = {"DBFortress1.tga": "DBFortressJ.tga"}
    bake_hidden = ("P1",)           # the flat platform card under the floor
    views = {
        "rts": ((0, 0, 30), 300, 50, -38, 50),
        "close": ((10, -6, 42), 150, 26, -30, 45),
        "ingame": ((0, 0, 28), 700, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from ..wall_tower.crown import chevron, step_pyramid
        s = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                a, t, n, flipped = self.angled(sx, sy)
                for u in ANGLED_U:
                    u = self.face_len() - u if flipped else u
                    s += chevron(a, t, n, u, RIM, MERLON_W, -2.4, 0.0, s=MERLON_S)
                for u in (-BANNER_U, BANNER_U):
                    z_top, width, length, d = BANNER
                    s += kit.banner(a, t, n, self.face_len() / 2 + u, z_top, width, length, d=d, free=True)
                s += chevron(V((0, sy * CORNER[1], 0)), V((1, 0, 0)), V((0, sy, 0)), sx * WALL_FACE_X, RIM,
                             MERLON_W, -2.4, 0.0, s=MERLON_S)
            s += step_pyramid(sx * (TIP - 2.3), 0.0, RIM, 0.5)
        for sy in (-1, 1):
            s += self._pier(sy)
        return s

    @staticmethod
    def _pier(sy):
        """Over each wall join (the wall face y = sy 22.5, the wall x +-8.3) a pier on the rim that
        receives the wall segment's parapet (coping to z 57, chevrons to 63.6): a block with the
        hexagon frieze, a bronze cornice, a stepped tier and a stone point, within the rim (y from
        19.0, the platform stops at 18.7) and the height limit (63.67)."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        a, t, n = V((0, sy * CORNER[1], 0)), V((sy, 0, 0)), V((0, sy, 0))
        d0 = -(CORNER[1] - 19.0)
        h, z = PIER_X, RIM
        out = [prism_uz(a, t, n, [(-h, z), (h, z), (h, z + 3.9), (-h, z + 3.9)], d0, 0.0,
                        [None, "stoneB", None, "stoneB"], "hex", "stoneA"),
               prism_uz(a, t, n, [(-h - 0.4, z + 3.9), (h + 0.4, z + 3.9), (h + 0.4, z + 4.5), (-h - 0.4, z + 4.5)], d0, 0.0,
                        ["trim", "trim", "top", "trim"], "trim", "trim"),
               prism_uz(a, t, n, [(-h + 1.8, z + 4.5), (h - 1.8, z + 4.5), (h - 1.8, z + 6.9), (-h + 1.8, z + 6.9)], d0 + 0.4, -0.3,
                        [None, "stoneB", "top", "stoneB"], "tri|a", "stoneA"),
               prism_uz(a, t, n, [(-h + 1.8, z + 6.9), (h - 1.8, z + 6.9), (0.0, z + 10.3)], d0 + 0.4, -0.3,
                        [None, "top", "top"], "stoneA", "stoneA")]
        return out

    @staticmethod
    def face_len():
        return ((TIP - CORNER[0]) ** 2 + CORNER[1] ** 2) ** 0.5

    @staticmethod
    def angled(sx, sy):
        """(anchor, along the face, outward normal, whether the anchor is the prow tip rather than
        the corner): t x n = -z, so a banner's front faces out."""
        from mathutils import Vector as V
        a = V((sx * CORNER[0], sy * CORNER[1], 0))
        t = (V((sx * TIP, 0, 0)) - a).normalized()
        n = V((t.y, -t.x, 0))
        if n.dot(a) < 0:
            n = -n
        if t.cross(n).z > 0:
            return V((sx * TIP, 0, 0)), -t, n, True
        return a, t, n, False

    def emphasis(self, c, n):
        return 1.4 if c.z > 40 else 1.0
