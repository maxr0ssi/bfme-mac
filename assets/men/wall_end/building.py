"""Men wall end (MenWallCliffCap, and Arnor's; model GBWallNE): the piece a wall run ends in where it
meets a cliff. EA's model is two wall segments end to end (y -19..57), a full pier where they
meet (y 16.91..21.09), the half pier of the joint at y -19, the far end cut plain, the faces
carried on below the ground to z -46.13 for the falling ground at the cliff's foot.

EA's body is kept whole. Both faces take the walls' shared profile (men/wall_segment/wall.py),
so the joint with the next segment is exact: the machicolated crown with its black band of
silver stars and merlons in the same rhythm, a pilaster with the White Tree shield and a
pinnacle in the middle of each bay, arrow slits, the string course, caps on the piers. No
battered foot: the faces run on down the cliff. The cut end gets a Gondor end turret standing on
the wall top: a chamfered-square tower corbelled out over the wall's faces, its own machicolated
gallery with merlons (men/wall_hub/dome.py, the citadel's), a steel-ribbed slate dome with a
steel eave band, a gilt orb and a spike - the end of the wall seen from the field. No banners
(the wall run's two hang on the gate).

GBWALLNE hangs under a bone turned 180 degrees about z (model = (-x, -y, z) of the mesh); the
design is in mesh coordinates, where z is still up. Height: EA's -46.13..49.5 (95.6) may grow to
114.8 (the turret's spike reaches 68.4: +19.7 %).
"""
from sagekit.building import Building

from ..style import MenStyle

JOINT_Y, END_Y = -19.0, 57.0
PIER = (16.91, 21.09)              # EA's full pier where its two segments meet
TURRET_Y, TURRET_HALF = 49.55, 6.05   # the end turret's centre (y) and half width (over EA's cornice, 5.98)
TURRET_FOOT = 40.4                 # the corbel course under it (from the wall's face out to the shaft)
GALLERY = (50.2, 1.3)              # corbel foot, slab out of the shaft (front at 7.35: the footprint is 7.45)
DOME = [(57.0, 4.9), (60.4, 3.9), (63.0, 2.3), (64.3, 1.0)]
FINIAL = (65.9, 68.3)


class WallEnd(Building):
    style = MenStyle()
    source = "GBWallNE"
    target = "GBWALLNE"
    sheet = "GBWall.tga"
    sheet_normal = "GBWall_NRM.tga"
    own_textures = {"GBWall.tga": "GBWalX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallEnd"
    house_tags = ()                 # no banners on the wall pieces but the gate
    # its collapse is the segment's GBWallN_D3 (EA shares it): men/wall_segment ships that one
    lifecycle = {"GBWallN_D3": {"skip": "the segment's collapse model: men/wall_segment ships it"}}
    views = {                                                # model space: the cut end at y = -57
        "rts": ((0.0, -19.0, 20.0), 250, 50, -38, 50),
        "close": ((0.0, -30.0, 38.0), 150, 24, -30, 45),
        "end": ((0.0, -50.0, 52.0), 70, 26, -62, 45),
        "ingame": ((0.0, -19.0, 1.7), 615, 53, -62, 50),
    }

    def design(self, kit):
        return self._faces(kit) + self._turret(kit)

    @staticmethod
    def _faces(kit):
        from mathutils import Vector as V

        from ..wall_segment.wall import PIER_W, pier_cap, straight
        ya = TURRET_Y - TURRET_HALF                       # the crown runs into the turret's side
        bays = [(JOINT_Y + PIER_W, PIER[0]), (PIER[1], END_Y)]
        out = straight(kit, JOINT_Y, ya + 0.6, bays, pilasters=(0.0, 36.0), slits=(-8.5, 8.5, 28.5, 44.0),
                       with_foot=False, crown_run=(JOINT_Y, ya + 0.6))
        a, t = V((0, 0, 0)), V((0, 1, 0))
        for s in (1, -1):
            for u0, u1 in ((JOINT_Y, JOINT_Y + PIER_W + 0.2), (PIER[0] - 0.2, PIER[1] + 0.2)):
                out += pier_cap(a, t, V((s, 0, 0)), u0, u1)
        return out

    @staticmethod
    def _turret(kit):
        from ..wall_hub import dome as D
        from ..wall_segment.wall import FACE
        sec = D.Section(0.0, TURRET_Y, chamfer=0.28)
        h = TURRET_HALF
        zc, out_ = GALLERY
        zs, zw = zc + 3.6, zc + 6.1
        res = D.drum(sec, h, TURRET_FOOT + 1.2, zw - 0.5, "stoneA")
        # the corbel course from the wall's face out to the shaft
        res += D.moulding(sec, h, TURRET_FOOT, [(FACE - h - 0.05, 0.0), (0.0, 1.25), (0.0, 1.4)],
                          ["course", "stoneB"], inner=FACE - h - 0.4)
        res += D.gallery(kit, sec, h, zc, zs, zw, out=out_, merlon=dict(w=2.0, gap=1.5, h=2.6))
        res += D.window_frames(kit, sec, h, 43.4, 49.2, 0.9, faces=(2, 4, 6), d=(0.0, 0.55), rim=0.45)
        res += D.dome(sec, DOME, tag="slate", point=None)
        res += D.crown(kit, sec, (DOME[0][1] + 0.3, DOME[0][0] + 0.3), DOME, finial=FINIAL, rib=(0.26, 0.16))
        return res

    def decals(self):
        from ..paint import men_layers
        from ..wall_segment.wall import STAR_BAND
        Star = men_layers()[2]
        from ..wall_segment.paintwall import wall_layers
        return [Star(zrange=STAR_BAND, pitch=3.0, r=0.8), Star(zrange=(GALLERY[0] + 3.7, GALLERY[0] + 6.0), pitch=2.9, r=0.75),
                wall_layers()()]

    def emphasis(self, c, n):
        if c.z > 40:
            return 1.35                       # crown and turret: what the RTS camera sees
        return 1.0
