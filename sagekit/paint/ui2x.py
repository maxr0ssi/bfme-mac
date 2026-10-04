"""EA's painted UI art at 2x (numpy: run on Blender's Python, `python -m sagekit.paint.ui2x prep|finish
<job.json>`; sagekit/ui2x/build.py writes the job, docs/UI2X.md).

prep    per MappedImage rect: EA's pixels padded by their own edge, the colour under the invisible
        part filled from the visible part (so the upscaler never paints the colour outside a round
        button into its rim): the input Real-ESRGAN sees
finish  per rect: Real-ESRGAN's 4x box-filtered to 2x, with EA's own grain put back (the high
        frequencies of a Lanczos 2x of EA's pixels: Real-ESRGAN alone airbrushes the brush work),
        less of it where the result strays from EA's picture (busy noisy art);
        a rect of ours (an icon from sagekit/icons) is our 4x crop box-filtered to 2x instead;
        the alpha Lanczos 2x, a round button's disc steepened to a one-pixel edge and its rim an
        exact circle, every other mask (a portrait's vignette, the hero bar's silhouette) as soft
        as EA's; the rects pasted on
        a Lanczos 2x of EA's page; the mip chain box-filtered and sharpened a little; each rect
        checked against EA's: box-filtered back to 1x it must be EA's picture
tips    the tooltip frame's ten textures: Real-ESRGAN 4x recoloured (the frame by the Good palantir's
        metal, the glow EA's warmed), box-filtered to 2x
"""
import json
import os
import sys

import numpy as np

from .icons import downsample, load, save

PAD = 8                 # 1x pixels of edge padding round a rect before upscaling
HARD = 0.12             # a mask with fewer partial-alpha pixels than this (of the rect) is hard
GRAIN = 0.7             # how much of EA's own high frequencies goes back on Real-ESRGAN's
SMALL = 100             # rects narrower than this (buttons, hero bar faces) keep some Lanczos
SMALL_ESR = 0.8
STRAY = 0.045           # colour error at 1x past which less of Real-ESRGAN is used


def lanczos2(img):
    """A 2x Lanczos-3 upscale (pixel centres preserved), separable, edges extended."""
    def kern(phase):
        x = np.arange(-3, 4) - phase
        k = np.sinc(x) * np.sinc(x / 3)
        k[np.abs(x) >= 3] = 0
        return k / k.sum()

    def axis(a, ax):
        a = np.moveaxis(a, ax, 0)
        p = np.pad(a, [(3, 3)] + [(0, 0)] * (a.ndim - 1), mode="edge")
        n = a.shape[0]
        out = np.empty((2 * n,) + a.shape[1:], np.float32)
        for j, phase in ((0, -0.25), (1, 0.25)):     # output 2i+j sits at input i + phase
            k = kern(phase)
            out[j::2] = sum(p[t:t + n] * k[t] for t in range(7))
        return np.moveaxis(out, 0, ax)

    return axis(axis(img.astype(np.float32), 0), 1)


def gauss(img, s):
    r = int(3 * s + 1)
    x = np.arange(-r, r + 1)
    k = np.exp(-x * x / (2 * s * s))
    k /= k.sum()
    pad = [(r, r), (r, r)] + [(0, 0)] * (img.ndim - 2)
    p = np.pad(img, pad, mode="edge")
    t = sum(p[:, i:i + img.shape[1]] * k[i] for i in range(2 * r + 1))
    return sum(t[i:i + img.shape[0]] * k[i] for i in range(2 * r + 1))


def box3(img):
    p = np.pad(img, [(1, 1), (1, 1)] + [(0, 0)] * (img.ndim - 2), mode="edge")
    return sum(p[y:y + img.shape[0], x:x + img.shape[1]] for y in range(3) for x in range(3)) / 9


def hard(alpha):
    """Whether a rect's mask is hard (a round button's disc) rather than soft (a vignette)."""
    partial = ((alpha > 0.06) & (alpha < 0.94)).mean()
    return partial < HARD and alpha.min() < 0.5


def bleed(rgb, alpha, disc):
    """rgb with the colour under the invisible pixels filled outward from the visible ones; for a
    disc (a round button) its fringe too: EA's is dark there and drew as a stair-stepped rim. Any
    other shape keeps its fringe colour (the hero bar's light edge)."""
    vis = (alpha >= (0.97 if disc else 0.02)).astype(np.float32)
    if vis.all() or not vis.any():
        return rgb
    col, w = rgb * vis[..., None], vis.copy()
    out = rgb.copy()
    known = vis > 0
    for _ in range(max(rgb.shape[:2])):
        col, w = box3(col), box3(w)
        fill = (~known) & (w > 1e-4)
        out[fill] = col[fill] / w[fill][:, None]
        known |= fill
        col = out * known[..., None]
        w = known.astype(np.float32)
        if known.all():
            break
    return out


def crop_padded(page, rect):
    l, t, r, b = rect
    return np.pad(page[t:b, l:r], [(PAD, PAD), (PAD, PAD), (0, 0)], mode="edge")


def prep(job):
    for pg in job["pages"]:
        page = load(pg["src"])
        for rc in pg["rects"]:
            if rc.get("own"):
                continue
            c = crop_padded(page, rc["rect"])
            inner = c[PAD:-PAD, PAD:-PAD, 3]
            rgb = bleed(c[..., :3], c[..., 3], hard(inner) and circle(inner) is not None)
            save(rc["input"], np.concatenate([rgb, np.ones_like(c[..., :1])], -1))


def crossings(alpha):
    """Sub-pixel points (x, y) where the alpha crosses 0.5 along rows and columns (1x pixels,
    pixel centres at i + 0.5)."""
    pts = []
    for ax in (1, 0):
        a = alpha if ax == 1 else alpha.T
        lo, hi = a[:, :-1], a[:, 1:]
        ys, xs = np.nonzero((lo - 0.5) * (hi - 0.5) < 0)
        f = (0.5 - lo[ys, xs]) / (hi[ys, xs] - lo[ys, xs])
        p = np.stack([xs + 0.5 + f, ys + 0.5], -1)
        pts.append(p if ax == 1 else p[:, ::-1])
    return np.concatenate(pts)


def circle(alpha):
    """(cx, cy, r) of the disc a hard mask is, or None when its edge is not one (EA's staircase
    is fitted through, a shape that leaves the circle by more than a pixel and a half is not)."""
    p = crossings(alpha)
    if len(p) < 24:
        return None
    x, y = p[:, 0], p[:, 1]
    a = np.stack([x, y, np.ones_like(x)], -1)
    sol, *_ = np.linalg.lstsq(a, x * x + y * y, rcond=None)
    cx, cy = sol[0] / 2, sol[1] / 2
    r = np.sqrt(sol[2] + cx * cx + cy * cy)
    dev = np.abs(np.hypot(x - cx, y - cy) - r)
    if dev.max() > 1.5 or np.sqrt((dev ** 2).mean()) > 0.6:
        return None
    ang = np.degrees(np.arctan2(y - cy, x - cx))
    if len(np.unique(np.floor(ang / 30))) < 6:        # an arc of a circle is not enough evidence
        return None
    return cx, cy, r


def mask2x(padded):
    """EA's alpha at 2x (padded as the colour is): Lanczos, which keeps every edge as soft as EA
    drew it; a disc (a round button's hard mask) steepened to a one-pixel edge (its DXT noise
    smoothed first) and its rim drawn as an exact circle (EA's 1x discs are stair-stepped; at 2x
    the steps showed)."""
    a2 = np.clip(lanczos2(padded), 0, 1)
    inner = padded[PAD:-PAD, PAD:-PAD]
    c = circle(inner) if hard(inner) else None
    if c is None:
        return a2
    a2 = np.clip((box3(a2) - 0.5) * 2.2 + 0.5, 0, 1)
    cx, cy, r = c
    h, w = a2.shape
    ys = (np.arange(h, dtype=np.float32) + 0.5) / 2 - PAD
    xs = (np.arange(w, dtype=np.float32) + 0.5) / 2 - PAD
    d = 2 * np.hypot(xs[None, :] - cx, ys[:, None] - cy)
    cov = np.clip(2 * r - d + 0.5, 0, 1)
    return np.where(d < 2 * r - 2, a2, cov)


def rect2x(page, rc, sharpen_own):
    l, t, r, b = rc["rect"]
    ea = page[t:b, l:r]
    padded = crop_padded(page, rc["rect"])
    alpha = mask2x(padded[..., 3])[2 * PAD:-2 * PAD, 2 * PAD:-2 * PAD]
    rc["circle"] = bool(hard(ea[..., 3]) and circle(ea[..., 3]) is not None)
    vis = ea[..., 3] > 0.5

    def judged(rgb):
        """(rgb with alpha, colour error, alpha error): box-filtered back to 1x, it must be EA's
        picture (mean colour error where EA's is visible, and the alpha)."""
        out = np.concatenate([np.clip(rgb, 0, 1), alpha[..., None]], -1)
        one = downsample(out, 2)
        err = float(np.abs(one[..., :3] - ea[..., :3])[vis].mean()) if vis.any() else 0.0
        return out, err, float(np.abs(one[..., 3] - ea[..., 3]).mean())

    if rc.get("own"):                       # our icon: the graded 4x crop, box-filtered
        big = load(rc["own"])[..., :3]
        rgb = downsample(big, big.shape[0] // (2 * (b - t)))
        rc["esr"] = None
        return judged(rgb + sharpen_own.get(rc["kind"], 0.3) * (rgb - box3(rgb)))
    esr = load(rc["x4"])[..., :3]
    esr = downsample(esr, 2)[2 * PAD:-2 * PAD, 2 * PAD:-2 * PAD]
    lz = lanczos2(load(rc["input"])[..., :3])[2 * PAD:-2 * PAD, 2 * PAD:-2 * PAD]
    grain = GRAIN * (lz - gauss(lz, 1.2))
    # Real-ESRGAN invents strands in busy noisy art (webs, sparks): when the result strays from
    # EA's picture, less of it, down to Lanczos with EA's grain sharpened
    for w in (1.0 if min(r - l, b - t) >= SMALL else SMALL_ESR, 0.5, 0.0):
        out, err, aerr = judged(w * esr + (1 - w) * lz + grain)
        if err <= STRAY:
            break
    rc["esr"] = w
    return out, err, aerr


def levels(top, n):
    """The mip chain from the 2x page: box-filtered, the colour sharpened a little per level."""
    out = [top]
    for _ in range(n - 1):
        a = out[-1]
        h, w = a.shape[:2]
        ky, kx = (2 if h > 1 else 1), (2 if w > 1 else 1)
        a = a.reshape(h // ky, ky, w // kx, kx, 4).mean((1, 3))
        if min(a.shape[:2]) >= 4:
            a = np.concatenate([np.clip(a[..., :3] + 0.3 * (a[..., :3] - box3(a[..., :3])), 0, 1), a[..., 3:]], -1)
        out.append(a)
    return out


def finish(job):
    report = {}
    for pg in job["pages"]:
        page = load(pg["src"])
        top = np.clip(lanczos2(page), 0, 1)
        rows = []
        for rc in pg["rects"]:
            out, err, aerr = rect2x(page, rc, job.get("sharpen_own", {}))
            l, t, r, b = rc["rect"]
            top[2 * t:2 * b, 2 * l:2 * r] = out
            rows.append([rc["rect"], round(err, 4), round(aerr, 4), bool(rc.get("own")), rc["circle"], rc["esr"]])
            if rc.get("review"):
                save(rc["review"], out)
        for k, lv in enumerate(levels(top, pg["mips"])):
            save(os.path.join(pg["out"], "%d.png" % k), lv)
        report[pg["name"]] = rows
        print("finished", pg["name"], flush=True)
    with open(job["report"], "w") as fh:
        json.dump(report, fh, indent=0)


# the tooltip frame (sagekit/ui2x/tooltip.py): one set serves both sides, so it takes the Good
# palantir's metal (EA's is gold for both); the glow EA's own, warmed toward the ember a little
GLOW = (1.0, 0.86, 0.66)


def tips(job):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from assets.hud.look import LOOKS
    good = LOOKS["good"]
    luma = np.array([0.299, 0.587, 0.114], np.float32)
    for t in job["textures"]:
        esr = load(t["x4"])[..., :3]
        alpha2 = load(t["alpha2"])[..., 0]
        lum = esr @ luma
        col = good.regrade(lum) if t["kind"] == "frame" else np.clip(esr * np.array(GLOW, np.float32), 0, 1)
        two = downsample(col, 2)
        two = np.clip(two + 0.3 * (two - box3(two)), 0, 1)
        save(t["out2"], np.concatenate([two, alpha2[..., None]], -1))
        print("painted", t["name"], flush=True)


if __name__ == "__main__":
    {"prep": prep, "finish": finish, "tips": tips}[sys.argv[1]](json.load(open(sys.argv[2])))
