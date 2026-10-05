"""Angmar's palantir, cut from Carn Dum: the citadel's warm timber walk round the glass (its ring of
planks), its blue-black stone wall, the blue steel scale roof as the outer coping, black horn tines
of the Witch-king's crown hooked over the wall with a frost line down their edge, rime in the
hollows; the crown of tines over a cold fire as the medallion. Bold at the focal points (the joint,
the bar's ends, the top): translucent ice crystals grow from the iron with a cold glow inside,
frost creeps over the rim, cold glints; past the frame, ice crystals rise over the joint, icicles
hang off the bar's ends and a horn tine hooks off the top left. Timber, stone, scales and horn are
the citadel's own sheet (assets/hud/factions/swatches.py)."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import Mat, cells, dome, fbm, fill, noise, sd_poly, smoothstep
from sagekit.paint.palantir.prof import local

from . import fx
from .base import Faction, disc, zero3

COLD = np.array((0.30, 0.62, 1.0), np.float32)


def tine(lx, ly, w, lean=0.35):
    """A hooked horn tine rising outward (+ly) and curving along the ring."""
    t = np.clip((ly + 0.5 * w) / w, 0, 1)
    cx = lean * w * t * t
    half = 0.2 * w * (1 - t) ** 0.8 + 0.01
    return np.where((ly > -0.5 * w) & (ly < 0.5 * w), np.abs(lx - cx) - half, 9.0), t, (lx - cx) / half


class Angmar(Faction):
    name = "angmar"
    side = "evil"
    IRON, STEEL, STONE, HORN, DARK, WOOD, ICE = range(7)
    mats = [Mat((0.14, 0.16, 0.21), rough=0.36, edge=(0.7, 0.82, 0.95)),
            Mat((0.62, 0.70, 0.80), rough=0.18, edge=(0.95, 1, 1)),
            Mat((0.24, 0.28, 0.36), metal=0, rough=0.7),
            Mat((0.06, 0.06, 0.07), rough=0.3, edge=(0.85, 0.92, 1.0)),
            Mat((0.015, 0.02, 0.035), metal=0.4, rough=0.7),
            Mat((0.55, 0.36, 0.22), metal=0, rough=0.6),
            Mat((0.62, 0.84, 1.0), metal=0, rough=0.03, edge=(1, 1, 1), emit=(0.03, 0.08, 0.16))]
    orn_mat = 3
    orn_stops = [(0, (0.01, 0.01, 0.015)), (0.4, (0.07, 0.075, 0.09)), (0.72, (0.36, 0.40, 0.48)), (1, (0.92, 0.96, 1))]
    glass_col = (0.01, 0.025, 0.05)
    tick_col = (0.6, 0.82, 1.0)
    rim_glow = ((0.12, 0.30, 0.55), 2.6)
    halo = ((0.35, 0.65, 1.0), 0.12)
    rim_col = (0.5, 0.8, 1.0)
    sky_col = (0.88, 0.95, 1.0)
    ground_col = (0.02, 0.04, 0.08)
    patina = 0.1
    medals = [("minimap", 180, 8.8)]
    bloom = (1.0, (3, 10))
    shine = (0.78, 0.6, 3, (0.8, 0.92, 1.0))
    glint = (46, 0.8, (0.8, 0.92, 1.0), (8, 20))

    def ice(self, p, ctx, s0, s1, foc, every, seed=0):
        """Ice crystals growing outward from [s0, s1], clustered at the focal points."""
        ctx_s = ctx.s
        u = (ctx_s - s0) / (s1 - s0)
        w = (s1 - s0) * float(np.median(ctx.bw))
        lx, ly, idx, L = local(ctx, u, w, every * w)
        keep = (foc > 0.32) | ((idx % 9) == seed % 9)
        tilt = (noise(idx * 3.7 + seed, 0.5 + 0 * idx, 5) - 0.5) * 0.9
        size = 0.7 + 0.5 * noise(idx * 1.9 + seed, 0.2 + 0 * idx, 6)
        clen = w * size * (0.75 + 0.5 * foc)
        cd, cx_, cy_ = prof.crystal(lx, ly - 0.5 * w + 0.5 * clen, clen, 0.38 * w * size, np.pi / 2 + tilt)
        facet = np.clip(1 - np.abs(cy_) / (0.19 * w * size), 0, 1) ** 0.6
        cov = fill(cd) * keep * (u > -0.1) * (u < 1.05)
        p.over(cov, 1.2 + 1.4 * facet, self.ICE)
        p.tint(cov, fx.crystal_glass(np.full(cov.shape, 0.3, np.float32) * facet, facet))
        core = np.exp(-(cy_ / (0.12 * w)) ** 2) * cov
        p.glow(core * (0.35 + 0.4 * foc), COLD)
        return cov

    def ring(self, ctx, name):
        I, S, St, Ho, D, Wd = range(6)
        p = prof.P(ctx)
        if name == "bar":
            prof.lip(p, 0.08, I)
            prof.chamfer(p, 0.08, 0.28, S, 1.1, flat=0.3)
            self.skin(p, "planks", 0.28, 0.62, Wd, base=0.7, carve=1.4, gain=1.0, v0=0.1, v1=0.9, aspect=3.0,
                      wrap="mirror")
            prof.bead(p, 0.62, 0.68, I, 0.6)
            self.skin(p, "scales", 0.68, 1.0, I, base=0.7, carve=1.6, gain=1.2, v0=0.08, v1=0.2)
            foc = fx.focus(ctx)
            self.ice(p, ctx, 0.2, 1.0, foc * (foc > 0.3), 0.9, seed=3)
            return p
        prof.lip(p, 0.04, I)
        prof.chamfer(p, 0.04, 0.12, S, 1.4, flat=0.3)            # frosted steel round the glass
        rgb, lum, m, u = self.skin(p, "planks", 0.12, 0.38, Wd, base=0.75, carve=0.6, gain=1.15, v0=0.08, v1=0.9,
                                   aspect=3.0, wrap="mirror")     # the timber walk, its planks across it
        lx, ly, idx, L = local(ctx, u, 1.0, 2.6)
        seam = np.exp(-((np.abs(lx) - 0.5 * L) / 0.22) ** 2) * m
        p.h = p.h - 0.35 * seam
        p.aw = p.aw * (1 - 0.7 * seam)
        p.mat = np.where(seam > 0.5, D, p.mat)
        prof.bead(p, 0.38, 0.43, I, 0.7, base=0.4)
        rgb, lum, m, u = self.skin(p, "blocks", 0.43, 0.8, St, base=0.85, carve=1.6, gain=1.15, v0=0.3, v1=0.62,
                                   aspect=1.0, wrap="mirror")
        self.skin(p, "scales", 0.8, 0.99, I, base=0.8, carve=1.6, gain=1.0, v0=0.08, v1=0.2)
        # the crown's horn tines hooked over the wall, every few blocks
        u2 = (ctx.s - 0.16) / 0.84
        w = 0.84 * float(np.median(ctx.bw))
        lx, ly, idx, L = local(ctx, u2, w, 2.4 * w)
        d, t, x = tine(lx, ly, w, 0.42)
        cov = fill(d) * (ctx.s > 0.16) * (ctx.s < 1.0)
        p.over(cov, 1.1 + 1.2 * np.sqrt(np.clip(1 - x * x, 0, 1)) * (1 - 0.3 * t), Ho)
        frost = cov * np.exp(-((x + 0.6) / 0.28) ** 2)            # the white frost line down its edge
        p.tint(frost, np.full(d.shape + (3,), 0.9, np.float32))
        self.ice(p, ctx, 0.45, 1.0, fx.focus(ctx), 0.75, seed=1)   # ice crystals, clustered at the focal points
        return p

    def post(self, col, env):
        """Rime in the hollows of the stone and the scales."""
        ctx = env["ctx"]["minimap"]
        x, y, a4 = ctx.x, ctx.yy, env["a4"]
        f1, f2 = cells(x * 1.6, y * 1.6, 3)
        grain = np.clip((f2 - f1) * 2.2, 0, 1)
        patch = smoothstep(0.42, 0.62, fbm(x * 0.12, y * 0.12, 4, 1))
        stone = (env["mat"] == self.STONE) | (env["mat"] == self.IRON)
        foc = fx.focus(ctx)
        rime = np.clip(env["cav"] * 1.4 * patch * stone + 0.75 * foc * (stone | (env["mat"] == self.STEEL))
                       * smoothstep(0.3, 0.6, fbm(x * 0.4, y * 0.4, 3, 7)), 0, 1) * smoothstep(0.5, 0.9, a4)
        rime *= smoothstep(-0.1, 0.05, env["bar"].s)
        rc = np.array((0.80, 0.90, 1.0), np.float32)
        col = col * (1 - 0.6 * rime[..., None]) + rc * (0.6 * rime[..., None]) * (0.7 + 0.4 * grain[..., None])
        return self.signature(col, env)

    def protrude(self, x, y):
        """Past the frame: ice crystals rising over the joint, icicles off the bar's ends, a horn tine
        hooking off the top left with frost down its edge."""
        out = []
        rng = np.random.default_rng(9)
        spikes = [(240, 46, -88, 30, 6.5), (231, 47, -112, 20, 5.0), (250, 50, -66, 22, 5.0), (222, 44, -128, 12, 3.6),
                  (127, 6, -90, 0, 0)]
        drips = [(x0, 229.0, 90, rng.uniform(7, 19), rng.uniform(2.6, 4.0)) for x0 in (13, 19, 25, 31, 37, 221, 227, 233, 239)]
        for x0, y0, ang, L, W in spikes[:4] + drips:
            d, t, a = fx.spike(x, y, x0, y0, ang, L, W, 0.0, p=1.0 if ang == 90 else 0.7)
            cov = fill(d)
            facet = np.clip(1 - np.abs(a), 0, 1) ** 0.5
            alb = fx.crystal_glass(0.25 * facet, facet)
            core = np.exp(-(a / 0.35) ** 2) * cov * (1 - 0.6 * t)
            out.append(fx.layer(1.0 + 1.3 * facet * (1 - 0.3 * t), self.ICE, cov, (core * 0.55)[..., None] * COLD,
                                alb, cov))
        d, t, a = fx.spike(x, y, 42, 41, -138, 30, 7.0, -0.3)
        cov = fill(d)
        frost = np.exp(-((a + 0.6) / 0.3) ** 2) * cov
        out.append(fx.layer(fx.ridge(a, t, 0.9, 1.5), self.HORN, cov, None,
                            np.full(cov.shape + (3,), 0.92, np.float32), frost))
        return out

    def medal(self, lx, ly, R):
        """The Witch-king's crown: black horn tines round a cold blue fire, in an iron ring."""
        h, mat, cov = disc(lx, ly, R, self.STEEL, self.DARK, rim_w=1.2, field_h=0.5)
        fire = np.exp(-((lx / (R * 0.35)) ** 2 + ((ly + 0.1 * R) / (R * 0.55)) ** 2))
        em = (fire * (np.hypot(lx, ly) < R - 1.2))[..., None] * np.array((0.25, 0.55, 1.0), np.float32) * 0.9
        for k, (ox, lean) in enumerate(((-0.5, -0.45), (-0.17, -0.15), (0.17, 0.15), (0.5, 0.45))):
            d, t, x = tine(lx - ox * R, ly + 0.1 * R, R * 1.3, lean)
            inside = (d < 0) & (np.hypot(lx, ly) < R - 1.2)
            h = np.where(inside, 0.7 + 1.0 * np.sqrt(np.clip(1 - x * x, 0, 1)), h)
            mat = np.where(inside, self.HORN, mat)
            em = em * (1 - inside[..., None])
        return h, mat.astype(np.int16), cov, em


LOOK = Angmar
