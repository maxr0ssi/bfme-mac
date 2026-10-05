"""The faction palantir look's defaults: glass, ornament recolour, crevice embers, medallions (numpy).

A look draws, per band (the minimap ring, the portrait ring, the resource bar's rails), a height
field and a material per pixel (`ring`); sagekit/paint/palantir lights it as metal and blends it
into EA's upscaled frame, whose other parts (scroll joint, knots, spikes) take `orn_stops`.
"""
import numpy as np

from sagekit.paint.palantir import prof, tex
from sagekit.paint.palantir.core import Mat, fill, noise, ramp, smoothstep

from . import fx


class Faction:
    name = "base"
    side = "good"
    mats = [Mat((0.6, 0.5, 0.3))]
    orn_mat = 0
    orn_height = 1.6
    orn_mix = 0.55
    orn_stops = [(0, (0.03, 0.02, 0.01)), (0.5, (0.5, 0.4, 0.2)), (1, (1, 0.95, 0.8))]
    rim_col = (0.6, 0.65, 0.75)
    sky_col = (1.0, 0.97, 0.92)
    ground_col = (0.08, 0.07, 0.06)
    glass_col = (0.02, 0.02, 0.02)
    tick_col = (0.6, 0.55, 0.45)
    patina = 0.22
    rim_glow = None           # (colour, falloff px) inner-rim glow into the glass
    halo = None               # (colour, strength) glow in the drop shadow
    ember = None              # (colour, gain) glow in the crevices
    medals = []
    bloom = None              # (gain, (radii)) painted glow round the emissive parts
    shine = None              # (threshold, gain, radius, tint) bloom on the brightest metal
    glint = None              # (count, threshold, colour, (arm lengths)) four-point glints
    tex = {}                  # {name: tex.Tex}: the swatches cut from the citadel (set by the painter)

    def orn_colour(self, lum, x4):
        return ramp(self.orn_stops, lum)

    def ring(self, ctx, name):
        raise NotImplementedError

    def skin(self, p, name, s0, s1, mat, base=0.8, carve=0.8, lift=0.0, gain=1.0, v0=0.0, v1=1.0,
             aspect=1.0, wrap="repeat", flip=True, offset=0.0, soft=0):
        """Lay swatch `name` (cut from the citadel) over band [s0, s1] of P: its colour is the albedo,
        its luminance a relief (carve: the high-pass, the joints and carving; lift: bright parts
        proud). Returns (rgb, luminance, mask, u)."""
        rgb, lum, m, u = tex.skin(p.ctx, self.tex[name], s0, s1, v0, v1, aspect, wrap, flip, offset, soft)
        p.put(m, base + lift * lum + tex.relief(lum, 3, carve), mat)
        p.tint(m.astype(np.float32), np.clip(rgb * gain, 0, 1))
        return rgb, lum, m, u

    @staticmethod
    def rims(ctx):
        """[(ring, where the other ring leaves the glass alone)]; the single frame has no portrait."""
        m, p = ctx["minimap"], ctx.get("portrait")
        if p is None:
            return [(m, True)]
        return [(m, p.r > p.r_in), (p, m.r > m.r_out)]

    def glass(self, x4, lum, a4, ctx):
        tick = (np.clip(lum - 0.03, 0, 1) * 1.6)[..., None]
        col = np.array(self.glass_col, np.float32) * (1 - tick) + np.array(self.tick_col, np.float32) * tick
        col = col * np.ones(lum.shape + (1,), np.float32)
        if self.rim_glow:
            c, fall = self.rim_glow
            for r, other_ok in self.rims(ctx):
                din = r.r_in - r.r
                g = np.exp(-np.clip(din, 0, None) / fall) * (din > -1.0) * other_ok
                col += g[..., None] * np.array(c, np.float32)
        if self.halo:
            c, st = self.halo
            m, p = ctx["minimap"], ctx.get("portrait")
            out = m.r > m.r_out - 0.5
            if p is not None:
                out = (out & (p.r > p.r_out - 0.5)) | (out & (p.r < p.r_in))
            col += (np.clip(a4 * 1.4, 0, 1) * out * st)[..., None] * np.array(c, np.float32)
        return col

    def post(self, col, env):
        if self.ember:
            c, gain = self.ember
            cav = smoothstep(0.22, 0.6, env["cav"])
            m = env["ctx"]["minimap"]
            flick = 0.4 + 1.0 * noise(m.x * 0.25, m.yy * 0.25, 5)
            col = col + (gain * cav * flick)[..., None] * np.array(c, np.float32)
        return self.signature(col, env)

    def signature(self, col, env):
        """The look's bloom, shine and glints (fx.py), from its class settings."""
        a4 = env["a4"]
        if self.bloom:
            col = fx.bloom(col, env["emit"], a4, *self.bloom)
        if self.shine:
            col = fx.shine(col, a4, *self.shine)
        if self.glint:
            n, thr, c, size = self.glint
            where = (col @ fx.LUMA > thr) & fx.ring_mask(env, 0.3)
            col = fx.glints(col, where, n, c, size)
        return col

    def medal(self, lx, ly, R):
        z = np.zeros(lx.shape, np.float32)
        return z, z.astype(np.int16), z, np.zeros(lx.shape + (3,), np.float32)


def stamp(t, lx, ly, wpx, hpx, k=4):
    """Swatch t fitted to a wpx x hpx box centred on (lx, ly) = 0, its top row outward (+ly)."""
    x = (lx / wpx + 0.5) * t.w
    y = (0.5 - ly / hpx) * t.h
    return t.sample(np.clip(x, 0, t.w - 1), y, max(t.w / (wpx * k), t.h / (hpx * k)), "repeat")


def lancet(lx, ly, W, H):
    """A pointed (equilateral) arch W wide, H tall, centred, its point outward (+ly)."""
    ys = H / 2 - 0.866 * W
    top = np.maximum(np.hypot(lx - W / 2, ly - ys) - W, np.hypot(lx + W / 2, ly - ys) - W)
    low = np.maximum(np.abs(lx) - W / 2, -(ly + H / 2))
    return np.where(ly > ys, np.maximum(top, -(ly + H / 2)), low)


def disc(lx, ly, R, rim_mat, field_mat, rim_w=1.4, field_h=0.7, rim_h=1.5):
    """A medallion: a round plate with a raised bead rim. (height, material, coverage)."""
    d = np.hypot(lx, ly)
    cov = fill(d - R)
    u = np.clip((R - d) / rim_w, 0, 1)
    rimh = 0.4 + rim_h * np.sqrt(np.clip(1 - (2 * u - 1) ** 2, 0, 1))
    h = np.where(d > R - rim_w, rimh, field_h)
    mat = np.where(d > R - rim_w, rim_mat, field_mat).astype(np.int16)
    return h.astype(np.float32), mat, cov


def zero3(shape):
    return np.zeros(shape + (3,), np.float32)


__all__ = ["Faction", "disc", "lancet", "stamp", "zero3", "prof"]
