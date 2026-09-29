"""The warg sentry (Blender side), IBWARGSENT mesh coordinates (identity bone). EA's den (probed
2026-09-29): a trodden disc of earth r ~50 at z 0..1, rocks, tusks and stakes round its rim, a
great ribcage on its +X side (x 30..52, y -12..38, to z 32.7). Three wargs spawn here and roam the
middle (UnitCreatePoint (10, 0), rally (20, -20)): nothing new inside r 38.

Isengard's kennel, on the rim where EA's collision boxes stand ((-40, 25), (0, 45), (-15, -45),
(35, -45)): an iron-banded palisade of sharpened stakes along the back rim, iron-capped warg posts
with a collar ring and a chain trailing in, sharpened stakes with iron tips in three clusters, the White Hand on an Uruk shield raised on a post, a fire pit
under an iron grate and two tall braziers by the way out to the rally point (real fire)."""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z

POSTS = [(0.0, 45.5), (-15.0, -45.5), (35.0, -44.0), (-47.0, -8.0)]
STAKES = [(-48.0, 4.0), (-43.0, -24.0), (18.0, -47.0)]
BRAZIERS = [(40.0, -30.0), (46.0, -14.0)]
PIT = (-30.0, -34.0)
STANDARD = (-21.0, 44.0)


def post(kit, x, y):
    """A warg post: a timber stake with an iron cap and spike, an iron collar ring, a chain trailing in."""
    c = V((x, y, 0))
    inward = (-c).normalized()
    out = [kit.beam(c + Z * 0.3, c + Z * 11.0, 1.0, "timber")]
    out.append(kit.beam(c + Z * 10.0, c + Z * 12.0, 1.25, "iron"))
    out.append(kit.beam(c + Z * 12.0, c + Z * 15.5, 0.8, "trim", 0.0))
    out += kit.hoop((x, y), 3.2, 1.05, h=0.8, th=0.35, inner=0.4, k=6, rivets=False, closed=True)
    ring = c + Z * 3.2 + inward * 1.4
    out += kit.chain(ring, c + inward * 7.0 + Z * 0.5, link=1.3)
    return out


def stakes(kit, x, y):
    """Four sharpened timber stakes leaning out of the rim, iron tips."""
    c = V((x, y, 0))
    out_dir = c.normalized()
    t = V((-out_dir.y, out_dir.x, 0))
    out = []
    for i, u in enumerate((-3.0, -1.0, 1.0, 3.0)):
        base = c + t * u + Z * 0.6
        top = base + (out_dir * 0.45 + Z).normalized() * (7.5 + 1.5 * math.sin(i * 2.3))
        out.append(kit.beam(base, top, 0.5, "timber"))
        d = (top - base).normalized()
        out.append(kit.beam(top, top + d * 2.2, 0.5, "iron", 0.0))
    out.append(kit.beam(c + t * -3.6 + Z * 2.5, c + t * 3.6 + Z * 2.5, 0.3, "iron"))
    return out


def standard(kit, x, y):
    """The White Hand on an Uruk shield raised on an iron-shod post, facing the den."""
    c = V((x, y, 0))
    n = (-c).normalized()
    t = V((-n.y, n.x, 0))
    out = [kit.beam(c + Z * 0.3, c + Z * 16.0, 0.6, "timber"), kit.beam(c + Z * 16.0, c + Z * 19.5, 0.5, "trim", 0.0)]
    out += kit.shield(c + n * 0.6, t, n, 0.0, 8.5, 7.0, d=0.0)
    return out


def palisade(kit, deg0=118.0, deg1=164.0, r=47.5, n=17):
    """A palisade arc on the back rim (EA's collision box at (-40, 25)): sharpened timber stakes
    8..11 tall with iron tips, leaning out, two riveted iron bands along them, a pointed iron cap
    on every fourth."""
    out = []
    pts = []
    for i in range(n):
        a = math.radians(deg0 + (deg1 - deg0) * i / (n - 1))
        d = V((math.cos(a), math.sin(a), 0))
        base = d * (r + 0.4 * math.sin(i * 1.7)) + Z * 0.5
        h = 8.5 + 2.5 * (0.5 + 0.5 * math.sin(i * 2.1))
        top = base + (d * 0.18 + Z).normalized() * h
        out.append(kit.beam(base, top, 0.85, "timber"))
        out.append(kit.beam(top, top + (d * 0.18 + Z).normalized() * (2.4 if i % 4 else 3.6), 0.85, "iron", 0.0))
        pts.append((base, d))
    for z in (2.6, 6.2):
        for (b0, d0), (b1, d1) in zip(pts, pts[1:]):
            out.append(kit.beam(b0 + d0 * (0.9 + z * 0.18) + Z * z, b1 + d1 * (0.9 + z * 0.18) + Z * z, 0.3, "iron"))
    return out


def build(kit):
    out = []
    for x, y in POSTS:
        out += post(kit, x, y)
    for x, y in STAKES:
        out += stakes(kit, x, y)
    for x, y in BRAZIERS:
        out += kit.brazier(V((x, y, 0.4)), 2.0, 8.0)
    out += kit.floor_grate(V((PIT[0], PIT[1], 0.7)), V((0.7, -0.7, 0)), 4.0, 4.0)
    kit.fire(V((PIT[0], PIT[1], 1.2)), "grate")
    out += standard(kit, *STANDARD)
    return out + palisade(kit)
