"""Goblins' palantir: crude hammered bronze, bone fangs, skulls and leather lashings."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import (Mat, blur, cells, dome, fbm, fill, noise, sd_box, sd_circle, sd_poly,
                                         sd_seg, sd_star, smoothstep)
from sagekit.paint.palantir.prof import band, local

from .base import Faction, disc, zero3

class Goblins(Faction):
    name = "goblins"
    side = "evil"
    BRONZE, BONE, IRON, LEATHER, DARK, BLOOD = range(6)
    mats = [Mat((0.62, 0.41, 0.18), rough=0.34, edge=(0.95, 0.75, 0.45)),
            Mat((0.84, 0.80, 0.68), metal=0, rough=0.5),
            Mat((0.16, 0.16, 0.17), rough=0.6),
            Mat((0.22, 0.11, 0.05), metal=0, rough=0.75),
            Mat((0.03, 0.02, 0.015), metal=0.2, rough=0.9),
            Mat((0.32, 0.03, 0.03), metal=0, rough=0.35)]
    orn_mat = 0
    orn_stops = [(0, (0.02, 0.012, 0.006)), (0.35, (0.20, 0.12, 0.05)), (0.7, (0.55, 0.38, 0.18)), (1, (0.92, 0.80, 0.58))]
    glass_col = (0.025, 0.012, 0.008)
    tick_col = (0.75, 0.68, 0.55)
    rim_glow = ((0.25, 0.02, 0.02), 2.0)
    sky_col = (1.0, 0.9, 0.78)
    ember = ((0.9, 0.2, 0.12), 0.12)
    medals = [("minimap", 180, 8.6)]

    def ring(self, ctx, name):
        Br, Bo, I, Le, D, Bl = range(6)
        p = prof.P(ctx)
        # crude: the band's s wobbles with the hammer
        s0 = ctx.s
        ctx.s = s0 + prof.wobble(ctx, 0.07)
        if name == "bar":
            prof.lip(p, 0.08, Br)
            prof.bead(p, 0.08, 0.35, Br, 1.1)
            u, w, m = prof.flat(p, 0.38, 1.0, Br, 0.8, 0.3)
            lx, ly, idx, L = local(ctx, u, w, 4.0 * w)
            lash = (np.abs(lx) < 0.7 * w)
            st = ((lx + ly * 0.7) / (0.45 * w)) % 1.0
            p.over(lash * m * (st < 0.62), 1.0 + 0.3 * prof.half_round(st / 0.62), Le)
            prof.hammer(p, 0.4, 0.5)
            ctx.s = s0
            return p
        prof.lip(p, 0.04, Br)
        prof.bead(p, 0.04, 0.16, Br, 1.3)
        # fangs pointing into the glass
        u, w, m = band(ctx, 0.16, 0.46)
        lx, ly, idx, L = local(ctx, u, w, 0.85 * w)
        size = 0.75 + 0.25 * noise(idx * 3.1, 0.0 * idx, 6)
        tipu = 1 - size
        half = 0.46 * L * np.clip((u - tipu) / (1 - tipu), 0, 1) ** 0.75
        inside = (np.abs(lx) < half) & (u > tipu)
        fang = 0.35 + 1.1 * np.sqrt(np.clip(1 - (lx / np.maximum(half, 1e-3)) ** 2, 0, 1)) * (0.5 + 0.5 * u)
        p.put(m, 0.1 + 0.0 * u, D)
        p.put(m & inside, fang, Bo)
        stain = m & inside & (u > 0.8)
        p.mat = np.where(stain & (noise(ctx.t, ctx.y, 2) > 0.55), Bl, p.mat)
        # a crude bronze strap with leather lashings and bone skulls
        u, w, m = prof.flat(p, 0.48, 0.97, Br, 0.8, 0.3)
        lx, ly, idx, L = local(ctx, u, w, 2.2 * w)
        kind = idx % 3
        lash = (np.abs(lx) < 0.45 * w) & (kind != 0)
        st = ((lx + ly * 0.7) / (0.36 * w)) % 1.0
        p.over(lash * m * (st < 0.62), 1.0 + 0.3 * prof.half_round(st / 0.62), Le)
        sk, holes = prof.skull(lx, ly - 0.02 * w, 1.05 * w)
        isk = (kind == 0) & m
        p.over(fill(sk) * isk, 0.9 + 0.7 * dome(sk, 0.9), Bo)
        p.over(fill(holes) * isk * (sk < 0), np.full(u.shape, 0.4, np.float32), D)
        nail = sd_circle(np.abs(lx) - 0.78 * L * 0.5, ly, 0.5)
        p.over(fill(nail) * m * (kind != 0), 1.0 + 0.4 * dome(nail, 0.4), I)
        prof.hammer(p, 0.35, 0.45)
        ctx.s = s0
        return p

    def post(self, col, env):
        col = Faction.post(self, col, env)
        c = env["ctx"]["minimap"]
        patch = smoothstep(0.5, 0.68, fbm(c.x * 0.15, c.yy * 0.15, 4, 3))
        v = np.clip(env["cav"] * 2.0, 0, 1) * patch * (env["mat"] == self.BRONZE) * 0.8
        verd = np.array((0.20, 0.36, 0.28), np.float32) * (0.6 + 0.6 * fbm(c.x * 0.8, c.yy * 0.8, 3, 4))[..., None]
        return col * (1 - 0.7 * v[..., None]) + verd * 0.7 * v[..., None]

    def medal(self, lx, ly, R):
        sk, holes = prof.skull(lx, ly + 0.3, R * 1.9)
        cov = fill(sk)
        h = 0.6 + 1.1 * dome(sk, 1.6)
        h = np.where(holes < 0, 0.35, h)
        mat = np.where(holes < 0, self.DARK, self.BONE)
        # crude bronze horns behind it
        for s_ in (1, -1):
            hd = sd_seg(lx, ly, s_ * 3.5, 4.0, s_ * 6.5, 7.2, 1.0)
            c2 = fill(hd) * (sk > 0)
            h = h * (1 - c2) + (0.8 + 0.6 * dome(hd, 0.8)) * c2
            mat = np.where(c2 > 0.5, self.BONE, mat)
            cov = np.maximum(cov, c2)
        return h.astype(np.float32), mat.astype(np.int16), cov, zero3(lx.shape)


LOOK = Goblins
