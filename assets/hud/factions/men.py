"""Men's palantir, cut from the Gondor citadel: white Minas Tirith ashlar under a corbelled
battlement, the citadel's sable band of white stars round the glass between steel fillets, white
stone mouldings; the White Tree on a royal blue banner (the citadel's banners) as the medallion.
Ashlar, corbels and the star band are the citadel's own sheet (assets/hud/factions/swatches.py).
Bold at the focal points (the joint, the bar's ends, the top): bright polished silver, the White
Tree glowing softly on a blue plaque at the top, stars that glint; past the frame a white stone
pinnacle with a silver star rises over the joint, and a silver spear point off the top left."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import Mat, dome, fill, sd_box, sd_circle, sd_poly, sd_seg, sd_star, smoothstep
from sagekit.paint.palantir.prof import local

from . import fx
from .base import Faction

TREE_GLOW = (0.55, 0.72, 1.0)


def white_tree(lx, ly, k):
    """SDF of the White Tree (crown outward, +y), k px per unit (about 10 units tall)."""
    d = sd_seg(lx, ly, 0, -4.6 * k, 0, 2.6 * k, 0.45 * k)
    for y0, dx, dy in ((-0.6, 2.6, 2.2), (0.6, 2.1, 2.6), (1.7, 1.4, 2.4)):
        for s_ in (1, -1):
            d = np.minimum(d, sd_seg(lx, ly, 0, y0 * k, s_ * dx * k, (y0 + dy) * k, 0.32 * k))
    for s_ in (1, -1):
        d = np.minimum(d, sd_seg(lx, ly, 0, -4.0 * k, s_ * 1.6 * k, -4.9 * k, 0.3 * k))
    return np.minimum(d, sd_seg(lx, ly, 0, 2.6 * k, 0, 4.4 * k, 0.3 * k))


class Men(Faction):
    name = "men"
    side = "good"
    STEEL, STONE, SABLE, SILVER, DARK, BLUE = range(6)
    mats = [Mat((0.62, 0.65, 0.70), rough=0.24, edge=(1, 1, 1)),
            Mat((0.92, 0.91, 0.88), metal=0, rough=0.5),
            Mat((0.02, 0.025, 0.03), metal=0, rough=0.1),
            Mat((0.93, 0.95, 0.99), rough=0.05, edge=(1, 1, 1)),
            Mat((0.20, 0.20, 0.21), metal=0, rough=0.8),
            Mat((0.10, 0.22, 0.55), metal=0, rough=0.45)]
    orn_mat = 1
    orn_stops = [(0, (0.12, 0.12, 0.12)), (0.3, (0.50, 0.50, 0.49)), (0.65, (0.86, 0.86, 0.84)), (1, (1, 1, 0.98))]
    glass_col = (0.015, 0.018, 0.025)
    tick_col = (0.88, 0.9, 0.94)
    rim_glow = ((0.16, 0.18, 0.22), 2.5)
    sky_col = (0.97, 0.98, 1.0)
    ground_col = (0.16, 0.16, 0.17)
    patina = 0.08
    medals = [("minimap", 180, 9.0)]
    bloom = (1.0, (3, 10))
    shine = (0.78, 1.0, 4, (0.95, 0.97, 1.0))
    glint = (60, 0.86, (0.95, 0.97, 1.0), (9, 22))

    def ring(self, ctx, name):
        S, St, Sa, Si, D, B = range(6)
        p = prof.P(ctx)
        if name == "bar":
            prof.lip(p, 0.08, S)
            prof.bead(p, 0.08, 0.26, St, 1.0, base=0.4)
            prof.groove(p, 0.26, 0.3, D)
            self.skin(p, "stars", 0.3, 0.86, Sa, base=0.5, carve=0.5, lift=0.6, v0=0.0, v1=0.86, gain=1.1)
            prof.bead(p, 0.86, 1.02, St, 0.9)
            return p
        prof.lip(p, 0.04, S)
        prof.bead(p, 0.04, 0.12, St, 1.2, base=0.4)              # a white stone torus
        prof.bead(p, 0.12, 0.16, S, 0.6, base=0.4)               # steel fillet
        rgb, lum, m, u = self.skin(p, "stars", 0.16, 0.42, Sa, base=0.5, carve=0.4, lift=0.6, v0=0.0, v1=0.86,
                                   aspect=1.0, gain=1.1)
        p.mat = np.where(m & (lum > 0.4), Si, p.mat)              # the stars: silver
        prof.bead(p, 0.42, 0.46, S, 0.6, base=0.4)
        rgb, lum, m, u = self.skin(p, "ashlar", 0.46, 0.8, St, base=0.85, carve=1.4, v0=0.05, v1=0.7,
                                   aspect=1.0, wrap="mirror", gain=1.15)
        # every so often a white-stone cartouche carrying the White Tree, as over the citadel's gate
        w = 0.34 * float(np.median(ctx.bw))
        cx, cy, cidx, CL = local(ctx, u, w, 9.0 * w, 0.5)
        tree = white_tree(cx, cy, 0.085 * w)
        p.over(fill(tree) * m * (np.abs(cx) < w), 1.15 + 0.35 * dome(tree, 0.35), Si)
        p.glow(fill(tree) * m * (np.abs(cx) < w) * 0.35, TREE_GLOW)
        self.skin(p, "corbel", 0.8, 0.97, St, base=0.8, carve=1.2, lift=0.3, aspect=1.0, gain=1.15)
        prof.bead(p, 0.97, 1.02, S, 0.3)
        return p

    def medal(self, lx, ly, R):
        """The citadel's banner: royal blue, swallow-tailed, the White Tree in white."""
        tail = 0.55 * R
        body = sd_poly(lx, ly, [(-R * 0.72, R * 1.0), (R * 0.72, R * 1.0), (R * 0.72, -R * 1.0),
                                (0.0, -R * 1.0 + tail), (-R * 0.72, -R * 1.0)])
        cov = fill(body)
        rim = body + 1.1
        h = np.where(rim > 0, 0.5 + 1.1 * dome(body, 1.1), 0.55)
        mat = np.where(rim > 0, self.SILVER, self.BLUE)
        k = R / 8.0
        d = white_tree(lx, ly - 0.05 * R, k * 0.95)
        h = np.where((d < 0) & (rim < 0), 0.6 + 0.6 * dome(d, 0.35), h)
        glow = (fill(d) * (rim < 0) * 0.6)[..., None] * np.array(TREE_GLOW, np.float32)
        mat = np.where((d < 0) & (rim < 0), self.STONE, mat)
        for sx_, sy_ in ((-2.6, 4.6), (0, 5.6), (2.6, 4.6)):
            st = sd_star(lx - sx_ * k * 0.9, ly - sy_ * k * 0.9 + 1.0 * k, 0.65 * k, 6, 0.45)
            h = np.where((st < 0) & (rim < 0), 0.55 + 0.5 * dome(st, 0.3), h)
            mat = np.where((st < 0) & (rim < 0), self.SILVER, mat)
        return h.astype(np.float32), mat.astype(np.int16), cov, glow


LOOK = Men
