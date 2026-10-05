"""Swatches cut from a faction's citadel, laid along the palantir's bands (numpy; Blender's Python).

A swatch is a crop of the sheet the citadel is painted with (assets/hud/factions/swatches.py). `Tex`
keeps a box-filtered mip chain so a frieze shrunk into a 5 px band does not alias; `skin` lays one
across a band of a ring (its height across the band, repeated a whole number of times round it) and
returns the colour, its luminance and a relief taken from it."""
import os

import numpy as np

from ..hudrings import bilinear
from ..icons import load
from .core import K, blur

LUMA = np.array([0.299, 0.587, 0.114], np.float32)


class Tex:
    def __init__(self, rgb):
        self.mips = [rgb.astype(np.float32)]
        while min(self.mips[-1].shape[:2]) >= 4:
            m = self.mips[-1]
            h, w = (m.shape[0] // 2) * 2, (m.shape[1] // 2) * 2
            self.mips.append(m[:h, :w].reshape(h // 2, 2, w // 2, 2, 3).mean((1, 3)))
        self.h, self.w = rgb.shape[:2]

    def sample(self, x, y, texel_per_px, wrap="repeat"):
        """Colour at texel coords (x, y) of the full-size swatch; x repeats (or mirrors), y clamps."""
        lvl = int(np.clip(np.floor(np.log2(max(texel_per_px, 1.0))), 0, len(self.mips) - 1))
        m = self.mips[lvl]
        f = 2.0 ** lvl
        mh, mw = m.shape[:2]
        xs = x / f - 0.5
        if wrap == "mirror":
            xs = np.mod(xs, 2 * mw)
            xs = np.where(xs >= mw, 2 * mw - 1 - xs, xs)
        else:
            xs = np.mod(xs, mw)
        ys = np.clip(y / f - 0.5, 0, mh - 1.001)
        # wrap the bilinear tap round the right edge
        pad = np.concatenate([m, m[:, :1]], 1)
        return bilinear(pad, np.clip(xs, 0, mw - 0.001), ys)


def load_all(folder):
    """{name: Tex} of a look's swatches (empty when the folder is missing)."""
    out = {}
    if folder and os.path.isdir(folder):
        for n in sorted(os.listdir(folder)):
            if n.endswith(".png"):
                out[n[:-4]] = Tex(load(os.path.join(folder, n))[..., :3])
    return out


def skin(ctx, tex, s0, s1, v0=0.0, v1=1.0, aspect=1.0, wrap="repeat", flip=True, offset=0.0):
    """Lay rows v0..v1 of `tex` across band [s0, s1] of a ring (or the bar), its top row outward
    (flip) so a frieze reads upright at the top of the ring. aspect stretches it along the ring.
    Returns (rgb, luminance, mask, u)."""
    u = (ctx.s - s0) / (s1 - s0)
    m = (ctx.s >= s0) & (ctx.s < s1)
    bw = (s1 - s0) * float(np.median(ctx.bw))                 # band width, 1x px
    rows = (v1 - v0) * tex.h
    scale = rows / bw                                         # texels per 1x px across
    tile = tex.w / (scale / aspect)                           # one repeat along the ring, 1x px
    n = max(1, int(round(ctx.C / tile)))
    if wrap == "mirror":
        n = max(2, 2 * int(round(ctx.C / (2 * tile))))         # mirrored pairs close round the ring
    along = (ctx.t / (ctx.C / n) + offset) * tex.w
    vv = (1 - np.clip(u, 0, 1)) if flip else np.clip(u, 0, 1)
    y = (v0 + vv * (v1 - v0)) * tex.h
    rgb = tex.sample(along, y, scale / K, wrap)
    return rgb, rgb @ LUMA, m, u


def relief(lum, r=3, gain=1.0):
    """A height from a swatch's luminance: its high-pass (the carving, the joints)."""
    return gain * (lum - blur(lum, r, 2))
