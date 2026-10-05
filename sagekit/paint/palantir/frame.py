"""Paint a faction's palantir frame (numpy; Blender's Python): EA's frame upscaled 4x, its rings and
the resource bar's rails drawn again in the faction's cross-section, the rest (scroll joint, knots,
spikes) recoloured by the faction's ornament ramp. Ships at 2x with EA's alpha resized; the mock-up
composites it over an in-game screenshot where the game draws it (docs/HUD.md).

Sources are the Good/Evil pack's (build/assets/_hud): src/<key>.png (EA's page), up/<key>_x4.png
(Real-ESRGAN colour), up/<key>_a4.png and _a2.png (EA's alpha, Lanczos).
"""
import os

import numpy as np

from .. import hudrings
from ..hudsheet import above, draw
from ..icons import load, save
from .core import K, RingCtx, blur, downsample, fbm, shade, smoothstep, unsharp

LUMA = np.array([0.299, 0.587, 0.114], np.float32)
# EA's page per side and frame: the double (minimap and portrait) and the single (minimap alone)
KEYS = {("good", "double"): "palantirexport_17", ("good", "single"): "palantirexport_20",
        ("evil", "double"): "palantirexport_11", ("evil", "single"): "palantirexport_14"}
RINGS = {"minimap": ((127.5, 128.5), (95, 135)), "portrait": ((286.5, 148.5), (66, 110))}
# the resource bar's slot (1x): a capsule; its rails are drawn RAIL px round it
SLOT = dict(x0=47.0, x1=208.0, y=218.0, r=9.0)
RAIL = 7.5

_CACHE = {}


def sources(hud, side, kind):
    """(key, EA's page, alpha 4x, alpha 2x, colour 4x, measured rings, ring coordinates)."""
    if (side, kind) in _CACHE:
        return _CACHE[side, kind]
    key = KEYS[side, kind]
    ea = load(os.path.join(hud, "src", key + ".png"))
    a4 = load(os.path.join(hud, "up", key + "_a4.png"))[..., 0]
    a2 = load(os.path.join(hud, "up", key + "_a2.png"))[..., 0]
    x4 = load(os.path.join(hud, "up", key + "_x4.png"))[..., :3]
    names = ("minimap", "portrait") if kind == "double" else ("minimap",)
    rings = {n: hudrings.measure(ea[..., 3], *RINGS[n]) for n in names}
    if kind == "double":
        # the minimap ring runs on over the portrait ring (it is on top there): redraw it there too
        rings["minimap"].inner[np.r_[np.arange(338, 360), np.arange(0, 32)]] = True
    ctx = {n: RingCtx(rings[n], a4.shape) for n in rings}
    _CACHE[side, kind] = (key, ea, a4, a2, x4, rings, ctx)
    return _CACHE[side, kind]


class BarCtx:
    """The resource bar's rails as a ring-like band: s outward from the slot's edge."""

    def __init__(self, shape, k=K):
        h, w = shape
        ys, xs = np.mgrid[:h, :w].astype(np.float32)
        x, y = (xs + 0.5) / k - 0.5, (ys + 0.5) / k - 0.5
        cx = np.clip(x, SLOT["x0"], SLOT["x1"])
        d = np.hypot(x - cx, y - SLOT["y"]) - SLOT["r"]
        self.s = d / RAIL
        self.bw = np.full(shape, RAIL, np.float32)
        self.t = x.copy()
        self.C = 2 * (SLOT["x1"] - SLOT["x0"]) + 2 * np.pi * (SLOT["r"] + RAIL / 2)
        self.y = self.s * RAIL
        self.x, self.yy = x, y
        self.deg = np.where(y < SLOT["y"], 270.0, 90.0) + 0 * x
        inside = smoothstep(-0.04, 0.02, self.s) * (1 - smoothstep(0.97, 1.03, self.s))
        xw = smoothstep(39.5, 43.5, x) * (1 - smoothstep(211.5, 215.5, x))
        self.weight = inside * xw * (y < 240)
        self.r_in = SLOT["r"]

    def cell(self, approx_px, offset=0.0):
        n = max(4, int(round(self.C / approx_px)))
        L = self.C / n
        tt = self.t + offset * L
        idx = np.floor(tt / L)
        return tt - (idx + 0.5) * L, idx.astype(int) % n, L


def safe(ctx, keep, place):
    """Where a protrusion may draw: outside both glasses, 6 screen px clear of what the game draws
    over the frame (keep: the buttons and the resource numbers in the 3024x1964 backdrop; place:
    the page's scale and offset there)."""
    m, p = ctx["minimap"], ctx.get("portrait")
    ok = m.r > m.r_in + 1.0
    if p is not None:
        ok &= p.r > p.r_in + 1.0
    if keep and place:
        sx, sy, ox, oy = place
        X, Y = m.x * sx + ox, m.yy * sy + oy
        for cx, cy, r in keep["circles"]:
            ok &= np.hypot(X - cx, Y - cy) > r + 6
        for l, t, r, b in keep["rects"]:
            ok &= ~((X > l - 6) & (X < r + 6) & (Y > t - 6) & (Y < b + 6))
    return ok


def paint(F, hud, kind, out):
    """Paint faction look F's `kind` frame; writes out_4.png (review) and out_2.png (ships).
    Returns (colour 4x, alpha 4x, EA's page)."""
    key, ea, a4, a2, x4, rings, ctx = sources(hud, F.side, kind)
    a4, a2 = a4.copy(), a2.copy()
    lum = x4 @ LUMA
    h = blur(lum, 2, 2) * F.orn_height
    mat = np.full(a4.shape, F.orn_mat, np.int16)
    emit = np.zeros(a4.shape + (3,), np.float32)
    alb = np.zeros(a4.shape + (3,), np.float32)
    aw = np.zeros(a4.shape, np.float32)
    wsum = np.zeros(a4.shape, np.float32)
    bands = [(n, ctx[n]) for n in ("portrait", "minimap") if n in ctx] + [("bar", BarCtx(a4.shape))]
    for name, c in bands:
        p = F.ring(c, name)
        w = c.weight
        h = h * (1 - w) + p.h * w
        mat = np.where(w > 0.5, p.mat, mat)
        emit = emit * (1 - w[..., None]) + p.emit * w[..., None]
        alb = alb * (1 - w[..., None]) + p.alb * w[..., None]
        aw = aw * (1 - w) + p.aw * w
        wsum = np.maximum(wsum, w)
    for rname, deg, R in F.medals:
        rg, c = rings[rname], ctx[rname]
        mid = 0.5 * (np.median(rg.r_in) + np.median(rg.r_out))
        cx = rg.cx + mid * np.cos(np.radians(deg))
        cy = rg.cy + mid * np.sin(np.radians(deg))
        res = F.medal(c.x - cx, -(c.yy - cy), R)
        hm, mm, cov, em = res[:4]
        h = h * (1 - cov) + hm * cov
        mat = np.where(cov > 0.5, mm, mat)
        emit = emit * (1 - cov[..., None]) + em * cov[..., None]
        ma, mw = res[4:6] if len(res) > 4 else (np.zeros_like(em), np.zeros_like(cov))
        alb = alb * (1 - cov[..., None]) + ma * cov[..., None]
        aw = aw * (1 - cov) + mw * cov
        wsum = np.maximum(wsum, cov)
    col, cav, n = shade(h, mat, F.mats, rim_col=F.rim_col, sky_col=F.sky_col, ground_col=F.ground_col,
                        alb=alb, aw=aw)
    c0 = ctx["minimap"]
    col = col * (1 + F.patina * (fbm(c0.x * 0.35, c0.yy * 0.35, 4, 6) - 0.5))[..., None]
    col = col + emit
    ow = ((1 - wsum) * F.orn_mix)[..., None]
    col = col * (1 - ow) + F.orn_colour(lum, x4) * ow
    env = dict(h=h, mat=mat, n=n, cav=cav, lum=lum, x4=x4, a4=a4, ring=wsum, ctx=ctx, emit=emit, bar=bands[-1][1],
               aw=aw)
    col = F.post(col, env)
    op = smoothstep(0.62, 0.93, a4)[..., None]
    col = np.clip(col * op + F.glass(x4, lum, a4, ctx) * (1 - op), 0, 1)
    pieces = getattr(F, "pieces", {}).get(kind)
    if pieces is not None:
        # the 3D ornaments (sagekit/hud/pieces.py) and their shadows, over the frame and past it, only
        # where safe(): outside both glasses, clear of the buttons and the numbers; feathered edges
        ok = blur(safe(ctx, getattr(F, "keep", None), getattr(F, "place", None)).astype(np.float32), K // 2, 2)
        pa = pieces[..., 3] * ok
        col = col * (1 - pa[..., None]) + pieces[..., :3] * pa[..., None]
        a4 = np.maximum(a4, pa)
        a2 = np.maximum(a2, downsample(pa, 2))
    save(out + "_4.png", np.concatenate([col, a4[..., None]], -1))
    save(out + "_2.png", np.concatenate([unsharp(downsample(col, 2), 0.3), a2[..., None]], -1))
    return col, a4, ea


def up2(img):
    """Bilinear 2x."""
    h, w = img.shape[:2]
    ys, xs = np.mgrid[:2 * h, :2 * w].astype(np.float32)
    return hudrings.bilinear(img, (xs + 0.5) / 2 - 0.5, (ys + 0.5) / 2 - 0.5)


def mockup(rgba4, ea, back_path, place, keep, out):
    """The frame (4x colour + alpha) over the screenshot where the game draws EA's frame. Where
    EA's alpha is partial (the glass vignette, the drop shadow) the screenshot already holds EA's
    frame blended in, so only the difference is added; where the screenshot shows something drawn
    above the frame (`keep`: the buttons, the portrait, the bar's numbers) it is kept."""
    back = load(back_path)[..., :3]
    pad = 40                                                # room above for accents past the frame's top
    strip = back[:pad, back.shape[1] // 2:][::-1]           # bare ground from the right half
    back = np.concatenate([np.tile(strip, (1, 3, 1))[:, :back.shape[1]], back], 0)
    oy_pad = pad
    S = 2                                                   # composite at 2x the screenshot
    big = up2(back)
    H, W = big.shape[:2]
    sx, sy, ox, oy = place
    oy = oy + oy_pad
    ours = draw((H, W), rgba4, sx * S / 4, sy * S / 4, ox * S, oy * S)
    theirs = draw((H, W), ea, sx * S, sy * S, ox * S, oy * S)
    a_o, a_e = ours[..., 3:4], theirs[..., 3:4]
    semi = big + a_e * (ours[..., :3] - theirs[..., :3])
    full = a_o * ours[..., :3] + (1 - a_o) * big
    w = np.clip((a_o - 0.82) / 0.13, 0, 1)
    canvas = w * full + (1 - w) * semi
    k = above((H, W), [(cx, cy + oy_pad, r) for cx, cy, r in keep["circles"]],
              [(l, t + oy_pad, r, b + oy_pad) for l, t, r, b in keep["rects"]], S)[..., None]
    canvas = canvas * (1 - k) + big * k
    res = np.clip(back + downsample(canvas - big, S), 0, 1)
    save(out, np.concatenate([res, np.ones(res.shape[:2] + (1,), np.float32)], -1))
