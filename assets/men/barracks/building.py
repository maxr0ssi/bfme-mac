"""Men barracks (GondorBarracks): EA's body kept whole - the square keep with its battered corner
buttresses, painted corbel arcade and ribbed slate dome, the gate porch on its north-east chamfer,
and the two crenellated wings round the drill yard - and dressed like the citadel.

EA's GBBarracks_SKN, body BARRACKS (1452 triangles), painted from gbbarracks_new.tga (own copy
gbbarracks_neH.tga); new faces sample the Men atlas (GBFortress1). BARRACKS mesh coordinates are the
model's. What EA's body is, measured (work/measure.json, slices):

    keep      centre (-19.85, -25.75); lower shaft about 17 half to z 50, a sloped weathering to the
              upper shaft (half 15.15, chamfer 4.2) at z 54.3; corner piers to z 60; the dome's eave
              at 64.5..65.6 (half 14.9), the dome to its point at 73.96
    porch     the gate porch on the keep's NE chamfer: its front the plane through (-3.55, -9.75)
              facing (0.71, 0.71), |u| <= 10.8, the gate |u| < 6.7 to its crown at about 37.5,
              the front's top at 44.8
    wings     east wing: south face y -42.36 (x -2..31), its end block x 17..39.6, y -41..-17.8 up
              to 36.1; north wing: courtyard face x -13.69 (y -9.9..30.3), west face x -36.7; the
              parapets' tops at 28.5 over a walkway at 25.5; windows z 11..19

What stands on it here:

    keep crown  a machicolated gallery on the upper shaft (corbels from the weathering, a slab with
                a sable band of silver stars, parapet and square merlons), a pinnacle over each
                corner pier; the dome's steel eave band, ribs, lantern, gilt orb and spike
    keep faces  two house-colour banners on the south face either side of EA's window, framed in a
                voussoir surround under a White Tree roundel; roundels on the west and east faces
    porch       pilasters, an archivolt with keystone, an entablature with the seven gilt stars and
                a pediment with the White Tree under a winged crest
    wings       square merlons with capstones on every parapet, surrounds round EA's windows, a
                house-colour banner on the yard face of the north wing

The level-up meshes are chained on this (assets/men/barracks_level2, _level3; levels.py): V1 (the
yard wall, level 2) hides the outer faces below z 20; V2 (level 3) sets a belfry storey on the
keep's eave (from z 65.3, half 14.9 to 16.5) and turrets on both end blocks (from z 30). So
everything here above 65.3 lies inside V2's storey (the dome dress, seen at levels 1-2), and the
end blocks carry nothing above the parapets.
"""
import math

from sagekit.building import Building

from ..style import MenStyle

C = (-19.85, -25.75)                     # the keep's centre
UPPER, CH = 15.15, 4.2                  # the upper shaft's half and chamfer
Z_CORBEL, Z_SLAB, Z_WALK, Z_PARAPET = 50.9, 54.5, 56.5, 57.7
OUT = 2.45                              # the gallery's front, out of the upper shaft
DOME = [(65.7, 14.4, 4.1), (67.0, 13.3, 3.8), (69.4, 10.95, 3.2), (71.2, 7.5, 2.1), (72.6, 3.3, 1.0)]
PORCH = ((-3.55, -9.75), (0.70711, 0.70711))
GATE = (6.9, 6.8, 31.0)                 # the archivolt's inner curve: half, rise, spring
NOT_BAKED = ("MANATARMS", "SOLDIER_SHIELD", "N_WINDOW", "V1", "V2")


class Barracks(Building):
    style = MenStyle()
    source = "GBBarracks_SKN"
    target = "BARRACKS"
    sheet = "gbbarracks_new.tga"
    sheet_normal = "gbbarracks_new_nrm.tga"
    own_textures = {"gbbarracks_new.tga": "gbbarracks_neH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    bake_hidden = NOT_BAKED
    views = {
        "rts": ((0.2, -2.3, 35.2), 320, 50, -38, 50),
        "close": ((0.2, -2.3, 35.2), 189, 24, -30, 45),
        "gate": ((-3.5, -9.7, 32.0), 120, 18, 45, 45),
        "crown": ((-19.85, -25.75, 58.0), 95, 22, -50, 45),
        "ingame": ((0.2, -2.3, 35.2), 726, 53, -62, 50),
    }

    def design(self, kit):
        out = []
        out += self._gallery(kit)
        out += self._dome(kit)
        out += self._keep_faces(kit)
        out += self._porch(kit)
        out += self._wings(kit)
        return out

    # ------------------------------------------------------------------ the keep's crown
    @staticmethod
    def _gallery(kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import sweep

        from .motifs import corbel_table, octagon
        cx, cy = C
        path = octagon(cx, cy, UPPER, CH)
        slab = [(-2.0, Z_SLAB), (OUT, Z_SLAB), (OUT, Z_WALK), (-2.0, Z_WALK)]
        out, segs = sweep(path, slab, ["stoneB", "enamel", "top", None], center=C)
        par = [(OUT - 1.15, Z_WALK - 0.1), (OUT - 0.1, Z_WALK - 0.1), (OUT - 0.1, Z_PARAPET), (OUT - 1.15, Z_PARAPET)]
        out += sweep(path, par, [None, "stoneA", "top", "stoneA"], center=C)[0]
        for a, b, t, n in segs:
            L = (b - a).length
            a3 = V((a.x, a.y, 0))
            if L < 10:                       # a chamfer: a pinnacle over EA's corner pier
                m = (a3 + V((b.x, b.y, 0))) / 2 + n.to_3d() * 1.35
                out += kit.pinnacle(m.x, m.y, Z_WALK, Z_PARAPET + 3.4, half=1.2, spire=4.2)
                continue
            out += corbel_table(kit, a3, t.to_3d(), n.to_3d(), 0.3, L - 0.3, Z_CORBEL, pitch=3.1, d1=1.9, d2=OUT, h=1.8)
            out += kit.merlons(a3, t.to_3d(), n.to_3d(), 0.35, L - 0.35, Z_PARAPET, OUT - 1.15, OUT - 0.1, w=2.2, gap=1.6, h=2.6)
        return out

    @staticmethod
    def _dome(kit):
        from .motifs import crown_dome
        return crown_dome(kit, *C, DOME, eave=(65.05, 14.95, 4.2), lantern=(72.0, 2.9, 76.2), finial=(80.4, 88.5))

    @staticmethod
    def _keep_faces(kit):
        """The south face (battered: y = 0.03 z - 44.2, so anchored at each piece's height) between its
        corner buttresses: EA's window framed, a roundel over it, a banner either side. A roundel on
        the west face (x = 0.03 z - 38.29)."""
        from mathutils import Vector as V

        from .motifs import roundel, window_surround
        out = []
        t, n = V((1, 0, 0)), V((0, -1, 0))
        def south(z):
            return V((0, 0.03 * z - 44.2, 0))
        out += window_surround(kit, south(31.5), t, n, -21.6, 1.05, 27.6, 34.8, w=0.65, d=0.6, hood=True)
        out += roundel(kit, south(42.3), t, n, -21.6, 42.3, 3.3, d=0.3)
        for u in (-29.2, -14.0):
            out += kit.banner(south(49.2), t, n, u, 49.2, 5.4, 17.0, d=1.0)
        a, t, n = V((0.03 * 40.5 - 38.29, 0, 0)), V((0, -1, 0)), V((-1, 0, 0))
        out += roundel(kit, a, t, n, 25.75, 40.5, 3.3, d=0.3)
        return out

    # ------------------------------------------------------------------ the gate porch
    @staticmethod
    def _porch(kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz

        from .motifs import slab, star_frieze
        (px, py), (nx, ny) = PORCH
        a, n = V((px, py, 0)), V((nx, ny, 0))
        t = V((-ny, nx, 0))
        out = []
        for e in (-1, 1):                         # pilasters either side of the gate
            u0, u1 = sorted((e * 7.2, e * 10.4))
            out.append(slab(a, t, n, u0 - 0.3, u1 + 0.3, 0.0, 2.2, -0.25, 1.75, front="stoneB"))
            out.append(slab(a, t, n, u0, u1, 2.2, 30.0, -0.25, 1.35, ("stoneB", "stoneB", None, "stoneB"), "stoneA"))
            out.append(slab(a, t, n, u0 + 0.7, u1 - 0.7, 4.5, 28.0, 1.2, 1.55, ("stoneB", "stoneB", "stoneB", "stoneB"), "stoneB"))
            out.append(slab(a, t, n, u0 - 0.35, u1 + 0.35, 30.0, 31.0, -0.25, 1.8, front="course"))
        h, r, s = GATE
        out += kit.voussoirs(a, t, n, (h, r, s), (h + 2.5, r + 2.5, s), -0.25, 1.4, count=11, key=(1.3, 41.9, 0.5))
        for e in (-1, 1):                         # spandrels up to the architrave
            u0, u1 = sorted((e * (h + 2.3), e * 10.8))
            out.append(slab(a, t, n, u0, u1, 31.0, 41.6, -0.25, 1.0, (None, "stoneB", None, "stoneB"), "stoneA"))
        out.append(slab(a, t, n, -11.2, 11.2, 41.6, 42.4, -0.25, 1.6, front="course"))
        out += star_frieze(kit, a, t, n, -11.0, 11.0, 42.4, h=2.0, d1=1.35, count=7)
        out.append(slab(a, t, n, -11.8, 11.8, 44.4, 45.4, -0.25, 2.0, ("stoneB", "stoneB", "top", "stoneB"), "course"))
        z0, apex, half = 45.4, 50.6, 10.8
        out.append(prism_uz(a, t, n, [(-half, z0), (half, z0), (0, apex)], -2.5, 1.2, [None, "stoneB", "stoneB"], "enamel", "stoneB"))
        for e in (-1, 1):
            poly = [(0, apex), (e * half, z0), (e * (half + 1.1), z0), (0, apex + 1.2)]
            out.append(prism_uz(a, t, n, poly, -2.6, 1.9, ["stoneB", "stoneB", "slate", None], "course", "stoneB"))
            c = a + t * (e * (half + 0.2)) + n * 0.6
            out += kit.pinnacle(c.x, c.y, z0, z0 + 1.6, half=0.8, spire=2.8)
        out += kit.white_tree(a, t, n, 0.0, 45.7, 4.2, 1.3, r=0.16)
        out += kit.winged_crest(a, t, n, 0.0, apex + 0.9, -0.6, 1.4, s=0.8)
        return out

    # ------------------------------------------------------------------ the wings
    @staticmethod
    def _wings(kit):
        from mathutils import Vector as V

        from .motifs import window_surround
        out = []
        # each parapet face, battered: (face at height z, t, n, merlon runs (u0, u1), windows at u),
        # t x n = -z; the end blocks (x >= 17, y >= 21) carry V2's turrets at level 3
        faces = [(lambda z: (0, 0.05 * z - 42.36), (1, 0), (0, -1), [(0.4, 16.4)], [9.4, 25.3]),     # east wing, south
                 (lambda z: (0, -16.23 - 0.05 * z), (-1, 0), (0, 1), [(-16.4, -8.6)], []),          # east wing, yard
                 (lambda z: (-13.69 - 0.02 * z, 0), (0, 1), (1, 0), [(0.6, 20.4)], [3.4, 17.1, 30.2]),  # north wing, yard
                 (lambda z: (0.05 * z - 36.67, 0), (0, -1), (-1, 0), [(-20.6, 7.4)], [])]            # north wing, west
        for at, (tx, ty), (nx, ny), runs, wins in faces:
            t, n = V((tx, ty, 0)), V((nx, ny, 0))
            a = V((*at(28.5), 0))
            for u0, u1 in runs:
                out += kit.merlons(a, t, n, u0, u1, 28.5, -1.4, 0.25, w=2.2, gap=1.6, h=2.6)
            a = V((*at(14.4), 0))
            for u in wins:
                out += window_surround(kit, a, t, n, u, 1.1, 11.2, 17.6, w=0.6, d=0.5)
        a, t, n = V((-13.69 - 0.02 * 24.5, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        out += kit.banner(a, t, n, 10.2, 24.0, 4.8, 12.5, d=0.9)
        return out

    def variants(self, install):
        from .levels import with_damaged           # EA's damaged barracks (D1-D3) draw GBBarracks_NewD
        return with_damaged(self, super().variants(install), "GBBarracks_NewD.tga")

    def decals(self):
        from ..paint import men_layers
        from .paintkit import Slate
        return [men_layers()[2](zrange=(Z_SLAB, Z_WALK), pitch=3.1, r=0.72),    # silver stars on the gallery's band
                Slate(65.4)]                                                     # the dome's tiles in charcoal slate

    def emphasis(self, c, n):
        if c.z > 50:
            return 1.35                       # the keep's crown and dome
        if abs((c.x - PORCH[0][0]) * 0.7071 + (c.y - PORCH[0][1]) * 0.7071) < 3 and c.z > 28:
            return 1.3                        # the porch's archivolt, frieze and pediment
        return 1.0
