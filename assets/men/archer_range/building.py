"""Men archer range (GondorArcherRange): EA's body kept whole - the tall buttressed tower and its
little ribbed dome, the slate-roofed hall, the low south-west block, the yard walls and the target
arcade at the north end with its animated pulley - and dressed like the citadel.

EA's GBArcheryN_SKN, body ARCHERY (913 triangles), painted from gbarcheryn_l.tga (own copy
gbarcheryn_H.tga); new faces sample the Men atlas. ARCHERY mesh coordinates are the model's.
What EA's body is, measured:

    tower   centre (29.21, -36.67): the lower shaft half 11.3 (chamfer 2.6: south face y -48.0,
            east face x 40.52) to z 70, a sloped set-back to the upper shaft (half 9.09) at 78,
            EA's crenellated band at 96..100, the dome an octagon (vertices at 0, 45, ... degrees:
            circumradius 8.25 at 98.18, 6.77 at 101.6, 4.28 at 104.03) to its point at 104.86
    hall    front y -45.95 (x -1.9..17.9, a corner pier to -48.3), walls to 27.8, a slate roof to its
            ridge at 38.7 (y -37)
    terrace a paved terrace x -31.1..-5.6 south of the yard's south wall (y -28.4, to z 14)
    yard    walls x -31.2..-27.7 and 27.7..30.4 to z 14 (V2 raises them at level 3), the targets'
            pulley (skinned) across the yard, the target arcade at y 46..51

What stands on it here:

    tower   two machicolated galleries (corbels, a sable band of silver stars, merlons with
            capstones): round the lower shaft at z 64..73 and the upper at 87..96, with a corbelled
            bartizan on each chamfer of the upper one; steel ribs and a lantern on the dome, kept
            under 107.5 (level 3 stands an archer's statue on the dome, its plinth half 3.1)
    faces   a house-colour banner on the tower's south and east faces; a White Tree roundel and a
            frieze of gilt stars on the hall's front; a roundel on the terrace's back wall
    roof    a steel ridge with cresting and gilt knobs, a fascia on brackets along the hall's eave
    yard    upright piers and White Tree roundels on the yard walls' outer faces (below z 14)
"""
from sagekit.building import Building

from ..style import MenStyle

T = (29.21, -36.67)
LOW, UP, CH = 11.1, 9.09, 2.6
DOME = [(98.18, 8.25), (101.6, 6.77), (104.03, 4.28), (104.8, 0.6)]      # (z, circumradius): an octagon
NOT_BAKED = ("ARCHER", "Y_ARCHER", "Z_ARCHER", "QUIVER", "Y_QUIVER", "Z_QUIVER", "BOW", "Y_BOW", "Z_BOW", "SWORD",
             "N_WINDOW", "OBJECTS", "OBJECT01", "OBJECT02", "OBJECT03", "Z_ARROWNOCK01", "Z_ARROWNOCK", "Y_ARROWNOCK01",
             "Y_ARROWNOCK", "Y_ARROW", "Z_ARROW", "PULLEY_SYSTEM", "V1", "V2")


def gallery(kit, half, z_corbel, out, bartizans=None):
    """A machicolated gallery round the tower's shaft (half `half`): corbels from z_corbel on the
    long faces, a slab `out` proud 2 high with a sable front, a parapet and merlons; on the
    chamfers a bartizan (bartizans: (z0, h, spire)) or nothing."""
    import math

    from mathutils import Vector as V

    from sagekit.blender.geometry import sweep

    from ..motifs import corbel_table, octagon
    zs, zw, zp = z_corbel + 3.4, z_corbel + 5.4, z_corbel + 6.5
    path = octagon(*T, half, CH)
    res, segs = sweep(path, [(-1.6, zs), (out, zs), (out, zw), (-1.6, zw)], ["stoneB", "enamel", "top", None], center=T)
    res += sweep(path, [(out - 1.0, zw - 0.1), (out - 0.1, zw - 0.1), (out - 0.1, zp), (out - 1.0, zp)],
                 [None, "stoneA", "top", "stoneA"], center=T)[0]
    for a, b, t, n in segs:
        L = (b - a).length
        if L < 5:
            continue
        a3, t3, n3 = V((a.x, a.y, 0)), t.to_3d(), n.to_3d()
        res += corbel_table(kit, a3, t3, n3, 0.3, L - 0.3, z_corbel, pitch=2.9, w=0.45, d1=0.55 * out, d2=out, h=1.7)
        res += kit.merlons(a3, t3, n3, 0.3, L - 0.3, zp, out - 1.0, out - 0.1, w=2.0, gap=1.4, h=2.5)
    if bartizans:
        z0, h, spire = bartizans
        r = (2 * half - CH) / 2 + 0.1
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            res += kit.bartizan(T[0] + dx * r, T[1] + dy * r, z0, r=1.9, h=h, spire=spire, facing=math.atan2(dy, dx))
    return res


class ArcherRange(Building):
    style = MenStyle()
    source = "GBArcheryN_SKN"
    target = "ARCHERY"
    sheet = "gbarcheryn_l.tga"
    sheet_normal = "gbarcheryn_l_nrm.tga"
    own_textures = {"gbarcheryn_l.tga": "gbarcheryn_H.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    bake_hidden = NOT_BAKED
    footprint_margin = 1.3              # the yard walls' and the tower's faces are the footprint's edge: their
                                        # piers, banners and roundels stand proud of it (collision is the INI's)
    views = {
        "rts": ((5.2, 0.4, 52.2), 356, 50, -38, 50),
        "close": ((5.2, 0.4, 52.2), 210, 24, -30, 45),
        "tower": ((29.2, -36.7, 80.0), 110, 15, -45, 45),
        "ingame": ((5.2, 0.4, 52.2), 809, 53, -62, 50),
    }

    def design(self, kit):
        out = []
        out += gallery(kit, LOW, 64.0, 1.6)
        out += gallery(kit, UP, 86.8, 2.0, bartizans=(85.4, 7.0, 5.0))
        import math

        from ..shapes import rail
        for k in range(8):                        # steel ribs up the dome's edges (vertices at k 45 degrees)
            th = k * math.pi / 4
            pts = [(T[0] + (r + 0.18) * math.cos(th), T[1] + (r + 0.18) * math.sin(th), z + 0.08) for z, r in DOME]
            out.append(rail(pts, 0.26, "trim", 0.16))
        out += kit.lantern(*T, 104.0, r=2.2, top=107.2)
        out += self._faces(kit)
        out += self._hall(kit)
        out += self._yard(kit)
        return out

    @staticmethod
    def _faces(kit):
        from mathutils import Vector as V
        out = kit.banner(V((0, -48.0, 0)), V((1, 0, 0)), V((0, -1, 0)), T[0], 62.6, 5.4, 20.0, d=1.0)
        out += kit.banner(V((40.52, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), T[1], 62.6, 5.4, 20.0, d=1.0)
        return out

    @staticmethod
    def _hall(kit):
        """The hall's front (y -45.95, x -1.9..17.9, walls to 27.8 under the eave at 29.9; its corner
        pier x -5.6..-1.9 stands out to -48.3) and, west of it, the paved terrace in front of the
        yard's south wall (y -28.4 facing south, to z 14; level 3 stands an arcade on it)."""
        from mathutils import Vector as V

        from ..motifs import closed, eave, ridge, roundel, star_frieze
        a, t, n = V((0, -45.95, 0)), V((1, 0, 0)), V((0, -1, 0))
        out = ridge((-3.6, -37.0, 38.7), (15.4, -37.0, 38.7), r=0.32, cresting=2.4, spike=1.9)
        out += closed(eave(a, t, n, -1.7, 17.6, 28.9, out=0.9, h=0.55, brackets=2.6))     # over the wall's top
        out += star_frieze(kit, a, t, n, -1.5, 17.4, 25.4, h=1.8, d1=0.45, count=6)
        out += roundel(kit, a, t, n, 7.95, 17.0, 3.4, d=0.3)
        out += roundel(kit, V((0, -28.4, 0)), t, n, -18.3, 7.2, 2.8, d=0.3)
        return out

    @staticmethod
    def _yard(kit):
        """Piers and roundels on the yard walls' outer faces (x 30.43 east, -31.16 west), under
        V2's raised walls (z 14 up)."""
        from mathutils import Vector as V

        from ..motifs import roundel, slab
        out = []
        for a, t, n, us, rs in ((V((30.43, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), (-5.0, 10.0, 25.0, 40.0), (2.5, 32.5)),
                                (V((-31.16, 0, 0)), V((0, -1, 0)), V((-1, 0, 0)), (-40.0, -25.0, -10.0, 5.0, 20.0), (-32.5, -2.5))):
            for u in us:
                out.append(slab(a, t, n, u - 1.1, u + 1.1, 0.0, 12.2, -0.25, 1.0, ("stoneB", "stoneB", None, "stoneB"), "stoneB"))
                out.append(slab(a, t, n, u - 1.35, u + 1.35, 12.2, 13.0, -0.25, 1.25, front="course"))
            for u in rs:
                out += roundel(kit, a, t, n, u, 7.0, 2.3, d=0.25)
        return out

    def variants(self, install):
        from ..levels import with_damaged    # EA's damaged ranges (D1-D3) draw GBArcheryN_LD
        return with_damaged(self, super().variants(install), "GBArcheryN_LD.tga")

    def decals(self):
        from ..paint import Keep, Slate, men_layers
        band = men_layers()[2]
        return [band(zrange=(67.4, 69.4), pitch=3.0, r=0.72), band(zrange=(90.2, 92.2), pitch=3.0, r=0.72),
                Slate(97.8), Slate(29.0, box=(-7.0, 19.0, -47.0, -27.0)),     # the dome's and the hall roof's tiles
                Keep()]                                                          # the red and white targets

    def emphasis(self, c, n):
        if c.z > 60:
            return 1.35                       # the tower's galleries, bartizans and dome
        return 1.0
