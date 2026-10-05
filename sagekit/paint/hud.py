"""Paint the palantir's textures (numpy: run on Blender's Python, `python -m sagekit.paint.hud
<job.json>`; sagekit/hud/cli.py writes the job, docs/HUD.md).

Per texture, at 4x EA's pixels:
  base    EA's texture upscaled 4x (Real-ESRGAN, colour; Lanczos, alpha), its metal recoloured by
          the side's look from its luminance (assets/hud/look.py `regrade`): the scroll joint, the
          resource bar, the knots and spikes stay EA's drawing, in our metal and four times sharper
  rings   each ring of the frame drawn again along EA's own edges where nothing sits on it
          (sagekit/paint/hudrings.py), blended into the base over a few degrees
  parts   for an atlas: only the rects the job names are recoloured (a button's bezel, a ring of
          the portrait's chain); every other pixel is EA's, upscaled
Then box-filtered to the two sizes we ship: 2x (EA's alpha resized Lanczos) and 1x (EA's alpha
exactly). Every texture's alpha stays EA's, so the APT movie draws the same shape.
"""
import json
import os
import sys

import numpy as np

from . import hudrings
from .icons import downsample, load, save

LUMA = np.array([0.299, 0.587, 0.114], np.float32)


def look_for(side):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from assets.hud.look import LOOKS
    return LOOKS[side]


def box(img, radius):
    """A (2 radius + 1)-wide box blur."""
    k = 2 * radius + 1
    pad = np.pad(img, [(radius, radius), (radius, radius)] + [(0, 0)] * (img.ndim - 2), mode="edge")
    c = np.cumsum(np.cumsum(pad, 0), 1)
    c = np.pad(c, [(1, 0), (1, 0)] + [(0, 0)] * (img.ndim - 2))
    h, w = img.shape[:2]
    return (c[k:k + h, k:k + w] - c[:h, k:k + w] - c[k:k + h, :w] + c[:h, :w]) / (k * k)


def unsharp(img, amount, radius=1):
    """img + amount * (img - a small box blur of it)."""
    if amount <= 0:
        return img
    return np.clip(img + amount * (img - box(img, radius)), 0, 1)


def bounded(alpha2, ea_alpha):
    """The Lanczos 2x alpha held between the least and the most of EA's alpha round each texel (its
    3 x 3 neighbourhood): no ringing, so a texel clear (or solid) all round in EA's stays exactly
    clear (or solid) in ours, and a glow or a masked button never grows a faint square round it."""
    h, w = ea_alpha.shape
    pad = np.pad(ea_alpha, 1, mode="edge")
    near = np.stack([pad[y:y + h, x:x + w] for y in range(3) for x in range(3)])
    lo, hi = (np.repeat(np.repeat(v, 2, 0), 2, 1) for v in (near.min(0), near.max(0)))
    return np.clip(alpha2, lo, hi)


def ember(col, opaque, look, k):
    """The look's faint forge-glow in the metal's crevices: wherever a pixel is darker than the
    metal round it (grooves, plate seams, between rivets, the cuts of EA's spikes), by how much."""
    if not look.ember_gain:
        return col
    lum = col @ LUMA
    cavity = np.clip((box(lum, 3 * k // 2) - lum) * 4, 0, 1) * opaque
    return np.clip(col + look.ember_gain * cavity[..., None] * np.array(look.ember_colour, np.float32), 0, 1)


def rect_mask(shape, rects, k, feather=1.0):
    """1 inside the 1x rects (l, t, r, b), scaled to k x, with a soft edge `feather` 1x px wide."""
    h, w = shape
    m = np.zeros((h, w), np.float32)
    ys = (np.arange(h, dtype=np.float32) + 0.5) / k
    xs = (np.arange(w, dtype=np.float32) + 0.5) / k
    for l, t, r, b in rects:
        fy = np.clip(np.minimum(ys - t, b - ys) / feather + 0.5, 0, 1)
        fx = np.clip(np.minimum(xs - l, r - xs) / feather + 0.5, 0, 1)
        m = np.maximum(m, fy[:, None] * fx[None, :])
    return m


def metal_weight(rgb):
    """1 on metal (grey, or bronze-to-gold hues), 0 on a coloured emblem or glow (blue, red, green)."""
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    gold = hudrings.smoothstep(8, 20, hue) * (1 - hudrings.smoothstep(58, 72, hue))
    grey = 1 - hudrings.smoothstep(0.18, 0.35, sat)
    return np.maximum(gold, grey).astype(np.float32)


def paint(job, tex):
    look = look_for(tex.get("side", "good"))
    k = 4
    ea = load(tex["ea"])
    esr = load(tex["x4"])[..., :3]
    alpha4 = load(tex["alpha4"])[..., 0]
    h, w = esr.shape[:2]
    lum = esr @ LUMA
    report = []
    if tex["kind"] == "atlas":              # recolour only the named rects, and only their metal
        col = esr.copy()
        metal = metal_weight(esr)
        for rect, side in tex["parts"]:
            m = (rect_mask((h, w), [rect], k) * metal)[..., None]
            col = look_for(side).regrade(lum) * m + col * (1 - m)
        report.append("%s: %d parts recoloured, %.1f%% of the sheet" % (
            tex["name"], len(tex["parts"]), 100 * rect_mask((h, w), [r for r, _ in tex["parts"]], k).mean()))
    else:
        col = look.regrade(lum)
    opaque = hudrings.smoothstep(0.5, 0.9, alpha4)
    for spec in tex.get("rings", []):
        ring = hudrings.measure(ea[..., 3], spec["centre"], spec["radii"])
        report.append("%s ring %s: %s" % (tex["name"], spec["name"], ring.describe()))
        height, mat, weight, _ = hudrings.draw(ring, look, k, (h, w))
        shade, spec_term = hudrings.light(height, k, look)
        ours = look.colour(mat, shade, spec_term)
        wgt = (weight * opaque)[..., None]
        col = ours * wgt + col * (1 - wgt)
    if tex["kind"] == "frame":
        col = ember(col, opaque, look, k)
    col = unsharp(col, tex.get("sharpen", 0.35))
    os.makedirs(os.path.dirname(tex["out4"]), exist_ok=True)
    save(tex["out4"], np.concatenate([col, alpha4[..., None]], -1))
    two = unsharp(downsample(col, 2), 0.25)
    alpha2 = bounded(load(tex["alpha2"])[..., 0], ea[..., 3])
    save(tex["out2"], np.concatenate([two, alpha2[..., None]], -1))
    one = unsharp(downsample(col, 4), 0.2)
    save(tex["out1"], np.concatenate([one, ea[..., 3:4]], -1))
    return report


def main(path):
    job = json.load(open(path))
    report = []
    for tex in job["textures"]:
        report += paint(job, tex)
    with open(job["report"], "w") as fh:
        fh.write("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main(sys.argv[1])
