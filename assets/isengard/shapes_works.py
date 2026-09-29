"""The Isengard kit's works (a mixin of IsengardShapes, assets/isengard/shapes.py): heavy riveted
plate and hoops ("iron"), dark oiled chains ("chain"), the machinery on the walls, ember-lit vents
and slag ("ember", "soot"), iron spikes and pike racks, the White Hand ("mark") and the heavy
banners on iron frames in the player's colour ("cloth").

    rivets(a, t, n, pts, d)            round-topped rivet heads on a face
    plate(a, t, n, u0, u1, z0, z1)     a heavy riveted plate, its top edge bevelled
    hoop(c, z, r)                      a riveted band round a post, stack or tower (a k-gon)
    chain(p, q)                        a chain of alternating links
    gear(a, t, n, u, z, r, d)          a gear wheel on a wall: disk, teeth, hub and axle bolt
    pulley(a, t, n, u, z, r, d, drop)  a grooved wheel on a bracket, a chain and hook hanging from it
    vent(a, t, n, u, z, w, h, d)       an iron-framed grille over glowing coals
    slag_heap(c, r, h)                 a lumpy heap of soot-black slag, embers in it
    hook(p, size)                      an iron meat hook on a short chain
    spike_row(a, t, n, u0, u1, z, ...) iron spikes along an edge, leaning out
    pike_rack(a, t, n, u, z, w, h, d)  a rack of pikes against a wall
    hand(a, t, n, u, z, size, d)       the White Hand, raised (palm and five fingers)
    banner(a, t, n, u, z_top, w, l)    a heavy house-colour banner on an iron frame, the Hand on it
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz, sweep


def _stroke(p, q, w):
    (u0, z0), (u1, z1) = p, q
    L = math.hypot(u1 - u0, z1 - z0)
    nu, nz = -(z1 - z0) / L * w / 2, (u1 - u0) / L * w / 2
    return [(u0 + nu, z0 + nz), (u0 - nu, z0 - nz), (u1 - nu * 0.8, z1 - nz * 0.8), (u1 + nu * 0.8, z1 + nz * 0.8)]


# the White Hand in a unit box (u -0.5..0.5, z 0..1): the palm and five fingers ((u0, z0), (u1, z1), width)
HAND_PALM = [(-0.24, 0.08), (0.2, 0.06), (0.25, 0.52), (-0.25, 0.54)]
HAND_FINGERS = [((-0.19, 0.5), (-0.3, 0.86), 0.11), ((-0.07, 0.52), (-0.09, 0.98), 0.11), ((0.06, 0.52), (0.08, 1.0), 0.11),
                ((0.18, 0.5), (0.27, 0.88), 0.11), ((0.2, 0.26), (0.46, 0.46), 0.11)]


class WorksKit:
    # ------------------------------------------------------------------ plate
    @staticmethod
    def rivets(a, t, n, pts, d, r=0.3, tag="iron", k=4):
        """A round-topped rivet head (a low k-sided dome, 4k triangles) at each (u, z) of a face,
        proud of d."""
        a, t, n = V(a), V(t), V(n)
        out = []
        ph = math.pi / k
        for u, z in pts:
            c = V((a.x + t.x * u + n.x * d, a.y + t.y * u + n.y * d, z))
            ring0 = [c - n * 0.12 + (t * math.cos(ph + 2 * math.pi * i / k) + Z * math.sin(ph + 2 * math.pi * i / k)) * r
                     for i in range(k)]
            ring1 = [c + n * r * 0.55 + (t * math.cos(ph + 2 * math.pi * i / k) + Z * math.sin(ph + 2 * math.pi * i / k)) * r * 0.6
                     for i in range(k)]
            out.append(loft([ring0, ring1, [c + n * r * 0.8] * k], [tag, tag], cap0=(tag, False), cap1=(tag, False)))
        return out

    def plate(self, a, t, n, u0, u1, z0, z1, d=0.0, th=0.6, pitch=2.6, rivet=0.3, tag="iron"):
        """A heavy plate on a face from u0..u1, z0..z1, th thick, its top edge bevelled, with a row
        of rivets along its top and foot every `pitch` (rivet=0: none)."""
        b = min(th * 0.8, (z1 - z0) * 0.2)
        a, t, n = V(a), V(t), V(n)
        out = [prism_uz(a, t, n, [(u0, z0), (u1, z0), (u1, z1 - b), (u0, z1 - b)], d - 0.15, d + th, ["iron"] * 4, tag, tag),
               prism_uz(a, t, n, [(u0, z1 - b - 0.01), (u1, z1 - b - 0.01), (u1, z1), (u0, z1)], d - 0.15, d + th - b,
                        [tag] * 4, tag, tag)]
        if rivet:
            m = max(1, int(round((u1 - u0) / pitch)))
            us = [u0 + (u1 - u0) * (i + 0.5) / m for i in range(m)]
            out += self.rivets(a, t, n, [(u, z0 + rivet * 2.2) for u in us] + [(u, z1 - b - rivet * 2.2) for u in us],
                               d + th, rivet, tag)
        return out

    def hoop(self, c, z, r, h=1.4, th=0.55, inner=1.0, k=8, phase=None, rivets=True, tag="iron", closed=False):
        """A riveted band h tall round a vertical post, stack or tower at c: a k-gon path of
        circumradius r (faces toward the axes by default), standing th out and sunk `inner` in.
        rivets: one on every side (a number n: every n-th side). closed: its inner face too."""
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
                out += self.rivets(V((m.x, m.y, 0)), V((t2.x, t2.y, 0)), V((n2.x, n2.y, 0)), [(0.0, z)], th, 0.26, tag)
        return out

    # ------------------------------------------------------------------ machinery
    def chain(self, p, q, link=1.4, w=0.5, th=0.2, tag="chain"):
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
            out.append(loft([[a2] * 4, [c + sa * w, c + sb * th, c - sa * w, c - sb * th], [b2] * 4], [tag, tag],
                            cap0=(tag, False), cap1=(tag, False)))
        return out

    @staticmethod
    def gear(a, t, n, u, z, r, d, teeth=10, th=0.7, tag="iron"):
        """A gear wheel of radius r (teeth included) on a face, its disk th thick standing from d:
        a 2*teeth-gon disk, trapezoid teeth, a raised hub and an axle bolt."""
        a, t, n = V(a), V(t), V(n)
        k, root, out = teeth * 2, r * 0.8, []

        def P(ang, rr):
            return (u + rr * math.cos(ang), z + rr * math.sin(ang))
        disk = [P(2 * math.pi * i / k, root) for i in range(k)]
        out.append(prism_uz(a, t, n, disk, d, d + th, [tag] * k, tag, tag))
        for i in range(teeth):
            c = 2 * math.pi * i / teeth
            s = math.pi / teeth * 0.55
            poly = [P(c - s, root * 0.96), P(c + s, root * 0.96), P(c + s * 0.6, r), P(c - s * 0.6, r)]
            out.append(prism_uz(a, t, n, poly, d + 0.05, d + th - 0.05, [tag] * 4, tag, tag))
        hub = [P(2 * math.pi * i / 6 + math.pi / 6, root * 0.36) for i in range(6)]
        out.append(prism_uz(a, t, n, hub, d + th - 0.1, d + th + 0.55, [tag] * 6, tag, tag))
        bolt = [P(2 * math.pi * i / 6, root * 0.14) for i in range(6)]
        out.append(prism_uz(a, t, n, bolt, d + th + 0.4, d + th + 1.0, ["chain"] * 6, "chain", "chain"))
        for i in range(4):                                  # spokes, raised on the disk
            ang = math.pi / 4 + math.pi / 2 * i
            sp = [P(ang - 0.12, root * 0.36), P(ang + 0.12, root * 0.36), P(ang + 0.06, root * 0.9), P(ang - 0.06, root * 0.9)]
            out.append(prism_uz(a, t, n, sp, d + th - 0.1, d + th + 0.3, [tag] * 4, tag, tag))
        return out

    def pulley(self, a, t, n, u, z, r, d, drop=8.0, hook=True):
        """A grooved wheel of radius r on an iron bracket d out from a face at (u, z), a chain
        running over it and `drop` down to a hook."""
        a, t, n = V(a), V(t), V(n)
        base = a + t * u + Z * z
        c = base + n * d
        out = [self.beam(base - n * 0.6 + Z * (r + 0.6), c + Z * (r + 0.6), 0.35),
               self.beam(c + Z * (r + 0.6), c - Z * 0.2, 0.3)]
        for off, rr in ((-0.45, r), (0.0, r * 0.78), (0.45, r)):          # two cheeks and the groove
            p = c + t * off
            out.append(self.tube([p - t * 0.22, p + t * 0.22], [rr, rr], "iron", k=8, cap0="iron", cap1="iron",
                                 phase=math.pi / 8))
        top = c + n * r * 0.78
        out += self.chain(top, top - Z * drop)
        if hook:
            out += self.hook(top - Z * drop, 1.3, chain=0.0)
        return out

    def vent(self, a, t, n, u, z, w, h, d, bars=4):
        """An iron-framed grille w x h on a face at (u, z) (its foot), proud of d: glowing coals
        behind (an "ember" panel) and `bars` vertical bars across them."""
        a, t, n = V(a), V(t), V(n)
        f = 0.55
        out = [prism_uz(a, t, n, [(u - w / 2, z), (u + w / 2, z), (u + w / 2, z + h), (u - w / 2, z + h)], d - 0.2, d + 0.1,
                        ["ember"] * 4, "ember", "ember")]
        for poly in ([(u - w / 2 - f, z - f), (u + w / 2 + f, z - f), (u + w / 2 + f, z), (u - w / 2 - f, z)],
                     [(u - w / 2 - f, z + h), (u + w / 2 + f, z + h), (u + w / 2 + f, z + h + f), (u - w / 2 - f, z + h + f)],
                     [(u - w / 2 - f, z), (u - w / 2, z), (u - w / 2, z + h), (u - w / 2 - f, z + h)],
                     [(u + w / 2, z), (u + w / 2 + f, z), (u + w / 2 + f, z + h), (u + w / 2, z + h)]):
            out.append(prism_uz(a, t, n, poly, d - 0.2, d + 0.7, ["iron"] * 4, "iron", "iron"))
        for i in range(bars):
            ub = u - w / 2 + w * (i + 1) / (bars + 1)
            out.append(prism_uz(a, t, n, [(ub - 0.2, z), (ub + 0.2, z), (ub + 0.2, z + h), (ub - 0.2, z + h)], d, d + 0.5,
                                ["iron"] * 4, "iron", "iron"))
        return out

    def slag_heap(self, c, r, h, seed=1, embers=3):
        """A lumpy heap of slag r across and h high at c: soot black, a few glowing lumps."""
        cx, cy = c[0], c[1]
        k = 7

        def jit(i, j):
            return 0.82 + 0.3 * (0.5 + 0.5 * math.sin(seed * 3.7 + i * 2.3 + j * 1.9))
        rings = [[V((cx + r * jit(i, 0) * math.cos(2 * math.pi * i / k), cy + r * jit(i, 0) * math.sin(2 * math.pi * i / k),
                     c[2] - 0.05)) for i in range(k)],
                 [V((cx + r * 0.7 * jit(i, 1) * math.cos(2 * math.pi * i / k + 0.3),
                     cy + r * 0.7 * jit(i, 1) * math.sin(2 * math.pi * i / k + 0.3), c[2] + h * 0.55)) for i in range(k)],
                 [V((cx + r * 0.25 * jit(i, 2) * math.cos(2 * math.pi * i / k), cy + r * 0.25 * jit(i, 2) * math.sin(2 * math.pi * i / k),
                     c[2] + h)) for i in range(k)]]
        out = [loft(rings, ["soot", "soot"], cap0=("soot", False), cap1=("soot", True))]
        for i in range(embers):
            ang = seed + i * 2.2
            p = V((cx + r * 0.55 * math.cos(ang), cy + r * 0.55 * math.sin(ang), c[2] + h * 0.35))
            out.append(self.facet_lump(p, r * 0.18, "ember"))
        return out

    @staticmethod
    def facet_lump(p, s, tag):
        """A small faceted lump (an octahedron-ish nugget) of size s at p."""
        p = V(p)
        mid = [p + V((s * math.cos(i * math.pi / 2 + 0.4), s * math.sin(i * math.pi / 2 + 0.4), 0)) for i in range(4)]
        return loft([[p - Z * s * 0.5] * 4, mid, [p + Z * s * 0.7] * 4], [tag, tag], cap0=(tag, False), cap1=(tag, False))

    def hook(self, p, size, chain=2.0):
        """An iron meat hook of `size` hanging from p (on `chain` units of chain)."""
        p = V(p)
        out = self.chain(p, p - Z * chain) if chain else []
        top = p - Z * chain
        pts = [top, top - Z * size * 0.7, top - Z * size * 1.05 + V((size * 0.25, 0, 0)),
               top - Z * size * 0.95 + V((size * 0.5, 0, 0)), top - Z * size * 0.6 + V((size * 0.55, 0, 0))]
        out.append(self.tube(pts, [0.2, 0.2, 0.18, 0.14, 0.0], "chain", k=4, cap0="chain", cap1=None))
        return out

    # ------------------------------------------------------------------ spikes and arms
    def spike_row(self, a, t, n, u0, u1, z, length, count, d=0.0, lean=0.35, r=0.35, tag="iron"):
        """`count` iron spikes from u0 to u1 along a face's edge at z, `length` long, leaning out
        by `lean` (0: straight up)."""
        a, t, n = V(a), V(t), V(n)
        out = []
        for i in range(count):
            u = u0 + (u1 - u0) * (i + 0.5) / count
            base = a + t * u + n * d + Z * (z - 0.6)
            dirn = (Z + n * lean).normalized()
            L = length * (0.85 + 0.15 * math.sin(i * 2.1))
            out.append(self.tube([base, base + dirn * L * 0.65, base + dirn * L], [r, r * 0.55, 0.0], tag, k=4,
                                 cap0=tag, cap1=None, phase=math.pi / 4))
        return out

    def pike_rack(self, a, t, n, u, z, w, h, d=1.0, pikes=5):
        """A rack w wide on a face at (u, z): two iron uprights and two rails d out, `pikes` pikes
        (timber shafts, iron blades) leaning in it."""
        a, t, n = V(a), V(t), V(n)
        out = []
        for s in (-1, 1):
            p = a + t * (u + s * w / 2) + n * d + Z * z
            out.append(self.beam(p - n * d, p, 0.25))
            out.append(self.beam(p - Z * 0.3, p + Z * h * 0.75, 0.25))
        for f in (0.25, 0.7):
            p = a + n * d + Z * (z + h * f)
            out.append(self.beam(p + t * (u - w / 2), p + t * (u + w / 2), 0.2))
        for i in range(pikes):
            uu = u - w / 2 + w * (i + 0.5) / pikes
            foot = a + t * uu + n * (d + 0.9) + Z * z
            top = a + t * (uu + 0.4) + n * (d - 0.1) + Z * (z + h)
            out.append(self.beam(foot, top, 0.16, "timber"))
            dd = self.unit(top - foot)
            out.append(self.beam(top, top + dd * 2.2, 0.32, "iron", 0.0))
        return out

    # ------------------------------------------------------------------ the Hand and the banners
    @staticmethod
    def hand(a, t, n, u, z, size, d, th=0.2, tag="mark", back=None):
        """The White Hand `size` tall on a face, its foot at z, standing th proud of d. back: a tag
        closes it behind (on cloth that leaves for the house-colour model)."""
        a, t, n = V(a), V(t), V(n)
        polys = [HAND_PALM] + [_stroke(p, q, w) for p, q, w in HAND_FINGERS]
        return [prism_uz(a, t, n, [(u + x * size, z + y * size) for x, y in poly], d - 0.08, d + th,
                         [tag] * len(poly), tag, back) for poly in polys]

    def banner(self, a, t, n, u, z_top, width, length, d=1.2, mark=True):
        """A heavy banner `width` wide hung `length` from an iron frame held d out from a face on
        two brackets: a top bar, iron side rods, a weighted foot bar and a V-cut foot. The cloth
        ("cloth") leaves for the house-colour model and takes the player's colour; the frame and
        the Hand (closed behind) stay on the body."""
        a, t, n = V(a), V(t), V(n)
        h, cut = width / 2, min(length * 0.18, width * 0.35)
        zb = z_top - length
        out = [prism_uz(a, t, n, [(u - h, zb + cut), (u + h, zb + cut), (u + h, z_top), (u - h, z_top)], d - 0.15, d + 0.15,
                        ["cloth"] * 4, "cloth", "cloth")]
        for x0, x1 in ((-h, 0.0), (0.0, h)):
            tip = (x0 + x1) / 2
            out.append(prism_uz(a, t, n, [(u + x0, zb + cut), (u + x1, zb + cut), (u + tip, zb)], d - 0.15, d + 0.15,
                                ["cloth"] * 3, "cloth", "cloth"))
        P = lambda uu, zz, dd=d: a + t * uu + n * dd + Z * zz     # noqa: E731
        out.append(self.beam(P(u - h - 1.0, z_top + 0.45), P(u + h + 1.0, z_top + 0.45), 0.42))
        out.append(self.beam(P(u - h - 0.4, zb + cut - 0.35), P(u + h + 0.4, zb + cut - 0.35), 0.32))
        for s in (-1, 1):
            out.append(self.beam(P(u + s * (h + 0.35), zb + cut - 0.4), P(u + s * (h + 0.35), z_top + 0.4), 0.22))
            out.append(self.beam(P(u + s * (h + 1.0), z_top + 0.45, -0.8), P(u + s * (h + 1.0), z_top + 0.45), 0.36))
            out.append(self.beam(P(u + s * (h + 1.0), z_top + 0.45), P(u + s * (h + 1.6), z_top + 2.2), 0.3, "iron", 0.0))
        if mark:
            size = min(width * 0.72, (length - cut) * 0.7)
            out += self.hand(a, t, n, u, zb + cut + (length - cut - size) * 0.5, size, d + 0.15, back="mark")
        return out
