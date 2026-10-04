"""Image steps of the heroes pack, on numpy (Blender's Python: `python -m assets.heroes.imaging
<jobs.json>`; run() writes the jobs and calls it). Each job is {"op": ..., ...}:

  recolour   EA's sheet with its red cloth repainted through a palette ramp (by luminance), and the
             unit house-colour mask of what was repainted (RGB the cloth's shading, alpha the area):
             the game tints it with the player's colour, as EA's HC_ masks do
  unit_mask  a Create-a-Hero 3-colour mask (alpha: tinted; G: cloth) as a unit mask (G only)
  portrait   a hero portrait (EA's HP look): our render's luminance matched rank for rank to EA's
             portrait, coloured by EA's sepia at that luminance with some of our colour kept, on
             EA's parchment, inside EA's alpha
  icon       a hero icon (EA's HI look): the render's figure cut out, toned part way to EA's icon
  polish     a copy of EA's sheet with more contrast (Aragorn's plates, lifted off his own surface)
  revive     the revive icon (EA's HI_res look): our icon's luminance through EA's blue at that
             luminance, on EA's disc and alpha
Every output is checked for size; renders are graded at their size then box-filtered.
"""
import json
import subprocess
import sys

try:                                        # Blender's Python has numpy; the host only calls run()
    import numpy as np
    LUMA = np.array([0.299, 0.587, 0.114], np.float32)
except ImportError:
    np = LUMA = None


def load(path):
    w, h = (int(x) for x in subprocess.check_output(["magick", "identify", "-format", "%w %h", path + "[0]"]).split())
    data = subprocess.check_output(["magick", path + "[0]", "-depth", "8", "RGBA:-"])
    return np.frombuffer(data, np.uint8).reshape(h, w, 4).astype(np.float32) / 255


def save(path, img):
    h, w = img.shape[:2]
    data = np.clip(np.rint(img * 255), 0, 255).astype(np.uint8).tobytes()
    subprocess.run(["magick", "-size", "%dx%d" % (w, h), "-depth", "8", "RGBA:-", path], input=data, check=True)


def ramp(points, v):
    xs = np.array([p[0] for p in points], np.float32)
    out = np.stack([np.interp(v, xs, [p[1][k] for p in points]) for k in range(3)], -1)
    return out.astype(np.float32)


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-6
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    return h, d / (mx + 1e-6), mx


def recolour(j):
    img = load(j["src"])
    rgb = img[..., :3]
    h, s, v = hsv(rgb)
    hue = np.minimum(h, 1 - h)                              # distance from red
    w = np.clip((j["hue"] - hue) / j["soft"], 0, 1) * np.clip((s - j["sat"]) / .12, 0, 1) * np.clip((v - .05) / .06, 0, 1)
    lum = (rgb * LUMA).sum(-1)
    col = ramp(j["ramp"], np.clip(lum * j["gain"] + j["lift"], 0, 1))
    out = img.copy()
    out[..., :3] = rgb * (1 - w[..., None]) + col * w[..., None]
    save(j["out"], out)
    mask = np.zeros_like(img)
    shade = np.clip(.35 + lum * 2.2, 0, 1)
    mask[..., 0] = mask[..., 1] = mask[..., 2] = shade * (w > .02)
    mask[..., 3] = w
    if j.get("mask_size"):
        k = img.shape[0] // j["mask_size"]
        mask = mask.reshape(j["mask_size"], k, mask.shape[1] // k, k, 4).mean((1, 3))
    save(j["mask"], mask)
    return dict(repainted=float((w > .5).mean()))


def unit_mask(j):
    m = load(j["src"])
    g = m[..., 1] * (m[..., 1] >= np.maximum(m[..., 0], m[..., 2]))
    out = np.zeros_like(m)
    out[..., 0] = out[..., 1] = out[..., 2] = g
    out[..., 3] = m[..., 3] * (g > 0)
    save(j["out"], out)
    return dict(tinted=float((out[..., 3] > .5).mean()))


def box(img, k):
    h, w = img.shape[:2]
    return img.reshape(h // k, k, w // k, k, img.shape[2]).mean((1, 3))


def sharpen(img, amount):
    blur = img.copy()
    blur[1:-1, 1:-1] = (img[:-2, 1:-1] + img[2:, 1:-1] + img[1:-1, :-2] + img[1:-1, 2:] + img[1:-1, 1:-1]) / 5
    out = img + (img - blur) * amount
    out[..., 3] = img[..., 3]
    return np.clip(out, 0, 1)


def match(lum, ref, weights=None):
    """lum's values replaced by ref's at the same rank (weights: which of lum's pixels count)."""
    flat = lum.ravel()
    sel = flat if weights is None else flat[weights.ravel() > .5]
    ranks = np.searchsorted(np.sort(sel), flat) / max(1, len(sel) - 1)
    return np.quantile(ref, np.clip(ranks, 0, 1)).reshape(lum.shape).astype(np.float32)


def colour_table(ref):
    """EA's mean colour per luminance bin (64 bins, empty bins interpolated)."""
    lum = (ref[..., :3] * LUMA).sum(-1)
    a = ref[..., 3] > .5
    bins = np.clip((lum[a] * 63).astype(int), 0, 63)
    tab = np.zeros((64, 3), np.float32)
    have = np.zeros(64, bool)
    for b in range(64):
        sel = bins == b
        if sel.sum() > 3:
            tab[b] = ref[..., :3][a][sel].mean(0)
            have[b] = True
    xs = np.nonzero(have)[0]
    for k in range(3):
        tab[:, k] = np.interp(np.arange(64), xs, tab[xs, k])
    return tab


def portrait(j):
    """192 x 192 at 4x: our render over EA's parchment, graded to EA's portrait."""
    ours, ea = load(j["render"]), load(j["ea"])               # ours 768x768 RGBA, EA's 192x192 crop
    k = ours.shape[0] // ea.shape[0]
    ea4 = np.repeat(np.repeat(ea, k, 0), k, 1)
    alpha = ours[..., 3:4]
    lum = (ours[..., :3] * LUMA).sum(-1)
    ea_lum = (ea[..., :3] * LUMA).sum(-1)[ea[..., 3] > .5]
    m = match(lum, ea_lum, alpha[..., 0])
    tab = colour_table(ea)
    sepia = tab[np.clip((m * 63).astype(int), 0, 63)]
    own = j.get("own", .3)
    ourcol = ours[..., :3] / np.maximum(lum[..., None], 1e-3) * m[..., None]
    fig = sepia * (1 - own) + np.clip(ourcol, 0, 1) * own
    yy, xx = np.mgrid[0:ours.shape[0], 0:ours.shape[1]] / ours.shape[0] - .5
    ground = np.median(tab[20:44], 0) * (1 - .55 * np.clip(np.hypot(xx, yy * 1.1) * 1.6, 0, 1))[..., None]
    rgb = fig * alpha + ground * (1 - alpha)
    out = np.concatenate([rgb, ea4[..., 3:4]], -1)
    out = sharpen(box(out, k), j.get("sharpen", .5))
    out[..., 3] = ea[..., 3]
    save(j["out"], out)
    return dict(size=out.shape[:2])


def icon(j):
    """64 x 64 at 4x: the figure cut out (alpha its silhouette, faded at the chest), toned toward EA's."""
    ours, ea = load(j["render"]), load(j["ea"])
    k = ours.shape[0] // ea.shape[0]
    lum = (ours[..., :3] * LUMA).sum(-1)
    a = ours[..., 3]
    ea_lum = (ea[..., :3] * LUMA).sum(-1)[ea[..., 3] > .5]
    m = match(lum, ea_lum, a)
    t = j.get("transfer", .55)
    tab = colour_table(ea)
    toned = tab[np.clip((m * 63).astype(int), 0, 63)]
    ourcol = np.clip(ours[..., :3] / np.maximum(lum[..., None], 1e-3) * m[..., None], 0, 1)
    rgb = toned * t + ourcol * (1 - t)
    y = np.arange(ours.shape[0])[:, None] / ours.shape[0]
    fade = np.clip((1.0 - y) / .1, 0, 1)
    out = np.concatenate([rgb, (a * fade)[..., None]], -1)
    out[..., :3] *= out[..., 3:4] > 0
    out = sharpen(box(out, k), j.get("sharpen", .45))
    save(j["out"], out)
    return dict(size=out.shape[:2])


def revive(j):
    """EA's revive icon look: our icon's luminance through EA's blues, on EA's disc, EA's alpha."""
    ours, ea = load(j["icon"]), load(j["ea"])
    lum = (ours[..., :3] * LUMA).sum(-1)
    tab = colour_table(ea)
    ea_lum = (ea[..., :3] * LUMA).sum(-1)[ea[..., 3] > .5]
    m = match(lum, ea_lum, ours[..., 3])
    blue = tab[np.clip((m * 63).astype(int), 0, 63)]
    disc = tab[52]
    a = ours[..., 3:4]
    out = np.concatenate([blue * a + disc * (1 - a), ea[..., 3:4]], -1)
    save(j["out"], out)
    return dict(size=out.shape[:2])


def polish(j):
    """EA's sheet as plate: more contrast and a little lift, so the lifted plates read as burnished
    metal over the cloth and mail they copy (alpha kept)."""
    img = load(j["src"])
    rgb = img[..., :3]
    lum = (rgb * LUMA).sum(-1)[..., None]
    out = img.copy()
    out[..., :3] = np.clip((rgb - .5) * j.get("contrast", 1.25) + .5 + j.get("lift", .03) + (rgb - lum) * j.get("saturation", .1), 0, 1)
    save(j["out"], out)
    return dict(size=img.shape[:2])


OPS = {"polish": polish, "recolour": recolour, "unit_mask": unit_mask, "portrait": portrait, "icon": icon, "revive": revive}


def run(jobs, workdir):
    """Run `jobs` on Blender's Python (numpy); returns their results."""
    from pathlib import Path
    from sagekit import paths
    spec = Path(workdir) / "imaging-jobs.json"
    spec.write_text(json.dumps(jobs, indent=1))
    out = subprocess.run([paths.blender_python(), "-m", "assets.heroes.imaging", str(spec)], cwd=paths.REPO,
                         capture_output=True, text=True)
    if out.returncode:
        raise SystemExit("heroes: imaging failed:\n" + out.stderr[-3000:])
    return json.loads(out.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    results = [OPS[j["op"]](j) for j in json.loads(open(sys.argv[1]).read())]
    print(json.dumps(results))
