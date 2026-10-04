"""Angmar's palantir: frost-rimed iron, Carn Dum ice crystals, rime and glints."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import (Mat, blur, cells, dome, fbm, fill, noise, sd_box, sd_circle, sd_poly,
                                         sd_seg, sd_star, smoothstep)
from sagekit.paint.palantir.prof import band, local

from .base import Faction, disc, zero3

class Angmar(Faction):
    name = "angmar"
    side = "evil"
    IRON, STEEL, ICE, RIME, DARK, GLOW = range(6)
    mats = [Mat((0.15, 0.18, 0.24), rough=0.36, edge=(0.7, 0.82, 0.95)),
            Mat((0.62, 0.70, 0.80), rough=0.18, edge=(0.95, 1, 1)),
            Mat((0.60, 0.76, 0.88), metal=0, rough=0.03, emit=(0.03, 0.07, 0.12)),
            Mat((0.86, 0.93, 1.0), metal=0, rough=0.65),
            Mat((0.015, 0.02, 0.035), metal=0.4, rough=0.7),
            Mat((0.10, 0.2, 0.3), metal=0, rough=0.3, emit=(0.16, 0.36, 0.6))]
    orn_mat = 0
    orn_stops = [(0, (0.01, 0.012, 0.02)), (0.35, (0.10, 0.13, 0.19)), (0.7, (0.45, 0.55, 0.68)), (1, (0.9, 0.96, 1))]
    glass_col = (0.01, 0.025, 0.05)
    tick_col = (0.6, 0.82, 1.0)
    rim_glow = ((0.12, 0.30, 0.55), 2.6)
    halo = ((0.35, 0.65, 1.0), 0.16)
    rim_col = (0.5, 0.8, 1.0)
    sky_col = (0.88, 0.95, 1.0)
    ground_col = (0.02, 0.04, 0.08)
    medals = [("minimap", 180, 8.4)]

    def ring(self, ctx, name):
        I, S, Ic, R, D, G = range(6)
        p = prof.P(ctx)
        if name == "bar":
            prof.lip(p, 0.08, I)
            prof.chamfer(p, 0.08, 0.32, S, 1.1, flat=0.3)
            u, w, m = band(ctx, 0.32, 0.4)
            p.put(m, 0.05 + 0.0 * u, G)
            u, w, m = prof.flat(p, 0.4, 1.0, I, 0.8, 0.2)
            lx, ly, idx, L = local(ctx, u, w, 3.0 * w)
            cd, cx_, cy_ = prof.crystal(lx, ly, 1.7 * w, 0.62 * w)
            facet = 1 - np.abs(cy_) / (0.31 * w)
            p.over(fill(cd) * m, 0.6 + 1.0 * np.clip(facet, 0, 1), Ic)
            return p
        prof.lip(p, 0.05, I)
        prof.chamfer(p, 0.05, 0.16, S, 1.4, flat=0.3)
        u, w, m = band(ctx, 0.16, 0.2)
        p.put(m, 0.05 + 0.0 * u, G)
        # iron plates with Carn Dum notches, a blue crystal set between each pair
        u, w, m = band(ctx, 0.2, 0.83)
        lx, ly, idx, L = local(ctx, u, w, 2.5 * w)
        plate = 0.8 + 0.12 * prof.half_round(u)
        notch = np.abs(np.abs(lx) - 0.5 * L) + 0.6 * np.abs(ly) - 0.25 * w
        p.put(m, plate, I)
        p.over(fill(-notch - 0.0) * 0 + (notch < 0) * m, np.full(u.shape, 0.2, np.float32), D)
        clen = (1.15 + 0.4 * noise(idx * 2.7, 0 * idx, 5)) * w
        cd, cx_, cy_ = prof.crystal(lx, ly, clen, 0.52 * w)
        facet = np.clip(1 - np.abs(cy_) / (0.26 * w), 0, 1) * np.clip(1 - np.abs(cx_) / (0.5 * clen), 0, 1) ** 0.3
        setting = cd - 0.55
        p.over(fill(setting) * m * (cd > 0), 1.05 + 0.2 * dome(setting, 0.4), S)
        p.over(fill(cd) * m, 0.5 + 1.1 * facet, Ic)
        core = np.exp(-(cx_ / (0.35 * w)) ** 2 - (cy_ / (0.12 * w)) ** 2) * (cd < 0) * m
        p.glow(core * 0.35, (0.55, 0.8, 1.0))
        prof.hammer(p, 0.08, 0.6, mask=m)
        prof.groove(p, 0.83, 0.86, D)
        # serrated outer edge
        u, w, m = band(ctx, 0.86, 0.98)
        lx, ly, idx, L = local(ctx, u, w, 1.8 * w)
        tooth = np.clip(1 - np.abs(lx) / (0.5 * L), 0, 1)
        p.put(m, 0.4 + 1.0 * prof.half_round(u) * (0.55 + 0.45 * tooth), S)
        return p

    def post(self, col, env):
        n = env["n"]
        ctx = env["ctx"]["minimap"]
        x, y = ctx.x, ctx.yy
        a4 = env["a4"]
        up = np.clip(-n[..., 1] * 1.4 + 0.15, 0, 1)
        f1, f2 = cells(x * 1.6, y * 1.6, 3)
        grain = np.clip((f2 - f1) * 2.2, 0, 1)
        patch = smoothstep(0.34, 0.56, fbm(x * 0.12, y * 0.12, 4, 1))
        rime = np.clip(1.3 * up * patch * (0.5 + 0.5 * grain) + env["cav"] * 0.8 * patch, 0, 1)
        rime *= smoothstep(0.5, 0.9, a4) * smoothstep(-0.1, 0.05, env["bar"].s)    # the bar's slot stays clear
        rc = np.array((0.80, 0.90, 1.0), np.float32)
        col = col * (1 - 0.85 * rime[..., None]) + rc * (0.85 * rime[..., None]) * (0.7 + 0.4 * grain[..., None])
        # frost glints: tiny 4-point stars on the brightest rime
        lum = col.mean(-1) * rime
        rng = np.random.default_rng(3)
        ys, xs = np.where((lum > 0.62) & (a4 > 0.95))
        if len(xs):
            pick = rng.choice(len(xs), size=min(40, len(xs)), replace=False)
            gl = np.zeros(a4.shape, np.float32)
            for i in pick:
                cy_, cx_ = ys[i], xs[i]
                L_ = rng.uniform(5, 11)
                y0, y1 = max(0, cy_ - 12), min(a4.shape[0], cy_ + 13)
                x0, x1 = max(0, cx_ - 12), min(a4.shape[1], cx_ + 13)
                yy, xx = np.mgrid[y0:y1, x0:x1]
                dx, dy = np.abs(xx - cx_).astype(np.float32), np.abs(yy - cy_).astype(np.float32)
                star = np.exp(-dy / 0.7) * np.clip(1 - dx / L_, 0, 1) + np.exp(-dx / 0.7) * np.clip(1 - dy / L_, 0, 1)
                star += np.exp(-(dx * dx + dy * dy) / 4.0)
                gl[y0:y1, x0:x1] = np.maximum(gl[y0:y1, x0:x1], star)
            col = col + gl[..., None] * np.array((0.85, 0.95, 1.0), np.float32)
        return col

    def glass(self, x4, lum, a4, ctx):
        col = Faction.glass(self, x4, lum, a4, ctx)
        # frost creeping from the rim into the glass
        for r, ok in self.rims(ctx):
            din = r.r_in - r.r
            f1, f2 = cells(r.x * 0.9, r.yy * 0.9, 5)
            fern = np.clip(1 - (f2 - f1) / 0.12, 0, 1)
            reach = 4.0 + 7.0 * fbm(np.radians(r.deg) * 6, 0 * r.deg, 3, 2)
            g = np.clip(1 - din / reach, 0, 1) * (din > 0) * ok
            col += (g * (0.25 + 0.6 * fern) * 0.55)[..., None] * np.array((0.7, 0.86, 1.0), np.float32)
        return col

    def medal(self, lx, ly, R):
        h, mat, cov = disc(lx, ly, R, self.STEEL, self.IRON, rim_w=1.2, field_h=0.6)
        st = sd_star(lx, ly, R * 0.78, 6, 0.28)
        a = np.arctan2(ly, lx)
        ridge = np.abs(np.cos(3 * a))
        h = np.where(st < 0, 0.6 + 1.0 * dome(st, 1.0) * (0.7 + 0.3 * ridge), h)
        mat = np.where(st < 0, self.ICE, mat)
        em = (np.exp(-(np.hypot(lx, ly) / (R * 0.35)) ** 2) * (st < 0))[..., None] * np.array((0.4, 0.75, 1.0), np.float32)
        return h, mat.astype(np.int16), cov, em


LOOK = Angmar
