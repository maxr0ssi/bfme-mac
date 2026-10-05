"""Mordor's palantir, cut from the Barad-dur citadel: the towers' black fluted iron under an ash-grey
crust, split by glowing lava seams, a lava channel round the glass, the crown windows burning
orange (a rare one Morgul green), hard steel on the inner edge and the crown of blades outside.
Bold at the focal points (the joint, the bar's ends, the top): flames lick up from the channel,
embers fly, a fleck of green witch-fire; steel blades of the crown rise past the frame over the
joint and off the top left. The Eye of fire is the medallion. Iron, windows and lava are the
citadel's own sheet (assets/hud/factions/swatches.py)."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import Mat, cells, fbm, fill, noise, smoothstep
from sagekit.paint.palantir.prof import band, local

from . import fx
from .base import Faction, disc, stamp

LAVA = [(0, (0.10, 0.01, 0.0)), (0.35, (0.75, 0.12, 0.0)), (0.7, (1.0, 0.45, 0.04)), (1, (1.0, 0.86, 0.45))]
WITCH = [(0, (0.0, 0.05, 0.01)), (0.35, (0.05, 0.55, 0.10)), (0.7, (0.35, 1.0, 0.30)), (1, (0.92, 1.0, 0.72))]
FIRE = np.array((1.0, 0.36, 0.04), np.float32)
MORGUL = np.array((0.40, 0.95, 0.42), np.float32)


class Mordor(Faction):
    name = "mordor"
    side = "evil"
    IRON, STEEL, ASH, DARK, EMBER = range(5)
    mats = [Mat((0.11, 0.10, 0.095), rough=0.42, edge=(0.5, 0.46, 0.42)),
            Mat((0.80, 0.80, 0.82), rough=0.1, edge=(1, 1, 1)),
            Mat((0.34, 0.33, 0.31), metal=0, rough=0.9),
            Mat((0.012, 0.01, 0.01), metal=0.3, rough=0.8),
            Mat((0.08, 0.015, 0.0), metal=0, rough=0.9)]
    orn_mat = 0
    orn_stops = [(0, (0.01, 0.008, 0.007)), (0.35, (0.08, 0.07, 0.065)), (0.7, (0.34, 0.32, 0.30)), (1, (0.85, 0.82, 0.78))]
    glass_col = (0.02, 0.008, 0.004)
    tick_col = (1.0, 0.45, 0.12)
    rim_glow = ((0.6, 0.14, 0.0), 2.6)
    halo = ((1.0, 0.30, 0.02), 0.32)
    ember = ((1.0, 0.32, 0.03), 0.22)
    bloom = (1.25, (3, 12))
    shine = (0.82, 0.5, 3, (1.0, 0.9, 0.8))
    rim_col = (1.0, 0.45, 0.15)
    sky_col = (0.86, 0.84, 0.82)
    ground_col = (0.16, 0.04, 0.0)
    medals = [("minimap", 180, 8.4)]

    def ring(self, ctx, name):
        I, S, A, D, E = range(5)
        p = prof.P(ctx)
        foc = fx.focus(ctx)
        if name == "bar":
            prof.lip(p, 0.08, I)
            prof.chamfer(p, 0.08, 0.28, S, 1.1, flat=0.2)
            rgb, lum, m, u = self.skin(p, "lava", 0.28, 0.44, E, base=0.05, carve=0.0, v0=0.3, v1=0.7)
            p.emit = p.emit + m[..., None] * fx.heat(0.35 + 0.8 * lum, LAVA) * 1.2
            self.skin(p, "fluted", 0.44, 1.0, I, base=0.8, carve=1.6, gain=1.25, v0=0.1, v1=0.6, aspect=1.0)
            self.seams(p, ctx, 0.44, 1.0, foc)
            return p
        prof.lip(p, 0.04, I)
        prof.chamfer(p, 0.04, 0.12, S, 1.5, flat=0.12)          # hard steel round the glass
        rgb, lum, m, u = self.skin(p, "lava", 0.12, 0.22, E, base=0.05, carve=0.0, v0=0.3, v1=0.7, aspect=1.6)
        p.emit = p.emit + m[..., None] * fx.heat(0.45 + 0.8 * lum, LAVA) * 1.25   # the lava channel
        rgb, lum, m, u = self.skin(p, "fluted", 0.22, 0.8, I, base=0.8, carve=1.8, gain=1.3, v0=0.05, v1=0.55,
                                   aspect=1.0)
        w = 0.58 * float(np.median(ctx.bw))
        lx, ly, idx, L = local(ctx, u, w, 2.4 * w)
        frame = (np.abs(lx) < 0.36 * w) & (np.abs(ly) < 0.46 * w) & m
        p.put(frame, 0.95 + 0.1 * u, I)
        win = stamp(self.tex["windows"], lx, ly, 0.72 * w, 0.92 * w)
        p.tint(frame.astype(np.float32), np.clip(win * 1.3, 0, 1))
        hot = np.clip((win[..., 0] - win[..., 1]) * 4.0, 0, 1) * frame
        green = ((idx % 9) == 4)[..., None]                       # a rare window burns Morgul green
        flick = 0.9 + 0.4 * noise(idx * 2.3 + 0.5, 0.5 + 0 * idx, 7)
        p.emit = p.emit + (hot * flick * 1.5)[..., None] * np.where(green, MORGUL, FIRE * 1.3)
        prof.hammer(p, 0.15, 0.5, mask=m)
        self.seams(p, ctx, 0.22, 0.8, foc)
        # at the focal points flames lick up from the channel; one tongue in a dozen burns green
        fl = fx.flames(ctx, 0.2, 0.78, 1.3 * w, seed=4, lean=0.4) * smoothstep(0.25, 0.6, foc)
        gtongue = (np.floor(ctx.t / (1.3 * w)) % 12 == 5)[..., None]
        on = smoothstep(0.02, 0.2, fl)[..., None] * 1.2
        p.emit = p.emit + np.where(gtongue, fx.heat(fl * 1.2, WITCH), fx.heat(fl * 1.2, LAVA)) * on
        # the Barad-dur crown: steel blades along the outer edge, fire glinting between
        u, w, m = band(ctx, 0.8, 0.98)
        lx, ly, idx, L = local(ctx, u, w, 2.0 * w, 0.5)
        half = 0.5 * L * np.clip(1 - u, 0, 1) ** 0.9
        inside = np.abs(lx + 0.25 * L * u) < half
        bl = 0.4 + 1.2 * (1 - np.abs(lx + 0.25 * L * u) / np.maximum(half, 1e-3)) * (1 - 0.4 * u)
        p.put(m, 0.12 + 0.0 * u, D)
        p.put(m & inside, bl, S)
        root = m & ~inside & (u < 0.4)
        p.emit = p.emit + (root * (0.5 + 0.9 * foc) * (1 - u / 0.4))[..., None] * FIRE
        return p

    def seams(self, p, ctx, s0, s1, foc):
        """Lava seams cracking the iron: a sparse network, hotter and denser near the focal points."""
        m = (ctx.s >= s0) & (ctx.s < s1)
        f1, f2 = cells(ctx.t * 0.42, ctx.y * 0.42, 2)
        crack = np.clip(1 - (f2 - f1) / 0.09, 0, 1) * m
        crack = crack * smoothstep(0.5 - 0.25 * foc, 0.62 - 0.25 * foc, noise(ctx.t * 0.08, ctx.y * 0.08, 4))
        p.h = p.h - 0.7 * crack
        p.mat = np.where(crack > 0.4, self.EMBER, p.mat)
        p.aw = p.aw * (1 - crack)
        p.emit = p.emit + fx.heat(crack * (0.75 + 0.35 * foc), LAVA) * smoothstep(0.05, 0.3, crack)[..., None]

    def post(self, col, env):
        """An ash-grey crust on the up-facing iron, embers flying at the focal points, then the bloom."""
        n, c = env["n"], env["ctx"]["minimap"]
        up = np.clip(-n[..., 1] * 1.2 + 0.25, 0, 1)
        dust = smoothstep(0.42, 0.66, fbm(c.x * 0.5, c.yy * 0.5, 4, 9)) * up
        iron = (((env["mat"] == self.IRON) | (env["mat"] == self.DARK)) * dust)[..., None] * 0.6
        col = col * (1 - iron) + iron * np.array((0.42, 0.40, 0.37), np.float32) * (0.8 + 0.4 * up[..., None])
        pts = [(243, 40), (30, 214), (222, 214), (128, 8)] if c.x.shape[1] > 1200 else [(30, 214), (222, 214), (128, 8)]
        sp = fx.sparks(c.x, c.yy, pts, 16, 9.0, seed=11) * np.clip(env["a4"] * 1.5, 0, 1)
        col = col + sp[..., None] * np.array((1.0, 0.6, 0.15), np.float32) * 1.4
        return Faction.post(self, col, env)

    def medal(self, lx, ly, R):
        # the Eye: a slit of fire in a black iron disc
        h, mat, cov = disc(lx, ly, R, self.STEEL, self.IRON, rim_w=1.1, field_h=0.6)
        d, a, b = prof.leaf(lx, ly, R * 1.45, R * 0.75, 0.0)
        eye = fill(d)
        h = np.where(d < 0, 0.3, h)
        mat = np.where(d < 0, self.EMBER, mat)
        pupil = np.abs(lx) - 0.35 * np.sqrt(np.clip(1 - (ly / (R * 0.36)) ** 2, 0, 1))
        glow = eye * np.exp(-(np.hypot(lx * 1.3, ly * 2.2) / (R * 0.55)) ** 2)
        em = (eye * (0.7 + 1.3 * glow))[..., None] * np.array((1.0, 0.42, 0.06), np.float32)
        em *= (1 - 0.95 * fill(pupil) * (np.abs(ly) < R * 0.36))[..., None]
        return h, mat.astype(np.int16), cov, em


LOOK = Mordor
