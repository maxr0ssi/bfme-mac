"""Elven wall hub (ElvenCastleWallHub; model EBWallRmprtN, drawn healthy as EBWallRmprtN_A): EA's
round tower where wall segments meet, kept whole - its six lancet windows with their lattice glass,
the pointed hoods with EA's gold leaf emblems, the ivy - and crowned as the citadel's ring is:

- the walls' band and silver coping round the rim (the segments' own, at the same heights, so the
  line runs on through the hub), without the segments' merlon cresting: the hub is no castle tower;
- EA's lattice dome crowned in gold: eight gilt ribs up its meridians to a gilt collar, a coronet
  of eight leaf blades and a tall leaf finial on the top;
- five crystal lanterns on silver posts on the rim (the citadel's ring lanterns).

No banners: hubs repeat along every wall.

EA's hub (EBWALLRMPRTN, mesh coordinates = model space): a 20-gon (corner radius 22.5..22.59,
corners every 18 degrees from the x axis) to z 49.1, piers to 22.27..22.59 between six lancet
windows (centred at 36, 90, 144, 216, 270, 324 degrees; recess backs at 19.43, faces about 21.69,
jambs to 30.81, apex 37.1 at the 20-gon's corner), a V cornice to r 24.09 between them, a sloped
rim to a walk at 51.45 (r 20.8) and a platform at 53.05 (r 11.2) carrying EA's dome (SPHERE01, its
own mesh on a bone at z 47.09: 16 meridians every 22.5 degrees from the x axis, rings (r, z) 20.65
51.06, 19.55 54.5, 14.96 61.4, 8.1 66.0, the pole at 67.6), which stays. Segments run in from any
side: nothing new passes the footprint (x +-24.09, y +-22.83); the crown's face line is the 20-gon
at RIM.

The pieces are static methods, reused by elves/fortress_wall_hub (EA's EBEFWHub: the same body).
"""
import math

from sagekit.building import Building

from ..style import ElvenStyle

RIM = 22.3                        # the crown's face line: a 20-gon of this corner radius
RIM_IN = -2.4                     # the coping and core reach in to r 19.9 (over the dome's foot)
LANTERN_ANGLES = (0, 72, 144, 216, 288)   # on the rim, between the merlons of a corner
LANTERN_R = RIM - 1.1                # on the coping's silver strip, in front of the dome's foot
# EA's dome: its meridians' (r, z) from the coping up (the first point interpolated at z 52.9, its
# foot buried in the coping's top) to where the gilt collar takes over
DOME = [(20.06, 52.9), (19.55, 54.5), (14.96, 61.4), (8.1, 66.0), (2.1, 67.18)]
DOME_Y = 0.01                        # the dome's axis (x 0)
RIBS = 8                             # gilt ribs on every other meridian (0, 45, ... degrees)
DOME_TOP = 67.6
EXPANSION = "ElvenCastleWallHubExpansion"   # the fortress's own hub: elves/fortress_wall_hub's


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
    house_tags = ()                 # no banners: hubs repeat along every wall
    # the gold crown stands on EA's dome (SPHERE01, to 67.6), which is not in the target (53.05 high):
    # 40 % of the target (as the Dwarven old castle hub) is 74.27, 10 % over the dome's pole
    max_z_growth = 0.40
    # Frame zero has already displaced the collapse pieces; their rest pose fits the intact body.
    lifecycle = {"EBWallRmprtN_D3": {"match": "rest"}}
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
        return self.crown(kit) + self.dome(kit) + self.lanterns(kit)

    @staticmethod
    def crown(kit):
        """The walls' band and silver coping round the rim (no merlons)."""
        from ..wall_segment.wall import crown, ring
        return crown(kit, ring(RIM), (0, 0), RIM_IN, inner="stoneB", parapet=False)

    @staticmethod
    def dome(kit):
        """EA's lattice dome crowned in gold: gilt ribs up the meridians, a gilt collar at the pole,
        a coronet of leaf blades round it and a leaf finial on top."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import loft

        from ..shapes import turned
        out = []
        for i in range(RIBS):
            ang = 2 * math.pi * i / RIBS
            c, s = math.cos(ang), math.sin(ang)
            rad, tan = V((c, s, 0)), V((-s, c, 0))
            rings = []
            for j, (r, z) in enumerate(DOME):
                (ra, za), (rb, zb) = DOME[max(j - 1, 0)], DOME[min(j + 1, len(DOME) - 1)]
                L = math.hypot(rb - ra, zb - za)
                nr, nz = (zb - za) / L, -(rb - ra) / L          # the meridian's outward normal
                nrm = rad * nr + V((0, 0, nz))
                half = 0.42 - 0.17 * j / (len(DOME) - 1)         # tapering to the pole
                p = V((c * r, DOME_Y + s * r, z))
                lo, hi = p - nrm * 0.15, p + nrm * 0.42
                rings.append([lo - tan * half, hi - tan * half, hi + tan * half, lo + tan * half])
            out.append(loft(rings, ["gilt"] * (len(DOME) - 1), cap0=("gilt", False), cap1=("gilt", False)))
        z = DOME_TOP
        out.append(turned(0, DOME_Y, [(2.7, z - 0.75), (3.0, z - 0.2), (2.9, z + 0.4), (1.9, z + 1.0), (1.0, z + 1.5)],
                          ["gilt"] * 4, 12, cap0=("gilt", False), cap1=("gilt", True)))
        for i in range(RIBS):                               # the coronet: a leaf between each pair of ribs
            ang = 2 * math.pi * (i + 0.5) / RIBS
            t, n = V((math.cos(ang), math.sin(ang), 0)), V((-math.sin(ang), math.cos(ang), 0))
            out.append(kit.leaf_blade(V((0, DOME_Y, 0)), t, n, 2.2, z + 0.1, 3.4, 1.3, lean=0.45, thick=0.14))
        return out + kit.leaf_finial(0, DOME_Y, z + 1.3, 5.2, 2.0)

    @staticmethod
    def lanterns(kit, angles=LANTERN_ANGLES):
        """Crystal lanterns on silver posts standing on the coping at the rim's corners."""
        from ..wall_segment.wall import COPING, lantern_post
        out = []
        for deg in angles:
            c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            out += lantern_post(kit, c * LANTERN_R, s * LANTERN_R, COPING[1], h=5.0, r=0.8, post=3.2)
        return out

    def emphasis(self, c, n):
        if c.z > 48:
            return 1.4                        # crown: what the RTS camera sees
        return 1.0
