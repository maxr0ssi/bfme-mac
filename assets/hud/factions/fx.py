"""The faction palantirs' signatures over the citadel's materials (numpy): painted bloom round what
glows, a soft bloom on the brightest metal, four-point glints, flames and ice crystals.

All of it is painted into the frame's colour; the painter then puts EA's glass back wherever the
frame is not opaque, so a glow spills over the rim's edge at most, never onto the map."""
import numpy as np

from sagekit.paint.palantir.core import blur, fbm, noise, smoothstep

LUMA = np.array([0.299, 0.587, 0.114], np.float32)


def bloom(col, emit, a4, gain=1.0, radii=(3, 10)):
    """The glow of the emissive parts: a tight halo and a wide one, on the frame only."""
    g = sum(blur(emit, r, 2) for r in radii) / len(radii)
    return col + gain * g * np.clip(a4 * 1.2, 0, 1)[..., None]


def shine(col, a4, thresh=0.8, gain=0.6, r=4, tint=(1, 1, 1)):
    """Polished metal: its brightest highlights bloom a little."""
    hi = np.clip(col @ LUMA - thresh, 0, None)[..., None] * col
    return col + gain * blur(hi, r, 2) * np.array(tint, np.float32) * np.clip(a4, 0, 1)[..., None]


def glints(col, where, count, colour=(1, 1, 1), size=(8, 18), seed=3, strength=1.0):
    """Four-point star glints on `count` of the pixels in `where` (4x pixels; size: arm length)."""
    rng = np.random.default_rng(seed)
    ys, xs = np.where(where)
    if not len(xs):
        return col
    pick = rng.choice(len(xs), size=min(count, len(xs)), replace=False)
    gl = np.zeros(where.shape, np.float32)
    H, W = where.shape
    for i in pick:
        cy, cx = ys[i], xs[i]
        L = rng.uniform(*size)
        r = int(L) + 2
        y0, y1, x0, x1 = max(0, cy - r), min(H, cy + r + 1), max(0, cx - r), min(W, cx + r + 1)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        dx, dy = np.abs(xx - cx).astype(np.float32), np.abs(yy - cy).astype(np.float32)
        star = (np.exp(-dy / 0.8) * np.clip(1 - dx / L, 0, 1) ** 1.5 + np.exp(-dx / 0.8) * np.clip(1 - dy / L, 0, 1) ** 1.5
                + 0.45 * np.exp(-np.abs(dx - dy) / 0.7) * np.clip(1 - (dx + dy) / L, 0, 1) ** 2
                + 1.2 * np.exp(-(dx * dx + dy * dy) / 5.0))
        gl[y0:y1, x0:x1] = np.maximum(gl[y0:y1, x0:x1], star * rng.uniform(0.6, 1.0))
    return col + strength * gl[..., None] * np.array(colour, np.float32)


def heat(h, stops):
    """A flame's colour from its heat 0..1 (stops: [(t, rgb)], the edge first, the core last)."""
    xs = [s[0] for s in stops]
    h = np.clip(h, 0, 1)
    return np.stack([np.interp(h, xs, [s[1][c] for s in stops]) for c in range(3)], -1).astype(np.float32)


def flames(ctx, s0, s1, every, seed=0, lean=0.0):
    """Flame tongues rising outward from s0 over [s0, s1] of a ring: heat 0..1 (0 outside)."""
    u = (ctx.s - s0) / (s1 - s0)
    w = (s1 - s0) * float(np.median(ctx.bw))
    n = max(4, int(round(ctx.C / every)))
    L = ctx.C / n
    warp = (fbm(ctx.t * 0.22, u * 2.5 - 0.0, 3, seed) - 0.5) * 0.9 * L
    tt = ctx.t + warp * np.clip(u, 0, 1) + lean * u * w
    idx = np.floor(tt / L)
    lx = tt - (idx + 0.5) * L
    tall = 0.45 + 0.55 * noise(idx * 1.7 + 0.3, 0.5 + 0 * idx, seed + 1)
    v = np.clip(u / tall, 0, 1)
    half = 0.48 * L * (1 - v) ** 0.7 * (0.55 + 0.45 * np.sin(np.clip(v, 0, 1) * np.pi * 0.5 + 0.6))
    body = np.clip(1 - np.abs(lx) / np.maximum(half, 1e-3), 0, 1) * (u < tall) * (u > 0)
    core = body ** 1.5 * (1 - v) ** 0.6
    lick = 0.75 + 0.5 * fbm(ctx.t * 0.6, ctx.s * 9.0, 3, seed + 2)
    return np.clip(core * lick, 0, 1) * (u <= 1)


def ring_mask(env, lo=0.5):
    """Where a band of ours is drawn (not EA's ornament), opaque."""
    return (env["ring"] > lo) & (env["a4"] > 0.97)


# the frames' focal points (1x page px): the joint between the rings, the bar's end caps, the top
FOCUS = {"double": [(243, 48, 20), (30, 218, 14), (222, 218, 14), (128, 4, 26)],
         "single": [(30, 218, 14), (222, 218, 14), (128, 4, 26)]}


def focus(ctx):
    """0..1: how near a focal point, where the bold accents go."""
    x, y = ctx.x, ctx.yy
    kind = "double" if x.shape[1] > 300 * 4 else "single"
    f = np.zeros(x.shape, np.float32)
    for fx_, fy, sg in FOCUS[kind]:
        f = np.maximum(f, np.exp(-((x - fx_) ** 2 + (y - fy) ** 2) / (2 * sg * sg)))
    return f


def sparks(x, y, centres, count, radius, seed=5):
    """Embers or ice motes: small bright dots scattered round the given points (1x px)."""
    rng = np.random.default_rng(seed)
    out = np.zeros(x.shape, np.float32)
    for cx, cy in centres:
        for _ in range(count):
            px, py = cx + rng.normal(0, radius), cy + rng.normal(0, radius * 0.7)
            r = rng.uniform(0.25, 0.6)
            out = np.maximum(out, np.exp(-((x - px) ** 2 + (y - py) ** 2) / (2 * r * r)) * rng.uniform(0.5, 1))
    return out
