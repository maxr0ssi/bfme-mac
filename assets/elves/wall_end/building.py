"""Elven wall end (ElvenWallCliffCap, model EBWallNE): the piece a wall run ends in where it meets a
cliff. EA's model is two wall segments end to end (four lancet bays), its faces carried on below
the ground to z -51.2 for the falling ground at the cliff's foot, the far end cut plain.

The walls' crown runs its whole length (filigree band, silver coping, lancet merlons: the shared
profile, wall_segment/wall.py), so the joint with the next segment is exact; the four windows per
face take the segments' silver arch frames and leaf banners in the player's colour; the cut end
gets a slender Elven turret on the crown: a pale stone lantern-house with a lancet window on each
open face, under a swept slate roof with upturned eaves and a gilt leaf finial - the end of the
wall seen from the field.

EBWALLN hangs under a bone turned 180 degrees about z (model = (-x, -y, z) of the mesh): the design
is in mesh coordinates, where z is still up (world_space is not needed). In them: y -19..57, the
joint with a segment at y = -19 (the segment's end, a half pier), the cut end at y = 57; the wall
face |x| 3.06, piers |x| 4.9 (the footprint) at y 0, 38 and the ends; windows at y -9.73, 9.73,
28.27, 47.73; the V cornice and pointed hoods to the top edge 49.1 and the ridge 51.2 as on the
segment. Below z 0 all is EA's (underground)."""
from sagekit.building import Building

from ..style import ElvenStyle

JOINT_Y, END_Y = -19.0, 57.0
WINDOWS = (-9.73, 9.73, 28.27, 47.73)
# the turret at the cut end: body (half x, y0, y1 (0.3 short of the cut), z0, eaves), roof
TURRET = (4.2, 48.4, 56.7, 52.9, 58.6)
ROOF = (4.45, 8.2, 1.1)            # half size at the eaves (corners <= the footprint), rise, upturn
MERLON_END = TURRET[1] + 0.3       # the merlons run from the joint into the turret's side


class WallEnd(Building):
    style = ElvenStyle()
    source = "EBWallNE"
    target = "EBWALLN"
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresE.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallEnd"
    views = {                                                # model space: the cut end at y = -57
        "rts": ((0, -19, 30), 230, 48, -24, 50),
        "close": ((0, -19, 34), 150, 20, -18, 45),
        "end": ((0, -50, 50), 70, 26, -62, 45),
        "ingame": ((0, -19, 26), 520, 53, -62, 50),
    }

    def design(self, kit):
        from ..wall_segment.wall import segment_windows
        return self._crown(kit) + segment_windows(kit, WINDOWS) + self._turret(kit)

    @staticmethod
    def _crown(kit):
        from mathutils import Vector as V

        from ..wall_segment.wall import FACE_X, crown, merlons
        out = []
        for s in (1, -1):
            path = [(s * FACE_X, JOINT_Y), (s * FACE_X, END_Y - 0.1)]
            out += crown(kit, path, (0, 19), -FACE_X, inner=None, parapet=False)
            out += merlons(kit, V((s * FACE_X, JOINT_Y)), V((0, 1)), V((s, 0)), MERLON_END - JOINT_Y)
        return out

    @staticmethod
    def _turret(kit):
        import math

        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz

        from ..wall_segment.wall import box
        hx, y0, y1, z0, z1 = TURRET
        out = [box(-hx, hx, y0, y1, z0, z1, ["stoneA", "stoneA", "stoneA", "stoneA"], bottom=("stoneB", False),
                   top=("top", False))]
        # a string course under the eaves
        out.append(box(-hx - 0.25, hx + 0.25, y0 - 0.25, y1 + 0.25, z1 - 1.0, z1 - 0.4, "trim", bottom=("trim", True),
                       top=("top", True)))
        # a lancet window (EA's lattice glass) in an arch frame on the two faces and the end
        cy = (y0 + y1) / 2
        faces = [(V((hx, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), cy), (V((-hx, 0, 0)), V((0, -1, 0)), V((-1, 0, 0)), -cy),
                 (V((0, y1, 0)), V((-1, 0, 0)), V((0, 1, 0)), 0.0)]
        for a, t, n, u in faces:
            glass = kit.arch_outline(1.1, 54.9, 56.7, 0.25, 5)
            poly = [(u - 1.1, 53.4), (u + 1.1, 53.4)] + [(u + x, z) for x, z in glass[:-1]] + \
                   [(u - x, z) for x, z in reversed(glass)]
            out.append(prism_uz(a, t, n, poly, -0.2, 0.05, [None] * len(poly), "window", None))
            out += kit.arch(a, t, n, u, 1.1, 53.4, 54.9, 56.7, w=0.45, d0=0.0, d1=0.3, ogee=0.25, finial=False)
        half, rise, up = ROOF
        out += kit.swept_roof(0.0, cy, half * math.sqrt(2), z1, rise, k=4, per_side=4, upturn=up, phase=math.pi / 4)
        return out

    def emphasis(self, c, n):
        if c.z > 48:
            return 1.4                        # crown and turret: what the RTS camera sees
        return 1.0
