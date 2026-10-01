"""The Angmar kit's crown (a mixin of AngmarShapes, assets/angmar/shapes.py): the Witch-king's
crown made iron. A crown tine is a broad blade with a ridge down both faces (an eight-sided lens
in section, its two cutting edges steel), rising along a spine that leans in, with barbs hooking
up off both edges like the jagged points of his helm's crown. Broad and barbed, never a needle.

    CrownTine(keys, out, tip)          keys [(z, (x, y), (W, D))]: the spine and the section (half
                                       width along the crown's ring, half depth across it) at each
                                       height; out the horizontal outward axis (the broad face's
                                       normal); tip the point (x, y, z)
      .centre(z), .section(z), .point(z, w, d)
    crown_tine(h, barbs)               the tine's solid: barbs [(z, edge, depth)], edge +1 / -1 (the
                                       ring's two directions), depth a fraction of the half width
    witch_crown(c, r, tines)           a ring of tines round c: tines [(deg, size)], size a key of
                                       `sizes` {name: (keys as (z, r from c, W, D), tip (r, z), barbs)}
    cold_brazier(c, r, h)              a sorcerer's brazier: a claw of five iron prongs out of a
                                       cluster of black stone shards, the cold fire among them
                                       (its point recorded: kind "coldflame" by default)
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft


def _lerp(keys, z):
    if z <= keys[0][0]:
        return keys[0][1], keys[0][2]
    for (z0, c0, s0), (z1, c1, s1) in zip(keys, keys[1:]):
        if z <= z1:
            f = (z - z0) / (z1 - z0)
            return (tuple(a + (b - a) * f for a, b in zip(c0, c1)), tuple(a + (b - a) * f for a, b in zip(s0, s1)))
    return keys[-1][1], keys[-1][2]


class CrownTine:
    def __init__(self, keys, out, tip):
        self.keys = sorted(keys, key=lambda k: k[0])
        self.n = V((out[0], out[1], 0)).normalized()          # the broad face's normal (outward)
        self.t = V((-self.n.y, self.n.x, 0))                   # along the crown's ring
        self.tip = V(tip)

    def centre(self, z):
        return _lerp(self.keys, z)[0]

    def section(self, z):
        return _lerp(self.keys, z)[1]

    def point(self, z, w, d):
        c = self.centre(z)
        return V((c[0], c[1], z)) + self.t * w + self.n * d

    def lens(self, z, wr=1.0, wl=1.0):
        """The section at z: the right edge (+t, scaled wr), the outer ridge, the left edge (scaled
        wl), the inner ridge, with narrow steel bevels at the edges."""
        W, D = self.section(z)
        return [self.point(z, a, b) for a, b in (
            (W * wr, 0), (0.7 * W * wr, 0.5 * D), (0, D), (-0.7 * W * wl, 0.5 * D), (-W * wl, 0),
            (-0.7 * W * wl, -0.5 * D), (0, -D), (0.7 * W * wr, -0.5 * D))]


class CrownKit:
    CrownTine = CrownTine

    def crown_tine(self, h, barbs=(), tag="iron", edge="steel", frost=None):
        """The tine's solid: lens rings at every keyframe and round each barb (the edge jumping out
        by `depth` of the half width at z, dropping back 0.8 higher, starting 3.5 below: barbs
        hooking up), then the tip. The bevel faces at both edges take `edge`, the faces `tag`;
        frost (a tag): the point (from the last keyframe up) rimed in it."""
        zs = {round(k[0], 3): [1.0, 1.0] for k in h.keys}
        for z, side, dep in barbs:
            i = 0 if side > 0 else 1
            zs.setdefault(round(z - 3.5, 3), [1.0, 1.0])
            zs.setdefault(round(z, 3), [1.0, 1.0])[i] = 1.0 + dep
            zs.setdefault(round(z + 0.8, 3), [1.0, 1.0])[i] = 0.9
        top = h.keys[-1][0]
        rings = [h.lens(z, wr, wl) for z, (wr, wl) in sorted(zs.items()) if z <= top]
        rings.append([h.tip.copy() for _ in range(8)])
        tags = [[edge, tag, tag, edge, edge, tag, tag, edge]] * (len(rings) - 1)
        if frost:
            tags[-1] = [frost] * 8
        return [loft(rings, tags, cap0=(tag, False), cap1=(tag, False))]

    def witch_crown(self, c, tines, sizes, tag="iron", edge="steel", frost=None):
        """A ring of tines round c (x, y): tines [(deg, size)], sizes {size: (keys [(z, r, W, D)],
        (tip r, tip z), barbs [(z, edge, depth)])}: each tine's spine at r from c on the ray at
        deg, its broad face to the outside. Returns (solids, [CrownTine])."""
        out, made = [], []
        for deg, size in tines:
            keys, (rt, zt), barbs = sizes[size]
            a = math.radians(deg)
            e = V((math.cos(a), math.sin(a), 0))
            ctr = V((c[0], c[1], 0))
            h = CrownTine([(z, tuple((ctr + e * r)[:2]), (W, D)) for z, r, W, D in keys], e,
                          ctr + e * rt + V((0, 0, zt)))
            out += self.crown_tine(h, barbs, tag=tag, edge=edge, frost=frost)
            made.append(h)
        return out, made

    def cold_brazier(self, c, r=1.8, h=6.0, prongs=5, kind="coldflame", seed=0.0):
        """A sorcerer's brazier at c: a cluster of black stone shards (r across, about h/2 tall)
        and out of it a claw of `prongs` iron prongs curving up and in to h, steel-tipped; the
        cold fire among them (its point recorded at the claw's heart)."""
        c = V((c[0], c[1], c[2] if len(c) > 2 else 0.0))
        out = self.ice_cluster(c, r * 0.9, h * 0.5, n=5, seed=seed, lean=0.45, thick=0.28, tag="rock", stone="ice")
        for i in range(prongs):
            a = 2 * math.pi * (i + 0.5 * (seed % 1)) / prongs
            e = V((math.cos(a), math.sin(a), 0))
            p0 = c + e * r * 0.55 + Z * (h * 0.3)
            p1 = c + e * r * 1.15 + Z * (h * 0.65)
            p2 = c + e * r * 0.8 + Z * h
            out.append(self.tube([p0, p1, p2], [0.34, 0.28, 0.0], "iron", k=4, cap0="iron", cap1=None,
                                 phase=math.pi / 4))
        self.fire(c + Z * (h * 0.62), kind)
        return out
