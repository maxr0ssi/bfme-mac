"""The Mordor kit's lava (a mixin of MordorShapes, assets/mordor/shapes.py): the black land split by
fire. Lava is "flame" where it runs open (brightest), "ember" in cracks and crusts; the kerbs are
raw basalt ("rock"), never masonry.

    lava_channel(points, w)            a channel of open lava along a polyline on the ground or a
                                       walk: jagged basalt kerbs each side, the lava between, a
                                       crust of cooling rafts on it
    lava_crack(a, t, n, pts, w, bat)   a crack glowing out of a face: a polyline of (u, z) points,
                                       each run a thin ember prism tapering to the last point
    face_crack(points, n, w)           a crack over any surface: 3D points on it, n its outward
                                       normal (one, horizontal), tapering from w to a point
    lava_pool(c, r)                    an irregular pool of lava in a basalt lip (seven-sided)
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz


def _v(p):
    return V((p[0], p[1], p[2] if len(p) > 2 else 0.0))


class LavaKit:
    def lava_channel(self, points, w=1.4, kerb=0.9, h=0.9, seed=0.0, rafts=True, sides=(-1, 1), pitch=5.0):
        """Open lava along `points` (their z the ground's), w its half width: a flat lava strip
        just proud of the ground, and a jagged basalt kerb on `sides` (-1 left, +1 right of the
        run; kerb wide, h high, broken into teeth about `pitch` long); a few dark rafts on it."""
        pts = [_v(p) for p in points]
        out = []
        for a, b in zip(pts, pts[1:]):
            t = V((b.x - a.x, b.y - a.y, 0))
            L = t.length
            if L < 1e-3:
                continue
            t.normalize()
            n = V((-t.y, t.x, 0))
            out.append(prism_uz(a, t, n, [(0.0, a.z), (L, a.z), (L, a.z + 0.35), (0.0, a.z + 0.35)], -w, w,
                                ["flame"] * 4, "flame", "flame"))
            for s in sides:                                 # the kerbs: a row of broken basalt teeth
                k = max(1, int(round(L / pitch)))
                for i in range(k):
                    u0, u1 = L * i / k, L * (i + 1) / k
                    hh = h * (0.7 + 0.5 * (0.5 + 0.5 * math.sin(seed * 2.3 + i * 1.9 + s)))
                    poly = [(u0, a.z), (u1, a.z), (u1 - (u1 - u0) * 0.25, a.z + hh * 0.8), (u0 + (u1 - u0) * 0.4, a.z + hh)]
                    d0, d1 = (w - 0.2, w + kerb) if s > 0 else (-w - kerb, -w + 0.2)
                    out.append(prism_uz(a, t, n, poly, d0, d1, ["rock"] * 4, "rock", "rock"))
            if rafts and L > 4:                             # cooling crust rafts
                for i in range(int(L // 6)):
                    u = L * (i + 0.5) / max(int(L // 6), 1) + 0.6 * math.sin(seed + i)
                    dd = w * 0.35 * math.sin(seed * 1.3 + i * 2.7)
                    r = w * 0.45
                    poly = [(u - r, a.z + 0.3), (u + r * 0.8, a.z + 0.3), (u + r * 0.4, a.z + 0.6), (u - r * 0.6, a.z + 0.6)]
                    out.append(prism_uz(a, t, n, poly, dd - r * 0.6, dd + r * 0.6, ["soot"] * 4, "soot", "soot"))
        return out

    def lava_crack(self, a, t, n, pts, w=0.8, d=0.0, depth=0.35, tag="ember", bat=0.0):
        """A crack glowing out of a face (a, t, n): through (u, z) points, w wide at the first,
        tapering to a point at the last, standing `depth` proud of d; bat: the face leans back
        this much per unit of height above z 0 (EA's battered walls)."""
        a, t, n = V(a), V(t), V(n)
        out = []
        m = len(pts) - 1
        for i, ((u0, z0), (u1, z1)) in enumerate(zip(pts, pts[1:])):
            w0, w1 = w * (1 - i / m) + 0.12, w * (1 - (i + 1) / m) + 0.12
            L = math.hypot(u1 - u0, z1 - z0)
            if L < 1e-3:
                continue
            nu, nz = -(z1 - z0) / L, (u1 - u0) / L
            poly = [(u0 + nu * w0 / 2, z0 + nz * w0 / 2), (u0 - nu * w0 / 2, z0 - nz * w0 / 2),
                    (u1 - nu * w1 / 2, z1 - nz * w1 / 2), (u1 + nu * w1 / 2, z1 + nz * w1 / 2)]
            back = bat * min(z0, z1)
            out.append(prism_uz(a, t, n, poly, d - 0.3 - back, d + depth - back, [tag] * 4, tag, None,
                                bat=bat))
        return out

    def face_crack(self, points, n, w=1.0, depth=0.3, tag="ember"):
        """A glowing crack through 3D `points` on a surface whose outward normal is n (horizontal),
        w wide at the first point tapering to a point at the last, standing `depth` proud."""
        pts, n = [V(p) for p in points], V((n[0], n[1], 0)).normalized()
        out = []
        m = len(pts) - 1
        for i, (p, q) in enumerate(zip(pts, pts[1:])):
            s = (q - p).cross(n)
            if s.length < 1e-6:
                continue
            s.normalize()
            w0, w1 = (w * (1 - i / m) + 0.15) / 2, (w * (1 - (i + 1) / m) + 0.15) / 2
            ring = lambda c, hw: [c - s * hw - n * 0.4, c + s * hw - n * 0.4, c + s * hw + n * depth,  # noqa: E731
                                  c - s * hw + n * depth]
            out.append(loft([ring(p, w0), ring(q, w1)], [tag], cap0=(tag, True), cap1=(tag, True)))
        return out

    def lava_pool(self, c, r, seed=0.0, lip=0.9):
        """An irregular seven-sided pool of lava r across at c in a raised basalt lip."""
        c = _v(c)
        k = 7
        jit = [0.8 + 0.35 * (0.5 + 0.5 * math.sin(seed * 3.1 + i * 2.2)) for i in range(k)]
        ringp = lambda s, z: [c + V((r * s * jit[i] * math.cos(2 * math.pi * i / k + seed),  # noqa: E731
                                     r * s * jit[i] * math.sin(2 * math.pi * i / k + seed), z)) for i in range(k)]
        out = [loft([ringp(1.0 + lip / r, 0.0), ringp(1.0 + lip / r * 0.6, 0.8), ringp(1.0, 0.5), ringp(1.0, 0.3)],
                    ["rock", "rock", "rock"], cap0=("rock", False), cap1=("flame", True))]
        return out
