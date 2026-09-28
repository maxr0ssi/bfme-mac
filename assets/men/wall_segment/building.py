"""Men wall segment (MenWallSegmentSmall, MenWallPosternGateSmall, and Arnor's; model GBWallN):
EA's ashlar curtain kept whole - its end piers, the painted corbel arcade under the cornice, the
paved walk - and given the citadel's machicolated crown and a Gondor face (wall.py, the shared
profile every wall piece imports):

- two-step corbels on EA's cornice carrying a machicolation slab whose front is a black enamel
  band of silver stars, a breastwork with a coping course and square merlons with capstones in
  an even rhythm that runs on into the neighbours (half a gap at each end);
- in the middle of each face a pilaster from a battered base to the slab, a steel-framed shield
  with the White Tree on it, and a pinnacle with a steel spike over it on the breastwork;
- two arrow slits a face in stone surrounds with lintels and sills, a moulded string course at
  EA's course line (24) and a battered foot with a course, between EA's piers.

No banners: segments repeat many times along a wall (the gate carries the run's two).

The segment tiles (7.45 x 38, 49.5 high): its ends (y = +-19) meet the next segment, a hub, the
gate, a stub or a wall end, and the engine may stretch it along y. Only the crown reaches the ends
(its runs continue into the neighbour's); everything stays inside EA's footprint (x +-7.45: the
piers' fronts). Both faces are the same (either may face the enemy). GBWallN's mesh BOX01 stands
on an identity bone: mesh coordinates are model coordinates.
"""
from sagekit.building import Building

from ..style import MenStyle


class Degenerate:
    """A clear spec (sagekit/clear.py) for EA's zero-area triangles: GBWallN carries three, all
    three corners on one point (0, 0, 0) or (0, 0, 49.5); the checks want none in our target."""

    def select(self, faces):
        out = set()
        for f, p in enumerate(faces.polys):
            a, b, c = (faces.verts[i] for i in p[:3])
            u, v = [b[k] - a[k] for k in range(3)], [c[k] - a[k] for k in range(3)]
            cr = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            if len(p) == 3 and sum(x * x for x in cr) < 4e-12:
                out.add(f)
        return out


HALF = 19.0                        # the segment's half length (its ends meet the neighbours)


class WallSegment(Building):
    style = MenStyle()
    source = "GBWallN"
    target = "BOX01"
    sheet = "GBWall.tga"
    sheet_normal = "GBWall_NRM.tga"
    own_textures = {"GBWall.tga": "GBWalH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallSegment"
    house_tags = ()                 # no banners: segments repeat many times along a wall
    # the placement cursor: EA's segment on the same bone and box (checked by the derive step)
    also_derived = ("GBWallN_CUR",)
    clear = [Degenerate()]          # EA's three zero-area triangles (nothing visible)
    views = {
        "rts": ((0.0, 0.0, 24.7), 141, 50, -38, 50),
        "close": ((0.0, 0.0, 36.0), 88, 24, -30, 45),
        "ingame": ((0.0, 0.0, 24.7), 321, 53, -62, 50),
    }

    def is_body(self, draw):
        """Not the wall end's (MenWallCliffCap, ArnorWallCliffCap): its Draw shows our GBWallN_D3 for
        its collapse, but its own models are men/wall_end's."""
        return "cliffcap" not in draw.object.lower() and super().is_body(draw)

    def design(self, kit):
        from mathutils import Vector as V

        from .wall import PIER_W, pier_cap, straight
        out = straight(kit, -HALF, HALF, [(-HALF + PIER_W, HALF - PIER_W)])
        for s in (1, -1):                       # caps on the half piers at both ends
            for u0, u1 in ((-HALF, -HALF + PIER_W + 0.2), (HALF - PIER_W - 0.2, HALF)):
                out += pier_cap(V((0, 0, 0)), V((0, 1, 0)), V((s, 0, 0)), u0, u1)
        return out

    def decals(self):
        from ..paint import men_layers
        from .wall import STAR_BAND
        from .paintwall import wall_layers
        return [men_layers()[2](zrange=STAR_BAND, pitch=3.0, r=0.8),     # silver stars on the slab's band
                wall_layers()()]                                          # EA's joints crisp on the white stone

    def emphasis(self, c, n):
        if c.z > 42:
            return 1.35                       # the crown: what the RTS camera sees
        return 1.0
