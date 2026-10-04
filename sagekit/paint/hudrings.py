"""The palantir's rings, measured on EA's frame and drawn again (numpy; Blender's Python).

EA's frames are hand-painted: the minimap ring and the portrait ring are not true circles (an
ellipse fit misses EA's edge by 1-2 pixels), so a ring is followed, not fitted. `measure()` walks
round EA's alpha from a centre and records, per degree, where the opaque metal starts and ends
(alpha >= 0.9: inside it the glass vignette fades in, outside the drop shadow fades out). The
centre is refined until the inner edge has no first harmonic. A degree is "clean" when the band
there is the ring's usual width; elsewhere something sits on the ring (the scroll joint, the
resource bar, a knot, Evil's spikes, the other ring), and EA's art is kept there.

Every ring of EA's has the same cross-section (all four frames, both rings): an inner lip, a bead,
a groove, a second bead, a groove, a broad band, the outer edge. `draw()` paints that cross-section
again at 4x the texture's pixels along the measured edges: a height field per band (the face's
`Look` says what each band is: polished bead, rope, engraved band, rivets...), lit as metal from
the top left, coloured by the look's ramps. Coordinates: 1x index space (pixel x's centre is x).
"""
import numpy as np

OPAQUE = 0.9


def bilinear(img, x, y):
    h, w = img.shape[:2]
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    if img.ndim == 3:
        fx, fy = fx[..., None], fy[..., None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def circular_smooth(v, k):
    """A ±k-degree moving average round a 360-entry circle."""
    pad = np.r_[v[-k:], v, v[:k]]
    c = np.cumsum(np.r_[0, pad])
    return (c[2 * k + 1:] - c[:-2 * k - 1]) / (2 * k + 1)


def fill_gaps(v, ok):
    """v with the entries where ok is False interpolated round the circle from their neighbours."""
    idx = np.arange(360)
    if ok.all():
        return v
    good = idx[ok]
    return np.interp(idx, np.r_[good - 360, good, good + 360], np.r_[v[ok], v[ok], v[ok]])


class Ring:
    """A measured ring: centre (1x index space), per-degree inner and outer edge, clean degrees."""

    def __init__(self, cx, cy, r_in, r_out, clean, inner, width):
        self.cx, self.cy = cx, cy
        self.r_in, self.r_out, self.clean, self.inner, self.width = r_in, r_out, clean, inner, width

    def describe(self):
        return "centre (%.2f, %.2f), radius %.1f-%.1f, band %.1f px; redrawn: whole band %d, beads %d of 360 degrees" % (
            self.cx, self.cy, np.median(self.r_in), np.median(self.r_out), self.width, self.clean.sum(),
            self.inner.sum())


def _edges(alpha, cx, cy, rlo, rhi):
    rs = np.arange(rlo, rhi, 0.1)
    t = np.radians(np.arange(360.0))[:, None]
    a = bilinear(alpha, cx + rs[None] * np.cos(t), cy + rs[None] * np.sin(t))
    r_in, r_out = np.full(360, np.nan), np.full(360, np.nan)
    for i in range(360):
        op = np.where(a[i] >= OPAQUE)[0]
        if len(op):
            runs = np.split(op, np.where(np.diff(op) != 1)[0] + 1)
            run = max(runs, key=len)
            r_in[i], r_out[i] = rs[run[0]], rs[run[-1]]
    return r_in, r_out


def _runs_shorter(ok, n_min):
    """ok with every True run shorter than n_min degrees set False (gaps between ornaments)."""
    out = ok.copy()
    for i in range(360):
        if ok[i] and not ok[i - 1]:
            n = 0
            while ok[(i + n) % 360] and n < 360:
                n += 1
            if n < n_min:
                out[[(i + k) % 360 for k in range(n)]] = False
    return out


def measure(alpha, centre, radii, tolerance=1.2):
    """The ring round `centre` whose metal lies between radii (lo, hi) on EA's alpha (1x).

    clean: the whole band is EA's usual band there (nothing on it, nothing growing out of it).
    inner: at least the beads are (a spike or knot grows from the broad band, the beads run on)."""
    cx, cy = centre
    t = np.radians(np.arange(360.0))
    for _ in range(4):
        r_in, r_out = _edges(alpha, cx, cy, *radii)
        width = r_out - r_in
        med = np.nanmedian(width)
        ok = np.abs(width - med) < tolerance
        # no first harmonic in the inner edge: the centre sits in the middle of the ring
        dx = 2 * np.mean((r_in[ok] - r_in[ok].mean()) * np.cos(t[ok]))
        dy = 2 * np.mean((r_in[ok] - r_in[ok].mean()) * np.sin(t[ok]))
        cx, cy = cx + dx, cy + dy
        if abs(dx) + abs(dy) < 0.02:
            break
    r_in, r_out = _edges(alpha, cx, cy, *radii)
    width = r_out - r_in
    med = float(np.nanmedian(width))
    # EA's hand-drawn band swells and thins round the ring: compare each degree with its own
    # neighbourhood (a spike or knot is a few degrees wide), and with the ring as a whole
    w = np.nan_to_num(width)
    local = np.array([np.median(np.take(w, range(i - 15, i + 16), mode="wrap")) for i in range(360)])
    full = (np.abs(w - local) < tolerance) & (np.abs(w - med) < 0.2 * med)
    smooth_in = circular_smooth(fill_gaps(np.nan_to_num(r_in), full), 3)
    steady = np.abs(np.nan_to_num(r_in) - smooth_in) < 1.0      # a knot moves the inner edge
    inner = steady & (np.nan_to_num(width) > 0.6 * med)
    full = _runs_shorter(full & steady, 6)
    inner = _runs_shorter(inner | full, 6)
    r_in = circular_smooth(fill_gaps(np.nan_to_num(r_in), inner), 2)
    # where something grows out of the band, its outer edge is where the band's usual width puts it
    r_out = circular_smooth(fill_gaps(np.nan_to_num(r_out), full), 2)
    r_out = np.where(full, r_out, r_in + med)
    r_out = circular_smooth(r_out, 2)
    return Ring(cx, cy, r_in, r_out, full, inner, med)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def bead(s, lo, hi):
    """A half-round bead's height (0..1) across s in [lo, hi]."""
    u = np.clip((s - lo) / (hi - lo), 0, 1) * 2 - 1
    return np.sqrt(np.clip(1 - u * u, 0, 1))


def ring_coords(ring, k, shape):
    """Per 4x pixel: s across the band (0 inner edge, 1 outer), the arc length t (1x px) at the
    band's middle, theta in degrees, and the band width (1x px)."""
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
    bw = r_out - r_in
    s = (r - r_in) / bw
    mid = 0.5 * (np.median(ring.r_in) + np.median(ring.r_out))
    t = np.radians(deg) * mid

    def blend(ok):
        """1 well inside the redrawn degrees, 0 outside them: the blend runs inside the redrawn side."""
        g = np.clip(circular_smooth(ok.astype(np.float32), 3) * 2 - 1, 0, 1)
        return g[i0] * (1 - f) + g[(i0 + 1) % 360] * f

    beads, whole = blend(ring.inner), blend(ring.clean)
    tr = smoothstep(0.53, 0.60, s)                     # the second groove is the seam
    weight = beads * (1 - tr) + whole * tr
    return s, t, deg, bw, np.clip(weight, 0, 1), mid


def periodic(t, period):
    """Phase in [0, 1) along the ring, with a whole number of periods round it."""
    return (t / period) % 1.0


def draw(ring, look, k, shape):
    """(height in 1x px, material index, band weight) of the ring at 4x. Materials index look.ramps."""
    s, t, deg, bw, weight, mid = ring_coords(ring, k, shape)
    b = look.bands
    bandw = (b["band"][1] - b["band"][0]) * ring.width
    n = max(8, int(round(2 * np.pi * mid / (look.period * bandw))))
    period = 2 * np.pi * mid / n                         # a whole number of motifs round the ring
    beadw = (b["bead2"][1] - b["bead2"][0]) * ring.width
    m = max(8, int(round(2 * np.pi * mid / (look.rope * beadw))))
    rope = 2 * np.pi * mid / m
    h = np.zeros(s.shape, np.float32)
    mat = np.zeros(s.shape, np.int8)
    # inner lip falls into the glass; outer edge rolls off into the shadow
    lip = smoothstep(0.0, b["bead1"][0], s) * 0.25
    h += lip
    # bead 1: the look's profile (Good: half-round and polished, Evil: a chamfered bar)
    one = (s >= b["bead1"][0]) & (s < b["bead1"][1])
    u1 = np.clip((s - b["bead1"][0]) / (b["bead1"][1] - b["bead1"][0]), 0, 1) * 2 - 1
    h = np.where(one, 0.25 + look.bead_height * look.bead1(u1), h)
    mat = np.where(one, look.mat["bead1"], mat)
    # groove floors
    for g in ("groove1", "groove2"):
        sel = (s >= b[g][0]) & (s < b[g][1])
        h = np.where(sel, 0.1, h)
        mat = np.where(sel, look.mat["groove"], mat)
    # bead 2: the look's (Good: a twisted rope, Evil: a notched blade edge); ph runs along the ring
    two = (s >= b["bead2"][0]) & (s < b["bead2"][1])
    u = np.clip((s - b["bead2"][0]) / (b["bead2"][1] - b["bead2"][0]), 0, 1)
    ph = periodic(t + look.twist * u * beadw, rope)
    h = np.where(two, 0.2 + look.bead_height * look.bead2(u * 2 - 1, ph), h)
    mat = np.where(two, look.mat["bead2"], mat)
    # broad band: slightly domed, with the look's engraving and rivets
    lo, hi = b["band"]
    band = (s >= lo) & (s < hi)
    v = np.clip((s - lo) / (hi - lo), 0, 1)
    dome = 0.55 + 0.35 * bead(s, lo - 0.1, hi + 0.1)
    p = periodic(t, period)
    engr, studs = look.engrave(p, v, period, bandw)
    hb = dome - look.engrave_depth * engr
    hb = np.maximum(hb, studs * look.rivet_height + dome * (studs > 0))
    edge = 1 - smoothstep(hi - 0.06, 1.0, s)              # the outer roll-off
    hb = hb * np.where(s > hi - 0.06, edge, 1.0)
    h = np.where(band, hb, h)
    mat = np.where(band, look.mat["band"], mat)
    mat = np.where(band & (studs > 0.05), look.mat["rivet"], mat)
    mat = np.where(band & (engr > 0.5), look.mat["engraved"], mat)
    out = s >= hi
    h = np.where(out, 0.55 * (1 - smoothstep(hi, 1.02, s)), h)
    mat = np.where(out, look.mat["band"], mat)
    inside = smoothstep(-0.02, 0.02, s) * (1 - smoothstep(1.0, 1.04, s))
    return h * look.height_px, mat, weight * inside, s


def light(h, k, look):
    """Shade (0..1 ramp position) and a specular term of a height field at k x."""
    gy, gx = np.gradient(h, 1.0 / k)
    nrm = np.stack([-gx, -gy, np.ones_like(h)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    L = np.array(look.light, np.float32)
    L /= np.linalg.norm(L)
    H = L + np.array([0, 0, 1], np.float32)
    H /= np.linalg.norm(H)
    diff = np.clip(nrm @ L, 0, 1)
    env = 0.5 - 0.5 * nrm[..., 1]                       # faces turned up catch the sky
    spec = np.clip(nrm @ H, 0, 1) ** look.shininess
    flat = nrm[..., 2] ** 8                              # a face square to the eye: the metal's own tone
    shade = look.ambient + look.diffuse * diff + look.env * env - 0.08 * (1 - flat)
    return np.clip(shade, 0, 1), spec
