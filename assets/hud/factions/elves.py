"""Elves' palantir, cut from the Elven citadel: its dressed ivory ashlar round the glass, pierced by
teal-glass lancet windows like the citadel's arcade, a slate scale roof on the outside edged in
mallorn gold as the gables are, the little arcade frieze along the resource bar; a lancet window in
a gold pointed arch as the medallion. Bold at the focal points (the joint, the bar's ends, the top):
polished gold and moonsilver that flash and sparkle, gold leaf filigree over silver in place of the
slates, a moonlight sheen on the ivory; past the frame a silver spire with gold leaves rises over
the joint and a gold leaf curls off the top left. Ivory, glass, slate and frieze are the citadel's own sheet
(assets/hud/factions/swatches.py)."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import Mat, dome, fill, sd_circle, smoothstep
from sagekit.paint.palantir.prof import local

from . import fx
from .base import Faction, lancet, stamp


class Elves(Faction):
    name = "elves"
    side = "good"
    IVORY, GOLD, GLASS, SLATE, DARK, SILVER = range(6)
    mats = [Mat((0.92, 0.89, 0.82), metal=0, rough=0.45),
            Mat((1.0, 0.80, 0.32), rough=0.07, edge=(1, 0.97, 0.75)),
            Mat((0.10, 0.32, 0.32), metal=0, rough=0.06),
            Mat((0.36, 0.40, 0.46), metal=0.3, rough=0.35),
            Mat((0.10, 0.10, 0.11), metal=0, rough=0.8),
            Mat((0.90, 0.93, 0.98), rough=0.05, edge=(1, 1, 1))]
    orn_mat = 1
    orn_stops = [(0, (0.08, 0.06, 0.02)), (0.25, (0.50, 0.36, 0.10)), (0.55, (1.0, 0.80, 0.34)), (1, (1, 1, 0.9))]
    glass_col = (0.01, 0.03, 0.035)
    tick_col = (0.92, 0.80, 0.50)
    rim_glow = ((0.10, 0.30, 0.30), 2.6)
    sky_col = (1.0, 0.98, 0.94)
    rim_col = (0.75, 0.85, 0.85)
    patina = 0.1
    medals = [("minimap", 180, 8.6)]
    bloom = (0.8, (3, 9))
    shine = (0.7, 1.5, 4, (1.0, 0.95, 0.8))
    glint = (90, 0.8, (1.0, 0.98, 0.92), (12, 28))

    def ring(self, ctx, name):
        Iv, G, Gl, Sl, D = range(5)
        p = prof.P(ctx)
        if name == "bar":
            prof.lip(p, 0.08, Iv)
            prof.bead(p, 0.08, 0.24, G, 1.1)
            prof.groove(p, 0.24, 0.28, D)
            self.skin(p, "scallop", 0.28, 0.9, Iv, base=0.7, carve=1.0, lift=0.3, gain=1.05)
            prof.bead(p, 0.9, 1.02, G, 0.9)
            return p
        prof.lip(p, 0.04, Iv)
        prof.bead(p, 0.04, 0.12, G, 1.3)                         # mallorn gold round the glass
        prof.groove(p, 0.12, 0.14, D)
        rgb, lum, m, u = self.skin(p, "ashlar", 0.14, 0.52, Iv, base=0.85, carve=1.2, v0=0.05, v1=0.75,
                                   aspect=1.0, wrap="mirror", gain=1.05)
        w = 0.38 * float(np.median(ctx.bw))
        lx, ly, idx, L = local(ctx, u, w, 2.6 * w)
        arch = lancet(lx, ly + 0.02 * w, 0.66 * w, 0.92 * w)
        p.over(fill(arch - 0.45) * m, 1.0 + 0.2 * dome(arch - 0.45, 0.4), G)
        win = fill(arch + 0.35) * m
        p.over(win, np.full(u.shape, 0.45, np.float32), Gl)
        p.tint(win, np.clip(stamp(self.tex["window"], lx, ly, 0.66 * w, 0.92 * w) * 1.15, 0, 1))
        prof.bead(p, 0.52, 0.57, self.SILVER, 0.8, base=0.5)     # a moonsilver fillet
        self.skin(p, "roof", 0.57, 0.93, Sl, base=0.6, carve=1.6, v0=0.0, v1=0.3, aspect=1.0, gain=1.1)
        self.filigree(p, ctx, 0.57, 0.93, smoothstep(0.18, 0.38, fx.focus(ctx)))
        prof.bead(p, 0.93, 1.02, G, 0.9)
        prof.turned(p, 0.02)
        return p

    def filigree(self, p, ctx, s0, s1, on):
        """Gold leaf-and-vine filigree on polished moonsilver, where `on` (the focal points)."""
        u = (ctx.s - s0) / (s1 - s0)
        m = (ctx.s >= s0) & (ctx.s < s1)
        w = (s1 - s0) * float(np.median(ctx.bw))
        cov = on * m
        p.over(cov, 0.75 + 0.1 * prof.half_round(u), self.SILVER)
        lx, ly, idx, L = local(ctx, u, w, 2.6 * w)
        yc = 0.25 * w * np.sin(2 * np.pi * lx / L)
        vine = fill(np.abs(ly - yc) - 0.13 * w) * cov
        p.over(vine, 1.0 + 0.3 * vine, self.GOLD)
        for sg in (1, -1):
            d, a, b = prof.leaf(lx - sg * 0.25 * L, ly + sg * 0.12 * w, 0.62 * w, 0.3 * w, sg * -0.9)
            p.over(fill(d) * cov, 0.95 + 0.5 * dome(d, 0.6), self.GOLD)
            bd = sd_circle(lx + sg * 0.12 * L, ly - sg * 0.25 * w, 0.1 * w)
            p.over(fill(bd) * cov, 1.2 + 0.4 * dome(bd, 0.3), self.SILVER)

    def post(self, col, env):
        """A moonlight sheen on the up-facing ivory, then the shine and glints."""
        n = env["n"]
        up = np.clip(-n[..., 1] * 1.5 + 0.2, 0, 1) * (env["mat"] == self.IVORY)
        col = col + up[..., None] * np.array((0.05, 0.08, 0.14), np.float32)
        return Faction.post(self, col, env)

    def protrude(self, x, y):
        """A moonsilver spire with gold leaves over the joint; a gold leaf curling off the top left."""
        out = []
        d, t, a = fx.spike(x, y, 243, 52, -90, 42, 6.0, 0.0, p=0.9)
        out.append(fx.layer(fx.ridge(a, t, 1.0, 1.4), self.SILVER, fill(d)))
        for sg in (1, -1):
            d, t, a = fx.spike(x, y, 243 + sg * 2.0, 42, -90 + sg * 40, 22, 9.0, sg * 0.3, p=1.2)
            out.append(fx.layer(fx.ridge(a, t, 1.0, 1.2) - 0.3 * np.exp(-(a / 0.15) ** 2), self.GOLD, fill(d)))
        knot = sd_circle(x - 243, y - 40, 3.4)
        out.append(fx.layer(1.6 + 0.8 * dome(knot, 3.4), self.GOLD, fill(knot)))
        d, t, a = fx.spike(x, y, 42, 41, -138, 28, 10.0, -0.25, p=1.3)
        out.append(fx.layer(fx.ridge(a, t, 1.0, 1.2) - 0.3 * np.exp(-(a / 0.15) ** 2), self.GOLD, fill(d)))
        return out

    def medal(self, lx, ly, R):
        """A lancet window of the citadel in a gold pointed arch."""
        W, H = R * 1.25, R * 1.95
        outer = lancet(lx, ly, W + 2.6, H + 2.6)
        cov = fill(outer)
        inner = lancet(lx, ly, W, H)
        h = np.where(inner < 0, 0.45, 0.6 + 1.0 * dome(outer, 1.2))
        mat = np.where(inner < 0, self.GLASS, self.GOLD).astype(np.int16)
        alb = stamp(self.tex["window"], lx, ly, W, H) * 1.2
        aw = (inner < 0).astype(np.float32)
        return h.astype(np.float32), mat, cov, np.zeros(lx.shape + (3,), np.float32), np.clip(alb, 0, 1), aw


LOOK = Elves
