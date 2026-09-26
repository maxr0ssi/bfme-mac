"""A faction's night-light texture, painted from its NightLook (pure Python, no Blender).

One small sheet of glow motifs in a 2 x 2 grid of cells, each with a black margin (the meshes are
drawn additively, so black is invisible and the margins keep mip levels from bleeding one motif
into the next):

    window   light from inside the stone behind a mullion and two transoms, brightest low down
    door     firelight spilling out of a doorway: bright at the threshold, fading upwards
    slit     a narrow vertical glow (arrow slits, loopholes)
    halo     a soft round spill of light on the stone round an opening (the N_GLOW meshes)

Intensity 0..1 is coloured by the look's ramp, so one faction's forge orange and another's cool
lamplight come from the same shapes. The motif's (s, t) run across the light and from its foot
(t = 0) to its head; sagekit/nightlights.py maps each light's outline onto its motif's cell.
"""
import math
import os
import subprocess

from ..formats.textures import MAGICK, write_dds_dxt1

CELLS = {"window": (0, 0), "door": (1, 0), "slit": (0, 1), "halo": (1, 1)}
MARGIN = 6 / 128                  # of a cell, black on every side


def smooth(e0, e1, x):
    x = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return x * x * (3 - 2 * x)


def edge(x, w):
    return smooth(0.0, w, x) * smooth(0.0, w, 1.0 - x)


def band(x, c, w):
    """1 at c, falling to 0 at c +- w (a bar's soft shadow)."""
    return max(0.0, 1.0 - abs(x - c) / w) ** 1.5


def intensity(kind, s, t):
    if kind == "window":
        bars = max(band(s, 0.5, 0.06), band(t, 0.36, 0.045), band(t, 0.68, 0.045))
        flicker = 1.0 + 0.05 * math.sin(11 * s + 3 * t) * math.sin(7 * t)
        return edge(s, 0.16) * edge(t, 0.10) * (0.62 + 0.38 * (1 - t) ** 1.2) * (1 - 0.62 * bars) * flicker
    if kind == "door":
        return edge(s, 0.14) * smooth(0.0, 0.03, t) * smooth(0.0, 0.30, 1 - t) * (0.32 + 0.68 * (1 - t) ** 1.6)
    if kind == "slit":
        return math.exp(-((s - 0.5) / 0.2) ** 2) * edge(t, 0.12) * (0.6 + 0.4 * (1 - t))
    if kind == "halo":
        r = math.hypot(2 * s - 1, 2 * t - 1)
        return 0.72 * (1 - smooth(0.0, 1.0, r)) ** 1.4
    raise ValueError("no night motif %r" % kind)


def colour(ramp, x):
    """The ramp [(intensity, (r, g, b))] at x (sRGB 0..1)."""
    if x <= ramp[0][0]:
        return ramp[0][1]
    for (a, ca), (b, cb) in zip(ramp, ramp[1:]):
        if x <= b:
            k = (x - a) / (b - a)
            return tuple(p + (q - p) * k for p, q in zip(ca, cb))
    return ramp[-1][1]


def paint(look, out_dds):
    """Write the look's texture as DXT1 with a full mip chain; returns the DDS path."""
    size = look.size
    cell = size // 2
    rows = bytearray()
    for y in range(size):
        for x in range(size):
            cx, cy = x // cell, y // cell
            kind = next(k for k, c in CELLS.items() if c == (cx, cy))
            s = ((x % cell) + 0.5) / cell
            t = 1.0 - ((y % cell) + 0.5) / cell          # rows top down; t = 0 at the light's foot
            s, t = (s - MARGIN) / (1 - 2 * MARGIN), (t - MARGIN) / (1 - 2 * MARGIN)
            v = intensity(kind, s, t) * look.gain.get(kind, 1.0) if 0 <= s <= 1 and 0 <= t <= 1 else 0.0
            rows += bytes(int(round(255 * min(1.0, max(0.0, c)))) for c in colour(look.ramp, v))
    os.makedirs(os.path.dirname(out_dds), exist_ok=True)
    ppm = out_dds[:-4] + ".ppm"
    with open(ppm, "wb") as fh:
        fh.write(b"P6\n%d %d\n255\n" % (size, size) + bytes(rows))
    png = out_dds[:-4] + ".png"
    subprocess.check_call([MAGICK, ppm, png])
    write_dds_dxt1(png, out_dds)
    os.remove(ppm)
    return out_dds


def uv(kind, s, t, size):
    """W3D texture coordinates of a point (s across, t up) of a motif. W3D's v runs up the image
    as the file stores it (EA's glow cards map EXGlow02's and gbnightwindows' bottom rows at v 0)."""
    cx, cy = CELLS[kind]
    s = MARGIN + min(1.0, max(0.0, s)) * (1 - 2 * MARGIN)
    t = MARGIN + min(1.0, max(0.0, t)) * (1 - 2 * MARGIN)
    return (cx + s) / 2, 1 - (cy + 1 - t) / 2


BLACK_UV = (0.5 * MARGIN / 2, 0.5 * MARGIN / 2)      # a texel in the black margin (stand-ins)
