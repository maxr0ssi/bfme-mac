"""The Angmar kit's forged tine (a mixin of AngmarShapes, assets/angmar/shapes.py): one point of
the Witch-king's crown made as a quality piece (Max on the citadel's pass 3: fewer tines, "4 more
detailed ones", and "ice cold tips, like frozen style").

A forged tine is a CrownTine (shapes_crown.py) given a ten-sided section: steel bevels at both
cutting edges, flat faces, and a raised spine down the outer face; barbs hooking up off both edges;
riveted iron bands round its root where it rises above the walk; a rune groove down the spine
glowing faint cold blue; and a frozen tip: from `frost` up the iron is cased in ice under a ragged
frost line, white rime on the last stretch to the point, ice crystals (the wall-foot clusters'
shards) growing up out of the casing and a few out of the iron below it, icicles hanging off the
barbs, as if the iron froze from the point down.

    forged_tine(h, barbs, bands, rune, frost)
        h       a CrownTine
        barbs   [(z, edge, depth)] as crown_tine's
        bands   [z]: a riveted band 2.4 tall at each height
        rune    (z0, z1): the glowing groove's run up the spine
        frost   z: where the ice casing starts
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft

# the section: (along the ring as a fraction of the half width W, across as a fraction of the half
# depth D), the outer face (+D) first carrying the spine
SECTION = ((1.0, 0.0), (0.72, 0.42), (0.22, 0.72), (0.0, 1.2), (-0.22, 0.72), (-0.72, 0.42), (-1.0, 0.0),
           (-0.72, -0.42), (0.0, -0.72), (0.72, -0.42))
EDGE_SIDES = (0, 5, 6, 9)            # the bevels at the two cutting edges


def _h(*xs):
    v = math.sin(sum(x * (12.9898 + 7.233 * i) for i, x in enumerate(xs))) * 43758.5453
    return v - math.floor(v)


class TineKit:
    def tine_ring(self, h, z, wr=1.0, wl=1.0, grow=1.0, dgrow=1.0):
        W, D = h.section(z)
        return [h.point(z, a * W * (wr if a > 0 else wl) * grow, b * D * dgrow) for a, b in SECTION]

    def forged_tine(self, h, barbs=(), bands=(), rune=None, frost=None, tag="iron", edge="steel", seed=0.0):
        out = []
        zs = {round(k[0], 3): [1.0, 1.0] for k in h.keys}
        for z, side, dep in barbs:
            i = 0 if side > 0 else 1
            zs.setdefault(round(z - 3.5, 3), [1.0, 1.0])
            zs.setdefault(round(z, 3), [1.0, 1.0])[i] = 1.0 + dep
            zs.setdefault(round(z + 0.8, 3), [1.0, 1.0])[i] = 0.9
        if frost is not None:
            zs.setdefault(round(frost, 3), [1.0, 1.0])
        top = h.keys[-1][0]
        levels = sorted((z, w) for z, w in zs.items() if z <= top)
        rings = [self.tine_ring(h, z, wr, wl) for z, (wr, wl) in levels] + [[h.tip.copy() for _ in SECTION]]
        tags = []
        for j in range(len(rings) - 1):
            z0 = levels[j][0]
            iced = frost is not None and z0 >= frost - 1e-3
            tags.append(["ice"] * len(SECTION) if iced else [edge if s in EDGE_SIDES else tag
                                                              for s in range(len(SECTION))])
        out.append(loft(rings, tags, cap0=(tag, False), cap1=(tag, False)))
        for z in bands:
            out += self.tine_band(h, z)
        if rune:
            out += self.tine_rune(h, *rune)
        if frost is not None:
            out += self.frozen_tip(h, frost, [b for b in barbs if b[0] >= frost - 2.0], seed=seed)
        return out

    def tine_band(self, h, z, height=2.4, tag="iron"):
        """A riveted iron band hugging the tine at z: its section grown 16% out, 2.4 tall, chamfered
        top and bottom; four rivets on the outer face either side of the spine."""
        rings = [self.tine_ring(h, z - height / 2, grow=0.98, dgrow=0.98),       # flush with the tine: no gap
                 self.tine_ring(h, z - height / 2 + 0.4, grow=1.16, dgrow=1.3),   # for the sky to look into
                 self.tine_ring(h, z + height / 2 - 0.4, grow=1.16, dgrow=1.3),
                 self.tine_ring(h, z + height / 2, grow=0.98, dgrow=0.98)]
        out = [loft(rings, [tag, tag, tag], cap0=(tag, False), cap1=(tag, False))]
        W, D = h.section(z)
        c = h.point(z, 0, 0)
        a = V((c.x, c.y, 0))
        for u in (-0.62, -0.38, 0.38, 0.62):
            d = (0.42 + (0.72 - 0.42) * (0.72 - abs(u)) / 0.5) * D * 1.3
            out += self.rivets(a, h.t, h.n, [(u * W * 1.16, z)], d, r=0.42)
        return out

    def tine_rune(self, h, z0, z1, tag="ember"):
        """A rune groove up the spine: short strokes of cold glow inlaid on the spine's two flanks,
        stepping side to side with a diamond every third stroke."""
        out = []
        n = max(3, int((z1 - z0) / 4.5))
        for i in range(n):
            za, zb = z0 + (z1 - z0) * i / n, z0 + (z1 - z0) * (i + 0.72) / n
            s = 1 if i % 2 else -1
            pts = []
            for z, f in ((za, 0.18), (zb, 0.06)):
                W, D = h.section(z)
                pts.append(h.point(z, s * f * W, D * (1.2 - 2.4 * f) + 0.12))
            out.append(self._stroke(pts[0], pts[1], h.n, 0.55, tag))
            if i % 3 == 1:
                zm = (za + zb) / 2
                W, D = h.section(zm)
                c = h.point(zm, 0, D * 1.2 + 0.1)
                c = c - h.n * 0.7                           # its foot sunk into the spine's ridge
                out.append(loft([[c + Z * 1.1, c + h.t * 0.6, c - Z * 1.1, c - h.t * 0.6],
                                 [c + Z * 0.7 + h.n * 0.3, c + h.t * 0.35 + h.n * 0.3, c - Z * 0.7 + h.n * 0.3,
                                  c - h.t * 0.35 + h.n * 1.0]], [tag], cap0=(tag, True), cap1=(tag, True)))
        return out

    @staticmethod
    def _stroke(p, q, n, w, tag):
        s = (q - p).cross(n).normalized() * (w / 2)
        ring = lambda c: [c - s - n * 0.3, c + s - n * 0.3, c + s + n * 0.22, c - s + n * 0.22]   # noqa: E731
        return loft([ring(p), ring(q)], [tag], cap0=(tag, True), cap1=(tag, True))

    def frozen_tip(self, h, frost, barbs, seed=0.0):
        """The ice from `frost` up: a casing of ice over the iron to the point (the section grown, its
        corners pushed out unevenly: crystal facets), its lower edge ragged, white rime on its last
        stretch; crystals growing up out of the casing and, a few, out of the iron just below it
        (the frost creeping down); icicles hanging off the barbs."""
        out = []
        top = h.keys[-1][0]
        rings = [self.tine_ring(h, frost - 5.5, grow=0.98, dgrow=0.98)]     # flush with the iron: no open foot
        ragged = self.tine_ring(h, frost - 1.0, grow=1.24, dgrow=1.55)
        D0 = h.section(frost)[1]
        rings.append([V((p.x, p.y, p.z - 3.6 * _h(seed, 7, j))) + h.n * (0.4 * D0 * (_h(seed, 0, j) - 0.4))
                      for j, p in enumerate(ragged)])                     # the frost line: ragged
        for i, f in enumerate((0.3, 0.6, 0.88)):
            z = frost + (top - frost) * f
            W, D = h.section(z)
            ring = self.tine_ring(h, z, grow=1.2 - 0.05 * i, dgrow=1.5)
            rings.append([p + h.n * (0.5 * D * (_h(seed, i + 1, j) - 0.4)) for j, p in enumerate(ring)])
        rings.append([h.tip + Z * 2.0 + h.n * 0.3] * len(SECTION))
        out.append(loft(rings, ["ice", "ice", "ice", "rime", "rime"], cap0=("ice", False), cap1=("rime", False)))
        up = (h.tip - h.point(frost, 0, 0)).normalized()
        for k in range(12):                                 # crystals: a few below the casing, most on it
            f = -0.22 + 0.9 * k / 11
            z = frost + (top - frost) * f
            j = (1, 4, 2, 5, 9, 7)[k % 6]                   # round the section: both faces, both edges
            side = 1 if j in (1, 2, 9) else -1
            out_d = -1 if j in (7, 9) else 1
            grow = (1.08, 1.25) if f > 0 else (0.9, 0.9)    # inside the casing, or the iron
            base = self.tine_ring(h, z, grow=grow[0], dgrow=grow[1])[j]
            lean = h.t * side * 0.4 + h.n * 0.4 * out_d
            L = (8.5 - 3.5 * max(f, 0.0)) * (0.75 + 0.5 * _h(seed + 5, k))
            out += self.shard(base, up + lean, L, 0.8 + 0.5 * (1 - abs(f)), k=4 + k % 2, seed=seed + k, bury=0.6)
        for z, side, dep in barbs:                          # icicles off the barbs' points
            W, D = h.section(z)
            p = h.point(z + 0.4, side * W * (1.0 + dep) * 0.96, 0)
            for j, (du, L) in enumerate(((0.0, 4.5), (-side * 0.9, 3.0))):
                q = p + h.t * du
                ring = [q + h.t * 0.45, q + h.n * 0.5, q - h.t * 0.45, q - h.n * 0.5]
                out.append(loft([ring, [q - Z * L * (0.8 + 0.4 * _h(seed, z, j))] * 4], ["ice"], cap0=("ice", True),
                                cap1=("ice", False)))
        return out
