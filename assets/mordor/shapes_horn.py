"""The Mordor kit's horns, the Eye and the witch-light (a mixin of MordorShapes,
assets/mordor/shapes.py).

A Horn is Barad-dur's crown prong: a black basalt blade rising along a spine, its horizontal
section a knife-edged hexagon (an outer arris, an inner arris, flat faces front and back), with a
saw-toothed inner edge whose teeth hook upward and hooks pointing down off the outer edge,
tapering to a point that hooks toward its partner. It is built from keyframes so a recipe can find points on it
(the Eye's slot, the slits, the barbs) at any height.

    Horn(keys, e, f, tip)              keys [(z, (x, y), (Wo, Wi, D))]: the spine and the section
                                       (outer reach, inner reach, half depth) at each height; e the
                                       horizontal outward axis (away from its partner), f its front
                                       (toward the camera); tip the point (x, y, z)
      .centre(z), .section(z)          interpolated
      .point(z, eo, fo)                a point of the section plane at z
      .facet(z, i)                     (midpoint, along, out) of the section's side i at z:
                                       0 outer-front, 1 front, 2 inner-front, 3 inner-back, 4 back,
                                       5 outer-back
    horn(h, teeth, hooks)              the horn's solid: teeth [(z, depth)] hooking up on the inner
                                       edge, hooks [(z, depth)] pointing down on the outer edge
    eye(a, t, n, u, z0, w, h)          the Lidless Eye in a pointed slot: an iron slot with a fire-lit
                                       frame, a flame almond, a black slit pupil, lashes of fire
    witch_slit(a, t, n, u, z0, w, h)   a pointed lancet sunk in a face: a window ("slit") or a
                                       Morgul witch-light ("witch")
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz


def _lerp_keys(keys, z):
    """(centre (x, y), section (Wo, Wi, D)) at z by linear interpolation of the keyframes."""
    if z <= keys[0][0]:
        return keys[0][1], keys[0][2]
    for (z0, c0, s0), (z1, c1, s1) in zip(keys, keys[1:]):
        if z <= z1:
            f = (z - z0) / (z1 - z0)
            return (tuple(a + (b - a) * f for a, b in zip(c0, c1)), tuple(a + (b - a) * f for a, b in zip(s0, s1)))
    return keys[-1][1], keys[-1][2]


def pointed(w, z0, h, head=0.5):
    """A pointed arch (u, z) polygon w wide from z0 to its point at z0 + h; `head` of the width is
    the height of the pointed head."""
    return [(-w / 2, z0), (w / 2, z0), (w / 2, z0 + h - w * head), (0, z0 + h), (-w / 2, z0 + h - w * head)]


class Horn:
    def __init__(self, keys, e, f, tip):
        self.keys = sorted(keys, key=lambda k: k[0])
        self.e = V((e[0], e[1], 0)).normalized()
        self.f = V((f[0], f[1], 0)).normalized()
        self.tip = V(tip)

    def centre(self, z):
        return _lerp_keys(self.keys, z)[0]

    def section(self, z):
        return _lerp_keys(self.keys, z)[1]

    def point(self, z, eo, fo):
        c = self.centre(z)
        return V((c[0], c[1], z)) + self.e * eo + self.f * fo

    def hexagon(self, z, wo=1.0, wi=1.0):
        Wo, Wi, D = self.section(z)
        Wo, Wi = Wo * wo, Wi * wi
        return [self.point(z, a, b) for a, b in ((Wo, 0), (0.4 * Wo, D), (-0.5 * Wi, D), (-Wi, 0), (-0.5 * Wi, -D),
                                                  (0.4 * Wo, -D))]

    def facet(self, z, i):
        """(midpoint, along, out) of side i of the section at z (see the module docstring)."""
        ring = self.hexagon(z)
        a, b = ring[i], ring[(i + 1) % 6]
        m = (a + b) / 2
        t = (b - a).normalized()
        n = V((t.y, -t.x, 0))
        ctr = sum(ring, V((0, 0, 0))) / 6
        if n.dot(m - ctr) < 0:
            n = -n
        return m, t, n


class HornKit:
    Horn = Horn
    pointed = staticmethod(pointed)

    def horn(self, h, teeth=(), hooks=(), tag="stoneA", edge="stoneB", outer=None):
        """The horn's solid: horizontal hexagon rings at every keyframe, a saw tooth at each
        (z, depth) of `teeth` on the inner arris (out by `depth` of its reach, sloping up to its
        point and dropping back 0.6 higher: teeth hooking up), a hook at each (z, depth) of `hooks`
        on the outer arris (jumping out 0.8 below z, sloping back in 4 below: hooks pointing down),
        and the tip. The arrises' faces take `edge` (the outer one `outer` when given: a steel
        cutting edge), the front and back faces `tag`."""
        zs = {k[0]: [1.0, 1.0] for k in h.keys}

        def put(z, i, v):
            zs.setdefault(round(z, 3), [1.0, 1.0])[i] = v
        for z, dep in teeth:
            zs.setdefault(round(z - 3.2, 3), [1.0, 1.0])
            put(z, 1, 1.0 + dep)
            put(z + 0.6, 1, 0.92)
        for z, dep in hooks:
            zs.setdefault(round(z + 4.0, 3), [1.0, 1.0])
            put(z, 0, 1.0 + dep)
            put(z - 0.8, 0, 0.96)
        top = h.keys[-1][0]
        rings = [h.hexagon(z, wo, wi) for z, (wo, wi) in sorted(zs.items()) if z <= top]
        rings.append([h.tip.copy() for _ in range(6)])
        o = outer or edge
        tags = [[o, tag, edge, edge, tag, o]] * (len(rings) - 1)
        return [loft(rings, tags, cap0=(tag, False), cap1=(tag, False))]

    # ------------------------------------------------------------------ the Eye
    def eye(self, a, t, n, u, z0, w, h, d=0.0, frame="trim"):
        """The Lidless Eye in a pointed slot on a face (a, t, n) at u, from z0, w wide and h tall,
        standing from d: an iron slot, a fire-lit frame, a flame almond, a black slit pupil and six
        lashes of fire round the almond."""
        a, t, n = V((a[0], a[1], 0)), V(t), V(n)           # heights are absolute: the anchor's z is dropped
        out = [prism_uz(a, t, n, [(u + x, z) for x, z in pointed(w, z0, h, 0.55)], d - 1.6, d + 0.9, ["iron"] * 5,
                        "iron", "iron")]
        poly = pointed(w, z0, h, 0.55)
        for (u0, za), (u1, zb) in zip(poly, poly[1:] + poly[:1]):
            out.append(self.beam(a + t * (u + u0) + Z * za + n * (d + 0.9), a + t * (u + u1) + Z * zb + n * (d + 0.9),
                                 max(0.3, w * 0.05), frame))
        cz = z0 + h * 0.46                                  # the almond: a vesica across the slot
        rw, rh = w * 0.4, h * 0.2
        alm = [(u + rw * math.cos(math.pi * i / 6), cz + rh * math.copysign(math.sin(math.pi * i / 6) ** 2, 5.5 - i)
                if i % 6 else cz) for i in range(12)]           # parabolic arcs meeting in points
        out.append(prism_uz(a, t, n, alm, d + 0.5, d + 1.3, ["flame"] * 12, "flame", None))
        pupil = [(u, cz - rh * 0.95), (u + rw * 0.13, cz), (u, cz + rh * 0.95), (u - rw * 0.13, cz)]
        out.append(prism_uz(a, t, n, pupil, d + 1.0, d + 1.6, ["iron"] * 4, "iron", None))
        for i in range(6):                                  # lashes of fire
            ang = math.pi * (0.12 + 0.76 * i / 5)
            for sgn in (1, -1):
                if sgn < 0 and i in (0, 5):
                    continue
                cu, cs = math.cos(ang), math.sin(ang) * sgn
                b = (u + rw * 0.92 * cu, cz + rh * 1.0 * cs)
                tip = (u + rw * 1.22 * cu, cz + rh * 1.9 * cs)
                sp = 0.3
                out.append(prism_uz(a, t, n, [(b[0] - sp, b[1]), (b[0] + sp, b[1]), tip] if sgn > 0 else
                                    [(b[0] + sp, b[1]), (b[0] - sp, b[1]), tip], d + 0.6, d + 1.1, ["ember"] * 3,
                                    "ember", None))
        return out

    # ------------------------------------------------------------------ witch-light
    def witch_slit(self, a, t, n, u, z0, w, h, d0=-0.8, d1=0.5, bat=0.0, sill=True, tag="slit"):
        """A pointed lancet on a face at u from z0, w wide, h tall, from d0 (buried) to d1 (proud),
        tagged `tag` ("slit": a window, lit as the palette's windows; "witch": the few kept in the
        Morgul witch-light); an iron sill and hood-spike above when `sill`."""
        a, t, n = V((a[0], a[1], 0)), V(t), V(n)
        out = [prism_uz(a, t, n, [(u + x, z) for x, z in pointed(w, z0, h, 0.7)], d0, d1, [tag] * 5, tag, tag,
                        bat=bat)]
        if sill:
            lean = bat * h
            out.append(self.beam(a + t * (u - w * 0.75) + Z * (z0 - 0.3) + n * (d1 + 0.1),
                                 a + t * (u + w * 0.75) + Z * (z0 - 0.3) + n * (d1 + 0.1), 0.3, "iron"))
            top = a + t * u + Z * (z0 + h) + n * (d1 - lean)
            out.append(self.beam(top - Z * 0.4, top + Z * (w * 1.3), w * 0.28, "iron", 0.0))
        return out
