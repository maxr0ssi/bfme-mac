"""Vectorised building blocks for the painter: smoothstep, ramps, blurs, hashing and value noise."""
import numpy as np


def smooth(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def ramp(x, stops):
    """Piecewise-linear colour ramp: stops [(position, (r, g, b))] -> (..., 3)."""
    xs = np.array([s[0] for s in stops], np.float32)
    cs = np.array([s[1] for s in stops], np.float32)
    return np.stack([np.interp(x, xs, cs[:, c]) for c in range(3)], -1).astype(np.float32)


def roll_blur(x, r=1):
    """Separable box blur with wrap-around (np.roll), radius r."""
    for ax in (0, 1):
        acc = np.zeros_like(x)
        n = 0
        for d in range(-r, r + 1):
            acc += np.roll(x, d, axis=ax)
            n += 1
        x = acc / n
    return x


def box_blur(x, r):
    """Separable box blur with edge padding (cumulative sums), radius r."""
    for ax in (0, 1):
        pad = [(r + 1, r) if a == ax else (0, 0) for a in range(x.ndim)]
        c = np.cumsum(np.pad(x, pad, mode="edge"), axis=ax)
        hi, lo = [slice(None)] * x.ndim, [slice(None)] * x.ndim
        hi[ax], lo[ax] = slice(2 * r + 1, None), slice(0, -2 * r - 1)
        x = (c[tuple(hi)] - c[tuple(lo)]) / (2 * r + 1)
    return x


def hsv(a):
    mx, mn = a.max(-1), a.min(-1)
    c = mx - mn
    s = np.where(mx > 1e-6, c / np.maximum(mx, 1e-6), 0)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    cc = np.maximum(c, 1e-6)
    h = np.where(mx == r, ((g - b) / cc) % 6, np.where(mx == g, (b - r) / cc + 2, (r - g) / cc + 4)) * 60
    return np.where(c < 1e-6, 0, h), s, mx


def hash32(*ks):
    h = np.full(np.shape(ks[0]), 2166136261, np.uint32)
    for k in ks:
        k = np.asarray(k).astype(np.int64).astype(np.uint32)
        h = (h ^ k) * np.uint32(16777619)
        h ^= h >> np.uint32(13)
        h = h * np.uint32(0x5bd1e995)
        h ^= h >> np.uint32(15)
    return h


def hash01(*ks):
    return (hash32(*ks) & np.uint32(0xFFFFFF)).astype(np.float32) / float(0xFFFFFF)


def vnoise(p, seed=0):
    """3D value noise at points p (n, 3), already scaled."""
    i = np.floor(p).astype(np.int64)
    f = (p - i).astype(np.float32)
    f = f * f * (3 - 2 * f)
    out = np.zeros(len(p), np.float32)
    for dx in (0, 1):
        wx = f[:, 0] if dx else 1 - f[:, 0]
        for dy in (0, 1):
            wy = f[:, 1] if dy else 1 - f[:, 1]
            for dz in (0, 1):
                wz = f[:, 2] if dz else 1 - f[:, 2]
                out += wx * wy * wz * hash01(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, seed)
    return out


def fbm(p, octaves=4, seed=0):
    a, s, tot, out = 1.0, 1.0, 0.0, 0.0
    for o in range(octaves):
        out = out + a * vnoise(p * s, seed + o)
        tot += a
        a *= 0.5
        s *= 2.03
    return out / tot


def seg_dist(px, pz, a, b):
    """Distance from points (px, pz) to segment a-b."""
    (ax, az), (bx, bz) = a, b
    dx, dz = bx - ax, bz - az
    t = np.clip(((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz), 0, 1)
    return np.hypot(px - ax - t * dx, pz - az - t * dz)
