"""The Isengard kit's yard (a mixin of IsengardShapes, assets/isengard/shapes.py): the war-works'
story pieces, free-standing on the ground or a wall walk rather than pasted on a face. Felled
Fangorn (stumps, logs, a frame saw), forges (hearths, anvils, bellows, crucibles), cranes, the
dammed Isen (a water wheel on its sluice, driving gears), scaffolding round half-built siege
work, Uruk shield racks, and the pipework and fire grates that link the furnaces.

Placement: c a ground point (x, y, z), t the piece's long axis (horizontal), n its front.

    stump(c, r, h)                     a felled tree's stump: cut top, flared roots
    log(p, q, r)                       a trimmed trunk
    log_stack(c, t, length, r, rows)   trunks stacked in a pyramid between iron stakes
    saw_frame(c, t, length, h)         a frame saw on trestles, a trunk half cut through it
    hearth(c, t, n, w, d, h)           a stone forge hearth: glowing bed, iron hood, flue
    anvil(c, t, s)                     an anvil on its stone block
    bellows(c, t, s)                   a great bellows: boards, leather, iron nozzle
    crucible(c, r, h)                  an iron crucible of molten metal, lugs for its chains
    gantry(c, t, span, h, load)        an A-framed gantry, trolley, chain and a hanging load
    water_wheel(c, t, r, w)            an undershot wheel, rims, spokes, paddles, axle
    sluice(c, t, length, w)            a timber flume on trestles, its gate in an iron frame
    scaffold(c, t, n, w, d, h, levels) poles, ledgers, braces and plank decks
    siege_ladder(c, t, n, h, w, rungs) a tall ladder leaning in, half its rungs fitted
    shield(a, t, n, u, z, s)           an Uruk shield: tall, black, silver-rimmed, the Hand on it
    shield_rack(c, t, n, w, count)     a rack of Uruk shields and a crossbar of spears
    pipe(points, r)                    iron pipework with flanged joints
    fire_grate(c, t, n, w, h, d)       a deep iron firebox, glowing, barred

Nothing reaches more than 0.7 below c (a sunk leg's corners): on open ground put c at z GROUND so no piece passes EA's
ground (the preview's height check fails a model that grows downward).
"""
import math

from mathutils import Vector as V

GROUND = 0.7

from sagekit.blender.geometry import Z, loft, prism_uz


def _v(p):
    return V((p[0], p[1], p[2] if len(p) > 2 else 0.0))


def prism(a, t, n, poly, *args):
    """prism_uz with the polygon's z measured from the anchor's height (prism_uz's is absolute)."""
    return prism_uz(a, t, n, [(u, z + a.z) for u, z in poly], *args)


class YardKit:
    # ------------------------------------------------------------------ Fangorn
    def stump(self, c, r, h, seed=0):
        """A stump r across, h high: seven-sided, its cut top pale ("timber"), four flared roots."""
        c = _v(c)
        out = [self.tube([c - Z * 0.4, c + Z * h * 0.6, c + Z * h], [r * 1.25, r * 1.02, r], "timber", k=7,
                         cap0=None, cap1="timber", phase=seed)]
        for i in range(4):
            a = seed + i * math.pi / 2 + 0.4
            d = V((math.cos(a), math.sin(a), 0))
            out.append(self.tube([c + d * r * 0.7 + Z * h * 0.4, c + d * r * 2.1 - Z * 0.35], [r * 0.38, r * 0.12], "timber",
                                 k=4, cap0="timber", cap1="timber"))
        return out

    def log(self, p, q, r):
        return self.tube([_v(p), _v(q)], [r, r * 0.92], "timber", k=6, cap0="timber", cap1="timber")

    def log_stack(self, c, t, length, r, rows=3):
        """Trunks `length` long along t, stacked rows-1 .. 1 on a bottom row of `rows`, between two
        iron stakes at each end."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        out = []
        for j in range(rows):
            for i in range(rows - j):
                off = (i - (rows - j - 1) / 2) * r * 2.02
                m = c + n * off + Z * (r * 0.95 + j * r * 1.72)
                out.append(self.log(m - t * length / 2, m + t * length / 2, r * (0.92 + 0.08 * math.sin(i * 3 + j))))
        for s in (-1, 1):
            for e in (-1, 1):
                b = c + t * (e * length * 0.36) + n * (s * (rows * r + 0.3))
                out.append(self.beam(b - Z * 0.4, b + Z * (rows * r * 1.6 + 0.8), 0.28, "iron", 0.05))
        return out

    def trestle(self, c, t, h, w):
        """A timber trestle: two splayed legs each side and a top rail along n."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        out = [self.beam(c + Z * h - n * w / 2, c + Z * h + n * w / 2, 0.4, "timber")]
        for s in (-1, 1):
            top = c + Z * h + n * (s * w * 0.4)
            out.append(self.beam(top, c + n * (s * w * 0.4) + t * 1.2 - Z * 0.4, 0.3, "timber"))
            out.append(self.beam(top, c + n * (s * w * 0.4) - t * 1.2 - Z * 0.4, 0.3, "timber"))
        return out

    def saw_frame(self, c, t, length, h):
        """A great frame saw: a trunk on two trestles, a tall iron-bound frame straddling it with the
        blade down into the cut."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        top = h * 0.35
        out = self.trestle(c - t * length * 0.3, t, top, 4.0) + self.trestle(c + t * length * 0.3, t, top, 4.0)
        out.append(self.log(c - t * length / 2 + Z * (top + 1.3), c + t * length / 2 + Z * (top + 1.3), 1.3))
        m = c + t * length * 0.12
        for s in (-1, 1):
            out.append(self.beam(m + n * (s * 2.6) - Z * 0.4, m + n * (s * 2.6) + Z * h, 0.35, "timber"))
        out.append(self.beam(m - n * 3.2 + Z * h, m + n * 3.2 + Z * h, 0.4, "timber"))
        out.append(self.beam(m - n * 2.6 + Z * (top + 3.2), m + n * 2.6 + Z * (top + 3.2), 0.3, "iron"))
        out.append(prism(m, n, t, [(-0.1, top + 0.4), (0.1, top + 0.4), (0.1, h - 0.4), (-0.1, h - 0.4)], -1.4, 1.4,
                            ["trim"] * 4, "trim", "trim"))
        return out

    # ------------------------------------------------------------------ forges
    def hearth(self, c, t, n, w=5.0, d=3.6, h=2.6, hood=4.5):
        """A stone forge hearth w x d, h high, a glowing bed sunk in its top, an iron hood over it
        and a flue pipe rising from the hood."""
        c, t, n = _v(c), _v(t).normalized(), _v(n).normalized()
        P = lambda u, dd, z: c + t * u + n * dd + Z * z          # noqa: E731
        ring = lambda z, s=1.0: [P(-w / 2 * s, -d / 2 * s, z), P(w / 2 * s, -d / 2 * s, z), P(w / 2 * s, d / 2 * s, z),  # noqa: E731
                                 P(-w / 2 * s, d / 2 * s, z)]
        out = [loft([ring(-0.5), ring(h), ring(h, 0.8), ring(h - 0.5, 0.8)], ["stoneA", "trim", "ember"],
                    cap0=("stoneA", False), cap1=("ember", True))]
        hz = h + hood * 0.35
        out.append(loft([ring(hz, 0.95), ring(hz + hood * 0.5, 0.55), ring(hz + hood * 0.55, 0.3)], ["iron", "iron"],
                        cap0=("soot", True), cap1=("iron", True)))
        for s in (-1, 1):
            out.append(self.beam(P(s * w * 0.45, -d * 0.45, h), P(s * w * 0.45, -d * 0.45, hz + 0.3), 0.18, "iron"))
        out.append(self.tube([c + Z * (hz + hood * 0.5), c + Z * (hz + hood * 1.6)], [w * 0.14, w * 0.14], "iron", k=6,
                             cap0="iron", cap1="soot"))
        return out

    def anvil(self, c, t, s=1.0):
        """An anvil on a squat stone block, its horn along t."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        B = lambda u0, u1, d0, d1, z0, z1, tag: loft(                                     # noqa: E731
            [[c + t * u + n * dd + Z * z for u, dd in ((u0, d0), (u1, d0), (u1, d1), (u0, d1))] for z in (z0, z1)],
            [tag], cap0=(tag, False), cap1=(tag, True))
        out = [B(-0.9 * s, 0.9 * s, -0.8 * s, 0.8 * s, -0.3, 1.6 * s, "stoneA"),
               B(-0.5 * s, 0.5 * s, -0.35 * s, 0.35 * s, 1.6 * s, 2.2 * s, "iron"),
               B(-1.3 * s, 1.0 * s, -0.55 * s, 0.55 * s, 2.2 * s, 2.8 * s, "trim")]
        out.append(self.beam(c + t * 1.0 * s + Z * 2.55 * s, c + t * 2.3 * s + Z * 2.6 * s, 0.28 * s, "trim", 0.0))
        return out

    def bellows(self, c, t, s=1.0):
        """A great bellows lying along t: two tapered boards, the leather between them, an iron
        nozzle toward +t, a handle toward -t."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        shape = [(-2.2, -1.4), (1.2, -0.7), (2.0, 0.0), (1.2, 0.7), (-2.2, 1.4)]
        out = []
        for z0, z1, tag in ((0.9, 1.2, "timber"), (1.2, 2.2, "soot"), (2.2, 2.5, "timber")):
            sc = 1.0 if tag == "timber" else 0.9
            rings = [[c + t * (u * s * sc) + n * (dd * s * sc) + Z * z * s for u, dd in shape] for z in (z0, z1)]
            out.append(loft(rings, [tag], cap0=(tag, True), cap1=(tag, True)))
        out.append(self.beam(c + t * 2.0 * s + Z * 1.7 * s, c + t * 3.4 * s + Z * 1.2 * s, 0.25 * s, "iron", 0.12 * s))
        out.append(self.beam(c - t * 2.2 * s + Z * 2.5 * s, c - t * 3.6 * s + Z * 3.4 * s, 0.14 * s, "timber"))
        out.append(self.beam(c - Z * 0.2, c + Z * 0.9 * s, 0.5 * s, "timber"))
        return out

    def crucible(self, c, r, h, lugs=True):
        """An iron crucible r across and h deep at c (its foot), brim-full of molten metal."""
        c = _v(c)
        out = [self.tube([c, c + Z * h * 0.25, c + Z * h * 0.9, c + Z * h], [r * 0.55, r * 0.95, r, r * 1.08], "iron",
                         k=8, cap0="iron", cap1="ember")]
        out += (self.hoop((c.x, c.y), c.z + h * 0.8, r * 1.02, h=0.45, th=0.2, inner=0.3, k=8, rivets=False,
                             tag="trim"))
        if lugs:
            for s in (-1, 1):
                p = c + V((s * r * 1.02, 0, h * 0.75))
                out.append(self.beam(p, p + V((s * 0.8, 0, 0)), 0.22, "iron"))
        return out

    def gantry(self, c, t, span, h, load="crucible", drop=None):
        """A gantry over `span` along t at c: an A-frame of iron-shod timber at each end, a riveted
        iron top beam, a trolley and a chain down to a crucible (or a siege beam: load="beam")."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        out = []
        for e in (-1, 1):
            top = c + t * (e * span / 2) + Z * h
            for s in (-1, 1):
                out.append(self.beam(c + t * (e * span / 2) + n * (s * h * 0.3) - Z * 0.4, top, 0.4, "timber"))
            out.append(self.beam(c + t * (e * span / 2) - n * h * 0.2 + Z * h * 0.35,
                                 c + t * (e * span / 2) + n * h * 0.2 + Z * h * 0.35, 0.3, "iron"))
        a, b = c - t * (span / 2 + 0.8) + Z * (h + 0.5), c + t * (span / 2 + 0.8) + Z * (h + 0.5)
        out.append(self.beam(a, b, 0.6, "iron"))
        out.append(self.beam(a + Z * 0.6, b + Z * 0.6, 0.25, "trim"))
        m = c + t * span * 0.15 + Z * (h - 0.3)
        out.append(self.beam(m - t * 0.8 - Z * 0.2, m + t * 0.8 - Z * 0.2, 0.45, "iron"))
        drop = drop if drop is not None else h * 0.45
        out += self.chain(m - Z * 0.6, m - Z * drop)
        if load == "beam":
            out.append(self.beam(m - Z * drop - n * 5.5 - Z * 0.5, m - Z * drop + n * 5.5 - Z * 0.5, 0.55, "timber"))
            out += (self.hoop((m.x, m.y), m.z - drop - 0.5, 0.95, h=0.5, th=0.15, inner=0.2, k=4, rivets=False,
                                 tag="iron", closed=True))
        else:
            out += self.crucible(m - Z * (drop + 3.0), 1.5, 2.8)
        return out

    # ------------------------------------------------------------------ the dammed Isen
    def water_wheel(self, c, t, r, w=2.4, spokes=8, paddles=12):
        """A wheel of radius r turning in the plane of t and z about c (its hub), w wide across n:
        two rims, spokes, paddles between the rims and an iron axle running back along -n."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        out = []
        k = paddles

        def P(ang, rr, dd):
            return c + t * (rr * math.cos(ang)) + Z * (rr * math.sin(ang)) + n * dd
        for dd in (-w / 2, w / 2):
            outer = [P(2 * math.pi * i / k, r, dd - 0.25) for i in range(k)]
            inner = [P(2 * math.pi * i / k, r * 0.84, dd - 0.25) for i in range(k)]
            outer2 = [p + n * 0.5 for p in outer]
            inner2 = [p + n * 0.5 for p in inner]
            for i in range(k):
                j = (i + 1) % k
                out.append(loft([[outer[i], outer[j], inner[j], inner[i]], [outer2[i], outer2[j], inner2[j], inner2[i]]],
                                ["timber"], cap0=("timber", True), cap1=("timber", True)))
            for i in range(spokes):
                ang = 2 * math.pi * (i + 0.5) / spokes
                out.append(self.beam(P(ang, r * 0.18, dd), P(ang, r * 0.86, dd), 0.22, "timber"))
        for i in range(k):
            ang = 2 * math.pi * i / k
            out.append(self.beam(P(ang, r * 0.9, -w / 2 - 0.3), P(ang, r * 0.9, w / 2 + 0.3), 0.3, "timber"))
            out.append(self.beam(P(ang, r * 0.9, 0), P(ang, r * 1.12, 0), 0.25, "timber"))
        out.append(self.tube([c + n * (w / 2 + 0.8), c - n * (w / 2 + 4.0)], [r * 0.12, r * 0.12], "iron", k=6,
                             cap0="trim", cap1="iron"))
        out.append(self.tube([c - n * 0.9, c + n * 0.9], [r * 0.2, r * 0.2], "iron", k=8, cap0="iron", cap1="iron"))
        return out

    def sluice(self, c, t, length, w=2.6, h=3.0, gate=True):
        """A flume `length` along t at c (its middle), its floor h above the ground on trestles,
        water in it ("water"), and an iron-framed gate at its -t end."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        a, b = c - t * length / 2, c + t * length / 2
        out = []
        for dd in (-w / 2, w / 2):
            out.append(self.beam(a + n * dd + Z * (h + 0.6), b + n * dd + Z * (h + 0.6), 0.3, "timber"))
        out.append(self.beam(a + Z * h, b + Z * h, w / 2, "timber"))
        out.append(prism(c + Z * 0.0, t, n, [(-length / 2, h + 0.3), (length / 2, h + 0.3), (length / 2, h + 0.7),
                                                 (-length / 2, h + 0.7)], -w / 2 + 0.3, w / 2 - 0.3, ["water"] * 4,
                            "water", "water"))
        for f in (0.2, 0.55, 0.9):
            out += self.trestle(a.lerp(b, f) - Z * 0.0, t, h - 0.3, w + 0.8)
        if gate:
            g = a + t * 0.6
            for s in (-1, 1):
                out.append(self.beam(g + n * (s * (w / 2 + 0.35)) + Z * h, g + n * (s * (w / 2 + 0.35)) + Z * (h + 4.2),
                                     0.3, "iron"))
            out.append(self.beam(g - n * (w / 2 + 0.6) + Z * (h + 4.2), g + n * (w / 2 + 0.6) + Z * (h + 4.2), 0.3, "iron"))
            out.append(prism(g, n, t, [(-w / 2, h + 1.6), (w / 2, h + 1.6), (w / 2, h + 3.4), (-w / 2, h + 3.4)],
                                -0.2, 0.2, ["iron"] * 4, "iron", "iron"))
            out.append(self.tube([g + Z * (h + 4.2), g + Z * (h + 5.6)], [0.14, 0.14], "iron", k=4, cap0="iron", cap1="trim"))
        return out

    # ------------------------------------------------------------------ siege work
    def scaffold(self, c, t, n, w, d, h, levels=3):
        """Scaffolding w along t and d deep along n from c (its front-left foot): poles at the
        corners and midpoints, a ledger and a plank deck every level, a brace on each side."""
        c, t, n = _v(c), _v(t).normalized(), _v(n).normalized()
        P = lambda u, dd, z: c + t * u + n * dd + Z * z          # noqa: E731
        out = []
        for u in (0.0, w / 2, w):
            for dd in (0.0, d):
                out.append(self.beam(P(u, dd, -0.4), P(u, dd, h), 0.25, "timber"))
        for i in range(1, levels + 1):
            z = h * i / (levels + 0.3)
            for dd in (0.0, d):
                out.append(self.beam(P(-0.4, dd, z), P(w + 0.4, dd, z), 0.2, "timber"))
            if i < levels + 1:
                out.append(prism(P(0, 0, 0), t, n, [(0.2, z + 0.2), (w - 0.2, z + 0.2), (w - 0.2, z + 0.45),
                                                       (0.2, z + 0.45)], 0.2, d - 0.2, ["timber"] * 4, "timber", "timber"))
        out.append(self.beam(P(0, 0, 0.3), P(w / 2, 0, h * 0.72), 0.18, "timber"))
        out.append(self.beam(P(w, d, 0.3), P(w / 2, d, h * 0.72), 0.18, "timber"))
        return out

    def siege_ladder(self, c, t, n, h, w=3.2, rungs=9, built=0.55, lean=0.28):
        """A siege ladder h tall at c, its rails along t apart, leaning back toward -n; only the
        lower `built` of its rungs fitted, iron hooks at its head."""
        c, t, n = _v(c), _v(t).normalized(), _v(n).normalized()
        up = (Z - n * lean).normalized()
        out = []
        for s in (-1, 1):
            f = c + t * (s * w / 2)
            out.append(self.beam(f - Z * 0.4, f + up * h, 0.3, "timber"))
            out.append(self.beam(f + up * h, f + up * h - n * 1.2 - Z * 0.8, 0.2, "iron", 0.0))
        for i in range(int(rungs * built)):
            p = c + up * (h * (i + 0.6) / rungs)
            out.append(self.beam(p - t * w / 2, p + t * w / 2, 0.16, "timber"))
        return out

    # ------------------------------------------------------------------ arms
    def shield(self, a, t, n, u, z, s, d=0.0, tag="stoneB"):
        """An Uruk shield s tall on a face or rack at (u, z) (its foot, z absolute): black,
        round-shouldered, a silver rim, the White Hand on it."""
        a, t, n = _v(a), _v(t).normalized(), _v(n).normalized()
        w = s * 0.36
        poly = [(u - w * 0.8, z), (u + w * 0.8, z), (u + w, z + s * 0.25), (u + w, z + s * 0.8), (u + w * 0.6, z + s),
                (u - w * 0.6, z + s), (u - w, z + s * 0.8), (u - w, z + s * 0.25)]
        out = [prism_uz(a, t, n, poly, d, d + 0.35, ["trim"] * 8, tag, tag)]
        out += self.hand(a, t, n, u, z + s * 0.2, s * 0.55, d + 0.35, th=0.12)
        return out

    def shield_rack(self, c, t, n, w, count=4, s=4.2):
        """A rack w along t at c facing n: two posts and a crossbar, `count` shields hung on it,
        spears standing behind."""
        c, t, n = _v(c), _v(t).normalized(), _v(n).normalized()
        out = []
        for e in (-1, 1):
            out.append(self.beam(c + t * (e * w / 2) - Z * 0.4, c + t * (e * w / 2) + Z * (s + 1.2), 0.28, "timber"))
        out.append(self.beam(c - t * (w / 2 + 0.3) + Z * (s + 0.9), c + t * (w / 2 + 0.3) + Z * (s + 0.9), 0.24, "iron"))
        for i in range(count):
            u = -w / 2 + w * (i + 0.5) / count
            out += self.shield(c + n * 0.3, t, n, u, c.z + 0.6, s, d=0.0)
        for i in range(count + 1):
            p = c + t * (-w / 2 + w * i / count) - n * 0.6
            out.append(self.beam(p - Z * 0.3, p + Z * (s + 3.2), 0.12, "timber"))
            out.append(self.beam(p + Z * (s + 3.2), p + Z * (s + 4.6), 0.2, "trim", 0.0))
        return out

    # ------------------------------------------------------------------ pipework
    def pipe(self, points, r=0.55, flange=True):
        """Iron pipework through `points` (3D), a flanged silver joint at the start of every run."""
        pts = [_v(p) for p in points]
        out = [self.tube(pts, [r] * len(pts), "iron", k=6, cap0="iron", cap1="iron")]
        if flange:
            for p, q in zip(pts, pts[1:]):
                for f in (0.08,):
                    m = p.lerp(q, f)
                    d = (q - p).normalized()
                    out.append(self.tube([m - d * 0.2, m + d * 0.2], [r * 1.45, r * 1.45], "trim", k=6,
                                         cap0="trim", cap1="trim"))
        return out

    def fire_grate(self, c, t, n, w=3.6, h=2.8, d=2.4):
        """A deep iron firebox w wide, h high, d deep at c (its front foot, facing n): glowing
        inside, four bars across its mouth, a silver rim and a small hood."""
        c, t, n = _v(c), _v(t).normalized(), _v(n).normalized()
        out = [prism(c, t, n, [(-w / 2, -0.3), (w / 2, -0.3), (w / 2, h), (-w / 2, h)], -d, 0.0,
                        ["iron", "iron", "iron", "iron"], "ember", "iron")]
        out.append(prism(c, t, n, [(-w / 2 - 0.4, h), (w / 2 + 0.4, h), (w / 2 + 0.1, h + 0.9), (-w / 2 - 0.1, h + 0.9)],
                            -d - 0.2, 0.6, ["trim"] * 4, "iron", "iron"))
        for i in range(4):
            u = -w / 2 + w * (i + 0.5) / 4
            out.append(self.beam(c + t * u + n * 0.25 + Z * 0.1, c + t * u + n * 0.25 + Z * (h - 0.1), 0.14, "iron"))
        return out

    # ------------------------------------------------------------------ small furniture
    def brazier(self, c, r=1.2, h=3.2):
        """An iron fire basket r across on three splayed legs, h high, heaped with embers."""
        c = _v(c)
        out = [self.tube([c + Z * (h - r * 0.9), c + Z * h, c + Z * (h + 0.25)], [r * 0.45, r, r * 1.05], "iron", k=6,
                         cap0="iron", cap1="ember")]
        for i in range(3):
            a = 2 * math.pi * i / 3 + 0.5
            d = V((math.cos(a), math.sin(a), 0))
            out.append(self.beam(c + Z * (h - r * 0.5) + d * r * 0.5, c + d * r * 1.1 - Z * 0.3, 0.14, "iron"))
            out.append(self.beam(c + Z * (h + 0.1) + d * r, c + Z * (h + r * 0.9) + d * r * 1.25, 0.12, "iron", 0.0))
        return out

    def lantern(self, p, s=1.0, chain=1.6):
        """A caged lantern s tall hanging from p: a glowing core, four iron bars, cap and finial."""
        p = _v(p)
        out = self.chain(p, p - Z * chain, link=0.9, w=0.25, th=0.1) if chain else []
        top = p - Z * chain
        c = top - Z * s * 0.6
        out.append(loft([[c + V((x, y, 0)) * s * 0.34 - Z * s * 0.45 for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))],
                         [c + V((x, y, 0)) * s * 0.34 + Z * s * 0.35 for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]],
                        ["ember"], cap0=("iron", True), cap1=("iron", True)))
        out.append(self.beam(c + Z * s * 0.35, top, s * 0.3, "iron", s * 0.05))
        return out

    def bracket_lantern(self, a, t, n, u, z, reach=2.4, s=1.1):
        """A lantern hung from an iron bracket reaching out of a face at (u, z)."""
        a, t, n = _v(a), _v(t).normalized(), _v(n).normalized()
        p = a + t * u + Z * z
        out = [self.beam(p - n * 0.4, p + n * reach, 0.18, "iron"),
               self.beam(p - n * 0.2 - Z * 1.4, p + n * reach * 0.6, 0.13, "iron")]
        return out + self.lantern(p + n * reach, s, chain=0.8)

    def cable_drum(self, c, t, r=1.2, w=3.0):
        """A winch: a drum r across wound with cable, between two iron cheeks on a timber frame, a
        crank on one side."""
        c, t = _v(c), _v(t).normalized()
        axle = c + Z * (r + 1.2)
        out = [self.tube([axle - t * w / 2, axle + t * w / 2], [r, r], "chain", k=8, cap0="iron", cap1="iron")]
        for e in (-1, 1):
            m = axle + t * (e * (w / 2 + 0.15))
            out.append(self.tube([m - t * 0.15, m + t * 0.15], [r * 1.5, r * 1.5], "iron", k=8, cap0="trim", cap1="trim"))
            out.append(self.beam(m + t * e * 0.4 - Z * (r + 1.4), m + t * e * 0.4, 0.3, "timber"))
        k = axle + t * (w / 2 + 0.8)
        out.append(self.beam(axle + t * (w / 2), k, 0.15, "iron"))
        out.append(self.beam(k, k + Z * 1.4, 0.14, "iron"))
        return out

    def tool_rack(self, c, t, n, w=3.6, h=3.6):
        """A rack against a wall (n out of it): a rail on two posts, tongs, hammers and bars on it."""
        c, t, n = _v(c), _v(t).normalized(), _v(n).normalized()
        out = [self.beam(c + t * (e * w / 2) - Z * 0.3, c + t * (e * w / 2) + Z * h, 0.2, "timber") for e in (-1, 1)]
        out.append(self.beam(c - t * w / 2 + Z * (h - 0.4), c + t * w / 2 + Z * (h - 0.4), 0.16, "iron"))
        for i in range(4):
            u = -w / 2 + w * (i + 0.5) / 4
            top = c + t * u + n * 0.3 + Z * (h - 0.4)
            out.append(self.beam(top, top - Z * h * 0.7 + n * 0.2, 0.1, "iron"))
            if i % 2:
                out.append(self.beam(top - Z * h * 0.7 - t * 0.35, top - Z * h * 0.7 + t * 0.35, 0.22, "trim"))
        return out

    def floor_grate(self, c, t, w=3.0, d=3.0, bars=4):
        """A raised iron grate over a glowing pit: an iron kerb, embers inside, bars across."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        P = lambda u, dd, z: c + t * u + n * dd + Z * z          # noqa: E731
        ring = lambda s, z: [P(-w / 2 * s, -d / 2 * s, z), P(w / 2 * s, -d / 2 * s, z), P(w / 2 * s, d / 2 * s, z),  # noqa: E731
                             P(-w / 2 * s, d / 2 * s, z)]
        out = [loft([ring(1.0, -0.3), ring(1.0, 0.6), ring(0.82, 0.6), ring(0.82, 0.25)], ["iron", "trim", "ember"],
                    cap0=("iron", False), cap1=("ember", True))]
        for i in range(bars):
            u = -w / 2 + w * (i + 1) / (bars + 1)
            out.append(self.beam(P(u, -d * 0.45, 0.62), P(u, d * 0.45, 0.62), 0.12, "iron"))
        return out

    def cable(self, p, q, sag=4.0, r=0.22, steps=8):
        """A slack iron cable from p to q sagging `sag` at the middle (a k=4 tube)."""
        p, q = _v(p), _v(q)
        pts = [p.lerp(q, i / steps) - Z * (sag * 4 * (i / steps) * (1 - i / steps)) for i in range(steps + 1)]
        return self.tube(pts, [r] * len(pts), "chain", k=4, cap0="chain", cap1="chain")

