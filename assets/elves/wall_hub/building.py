"""Elven wall hub (ElvenCastleWallHub; model EBWallRmprtN, drawn healthy as EBWallRmprtN_A): EA's
round tower where wall segments meet, given the walls' crown and the Elven windows: a filigree band,
a silver coping and lancet merlons round the rim (the segments' own, at the same heights, so the
parapet line runs on through the hub), silver arch frames with sea-green reveals round its six
lancet windows, a leaf banner in the player's colour in each, and five crystal lanterns on the rim.

EA's hub (EBWALLRMPRTN, mesh coordinates = model space): a 20-gon (corner radius 22.5..22.59,
corners every 18 degrees from the x axis) to z 49.1, piers to 22.27..22.59 between six lancet
windows (centred at 36, 90, 144, 216, 270, 324 degrees; recess backs at 19.43, faces about 21.69,
jambs to 30.81, apex 37.1 at the 20-gon's corner), a V cornice to r 24.09 between them, a sloped
rim to a walk at 51.45 (r 20.8) and a platform at 53.05 (r 11.2) carrying EA's dome (SPHERE01, its
own mesh: r 20.65, z 51.06..67.6), which stays. Segments run in from any side: nothing new passes
the footprint (x +-24.09, y +-22.83); the crown's face line is the 20-gon at RIM.

The pieces are static methods, reused by elves/fortress_wall_hub (EA's EBEFWHub: the same body).
"""
import math

from sagekit.building import Building

from ..style import ElvenStyle

RIM = 22.3                        # the crown's face line: a 20-gon of this corner radius
RIM_IN = -2.4                     # the coping and core reach in to r 19.9 (over the dome's foot)
WINDOW_ANGLES = (36, 90, 144, 216, 270, 324)
WIN_BACK, WIN_FACE = 19.43, 21.69     # recess back, face-frame plane (distance from the axis)
LANTERN_ANGLES = (0, 72, 144, 216, 288)   # on the rim, between the merlons of a corner
LANTERN_R = RIM - 2.1                # inside the merlons, at the dome's foot
EXPANSION = "ElvenCastleWallHubExpansion"   # the fortress's own hub: elves/fortress_wall_hub's


def _frame(deg, dist):
    """(a, t, n) of a vertical plane facing out at angle deg, `dist` from the axis (t x n = -z)."""
    from mathutils import Vector as V
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    n = V((c, s, 0))
    return V((c * dist, s * dist, 0)), V((-s, c, 0)), n


class WallHub(Building):
    style = ElvenStyle()
    # EA's healthy state draws EBWallRmprtN_A, the construction model, at rest; its file carries
    # the construction animation, whose first frame Blender imports (the body 70 below ground).
    # EBWallRmprtN is the same body, static: the source, and _A takes ours by derive.
    source = "EBWallRmprtN"
    target = "EBWALLRMPRTN"
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresC.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallHub"
    views = {
        "rts": ((0, 0, 30), 190, 48, -24, 50),
        "close": ((0, 0, 36), 120, 20, -18, 45),
        "ingame": ((0, 0, 26), 430, 53, -62, 50),
    }

    def is_body(self, draw):
        """Not the fortress's hub expansion: its construction state shows our EBWallRmprtN_A (as
        derived here), but its own models, cloth and lifecycle are elves/fortress_wall_hub's."""
        return draw.object != EXPANSION and super().is_body(draw)

    def design(self, kit):
        return self.crown(kit) + self.windows(kit) + self.lanterns(kit)

    @staticmethod
    def crown(kit):
        """The walls' crown round the rim (band, coping, lancet merlons)."""
        from ..wall_segment.wall import crown, ring
        return crown(kit, ring(RIM), (0, 0), RIM_IN, inner="stoneB")

    @staticmethod
    def windows(kit, angles=WINDOW_ANGLES):
        """Arch frames and leaf banners in EA's lancet windows."""
        from ..wall_segment.wall import window_arch, window_banner
        out = []
        for deg in angles:
            a, t, n = _frame(deg, WIN_FACE)
            out += window_arch(kit, a, t, n, 0.0, finial=False, d0=-0.6, d1=0.95)   # back buried where the 20-gon bends
            a, t, n = _frame(deg, WIN_BACK)
            out += window_banner(kit, a, t, n, 0.0)
        return out

    @staticmethod
    def lanterns(kit, angles=LANTERN_ANGLES):
        """Crystal lanterns standing on the coping at the rim's corners."""
        from ..wall_segment.wall import COPING, lantern_post
        out = []
        for deg in angles:
            c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            out += lantern_post(kit, c * LANTERN_R, s * LANTERN_R, COPING[1], r=0.7)
        return out

    def emphasis(self, c, n):
        if c.z > 48:
            return 1.4                        # crown: what the RTS camera sees
        return 1.0
