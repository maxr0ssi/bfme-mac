"""The Angmar kit's ice (a mixin of AngmarShapes, assets/angmar/shapes.py): Carn Dum's frost made
solid. Ice is angular crystal, never round: every shard a faceted prism (four to six hard faces,
a little twist) ending in a pyramid point; clusters fan out of the stone like a geode's druse;
icicles hang in rows of uneven three-sided points under a rime crust. Sized for the RTS camera:
a cluster's big shards are 2-4 across and 8-20 long, an icicle row's longest points 6-9.

    shard(base, d, length, r)          one crystal from base along d: a k-sided prism (r across its
                                       corners), its point the last `point` of its length
    ice_cluster(c, r, h, n)            n shards fanning out of c: the tallest (h) in the middle,
                                       shorter ones leaning out to r; up the cluster's axis
    icicles(a, t, n, u0, u1, z, length, count)  a rime crust strip along a ledge (a face a, t, n
                                       at height z) with uneven icicles hanging from it
    rime_cap(a, t, n, u0, u1, z, d0, d1)  a frost crust over a ledge's top: a thin jagged slab,
                                       drips over its front edge
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz


def _v(p):
    return V((p[0], p[1], p[2] if len(p) > 2 else 0.0))


def _frame(d):
    """Two unit vectors square to d (any d)."""
    d = d.normalized()
    s = Z.cross(d)
    s = s.normalized() if s.length > 1e-4 else V((1, 0, 0))
    return s, d.cross(s).normalized()


def _hash(*xs):
    """A repeatable pseudo-random number in [0, 1) from the arguments (no global state)."""
    h = math.sin(sum(x * (12.9898 + 7.233 * i) for i, x in enumerate(xs))) * 43758.5453
    return h - math.floor(h)


class IceKit:
    def shard(self, base, d, length, r, k=5, point=0.32, twist=0.25, flat=0.7, tag="ice", bury=1.0, seed=0.0,
              floor=None):
        """A crystal from base along d, `length` long beyond base (and `bury` back into what it stands
        on): a k-sided prism r across its corners (flattened to `flat` on one axis: crystals are
        never round), slightly narrowing, twisting `twist` radians, its last `point` of the length
        a pyramid to the tip. floor: no buried point below this height (EA's ground: a shard must
        not deepen the model)."""
        base, d = _v(base), _v(d).normalized()
        s, u = _frame(d)
        ph = seed * 2.39

        def ringp(c, rr, a0):
            return [c + (s * math.cos(a0 + 2 * math.pi * i / k) + u * math.sin(a0 + 2 * math.pi * i / k) * flat) * rr
                    for i in range(k)]
        L0 = length * (1 - point)
        foot = ringp(base - d * bury, r, ph)
        if floor is not None:
            foot = [V((p.x, p.y, max(p.z, floor))) for p in foot]
        rings = [foot, ringp(base + d * L0, r * 0.82, ph + twist)]
        tip = base + d * length + s * (r * 0.15 * math.sin(ph))
        rings.append([tip.copy() for _ in range(k)])
        return [loft(rings, [tag, tag], cap0=(tag, False), cap1=(tag, False))]

    def ice_cluster(self, c, r, h, n=7, up=Z, seed=0.0, lean=0.55, thick=0.16, tag="ice", stone=None, floor=None,
                    hollow=0):
        """n shards out of c: the tallest (h long) near the axis `up`, the rest leaning out by up
        to `lean` and shorter toward the rim, spread over r round c (seeded, repeatable). thick:
        a shard's width over its length. `stone` (a tag): every third shard is that instead (black
        stone shards among the ice). floor: as shard's. hollow: leave out that many of the central
        shards (a crater in the middle: a fire's hearth)."""
        c, up = _v(c), _v(up).normalized()
        s, u = _frame(up)
        out = []
        for i in range(n):
            f = (i + hollow) / max(n - 1 + hollow, 1)   # 0: the central shard, 1: the rim
            a = 2 * math.pi * (i * 0.382 + _hash(seed, i) * 0.15)
            rad = r * (0.15 + 0.85 * f) * (0.7 + 0.3 * _hash(i, seed + 1))
            off = s * (math.cos(a) * rad) + u * (math.sin(a) * rad)
            lean_i = lean * (0.25 + 0.75 * f) * (0.8 + 0.4 * _hash(seed + 2, i))
            d = (up + (s * math.cos(a) + u * math.sin(a)) * lean_i).normalized()
            L = h * (1.0 - 0.55 * f) * (0.8 + 0.25 * _hash(seed + 3, i))
            w = max(0.5, L * thick * (0.8 + 0.4 * _hash(i, seed + 4)))
            t = stone if stone and i % 3 == 2 else tag
            out += self.shard(c + off, d, L, w, k=4 + (i % 3), seed=seed + i, tag=t, bury=max(1.0, w), floor=floor)
        return out

    def icicles(self, a, t, n, u0, u1, z, length, count, d=0.0, crust=0.9, w=1.1, seed=0.0, tag="ice",
                crust_tag="rime"):
        """A rime crust (a strip 0.9 high, crust deep from d into the face) along a ledge of the
        face (a, t, n) from u0 to u1 at height z (its underside), with `count` icicles hanging
        from it: three-sided points w across, their lengths uneven round `length`."""
        a, t, n = _v(a), _v(t), _v(n)
        a = V((a.x, a.y, 0))
        out = [prism_uz(a, t, n, [(u0, z - 0.3), (u1, z - 0.3), (u1, z + 0.6), (u0, z + 0.6)], d - crust, d + 0.35,
                        [crust_tag] * 4, crust_tag, crust_tag)]
        for i in range(count):
            f = (i + 0.5) / count
            u = u0 + (u1 - u0) * f + (u1 - u0) / count * 0.3 * (_hash(seed, i) - 0.5)
            L = length * (0.45 + 0.75 * _hash(seed + 1, i)) * (1.0 if i % 3 else 1.25)
            ww = w * (0.75 + 0.45 * _hash(seed + 2, i))
            dd = d - crust * 0.45
            top = a + t * u + n * dd + Z * (z + 0.2)
            ring = [top + t * ww * 0.6, top + n * ww * 0.55, top - t * ww * 0.6]
            tip = top - Z * L + n * (0.15 * L * 0.1)
            out.append(loft([ring, [p - Z * (L * 0.3) + (top - p) * 0.25 for p in ring], [tip] * 3], [tag, tag],
                            cap0=(tag, False), cap1=(tag, False)))
        return out

    def rime_cap(self, a, t, n, u0, u1, z, d0, d1, th=0.7, drips=0, seed=0.0, tag="rime"):
        """A frost crust over a ledge top (face a, t, n; from u0 to u1, from d0 into the face to d1
        out of it) at height z: a slab th thick, its front edge saw-cut, `drips` short icicles off
        the front."""
        a, t, n = _v(a), _v(t), _v(n)
        a = V((a.x, a.y, 0))
        P = lambda uu, dd, zz: a + t * uu + n * dd + Z * zz       # noqa: E731
        k = max(2, int(abs(u1 - u0) / 2.2))
        front = []
        for i in range(k + 1):
            uu = u0 + (u1 - u0) * i / k
            front.append((uu, d1 + (0.35 if i % 2 else -0.1)))
        top = [P(uu, dd, z + th) for uu, dd in front] + [P(u1, d0, z + th), P(u0, d0, z + th)]
        bot = [P(uu, dd, z - 0.2) for uu, dd in front] + [P(u1, d0, z - 0.2), P(u0, d0, z - 0.2)]
        out = [loft([bot, top], [tag], cap0=(tag, False), cap1=(tag, True))]
        for i in range(drips):
            uu = u0 + (u1 - u0) * (i + 0.5) / drips
            c = P(uu, d1 + 0.1, z)
            L = 2.0 + 2.5 * _hash(seed, i)
            ring = [c + t * 0.5, c + n * 0.45, c - t * 0.5]
            out.append(loft([ring, [c - Z * L] * 3], [tag], cap0=(tag, False), cap1=(tag, False)))
        return out
