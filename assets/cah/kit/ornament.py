"""Ornament for the CaH sheets, drawn as ImageMagick vector strokes into 256 px masks (white on
black) that paint.py bevels into the metal as inlay, engraving or raised rivets; plus the seeded
grain and scratch layers."""
import math
import random
import subprocess

S = 256


def magick(*a):
    subprocess.run(["magick", *map(str, a)], check=True)


def gray(path):
    return subprocess.check_output(["magick", str(path), "-depth", "8", "gray:-"])


def draw(work, name, cmds, width=3.0, blur=.7, fill=False):
    """A 256 x 256 stroke mask (white on black) from ImageMagick draw primitives."""
    p = work / ("orn_%s.png" % name)
    if not cmds:
        return bytes(S * S)
    args = ["-size", "%dx%d" % (S, S), "xc:black", "-stroke", "white", "-strokewidth", str(width),
            "-fill", "white" if fill else "none"]
    for c in cmds:
        args += ["-draw", c]
    magick(*args, "-blur", "0x%g" % blur, p)
    return gray(p)


def noise(work, seed, blur):
    p = work / ("noise_%d_%g.png" % (seed, blur))
    magick("-size", "%dx%d" % (S, S), "-seed", str(seed), "plasma:gray50-gray50", "-colorspace", "Gray",
           "-blur", "0x%g" % blur, "-normalize", p)
    return gray(p)


def scratches(work, seed, n=60):
    rng = random.Random(seed)
    cmds = []
    for _ in range(n):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        a, L = rng.uniform(0, math.pi), rng.uniform(8, 40)
        cmds.append("line %d,%d %d,%d" % (x, y, x + L * math.cos(a), y + L * math.sin(a)))
    return draw(work, "scr%d" % seed, cmds, width=1, blur=.4)


# ------------------------------------------------------------------ ornament
def runes(cells, seed, y0=70, y1=186):
    """Angular Cirth-like glyphs, one per cell along u: a stave and two or three branches."""
    rng = random.Random(seed)
    w = S / cells
    out = []
    for c in range(cells):
        x = w * c + w / 2
        out.append("line %d,%d %d,%d" % (x, y0, x, y1))
        for _ in range(rng.choice((2, 3))):
            ya = rng.uniform(y0, y1 - 30)
            d = rng.choice((-1, 1)) * w * .32
            out.append("line %d,%d %d,%d" % (x, ya, x + d, ya + rng.choice((22, 34, -22))))
    return out


def chevrons(n, y_mid, amp, x0=0, x1=S):
    w = (x1 - x0) / n
    pts = []
    for i in range(n + 1):
        pts += ["%d,%d" % (x0 + w * i, y_mid + (amp if i % 2 else -amp))]
    return ["polyline " + " ".join(pts)]


def border(inset=8):
    return ["rectangle %d,%d %d,%d" % (inset, inset, S - inset, S - inset)]


def rivets_row(y, n, r=5, x0=10, x1=S - 10):
    return ["circle %d,%d %d,%d" % (x0 + (x1 - x0) * i / (n - 1), y, x0 + (x1 - x0) * i / (n - 1) + r, y) for i in range(n)]


def device():
    """The Erebor device for the shield face (planar UVs, centre 128,128, rim radius 120): the
    Lonely Mountain's three peaks under a seven-pointed star, ringed by chevrons."""
    c = 128
    out = ["polyline 52,176 92,108 112,136 128,82 144,136 164,108 204,176 52,176",
           "polyline 92,108 100,124 112,136", "polyline 164,108 156,124 144,136",
           "line 128,82 128,176"]
    for k in range(7):
        a = -math.pi / 2 + 2 * math.pi * k / 7
        out.append("line %d,%d %d,%d" % (c, 58, c + 18 * math.cos(a), 58 + 18 * math.sin(a)))
    out.append("circle 128,128 128,30")
    for k in range(24):
        a0 = 2 * math.pi * k / 24
        a1 = 2 * math.pi * (k + .5) / 24
        a2 = 2 * math.pi * (k + 1) / 24
        p = lambda a, r: "%d,%d" % (c + r * math.cos(a), c + r * math.sin(a))
        out.append("polyline %s %s %s" % (p(a0, 104), p(a1, 112), p(a2, 104)))
    return out


def knot(n=3):
    """Interlaced diamonds along the blade (u along the haft)."""
    out = []
    w = S / n
    for i in range(n):
        x = w * i + w / 2
        out.append("polygon %d,%d %d,%d %d,%d %d,%d" % (x, 40, x + w * .42, 128, x, 216, x - w * .42, 128))
        out.append("polygon %d,%d %d,%d %d,%d %d,%d" % (x, 80, x + w * .25, 128, x, 176, x - w * .25, 128))
    out.append("line 0,24 %d,24" % S)
    return out


def tri_frieze(y0, y1, n):
    w = S / n
    return ["polygon %d,%d %d,%d %d,%d" % (w * i, y1, w * i + w / 2, y0, w * (i + 1), y1) for i in range(n)]


# ------------------------------------------------------------------ tiles


def heart(cx=128, cy=132, r=70):
    """A heart (planar shield face)."""
    pts = []
    for k in range(48):
        t = 2 * math.pi * k / 48
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append("%d,%d" % (cx + x * r / 17, cy - y * r / 17))
    return ["polygon " + " ".join(pts)]


def smiley():
    """A grinning face: two eyes and a wide smile (planar shield face, boss = nose)."""
    smile = " ".join("%d,%d" % (128 + 72 * math.cos(a), 140 + 60 * math.sin(a))
                     for a in [math.pi * (.15 + .7 * k / 20) for k in range(21)])
    return ["ellipse 96,92 13,22 0,360", "ellipse 160,92 13,22 0,360", "polyline " + smile]


def sparkles(seed, n=70):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        x, y, r = rng.uniform(8, 248), rng.uniform(8, 248), rng.uniform(1, 3.5)
        out.append("circle %d,%d %d,%d" % (x, y, x + r, y))
    return out


def scales(rows=10, cols=8):
    out = []
    for r in range(rows):
        for c in range(cols + 1):
            x = (c + (.5 if r % 2 else 0)) * S / cols
            y = r * S / rows
            out.append("arc %d,%d %d,%d 0,180" % (x - S / cols / 2, y - 10, x + S / cols / 2, y + S / rows))
    return out
