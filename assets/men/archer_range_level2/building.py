"""Men archer range, level 2 (Upgrade_GondorArcheryRangeLevel2: ShowSubObjects V1): the thickened
yard walls and the eight obelisks V1, redesigned on the finished archer range (`base`, levels.py).

EA's V1 (model coordinates): the west and east yard walls thickened to 11 (x -35.4..-24.3 and
24..35, outer faces x = -35.9 + 0.035 z and 35.5 - 0.035 z) up to z 19.87 with a painted
crenellation; the north wall (outer face y 53.4 -> 53.0) to 14.65; eight obelisks at x +-45,
y -28.6, -2.1, 25.6, 50.9 (a base 8.2 square to 5.42, a sloped step to 6.36 at half 2.5, the shaft
tapering to half 1.12 at 19.51). Level 3 (V2) stands a domed turret on the north-west corner
(x -40..-19, y 38.6..59) and arcades across the yard on the walls' inner halves.

What stands on it here:

    walls     a machicolated gallery on the west and east walls' outer faces (corbels, a sable
              slab of silver stars, square merlons), merlons on the north wall, stopping short of
              level 3's turret
    obelisks  a moulded course on the base, a White Tree roundel on the outward face, gilt
              seven-pointed stars on all four faces, a steel collar and a steel mast with a gilt
              orb and spike (under the height limit, 23.86)

No cloth, no night lights (a level mesh: levels.py). Footprint = V1's bounding box.
"""
from ..archer_range.building import NOT_BAKED
from ..levels import LevelMesh, chain, level_textures

OBELISKS = [(-45.1, y) for y in (-28.6, -2.15, 25.6, 50.9)] + [(44.94, y) for y in (-28.7, -1.9, 25.3, 50.9)]
Z_TOP, Z_CORBEL, Z_SLAB, OUT = 19.87, 14.2, 17.7, 1.1


def shaft_half(z):
    return 2.5 - 0.105 * (z - 6.36)


class ArcherRangeLevel2(LevelMesh):
    source = "GBArcheryN_SKN"
    target = "V1"
    base = chain("archer_range", 2)
    own_textures = level_textures("A", 2)
    bake_hidden = NOT_BAKED[:-2] + ("V2",)
    views = {
        "rts": ((5.2, 0.4, 40.0), 356, 50, -38, 50),
        "close": ((20, 0, 15), 190, 22, -30, 45),
        "obelisk": ((44.9, -28.7, 12), 55, 15, -30, 45),
        "ingame": ((5.2, 0.4, 52.2), 809, 53, -62, 50),
    }

    def design(self, kit):
        out = self._walls(kit)
        for cx, cy in OBELISKS:
            out += self._obelisk(kit, cx, cy)
        from ..motifs import closed
        return closed(out)

    @staticmethod
    def _walls(kit):
        from mathutils import Vector as V

        from ..motifs import corbel_table, slab
        out = []
        for x0, sx, u0, u1 in ((-35.9, 0.035, -36.5, 10.0), (35.5, -0.035, -11.0, 50.0)):
            n = V((-1, 0, 0)) if x0 < 0 else V((1, 0, 0))
            t = V((-n.y, n.x, 0))
            a = V((x0 + sx * 17.5, 0, 0))
            lo, hi = sorted((u0, u1))
            out += corbel_table(kit, a, t, n, lo, hi, Z_CORBEL, pitch=2.9, w=0.45, d1=0.55, d2=OUT, h=1.75)
            out.append(slab(a, t, n, lo, hi, Z_SLAB, Z_TOP, -1.2, OUT, ("stoneB", "stoneB", "top", "stoneB"), "enamel"))
            out += kit.merlons(a, t, n, lo + 0.2, hi - 0.2, Z_TOP, -0.3, OUT - 0.05, w=2.1, gap=1.5, h=2.5)
        a, t, n = V((0, 53.1, 0)), V((-1, 0, 0)), V((0, 1, 0))
        out += kit.merlons(a, t, n, -21.0, 18.0, 14.65, -1.3, 0.25, w=2.1, gap=1.5, h=2.4)
        return out

    @staticmethod
    def _obelisk(kit, cx, cy):
        from mathutils import Vector as V

        from sagekit.blender.geometry import box_rings, loft

        from ..motifs import knob, roundel
        out = [loft([box_rings((cx - 3.75, cx + 3.75), (cy - 3.75, cy + 3.75), 5.2, 0),
                     box_rings((cx - 3.75, cx + 3.75), (cy - 3.75, cy + 3.75), 5.85, 0)], ["course"], cap0=("stoneB", True), cap1=("top", True))]
        h = shaft_half(15.6) + 0.28
        out.append(loft([box_rings((cx - h, cx + h), (cy - h, cy + h), 15.2, 0), box_rings((cx - h, cx + h), (cy - h, cy + h), 16.0, 0)],
                        ["trim"], cap0=("trim", True), cap1=("trim", True)))
        outward = 1 if cx > 0 else -1
        for nx, ny in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            n = V((nx, ny, 0))
            t = V((-ny, nx, 0))
            a = V((cx + nx * shaft_half(12.6), cy + ny * shaft_half(12.6), 0))
            out += kit.star(a, t, n, 0.0, 12.6, 0.95, -0.3, 0.3)
            if nx == outward:
                a = V((cx + nx * shaft_half(9.3), cy, 0))
                out += roundel(kit, a, t, n, 0.0, 9.3, 1.55, d=0.15, studs=False, back=-0.5)
        out += knob(cx, cy, 19.3, 23.7)
        return out

    def emphasis(self, c, n):
        if c.z > 14.0 or abs(abs(c.x) - 45.0) < 5.0:
            return 1.3                      # the galleries and the obelisks
        return 1.0
