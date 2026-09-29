"""Men forge, level 2 (Upgrade_StructureLevel2: ShowSubObjects V1): the towers and yard walls V1,
redesigned on the finished forge (`base`; the chain and its rules: assets/men/levels.py).

EA's V1 (model coordinates): four square towers round the hall's corner piers (east x
22.85..32.31, west -32.17..-22.7; front y 6.41..16.75, back 32.39..42.73) to 47.71 under
pyramid caps to 51.87; a yard wall down each side (east x 25.36..29.68, west -29.95..-25.63,
y -35.41..6.87, 17.76 high, an inner ledge at 10.36); a chamfered shaft behind the hall
(x -10..10.7, y 22..42.8, to 48.35) that V2's belfry stands on. The towers stand on V1's
bounding box, so pieces on their outer faces pass it by up to `footprint_margin` (collision
comes from the INI). EA's house banner stands at about (30, -36): the east gallery stops
short of it; the weapon racks and the smith are inside the walls: nothing here reaches in.

What stands on it here:

    towers  a corbelled sable band under each pyramid's eave, pinnacles on its four corners, a
            steel mast, gilt orb and spike on its apex; slit windows and (front towers) a White
            Tree roundel on the faces the camera sees
    walls   along both yard walls' outer faces: two-step corbels, a slab with a sable band and
            square merlons with capstones on the outer edge; buttresses below

No cloth and no night lights (a level mesh: levels.py)."""
from ..levels import LevelMesh, chain, level_textures
from ..forge.building import NOT_BAKED

T_TOP, T_APEX = 47.71, 51.87
TOWERS = [((22.85, 32.31), (6.41, 16.75)), ((22.85, 32.31), (32.39, 42.73)),
          ((-32.17, -22.7), (6.41, 16.75)), ((-32.17, -22.7), (32.39, 42.73))]
WALLS = [(29.68, 1), (-29.95, -1)]                # outer face x, outward sign
WALL_Y, W_TOP = (-33.6, 5.9), 17.76               # the galleries' run (the towers from 6.41), the top


class ForgeLevel2(LevelMesh):
    source = "GBBlkSmith_SKN"
    target = "V1"
    base = chain("forge", 2)
    own_textures = level_textures("F", 2)
    bake_hidden = tuple(n for n in NOT_BAKED if n != "V1")
    footprint_margin = 1.0
    views = {
        "rts": ((0.0, 3.0, 26.0), 260, 50, -38, 50),
        "close": ((20.0, 5.0, 30.0), 150, 24, -34, 45),
        "tower": ((27.6, 11.6, 40.0), 80, 18, -40, 45),
        "ingame": ((-0.0, 0.1, 27.6), 555, 53, -62, 50),
    }

    def design(self, kit):
        from ..motifs import closed
        out = []
        for (x0, x1), (y0, y1) in TOWERS:
            out += self._tower(kit, x0, x1, y0, y1)
        for x, e in WALLS:
            out += self._wall(kit, x, e)
        return closed(out)

    @staticmethod
    def _tower(kit, x0, x1, y0, y1):
        from mathutils import Vector as V

        from sagekit.blender.geometry import sweep

        from ..motifs import corbel_table, roundel, window
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        ring = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        prof = [(-0.4, T_TOP - 2.0), (0.9, T_TOP - 2.0), (0.9, T_TOP), (-0.4, T_TOP)]
        out, segs = sweep(ring, prof, ["stoneB", "enamel", "top", None], center=(cx, cy))
        for a, b, t, n in segs:
            L = (b - a).length
            out += corbel_table(kit, V((a.x, a.y, 0)), t.to_3d(), n.to_3d(), 0.6, L - 0.6, T_TOP - 5.3, pitch=2.3,
                                w=0.4, d1=0.4, d2=0.9, h=1.65)
        for px, py in ((x0 + 0.5, y0 + 0.5), (x1 - 0.5, y0 + 0.5), (x1 - 0.5, y1 - 0.5), (x0 + 0.5, y1 - 0.5)):
            out += kit.pinnacle(px, py, T_TOP, T_TOP + 1.5, half=0.75, spire=2.8)
        out += kit.finial(cx, cy, T_APEX - 0.6, T_APEX + 3.4, T_APEX + 8.2)
        ex = 1 if cx > 0 else -1                   # the outer face, then the yard face (front towers)
        faces = [(V((x1 if ex > 0 else x0, 0, 0)), V((0, ex, 0)), V((ex, 0, 0)), ex * cy)]
        if cy < 20:
            faces.append((V((0, y0, 0)), V((1, 0, 0)), V((0, -1, 0)), cx))
        for a, t, n, u in faces:
            out += window(kit, a, t, n, u, 0.55, 27.0, 33.5, glass="slit", w=0.45, d=0.4)
            if cy < 20:
                out += roundel(kit, a, t, n, u, 38.6, 2.4, d=0.2)
        return out

    @staticmethod
    def _wall(kit, x, e):
        """The gallery along a yard wall's outer face (x, facing e): corbels from 12.5, a sable
        slab to the top, merlons; buttresses every 13 below."""
        from mathutils import Vector as V

        from ..motifs import corbel_table, slab
        n = V((e, 0, 0))
        t = V((-n.y, n.x, 0))
        a = V((x, 0, 0))
        y0, y1 = WALL_Y
        u0, u1 = sorted((e * y0, e * y1))
        out = corbel_table(kit, a, t, n, u0 + 0.6, u1 - 0.6, 12.4, pitch=2.8, w=0.45, d1=0.5, d2=1.0, h=1.5)
        out.append(slab(a, t, n, u0, u1, 15.4, W_TOP, -1.2, 1.0, ("stoneB", "stoneB", "top", "stoneB"), "enamel"))
        out += kit.merlons(a, t, n, u0 + 0.3, u1 - 0.3, W_TOP, -0.35, 0.95, w=2.1, gap=1.5, h=2.4)
        for u in (u0 + 6.0, (u0 + u1) / 2, u1 - 6.0):
            out.append(slab(a, t, n, u - 1.1, u + 1.1, 0.0, 11.6, -1.2, 0.8, ("stoneB", "stoneB", None, "stoneB"), "stoneB"))
            out.append(slab(a, t, n, u - 1.35, u + 1.35, 11.6, 12.4, -1.2, 1.0, front="course"))
        return out

    def decals(self):
        from ..paint import men_layers
        return [men_layers()[2](zrange=(15.4, 17.76), pitch=3.0, r=0.72),        # silver stars on the walls' bands
                men_layers()[2](zrange=(T_TOP - 2.0, T_TOP), pitch=2.6, r=0.66)]  # ... and the towers'

    @property
    def sheet_atlas(self):
        from ..prodkit import VET_TILES, with_tiles
        return with_tiles(super().sheet_atlas, VET_TILES)       # EA's slate caps stay slate

    def emphasis(self, c, n):
        if c.z > 40 or 12 < c.z < 21:
            return 1.35                      # the towers' crowns and the galleries
        return 1.0
