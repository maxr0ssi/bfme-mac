"""Dwarves' palantir, cut from the Erebor citadel: honey granite ashlar under gold coping, the
citadel's rune frieze (gold runes on blue) round the glass, the triangle frieze along the resource
bar, a gilded double chevron on the granite like the tower shields; the shield as the medallion.
Granite, friezes and gold trim are the citadel's own sheet (assets/hud/factions/swatches.py). Bold
at the focal points (the joint, the bar's ends, the top): polished gold that flashes, the runes glow
as blue inlay, sapphires and Arkenstone-white gems set in gold; past the frame a stepped gold crest
with the Arkenstone rises over the joint, and a gem-capped pinnacle off the top left."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import Mat, dome, fill, sd_circle, sd_poly, smoothstep
from sagekit.paint.palantir.prof import band, local

from . import fx
from .base import Faction

RUNE = np.array((0.30, 0.62, 1.0), np.float32)


def chevrons(lx, ly, w, k):
    """SDF of the tower shields' gilded double chevron, pointing outward (+y), k px half-width."""
    d = np.full(lx.shape, 1e9, np.float32)
    for y0 in (-0.35 * k, 0.3 * k):
        dd = np.abs((ly - y0) + 0.8 * np.abs(lx) - 0.55 * k) / 1.28 - 0.17 * k
        d = np.minimum(d, np.maximum(dd, np.abs(lx) - 0.95 * k))
    return d


class Dwarves(Faction):
    name = "dwarves"
    side = "good"
    GOLD, GRANITE, ENAMEL, STEEL, DARK, SAPPHIRE, ARKEN = range(7)
    mats = [Mat((1.0, 0.76, 0.32), rough=0.1, edge=(1, 0.97, 0.75)),
            Mat((0.62, 0.52, 0.38), metal=0, rough=0.7),
            Mat((0.05, 0.12, 0.42), metal=0, rough=0.15),
            Mat((0.24, 0.30, 0.42), rough=0.28),
            Mat((0.12, 0.09, 0.06), metal=0, rough=0.8),
            Mat((0.06, 0.22, 0.95), metal=0, rough=0.02, edge=(0.7, 0.85, 1), emit=(0.02, 0.06, 0.22)),
            Mat((0.86, 0.93, 1.0), metal=0, rough=0.02, edge=(1, 1, 1), emit=(0.12, 0.14, 0.18))]
    orn_mat = 0
    orn_stops = [(0, (0.06, 0.04, 0.02)), (0.3, (0.40, 0.27, 0.10)), (0.65, (0.88, 0.64, 0.26)), (1, (1, 0.93, 0.66))]
    glass_col = (0.01, 0.02, 0.05)
    tick_col = (0.95, 0.72, 0.30)
    rim_glow = ((0.10, 0.20, 0.55), 2.5)
    sky_col = (1.0, 0.95, 0.85)
    patina = 0.12
    medals = [("minimap", 180, 8.6)]
    bloom = (1.0, (3, 10))
    shine = (0.78, 0.8, 3, (1.0, 0.85, 0.55))
    glint = (36, 0.88, (1.0, 0.95, 0.8), (8, 18))

    def frieze(self, p, name, s0, s1, **kw):
        """A citadel frieze: its bright paint is raised gold, the rest blue enamel."""
        rgb, lum, m, u = self.skin(p, name, s0, s1, self.ENAMEL, base=0.5, carve=0.5, lift=0.7, gain=1.25, **kw)
        gold = m & (lum > 0.42)
        p.mat = np.where(gold, self.GOLD, p.mat)
        p.aw = np.where(gold, 0.0, p.aw)                          # the gilding is the gold metal itself
        if name == "rune":                                        # the runes glow as blue inlay
            foc = fx.focus(p.ctx)
            inlay = gold & (u > 0.14) & (u < 0.86)
            p.mat = np.where(inlay, self.ENAMEL, p.mat)
            p.alb = np.where(inlay[..., None], RUNE * 0.5, p.alb * 0.75)
            p.aw = np.where(inlay, 1.0, p.aw)
            p.glow(inlay * (0.45 + 0.8 * foc), RUNE)
        return rgb, lum, m, u

    def granite(self, p, s0, s1, course=2.0, shields=True):
        """The citadel's granite in ashlar courses, a gilded chevron shield every few blocks."""
        rgb, lum, m, u = self.skin(p, "granite", s0, s1, self.GRANITE, base=0.85, carve=1.4, v0=0.08, v1=0.62,
                                   aspect=0.7, wrap="mirror", gain=np.array((1.42, 1.28, 1.02), np.float32))
        ctx = p.ctx
        w = (s1 - s0) * float(np.median(ctx.bw))
        lx, ly, idx, L = local(ctx, u, w, course * w)
        joint = np.minimum(np.abs(np.abs(lx) - 0.5 * L), 9.0)
        cut = np.exp(-(joint / 0.28) ** 2) * m
        p.h = p.h - 0.45 * cut
        p.mat = np.where(cut > 0.5, self.DARK, p.mat)
        p.aw = p.aw * (1 - 0.6 * cut)
        if shields:
            sh = (idx % 5) == 2
            body = sd_poly(lx, ly, [(-0.62 * w, 0.42 * w), (0.62 * w, 0.42 * w), (0.62 * w, -0.05 * w),
                                    (0.0, -0.46 * w), (-0.62 * w, -0.05 * w)])
            cov = fill(body) * m * sh
            p.over(cov, 0.9 + 0.25 * dome(body, 0.6), self.GOLD)
            ch = chevrons(lx, ly + 0.02 * w, w, 0.42 * w)
            p.over(fill(ch) * cov, 1.0 + 0.2 * dome(ch, 0.25), self.ENAMEL)
        return m, u

    def ring(self, ctx, name):
        G, Gr, E, S, D = range(5)
        p = prof.P(ctx)
        if name == "bar":
            prof.lip(p, 0.08, Gr)
            prof.bead(p, 0.08, 0.26, G, 1.2)
            prof.groove(p, 0.26, 0.3, D)
            self.frieze(p, "tri", 0.3, 0.86, aspect=1.0)
            prof.groove(p, 0.86, 0.9, D)
            prof.bead(p, 0.9, 1.02, G, 0.9)
            return p
        prof.lip(p, 0.05, Gr)
        prof.bead(p, 0.05, 0.14, G, 1.4)                         # the gold coping
        prof.groove(p, 0.14, 0.16, D)
        self.frieze(p, "rune", 0.16, 0.56, aspect=1.15)         # the citadel's rune frieze
        prof.bead(p, 0.56, 0.6, G, 0.8, base=0.5)
        m, u = self.granite(p, 0.6, 0.94)                        # honey granite, chevron shields
        prof.bead(p, 0.94, 1.02, G, 0.9)
        prof.turned(p, 0.02)
        return p

    def medal(self, lx, ly, R):
        """The tower shield: gold, a blue field, the gilded double chevron."""
        body = sd_poly(lx, ly, [(-R * 0.82, R * 0.9), (R * 0.82, R * 0.9), (R * 0.82, -R * 0.1),
                                (0.0, -R * 1.05), (-R * 0.82, -R * 0.1)])
        cov = fill(body)
        rim = body + 1.3
        h = np.where(rim > 0, 0.5 + 1.2 * dome(body, 1.3), 0.6)
        mat = np.where(rim > 0, self.GOLD, self.ENAMEL)
        ch = chevrons(lx, ly - 0.05 * R, R, 0.62 * R)
        h = np.where((ch < 0) & (rim < 0), 0.8 + 0.6 * dome(ch, 0.5), h)
        mat = np.where((ch < 0) & (rim < 0), self.GOLD, mat)
        return h.astype(np.float32), mat.astype(np.int16), cov, np.zeros(lx.shape + (3,), np.float32)


LOOK = Dwarves
