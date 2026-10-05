"""Isengard's palantir, cut from the Isengard citadel: Orthanc-black fluted wall plates and the
citadel's lancet arcade, edged in the bright worn silver of its copings, silver spikes along the
outer edge as on its walls, forge embers in the seams; the White Hand on black as the medallion.
Bold at the focal points (the joint, the bar's ends, the top): the furnace glows orange through the
lancets and between the flutes, the silver spikes gleam, a bold White Hand crowns the top; past the
frame Orthanc's horns rise over the joint and a needle off the top left.
Plates, arcade, coping and the Hand are the citadel's own sheet (assets/hud/factions/swatches.py)."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import Mat, dome, fill, sd_box, smoothstep
from sagekit.paint.palantir.prof import band, local

from . import fx
from .base import Faction, disc, lancet, zero3

FURNACE = [(0, (0.12, 0.02, 0.0)), (0.4, (0.8, 0.2, 0.01)), (0.75, (1.0, 0.55, 0.08)), (1, (1.0, 0.88, 0.55))]


class Isengard(Faction):
    name = "isengard"
    side = "evil"
    IRON, SILVER, WHITE, DARK, STONE = range(5)
    mats = [Mat((0.16, 0.16, 0.18), rough=0.32, edge=(0.66, 0.68, 0.72)),
            Mat((0.92, 0.94, 0.98), rough=0.07, edge=(1, 1, 1)),
            Mat((1.0, 1.0, 0.98), metal=0, rough=0.3, emit=(0.18, 0.18, 0.18)),
            Mat((0.02, 0.02, 0.025), metal=0.4, rough=0.7),
            Mat((0.14, 0.14, 0.15), metal=0.2, rough=0.55)]
    orn_mat = 0
    orn_stops = [(0, (0.012, 0.012, 0.015)), (0.35, (0.10, 0.10, 0.11)), (0.65, (0.46, 0.47, 0.5)), (1, (0.97, 0.98, 1))]
    glass_col = (0.012, 0.012, 0.015)
    tick_col = (0.75, 0.77, 0.8)
    ember = ((1.0, 0.42, 0.08), 0.16)
    sky_col = (0.95, 0.97, 1.0)
    rim_col = (0.9, 0.5, 0.2)
    patina = 0.1
    medals = [("minimap", 180, 9.0)]
    bloom = (1.1, (3, 11))
    shine = (0.8, 0.7, 3, (1.0, 1.0, 1.0))
    glint = (34, 0.86, (1.0, 1.0, 1.0), (7, 16))

    def ring(self, ctx, name):
        I, S, W, D, St = range(5)
        p = prof.P(ctx)
        if name == "bar":
            prof.lip(p, 0.08, I)
            prof.chamfer(p, 0.08, 0.3, S, 1.2, flat=0.5)
            self.skin(p, "ribs", 0.3, 0.86, St, base=0.7, carve=1.4, gain=1.3, v0=0.1, v1=0.9, aspect=1.0)
            prof.chamfer(p, 0.86, 1.02, S, 1.0, flat=0.4)
            return p
        prof.lip(p, 0.04, I)
        prof.chamfer(p, 0.04, 0.14, S, 1.4, flat=0.45)           # the silver coping round the glass
        prof.groove(p, 0.14, 0.17, D)
        # the citadel's black fluted wall, its lancet panels framed in worn silver
        rgb, lum, m, u = self.skin(p, "ribs", 0.17, 0.68, St, base=0.7, carve=1.6, gain=1.5, v0=0.1, v1=0.9,
                                   aspect=1.0)
        w = 0.51 * float(np.median(ctx.bw))
        lx, ly, idx, L = local(ctx, u, w, 1.25 * w)
        arch = lancet(lx, ly + 0.06 * w, 0.5 * w, 0.92 * w)
        rim = np.abs(arch + 0.25) - 0.32
        p.over(fill(arch + 0.1) * m, np.full(u.shape, 0.35, np.float32), D)
        p.over(fill(rim) * m, 0.95 + 0.35 * np.clip(-rim / 0.32, 0, 1), S)
        mull = sd_box(lx, ly + 0.12 * w, 0.045 * w, 0.3 * w)
        p.over(fill(mull) * m * (arch < 0), 0.75 + 0.2 * dome(mull, 0.3), S)
        foc = fx.focus(ctx)
        # the furnace behind: orange through the lancets, and between the flutes at the focal points
        win = fill(arch + 0.3) * m * (mull > 0.2)
        hot = win * 0.95 * smoothstep(0.15, 0.6, foc) * (0.75 + 0.35 * np.clip(-ly / (0.5 * w) + 0.5, 0, 1.4))
        p.emit = p.emit + fx.heat(hot, FURNACE) * smoothstep(0.02, 0.15, hot)[..., None] * 1.2
        groove = np.clip(0.45 - lum, 0, 1) * 2.2 * m * (arch > 0.4) * smoothstep(0.2, 0.6, foc)
        p.emit = p.emit + fx.heat(groove * 0.8, FURNACE) * smoothstep(0.02, 0.2, groove)[..., None]
        prof.chamfer(p, 0.68, 0.74, S, 0.9, flat=0.4)
        # silver spikes along the outer edge over black iron, as on the citadel's walls
        u, w, m = band(ctx, 0.74, 1.0)
        lx, ly, idx, L = local(ctx, u, w, 1.5 * w)
        half = 0.3 * L * np.clip(1 - u, 0, 1) ** 0.85
        spike = (np.abs(lx) < half) & m
        p.put(m & ~spike, 0.5 + 0.1 * u, I)
        p.put(spike, 0.9 + 0.9 * (1 - np.abs(lx) / np.maximum(half, 1e-3)), S)
        return p

    def medal(self, lx, ly, R):
        h, mat, cov = disc(lx, ly, R, self.SILVER, self.DARK, rim_w=1.3, field_h=0.6)
        hd = prof.white_hand(lx, ly + 0.6, R * 1.35)
        h = np.where(hd < 0, 0.7 + 0.8 * dome(hd, 0.5), h)
        mat = np.where(hd < 0, self.WHITE, mat)
        em = (fill(hd) * 0.3)[..., None] * np.ones(3, np.float32)
        return h, mat.astype(np.int16), cov, em


LOOK = Isengard
