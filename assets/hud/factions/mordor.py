"""Mordor's palantir (palette F, docs: the Mordor direction): black basalt-iron plates dusted with
ash, cut by wide fire seams whose molten core glows yellow-orange and spills onto the metal; a fire
channel round the glass; hard steel only on the Barad-dur crown's blades and the inner bar; a touch
of Morgul green (one seam in seven burns with witch-fire). The Eye of fire as the medallion."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import Mat, blur, cells, fbm, fill, noise, smoothstep
from sagekit.paint.palantir.prof import band, local

from .base import Faction, disc, zero3

FIRE = np.array((1.0, 0.36, 0.04), np.float32)
CORE = np.array((1.0, 0.66, 0.22), np.float32)
MORGUL = np.array((0.40, 0.80, 0.42), np.float32)


class Mordor(Faction):
    name = "mordor"
    side = "evil"
    IRON, STEEL, ASH, DARK, EMBER = range(5)
    mats = [Mat((0.11, 0.10, 0.095), rough=0.42, edge=(0.5, 0.46, 0.42)),
            Mat((0.78, 0.78, 0.80), rough=0.16, edge=(1, 1, 1)),
            Mat((0.34, 0.33, 0.31), metal=0, rough=0.9),
            Mat((0.012, 0.01, 0.01), metal=0.3, rough=0.8),
            Mat((0.08, 0.015, 0.0), metal=0, rough=0.9)]
    orn_mat = 0
    orn_stops = [(0, (0.01, 0.008, 0.007)), (0.35, (0.07, 0.062, 0.058)), (0.7, (0.30, 0.28, 0.27)), (1, (0.80, 0.78, 0.76))]
    glass_col = (0.02, 0.008, 0.004)
    tick_col = (1.0, 0.45, 0.12)
    rim_glow = ((0.55, 0.12, 0.0), 2.4)
    halo = ((1.0, 0.28, 0.02), 0.26)
    ember = ((1.0, 0.30, 0.03), 0.18)
    rim_col = (1.0, 0.45, 0.15)
    sky_col = (0.86, 0.84, 0.82)
    ground_col = (0.14, 0.035, 0.0)
    medals = [("minimap", 180, 8.4)]

    @staticmethod
    def fire(p, mask, heat, green=None):
        """Molten fire in `mask`: heat 0..1, yellow at the core, orange, red at the edge."""
        h = (heat * mask)[..., None]
        col = FIRE * np.clip(h * 1.3, 0, 1) + (CORE - FIRE) * np.clip(h * 2.2 - 1.4, 0, 1)
        if green is not None:
            g = green[..., None]
            col = col * (1 - g) + MORGUL * np.clip(h * 1.2, 0, 1) * g
        p.emit = p.emit + col

    def ring(self, ctx, name):
        I, S, A, D, E = range(5)
        p = prof.P(ctx)
        if name == "bar":
            prof.lip(p, 0.08, I)
            prof.chamfer(p, 0.08, 0.3, S, 1.1, flat=0.2)
            u, w, m = band(ctx, 0.3, 0.44)
            p.put(m, 0.05 + 0.0 * u, E)
            self.fire(p, m, 0.55 + 0.45 * prof.half_round(u))
            prof.saw(p, 0.44, 1.0, I, 1.1, spacing=1.6, lean=0.6)
            prof.hammer(p, 0.15, 0.6)
            return p
        prof.lip(p, 0.04, I)
        prof.chamfer(p, 0.04, 0.13, S, 1.5, flat=0.12)          # hard steel round the glass
        u, w, m = band(ctx, 0.13, 0.2)                           # the fire channel
        p.put(m, 0.05 + 0.0 * u, E)
        flick = 0.55 + 0.45 * noise(ctx.t * 0.35, 0 * ctx.t, 3)
        self.fire(p, m, (0.35 + 0.45 * prof.half_round(u)) * flick)
        # jagged basalt-iron plates, each rising along the ring to a blade-cut; fire in every cut
        u, w, m = band(ctx, 0.2, 0.8)
        lx, ly, idx, L = local(ctx, u, w, 1.9 * w)
        ph = lx / L + 0.5 + 0.35 * (u - 0.5)
        ph = ph - np.floor(ph)
        p.put(m, 0.35 + 1.1 * smoothstep(0.0, 1.0, (ph - 0.1) / 0.9) + 0.25, I)
        gap = m & (ph < 0.1)
        p.put(gap, 0.05 + 0.0 * u, E)
        green = ((idx % 7) == 3).astype(np.float32)
        core = np.clip(1 - np.abs(ph - 0.05) / 0.05, 0, 1)
        hot = 0.4 + 0.6 * smoothstep(0.3, 0.7, noise(idx * 2.3 + 0.5, 0.5 + 0 * idx, 7))
        self.fire(p, gap, (0.45 + 0.55 * core) * hot * (0.8 + 0.3 * noise(ctx.t * 0.6, ctx.y * 0.6, 6)), green)
        # the cut's lip catches the fire; the plate's top edge is hard steel
        p.mat = np.where(m & (ph > 0.93), S, p.mat)
        # lava cracks across the plates
        f1, f2 = cells(ctx.t * 0.5, ctx.y * 0.5, 2)
        crack = np.clip(1 - (f2 - f1) / 0.07, 0, 1) * m * ~gap
        crack = crack * smoothstep(0.55, 0.65, noise(ctx.t * 0.1, ctx.y * 0.1, 4))
        p.h = p.h - 0.6 * crack
        p.mat = np.where(crack > 0.5, E, p.mat)
        self.fire(p, crack, 0.75 * crack)
        prof.hammer(p, 0.3, 0.5, mask=m)
        # the Barad-dur crown: hooked steel blades along the outer edge, fire glinting between
        u, w, m = band(ctx, 0.8, 0.98)
        lx, ly, idx, L = local(ctx, u, w, 2.0 * w, 0.5)
        half = 0.5 * L * np.clip(1 - u, 0, 1) ** 0.9
        inside = np.abs(lx + 0.25 * L * u) < half
        bl = 0.4 + 1.2 * (1 - np.abs(lx + 0.25 * L * u) / np.maximum(half, 1e-3)) * (1 - 0.4 * u)
        p.put(m, 0.12 + 0.0 * u, D)
        p.put(m & inside, bl, S)
        root = m & ~inside & (u < 0.35)
        self.fire(p, root, 0.45 * (1 - u / 0.35))
        return p

    def post(self, col, env):
        """Ash on the up-facing iron, then the fire's light spilling onto the metal round it."""
        col = Faction.post(self, col, env)
        n, c = env["n"], env["ctx"]["minimap"]
        up = np.clip(-n[..., 1] * 1.2 + 0.1, 0, 1)
        dust = smoothstep(0.45, 0.7, fbm(c.x * 0.6, c.yy * 0.6, 4, 9)) * up
        iron = ((env["mat"] == self.IRON) * dust)[..., None] * 0.55
        col = col * (1 - iron) + iron * np.array((0.36, 0.35, 0.33), np.float32)
        spill = blur(env["emit"], 6, 2)
        return col + 0.6 * spill * np.clip(env["a4"], 0, 1)[..., None]

    def medal(self, lx, ly, R):
        # the Eye: a slit of fire in a black iron disc
        h, mat, cov = disc(lx, ly, R, self.STEEL, self.IRON, rim_w=1.1, field_h=0.6)
        d, a, b = prof.leaf(lx, ly, R * 1.45, R * 0.75, 0.0)
        eye = fill(d)
        h = np.where(d < 0, 0.3, h)
        mat = np.where(d < 0, self.EMBER, mat)
        pupil = np.abs(lx) - 0.35 * np.sqrt(np.clip(1 - (ly / (R * 0.36)) ** 2, 0, 1))
        glow = eye * np.exp(-(np.hypot(lx * 1.3, ly * 2.2) / (R * 0.55)) ** 2)
        em = (eye * (0.55 + 1.0 * glow))[..., None] * np.array((1.0, 0.42, 0.06), np.float32)
        em *= (1 - 0.95 * fill(pupil) * (np.abs(ly) < R * 0.36))[..., None]
        return h, mat.astype(np.int16), cov, em


LOOK = Mordor
