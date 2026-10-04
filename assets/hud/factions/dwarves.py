"""Dwarves' palantir: Erebor gold, blue enamel, chevrons and rune cartouches; the Erebor star."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import (Mat, blur, cells, dome, fbm, fill, noise, sd_box, sd_circle, sd_poly,
                                         sd_seg, sd_star, smoothstep)
from sagekit.paint.palantir.prof import band, local

from .base import Faction, disc, zero3

class Dwarves(Faction):
    name = "dwarves"
    side = "good"
    GOLD, BRONZE, ENAMEL, STEEL, DARK = range(5)
    mats = [Mat((1.0, 0.74, 0.30), rough=0.2, edge=(1, 0.95, 0.7)),
            Mat((0.56, 0.37, 0.15), rough=0.42),
            Mat((0.05, 0.15, 0.50), metal=0, rough=0.1),
            Mat((0.24, 0.30, 0.42), rough=0.28),
            Mat((0.14, 0.09, 0.04), metal=0.5, rough=0.7)]
    orn_mat = 0
    orn_stops = [(0, (0.05, 0.03, 0.01)), (0.3, (0.38, 0.24, 0.07)), (0.65, (0.86, 0.62, 0.24)), (1, (1, 0.93, 0.66))]
    glass_col = (0.01, 0.02, 0.05)
    tick_col = (0.95, 0.72, 0.30)
    rim_glow = ((0.10, 0.20, 0.55), 2.5)
    sky_col = (1.0, 0.95, 0.85)
    medals = [("minimap", 180, 8.2)]

    def ring(self, ctx, name):
        G, B, E, S, D = range(5)
        p = prof.P(ctx)
        if name == "bar":
            prof.lip(p, 0.08, B)
            prof.bead(p, 0.08, 0.32, G, 1.2)
            prof.groove(p, 0.32, 0.38, D)
            u, w, m = band(ctx, 0.38, 0.68)
            p.put(m, 0.5 + 0.05 * u, E)
            lx, ly, idx, L = local(ctx, u, w, 3.2 * w)
            st = sd_circle(lx, ly, 0.36 * w)
            p.over(fill(st) * m, 0.6 + 0.7 * dome(st, 0.5), G)
            prof.groove(p, 0.68, 0.73, D)
            prof.rope(p, 0.73, 1.0, G, 1.1, strands=1.1)
            prof.turned(p, 0.04)
            return p
        prof.lip(p, 0.05, B)
        prof.bead(p, 0.05, 0.19, G, 1.5)
        prof.groove(p, 0.19, 0.23, D)
        u, w, m = band(ctx, 0.23, 0.79)
        p.put(m, 0.55 + 0.05 * u, E)
        # gold fillets along both edges of the enamel
        fil = m & ((u < 0.11) | (u > 0.89))
        p.put(fil, 0.95 + 0.25 * prof.half_round(np.where(u < 0.5, u / 0.11, (u - 0.89) / 0.11)), G)
        # chevrons: gold V's pointing along the ring
        lx, ly, idx, L = local(ctx, u, w, 0.95 * w)
        per = L
        q = (lx + np.abs(ly) * 0.9) / per
        f = q - np.floor(q)
        dd = (np.abs(f - 0.25) - 0.16) * per
        chev = fill(dd, 0.3) * (np.abs(ly) < 0.36 * w) * m
        # rune cartouches: gold plates, two runes cut and filled with blue enamel
        cx, cy, cidx, CL = local(ctx, u, w, 5.5 * w, 0.0)
        cart = sd_box(cx, cy, 0.85 * w, 0.40 * w, 0.1 * w)
        incart = (cart < 0) & m
        chev = chev * (cart > 0.4)
        p.over(chev, 0.95 + 0.25 * np.clip(-dd / 0.6, 0, 1), G)
        p.put(incart, 1.0 + 0.25 * dome(cart, 0.8), G)
        sub = (cx > 0).astype(int)
        rx = cx - np.where(cx > 0, 0.4 * w, -0.4 * w)
        rd = prof.rune(rx, cy, cidx * 2 + sub, 0.56 * w, 0.36)
        cut = fill(rd) * incart
        p.over(cut, np.full(u.shape, 0.55, np.float32), E)
        prof.groove(p, 0.79, 0.83, D)
        prof.rope(p, 0.83, 0.97, G, 1.3, strands=1.2)
        prof.bead(p, 0.97, 1.02, B, 0.4)
        prof.turned(p, 0.04)
        return p

    def medal(self, lx, ly, R):
        h, mat, cov = disc(lx, ly, R, self.GOLD, self.ENAMEL, rim_w=1.6, field_h=0.6)
        # the Erebor star-and-crown: a gold 8-point star with a rune hammer
        st = sd_star(lx, ly + 0.4, R * 0.62, 8, 0.5)
        h = np.where(st < 0, 0.6 + 0.9 * dome(st, 1.2), h)
        mat = np.where(st < 0, self.GOLD, mat)
        cen = sd_circle(lx, ly + 0.4, R * 0.18)
        h = np.where(cen < 0, 1.5 + 0.4 * dome(cen, 0.6), h)
        mat = np.where(cen < 0, self.STEEL, mat)
        return h, mat.astype(np.int16), cov, np.zeros(lx.shape + (3,), np.float32)


LOOK = Dwarves
