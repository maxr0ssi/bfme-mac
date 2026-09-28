"""The Gondor farm at level 2 (FarmInterface's SubObjectsUpgrade: V1 shown, V1HIDE hidden): the
yard wall, redesigned on the finished farm (`base`; the chain's rules: assets/men/barracks/
levels.py). EA's V1 is a thick low stone wall round the yard with a timber palisade of sawtooth
stakes along its middle, tall pointed posts at the corners and an arched gate in the west wall.
Now, in the Pelennor's stone:

    gate        a voussoir archivolt with a raised keystone round the arch on both faces, a
                stone pediment over it with the White Tree on a sable field, and a pinnacle on
                each gate pier
    piers       dressed stone piers against the wall's outer faces (four on the long walls, two
                on each short one), each with a moulded cap and a steel-ringed stone ball

EA's palisade and corner posts stay. No cloth and no lights (a level mesh). Painted from our
own copy of GBFarm, GBFarW (the body's is GBFarH).

EA's V1 (mesh = model coordinates): the wall's outer faces x -48.44 (west), 43.04 (east),
y -34.99 (south), 35.72 (north), its inner faces about 5 in, its top about 13, the palisade
(1.3 thick, in the middle) to about 18; the gate's opening y -6.35..5.54 to its springing at
14.5, crown 20.2, its front x -48.76 (yard face -42.41), its top 22.8. The piers stand 0.9
out of the wall's faces (footprint_margin: the wall's collision is the building's)."""
from ..barracks.levels import LevelMesh, chain

# EA's timber on GBFarm (Blender UV, v up, modulo 1): the palisade stakes' planks and the corner posts' strip
STAKES = [(0.21, 0.24, 0.27, 0.41), (0.0, 0.455, 0.27, 0.5)]
GATE = (-48.76, -42.41, -0.4, 6.1, 14.5, 5.7, 22.8)     # x out, x yard, y centre, half, spring, rise, top
FACES = {"W": ((-48.44, 0.0), (-1, 0), (-22.0, 22.0)), "E": ((43.04, 0.0), (1, 0), (-18.0, 18.0)),
         "S": ((-2.7, -34.99), (0, -1), (-30.0, -10.0, 10.0, 30.0)), "N": ((-2.7, 35.72), (0, 1), (-30.0, -10.0, 10.0, 30.0))}


class FarmLevel2(LevelMesh):
    source = "GBFarm_SKN"
    target = "V1"
    base = chain("farm", 2)
    sheet = "GBFarm.tga"
    sheet_normal = "GBFarm_NRM.tga"
    own_textures = {"GBFarm.tga": "GBFarW.tga"}
    footprint_margin = 1.1
    bake_hidden = ("V2", "V1HIDE", "N_WINDOW")          # level 2: V2HIDE (the thatch) still shows
    views = {
        "rts": ((-1.1, 0.1, 11.8), 262, 50, -38, 50),
        "close": ((-10.0, -20.0, 10.0), 120, 22, -40, 45),
        "gate": ((-48.0, 0.0, 14.0), 70, 14, 170, 45),
        "ingame": ((-1.1, 0.1, 11.8), 595, 53, -62, 50),
    }

    def variants(self, install):
        from ..workshop.prodkit import same_length_variants
        return same_length_variants(self, install, super().variants(install))

    def decals(self):
        from ..workshop.prodkit import props_layer
        return [props_layer(sat=(0.12, 0.22), gate=(0.4, 0.65), hue=(22.0, 50.0), rects=STAKES)]          # EA's palisade and posts stay timber

    def design(self, kit):
        out = self._gate(kit)
        for key, (p, nrm, us) in FACES.items():
            out += self._piers(kit, p, nrm, us)
        from ..workshop.prodkit import closed
        return closed(out)                  # EA's wall faces are open planes behind the piers

    @staticmethod
    def _gate(kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz
        from ..barracks import motifs as M
        xo, xy, yc, half, spring, rise, top = GATE
        out = []
        for x, nx in ((xo, -1), (xy, 1)):
            a, t, n = M.face((x, yc), (nx, 0))
            inner, outer = (half + 0.3, rise + 0.2, spring), (half + 1.6, rise + 1.5, spring)
            out += kit.voussoirs(a, t, n, inner, outer, -0.6, 0.6, count=9, key=(0.9, top - 0.3, 0.3))
        # the pediment over the gate, on its top (both faces)
        a, t, n = V((xo, yc, 0)), V((0, -1, 0)), V((-1, 0, 0))
        w = half + 2.6
        d0, d1 = -(xy - xo) + 0.2, 0.5
        out.append(M.slab(a, t, n, -w, w, top - 0.2, top + 0.7, d0 - 0.2, d1 + 0.2, front="course", back="course"))
        apex = top + 0.7 + 3.4
        out.append(prism_uz(a, t, n, [(-w + 0.3, top + 0.7), (w - 0.3, top + 0.7), (0, apex)], d0, d1,
                            [None, "stoneB", "stoneB"], "enamel", "enamel"))
        for e in (-1, 1):
            poly = [(0, apex), (e * (w - 0.3), top + 0.7), (e * (w + 0.5), top + 0.7), (0, apex + 0.9)]
            out.append(prism_uz(a, t, n, poly, d0 - 0.15, d1 + 0.15, ["stoneB", "stoneB", "top", None], "course", "course"))
        out += kit.white_tree(a, t, n, 0.0, top + 1.0, 2.6, d1 - 0.05, r=0.11)
        b = V((xy, yc, 0))
        out += kit.white_tree(b, -t, -n, 0.0, top + 1.0, 2.6, -0.15, r=0.11)
        c = (xo + xy) / 2
        out += kit.pinnacle(c, yc, apex + 0.4, apex + 1.4, half=0.7, spire=2.4)
        for e in (-1, 1):
            out += kit.pinnacle(c, yc + e * (w - 0.6), top + 0.7, top + 2.2, half=0.8, spire=2.6)
        return out

    @staticmethod
    def _piers(kit, p, nrm, us):
        from ..barracks import motifs as M
        from ..shapes import turned
        a, t, n = M.face(p, nrm)
        out = []
        for w in us:                        # world x (south, north) or y (west, east) along the face
            q = (w, p[1]) if nrm[0] == 0 else (p[0], w)
            u = (q[0] - a.x) * t.x + (q[1] - a.y) * t.y
            out.append(M.slab(a, t, n, u - 1.1, u + 1.1, 0.35, 14.2, -0.4, 0.75, ("stoneB", "stoneB", None, "stoneB"), "stoneB"))
            out.append(M.slab(a, t, n, u - 1.4, u + 1.4, 14.2, 15.0, -0.4, 0.95, front="course"))
            c = a + t * u + n * 0.1
            out.append(turned(c.x, c.y, [(0.5, 14.9), (0.85, 15.4), (0.95, 16.2), (0.85, 17.0), (0.45, 17.5), (0.0, 17.7)],
                              ["trim", "stoneA", "stoneA", "stoneA", "stoneA"], k=8, cap0=("trim", True), cap1=("top", False)))
        return out
