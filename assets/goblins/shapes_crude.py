"""The Goblin kit's crude work (a mixin of GoblinShapes, assets/goblins/shapes.py): beaten iron
plates and hoops with fat rivets (gritty silver, "iron"), lashed charcoal timber ("timber") and
leather thongs ("rope"), stretched crimson hide ("hide") daubed with white war paint ("paint"),
chains, cages, braziers and the ragged banners in the player's colour ("cloth").

    rivets(a, t, n, pts, d)            fat rivet heads on a face
    plate(a, t, n, u0, u1, z0, z1)     a crude riveted plate, skewed as if hammered on
    hoop(c, z, r)                      a riveted band round a post, column or spire (a k-gon)
    pole(p, q, r)                      a rough log
    lashing(c, axis, r)                leather thongs wound round a pole
    stake(base, top, r)                a sharpened stake
    palisade(a, t, n, u0, u1, z0, h)   a row of leaning sharpened stakes on two lashed rails,
                                       skulls on some
    marking(a, t, n, u, z, size, d)    white war paint: "eye", "hand", "claw" or "fangs"
    hide_panel(a, t, n, u, z_top, ...) a crimson hide stretched from a lashed pole, painted
    fangs(a, t, n, u0, u1, z, length)  a row of bone teeth along an edge (a gate's jaws)
    chain(p, q)                        a hanging chain of alternating links
    cage(top, h, r)                    a gibbet cage on its chain, a skeleton slumped inside
    brazier(c, r, h)                   an iron fire bowl on three spiked legs, glowing coals
    banner(a, t, n, u, z_top, w, l)    a ragged house-colour banner on a bone spar, painted
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz, sweep


# war paint, in a unit box (u -0.5..0.5, z 0..1): strokes ((u0, z0), (u1, z1), width) and filled
# convex shapes [(u, z)]
MARKS = {
    "eye": ([((-0.5, 0.5), (0.0, 0.74), 0.08), ((0.0, 0.74), (0.5, 0.5), 0.08), ((0.5, 0.5), (0.0, 0.26), 0.08),
             ((0.0, 0.26), (-0.5, 0.5), 0.08), ((-0.14, 0.27), (-0.18, 0.02), 0.06), ((0.14, 0.27), (0.19, 0.06), 0.06)],
            [[(0.0, 0.36), (0.09, 0.5), (0.0, 0.64), (-0.09, 0.5)]]),
    "hand": ([((-0.17, 0.55), (-0.26, 0.9), 0.09), ((-0.06, 0.57), (-0.08, 1.0), 0.09), ((0.06, 0.57), (0.09, 0.98), 0.09),
              ((0.17, 0.55), (0.27, 0.86), 0.09), ((0.2, 0.3), (0.46, 0.52), 0.09)],
             [[(-0.23, 0.16), (0.22, 0.14), (0.24, 0.58), (-0.22, 0.58)]]),
    "claw": ([((-0.38, 0.92), (-0.12, 0.08), 0.1), ((-0.04, 0.98), (0.17, 0.06), 0.1), ((0.26, 0.9), (0.44, 0.18), 0.1)],
             []),
    "fangs": ([((-0.5, 0.95), (0.5, 0.95), 0.08)],
              [[(-0.5, 0.92), (-0.26, 0.92), (-0.38, 0.35)], [(-0.24, 0.92), (0.0, 0.92), (-0.12, 0.05)],
               [(0.0, 0.92), (0.24, 0.92), (0.12, 0.05)], [(0.26, 0.92), (0.5, 0.92), (0.38, 0.35)]]),
}


def _stroke(p, q, w):
    (u0, z0), (u1, z1) = p, q
    L = math.hypot(u1 - u0, z1 - z0)
    nu, nz = -(z1 - z0) / L * w / 2, (u1 - u0) / L * w / 2
    eu, ez = (u1 - u0) / L * w * 0.3, (z1 - z0) / L * w * 0.3
    return [(u0 - eu + nu, z0 - ez + nz), (u0 - eu - nu, z0 - ez - nz), (u1 + eu - nu, z1 + ez - nz), (u1 + eu + nu, z1 + ez + nz)]


class CrudeKit:
    # ------------------------------------------------------------------ iron
    @staticmethod
    def rivets(a, t, n, pts, d, r=0.32, tag="iron"):
        """A fat pyramid rivet head at each (u, z) of a face, standing r out from d."""
        a, t, n = V(a), V(t), V(n)
        out = []
        for u, z in pts:
            c = V((a.x + t.x * u + n.x * d, a.y + t.y * u + n.y * d, z))
            base = [c + t * (r * x) + Z * (r * y) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            out.append(loft([[p - n * 0.15 for p in base], [c + n * r * 1.1] * 4], [tag], cap0=(tag, False), cap1=(tag, False)))
        return out

    def plate(self, a, t, n, u0, u1, z0, z1, d=0.0, th=0.45, skew=0.5, rivet=0.3, tag="iron"):
        """A crude plate hammered onto a face: a skewed quadrilateral th thick with a rivet in each
        corner (rivet=0: none)."""
        poly = [(u0, z0 + skew * 0.4), (u1, z0), (u1 - skew * 0.5, z1), (u0 + skew * 0.3, z1 - skew * 0.6)]
        out = [prism_uz(V(a), V(t), V(n), poly, d - 0.12, d + th, [tag] * 4, tag, None)]
        if rivet:
            m = rivet * 1.8
            pts = [(u0 + m, z0 + skew * 0.4 + m), (u1 - m, z0 + m), (u1 - skew * 0.5 - m, z1 - m),
                   (u0 + skew * 0.3 + m, z1 - skew * 0.6 - m)]
            out += self.rivets(a, t, n, pts, d + th, rivet, tag)
        return out

    def hoop(self, c, z, r, h=1.6, th=0.6, inner=1.2, k=8, phase=None, rivets=True, tag="iron", closed=False):
        """A riveted band h tall round a vertical post, column or spire at c: a k-gon path of
        circumradius r (faces toward the axes by default, like EA's octagons), standing th out and
        sunk `inner` in. rivets: a rivet head in the middle of every side (a number n: of every n-th side). closed: its inner face
        too (a free-standing ring, a cage's; else it is buried in what it wraps)."""
        phase = math.pi / k if phase is None else phase
        path = [(c[0] + r * math.cos(phase + 2 * math.pi * i / k), c[1] + r * math.sin(phase + 2 * math.pi * i / k))
                for i in range(k)]
        path.append(path[0])
        prof = [(-inner, z - h / 2), (th, z - h / 2), (th, z + h / 2), (-inner, z + h / 2)]
        solids, segs = sweep(path, prof, [tag, tag, tag, tag if closed else None], center=(c[0], c[1]))
        out = list(solids)
        if rivets:
            for a2, b2, t2, n2 in segs[::rivets if isinstance(rivets, int) and rivets > 1 else 1]:
                m = (a2 + b2) / 2
                out += self.rivets(V((m.x, m.y, 0)), V((t2.x, t2.y, 0)), V((n2.x, n2.y, 0)), [(0.0, z)], th, 0.28, tag)
        return out

    # ------------------------------------------------------------------ timber and rope
    def pole(self, p, q, r, tag="timber", k=5):
        """A rough log from p to q (slightly swollen in the middle)."""
        p, q = V(p), V(q)
        return [self.tube([p, p.lerp(q, 0.5), q], [r, r * 1.08, r * 0.92], tag, k=k, cap0=tag, cap1=tag)]

    def lashing(self, c, axis, r, turns=2, w=0.3, tag="rope"):
        """`turns` bands of leather thong round a pole of radius r at c (along axis)."""
        c, ax = V(c), self.unit(axis)
        out = []
        for i in range(turns):
            m = c + ax * (i - (turns - 1) / 2) * w * 1.5
            out.append(self.tube([m - ax * w / 2, m + ax * w / 2], [r + 0.14, r + 0.14], tag, k=5, cap0=tag, cap1=tag))
        return out

    def stake(self, base, top, r, tag="timber", k=4, tip=None):
        """A sharpened stake from base to its point at top (tip: another tag for the point, "gore")."""
        base, top = V(base), V(top)
        d = self.unit(top - base)
        return [self.tube([base, top - d * r * 3.0, top], [r, r * 0.95, 0.0], [tag, tip or tag], k=k, cap0=tag, cap1=None)]

    def palisade(self, a, t, n, u0, u1, z0, h, d=0.5, pitch=2.4, r=0.55, lean=0.18, rails=(0.3, 0.68), skulls=(),
                 skull=2.2, seed=1):
        """Sharpened stakes along a wall top from u0 to u1 standing on z0 (sunk 1 below), h tall
        (each a little different), leaning out, every third point bloodied; two rails in front; a
        skull on the stakes whose index is in `skulls`."""
        a, t, n = V(a), V(t), V(n)
        count = max(1, int(round((u1 - u0) / pitch)))
        step = (u1 - u0) / count
        out = []
        for i in range(count):
            u = u0 + step * (i + 0.5)
            hh = h * (0.86 + 0.28 * (0.5 + 0.5 * math.sin(seed * 7.1 + i * 2.39)))
            base = a + t * u + n * d + Z * (z0 - 1.0)
            top = base + Z * (hh + 1.0) + n * lean * hh
            out += self.stake(base, top, r, tip="gore" if (i + seed) % 3 == 0 else None)
            if i in skulls:
                out += self.skull(top - Z * 1.1 * skull + n * lean * 0.1, n, skull, detail=1, tusks=True)
        for f in rails:
            z = z0 + h * f
            p = a + t * (u0 + 0.3) + n * (d + r + 0.35 + lean * h * f) + Z * z
            q = a + t * (u1 - 0.3) + n * (d + r + 0.35 + lean * h * f) + Z * z
            out.append(self.tube([p, q], [0.42, 0.42], "timber", k=4, cap0="timber", cap1="timber", phase=0.785))
        return out

    # ------------------------------------------------------------------ hide and paint
    @staticmethod
    def marking(a, t, n, u, z, size, d, kind="eye", tag="paint", th=0.16, back=None):
        """White war paint `size` across on a face, its foot at z, standing th proud of d: "eye",
        "hand", "claw" or "fangs" (MARKS). back: a tag closes the strokes behind (on cloth that
        leaves for the house-colour model)."""
        strokes, fills = MARKS[kind]
        a, t, n = V(a), V(t), V(n)
        polys = [_stroke(p, q, w) for p, q, w in strokes] + fills
        return [prism_uz(a, t, n, [(u + x * size, z + y * size) for x, y in poly], d - 0.08, d + th,
                         [tag] * len(poly), tag, back) for poly in polys]

    def hide_panel(self, a, t, n, u, z_top, width, length, d=0.6, mark="eye", th=0.35, pole=True):
        """A crimson hide `width` wide hung `length` down from a lashed pole at z_top, its foot cut
        to a point, the war-paint `mark` on it (None: plain)."""
        a, t, n = V(a), V(t), V(n)
        h, zb = width / 2, z_top - length
        tail = min(length * 0.25, width * 0.4)
        poly = [(u - h, z_top), (u + h, z_top), (u + h * 0.9, zb + tail), (u + h * 0.2, zb), (u - h * 0.35, zb + tail * 0.2),
                (u - h * 0.95, zb + tail * 0.9)]
        out = [prism_uz(a, t, n, poly, d, d + th, ["hide"] * 6, "hide", "hide")]
        if pole:
            p = a + t * (u - h - 1.2) + n * (d + th + 0.2) + Z * (z_top + 0.2)
            q = a + t * (u + h + 1.2) + n * (d + th + 0.2) + Z * (z_top + 0.2)
            out += self.pole(p, q, 0.5)
            out += self.lashing(p.lerp(q, 0.5), q - p, 0.5, turns=1, w=0.5)
        if mark:
            size = min(width * 0.78, length * 0.6)
            out += self.marking(a, t, n, u, zb + tail * 0.9 + (length - tail - size) * 0.35, size, d + th, mark)
        return out

    @staticmethod
    def fangs(a, t, n, u0, u1, z, length, count, d0, d1, down=True, tag="bone", seed=2):
        """`count` bone teeth from u0 to u1 along the edge at z, `length` long (the outer ones
        longest, like canines), pointing down (or up)."""
        a, t, n = V(a), V(t), V(n)
        step = (u1 - u0) / count
        out = []
        for i in range(count):
            u = u0 + step * (i + 0.5)
            edge = abs(i - (count - 1) / 2) / max((count - 1) / 2, 1)
            L = length * (0.55 + 0.45 * edge ** 2) * (0.9 + 0.1 * math.sin(seed + i * 1.9))
            w = step * 0.42
            zt = z - L if down else z + L
            out.append(prism_uz(a, t, n, [(u - w, z), (u + w, z), (u, zt)], d0, d1, [tag] * 3, tag, tag))
        return out

    # ------------------------------------------------------------------ chains, cages, fire
    def chain(self, p, q, link=1.3, w=0.5, th=0.18, tag="iron"):
        """A chain from p to q of alternating links (each a flat diamond, 8 triangles)."""
        p, q = V(p), V(q)
        d = q - p
        m = max(1, int(math.ceil(d.length / (link * 0.78))))
        ax = self.unit(d)
        s0 = self.side_of(ax)
        s1 = ax.cross(s0).normalized()
        out = []
        for i in range(m):
            a2, b2 = p + d * (i / m), p + d * ((i + 1) / m) + ax * link * 0.12
            c = (a2 + b2) / 2
            sa, sb = (s0, s1) if i % 2 == 0 else (s1, s0)
            ring = [c + sa * w, c + sb * th, c - sa * w, c - sb * th]
            out.append(loft([[a2] * 4, ring, [b2] * 4], [tag, tag], cap0=(tag, False), cap1=(tag, False)))
        return out

    def cage(self, top, h, r, bars=5, skeleton=True, facing=(1, 0, 0), chain=0.0):
        """A gibbet cage hanging from `top` (on `chain` units of chain above it): a domed crown of
        bars, two hoops, a floor, and a skeleton slumped inside."""
        top = V(top)
        out = self.chain(top + Z * chain, top) if chain else []
        crown = top - Z * 0.4
        z1, z0 = top.z - 2.2, top.z - h
        for i in range(bars):
            a = 2 * math.pi * i / bars
            rad = V((math.cos(a), math.sin(a), 0))
            pts = [crown, crown + rad * r * 0.62 - Z * 0.8, V((top.x, top.y, z1)) + rad * r,
                   V((top.x, top.y, z0 + 0.5)) + rad * r, V((top.x, top.y, z0)) + rad * r * 0.86]
            out.append(self.tube(pts, [0.2, 0.17, 0.17, 0.17, 0.17], "iron", k=3, cap0="iron", cap1="iron"))
        for z in (z1, z0 + 0.4):
            out += self.hoop((top.x, top.y), z, r * 1.02, h=0.5, th=0.22, inner=0.25, k=bars, phase=0.0, rivets=False,
                             closed=True)
        floor = [V((top.x + r * 0.92 * math.cos(2 * math.pi * i / bars), top.y + r * 0.92 * math.sin(2 * math.pi * i / bars), 0))
                 for i in range(bars)]
        out.append(loft([[p + Z * (z0 - 0.3) for p in floor], [p + Z * (z0 + 0.1) for p in floor]], ["iron"],
                        cap0=("iron", True), cap1=("iron", True)))
        if skeleton:
            f = V(facing)
            out += self.skeleton(V((top.x, top.y, z0 + 0.6)) - f * r * 0.35, f, h * 0.95, "slump")
        return out

    def brazier(self, c, r, h, legs=3):
        """An iron fire bowl r across on spiked legs, h high, heaped with glowing coals ("ember")."""
        c = V(c)
        out = [self.tube([c + Z * (h - r * 0.55), c + Z * h, c + Z * (h + 0.3)], [r * 0.35, r, r * 1.08], "iron", k=6,
                         cap0="iron", cap1="ember")]
        for i in range(legs):
            a = 2 * math.pi * i / legs + 0.4
            rad = V((math.cos(a), math.sin(a), 0))
            out.append(self.tube([c + Z * (h - r * 0.3) + rad * r * 0.4, c + rad * r * 0.95], [0.22, 0.16], "iron", k=3,
                                 cap0="iron", cap1="iron"))
            out += self.spike(c + Z * (h + 0.2) + rad * r * 0.95, rad * 0.4 + Z, r * 0.9, 0.18, k=3)
        return out

    # ------------------------------------------------------------------ banners
    def banner(self, a, t, n, u, z_top, width, length, d=1.4, mark="eye", skull=False):
        """A ragged banner `width` wide hung `length` from a bone spar held d out from a wall face on
        two iron spikes: its foot torn into three tongues, the war-paint `mark` on it. The cloth
        ("cloth") leaves for the house-colour model and takes the player's colour; the spar, the
        spikes, the paint (closed behind) and the skull stay on the body."""
        a, t, n = V(a), V(t), V(n)
        h, tail = width / 2, min(length * 0.28, width * 0.6)
        zb = z_top - length
        out = [prism_uz(a, t, n, [(u - h, zb + tail), (u + h, zb + tail), (u + h, z_top), (u - h, z_top)], d - 0.15, d + 0.15,
                        ["cloth"] * 4, "cloth", "cloth")]
        for x0, x1, tip in ((-h, -h / 3, -h * 0.72), (-h / 3, h / 3, 0.0), (h / 3, h, h * 0.68)):
            drop = tail * (1.0 if tip == 0.0 else 0.75)
            out.append(prism_uz(a, t, n, [(u + x0, zb + tail), (u + x1, zb + tail), (u + tip, zb + tail - drop)],
                                d - 0.15, d + 0.15, ["cloth"] * 3, "cloth", "cloth"))
        p = a + t * (u - h - 1.0) + n * d + Z * (z_top + 0.35)
        q = a + t * (u + h + 1.0) + n * d + Z * (z_top + 0.35)
        out += self.bone(p, q, 0.32)
        for f in (0.1, 0.9):
            m = p.lerp(q, f)
            out += self.spike(m - n * (d + 1.0), n, d + 1.6, 0.26, k=4)
        if mark:
            size = min(width * 0.75, (length - tail) * 0.8)
            out += self.marking(a, t, n, u, zb + tail + (length - tail - size) * 0.45, size, d + 0.15, mark, back="paint")
        if skull:
            out += self.skull(p.lerp(q, 0.5) + Z * 1.0, n, 1.7, detail=0)
        return out
