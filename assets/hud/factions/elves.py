"""Elves' palantir: moonsilver, leaf-and-vine filigree, gold beads; the star of Earendil."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import (Mat, blur, cells, dome, fbm, fill, noise, sd_box, sd_circle, sd_poly,
                                         sd_seg, sd_star, smoothstep)
from sagekit.paint.palantir.prof import band, local

from .base import Faction, disc, zero3

class Elves(Faction):
    name = "elves"
    side = "good"
    MOON, DIM, ENAMEL, GOLD, DARK = range(5)
    mats = [Mat((0.80, 0.85, 0.92), rough=0.14, edge=(1, 1, 1)),
            Mat((0.42, 0.48, 0.56), rough=0.35),
            Mat((0.04, 0.10, 0.13), metal=0, rough=0.08),
            Mat((0.96, 0.80, 0.46), rough=0.18),
            Mat((0.05, 0.07, 0.09), metal=0.5, rough=0.6)]
    orn_mat = 0
    orn_stops = [(0, (0.03, 0.04, 0.06)), (0.35, (0.30, 0.36, 0.44)), (0.7, (0.70, 0.77, 0.86)), (1, (0.96, 0.98, 1))]
    glass_col = (0.01, 0.03, 0.04)
    tick_col = (0.75, 0.85, 0.95)
    rim_glow = ((0.18, 0.30, 0.40), 3.0)
    sky_col = (0.92, 0.96, 1.0)
    rim_col = (0.55, 0.75, 0.85)
    medals = [("minimap", 180, 8.0)]

    def ring(self, ctx, name):
        M, Dm, E, G, D = range(5)
        p = prof.P(ctx)
        prof.lip(p, 0.05, Dm)
        prof.bead(p, 0.05, 0.14, M, 1.1)
        prof.groove(p, 0.14, 0.17, D)
        prof.bead(p, 0.17, 0.215, G, 0.7, base=0.35)
        prof.groove(p, 0.215, 0.245, D)
        u, w, m = band(ctx, 0.245, 0.775)
        p.put(m, 0.45 + 0.05 * u, E)
        lx, ly, idx, L = local(ctx, u, w, 2.7 * w)
        ph = lx / L
        yc = 0.27 * w * np.sin(2 * np.pi * ph)
        slope = 0.27 * w * 2 * np.pi / L * np.cos(2 * np.pi * ph)
        dv = np.abs(ly - yc) / np.sqrt(1 + slope ** 2) - 0.36
        vine = fill(dv) * m
        p.over(vine, 0.85 + 0.35 * np.clip(-dv / 0.36, 0, 1), M)
        for sgn in (1, -1):
            # a leaf hanging from each crest into the free space, a pair of berries beside it
            lxc, lyc = lx - sgn * 0.25 * L - 0.06 * L * sgn, ly - sgn * (0.27 * w - 0.36 * w)
            d, a, b = prof.leaf(lxc, lyc, 0.62 * w, 0.28 * w, sgn * -1.15)
            lv = fill(d) * m
            rib = np.exp(-(b / 0.18) ** 2)
            p.over(lv, 0.75 + 0.55 * dome(d, 0.7) - 0.2 * rib, M)
            bx, by = lx - sgn * 0.25 * L + 0.17 * L * sgn, ly - sgn * 0.02 * w
            bd = np.minimum(sd_circle(bx, by, 0.42), sd_circle(bx + 0.9 * sgn, by - 0.5 * sgn, 0.34))
            p.over(fill(bd) * m, 0.8 + 0.5 * dome(bd, 0.4), G)
        prof.groove(p, 0.775, 0.80, D)
        prof.bead(p, 0.80, 0.84, G, 0.7, base=0.35)
        prof.groove(p, 0.84, 0.87, D)
        prof.bead(p, 0.87, 0.97, M, 1.0)
        prof.bead(p, 0.97, 1.02, Dm, 0.3)
        prof.turned(p, 0.03)
        return p

    def medal(self, lx, ly, R):
        h, mat, cov = disc(lx, ly, R, self.MOON, self.ENAMEL, rim_w=1.0, field_h=0.45, rim_h=1.0)
        # the star of Earendil over a mallorn leaf pair
        st = sd_star(lx, ly - 1.6, R * 0.32, 8, 0.38)
        h = np.where(st < 0, 0.5 + 0.9 * dome(st, 0.6), h)
        mat = np.where(st < 0, self.MOON, mat)
        for sgn in (1, -1):
            d, a, b = prof.leaf(lx - sgn * 1.9, ly + 2.0, 4.8, 2.0, sgn * 0.9)
            h = np.where(d < 0, 0.5 + 0.8 * dome(d, 0.6) - 0.2 * np.exp(-(b / 0.2) ** 2), h)
            mat = np.where(d < 0, self.GOLD, mat)
        return h, mat.astype(np.int16), cov, np.zeros(lx.shape + (3,), np.float32)


LOOK = Elves
