"""The Gondor well (GondorWell): EA's fountain kept whole - the low outer wall round its sunken
pool, the raised basin, the hexagonal column and the guardsman on it - and its stonework dressed
the way of Minas Tirith. The raised basin's broad rim gains a moulded kerb and eight small
pinnacles with steel orbs; the outer wall a moulded coping and pinnacle posts; the column a
moulded base, two string rings, three White Tree shields, a steel necking and a gilt band under
its capital. The water (SPOUT03, RBWELLWATER01, SPLASH) and the figure are EA's and untouched:
nothing new stands in the spouts' arcs (r 5..11.1, z -1.3..6.6 here) or on the pools.

EA's GBWell.GBWELL (mesh coordinates; the mesh stands 14.85 up on its bone, so the ground is at
z -14.85 here): the outer wall a 16-gon (vertices at 0, 22.5, ... degrees) from the ground up to
its rim at -3.69, r 26.9..28.56, with a stepped block at each diagonal (33.8..56.3 + 90k); the
pool's floor at -9.57 and its water at -5.8 (r 14..26.9); the raised basin's rim a 16-gon slab r
13.43..18.8 from -0.83 to 1.93, its water inside at about 0.4..0.9; the column's hexagonal base
(r 9.0 at 0, 6.0 from 3.13 to 6.9) narrowing to the shaft (r 2.9, vertices at 0, 60, ...) from
9.62 to 25.1, the capital (r 4.4) at 28.3..30.0, the figure from 30 to 52.7. The footprint is x
-28.69..28.97, y -29.03..28.63."""
from sagekit.building import Building

from ..style import MenStyle

BASIN = (13.43, 18.8, 1.93)          # the raised basin's rim: inner, outer radius, top
RIM = (26.9, 28.56, -3.69)           # the outer wall's rim
SHAFT = (2.9, 9.62, 25.1)            # the column: vertex radius, foot, neck


class Well(Building):
    style = MenStyle()
    source = "GBWell"
    target = "GBWELL"
    sheet = "GBWell.tga"
    sheet_normal = "GBWell_NRM.tga"
    own_textures = {"GBWell.tga": "GBWelH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((0.1, -0.2, 30.0), 233, 50, -38, 50),
        "close": ((0.1, -0.2, 22.0), 125, 30, -30, 45),
        "column": ((0.1, -0.2, 34.0), 62, 18, -38, 45),
        "ingame": ((0.1, -0.2, 33.8), 530, 53, -62, 50),
    }

    def design(self, kit):
        out = self._basin(kit)
        out += self._rim(kit)
        out += self._column(kit)
        return out

    @staticmethod
    def _basin(kit):
        """A moulded kerb along the raised basin's outer edge, a pinnacle over every other vertex."""
        from ..shapes import turned
        _, r1, z = BASIN
        out = [turned(0, 0, [(r1 - 1.3, z - 0.2), (r1 + 0.05, z - 0.2), (r1 + 0.05, z + 0.35), (r1 - 0.2, z + 0.75),
                             (r1 - 1.1, z + 0.75), (r1 - 1.3, z - 0.2)], [None, "course", "course", "top", "stoneB"],
                      k=16, phase=0.0,
                      cap0=("stoneB", False), cap1=("top", False))]
        import math
        for k in range(8):
            a = math.radians(45 * k)
            rc = r1 - 0.85
            out += kit.pinnacle(rc * math.cos(a), rc * math.sin(a), z + 0.5, z + 3.2, half=0.6, spire=2.6)
        return out

    @staticmethod
    def _rim(kit):
        """A moulded coping on the outer wall's rim (inside the footprint), and a pinnacle post either
        side of each diagonal's stepped block."""
        import math

        from ..shapes import turned
        r0, r1, z = RIM
        out = [turned(0, 0, [(r0 - 0.25, z - 0.3), (r1 - 0.02, z - 0.3), (r1 - 0.02, z + 0.3), (r1 - 0.3, z + 0.6),
                             (r0 + 0.05, z + 0.6), (r0 - 0.25, z + 0.3), (r0 - 0.25, z - 0.3)],
                      ["stoneB", "course", "course", "top", "course", "course"],
                      k=16, phase=0.0, cap0=("stoneB", False), cap1=("stoneB", False))]
        rc = (r0 + r1) / 2
        for k in range(4):                                  # flanking each diagonal's stepped block
            for off in (-22.5, 22.5):
                b = math.radians(45 + 90 * k + off)
                out += kit.pinnacle(rc * math.cos(b), rc * math.sin(b), z + 0.5, z + 4.0, half=0.7, spire=3.0)
        return out

    @staticmethod
    def _column(kit):
        """A moulded base and two rings round the hexagonal shaft, White Tree shields on three of
        its faces, a steel necking and a gilt band under EA's capital."""
        import math

        from mathutils import Vector as V

        from ..shapes import turned
        r, z0, z1 = SHAFT
        ph = 0.0                                              # EA's hexagon: vertices at 0, 60, ...
        out = [turned(0, 0, [(r + 0.75, z0 - 0.3), (r + 0.75, z0 + 0.5), (r + 0.4, z0 + 0.9), (r + 0.4, z0 + 1.3),
                             (r - 0.1, z0 + 1.6)], ["course", "course", "course", "top"], k=6, phase=ph,
                      cap0=("stoneB", False), cap1=("top", False))]
        for z in (15.0, 20.4):
            out.append(turned(0, 0, [(r - 0.1, z), (r + 0.35, z), (r + 0.35, z + 0.6), (r - 0.1, z + 0.6)],
                              ["stoneB", "course", "top"], k=6, phase=ph, cap0=("stoneB", False), cap1=("top", False)))
        out.append(turned(0, 0, [(r - 0.1, z1 - 1.2), (r + 0.3, z1 - 1.2), (r + 0.3, z1 - 0.6), (r - 0.1, z1 - 0.6)],
                          ["trim", "trim", "trim"], k=6, phase=ph, cap0=("trim", False), cap1=("trim", False)))
        out.append(turned(0, 0, [(r - 0.1, z1 - 0.6), (r + 0.4, z1 - 0.6), (r + 0.4, z1), (r - 0.1, z1)],
                          ["gilt", "gilt", "gilt"], k=6, phase=ph, cap0=("gilt", False), cap1=("gilt", False)))
        apothem = r * math.cos(math.radians(30))
        for deg in (90, 210, 330):
            n = V((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0))
            out += kit.shield(n * apothem, V((-n.y, n.x, 0)), n, 0.0, 16.3, 1.15, 3.6)
        return out

    def emphasis(self, c, n):
        return 1.3 if c.z > 8 else 1.0
