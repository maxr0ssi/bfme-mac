"""Dwarven castle-wall tower (DwarvenCastleWallTower): the old castle wall's tower upgrade as a
two-stage Dwarven tower. EA's object draws Gondor's placeholder GBWallTwr (a cylinder labelled
"tower" on a wall section), which Men and Arnor draw too, so ours ships as a model of its own,
DBWallTwr2 (sagekit/owncopy.py; EA's unused DBWallTwr is filed in BFME2's cache).

The old castle wall's section (oldwall_segment/upgrade.py) runs along |y| <= 99.5 with a Dwarven
stair down EA's ramp at each end. In the middle the trebuchet platform's bastion (x +-38.02, rim to
42.35, platform 53.59) carries an upper tower x +-24, y +-17 in the same profile one storey up: a
rune belt on the platform, banners on its two outer faces, corbels under a rune band, the drip band
and coping (top 95.09), chevrons all round, stepped pyramids on its corners and a stepped rune roof
with a gilded point in the middle of its fighting platform (z 90).

EA's arrow bones ARROW_01..12 (z 95.5, a square +-11.2) stand on that platform: inside the
parapet, clear of the roof (half 9.4). EA's GBWALLUPGRD (the section) and CYLINDER01 (the label
cylinder, r 25 to z 100) are taken over by our target GBWALLGATE and dropped from our copy; their
volume bounds the redesign (height limit 100.09 x 1.2). All numbers are model coordinates."""
from sagekit.building import Building

from ..style import DwarvenStyle

HY = 24.0                         # the bastion (as the trebuchet platform's)
TX, TY = 24.0, 17.0               # the upper tower's faces
TOP = 90.0                        # its fighting platform (EA's arrow bones at 95.5)
# roof tiers (half0, half1, height, tag) from TOP, then a gilded point (wall_tower's crown roof)
ROOF = [(9.2, 9.0, 3.8, "rune"), (9.4, 9.4, 0.6, "trim"), (8.3, 8.1, 4.0, "tri"), (8.4, 8.4, 0.6, "trim"),
        (7.2, 7.0, 3.4, "stoneA")]
BANNER = (7.5, 5.0, 22.0)         # (|y|, width, length) on the upper tower's +-X faces


class OldWallTower(Building):
    style = DwarvenStyle()
    source = "GBWallTwr"
    own_model = "DBWallTwr2"
    replaces = ("GBWALLUPGRD", "CYLINDER01")
    target = "GBWALLGATE"
    sheet = "GBWall.tga"                                # Gondor's placeholder; no face samples it
    sheet_normal = None
    own_textures = {"GBWall.tga": "DBWalT.tga"}
    bake_hidden = ("P1", "R1", "R2")
    tri_budget = 14000
    views = {
        "rts": ((0, 0, 45), 500, 48, -38, 50),
        "close": ((0, 0, 70), 240, 22, -28, 45),
        "ingame": ((0, 0, 45), 1000, 53, -62, 50),
    }

    def design(self, kit):
        from ..oldwall_segment.upgrade import UP_WALK, bastion, flanks
        from ..oldwall_segment.wall import clear_target
        clear_target(self.target)
        return bastion(kit, HY, banners=False) + flanks(kit, HY) + self._upper(kit, UP_WALK)

    @staticmethod
    def _upper(kit, walk):
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft

        from ..oldwall_segment.upgrade import bays, corbels, upper_rings
        from ..wall_tower.crown import step_pyramid, ziggurat
        rings, tags = upper_rings(TX, TY, walk - 0.5, TOP)
        out = [loft(rings, tags, cap0=("stoneB", False), cap1=("top", True))]
        belt = [box_rings((-TX - d, TX + d), (-TY - d, TY + d), z, 0)
                for d, z in ((0.0, walk), (0.8, walk), (0.8, walk + 0.8), (0.6, walk + 0.8), (0.6, walk + 4.8),
                             (0.8, walk + 4.8), (0.8, walk + 5.6), (0.0, walk + 5.6))]
        out.append(loft(belt, [None, "trim", "top", "rune", "stoneB", "trim", "top"], cap0=("top", False),
                        cap1=("top", False)))
        dz, bz = TOP - 51.91, TOP - 7.22
        faces = []
        for s in (1, -1):
            faces.append((V((s * TX, -s * TY, 0)), V((0, s, 0)), V((s, 0, 0)), 2 * TY))
            faces.append((V((s * TX, s * TY, 0)), V((-s, 0, 0)), V((0, s, 0)), 2 * TX))
        for a, t, n, L in faces:
            out += kit.chevron_parapet(a, t, n, L, d0=0.2, d1=4.13, dz=dz)
            cs, _ = bays(0, L)
            out += corbels(a, t, n, cs, bz)
        for sx in (1, -1):
            for sy in (1, -1):
                out += step_pyramid(sx * (TX + 2.1), sy * (TY + 2.1), TOP + 5.09, 0.6)
            for u in (-BANNER[0], BANNER[0]):
                out += kit.banner(V((sx * TX, 0, 0)), V((0, sx, 0)), V((sx, 0, 0)), u, bz - 6.4, BANNER[1], BANNER[2],
                                  d=0.05)
        out += ziggurat(0, 0, TOP, ROOF, (5.0, 6.0))[0]
        return out

    def emphasis(self, c, n):
        if c.z < -2:
            return 0.15
        if c.z > 85:
            return 1.5                        # the tower's crown and roof
        return 1.3 if c.z > 50 else 1.0
