"""Men stable, level 3 (Upgrade_StructureLevel3: ShowSubObjects V1 V2): the belfry V2, redesigned
on the finished level 2 (`base`, levels.py), so the central block ends in the citadel's crown.

EA's V2 (model coordinates): on the central block's deck (from 51.5) a shaft (half 8.1..8.5)
flaring from 60.7 to the storey, a chamfered square centred (-28.51, -0.49), half 12.63,
chamfer 3.55, from 66.9 to its eave at 83.12; two round-arched windows a face (u +-4.95 from
the face's middle, half 2.33, sill 70.1, springing 77.2, crown 80.5; the level-3 arrows'
bones ARROW_01..08 in them at z 73.8); a flared eave to a dome of chamfered squares (85.53 half
9.79, 88.9 8.13, 91.65 6.28, 93.37 4.68, 94.22 3.14, 94.97 1.29) and a spike to 97.28. V2 also
carries the two flag poles leaving the gables (their flags V2FLAG): untouched.

What stands on it here:

    storey  the windows in voussoir surrounds with keystones and sills on corbels; a sable
            frieze of gilt stars under them; square merlons round the eave, a corbelled bartizan
            with a slate spirelet on each chamfer
    dome    steel eave band and ribs, a lantern, a gilt orb and spike (EA's spike goes inside)
    shaft   quoins up its corners

Nothing stands in a window (the arrows leave through them). No cloth, no night lights (levels.py).
"""
from ..barracks.levels import LevelMesh, chain, level_textures
from ..stable.building import NOT_BAKED
from ..stable.pieces import faces

C, HALF, CH = (-28.51, -0.49), 12.63, 3.55
Z_SILL, Z_SPRING, Z_EAVE = 70.1, 77.2, 83.12
WIN = (4.95, 2.33, 3.3)                          # |u|, half, rise
DOME = [(85.6, 9.79, 2.75), (88.9, 8.13, 2.3), (91.65, 6.28, 1.8), (93.37, 4.68, 1.3), (94.22, 3.14, 0.9)]
SHAFT = (8.3, 53.2, 60.4)                        # half, quoin foot and top


class StableLevel3(LevelMesh):
    source = "GBStable_SKN"
    target = "V2"
    base = chain("stable", 3)
    level = 3
    own_textures = level_textures("S", 3)
    bake_hidden = tuple(n for n in NOT_BAKED if n not in ("V1", "V2", "V2FLAG"))
    footprint_margin = 0.8                       # the bartizans corbel out of the storey's west chamfers (V2's box edge)
    views = {
        "rts": ((-8.0, -0.5, 40.0), 380, 50, -38, 50),
        "close": ((-28.5, -0.5, 75.0), 130, 22, -32, 45),
        "crown": ((-28.5, -0.5, 88.0), 70, 20, -40, 45),
        "ingame": ((2.8, -0.7, 28.5), 837, 53, -62, 50),
    }

    @property
    def clear(self):
        from sagekit.clear import Box
        return [Box((C[0] - 1.5, C[1] - 1.5, 95.5), (C[0] + 1.5, C[1] + 1.5, 98.0))]      # EA's spike: the lantern's

    def design(self, kit):
        from ..barracks.motifs import closed
        return closed(self._storey(kit) + self._crown(kit) + self._shaft())

    @staticmethod
    def _storey(kit):
        from ..barracks.motifs import star_frieze, window_surround
        out = []
        for a, t, n in faces(*C, HALF):
            for e in (-1, 1):
                u, h, rise = e * WIN[0], WIN[1], WIN[2]
                out += window_surround(kit, a, t, n, u, h, Z_SILL, Z_SPRING, rise=rise, w=0.7, d=0.6)
            out += star_frieze(kit, a, t, n, -(HALF - CH) + 0.2, HALF - CH - 0.2, 67.3, h=1.6, d1=0.45, count=5)
        return out

    @staticmethod
    def _crown(kit):
        """Merlons along the eave between the chamfers, a bartizan corbelled out of each chamfer
        from 74, the dome's steel dress, a lantern, orb and spike."""
        import math

        from ..barracks.motifs import crown_dome
        cx, cy = C
        out = []
        L = 2 * (HALF - CH)
        for a, t, n in faces(cx, cy, HALF):
            out += kit.merlons(a - t * (L / 2), t, n, 0.2, L - 0.2, Z_EAVE, -1.3, 0.25, w=2.1, gap=1.5, h=2.5)
        k = (2 * HALF - CH) / 2 + 0.35              # the chamfer's middle, a little out along the diagonal
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            out += kit.bartizan(cx + dx * k, cy + dy * k, 74.0, r=2.1, h=8.4, spire=6.8, facing=math.atan2(dy, dx))
        out += crown_dome(kit, cx, cy, DOME, eave=(Z_EAVE - 0.3, HALF, CH), lantern=(93.9, 2.6, 98.4), finial=(102.0, 106.8))
        return out

    @staticmethod
    def _shaft():
        """Long and short quoins up the shaft's four corners, below the flare."""
        from ..barracks.motifs import quoins
        cx, cy = C
        h, z0, z1 = SHAFT
        out = []
        for a, t, n in faces(cx, cy, h):
            for side in (-1, 1):
                out += quoins(a, t, n, side * h, z0, z1, side=side, long=2.0, short=1.2, h=1.5, d=0.3)
        return out

    @property
    def sheet_atlas(self):
        from ..workshop.prodkit import VET_TILES, with_tiles
        return with_tiles(super().sheet_atlas, VET_TILES)       # EA's slate caps stay slate

    def emphasis(self, c, n):
        if c.z > 66:
            return 1.35                      # the storey, crown and dome
        return 1.0
