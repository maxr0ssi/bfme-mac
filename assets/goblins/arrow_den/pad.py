"""The fortress expansions' pad (Blender side), shared by the arrow den, the burrows, the giant
sentry and the spider holes: where EA's body meets the ground it gets a skirt of broken black rock,
and great bleached ribs rise out of the rock to clasp the body, as if every expansion grew out of
the bones of something the Goblins killed. Built from the Goblin kit (assets/goblins/shapes.py);
design coordinates, z 0 the ground.

    rock(kit, c, r, h)                  one faceted boulder standing on the ground
    skirt(kit, outline, ...)            boulders along a footprint outline, pushed out from its centre,
                                        clipped to a box, skipping gaps (doors, spawn holes, stairs)
    rib(kit, ctrl, r)                   a great curved rib along a cubic Bezier: thick at its foot,
                                        a knob at its head, an iron collar and rope lashing low
    clasp(kit, c, ...)                  ribs rising from a ring round a column, bowing out and
                                        curling in to grip it (the arrow den's stalk, the giant's)
    arch(kit, x, half, apex, ...)       a pair of ribs from the ground either side of y = y0 meeting
                                        over the top, a vertebra where they meet (the burrows' ribcage)
    band(kit, path, z, h), ring(c, r)    a riveted iron band round any convex outline; a circle of points
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft


def jitter(seed, i):
    """A repeatable pseudo-random number in [0, 1)."""
    x = math.sin(seed * 12.9898 + i * 78.233) * 43758.5453
    return x - math.floor(x)


def rock(kit, c, r, h, seed=0, k=6, lean=(0.0, 0.0), tag="rock"):
    """A faceted boulder r across (roughly) and h tall standing on the ground at c (nothing may go
    below z 0: the height check counts from the lowest point): an irregular k-gon foot, a shoulder
    at 0.55 h pushed by `lean`, a small flat top."""
    c = V((c[0], c[1], c[2] if len(c) > 2 else 0.0))
    ph = jitter(seed, 0) * math.pi
    lean = V((lean[0], lean[1], 0.0))
    rings = []
    for z, s, off in ((0.0, 1.0, 0.0), (0.55 * h, 0.82, 0.6), (h, 0.42, 0.9)):
        ring = []
        for j in range(k):
            a = ph + 2 * math.pi * (j + 0.35 * (jitter(seed, j + 7) - 0.5)) / k
            rr = r * s * (0.72 + 0.4 * jitter(seed, j + 3 + int(z * 10)))
            ring.append(c + V((math.cos(a) * rr, math.sin(a) * rr, z)) + lean * off)
        rings.append(ring)
    return [loft(rings, [tag, tag], cap0=(tag, False), cap1=(tag, True))]


def _inside(p, box, r):
    x0, x1, y0, y1 = box
    return x0 + r <= p.x <= x1 - r and y0 + r <= p.y <= y1 - r


def skirt(kit, outline, centre, r=2.6, h=2.4, pitch=3.4, out=0.8, seed=1, gaps=(), box=None, closed=True, z=0.0):
    """Boulders every `pitch` along the outline [(x, y)] (the body's foot), each pushed `out` away
    from `centre`, sizes varied about r and h; none whose centre lies in a gap (x0, x1, y0, y1);
    each shrunk to stay inside `box` (the footprint the checks hold us to); z: the ground they
    stand on (a plinth's top)."""
    pts = [V((x, y, z)) for x, y in outline]
    if closed:
        pts.append(pts[0])
    c0 = V((centre[0], centre[1], z))
    out_ = []
    i = 0
    for p, q in zip(pts, pts[1:]):
        n = max(1, int(round((q - p).length / pitch)))
        for s in range(n):
            m = p.lerp(q, (s + 0.5 * jitter(seed, i)) / n)
            d = m - c0
            d = d.normalized() if d.length > 1e-6 else V((1, 0, 0))
            big = jitter(seed, i + 101)
            rr = r * (0.65 + 0.6 * big)
            m = m + d * out * (0.6 + 0.8 * jitter(seed, i + 55))
            i += 1
            if any(x0 <= m.x <= x1 and y0 <= m.y <= y1 for x0, x1, y0, y1 in gaps):
                continue
            if box is not None:
                while rr > 0.9 and not _inside(m, box, rr * 1.5):
                    rr *= 0.8
                if not _inside(m, box, rr * 1.5):
                    continue
            out_ += rock(kit, m, rr, h * (0.6 + 0.7 * big), seed=seed * 31 + i, k=5 + (i % 2), lean=d * rr * 0.25)
    return out_


def bezier(ctrl, n):
    p0, p1, p2, p3 = (V(p) for p in ctrl)
    return [p0 * (1 - s) ** 3 + p1 * 3 * s * (1 - s) ** 2 + p2 * 3 * s * s * (1 - s) + p3 * s ** 3
            for s in (i / n for i in range(n + 1))]


def rib(kit, ctrl, r, n=8, k=6, head=True, collar=True, lash=True, tip=False, path=False):
    """A great bleached rib along the cubic Bezier ctrl (path: along the points ctrl), foot first:
    r at the foot tapering to 0.55 r, its foot raised clear of z 0 (set a rock over it); a knob at
    its head (tip: a point instead); a riveted iron collar low down and a rope lashing above it."""
    pts = [V(p) for p in ctrl] if path else bezier(ctrl, n)
    n = len(pts) - 1
    if pts[0].z < r * 0.9:                                         # the foot ring stays above the ground
        pts[0] = V((pts[0].x, pts[0].y, r * 0.9))
    radii = [r * (1.0 - 0.45 * (i / n) ** 0.8) for i in range(n + 1)]
    if tip:
        radii[-1] = 0.0
    out = [kit.tube(pts, radii, "bone", k=k, cap0="bone", cap1=None if tip else "bone")]
    if head and not tip:
        d = (pts[-1] - pts[-2]).normalized()
        e = radii[-1]
        out.append(kit.tube([pts[-1] - d * r * 0.3, pts[-1] + d * r * 0.5, pts[-1] + d * r * 0.9],
                            [e * 1.35, e * 1.4, e * 0.8], "bone", k=k, cap0="bone", cap1="bone"))
    if collar:
        a, b = pts[1], pts[2]
        d = (b - a).normalized()
        m = a.lerp(b, 0.3)
        out.append(kit.tube([m - d * r * 0.55, m + d * r * 0.55], [r * 1.3, r * 1.25], "iron", k=k,
                            cap0="iron", cap1="iron"))
    if lash:
        out += kit.lashing(pts[2].lerp(pts[3], 0.5), pts[3] - pts[2], radii[2] * 0.95, turns=2, w=r * 0.45)
    return out


def clasp(kit, c, count, foot_r, top_r, top_z, r=1.3, bow=4.0, phase=0.0, skip=(), n=8, tip=True):
    """`count` ribs rising from the ground at radius foot_r round the vertical axis through c, each
    bowing out by `bow` and curling in to grip the column at radius top_r, height top_z (their
    points against it). skip: indices left out (a brace, a stair, a door)."""
    c = V((c[0], c[1], 0.0))
    out = []
    for i in range(count):
        if i in skip:
            continue
        a = phase + 2 * math.pi * i / count
        rad = V((math.cos(a), math.sin(a), 0.0))
        foot = c + rad * foot_r
        top = c + rad * top_r + Z * top_z
        ctrl = [foot, foot + rad * bow + Z * top_z * 0.35, c + rad * (top_r + bow * 1.4) + Z * top_z * 0.9, top]
        out += rib(kit, ctrl, r, n=n, head=not tip, tip=tip)
    return out


def arch(kit, x, half, apex, r=1.2, y0=0.0, bulge=0.12, n=6, spike=True):
    """A pair of ribs from the ground at (x, y0 +- half) arching over the top to meet at (x, y0,
    apex): each a quarter ellipse swelling `bulge` wider at the shoulder, a knobbed vertebra where
    they meet and (spike) a bone spike standing on it."""
    out = []
    top = V((x, y0, apex))
    for e in (-1, 1):
        pts = []
        for i in range(n + 1):
            th = 0.5 * math.pi * i / n
            w = half * math.cos(th) * (1 + bulge * math.sin(2 * th))
            pts.append(V((x, y0 + e * max(w, 0.35 * r), apex * math.sin(th))))
        out += rib(kit, pts, r, head=False, lash=e < 0, path=True)
    out.append(kit.tube([top - V((0.9 * r, 0, 0)), top + V((0.9 * r, 0, 0))], [1.45 * r, 1.45 * r], "bone", k=6,
                        cap0="bone", cap1="bone"))
    if spike:
        out += kit.spike(top + Z * r * 0.9, Z, 2.8 * r, 0.5 * r, tag="bone", k=4)
    return out


def band(kit, path, z, h, th=0.7, inner=1.4, rivets=1, center=(0, 0), tag="iron", closed=False):
    """A riveted iron band h tall along a closed convex (x, y) outline at height z, th proud of it
    and sunk `inner` into what it wraps (the kit's hoop on any outline); closed: its inner face
    too (round a lobed or tapering body the band cannot follow)."""
    from sagekit.blender.geometry import sweep
    pts = [tuple(p) for p in path] + [tuple(path[0])]
    prof = [(-inner, z - h / 2), (th, z - h / 2), (th, z + h / 2), (-inner, z + h / 2)]
    solids, segs = sweep(pts, prof, [tag, tag, tag, tag if closed else None], center=center)
    out = list(solids)
    if rivets:
        for a2, b2, t2, n2 in segs[::rivets]:
            m = (a2 + b2) / 2
            out += kit.rivets(V((m.x, m.y, 0)), V((t2.x, t2.y, 0)), V((n2.x, n2.y, 0)), [(0.0, z)], th, 0.3)
    return out


def ring(c, r, k=8, phase=0.0):
    """k (x, y) points on a circle (a band's outline)."""
    return [(c[0] + r * math.cos(phase + 2 * math.pi * i / k), c[1] + r * math.sin(phase + 2 * math.pi * i / k))
            for i in range(k)]
