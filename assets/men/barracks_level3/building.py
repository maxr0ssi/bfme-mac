"""Men barracks, level 3 (Upgrade_GondorBarracksLevel3: ShowSubObjects V1 V2): the belfry storey
and the two turrets V2, redesigned on the finished level 2 (`base`, levels.py), so the keep ends in
the citadel's crown.

EA's V2 (model coordinates): a belfry storey on the keep's eave, centre (-19.94, -25.73), a
chamfered square (half 16.6, chamfer 4.6) from z 65.3 (flaring out from 15.4 to 68.9) to its eave
at 89.25, two round-arched windows a face (u +-6, the opening 3.55 half at the face, sill 73,
the level-3 arrows' bones ARROW_17..24 in them at z 78), a slate dome to 104 and a spike to
119.6; and a turret on each wing's end block, centre (26.75, -29.25) and (-24.85, 28.25), half
13.55, chamfer 3.8, z 30..48.3, two windows a face (u +-5, ARROW_01..16 at z 38), a dome to 62.7
and a spike to 74.6. What stands on it here:

    storey      the windows in voussoir surrounds with keystones and sills on corbels; a sable
                frieze of gilt stars under them; square merlons on the eave round the dome and a
                corbelled bartizan (slit windows, slate spirelet) on each chamfer
    domes       steel eave bands and ribs; a lantern, gilt orb and spike on the storey's dome (EA's
                spike goes), gilt orbs and spikes on the turrets'
    turrets     window surrounds, merlons on the eave, a pinnacle on each chamfer

Nothing stands in a window (the arrows leave through them). No cloth, no night lights (levels.py).
"""
from ..barracks.building import NOT_BAKED
from ..levels import LevelMesh, chain, level_textures

KEEP = (-19.94, -25.73, 16.6, 4.6)               # centre, half, chamfer
TURRETS = [(26.75, -29.25), (-24.85, 28.25)]
T_HALF, T_CH = 13.55, 3.8
Z_EAVE, T_EAVE = 89.25, 48.3
DOME = [(90.5, 15.1, 4.2), (93.0, 12.4, 3.5), (96.0, 10.9, 3.0), (100.0, 8.15, 2.3), (103.0, 3.6, 1.0)]
T_DOME = [(50.0, 11.35, 3.2), (52.0, 9.8, 2.8), (55.0, 8.1, 2.3), (58.0, 5.65, 1.6), (60.0, 2.3, 0.7)]
SPIKES = [(-19.72, -25.5, 105.5), (26.75, -29.25, 61.0), (-24.85, 28.25, 61.0)]


def faces(cx, cy, half):
    """(anchor at the face's middle, t, n) of a square's four faces, t x n = -z."""
    from mathutils import Vector as V
    out = []
    for nx, ny in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        n = V((nx, ny, 0))
        out.append((V((cx + nx * half, cy + ny * half, 0)), V((-ny, nx, 0)), n))
    return out


class BarracksLevel3(LevelMesh):
    source = "GBBarracks_SKN"
    target = "V2"
    base = chain("barracks", 3)
    level = 3
    own_textures = level_textures("B", 3)
    bake_hidden = NOT_BAKED[:-2]
    footprint_margin = 1.0              # the turrets' outer faces are V2's edge: their window surrounds stand 0.95 proud
    views = {
        "rts": ((0.2, -2.3, 45.0), 360, 50, -38, 50),
        "close": ((-8, -12, 70), 200, 24, -30, 45),
        "crown": ((-19.94, -25.73, 90), 90, 18, -40, 45),
        "ingame": ((0.2, -2.3, 35.2), 726, 53, -62, 50),
    }

    @property
    def clear(self):
        from sagekit.clear import Box
        return [Box((x - 1.2, y - 1.2, z), (x + 1.2, y + 1.2, z + 16.0)) for x, y, z in SPIKES]

    def design(self, kit):
        out = self._storey(kit)
        for cx, cy in TURRETS:
            out += self._turret(kit, cx, cy)
        from ..motifs import closed
        return closed(out)

    @staticmethod
    def _crown(kit, cx, cy, half, ch, z, dome, bartizans):
        """Merlons on an eave (runs between the chamfers) and, on each chamfer, a bartizan corbelled
        out below the eave (bartizans: (corbel z, height, spire)) or a pinnacle on the eave."""
        import math

        from mathutils import Vector as V
        out = []
        L = 2 * (half - ch)
        for a, t, n in faces(cx, cy, half):
            out += kit.merlons(a - t * (L / 2), t, n, 0.2, L - 0.2, z, -1.3, 0.25, w=2.1, gap=1.5, h=2.5)
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            r = (2 * half - ch) / math.sqrt(2) / math.sqrt(2) + 0.1
            if bartizans:
                z0, h, spire = bartizans
                out += kit.bartizan(cx + dx * r, cy + dy * r, z0, r=2.1, h=h, spire=spire, facing=math.atan2(dy, dx))
            else:
                c = V((cx + dx * (r + 0.35), cy + dy * (r + 0.35), 0))
                out += kit.pinnacle(c.x, c.y, z, z + 2.6, half=1.0, spire=4.2)
        return out

    def _storey(self, kit):
        from ..motifs import crown_dome, star_frieze, window_surround
        cx, cy, half, ch = KEEP
        out = []
        for a, t, n in faces(cx, cy, half):
            for u in (-6.0, 6.0):
                out += window_surround(kit, a, t, n, u, 3.6, 72.9, 81.3, rise=4.2, w=0.75, d=0.7)
            out += star_frieze(kit, a, t, n, -11.6, 11.6, 69.3, h=1.8, d1=0.45, count=7)
        out += self._crown(kit, cx, cy, half, ch, Z_EAVE, DOME, (80.6, 8.2, 6.8))
        out += crown_dome(kit, cx, cy, DOME, eave=(Z_EAVE - 0.3, half, ch), lantern=(101.8, 3.1, 106.2), finial=(110.8, 123.5))
        return out

    def _turret(self, kit, cx, cy):
        from ..motifs import crown_dome, window_surround
        out = []
        for a, t, n in faces(cx, cy, T_HALF):
            for u in (-5.0, 5.0):
                out += window_surround(kit, a, t, n, u, 2.4, 33.9, 40.2, rise=2.6, w=0.6, d=0.6)
        out += self._crown(kit, cx, cy, T_HALF, T_CH, T_EAVE, T_DOME, None)
        out += crown_dome(kit, cx, cy, T_DOME, eave=(T_EAVE - 0.3, T_HALF, T_CH), finial=(64.8, 73.5))
        return out

    def decals(self):
        from ..paint import Slate                # the domes' tiles charcoal, as the body's
        return [Slate(Z_EAVE), Slate(T_EAVE, box=(12.0, 41.5, -44.0, -14.5)), Slate(T_EAVE, box=(-39.5, -10.0, 13.5, 43.0))]

    def emphasis(self, c, n):
        if c.z > 85 or (c.z > 45 and c.x > 0) or (c.z > 45 and c.y > 0):
            return 1.35                      # the crowns and domes
        return 1.0
