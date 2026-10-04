"""The HUD review panels (numpy: run on Blender's Python, `python -m sagekit.paint.hudsheet <job.json>`;
sagekit/hud/sheet.py writes the job and lays the panels out with labels).

  pages    EA's texture and ours, flattened on the sheet's grey, both shown at 2x (EA's magnified
           as the game magnifies it: bilinear, no mips)
  zooms    a detail of each at 4x EA's pixels (EA's 1x magnified 4x, ours 2x magnified 2x)
  mockups  the bottom-left of the screen as the game composes it: a screenshot's terrain, the
           frame drawn over it at the size the game draws it (EA's 1x, ours 2x, bilinear, no mips),
           at 3024x1964 (Retina on) and 1512x982 (Retina off: half the scale, so our 2x is shrunk)
"""
import json
import sys

import numpy as np

from .hudrings import bilinear
from .icons import load, save

BG = np.array([0x26, 0x26, 0x26], np.float32) / 255


def flatten(rgba, bg=BG):
    return rgba[..., :3] * rgba[..., 3:4] + bg * (1 - rgba[..., 3:4])


def sample(tex, scale):
    """tex resized by `scale` with bilinear filtering and no mip levels, as the game draws a UI texture."""
    h, w = tex.shape[:2]
    H, W = int(round(h * scale)), int(round(w * scale))
    ys, xs = np.mgrid[:H, :W].astype(np.float32)
    return bilinear(tex, (xs + 0.5) / scale - 0.5, (ys + 0.5) / scale - 0.5)


def draw(shape, tex, sx, sy, ox, oy):
    """tex as an RGBA layer of `shape` with texel (u, v) at (ox + u * sx, oy + v * sy), bilinear, no mips."""
    h, w = shape
    ys, xs = np.mgrid[:h, :w].astype(np.float32)
    u, v = (xs + 0.5 - ox) / sx - 0.5, (ys + 0.5 - oy) / sy - 0.5
    inside = (u > -0.5) & (v > -0.5) & (u < tex.shape[1] - 0.5) & (v < tex.shape[0] - 0.5)
    px = np.zeros((h, w, 4), np.float32)
    px[inside] = bilinear(tex, u[inside], v[inside])
    return px


def above(shape, circles, rects, k):
    """1 where the backdrop shows something the game draws over the frame (its buttons, the
    resource text): circles (x, y, r) and rects (l, t, r, b) in the 3024x1964 backdrop's pixels."""
    h, w = shape
    ys, xs = np.mgrid[:h, :w].astype(np.float32)
    xs, ys = (xs + 0.5) / k, (ys + 0.5) / k
    m = np.zeros((h, w), np.float32)
    for cx, cy, r in circles:
        m = np.maximum(m, np.clip(r + 1.5 - np.hypot(xs - cx, ys - cy), 0, 1))
    for l, t, r, b in rects:
        m = np.maximum(m, ((xs >= l) & (xs < r) & (ys >= t) & (ys < b)).astype(np.float32))
    return m


def place(canvas, layer, opaque_only=True):
    """layer (RGBA) over canvas; opaque_only: only where it is nearly opaque (the screenshot under
    it already carries EA's own frame, whose see-through glass and shadow would be laid on twice)."""
    a = layer[..., 3:4]
    if opaque_only:
        a = np.clip((a - 0.82) / 0.13, 0, 1)
    return layer[..., :3] * a + canvas * (1 - a)


def main(path):
    job = json.load(open(path))
    for p in job["pages"]:
        ea, ours = load(p["ea"]), load(p["ours"])
        save(p["out_ea"], np.concatenate([flatten(sample(ea, 2.0)), np.ones(ours.shape[:2] + (1,), np.float32)], -1))
        save(p["out_ours"], np.concatenate([flatten(ours), np.ones(ours.shape[:2] + (1,), np.float32)], -1))
        l, t, r, b = p["zoom"]
        z_ea = sample(ea[t:b, l:r], 4.0)
        z_ours = sample(ours[2 * t:2 * b, 2 * l:2 * r], 2.0)
        for img, out in ((z_ea, p["zoom_ea"]), (z_ours, p["zoom_ours"])):
            save(out, np.concatenate([flatten(img), np.ones(img.shape[:2] + (1,), np.float32)], -1))
    for m in job["mockups"]:
        back = load(m["backdrop"])[..., :3]
        k = m["scale"]                                    # 1 at 3024x1964, 0.5 at 1512x982
        if k != 1:
            back = sample(np.concatenate([back, np.ones(back.shape[:2] + (1,), np.float32)], -1), k)[..., :3]
        canvas = back
        keep = above(back.shape[:2], m["above"]["circles"], m["above"]["rects"], k)[..., None]
        for layer in m["layers"]:
            f = layer["texels"]                           # 1 for EA's 1x, 2 for our 2x
            sx, sy, ox, oy = layer["transform"]
            px = draw(back.shape[:2], load(layer["texture"]), sx * k / f, sy * k / f, ox * k, oy * k)
            canvas = place(canvas, px, layer.get("opaque_only", True))
        canvas = canvas * (1 - keep) + back * keep
        save(m["out"], np.concatenate([canvas, np.ones(canvas.shape[:2] + (1,), np.float32)], -1))


if __name__ == "__main__":
    main(sys.argv[1])
