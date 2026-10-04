"""Recolouring a particle system: its Color keyframes moved onto a faction's ramp, every value kept.

A particle's colour is its texture times the Color module's keyframes (`ColorN = R:r G:g B:b frame`,
0-255, interpolated over the particle's age; EA's fire textures are grey, so the keyframes alone make
its flames orange). A tint replaces only those keyframes' r, g, b: each keeps its perceived
lightness (`lightness`: CIE L* corrected for the Helmholtz-Kohlrausch effect, so EA's saturated
blood-red War Chant and a pale cyan of ours read equally bright; plain luma made the cyan half as
bright), its frame, and the module's ColorScale; the hue comes from the faction's ramp at that
lightness (dark keys take the ramp's dark end, bright ones its bright end, as a fire runs from ember
to white-hot). Additive systems (EA's default) add their colour to the frame; alpha systems (smoke)
keep their darkness. A key brighter than the ramp's top is lifted toward white.

Nothing else in the block changes: lifetimes, sizes, rates, counts, emission, priority, shader and
texture are EA's, so a copy costs what EA's system costs.
"""
import math
import re

from . import blocks

KEY = re.compile(r"R:\s*(-?\d+)\s+G:\s*(-?\d+)\s+B:\s*(-?\d+)(\s+-?\d+(?:\.\d+)?)?")
W = (0.30, 0.59, 0.11)
WHITE = (0.95047, 1.0, 1.08883)


def luma(rgb):
    return sum(w * c for w, c in zip(W, rgb))


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _f(t):
    return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116


def lightness(rgb):
    """Perceived lightness of an sRGB colour (0-1 channels): CIE L* with the Helmholtz-Kohlrausch
    correction of Fairchild and Pirrotta (L** = L* + (2.5 - 0.025 L*)(0.116 |sin((h - 90)/2)| + 0.085) C*),
    so a saturated red and a pale cyan of equal L** read equally bright."""
    r, g, b = (_lin(c) for c in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / WHITE[0]
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / WHITE[2]
    lab_l = 116 * _f(y) - 16
    a, bb = 500 * (_f(x) - _f(y)), 200 * (_f(y) - _f(z))
    c, h = math.hypot(a, bb), math.atan2(bb, a)
    return lab_l + (2.5 - 0.025 * lab_l) * (0.116 * abs(math.sin((h - math.pi / 2) / 2)) + 0.085) * c


def _solve(fn, target, lo=0.0, hi=1.0):
    """t in [lo, hi] with fn(t) == target for a rising fn (bisection; the end it cannot pass)."""
    if fn(hi) <= target:
        return hi
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if fn(mid) < target else (lo, mid)
    return (lo + hi) / 2


class Ramp:
    """A faction ramp [(x, (r, g, b)) 0-1] read by perceived lightness; `chroma` scales its colour
    about the grey of the same lightness (1 = the ramp's own colour, 0 = grey)."""

    def __init__(self, stops, chroma=1.0, name=""):
        self.stops = sorted(((lightness(c), tuple(c)) for _, c in stops), key=lambda s: s[0])
        self.chroma = chroma
        self.name = name

    def hue_at(self, t):
        s = self.stops
        if t <= s[0][0]:
            return s[0][1]
        for (y0, c0), (y1, c1) in zip(s, s[1:]):
            if t <= y1:
                f = (t - y0) / (y1 - y0) if y1 > y0 else 0.0
                return tuple(a + (b - a) * f for a, b in zip(c0, c1))
        return s[-1][1]

    def colour(self, t):
        """The ramp's colour at perceived lightness t (0-100), exactly that lightness: the ramp's hue
        scaled, lifted toward white where scaling alone would clip."""
        if t <= 0.01:
            return (0.0, 0.0, 0.0)
        h = self.hue_at(t)
        if max(h) <= 0:
            h = (1.0, 1.0, 1.0)
        top = 1.0 / max(h)
        k = _solve(lambda s: lightness(tuple(v * s for v in h)), t, 0.0, top)
        c = tuple(v * k for v in h)
        if self.chroma != 1.0:
            g = _solve(lambda s: lightness((s, s, s)), t)
            grey = (g, g, g)
            c = tuple(gv + (v - gv) * self.chroma for v, gv in zip(c, grey))
            m = 1.0 / max(max(c), 1e-6)
            k = _solve(lambda s: lightness(tuple(v * s for v in c)), t, 0.0, m)
            c = tuple(v * k for v in c)
        if lightness(c) < t - 0.05:                      # clipped: lift toward white to the lightness
            u = _solve(lambda w: lightness(tuple(v + (1 - v) * w for v in c)), t)
            c = tuple(v + (1 - v) * u for v in c)
        return tuple(min(1.0, max(0.0, v)) for v in c)


def ramp_from(stops, chroma=1.0, name=""):
    return Ramp(stops, chroma, name)


def recolour(rgb255, ramp, tex=(1.0, 1.0, 1.0)):
    """(r, g, b) 0-255 -> our key, 0-255 integers: the colour seen (key times the texture's tint,
    textures.py) keeps its perceived lightness and takes the ramp's hue there; the tint is divided
    back out of the key (a channel the texture starves clips at 255)."""
    seen = [min(1.0, v / 255.0 * t) for v, t in zip(rgb255, tex)]
    c = ramp.colour(lightness(seen))
    return tuple(int(round(min(1.0, v / t if t > 0 else v) * 255)) for v, t in zip(c, tex))


def keyframes(rows):
    """[(key, (r, g, b), frame, row index)] of a particle system's Color module, and its ColorScale."""
    out, scale = [], None
    for name, fields in blocks.modules_of(rows):
        if name.split("=")[0].strip().lower() != "color":
            continue
        for k, v, i in fields:
            m = KEY.match(v)
            if re.match(r"Color\d+$", k) and m:
                out.append((k, tuple(int(m.group(j)) for j in (1, 2, 3)), float((m.group(4) or "0").strip()), i))
            elif k.lower() == "colorscale":
                scale = v
    return out, scale


def tinted(rows, new_name, ramp, rename_refs, why, tex=(1.0, 1.0, 1.0)):
    """The rows of EA's system (header to End) as our copy: renamed, its Color keys on `ramp`, its
    slave and per-particle systems renamed by rename_refs {EA name: ours}, a comment line first.
    EA's trailing comments are dropped from the rows we change only."""
    old = blocks.PS_HEAD.match(rows[0]).group(1)
    out = blocks.rename(rows, old, new_name)
    keys, _ = keyframes(rows)
    for key, rgb, frame, i in keys:
        r, g, b = recolour(rgb, ramp, tex)
        raw = blocks.drop_comment(out[i])
        m = KEY.search(raw)
        out[i] = raw[:m.start()] + "R:%d G:%d B:%d%s" % (r, g, b, m.group(4) or "") + raw[m.end():]
    for name, fields in blocks.modules_of(rows):
        for k, v, i in fields:
            if k in blocks.SYSTEM_REFS and v.split()[0] in rename_refs:
                out[i] = blocks.set_value(blocks.drop_comment(out[i]), rename_refs[v.split()[0]])
    nl = "\r\n" if rows[0].endswith("\r\n") else "\n"
    return ["; sagekit (sagekit/fx): %s%s" % (why, nl)] + out


def same_but_colour(ea_rows, our_rows, rename_refs):
    """Whether our copy (without its comment line) is EA's block but for the name, the Color keys'
    r, g, b and the renamed system references: the frame, every other field and every module as EA's."""
    ours = our_rows[1:] if our_rows and our_rows[0].lstrip().startswith(";") else our_rows
    if len(ours) != len(ea_rows):
        return False
    keys = {i for _, _, _, i in keyframes(ea_rows)[0]}
    refs = {i for _, f in blocks.modules_of(ea_rows) for k, v, i in f if k in blocks.SYSTEM_REFS}
    from ..formats.ini import strip
    for i, (a, b) in enumerate(zip(ea_rows, ours)):
        sa, sb = strip(a), strip(b)
        if i == 0:
            continue
        if i in keys:
            ma, mb = KEY.search(sa), KEY.search(sb)
            if not (ma and mb and sa[:ma.start()] == sb[:mb.start()] and (ma.group(4) or "") == (mb.group(4) or "")):
                return False
        elif i in refs:
            ka, va = (x.strip() for x in sa.split("=", 1))
            kb, vb = (x.strip() for x in sb.split("=", 1))
            if ka != kb or rename_refs.get(va.split()[0], va.split()[0]) != vb.split()[0]:
                return False
        elif sa != sb:
            return False
    return True
