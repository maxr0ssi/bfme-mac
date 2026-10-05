"""Goblins' palantir, cut from the Goblin citadel: blood-red horn plates streaked white (the
citadel's spiked roofs and beams), bound by black iron bands, bone tusks biting in round the glass,
skulls and ribs on the plates as on the citadel's poles, dried blood over all of it and wet blood
running at the focal points (the joint, the bar's ends, the top); EA's spikes in the citadel's red
and bone; past the frame a bloodied bone juts over the joint, a tusk off the top left and a skull
hangs under the bar. A skull with red horns as the medallion. Horn, hide and bone are the citadel's own sheet
(assets/hud/factions/swatches.py)."""
import numpy as np

from sagekit.paint.palantir import prof
from sagekit.paint.palantir.core import Mat, dome, fbm, fill, noise, ramp, sd_circle, sd_seg, smoothstep
from sagekit.paint.palantir.prof import band, local

from . import fx
from .base import Faction, zero3


class Goblins(Faction):
    name = "goblins"
    side = "evil"
    HORN, BONE, IRON, DARK, RED, WET = range(6)
    mats = [Mat((0.55, 0.06, 0.05), metal=0, rough=0.35),
            Mat((0.86, 0.83, 0.76), metal=0, rough=0.45),
            Mat((0.20, 0.20, 0.21), rough=0.45, edge=(0.7, 0.7, 0.72)),
            Mat((0.03, 0.02, 0.02), metal=0.2, rough=0.9),
            Mat((0.45, 0.03, 0.03), metal=0, rough=0.3),
            Mat((0.55, 0.0, 0.02), metal=0, rough=0.03, edge=(1, 0.7, 0.7))]
    orn_mat = 0
    orn_stops = [(0, (0.03, 0.005, 0.005)), (0.3, (0.30, 0.03, 0.03)), (0.62, (0.62, 0.07, 0.06)),
                 (0.82, (0.80, 0.55, 0.50)), (1, (0.97, 0.95, 0.92))]
    glass_col = (0.025, 0.01, 0.008)
    tick_col = (0.8, 0.72, 0.65)
    rim_glow = ((0.30, 0.02, 0.02), 2.0)
    sky_col = (1.0, 0.92, 0.88)
    rim_col = (1.0, 0.75, 0.7)
    ember = ((0.9, 0.15, 0.08), 0.10)
    patina = 0.1
    medals = []                                                  # the skull at 180 degrees is 3D (pieces.py)
    shine = (0.8, 0.5, 3, (1.0, 0.9, 0.85))
    glint = (26, 0.86, (1.0, 0.97, 0.92), (6, 14))
    bloom = (0.9, (3, 9))

    def ring(self, ctx, name):
        H, Bo, I, D, R = range(5)
        p = prof.P(ctx)
        s0 = ctx.s
        ctx.s = s0 + prof.wobble(ctx, 0.05)                      # crude: the band wobbles
        if name == "bar":
            prof.lip(p, 0.08, I)
            prof.chamfer(p, 0.08, 0.3, I, 1.0, flat=0.4)
            self.skin(p, "beam", 0.3, 1.0, H, base=0.7, carve=0.8, lift=0.3, gain=1.0, v0=0.1, v1=1.0, soft=1)
            prof.hammer(p, 0.2, 0.5)
            ctx.s = s0
            return p
        prof.lip(p, 0.04, I)
        prof.chamfer(p, 0.04, 0.13, I, 1.2, flat=0.3)            # a black iron band round the glass
        # bone tusks biting into the glass
        u, w, m = band(ctx, 0.13, 0.4)
        lx, ly, idx, L = local(ctx, u, w, 1.7 * w)
        size = 0.75 + 0.25 * noise(idx * 3.1, 0.0 * idx, 6)
        tipu = 1 - size
        half = 0.42 * L * np.clip((u - tipu) / (1 - tipu), 0, 1) ** 0.8
        inside = (np.abs(lx + 0.15 * L * (1 - u)) < half) & (u > tipu)
        fang = 0.35 + 1.1 * np.sqrt(np.clip(1 - (lx / np.maximum(half, 1e-3)) ** 2, 0, 1)) * (0.5 + 0.5 * u)
        inside = inside & (fx.focus(ctx) > 0.12)                  # only near the focal points
        p.put(m, 0.6 + 0.3 * prof.half_round(u), I)
        p.put(m & inside, fang + 0.3, Bo)
        bone = self.tex["bone"].sample(np.clip((1 - u) * 130, 0, 135), np.clip(lx / L + 0.5, 0, 1) * 21, 1.0)
        p.tint((m & inside).astype(np.float32), np.clip(bone * 1.05, 0, 1))
        # the blood-red horn plates, black iron straps every few, a skull now and then
        rgb, lum, m, u = self.skin(p, "hide", 0.4, 0.94, H, base=0.8, carve=0.45, lift=0.1, gain=0.85,
                                   v0=0.15, v1=0.45, aspect=1.6, wrap="mirror", soft=2)
        w = 0.54 * float(np.median(ctx.bw))
        lx, ly, idx, L = local(ctx, u, w, 2.4 * w)
        kind = idx % 3
        strap = (np.abs(lx) < 0.16 * w) & (kind == 0) & m
        p.put(strap, 1.05 + 0.15 * prof.half_round(lx / (0.32 * w) + 0.5), I)
        nail = sd_circle(np.abs(lx) - 0.0, np.abs(ly) - 0.3 * w, 0.09 * w)
        p.over(fill(nail) * strap, 1.25 + 0.2 * dome(nail, 0.3), I)
        prof.chamfer(p, 0.94, 1.02, I, 0.8, flat=0.4)
        self.blood(p, ctx, fx.focus(ctx))
        prof.hammer(p, 0.25, 0.45)
        ctx.s = s0
        return p

    def blood(self, p, ctx, foc):
        """Dried blood in patches over the bone and the iron."""
        dried = smoothstep(0.55, 0.72, fbm(ctx.x * 0.3, ctx.yy * 0.3, 4, 12)) * ((p.mat == self.BONE) | (p.mat == self.IRON))
        p.tint(dried * 0.75, np.full(dried.shape + (3,), 0.0, np.float32) + np.array((0.28, 0.03, 0.02), np.float32))

    def orn_colour(self, lum, x4):
        """EA's spikes and joint as the citadel's: blood red, white-streaked at the ridges."""
        return ramp(self.orn_stops, lum * 1.08)

    def medal(self, lx, ly, R):
        sk, holes = prof.skull(lx, ly + 0.3, R * 1.9)
        cov = fill(sk)
        h = 0.6 + 1.1 * dome(sk, 1.6)
        h = np.where(holes < 0, 0.35, h)
        mat = np.where(holes < 0, self.DARK, self.BONE)
        for s_ in (1, -1):                                         # blood-red horns behind it
            hd = sd_seg(lx, ly, s_ * 3.5, 4.0, s_ * 6.5, 7.2, 1.0)
            c2 = fill(hd) * (sk > 0)
            h = h * (1 - c2) + (0.8 + 0.6 * dome(hd, 0.8)) * c2
            mat = np.where(c2 > 0.5, self.RED, mat)
            cov = np.maximum(cov, c2)
        return h.astype(np.float32), mat.astype(np.int16), cov, zero3(lx.shape)


LOOK = Goblins
