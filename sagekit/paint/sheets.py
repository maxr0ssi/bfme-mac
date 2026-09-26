"""Recolour a faction's own texture sheets to its palette, in the sheets' own pixel space.

Every model a faction has not redesigned yet (and every part that keeps the shared sheets:
debris, scaffolding, doors, add-ons) is painted from these sheets, so recolouring them keeps the
whole faction in one palette. Each sheet is decoded, upscaled 4x (Real-ESRGAN), its materials
masked (sagekit/paint/masks.py, with the Atlas's hints when the sheet is a known atlas), passed
through the style's sheet layers (the colour layers: no geometry exists here) and written back as
DDS at the faction's sheet size. Alpha (team colour, cut-outs) is kept: resized, never repainted.

Runs on Blender's bundled Python (numpy), no Blender needed:
    python3.11 -m sagekit.paint.sheets <faction> <in.dds> <out.dds> <size>
"""
import os
import subprocess
import sys
import tempfile

import numpy as np

from ..formats.textures import MAGICK, dds_info, full_chain
from . import masks as masklib


def read_rgba(path):
    """(h, w, 4) float32 0..1, rows TOP-down, via ImageMagick."""
    w, h = (int(x) for x in subprocess.check_output([MAGICK, "identify", "-format", "%w %h", path + "[0]"]).split())
    raw = subprocess.check_output([MAGICK, path + "[0]", "-depth", "8", "rgba:-"])
    return np.frombuffer(raw, np.uint8).reshape(h, w, 4).astype(np.float32) / 255


def write_png(rgba, path):
    h, w = rgba.shape[:2]
    data = np.clip(np.rint(rgba * 255), 0, 255).astype(np.uint8).tobytes()
    subprocess.run([MAGICK, "-size", "%dx%d" % (w, h), "-depth", "8", "rgba:-", path], input=data, check=True)


def write_dds(png, dds, alpha):
    w = int(subprocess.check_output([MAGICK, "identify", "-format", "%w", png]).decode())
    subprocess.check_call([MAGICK, png, "-define", "dds:compression=%s" % ("dxt5" if alpha else "dxt1"),
                           "-define", "dds:mipmaps=%d" % (full_chain(w) - 1), "-define", "dds:cluster-fit=true", dds])


class SheetCanvas:
    """The Canvas interface the colour layers use, for a flat sheet (no geometry)."""

    def __init__(self, rgb_bottom_up, atlas):
        self.rgb = rgb_bottom_up
        self.atlas = atlas
        self.masks = dict(zip(masklib.NAMES, masklib.compute(rgb_bottom_up, atlas, coherent=True)))
        self.lum = rgb_bottom_up @ np.array([0.3, 0.59, 0.11], np.float32)
        self.covm = np.ones(self.lum.shape, np.float32)
        m = self.masks
        self.w_stone = np.clip(1 - (m["bronze"] + m["gold"] + m["wood"] + m["ground"] + m["glyph"] + m["iron"]
                                    + m["rock"] + m["tiles"]), 0, 1)
        from .fields import box_blur
        self.bronze_blur = box_blur(box_blur(m["bronze"], 5), 5)

    def __getattr__(self, name):
        if name in masklib.NAMES:
            return self.masks[name]
        raise AttributeError(name)


def keep_motifs(col, cv):
    """The atlas's `keep` rects (original px, top-down) show EA's own colours wherever the masks do
    not take them for stone: a painted figure (the Elven eagle, EBFE) keeps its feathers, the stone
    round it takes the palette."""
    keep = getattr(cv.atlas, "keep", None)
    if not keep:
        return col
    h, w = cv.lum.shape
    f = h / float(cv.atlas.size)
    k = np.zeros((h, w), np.float32)
    for rects in keep.values():
        for x0, y0, x1, y1 in rects:
            k[h - int(y1 * f):h - int(y0 * f), int(x0 * f):int(x1 * f)] = 1.0      # rows are bottom-up here
    k = (k * np.clip(1 - cv.w_stone, 0, 1))[..., None]
    return col * (1 - k) + cv.rgb * k


def recolour_sheet(style, src_dds, out_dds, size, upscaler):
    info = dds_info(src_dds)
    alpha = info["fourcc"] in ("DXT3", "DXT5")
    with tempfile.TemporaryDirectory() as tmp:
        src_png, up_png = os.path.join(tmp, "src.png"), os.path.join(tmp, "up.png")
        subprocess.check_call([MAGICK, src_dds + "[0]", "-alpha", "off", src_png])
        subprocess.check_call([upscaler, "-i", src_png, "-o", up_png, "-n", "realesrgan-x4plus",
                               "-m", os.path.join(os.path.dirname(upscaler), "models")],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        up = read_rgba(up_png)[..., :3]
        cv = SheetCanvas(up[::-1].copy(), style.sheet_atlas(os.path.basename(src_dds)))
        col = None
        for layer in style.sheet_layers():
            col = layer.apply(col, cv, style.palette)
        col = keep_motifs(col, cv)
        col = np.clip(col, 0, 1)[::-1]                       # back to top-down rows
        a = np.ones(col.shape[:2] + (1,), np.float32)
        if alpha:
            a_png = os.path.join(tmp, "a.png")
            subprocess.check_call([MAGICK, src_dds + "[0]", "-alpha", "extract", "-filter", "Lanczos",
                                   "-resize", "%dx%d!" % (col.shape[1], col.shape[0]), a_png])
            a = read_rgba(a_png)[..., :1]
        rgba = np.concatenate([col, a], -1)
        f = rgba.shape[0] // size if rgba.shape[0] > size else 1
        if f > 1:
            h, w = rgba.shape[:2]
            rgba = rgba.reshape(h // f, f, w // f, f, 4).mean((1, 3))
        png = os.path.join(tmp, "out.png")
        write_png(rgba, png)
        os.makedirs(os.path.dirname(out_dds), exist_ok=True)
        write_dds(png, out_dds, alpha)
    return dds_info(out_dds)


def main():
    faction, src, out, size, upscaler = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
    from ..__main__ import _style
    print(recolour_sheet(_style(faction), src, out, size, upscaler))


if __name__ == "__main__":
    main()
