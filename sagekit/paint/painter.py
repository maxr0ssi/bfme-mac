"""Run a style's paint stack over a building's canvas and write the game's textures.

diffuse:  <name>.png + <name>.dds (DXT1, full mips) at the tier size
normal:   <name>_nrm.tga at the tier's normal size: the original detail re-expressed in the new
          tangent space + bevelled edges + every layer's relief, in the game's convention
"""
import os

import numpy as np

from ..formats.textures import write_dds_dxt1
from . import imageio


def save_png(rgb, path):
    import bpy
    h, w = rgb.shape[:2]
    px = np.ones((h, w, 4), np.float32)
    px[..., :3] = rgb
    im = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    im.colorspace_settings.name = "sRGB"
    im.pixels.foreach_set(px.ravel())
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)


class Painter:
    def __init__(self, canvas, palette, layers, log=print):
        self.cv, self.pal, self.layers, self.log = canvas, palette, layers, log

    def diffuse(self):
        col = None
        for layer in self.layers:
            col = layer.apply(col, self.cv, self.pal)
            self.log("layer", type(layer).__name__)
        return np.clip(col, 0, 1)

    def write_diffuse(self, col, outdir, name, sizes):
        """One DDS per size (the first is the shipped one, others fallbacks named <name>_<size>)."""
        os.makedirs(outdir, exist_ok=True)
        filled = imageio.pull_push(col, self.cv.covm)
        out = {}
        for i, size in enumerate(sizes):
            img = imageio.downsample(filled, filled.shape[0] // size)
            stem = name if i == 0 else "%s_%d" % (name, size)
            png = os.path.join(outdir, stem + ".png")
            save_png(img, png)
            out[size] = write_dds_dxt1(png, os.path.join(outdir, stem + ".dds"))
            self.log("wrote", stem, out[size])
        return out

    def normal(self, ref_tga, path):
        cv = self.cv
        ndet = cv.load("ndet") * 2 - 1
        nbev = cv.load("nbev") * 2 - 1
        R = ndet.shape[0]
        f = cv.covm.shape[0] // R

        def ds(a):
            return a.reshape(R, f, R, f, *a.shape[2:]).mean((1, 3))
        cov = (ds(cv.covm) > 0.99).astype(np.float32)
        pos = ds(cv.pos)
        hs = [h for h in (layer.height(cv, ds) for layer in self.layers) if h is not None]
        Hh = sum(hs) if hs else np.zeros((R, R), np.float32)

        def slope(ax):                           # world-unit slopes along the texel axes
            hp, hm = np.roll(Hh, -1, ax), np.roll(Hh, 1, ax)
            pp, pm = np.roll(pos, -1, ax), np.roll(pos, 1, ax)
            ok = cov * np.roll(cov, -1, ax) * np.roll(cov, 1, ax)
            dist = np.linalg.norm(pp - pm, axis=-1)
            return np.where((ok > 0) & (dist > 1e-5), (hp - hm) / np.maximum(dist, 1e-5), 0)
        su, sv = slope(1), slope(0)
        for a in (ndet, nbev):
            a /= np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-6)
        n = np.stack([ndet[..., 0] + nbev[..., 0] - su, ndet[..., 1] + nbev[..., 1] - sv,
                      np.maximum(ndet[..., 2], 0.2)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        enc = imageio.pull_push(n * 0.5 + 0.5, cov)
        ref = imageio.read_tga24(ref_tga)
        imageio.write_tga24(path, imageio.gl_to_game(enc), ref["header"], ref["footer"])
        save_png(enc, path[:-4] + "_gl_preview.png")
        self.log("wrote", path)
