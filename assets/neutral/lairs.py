"""The creep lairs' story pieces (Blender side): what lives there, told in a few bold pieces at the
RTS camera, at the Goblin and Mordor kits' quality (their bones, skulls and spikes are the Goblin
kit's own, retagged for the neutral atlas: dress.py retag_base). Points are in world axes.

    larder(c, facing, s)            a troll's or warg's kill: a big ribcage, a skull pile, long bones
    trophy(base, h, s, facing)      a beast skull driven onto a stake
    club(p, q, r)                   a troll's club: a tapering log studded with iron spikes
    web(c, t, n, R)                 a spider's web hung in the plane (t, n): spokes and rings of strands
    cocoon(p, d, L, r)              a wrapped victim, a spindle of web
    eggs(c, r, count)               a clutch of egg sacs
    hoard(c, r, h)                  a dragon's hoard: a heap of gold, a chest, a sword, a shield
    menhir(c, h, w, lean)           a standing stone
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, box, loft

from assets.men.shapes import beam, turned

from .dress import retag_base


def _kit():
    from assets.goblins.shapes import GoblinShapes
    return GoblinShapes()


def larder(c, facing, s, skulls=5):
    k, c, f = _kit(), V(c), V(facing).normalized()
    side = V((-f.y, f.x, 0))
    out = k.ribcage(c + Z * s * 0.45, f, s, pairs=4)
    out += k.skull_pile(c - side * s * 0.9 + Z * 0.0, s * 0.45, skulls, s * 0.28, face=f)
    for i, (a, b) in enumerate(((-0.6, 0.9), (0.9, 0.2), (-1.1, -0.6))):
        p = c + side * s * a + f * s * b
        q = p + (side * math.cos(i * 2.1) + f * math.sin(i * 2.1)) * s * 0.9
        out += k.bone(p + Z * 0.35 * s * 0.12, q + Z * 0.35 * s * 0.12, s * 0.07)
    return retag_base(out, "x")


def trophy(base, h, s, facing=(1, 0, 0)):
    k = _kit()
    base = V(base)
    out = k.stake(base, base + Z * (h + 1.0), max(0.35, s * 0.12), tag="timber")
    out += k.horned_skull(base + Z * (h - 0.2 * s), V(facing), s, horn=1.4, detail=1)
    return retag_base(out, "x")


def club(p, q, r):
    k, p, q = _kit(), V(p), V(q)
    d = (q - p).normalized()
    out = [beam(p, q, r, "log|a", r * 1.6)]
    side = d.cross(Z).normalized() if d.cross(Z).length > 1e-3 else V((1, 0, 0))
    up = side.cross(d).normalized()
    for i in range(7):
        f = 0.55 + 0.42 * i / 6
        a = i * 2.4
        o = (side * math.cos(a) + up * math.sin(a))
        out += k.spike(p + (q - p) * f + o * r * 1.4 * (0.6 + f * 0.6), o, r * 1.4, r * 0.35)
    return retag_base(out, "x")


def web(c, t, n, R, spokes=8, rings=3, r=0.22):
    """Strands in the plane of t and n round c: `spokes` radii R long, `rings` rings of chords."""
    c, t, n = V(c), V(t).normalized(), V(n).normalized()
    out = []
    pts = lambda rr: [c + (t * math.cos(2 * math.pi * i / spokes) + n * math.sin(2 * math.pi * i / spokes)) * rr  # noqa: E731
                      for i in range(spokes)]
    for p in pts(R):
        out.append(beam(c, p, r, "web"))
    for j in range(1, rings + 1):
        ring = pts(R * j / (rings + 0.6))
        for a, b in zip(ring, ring[1:] + ring[:1]):
            out.append(beam(a, b, r * 0.8, "web"))
    return out


def cocoon(p, d, L, r):
    """A wrapped body L long along d from p: a spindle of web, banded."""
    p, d = V(p), V(d).normalized()
    side = d.cross(Z).normalized() if d.cross(Z).length > 1e-3 else V((1, 0, 0))
    up = side.cross(d).normalized()
    k = 8
    rings = []
    for f, rr in ((0.0, 0.25), (0.15, 0.8), (0.5, 1.0), (0.8, 0.75), (1.0, 0.2)):
        cc = p + d * L * f
        rings.append([cc + (side * math.cos(2 * math.pi * i / k) + up * math.sin(2 * math.pi * i / k)) * r * rr for i in range(k)])
    return [loft(rings, ["web"] * 4, cap0=("web", True), cap1=("web", True))]


def eggs(c, r, count, s=1.6, seed=1):
    c = V(c)
    out = []
    for i in range(count):
        a = i * 2.39996 + seed
        rr = r * math.sqrt((i + 0.5) / count)
        p = c + V((math.cos(a), math.sin(a), 0)) * rr
        e = s * (0.8 + 0.4 * ((i * 7 + seed) % 5) / 4)
        out.append(turned(p.x, p.y, [(e * 0.3, p.z), (e, p.z + e * 0.7), (e * 0.85, p.z + e * 1.5), (e * 0.2, p.z + e * 1.9)],
                          ["web", "web", "web"], 8, cap0=("web", False), cap1=("web", True)))
    return out


def hoard(c, r, h, facing=(1, 0, 0)):
    """A heap of gold r across and h high on c, a banded chest at its edge, a sword driven into it,
    a round shield leaning on it, and coins spilled round its foot."""
    c, f = V(c), V(facing).normalized()
    side = V((-f.y, f.x, 0))
    out = [turned(c.x, c.y, [(r, c.z - 0.03), (r * 0.8, c.z + h * 0.45), (r * 0.42, c.z + h * 0.85), (r * 0.1, c.z + h)],
                  ["gold", "gold", "gold"], 12, cap0=("gold", False), cap1=("gold", True))]
    for i in range(9):                                          # spilled coins
        a = i * 2.39996
        p = c + V((math.cos(a), math.sin(a), 0)) * r * (1.05 + 0.25 * (i % 3))
        out.append(turned(p.x, p.y, [(0.75, c.z - 0.03), (0.75, c.z + 0.3)], ["gold"], 8, cap0=("gold", False), cap1=("gold", True)))
    ch = c + f * r * 0.95 + side * r * 0.35                      # the chest
    out.append(box(ch.x - 1.8, ch.x + 1.8, ch.y - 1.3, ch.y + 1.3, c.z - 0.03, c.z + 2.4, "log", ("log", False), ("log", True)))
    out.append(box(ch.x - 1.9, ch.x + 1.9, ch.y - 1.4, ch.y + 1.4, c.z + 2.4, c.z + 3.1, "gold", ("gold", True), ("gold", True)))
    sw = c + Z * (h * 0.55) - side * r * 0.25                      # a sword driven in
    out.append(beam(sw, sw + Z * 6.5, 0.3, "iron", 0.0))
    out.append(beam(sw + Z * 4.8 - side * 1.3, sw + Z * 4.8 + side * 1.3, 0.28, "gold"))
    out.append(beam(sw + Z * 4.8, sw + Z * 6.6, 0.25, "log"))
    sh = c - f * r * 0.7 + Z * (h * 0.35 + 2.2)                        # a round shield leaning on the heap
    k = 10
    ring = lambda d0: [sh + (side * math.cos(2 * math.pi * i / k) + (Z * 0.8 - f * 0.6).normalized() * math.sin(2 * math.pi * i / k)) * 2.6  # noqa: E731
                       + f * d0 for i in range(k)]
    out.append(loft([ring(0.0), ring(-0.5)], ["gold"], cap0=("iron", True), cap1=("gold", True)))
    return out


def menhir(c, h, w, lean=(0.0, 0.0), seed=0):
    """A rough standing stone h tall, w across at its foot, narrowing and leaning a little."""
    c = V(c)
    top = c + V((lean[0], lean[1], 0)) * h + Z * h
    k = 5
    rings = []
    for f, rr in ((0.0, 1.0), (0.55, 0.85), (0.92, 0.55), (1.0, 0.18)):
        cc = c.lerp(top, f)
        ph = seed * 0.7 + f * 0.4
        rings.append([cc + V((math.cos(ph + 2 * math.pi * i / k), math.sin(ph + 2 * math.pi * i / k) * 0.7, 0)) * w / 2 * rr
                      for i in range(k)])
    return [loft(rings, ["rock"] * 3, cap0=("rock", False), cap1=("rock", True))]
