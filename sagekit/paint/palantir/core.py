"""The faction palantir painter's core (numpy; Blender's Python): noise, SDFs, metal shading, ring
coordinates. Everything is in 1x texture pixels, painted at K = 4 samples per pixel."""
import numpy as np

K = 4  # paint at 4x EA's pixels


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def box(img, r):
    if r <= 0:
        return img
    k = 2 * r + 1
    pad = np.pad(img, [(r, r), (r, r)] + [(0, 0)] * (img.ndim - 2), mode="edge")
    c = np.cumsum(np.cumsum(pad, 0), 1)
    c = np.pad(c, [(1, 0), (1, 0)] + [(0, 0)] * (img.ndim - 2))
    h, w = img.shape[:2]
    return (c[k:k + h, k:k + w] - c[:h, k:k + w] - c[k:k + h, :w] + c[:h, :w]) / (k * k)


def blur(img, r, n=3):
    for _ in range(n):
        img = box(img, r)
    return img


_RNG = np.random.default_rng(7)
_LAT = _RNG.random((8, 257, 257)).astype(np.float32)
_LAT[:, 256, :] = _LAT[:, 0, :]
_LAT[:, :, 256] = _LAT[:, :, 0]


def noise(x, y, seed=0):
    """Value noise, period 256, smooth."""
    L = _LAT[seed % 8]
    x = np.mod(x, 256.0)
    y = np.mod(y, 256.0)
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    return (L[y0, x0] * (1 - fx) * (1 - fy) + L[y0, x0 + 1] * fx * (1 - fy)
            + L[y0 + 1, x0] * (1 - fx) * fy + L[y0 + 1, x0 + 1] * fx * fy)


def fbm(x, y, octaves=4, seed=0):
    out = np.zeros_like(x, dtype=np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        out += amp * noise(x * (2 ** o), y * (2 ** o), seed + o)
        tot += amp
        amp *= 0.5
    return out / tot


def cells(x, y, seed=0):
    """Distance to nearest jittered point (worley F1, F2) on a unit grid."""
    xi, yi = np.floor(x), np.floor(y)
    f1 = np.full(x.shape, 9.0, np.float32)
    f2 = np.full(x.shape, 9.0, np.float32)
    L = _LAT[seed % 8]
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx, cy = xi + dx, yi + dy
            jx = L[np.mod(cy, 256).astype(int), np.mod(cx, 256).astype(int)]
            jy = L[np.mod(cy + 97, 256).astype(int), np.mod(cx + 31, 256).astype(int)]
            d = np.hypot(cx + jx - x, cy + jy - y)
            f2 = np.where(d < f1, f1, np.minimum(f2, d))
            f1 = np.minimum(f1, d)
    return f1, f2


# --- 2D SDFs (negative inside) ---------------------------------------------------------------

def sd_circle(x, y, r):
    return np.hypot(x, y) - r


def sd_box(x, y, hx, hy, r=0.0):
    qx, qy = np.abs(x) - hx + r, np.abs(y) - hy + r
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def sd_seg(x, y, ax, ay, bx, by, r):
    pax, pay, bax, bay = x - ax, y - ay, bx - ax, by - ay
    h = np.clip((pax * bax + pay * bay) / (bax * bax + bay * bay + 1e-9), 0, 1)
    return np.hypot(pax - bax * h, pay - bay * h) - r


def sd_star(x, y, r, n=5, inner=0.45, rot=-np.pi / 2):
    a = np.arctan2(y, x) - rot
    seg = 2 * np.pi / n
    a = np.mod(a + seg / 2, seg) - seg / 2
    rr = np.hypot(x, y)
    px, py = rr * np.cos(a), np.abs(rr * np.sin(a))
    # edge from tip (r,0) to valley (inner*r*cos(seg/2), inner*r*sin(seg/2))
    vx, vy = inner * r * np.cos(seg / 2), inner * r * np.sin(seg / 2)
    ex, ey = vx - r, vy
    h = np.clip(((px - r) * ex + py * ey) / (ex * ex + ey * ey), 0, 1)
    d = np.hypot(px - r - ex * h, py - ey * h)
    side = (px - r) * ey - py * ex
    return np.where(side < 0, -d, d) * 1.0


def sd_poly(x, y, pts):
    pts = np.asarray(pts, np.float32)
    d = np.full(x.shape, 1e9, np.float32)
    inside = np.zeros(x.shape, bool)
    n = len(pts)
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        d = np.minimum(d, sd_seg(x, y, ax, ay, bx, by, 0))
        cond = ((ay > y) != (by > y)) & (x < (bx - ax) * (y - ay) / (by - ay + 1e-9) + ax)
        inside ^= cond
    return np.where(inside, -d, d)


def fill(d, aa=0.35):
    """Coverage of an SDF in 1x px with ~1 4x-pixel antialiasing."""
    return np.clip(0.5 - d / aa, 0, 1)


def dome(d, r):
    """Rounded relief height (0..1) inside an SDF, reaching 1 at depth r."""
    return np.sqrt(np.clip(1 - (1 - np.clip(-d / r, 0, 1)) ** 2, 0, 1))


def half_round(u):
    u = np.clip(u, 0, 1) * 2 - 1
    return np.sqrt(np.clip(1 - u * u, 0, 1))


# --- shading ----------------------------------------------------------------------------------

def nrm(v):
    return v / np.linalg.norm(v)


class Mat:
    def __init__(self, albedo, metal=1.0, rough=0.3, edge=None, emit=None, aniso=0.0, clear=0.0, sss=None):
        self.albedo = np.array(albedo, np.float32)
        self.metal, self.rough = metal, rough
        self.edge = np.array(edge if edge is not None else np.minimum(self.albedo * 1.6 + 0.15, 1), np.float32)
        self.emit = np.array(emit if emit is not None else (0, 0, 0), np.float32)
        self.aniso = aniso
        self.clear = clear
        self.sss = np.array(sss, np.float32) if sss is not None else None


LIGHT = nrm(np.array([-0.5, -0.75, 0.62], np.float32))
RIM = nrm(np.array([0.65, 0.55, 0.5], np.float32))


def shade(h, mat, mats, k=K, rim_col=(0.6, 0.65, 0.75), ao_r=6, ao_gain=0.9, edge_gain=0.5,
          sky_col=(1.0, 0.97, 0.92), ground_col=(0.08, 0.07, 0.06)):
    """Shade a height field (1x px units) with per-pixel material indices."""
    gy, gx = np.gradient(h, 1.0 / k)
    n = np.stack([-gx, -gy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    nx, ny, nz = n[..., 0], n[..., 1], n[..., 2]
    rx, ry, rz = 2 * nz * nx, 2 * nz * ny, 2 * nz * nz - 1
    A = np.stack([m.albedo for m in mats])[mat]
    metal = np.array([m.metal for m in mats], np.float32)[mat]
    rough = np.array([m.rough for m in mats], np.float32)[mat]
    edgec = np.stack([m.edge for m in mats])[mat]
    emit = np.stack([m.emit for m in mats])[mat]
    up = -ry
    sky = 0.06 + 0.94 * smoothstep(-0.35, 0.9, up) ** 1.3
    sky *= 1 - 0.7 * np.exp(-((up - 0.12) / 0.14) ** 2) * (1 - rough)       # horizon line: chrome read
    sky += 0.25 * np.exp(-((up - 0.55) / 0.08) ** 2) * (1 - rough)           # a soft-box band above it
    sky = sky * (1 - 0.6 * rough) + 0.5 * 0.6 * rough
    key_d = rx * LIGHT[0] + ry * LIGHT[1] + rz * LIGHT[2]
    w = 0.012 + 0.22 * rough ** 2
    key = np.exp((key_d - 1) / w) * (0.6 + 1.6 / (1 + 12 * rough))
    rim_d = rx * RIM[0] + ry * RIM[1] + rz * RIM[2]
    rim = 0.45 * np.exp((rim_d - 1) / 0.09)
    diff = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    skyc = np.array(sky_col, np.float32)
    gnd = np.array(ground_col, np.float32)
    envc = sky[..., None] * skyc + (1 - sky[..., None]) * gnd
    fres = (1 - nz) ** 4
    met = A * (0.12 + 0.95 * envc) + key[..., None] * (0.55 * A + 0.45) + rim[..., None] * np.array(rim_col) * A * 1.4
    met += fres[..., None] * 0.25
    die = A * (0.22 + 0.85 * diff[..., None]) + (0.05 + 0.25 * (1 - rough))[..., None] * (
        key[..., None] * 0.6 + 0.15 * envc)
    m3 = metal[..., None]
    col = met * m3 + die * (1 - m3)
    # cavity and edges
    cav = np.clip((blur(h, ao_r // 3 + 1) - h) * ao_gain, 0, 1)
    col *= (1 - 0.7 * cav)[..., None]
    convex = np.clip((h - blur(h, 1, 2)) * 1.6, 0, 1)
    col += edge_gain * convex[..., None] * edgec * (0.4 + 0.6 * m3)
    col += emit
    return np.clip(col, 0, 1.5), cav, n


def downsample(img, k):
    h, w = img.shape[:2]
    return img.reshape(h // k, k, w // k, k, *img.shape[2:]).mean((1, 3))


def unsharp(img, amount, r=1):
    return np.clip(img + amount * (img - box(img, r)), 0, 1)


def ramp(stops, t):
    t = np.clip(t, 0, 1)
    xs = [s[0] for s in stops]
    return np.stack([np.interp(t, xs, [s[1][c] for s in stops]) for c in range(3)], -1).astype(np.float32)


# --- ring coordinates -------------------------------------------------------------------------

class RingCtx:
    """Per 4x pixel coordinates round a measured ring (sagekit.paint.hudrings.Ring)."""

    def __init__(self, ring, shape, k=K, which="inner"):
        h, w = shape
        ys, xs = np.mgrid[:h, :w].astype(np.float32)
        x, y = (xs + 0.5) / k - 0.5, (ys + 0.5) / k - 0.5
        dx, dy = x - ring.cx, y - ring.cy
        r = np.hypot(dx, dy)
        deg = np.degrees(np.arctan2(dy, dx)) % 360
        i0 = np.floor(deg).astype(int) % 360
        f = deg - np.floor(deg)
        r_in = ring.r_in[i0] * (1 - f) + ring.r_in[(i0 + 1) % 360] * f
        r_out = ring.r_out[i0] * (1 - f) + ring.r_out[(i0 + 1) % 360] * f
        self.r, self.deg, self.r_in, self.r_out = r, deg, r_in, r_out
        self.bw = r_out - r_in
        self.s = (r - r_in) / self.bw
        self.mid = 0.5 * (np.median(ring.r_in) + np.median(ring.r_out))
        self.C = 2 * np.pi * self.mid
        self.t = np.radians(deg) * self.mid
        self.y = self.s * np.median(self.bw)    # px across from inner edge
        ok = ring.inner if which == "inner" else ring.clean

        def circ(v, kk):
            pad = np.r_[v[-kk:], v, v[:kk]]
            c = np.cumsum(np.r_[0, pad])
            return (c[2 * kk + 1:] - c[:-2 * kk - 1]) / (2 * kk + 1)
        g = np.clip(circ(ok.astype(np.float32), 3) * 2 - 1, 0, 1)
        self.ang_w = g[i0] * (1 - f) + g[(i0 + 1) % 360] * f
        self.inside = smoothstep(-0.03, 0.02, self.s) * (1 - smoothstep(0.98, 1.03, self.s))
        self.weight = self.ang_w * self.inside
        self.ring = ring
        self.x, self.yy = x, y

    def cell(self, approx_px, offset=0.0):
        """Along-ring cell: (local x in px centred on the cell, cell index, cell length px)."""
        n = max(4, int(round(self.C / approx_px)))
        L = self.C / n
        tt = self.t + offset * L
        idx = np.floor(tt / L)
        return tt - (idx + 0.5) * L, idx.astype(int) % n, L

    def band(self, s0, s1):
        """u across [s0,s1] (0..1), the band's px width, and a mask."""
        u = (self.s - s0) / (s1 - s0)
        m = (self.s >= s0) & (self.s < s1)
        return u, (s1 - s0) * np.median(self.bw), m
