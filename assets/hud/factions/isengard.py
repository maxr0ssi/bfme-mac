"""Isengard's palantir: Orthanc-black iron under bright silver (chamfered bars, cog teeth, fillets),
riveted plates, and the White Hand large on a sable shield every other plate; forge embers in the seams."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import (Mat, blur, cells, dome, fbm, fill, noise, sd_box, sd_circle, sd_poly,
                                         sd_seg, sd_star, smoothstep)
from sagekit.paint.palantir.prof import band, local

from .base import Faction, disc, zero3

class Isengard(Faction):
    name = "isengard"
    side = "evil"
    IRON, SILVER, WHITE, DARK, STEEL = range(5)
    mats = [Mat((0.19, 0.19, 0.21), rough=0.3, edge=(0.66, 0.68, 0.72)),
            Mat((0.88, 0.90, 0.94), rough=0.12, edge=(1, 1, 1)),
            Mat((0.97, 0.97, 0.95), metal=0, rough=0.25, emit=(0.06, 0.06, 0.06)),
            Mat((0.025, 0.025, 0.03), metal=0.4, rough=0.7),
            Mat((0.42, 0.44, 0.48), rough=0.3)]
    orn_mat = 0
    orn_stops = [(0, (0.015, 0.015, 0.018)), (0.3, (0.14, 0.14, 0.16)), (0.6, (0.55, 0.56, 0.6)), (1, (0.97, 0.98, 1))]
    glass_col = (0.012, 0.012, 0.015)
    tick_col = (0.75, 0.77, 0.8)
    ember = ((1.0, 0.42, 0.08), 0.18)
    sky_col = (0.95, 0.97, 1.0)
    rim_col = (0.9, 0.5, 0.2)
    medals = [("minimap", 180, 8.4)]

    def ring(self, ctx, name):
        I, S, W, D, St = range(5)
        p = prof.P(ctx)
        if name == "bar":
            prof.lip(p, 0.08, I)
            prof.chamfer(p, 0.08, 0.34, S, 1.2, flat=0.5)
            prof.groove(p, 0.34, 0.4, D)
            u, w, m = prof.flat(p, 0.4, 0.97, I, 0.8, 0.25)
            lx, ly, idx, L = local(ctx, u, w, 2.6 * w)
            rv = sd_circle(lx, ly, 0.22 * w)
            p.over(fill(rv) * m, 0.9 + 0.7 * dome(rv, 0.5), S)
            prof.hammer(p, 0.12, 0.8)
            return p
        prof.lip(p, 0.05, I)
        prof.chamfer(p, 0.05, 0.17, S, 1.4, flat=0.45)
        prof.groove(p, 0.17, 0.2, D)
        # gear teeth: square cogs with chamfered faces
        u, w, m = band(ctx, 0.2, 0.33)
        lx, ly, idx, L = local(ctx, u, w, 1.25 * w)
        tooth = sd_box(lx, ly, 0.27 * L, 0.6 * w, 0.06 * w)
        p.put(m, 0.25 + 0.0 * u, D)
        p.over(fill(tooth) * m, 0.4 + 0.9 * np.clip(-tooth / 0.45, 0, 1), S)
        prof.groove(p, 0.33, 0.36, D)
        # riveted plates, the White Hand on a sable shield on every other one
        u, w, m = band(ctx, 0.36, 0.84)
        lx, ly, idx, L = local(ctx, u, w, 2.3 * w)
        plate = 0.75 + 0.18 * prof.half_round(u) * prof.half_round(lx / L + 0.5)
        seam = np.abs(np.abs(lx) - 0.5 * L)
        plate = plate - 0.45 * np.exp(-(seam / 0.25) ** 2)
        p.put(m, plate, I)
        for sx in (-1, 1):
            for sy in (-1, 1):
                rv = sd_circle(lx - sx * (0.5 * L - 0.85), ly - sy * 0.27 * w, 0.5)
                p.over(fill(rv) * m, 0.9 + 0.6 * dome(rv, 0.45), St)
        fil = m & ((u < 0.11) | (u > 0.89))
        p.put(fil, 0.95 + 0.25 * prof.half_round(np.where(u < 0.5, u / 0.11, (u - 0.89) / 0.11)), S)
        hand = (idx % 2) == 0
        shield = sd_box(lx, ly, 0.24 * L, 0.47 * w, 0.1 * w)
        p.over(fill(shield) * m * hand, np.full(u.shape, 0.5, np.float32), D)
        rim = np.abs(shield) - 0.3
        p.over(fill(rim) * m * hand, 1.0 + 0.2 * dome(rim, 0.3), S)
        hd = prof.white_hand(lx + 0.06 * w, ly + 0.1 * w, 0.98 * w)
        p.over(fill(hd) * m * hand, 0.85 + 0.45 * dome(hd, 0.45), W)
        prof.hammer(p, 0.1, 0.7, mask=m)
        prof.groove(p, 0.84, 0.86, D)
        prof.chamfer(p, 0.86, 0.98, S, 1.2, flat=0.4)
        prof.bead(p, 0.98, 1.02, I, 0.3)
        return p

    def medal(self, lx, ly, R):
        h, mat, cov = disc(lx, ly, R, self.SILVER, self.DARK, rim_w=1.3, field_h=0.6)
        hd = prof.white_hand(lx, ly + 0.6, R * 1.25)
        h = np.where(hd < 0, 0.6 + 0.7 * dome(hd, 0.5), h)
        mat = np.where(hd < 0, self.WHITE, mat)
        return h, mat.astype(np.int16), cov, zero3(lx.shape)


LOOK = Isengard
