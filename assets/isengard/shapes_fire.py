"""The Isengard kit's fire (a mixin of IsengardShapes, assets/isengard/shapes.py): flames and
molten metal painted bright enough to read as fire by day ("flame": near-white orange; "ember":
orange), and the small forge furniture round them.

The game's own flicker (EA's orcfire: fire cards on an animated sheet and particle systems on
bones, `ParticleSysBone`) comes from a separate framework job: every fire records its point, and
the recipe lists them as `fire_points`. The painted flame tongues are off (PAINTED_FLAMES).

    fire(c, kind)                      record a fire point for the real-fire job (Building.fire_points)
    flames(c, r, h, n)                 a fire: its point recorded; painted tongues only if PAINTED_FLAMES
    runnel(points, w)                  an iron trough with molten metal in it
    slag_cart(c, t, s)                 a cart on four wheels heaped with glowing slag
    ingots(c, t, rows)                 a stack of iron ingots, the top row still glowing
    post_lantern(c, h)                 an ember lantern on an iron post with a spike
    glowing_work(c, t, s)              a white-hot bar lying on an anvil
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft


def _v(p):
    return V((p[0], p[1], p[2] if len(p) > 2 else 0.0))


class FireKit:
    PAINTED_FLAMES = False                  # geometry flames read as pale plastic (Max): real fire comes from
                                            # the game's particle systems at the recipe's fire_points

    def fire(self, c, kind):
        """Record a fire point (x, y, z, kind) for the real-fire job (Building.fire_points); a kit
        whose `fire_log` is a list collects them while a design runs."""
        log = getattr(self, "fire_log", None)
        if log is not None:
            c = _v(c)
            log.append((round(c.x, 1), round(c.y, 1), round(c.z, 1), kind))

    def flames(self, c, r, h, n=4, seed=0.0, tag="flame", kind="fire"):
        """A fire at c: its point recorded (fire()); flame tongues (n, r across, up to h tall,
        three-sided, twisting to points) only when PAINTED_FLAMES."""
        c = _v(c)
        self.fire(c, kind)
        if not self.PAINTED_FLAMES:
            return []
        out = []
        for i in range(n):
            a = seed + 2 * math.pi * i / n
            d = V((math.cos(a), math.sin(a), 0))
            s = V((-d.y, d.x, 0))
            hh = h * (0.62 + 0.38 * (0.5 + 0.5 * math.sin(seed * 3.1 + i * 2.3)))
            base = c + d * r * 0.45
            pts = [base - Z * 0.2, base + Z * hh * 0.45 - d * r * 0.2 + s * r * 0.15, base + Z * hh - d * r * 0.35 - s * r * 0.1]
            out.append(self.tube(pts, [r * 0.7, r * 0.5, 0.0], tag, k=3, cap0=tag, cap1=None, phase=a))
        return out

    def runnel(self, points, w=0.9):
        """A square iron trough through `points` with a molten strip in it."""
        pts = [_v(p) for p in points]
        out = [self.tube(pts, [w] * len(pts), "iron", k=4, cap0="iron", cap1="iron", phase=math.pi / 4)]
        out.append(self.tube([p + Z * (w * 0.62) for p in pts], [w * 0.6] * len(pts), "ember", k=4, cap0="ember",
                             cap1="ember", phase=math.pi / 4, squash=0.35))
        return out

    def slag_cart(self, c, t, s=1.0):
        """A cart along t: an iron box on four wheels, heaped with glowing slag, a pull bar."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        P = lambda u, d, z: c + t * u + n * d + Z * z          # noqa: E731
        box = [[P(-1.6 * s, -1.0 * s, z), P(1.6 * s, -1.0 * s, z), P(1.6 * s, 1.0 * s, z), P(-1.6 * s, 1.0 * s, z)]
               for z in (0.8 * s, 2.2 * s)]
        out = [loft(box, ["iron"], cap0=("iron", True), cap1=("ember", True))]
        out.append(self.facet_lump(P(0, 0, 2.3 * s), 0.9 * s, "ember"))
        for u in (-1.0, 1.0):
            for d in (-1.1, 1.1):
                p = P(u * s, d * s, 0.7 * s)
                out.append(self.tube([p - n * 0.2 * s, p + n * 0.2 * s], [0.65 * s, 0.65 * s], "iron", k=6, cap0="trim",
                                     cap1="trim"))
        out.append(self.beam(P(1.6 * s, 0, 1.3 * s), P(3.2 * s, 0, 0.9 * s), 0.12 * s, "iron"))
        return out

    def ingots(self, c, t, rows=3, s=1.0):
        """Ingots stacked crosswise, `rows` high; the top row glowing."""
        c, t = _v(c), _v(t).normalized()
        n = V((-t.y, t.x, 0))
        out = []
        for j in range(rows):
            a, b = (t, n) if j % 2 == 0 else (n, t)
            for i in (-1, 0, 1):
                m = c + b * (i * 0.75 * s) + Z * (0.3 * s + j * 0.55 * s)
                out.append(self.beam(m - a * 1.1 * s, m + a * 1.1 * s, 0.27 * s, "ember" if j == rows - 1 else "iron"))
        return out

    def post_lantern(self, c, h=4.5):
        """An iron post with a spike on top and an ember lantern hung from an arm."""
        c = _v(c)
        out = [self.beam(c - Z * 0.3, c + Z * h, 0.2, "iron"), self.beam(c + Z * h, c + Z * (h + 1.4), 0.24, "trim", 0.0)]
        arm = c + Z * (h - 0.4)
        out.append(self.beam(arm, arm + V((1.2, 0, 0)), 0.12, "iron"))
        out += self.lantern(arm + V((1.2, 0, 0)), 0.9, chain=0.5)
        return out

    def glowing_work(self, c, t, s=1.0):
        """A white-hot bar lying on an anvil (c: the anvil's face), a small flame off it."""
        c, t = _v(c), _v(t).normalized()
        return [self.beam(c - t * 1.1 * s + Z * 0.15, c + t * 1.0 * s + Z * 0.15, 0.2 * s, "ember")]
