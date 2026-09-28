"""Men stable, level 2 (Upgrade_StructureLevel2: ShowSubObjects V1): the yard wall V1, redesigned
on the finished stable (`base`; the chain and its rules: assets/men/barracks/levels.py) in the
citadel's wall language.

EA's V1 (model coordinates; V1 hangs on no bone): two curved walls from the wings' gable ends
round the yard to its gate, 19.86 high with a flat top about 8 wide (a painted crenellation on
the faces), and over the gate a round arch on two piers (x 41.4..44.8 at their foot, the arch's
faces x 40.31 and 45.88, its intrados crown at 50.36 and extrados at 53.47 over y 0.49, midway
between the piers' tops y 16.43..21.74 and -20.77..-15.46). EA's iron gate leaves stand at x 46.8..48.2,
|y| < 14, z 0..17 (they swing: kept clear); the horse on the walker circles within 25 of
(13.3, 0), inside the walls' inner edge (30 out): nothing here reaches inwards. The two arcs
are not mirror images; each is given by its outer top edge:

    north   (5.0, 38.6) (10.47, 39.8) (22.64, 39.25) (38.81, 32.93) (44.5, 26.2)
    south   (6.0, -39.7) (11.54, -41.32) (22.55, -39.87) (38.82, -32.7) (44.6, -25.9)

What stands on it here:

    gallery along both arcs' outer faces: two-step corbels from z 14.3, a slab standing out with
            a sable band of silver stars, square merlons with capstones on the wall top's outer edge
    faces   buttresses at the ends of each run, capped under the corbels, and a White Tree
            roundel in the middle of each long run
    arch    a keystone on each face of the gate arch's crown, a winged crest on its top,
            pinnacles on its haunches over the piers and moulded bands round both legs

No cloth and no night lights (a level mesh: levels.py). Footprint = V1's bounding box."""
from ..barracks.levels import LevelMesh, chain, level_textures
from ..stable.building import NOT_BAKED

Z_TOP, Z_CORBEL, Z_SLAB = 19.86, 14.3, 17.4
OUT = 0.8                                        # the slab's front, out of the outer face
NORTH = [(5.0, 38.6), (10.47, 39.8), (22.64, 39.25), (38.81, 32.93), (44.5, 26.2)]
SOUTH = [(6.0, -39.7), (11.54, -41.32), (22.55, -39.87), (38.82, -32.7), (44.6, -25.9)]
YARD = (13.3, -0.56)                             # inside both arcs: the sweeps' outward normals point away
ARCH = (40.31, 45.88, 0.49, 50.36, 53.47)        # faces x, crown y, intrados and extrados crown z
HAUNCH = (18.6, 44.9)
LEGS = [((41.1, 45.1), (15.2, 22.0)), ((41.1, 45.1), (-21.1, -15.2))]    # a band's box round each leg                            # |y - crown| and z of the arch's top over the piers


class StableLevel2(LevelMesh):
    source = "GBStable_SKN"
    target = "V1"
    base = chain("stable", 2)
    own_textures = level_textures("S", 2)
    bake_hidden = tuple(n for n in NOT_BAKED if n != "V1")
    footprint_margin = 0.3                       # merlon capstones on the walls' outer top edge (EA's foot sets the box)
    views = {
        "rts": ((20.0, 0.0, 22.0), 330, 50, -38, 50),
        "close": ((30.0, -10.0, 20.0), 170, 24, -34, 45),
        "gate": ((43.0, -0.5, 30.0), 110, 16, -8, 45),
        "ingame": ((2.8, -0.7, 28.5), 837, 53, -62, 50),
    }

    def design(self, kit):
        from ..barracks.motifs import closed
        out = []
        for path in (NORTH, SOUTH):
            out += self._gallery(kit, path)
        out += self._arch(kit)
        return closed(out)

    @staticmethod
    def _gallery(kit, path):
        """The gallery along one arc's outer top edge: a sable-fronted slab on corbels, merlons on
        its top edge, buttresses on the face below (one per segment, two on the long ones)."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import sweep

        from ..barracks.motifs import corbel_table, roundel, slab
        prof = [(-1.2, Z_SLAB), (OUT, Z_SLAB), (OUT, Z_TOP), (-1.2, Z_TOP)]
        out, segs = sweep(path, prof, ["stoneB", "enamel", "top", None], center=YARD)
        for a, b, t, n in segs:
            L = (b - a).length
            a3, t3, n3 = V((a.x, a.y, 0)), t.to_3d(), n.to_3d()
            out += corbel_table(kit, a3, t3, n3, 0.5, L - 0.5, Z_CORBEL, pitch=2.9, w=0.5, d1=0.55, d2=OUT, h=1.55)
            out += kit.merlons(a3, t3, n3, 0.4, L - 0.4, Z_TOP, -0.35, OUT - 0.05, w=2.2, gap=1.5, h=2.6)
            if L > 14:                            # a White Tree roundel in the middle of each long run
                out += roundel(kit, a3, t3, n3, L / 2, 8.4, 2.4, d=0.2, back=-0.6)
            for u in (1.6, L - 1.6):              # buttresses at the runs' ends
                out.append(slab(a3, t3, n3, u - 1.2, u + 1.2, 0.0, 12.9, -1.6, 0.6, ("stoneB", "stoneB", None, "stoneB"),
                                "stoneB", None))
                out.append(slab(a3, t3, n3, u - 1.45, u + 1.45, 12.9, 13.7, -1.6, 0.8, front="course"))
        return out

    @staticmethod
    def _arch(kit):
        """Keystones on both faces of the crown, a winged crest on its top (standing on the
        extrados, clear of EA's gate leaves far below), pinnacles over the piers."""
        from mathutils import Vector as V

        from ..stable.pieces import keystone
        x0, x1, yc, zi, ze = ARCH
        out = []
        for x, nx in ((x1, 1.0), (x0, -1.0)):
            n = V((nx, 0, 0))
            t = V((-n.y, n.x, 0))
            a = V((x, 0, 0))
            u = yc * (1 if nx > 0 else -1)
            out += keystone(a, t, n, u, zi - 0.4, ze + 0.9, half0=0.9, half1=1.35, d0=-0.4, d1=0.55)
        a, t, n = V((x1, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        out += kit.winged_crest(a, t, n, yc, ze + 0.85, -(x1 - x0) + 0.9, -0.9, s=1.0)
        dy, zh = HAUNCH
        for e in (-1, 1):
            out += kit.pinnacle((x0 + x1) / 2, yc + e * dy, zh - 0.4, zh + 1.6, half=1.1, spire=3.8)
        from sagekit.blender.geometry import box_rings, loft
        for (lx0, lx1), (ly0, ly1) in LEGS:          # moulded bands round the legs at the wall tops and half way
            for z0, z1 in ((19.6, 20.9), (35.0, 36.0)):
                out.append(loft([box_rings((lx0, lx1), (ly0, ly1), z0, 0), box_rings((lx0, lx1), (ly0, ly1), z1, 0)],
                                ["course"], cap0=("stoneB", True), cap1=("top", True)))
        return out

    def decals(self):
        from ..paint import men_layers
        return [men_layers()[2](zrange=(Z_SLAB, Z_TOP), pitch=3.0, r=0.72)]   # silver stars on the gallery's band

    @property
    def sheet_atlas(self):
        from ..workshop.prodkit import VET_TILES, with_tiles
        return with_tiles(super().sheet_atlas, VET_TILES)       # EA's slate caps stay slate

    def emphasis(self, c, n):
        if c.z > 13.5:
            return 1.35                      # the gallery, merlons and the arch's crown
        return 1.0
