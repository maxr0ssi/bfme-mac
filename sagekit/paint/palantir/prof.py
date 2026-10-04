"""Cross-section building blocks for the faction palantirs' rings, bar rails and sockets (numpy)."""
import numpy as np

from .core import (cells, dome, fbm, fill, half_round, noise, sd_box, sd_circle, sd_poly, sd_seg,
                  sd_star, smoothstep)


class P:
    def __init__(self, ctx):
        self.ctx = ctx
        shp = ctx.s.shape
        self.h = np.zeros(shp, np.float32)
        self.mat = np.zeros(shp, np.int16)
        self.emit = np.zeros(shp + (3,), np.float32)

    def put(self, mask, h, mat):
        self.h = np.where(mask, h, self.h)
        self.mat = np.where(mask, mat, self.mat)

    def over(self, cov, h, mat, thresh=0.5):
        """Blend a relief on top with coverage cov (0..1)."""
        self.h = self.h * (1 - cov) + h * cov
        if np.isscalar(mat):
            self.mat = np.where(cov > thresh, mat, self.mat)
        else:
            self.mat = np.where(cov > thresh, mat, self.mat)

    def glow(self, amount, colour):
        self.emit += amount[..., None] * np.array(colour, np.float32)


def band(ctx, s0, s1):
    u = (ctx.s - s0) / (s1 - s0)
    m = (ctx.s >= s0) & (ctx.s < s1)
    w = (s1 - s0) * float(np.median(ctx.bw))
    return u, w, m


def lip(p, s1, mat, top=0.35):
    u, w, m = band(p.ctx, -0.1, s1)
    p.put(m, top * smoothstep(0, 1, u), mat)


def bead(p, s0, s1, mat, height=1.3, base=0.3):
    u, w, m = band(p.ctx, s0, s1)
    p.put(m, base + height * half_round(u), mat)


def chamfer(p, s0, s1, mat, height=1.3, base=0.3, flat=0.4):
    u, w, m = band(p.ctx, s0, s1)
    e = np.minimum(u, 1 - u) / max(1e-3, (1 - flat) / 2)
    p.put(m, base + height * np.clip(e, 0, 1), mat)


def groove(p, s0, s1, mat, depth=0.05):
    u, w, m = band(p.ctx, s0, s1)
    p.put(m, depth + 0.1 * half_round(u), mat)


def rope(p, s0, s1, mat, height=1.2, base=0.3, strands=1.3, twist=1.2):
    ctx = p.ctx
    u, w, m = band(ctx, s0, s1)
    n = max(8, int(round(ctx.C / (strands * w))))
    L = ctx.C / n
    ph = ((ctx.t + twist * u * w) / L) % 1.0
    strand = np.sqrt(np.clip(1 - (2 * ph - 1) ** 2, 0, 1))
    hh = base + height * half_round(u) * (0.55 + 0.45 * strand)
    p.put(m, hh, mat)


def pearls(p, s0, s1, mat, height=1.2, base=0.25, spacing=1.15):
    ctx = p.ctx
    u, w, m = band(ctx, s0, s1)
    lx, idx, L = ctx.cell(w * spacing)
    d = np.hypot(lx, (u - 0.5) * w)
    hh = base + height * np.sqrt(np.clip(1 - (d / (0.5 * w)) ** 2, 0, 1))
    p.put(m, np.where(d < 0.5 * w, hh, base * 0.4), mat)


def saw(p, s0, s1, mat, height=1.3, base=0.2, spacing=1.0, lean=0.35, outward=True):
    """Sawtooth blades: each tooth a ramp along the ring, its cut a sharp drop."""
    ctx = p.ctx
    u, w, m = band(ctx, s0, s1)
    lx, idx, L = ctx.cell(w * spacing)
    ph = lx / L + 0.5
    v = u if outward else 1 - u
    ramp_ = np.clip(ph + lean * (v - 0.5), 0, 1)
    hh = base + height * ramp_ * (0.55 + 0.45 * half_round(u))
    p.put(m, hh, mat)


def flat(p, s0, s1, mat, height=0.9, crown=0.2):
    u, w, m = band(p.ctx, s0, s1)
    p.put(m, height + crown * half_round(u), mat)
    return u, w, m


def hammer(p, amount, scale=1.0, seed=0, mask=None):
    ctx = p.ctx
    n = fbm(ctx.t * 0.9 / scale, ctx.y * 0.9 / scale, 3, seed) - 0.5
    d = amount * n
    p.h = p.h + (d if mask is None else d * mask)


def turned(p, amount, mask=None):
    """Fine lathe marks across the band (along the ring)."""
    ctx = p.ctx
    n = noise(ctx.t * 0.05, ctx.y * 6.0, 3) - 0.5
    p.h = p.h + amount * n * (1 if mask is None else mask)


def local(ctx, u, w, approx, offset=0.0):
    """Cell-local coordinates in px: lx along (centred), ly across (outward +), cell index."""
    lx, idx, L = ctx.cell(approx, offset)
    ly = (u - 0.5) * w
    return lx, ly, idx, L


def wobble(ctx, amp, seed=1):
    """Hand-made irregularity: shift s by a slow noise."""
    return amp * (noise(ctx.t * 0.08, 0.0 * ctx.t, seed) - 0.5)


# ---- glyphs ----------------------------------------------------------------------------------

RUNES = [  # Cirth-like strokes in a unit cell (x across -0.5..0.5, y -0.5..0.5, + outward)
    [((0, -0.5), (0, 0.5)), ((0, 0.5), (0.35, 0.15))],
    [((0, -0.5), (0, 0.5)), ((0, 0.1), (0.35, 0.45)), ((0, 0.1), (-0.35, 0.45))],
    [((-0.2, -0.5), (-0.2, 0.5)), ((0.2, -0.5), (0.2, 0.5)), ((-0.2, 0.5), (0.2, 0.1))],
    [((0, -0.5), (0, 0.5)), ((0, 0.5), (0.35, 0.15)), ((0, 0.0), (0.35, -0.35))],
    [((0, -0.5), (0, 0.5)), ((-0.35, 0.15), (0, 0.5)), ((0, 0.5), (0.35, 0.15))],
    [((-0.25, -0.5), (0.25, 0.5)), ((0.25, -0.5), (-0.25, 0.5))],
    [((0, -0.5), (0, 0.5)), ((0, -0.1), (0.35, 0.25)), ((0, -0.1), (0.35, -0.45))],
    [((-0.2, -0.5), (-0.2, 0.5)), ((0.2, -0.5), (0.2, 0.5)), ((-0.2, 0.0), (0.2, 0.0))],
]


def rune(lx, ly, idx, size, stroke):
    """SDF of rune idx (array) scaled to size px."""
    d = np.full(lx.shape, 1e9, np.float32)
    for gi, strokes in enumerate(RUNES):
        sel = (idx % len(RUNES)) == gi
        if not sel.any():
            continue
        dd = np.full(lx.shape, 1e9, np.float32)
        for (ax, ay), (bx, by) in strokes:
            dd = np.minimum(dd, sd_seg(lx, ly, ax * size, ay * size, bx * size, by * size, stroke))
        d = np.where(sel, dd, d)
    return d


def white_hand(x, y, s):
    """SDF of a raised open hand (fingers outward/+y), height s px."""
    k = s / 10.0
    palm = sd_box(x, y + 1.0 * k, 2.4 * k, 2.4 * k, 1.4 * k)
    d = palm
    for fx, top in ((-1.8, 3.8), (-0.6, 4.9), (0.6, 5.1), (1.8, 4.3)):
        d = np.minimum(d, sd_seg(x, y, fx * k, 0.0, fx * k, top * k, 0.55 * k))
    d = np.minimum(d, sd_seg(x, y, -2.6 * k, -1.5 * k, -4.2 * k, 0.8 * k, 0.6 * k))
    return d


def skull(x, y, s):
    """(sdf of the skull, sdf of its holes) height s px, crown outward (+y)."""
    k = s / 10.0
    cran = sd_circle(x / 1.0, y - 1.2 * k, 3.6 * k)
    jaw = sd_box(x, y + 2.6 * k, 2.2 * k, 1.6 * k, 0.8 * k)
    body = np.minimum(cran, jaw)
    eyes = np.minimum(sd_circle(x - 1.35 * k, y - 0.7 * k, 1.05 * k), sd_circle(x + 1.35 * k, y - 0.7 * k, 1.05 * k))
    nose = sd_poly(x, y, [(0, -1.1 * k), (-0.55 * k, -2.0 * k), (0.55 * k, -2.0 * k)])
    teeth = np.full(x.shape, 1e9, np.float32)
    for tx in (-1.2, -0.4, 0.4, 1.2):
        teeth = np.minimum(teeth, sd_box(x - tx * k, y + 3.3 * k, 0.12 * k, 0.75 * k))
    return body, np.minimum(np.minimum(eyes, nose), teeth)


def leaf(x, y, length, width, angle):
    c, s_ = np.cos(angle), np.sin(angle)
    lx, ly = c * x + s_ * y, -s_ * x + c * y
    a, b = length / 2, width / 2
    # pointed ellipse: shrink width toward the tips
    taper = np.clip(1 - (lx / a) ** 2, 0, 1)
    d = np.abs(ly) - b * np.sqrt(taper) * (1 - 0.25 * (lx / a) ** 2)
    d = np.where(np.abs(lx) > a, np.hypot(np.abs(lx) - a, ly), d)
    return d, lx, ly


def crystal(x, y, length, width, angle=0.0):
    """Elongated hexagonal crystal SDF (pointed both ends), and its facet coordinates."""
    c, s_ = np.cos(angle), np.sin(angle)
    lx, ly = c * x + s_ * y, -s_ * x + c * y
    a, b = length / 2, width / 2
    d = np.maximum(np.abs(ly) - b, (np.abs(lx) + np.abs(ly) - a) / np.sqrt(2))
    return d, lx, ly
