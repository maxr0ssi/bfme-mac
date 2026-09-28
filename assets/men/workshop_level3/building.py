"""The Gondor siege workshop at level 3 (Upgrade_StructureLevel3): V2, the domed storeys on the
gate towers, redesigned on the finished level-2 workshop (`base`; levels.py). EA's V2 is a
chamfered-square storey on each tower with two arched windows a face and a slate dome with a
thin stone spike. Now, like the citadel's towers:

    frieze      a sable band with five gilt stars round the storey's foot, on every face
    windows     voussoir surrounds with keystones and sills round EA's sixteen windows
    bartizans   a corbelled turret on each of the four chamfers: slit windows, a steel-banded
                cornice, a slate spirelet and a steel spike
    dome        a steel eave band, steel ribs up the dome's eight hips and four middles, a
                lantern cupola where EA's spike stood, a steel mast, a gilt orb and a spike

No cloth and no lights (a level mesh). EA's V2 (model coordinates; the towers at (-29.37,
+-26.5)): the storey's faces 13.47 from the axis (chamfer 3.9) from its flared foot at 51.1 to
the eave at 67.6 (13.62, chamfer 3.85), string courses at 54.5 and 61.3 (13.67); the windows at
u +-5.0 on each face, half 2.4, sill 55.1, springing 61.2, crown 64.3; the dome's rings (z, half,
chamfer) (70.1, 10.44, 2.94) .. (78.9, 3.35, 0.65), apex 82.1, the spike to 93.8 (cleared).
The bartizans stand 0.6 past the storey's faces (footprint_margin); height +20 %: z 102.9."""
from sagekit.clear import Box

from ..barracks.levels import LevelMesh, chain, level_textures

CX, CY = -29.37, 26.5
FACE, CH = 13.47, 3.9
WINDOWS = (5.0, 2.4, 55.1, 61.2, 3.1)          # |u|, half, sill, springing, rise
DOME = [(67.8, 13.55, 3.85), (70.1, 10.44, 2.94), (73.5, 8.66, 2.57), (76.3, 6.70, 1.95), (78.1, 4.99, 1.30), (78.9, 3.35, 0.65)]
LANTERN = (78.2, 3.5, 83.6)                    # z0 (the dome's half there about 4.6), r, top
FINIAL = (87.8, 99.5)                          # orb, tip
BARTIZAN = (16.8, 57.6)                        # centre out along the diagonals, corbel foot


class WorkshopLevel3(LevelMesh):
    source = "GBWorkshop"
    target = "V2"
    base = chain("workshop", 3)
    level = 3
    own_textures = level_textures("W", 3)
    footprint_margin = 0.8
    clear = [Box((CX - 0.7, s * CY - 0.7, 82.5), (CX + 0.7, s * CY + 0.7, 94.5)) for s in (1, -1)]
    bake_hidden = ("V1HIDE", "N_WINDOW")
    views = {
        "rts": ((5.0, 0.0, 30.0), 320, 50, -38, 50),
        "close": ((-29.4, 0.0, 62.0), 130, 22, -30, 45),
        "crown": ((-29.4, -26.5, 74.0), 70, 24, -40, 45),
        "ingame": ((5.0, 0.0, 30.0), 700, 53, -62, 50),
    }

    @property
    def sheet_atlas(self):
        from ..workshop.prodkit import VET_TILES, with_tiles
        return with_tiles(super().sheet_atlas, VET_TILES)       # EA's slate caps stay slate

    def design(self, kit):
        out = []
        for s in (1, -1):
            out += self._storey(kit, CX, s * CY)
            out += self._dome(kit, CX, s * CY)
        return out

    @staticmethod
    def _faces(cx, cy):
        from ..barracks import motifs as M
        return [M.face((cx + FACE * nx, cy + FACE * ny), (nx, ny)) for nx, ny in ((1, 0), (0, 1), (-1, 0), (0, -1))]

    def _storey(self, kit, cx, cy):
        import math

        from ..barracks import motifs as M
        out = []
        flat = FACE - CH - 0.2
        uw, half, sill, spring, rise = WINDOWS
        for a, t, n in self._faces(cx, cy):
            out += M.star_frieze(kit, a, t, n, -flat, flat, 51.5, h=2.3, d0=-0.25, d1=0.3, count=5)
            for u in (-uw, uw):
                out += M.window_surround(kit, a, t, n, u, half, sill, spring, rise=rise, w=0.5, d=0.3, count=7)
        R, z0 = BARTIZAN
        for dx in (1, -1):
            for dy in (1, -1):
                r = R / math.sqrt(2)
                out += kit.bartizan(cx + dx * r, cy + dy * r, z0, facing=math.atan2(dy, dx))
        return out

    @staticmethod
    def _dome(kit, cx, cy):
        from ..barracks import motifs as M
        z, h, ch = DOME[0]
        out = M.band_path(M.octagon(cx, cy, h, ch), z - 0.45, z + 0.35, -0.4, 0.25, "trim", center=(cx, cy), top="trim")
        out += kit.ribs(cx, cy, DOME, r=(0.32, 0.18), proud=0.18)
        z0, r, top = LANTERN
        out += kit.lantern(cx, cy, z0, r=r, top=top)
        orb, tip = FINIAL
        out += kit.finial(cx, cy, top - 0.1, orb, tip)
        return out
