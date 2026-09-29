"""Men forge, level 3 (Upgrade_StructureLevel3: ShowSubObjects V1 V2): the belfry V2, redesigned
on the finished level 2 (`base`, levels.py), so the forge ends in the citadel's crown.

EA's V2 (model coordinates): on V1's shaft behind the hall a chamfered square tower centred
(0.34, 32.46), half 8.63, chamfer 3.85: its base from 48.33, a projecting band at 58.2, the
storey to its eave at 74.75 with one round-arched window a face (EA's frame half 2.9 from
61.6 to 72.1; the level-3 arrows' bones ARROW_01..04 in them at z 65.3); a dome of chamfered
squares (77.21 half 5.62, 79.82 4.13, 81.75 2.24) and a spike to 91.68.

What stands on it here:

    storey  a voussoir surround round each window (outside EA's frame) with a keystone and a
            sill on corbels; a steel band round the base
    crown   square merlons along the eave, a pinnacle on each chamfer; the dome's steel eave
            band and ribs, a steel mast, gilt orb and spike (EA's spike goes)

Nothing stands in a window (the arrows leave through them). No cloth, no night lights (levels.py).
"""
from ..levels import LevelMesh, chain, level_textures
from ..forge.building import NOT_BAKED

C, HALF, CH = (0.34, 32.46), 8.63, 3.85
Z_EAVE = 74.75
DOME = [(77.21, 5.62, 2.95), (79.82, 4.13, 1.9), (81.75, 2.24, 1.0)]


class ForgeLevel3(LevelMesh):
    source = "GBBlkSmith_SKN"
    target = "V2"
    base = chain("forge", 3)
    level = 3
    own_textures = level_textures("F", 3)
    bake_hidden = tuple(n for n in NOT_BAKED if n not in ("V1", "V2"))
    footprint_margin = 1.1                       # the window surrounds' sills stand on V2's faces, its box's edges
    views = {
        "rts": ((0.0, 10.0, 36.0), 290, 50, -38, 50),
        "close": ((0.3, 32.5, 66.0), 90, 20, -36, 45),
        "ingame": ((-0.0, 0.1, 27.6), 555, 53, -62, 50),
    }

    @property
    def clear(self):
        from sagekit.clear import Box
        return [Box((C[0] - 1.2, C[1] - 1.2, 83.0), (C[0] + 1.2, C[1] + 1.2, 92.0))]      # EA's spike: the finial's

    def design(self, kit):
        from mathutils import Vector as V

        from ..motifs import band_path, closed, crown_dome, octagon, window_surround
        from ..stable.pieces import faces
        cx, cy = C
        out = []
        L = 2 * (HALF - CH)
        for a, t, n in faces(cx, cy, HALF):
            out += window_surround(kit, a, t, n, 0.0, 2.95, 61.6, 68.5, rise=2.95, w=0.6, d=0.75)
            out += kit.merlons(a - t * (L / 2), t, n, 0.2, L - 0.2, Z_EAVE, -1.2, 0.25, w=1.9, gap=1.3, h=2.3)
        k = (2 * HALF - CH) / 2 + 0.3
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            c = V((cx + dx * k, cy + dy * k, 0))
            out += kit.pinnacle(c.x, c.y, Z_EAVE, Z_EAVE + 2.4, half=0.9, spire=3.6)
        out += band_path(octagon(cx, cy, HALF, CH), 48.4, 49.4, -0.4, 0.35, "trim", center=C, top="trim")
        out += crown_dome(kit, cx, cy, DOME, eave=(Z_EAVE - 0.3, HALF, CH), finial=(86.0, 96.5))
        return closed(out)

    @property
    def sheet_atlas(self):
        from ..prodkit import VET_TILES, with_tiles
        return with_tiles(super().sheet_atlas, VET_TILES)       # EA's slate caps stay slate

    def emphasis(self, c, n):
        if c.z > 60:
            return 1.35                      # the storey, crown and dome
        return 1.0
