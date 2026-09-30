"""The Mordor add-ons' shared pieces (Blender side): the citadel's upgrades (fire arrows, magma
cauldrons, the Gorgoroth spire, the lava moat) and its expansions (barricade, gate watchers, wall
catapult). Functions of the Mordor kit (`kit`, shapes.py), so the kit's own signatures stay
untouched; the citadel's own modules (assets/mordor/fortress/) are read, never changed.

The citadel's language, carried to every add-on: claws of jagged, hooked spikes rising from
INSIDE a bowl or crown and closing round a real fire (the citadel's crowns, fortress/crown.py),
glowing lava at the wall feet and in seams, steel only on blade edges, the Eye. Green only on the
Watchers' eyes (Morgul sorcery: the one accent).

    claw(kit, c, z0, spikes, ...)       spikes of the citadel's crowns, any size: each (deg, r0, h,
                                        rt) rises at `deg` round c from r0 at z0 to its tip rt from
                                        the axis h higher, leaning in; a Horn with a steel outer edge,
                                        teeth hooking up, a hook down, a lava seam on the tall ones
    ring(n, rot, r0, h, rt, short)      the crowns' pattern: n spikes, every other one `short` as tall
    leg_barb(kit, p, q, f, out, L)      a hooked barb off a leg (p to q) at f of its length, along out
    plane(a, t, n, bat), cylinder(c, r, a0)   surfaces for the cracks: (u, z) -> (point, normal)
    fissure(kit, P, u0, z0, h, ...)     a crack glowing from within (pass 2: the pass 1 cracks read as
                                        painted flames): a jagged line of short straight runs kinking
                                        left and right, widest at its root, tapering to a point, with
                                        forks veering off; each run an ember core in a dark lip
    runnel(kit, P, u, z0, z1, w)        lava pouring down a face: a narrow, straight, kinked fissure of
                                        even width, no forks
    witch_eye(kit, p, fwd, side, ...)   a small almond of Morgul witch-light on a face (tag "witch")
    arch_teeth(kit, x0, x1, y, z, ...)  a raised portcullis in an expansion's wall arch (both faces)

Coordinates are each add-on's own mesh coordinates (the citadel's for the upgrades).
"""
import math

from mathutils import Vector as V

from .fortress.crown import seam

Z = V((0, 0, 1))

# the citadel's crown spikes as fractions: (height, radius) keys, the section at each key, the tip
# (a key's height as a fraction of the spike's, how far its radius has gone from r0 toward the tip's)
TALL = ([(-0.02, 0.0), (0.434, 0.061), (0.70, 0.334), (0.87, 0.698)],
        [(1.2, 1.0, 0.9), (1.1, 0.9, 0.8), (0.8, 0.7, 0.6), (0.5, 0.45, 0.4)])
SHORT = ([(-0.02, 0.0), (0.553, 0.137), (0.842, 0.546)],
         [(0.9, 0.8, 0.7), (0.7, 0.6, 0.55), (0.4, 0.35, 0.3)])


def ring(n=8, rot=22.5, r0=7.5, h=26.0, rt=None, short=0.72):
    """The crowns' pattern: n spikes from `rot` degrees, every other one `short` of the height."""
    rt = 0.56 * r0 if rt is None else rt
    return [(rot + 360.0 * k / n, r0, h if k % 2 == 0 else h * short, rt if k % 2 == 0 else rt * 1.25)
            for k in range(n)]


def claw(kit, c, z0, spikes, w=1.0, tall_at=None, seams=True, outer="steel", inner=True):
    """Spikes rising round c from z0: each (deg, r0, h, rt) from r0 out of the axis up to its tip
    rt from it, h above z0 (a spike at least `tall_at` tall - default the tallest's 0.9 - takes the
    tall profile, teeth, hook and a lava seam). w scales the section (1.0: the citadel's corner
    crowns, 26 tall). inner=False: no teeth on the inner edge (a claw that must keep clear inside)."""
    c = V((c[0], c[1], 0))
    hmax = max(s[2] for s in spikes)
    tall_at = hmax * 0.9 if tall_at is None else tall_at
    out = []
    for deg, r0, h, rt in spikes:
        tall = h >= tall_at
        keys, secs = TALL if tall else SHORT
        a = math.radians(deg)
        e = V((math.cos(a), math.sin(a), 0))
        f = V((-e.y, e.x, 0))
        kz = [(z0 + h * fz, c + e * (r0 + (rt - r0) * g)) for fz, g in keys]
        horn = kit.Horn([(z, tuple(p[:2]), tuple(x * w for x in sec)) for (z, p), sec in zip(kz, secs)], e, f,
                        c + e * rt + Z * (z0 + h))
        s = h / 26.0
        if tall:
            teeth, hooks = [(z0 + h * 0.51, 0.6), (z0 + h * 0.70, 0.6)], [(z0 + h * 0.62, 0.35)]
        else:
            teeth, hooks = [(z0 + h * 0.66, 0.5)], [(z0 + h * 0.71, 0.3)]
        if s < 0.7:                                          # small spikes: one tooth, one hook
            teeth, hooks = teeth[:1], hooks
        out += kit.horn(horn, teeth=teeth if inner else (), hooks=hooks, outer=outer, edge="stoneB", tag="stoneA")
        if tall and seams:
            out += seam(kit, horn, z0 + h * 0.12, z0 + h * 0.77)
    return out


def leg_barb(kit, p, q, f, out, length, r=0.35):
    """A hooked barb off a leg from p to q at f of its length, along `out` (tipped up)."""
    p, q = V(p), V(q)
    b = p.lerp(q, f)
    d = V(out).normalized()
    return kit.barb(b - d * 0.2, (d + Z * 0.25).normalized(), length, r)


def plane(a, t, n, bat=0.0):
    """A face (a, t, n) as a surface for fissures: (u, z) -> (point, outward normal); bat: the face
    leans back this much per unit of height (EA's battered walls)."""
    a, t, n = V((a[0], a[1], 0)), V(t), V(n)
    return lambda u, z: (a + t * u + Z * z - n * (bat * z), n)


def cylinder(c, r, a0):
    """A round surface (radius r about the vertical axis at c) for fissures: u runs round it from
    the angle a0 (degrees) as arc length."""
    c = V((c[0], c[1], 0))

    def P(u, z):
        a = math.radians(a0) + u / r
        n = V((math.cos(a), math.sin(a), 0))
        return c + n * r + Z * z, n
    return P


def _hash(x):
    return (math.sin(x * 12.9898 + 4.1) * 43758.5453) % 1.0


def strand(kit, P, pts, ws, depth=0.2, core="ember"):
    """Straight runs through (u, z) points on the surface P, each run an ember core (proud `depth`)
    in a wider dark lip of soot (proud half that): closed solids, the backs buried 0.4."""
    out = []
    for (u0, z0), (u1, z1), w0, w1 in zip(pts, pts[1:], ws, ws[1:]):
        p, n0 = P(u0, z0)
        q, n1 = P(u1, z1)
        n = (n0 + n1).normalized()
        s = (q - p).cross(n)
        if s.length < 1e-6:
            continue
        s.normalize()
        for h0, h1, d, tag in ((w0 * 0.95 + 0.18, w1 * 0.95 + 0.12, depth * 0.45, "soot"), (w0 / 2, w1 / 2, depth, core)):
            ring = lambda c, hw: [c - s * hw - n * 0.4, c + s * hw - n * 0.4, c + s * hw + n * d, c - s * hw + n * d]  # noqa: E731
            out.append(kit.loft([ring(p, h0), ring(q, h1)], [tag], cap0=(tag, True), cap1=(tag, True)))
    return out


def fissure(kit, P, u0, z0, h, w=0.9, seed=0.0, segs=7, branches=2, spread=0.5, depth=0.2, core="ember", taper=1.0):
    """A crack glowing from within on the surface P: from (u0, z0) h up (down when h < 0) in `segs`
    short straight runs kinking alternately left and right, w wide at its root tapering to a point;
    `branches` forks off it, shorter and thinner, veering away to their own points. taper < 1: it
    ends that much narrower instead of in a point (a runnel)."""
    pts = [(u0, z0)]
    for i in range(1, segs + 1):
        dz = h / segs
        side = 1 if (i + int(seed)) % 2 else -1
        pts.append((pts[-1][0] + side * abs(dz) * spread * (0.5 + _hash(seed + i)), pts[-1][1] + dz))
    ws = [w * (1 - taper * i / segs) ** 0.8 + 0.08 for i in range(segs + 1)]
    out = strand(kit, P, pts, ws, depth, core)
    for b in range(branches):
        k = 1 + int((segs - 2) * (b + 1) / (branches + 1))
        side = 1 if (b + int(seed)) % 2 == 0 else -1
        L, bs = abs(h) * (0.36 - 0.08 * b), 4
        bp = [pts[k]]
        for j in range(1, bs + 1):
            du = side * L / bs * (0.8 + 0.4 * _hash(seed * 3 + b * 7 + j)) * (1.0 if j % 2 else 0.45)
            bp.append((bp[-1][0] + du, bp[-1][1] + math.copysign(L / bs * 0.75, h)))
        out += strand(kit, P, bp, [ws[k] * 0.6 * (1 - j / bs) + 0.06 for j in range(bs + 1)], depth * 0.9, core)
    return out


def runnel(kit, P, u, z0, z1, w=1.0, seed=0.0, depth=0.2):
    """Lava pouring down the surface P from (u, z0) to z1: a narrow, straight, kinked fissure of
    even width (never a cone), no forks."""
    segs = max(3, int(abs(z0 - z1) / 2.5))
    return fissure(kit, P, u, z0, z1 - z0, w=w, seed=seed, segs=segs, branches=0, spread=0.12, depth=depth,
                   core="flame", taper=0.35)


def witch_eye(kit, p, fwd, side, length=2.2, height=1.1, depth=0.5):
    """An almond of Morgul witch-light at p on a face whose outward normal is `side` (horizontal),
    its long axis along `fwd`: the Watchers' eyes (the one green accent)."""
    p, f, n = V(p), V((fwd[0], fwd[1], 0)).normalized(), V((side[0], side[1], 0)).normalized()
    poly = [p + f * (length / 2 * math.cos(math.pi * i / 4)) + Z * (height / 2 * math.sin(math.pi * i / 4))
            for i in range(8)]
    if f.cross(Z).dot(n) < 0:                           # the ring's normal along the sweep (loft's caps)
        poly.reverse()
    return [kit.loft([[q - n * 0.4 for q in poly], [q + n * depth for q in poly]], [["witch"] * 8],
                     cap0=("witch", False), cap1=("witch", True))]


def arch_teeth(kit, x0, x1, y, z0, z1, teeth=6, r=0.5, length=0.9):
    """The raised portcullis of an expansion's wall arch, on both faces (y and -y): its rails, bars
    and barbed teeth hanging below z0, between x0 and x1 (the arch runs along x)."""
    X, Y = V((1, 0, 0)), V((0, 1, 0))
    out = []
    for s in (-1, 1):
        out += kit.portcullis(V((0, s * y, 0)), X, Y * s, x0, x1, z0, z1, teeth=teeth, r=r, length=length)
    return out
