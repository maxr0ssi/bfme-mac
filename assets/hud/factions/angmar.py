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
