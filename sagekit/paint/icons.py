"""Grade a render to EA's icon look (numpy: run on Blender's Python, `python -m sagekit.paint.icons
<job.json>`; sagekit/icons/cli.py writes the job).

Portrait: our building and its ground over a parchment sky (EA's cloud texture, faint), a burnt
edge, then EA's tone: our luminance mapped rank for rank onto the luminance of EA's own portrait
(the histogram match), coloured by EA's sepia at that luminance, with a little of our own colour
kept (gold, fire, the blue banners read through as EA's hearth fire and Undermine glow do); EA's
vignette alpha exactly. Button: our close-up over a sky (a blue gradient and EA's clouds) or,
`sky=False`, over a dark stone wash, its luminance and colour moved part way to EA's button's;
EA's circle alpha exactly. Both are graded at the render's 4x, then box-filtered to the page's
size and sharpened a little (EA's icons are crisp).
"""
import json
import sys

import numpy as np

from ..icons import pixels

LUMA = np.array([0.299, 0.587, 0.114], np.float32)
DEFAULTS = {
    "portrait": dict(own=0.3, burn=0.45, sky=(0.50, 0.46, 0.36), clouds=0.35, sharpen=0.7, match=1.0),
    "button": dict(transfer=0.55, match=0.6, sky_top=(0.42, 0.58, 0.80), sky_low=(0.80, 0.86, 0.90),
                   clouds=0.75, wall=(0.36, 0.37, 0.35), sharpen=0.45),
}


def load(path):
    w, h, d = pixels.read(path)
    return np.frombuffer(d, np.uint8).reshape(h, w, 4).astype(np.float32) / 255


def save(path, img):
    h, w = img.shape[:2]
    pixels.write(path, w, h, np.clip(np.rint(img * 255), 0, 255).astype(np.uint8).tobytes())


def upsample(img, k):
    """Nearest-neighbour then a k-wide box blur: a smooth k-times larger copy (EA's alpha at 4x)."""
    if k == 1:
        return img
    big = np.repeat(np.repeat(img, k, 0), k, 1)
    pad = np.pad(big, [(k // 2, k // 2), (k // 2, k // 2)] + [(0, 0)] * (img.ndim - 2), mode="edge")
    c = np.cumsum(np.cumsum(pad, 0), 1)
    c = np.pad(c, [(1, 0), (1, 0)] + [(0, 0)] * (img.ndim - 2))
    h, w = big.shape[:2]
    return (c[k:k + h, k:k + w] - c[:h, k:k + w] - c[k:k + h, :w] + c[:h, :w]) / (k * k)


def downsample(img, k):
    h, w = img.shape[:2]
    return img.reshape(h // k, k, w // k, k, *img.shape[2:]).mean((1, 3))


def blur3(img):
    p = np.pad(img, [(1, 1), (1, 1)] + [(0, 0)] * (img.ndim - 2), mode="edge")
    return sum(p[y:y + img.shape[0], x:x + img.shape[1]] * wt
               for (y, x), wt in zip([(a, b) for a in range(3) for b in range(3)],
                                     [1, 2, 1, 2, 4, 2, 1, 2, 1])) / 16


def tile(tex, h, w, scale=1.0, shift=(0, 0)):
    """A texture's luminance tiled over (h, w), `scale` texels per pixel."""
    th, tw = tex.shape[:2]
    ys = ((np.arange(h) * scale + shift[0]) % th).astype(int)
    xs = ((np.arange(w) * scale + shift[1]) % tw).astype(int)
    return (tex[..., :3] @ LUMA)[ys][:, xs]


def match(values, weights, ref, ref_weights):
    """values mapped rank for rank onto the weighted distribution of ref (histogram matching).
    The curve is learnt from the values with weight (a portrait's building and ground, not its
    sky: a large even sky took the top ranks and glowed white at the horizon) and applied to all."""
    v, w = values.ravel(), weights.ravel()
    keep = w > 0
    order = np.argsort(v[keep])
    cw = np.cumsum(w[keep][order])
    ranks = np.interp(v, v[keep][order], cw / max(cw[-1], 1e-6))
    ro = np.argsort(ref, axis=None)
    rcw = np.cumsum(ref_weights.ravel()[ro])
    return np.interp(ranks, rcw / max(rcw[-1], 1e-6), ref.ravel()[ro]).reshape(values.shape).astype(np.float32)


def sepia(ea, alpha):
    """EA's colour as a function of luminance: (levels, mean RGB at each), over its opaque pixels."""
    rgb = ea[..., :3][alpha > 0.5]
    lum = rgb @ LUMA
    edges = np.quantile(lum, np.linspace(0, 1, 17))
    levels, cols = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (lum >= lo) & (lum <= hi)
        if m.any():
            levels.append(lum[m].mean())
            cols.append(rgb[m].mean(0) / max(lum[m].mean(), 1e-4))
    return np.array(levels), np.array(cols)


def radius(h, w):
    yy, xx = np.mgrid[:h, :w].astype(np.float32)
    return np.hypot((xx + 0.5) / w - 0.5, (yy + 0.5) / h - 0.5) * 2


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def over(fg, bg):
    a = fg[..., 3:4]
    return fg[..., :3] * a + bg * (1 - a)


def portrait(render, ea, clouds, o):
    h, w = render.shape[:2]
    k = h // ea.shape[0]
    alpha = upsample(ea[..., 3], k)
    lumc = tile(clouds, h, w, 0.5)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    sky = np.array(o["sky"], np.float32) * (1 - 0.12 * yy) * (1 + o["clouds"] * (lumc[..., None] - 0.6))
    img = over(render, sky)
    img *= (1 - o["burn"] * smoothstep(0.55, 1.05, radius(h, w)))[..., None]
    lum = img @ LUMA
    ea_alpha = ea[..., 3]
    target = match(lum, alpha * render[..., 3], ea[..., :3] @ LUMA, ea_alpha) * o["match"] + lum * (1 - o["match"])
    levels, cols = sepia(ea, ea_alpha)
    tint = np.stack([np.interp(target, levels, cols[:, c]) for c in range(3)], -1)
    own = (img - lum[..., None]) * (target / np.maximum(lum, 1e-3))[..., None]
    out = tint * target[..., None] + o["own"] * own
    return np.concatenate([np.clip(out, 0, 1), alpha[..., None]], -1)


STATS = np.array([[0.299, 0.587, 0.114], [1, -1, 0], [0.5, 0.5, -1]], np.float32)


def stats(rgb):
    """(luminance, red-green, yellow-blue) of (n, 3) colours."""
    return rgb @ STATS.T


def unstats(s):
    return np.linalg.solve(STATS, s.T).T


def button(render, ea, clouds, o, sky):
    h, w = render.shape[:2]
    k = h // ea.shape[0]
    alpha = upsample(ea[..., 3], k)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    if sky:
        back = np.array(o["sky_top"], np.float32) * (1 - yy) + np.array(o["sky_low"], np.float32) * yy
        c = tile(clouds, h, w, 0.3, (17, 41))        # a few large clouds, not a speckle
        puff = smoothstep(0.5, 0.8, c)[..., None] * o["clouds"]
        shade = 0.82 + 0.18 * smoothstep(0.5, 1.0, c)[..., None]
        back = back * (1 - puff) + np.float32(0.97) * shade * puff
    else:
        c = tile(clouds, h, w, 1.0)
        back = np.array(o["wall"], np.float32) * (0.85 + 0.3 * c[..., None]) * (1 - 0.25 * yy)
    img = over(render, back)
    flat = img.reshape(-1, 3)
    m, mea = alpha.ravel() > 0.5, ea[..., 3].ravel() > 0.5
    s, se = stats(flat), stats(ea[..., :3].reshape(-1, 3))
    out = s.copy()
    lum = match(s[:, 0], m.astype(np.float32), se[:, 0], mea.astype(np.float32))
    out[:, 0] = lum * o["match"] + s[:, 0] * (1 - o["match"])
    for c in (1, 2):
        mu, sd = s[m, c].mean(), s[m, c].std() + 1e-4
        mue, sde = se[mea, c].mean(), se[mea, c].std() + 1e-4
        moved = (s[:, c] - mu) / sd * sde + mue
        out[:, c] = moved * o["transfer"] + s[:, c] * (1 - o["transfer"])
    rgb = np.clip(unstats(out), 0, 1).reshape(h, w, 3)
    return np.concatenate([rgb, alpha[..., None]], -1)


def finish(big, ea, sharpen):
    """The page's size: box-filtered, sharpened, EA's alpha exactly."""
    k = big.shape[0] // ea.shape[0]
    small = downsample(big[..., :3], k)
    small = np.clip(small + sharpen * (small - blur3(small)), 0, 1)
    return np.concatenate([small, ea[..., 3:4]], -1)


def run(job):
    clouds = {k: load(v) for k, v in job["clouds"].items()}
    for it in job["icons"]:
        ea = load(it["ea"])
        o = dict(DEFAULTS[it["kind"]], **it.get("grade", {}))
        for src, big_out, out in it["renders"]:
            r = load(src)
            if r.shape[0] % ea.shape[0] or r.shape[1] % ea.shape[1]:
                raise SystemExit("%s: %dx%d is not a multiple of EA's %dx%d" % (src, r.shape[1], r.shape[0],
                                                                              ea.shape[1], ea.shape[0]))
            big = portrait(r, ea, clouds["parchment"], o) if it["kind"] == "portrait" else \
                button(r, ea, clouds["sky"], o, it["sky"])
            save(big_out, big)
            save(out, finish(big, ea, o["sharpen"]))
        print("graded", it["name"], flush=True)


if __name__ == "__main__":
    run(json.load(open(sys.argv[1])))
