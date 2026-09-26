"""Dwarven wall tower (DwarvenWallTowerSmall, model DBWallTwrN): the axe tower that stands on a
wall segment. EA's tower keeps its shaft (carved window panels, V-shaped corbel under the head)
and its head of bronze shield panels with the archer notches; the head gains the fortress's tower
crown (a battered crown ring, stepped pyramids on the corner posts, a chevron merlon mid-side) and a stepped
rune roof with a gilded point over EA's stone pyramid; the shaft a rune belt at the walkway, long
Erebor-blue banners either side of the carved window on the two faces that look out of the wall,
and a battered plinth with a string course on those faces.

All numbers are DBWALLTWRN mesh coordinates measured on the original. The wall runs along Y: the
model's own EA wall piece DBWALLN (x +-8.3, y +-19, top 53; not redesigned, the recoloured EA
sheet) passes through the tower, so nothing is added on the +-Y faces below z 53.
"""
from sagekit.building import Building

from ..style import DwarvenStyle

SHAFT = 11.2            # shaft half width (square), z 49.2 .. 75.2; the lower tower's +-X faces too
STUB_END = 18.0         # this mesh's footprint in y (the EA wall piece runs on to 19)
HEAD_TOP = 102.4        # tops of the bronze shield panels (outer face +-15.0, inner +-10.8)
POST = 12.15            # corner posts (+-10.8 .. +-13.5) rise to 110.5
# EA's stone pyramid roof: +-10.8 at z 99.5 to +-6.5 at 117.5 (a square hole at the top)
CROWN_PATH = 12.65      # crown ring centre line: the ring reaches 2.3 out, to +-14.95
DZ = HEAD_TOP - 110.8   # the fortress's crown numbers lowered onto the head
CROWN_TOP = 117.4 + DZ  # the crown ring's top (109.0)
CROWN = [(-2.9, 110.8), (2.3, 110.8), (1.6, 114.8), (1.6, 115.3), (0.6, 115.3), (0.2, 117.4), (-0.6, 117.4),
         (-1.6, 116.2), (-2.9, 116.2)]
CROWN_TAGS = [None, "stoneB", "trim", "top", "stoneA", "top", "top", "top", "stoneA"]
# roof tiers (half0, half1, height, tag) from z 106.0, each clear of EA's pyramid under it
ROOF = [(9.2, 9.0, 3.8, "rune"), (9.4, 9.4, 0.6, "trim"), (8.3, 8.1, 4.0, "tri"), (8.4, 8.4, 0.6, "trim"),
        (7.2, 7.0, 3.4, "stoneA")]
# banners on the +-X faces either side of the carved window (y +-5.6): hung free 1.2 out, rods under
# the head's V-shaped corbel (z 76.3 at the middle rising to 84.4 at the corners)
BANNER_U, BANNER = 8.4, (78.8, 4.2, 22.0, 1.2)     # (z_top, width, length, d)


class WallTower(Building):
    style = DwarvenStyle()
    source = "DBWallTwrN"
    target = "DBWALLTWRN"
    own_textures = {"DBFortress1.tga": "DBFortressV.tga"}
    views = {
        "rts": ((0, 0, 62), 330, 50, -38, 50),
        "close": ((0, 0, 96), 120, 26, -32, 45),
        "ingame": ((0, 0, 60), 700, 53, -62, 50),
    }

    def design(self, kit):
        from sagekit.blender.geometry import box_rings, loft, sweep

        from .crown import chevron, step_pyramid, ziggurat
        s = []
        h = CROWN_PATH                                                   # 1. crown ring
        path = [(-h, -h), (h, -h), (h, h), (-h, h), (-h, -h)]
        ring, segs = sweep(path, [(d, z + DZ) for d, z in CROWN], CROWN_TAGS, center=(0, 0))
        s += ring
        for a, b, t, n in segs:                                          # 2. a chevron mid-side
            s += chevron(a, t, n, (b - a).length / 2, CROWN_TOP - 0.4, 10.0, -1.8, 0.6)
        for sx in (-1, 1):                                               # 3. corner-post pyramids
            for sy in (-1, 1):
                s += step_pyramid(sx * POST, sy * POST, 107.5, 0.7)
        roof, _ = ziggurat(0, 0, 106.0, ROOF, (5.0, 6.0))                # 4. stepped rune roof
        s += roof
        belt = [box_rings((-12.0, 12.0), (-12.0, 12.0), z, 0.8) for z in (49.4, 50.2, 52.6, 53.4)]
        s.append(loft(belt, ["trim", ["rune" if k % 2 == 0 else "stoneB" for k in range(8)], "trim"],
                      cap0=("top", False), cap1=("top", True)))          # 5. rune belt at the walkway
        for sx in (-1, 1):                                               # 6. battered plinths
            s += kit.talus([(sx * SHAFT, -SHAFT), (sx * SHAFT, SHAFT)])
        s += self._banners(kit)                                          # 7. banners
        s += self._wall_stubs(kit)                                       # 8. the walls' parapet
        return s

    @staticmethod
    def _wall_stubs(kit):
        """The model's own EA wall piece (DBWALLN, not redesigned) shows between the shaft (|y| 11.2)
        and the neighbouring segments (|y| 19): the wall segment's coping and chevron parapet
        (wall_segment's profile, imported so the two stay one design) run along it on both faces,
        out to this mesh's footprint (|y| 18.03). Their undersides lie in the EA piece, a mesh the
        sky check cannot see, so they are closed."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import sweep

        from ..wall_segment.building import COPING, COPING_TAGS, COPING_X
        tags = [t if t is not None else "stoneB" for t in COPING_TAGS]
        out = []
        for sx in (-1, 1):
            for y0, y1 in ((SHAFT - 0.4, STUB_END), (-STUB_END, -SHAFT + 0.4)):
                out += sweep([(sx * COPING_X, y0), (sx * COPING_X, y1)], COPING, tags)[0]
                out += kit.chevron_parapet(V((sx * COPING_X, y0, 0)), V((0, 1, 0)), V((sx, 0, 0)), y1 - y0)
        return out

    @staticmethod
    def _banners(kit):
        from mathutils import Vector as V
        z_top, width, length, d = BANNER
        s = []
        for a, t, n in ((V((SHAFT, 0, 0)), V((0, 1, 0)), V((1, 0, 0))), (V((-SHAFT, 0, 0)), V((0, -1, 0)), V((-1, 0, 0)))):
            for u in (-BANNER_U, BANNER_U):
                s += kit.banner(a, t, n, u, z_top, width, length, d=d, free=True)
        return s

    def emphasis(self, c, n):
        if c.z > 98:
            return 1.5                        # the crown and roof: what the RTS camera sees
        return 1.2 if c.z > 45 else 1.0
