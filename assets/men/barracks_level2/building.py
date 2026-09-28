"""Men barracks, level 2 (Upgrade_GondorBarracksLevel2: ShowSubObjects V1): the yard wall V1,
redesigned on the finished barracks (`base`, levels.py) in the citadel's wall language.

EA's V1 is one battered wall, 19.9 high with a painted crenellation, round the whole barracks: its
outer faces lean in from the footprint's edge (south y = 0.0995 z - 49.63, east x = 44.97 - 0.111 z,
west x = 0.103 z - 42.98, north y = 47.48 - 0.0746 z), its yard side buried in the keep and the wings
except on the east wall (x = 31.4 + 0.081 z, y -23..13) and the north wall (y = 34 + 0.0625 z,
x -20.6..15.6). The entrance is the north-east gap between the north wall's rounded end (x 13..25,
y 34..47) and the east wall's (x 31..45, y 13..21). A flag pole (for V1FLAG, which the model has
not) stands on the keep's dome, where the body's lantern and spike now are: it goes (`clear`).

What stands on it here:

    gallery     round the four outer faces: corbels from z 14, a slab standing 1.1 out (its front a
                sable band of silver stars) and square merlons with capstones on it
    buttresses  upright piers every 14 up the battered faces, capped under the corbels
    bays        White Tree roundels and arrow slits in steel-framed surrounds, alternately
    gate towers the two rounded wall ends become square towers flanking the entrance: battered,
                a corbelled crown with a sable band, merlons, corner pinnacles and a slate spire
                with a steel finial; a roundel on each outward face

No cloth and no night lights (a level mesh: levels.py). Footprint = V1's bounding box."""
from ..barracks.building import NOT_BAKED
from ..barracks.levels import LevelMesh, chain, level_textures

Z_TOP, Z_CORBEL, Z_SLAB = 19.87, 14.0, 17.3
OUT = 1.1                                        # the slab's front, out of the face at z 17
FACES = {                                        # outer faces: position at height z, t, n (t x n = -z)
    "S": (lambda z: (0.0, 0.0995 * z - 49.63), (1, 0), (0, -1)),
    "E": (lambda z: (44.97 - 0.111 * z, 0.0), (0, 1), (1, 0)),
    "W": (lambda z: (0.103 * z - 42.98, 0.0), (0, -1), (-1, 0)),
    "N": (lambda z: (0.0, 47.48 - 0.0746 * z), (-1, 0), (0, 1)),
}
PIERS = {"S": (-34, -20, -6, 8, 22, 36), "E": (-40, -26, -12, 2), "W": (-36, -22, -8, 6, 20, 34), "N": (34, 20, 6, -8)}
TOWERS = {"E": ((31.3, 44.86), (7.4, 20.9)), "N": ((13.3, 24.8), (33.8, 47.35))}     # base rects (x, y)
TOWER = (0.8, 22.0)                              # batter to z 22, then the crown


def frame(name, z):
    from mathutils import Vector as V
    at, t, n = FACES[name]
    return V((*at(z), 0)), V((*t, 0)), V((*n, 0))


class BarracksLevel2(LevelMesh):
    source = "GBBarracks_SKN"
    target = "V1"
    base = chain("barracks", 2)
    own_textures = level_textures("B", 2)
    bake_hidden = NOT_BAKED[:-2] + ("V2",)
    views = {
        "rts": ((0.2, -2.3, 30.0), 330, 50, -38, 50),
        "close": ((10, -20, 15), 190, 22, -30, 45),
        "gate": ((28, 26, 18), 120, 20, 50, 45),
        "ingame": ((0.2, -2.3, 35.2), 726, 53, -62, 50),
    }

    @property
    def clear(self):
        from sagekit.clear import Box
        return [Box((-21.0, -27.0, 73.0), (-18.5, -24.3, 87.0))]          # the pole on the keep's dome

    def design(self, kit):
        out = []
        out += self._gallery(kit)
        out += self._bays(kit)
        for name in TOWERS:
            out += self._tower(kit, name)
        from ..barracks.motifs import closed
        return closed(out)

    @staticmethod
    def _gallery(kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import sweep

        from ..barracks.motifs import corbel_table
        e, n_ = FACES["E"][0](17.0)[0], FACES["N"][0](17.0)[1]
        w, s = FACES["W"][0](17.0)[0], FACES["S"][0](17.0)[1]
        path = [(TOWERS["N"][0][0] + 0.2, n_), (w, n_), (w, s), (e, s), (e, TOWERS["E"][1][0] - 0.2)]
        prof = [(-1.2, Z_SLAB), (OUT, Z_SLAB), (OUT, Z_TOP), (-1.2, Z_TOP)]
        out, segs = sweep(path, prof, ["stoneB", "enamel", "top", None], center=(0, 0))
        for a, b, t, n in segs:
            L = (b - a).length
            a3, t3, n3 = V((a.x, a.y, 0)), t.to_3d(), n.to_3d()
            out += corbel_table(kit, a3, t3, n3, 0.6, L - 0.6, Z_CORBEL, pitch=2.9, w=0.5, d1=0.55, d2=OUT, h=1.65)
            out += kit.merlons(a3, t3, n3, 0.3, L - 0.3, Z_TOP, -0.35, OUT - 0.05, w=2.2, gap=1.5, h=2.6)
        return out

    @staticmethod
    def _bays(kit):
        """Upright piers every 14 (their fronts on the footprint's edge, so they stand out of the
        battered face as it leans back) and, between them on the faces the camera sees (south and
        east), White Tree roundels and arrow slits in turn."""
        from ..barracks.motifs import roundel, slab, window
        out = []
        for name, us in PIERS.items():
            a0, t, n = frame(name, 0.0)
            for u in us:
                out.append(slab(a0, t, n, u - 1.3, u + 1.3, 0.0, 12.6, -1.8, -0.15, ("stoneB", "stoneB", None, "stoneB"), "stoneB"))
                out.append(slab(a0, t, n, u - 1.55, u + 1.55, 12.6, 13.4, -1.8, 0.1, front="course"))
            if name not in ("S", "E"):
                continue
            a, t, n = frame(name, 8.0)
            for i, (u0, u1) in enumerate(zip(us, us[1:])):
                m = (u0 + u1) / 2
                if i % 2 == 0:
                    out += roundel(kit, a, t, n, m, 8.0, 2.4, d=0.25, studs=False, back=-0.9)
                else:
                    out += window(kit, a, t, n, m, 0.45, 5.0, 10.6, rise=0.45, glass="slit", w=0.5, d=0.45, back=-0.9)
        return out

    @staticmethod
    def _tower(kit, name):
        """A gate tower round a rounded wall end: battered to z 22, a corbelled crown (a band of
        corbels, a sable slab, merlons with capstones), pinnacles on its corners and a slate spire
        with a steel finial in the middle; a roundel on each face but the one on the wall."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import box_rings, loft

        from ..barracks.motifs import roundel, window
        (x0, x1), (y0, y1) = TOWERS[name]
        k, zc = TOWER

        def R(e, z):
            return box_rings((x0 + e, x1 - e), (y0 + e, y1 - e), z, 0)
        out = [loft([R(0, 0.0), R(k, zc)], ["stoneA"], cap0=("stoneB", False), cap1=("top", False))]
        rings = [R(k, zc), R(k - 0.6, zc), R(k - 0.6, zc + 0.9), R(k - 0.1, zc + 0.9), R(0.0, zc + 2.6), R(0.0, zc + 4.4),
                 R(k + 1.1, zc + 4.4)]
        out.append(loft(rings, ["course", "course", "stoneB", "stoneB", "enamel", "top"], cap0=("stoneB", False), cap1=("top", True)))
        zt = zc + 4.4
        for (ax, ay), (tx, ty), L in (((x0, y0), (1, 0), x1 - x0), ((x1, y0), (0, 1), y1 - y0),
                                      ((x1, y1), (-1, 0), x1 - x0), ((x0, y1), (0, -1), y1 - y0)):
            a, t = V((ax, ay, 0)), V((tx, ty, 0))
            n = V((t.y, -t.x, 0))
            out += kit.merlons(a, t, n, 2.4, L - 2.4, zt, -1.3, 0.0, w=1.9, gap=1.4, h=2.5)
        for cx, cy in ((x0 + 1.5, y0 + 1.5), (x1 - 1.5, y0 + 1.5), (x1 - 1.5, y1 - 1.5), (x0 + 1.5, y1 - 1.5)):
            out += kit.pinnacle(cx, cy, zt, zt + 3.4, half=1.15, spire=4.6)
        cx, cy, h = (x0 + x1) / 2, (y0 + y1) / 2, min(x1 - x0, y1 - y0) / 2 - 2.6
        base = [box_rings((cx - h, cx + h), (cy - h, cy + h), zt - 0.2, 0), box_rings((cx - h, cx + h), (cy - h, cy + h), zt + 1.6, 0)]
        out.append(loft(base, ["stoneB"], cap0=("stoneB", False), cap1=("top", False)))
        out.append(loft([box_rings((cx - h - 0.4, cx + h + 0.4), (cy - h - 0.4, cy + h + 0.4), zt + 1.6, 0), [V((cx, cy, zt + 11.5))] * 4],
                        ["slate"], cap0=("slate", True), cap1=("top", False)))
        out += kit.finial(cx, cy, zt + 9.8, zt + 13.0, zt + 18.5)
        faces = {"E": [((x1, 0), (1, 0)), ((0, y1), (0, 1))], "N": [((0, y1), (0, 1)), ((x1, 0), (1, 0))]}[name]
        for (px, py), (nx, ny) in faces:
            n, t = V((nx, ny, 0)), V((-ny, nx, 0))
            z = 17.8                                # high on the battered face: inside V1's extent
            d = k * z / zc
            a = V((x1 - d, 0, 0)) if nx else V((0, y1 - d, 0))
            u = cy if nx else -cx
            out += roundel(kit, a, t, n, u, z, 2.6, d=0.0, back=-0.5)
            z = 7.5                                 # an arrow slit under it
            a = V((x1 - k * z / zc, 0, 0)) if nx else V((0, y1 - k * z / zc, 0))
            out += window(kit, a, t, n, u, 0.45, 4.5, 10.5, rise=0.45, glass="slit", w=0.45, d=0.12, back=-0.6)
        return out

    def decals(self):
        from ..paint import men_layers
        return [men_layers()[2](zrange=(Z_SLAB, Z_TOP), pitch=2.9, r=0.68)]     # silver stars on the gallery's band

    def emphasis(self, c, n):
        if c.z > 13.5:
            return 1.35                      # the gallery, merlons and the gate towers' crowns
        return 1.0
