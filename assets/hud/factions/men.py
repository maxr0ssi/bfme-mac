"""Men's palantir: Gondor's polished silver and white Minas Tirith stone, a narrow sable channel of
stars, white-stone cartouches carrying the White Tree; the White Tree on sable as the medallion.
Black is an accent only (the channel and the medallion's field), never the whole band."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import Mat, dome, fbm, fill, sd_box, sd_seg, sd_star, smoothstep
from sagekit.paint.palantir.prof import band, local

from .base import Faction, disc


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
    SILVER, STONE, SABLE, MITHRIL, DARK, STEEL = range(6)
    mats = [Mat((0.90, 0.91, 0.94), rough=0.14, edge=(1, 1, 1)),
            Mat((0.93, 0.92, 0.88), metal=0, rough=0.42),
            Mat((0.012, 0.015, 0.02), metal=0, rough=0.06),
            Mat((0.78, 0.84, 0.92), rough=0.1, edge=(1, 1, 1)),
            Mat((0.16, 0.17, 0.19), metal=0.5, rough=0.55),
            Mat((0.56, 0.59, 0.64), rough=0.28)]
    orn_mat = 0
    orn_stops = [(0, (0.10, 0.10, 0.11)), (0.3, (0.46, 0.47, 0.50)), (0.65, (0.84, 0.85, 0.87)), (1, (1, 1, 0.98))]
    glass_col = (0.015, 0.018, 0.025)
    tick_col = (0.88, 0.9, 0.94)
    rim_glow = ((0.16, 0.18, 0.22), 2.5)
    sky_col = (0.97, 0.98, 1.0)
    ground_col = (0.16, 0.16, 0.17)
    patina = 0.12
    medals = [("minimap", 180, 8.6)]

    def ring(self, ctx, name):
        S, St, Sa, Mi, D, Se = range(6)
        p = prof.P(ctx)
        prof.lip(p, 0.05, Se)
        prof.bead(p, 0.05, 0.16, S, 1.4)
        prof.groove(p, 0.16, 0.19, D)
        prof.bead(p, 0.19, 0.29, St, 1.0, base=0.4)           # a white stone torus
        prof.groove(p, 0.29, 0.32, D)
        # the broad band: silver plate, a narrow sable channel of stars down its middle
        u, w, m = band(ctx, 0.32, 0.83)
        p.put(m, 0.95 + 0.12 * prof.half_round(u), S)
        ch = m & (u > 0.27) & (u < 0.73)
        cu = (u - 0.27) / 0.46
        p.put(ch, 0.45 + 0.03 * cu, Sa)
        for e in (0.27, 0.73):                                   # mithril fillets either side
            fil = m & (np.abs(u - e) < 0.05)
            p.put(fil, 1.0 + 0.2 * prof.half_round((u - e + 0.05) / 0.1), Mi)
        lx, ly, idx, L = local(ctx, u, w, 1.4 * w)
        st = sd_star(lx, ly, 0.2 * w, 6, 0.42)
        p.over(fill(st) * ch, 0.55 + 0.7 * dome(st, 0.5), Mi)
        # engraved silver either side of the channel: a fine running line
        for c0 in (0.15, 0.85):
            ln = np.abs(u - c0) * w - 0.12
            p.h = p.h - 0.25 * fill(ln) * m * ~ch
        # every sixth cell a white-stone cartouche with the White Tree in silver
        cx, cy, cidx, CL = local(ctx, u, w, 1.4 * w * 6, 0.5)
        cart = sd_box(cx, cy, 0.72 * w, 0.5 * w, 0.2 * w)
        inc = (cart < 0) & m
        p.over(fill(cart) * m, 1.05 + 0.15 * dome(cart, 0.6), St)
        tree = white_tree(cx, cy, 0.092 * w)                    # crown outward
        p.over(fill(tree) * inc, 1.15 + 0.35 * dome(tree, 0.35), S)
        prof.groove(p, 0.83, 0.86, D)
        prof.bead(p, 0.86, 0.97, St, 1.1)
        prof.bead(p, 0.97, 1.02, Se, 0.3)
        prof.turned(p, 0.025)
        return p

    def post(self, col, env):
        """White stone: a faint cool veining so it reads as marble, not as grey paint."""
        c = env["ctx"]["minimap"]
        vein = np.abs(fbm(c.x * 0.5, c.yy * 0.5, 4, 2) - 0.5)
        stone = (env["mat"] == self.STONE)[..., None]
        v = (1 - smoothstep(0.0, 0.05, vein))[..., None] * 0.12
        return col * (1 - stone * v) + stone * v * np.array((0.55, 0.6, 0.68), np.float32)

    def medal(self, lx, ly, R):
        h, mat, cov = disc(lx, ly, R, self.SILVER, self.SABLE, rim_w=1.5, field_h=0.5)
        k = R / 8.3
        d = white_tree(lx, ly, k)
        h = np.where(d < 0, 0.5 + 0.8 * dome(d, 0.4), h)
        mat = np.where(d < 0, self.STONE, mat)
        for sx_, sy_ in ((-2.9, 5.0), (0, 6.1), (2.9, 5.0)):
            st = sd_star(lx - sx_ * k * 0.9, ly - sy_ * k * 0.9 + 1.2 * k, 0.75 * k, 6, 0.45)
            h = np.where(st < 0, 0.5 + 0.6 * dome(st, 0.3), h)
            mat = np.where(st < 0, self.MITHRIL, mat)
        return h, mat.astype(np.int16), cov, np.zeros(lx.shape + (3,), np.float32)


LOOK = Men
