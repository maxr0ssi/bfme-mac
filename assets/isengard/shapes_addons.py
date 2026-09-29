"""The Isengard add-ons' shared pieces (Blender side): the citadel's upgrades (the wizard's tower,
the burning forges, the excavations, the orcfire munitions) and the expansions and pads (ballista,
battle tower, warg sentry, mine launcher). Functions of the Isengard kit (`kit`, shapes.py), so the
kit's own signatures stay untouched.

    pier_ring(m, n, t, hw, proj, z)     a pier's section in plan: nine points standing out of a face
                                        (m its midpoint, n out, t along), fluted cheeks, its back buried
    pier(kit, rings)                    Orthanc's many-sided pier: the rings lofted, a silver arris
    horn(kit, m, n, t, z0, z1, ...)     a pier opening into a horn: the section narrowing to an
                                        inner knife edge, leaning out, curling back, to a point
    extrude(poly, off0, off1, ...)      a convex polygon swept along any direction, wound outward
    arch(u0, u1, z0, h)                 a pointed arch (EA's 35-degree head) as a (u, z) polygon
    arch_slot(kit, a, t, n, u, z0, w, h) a pointed-arch panel on a face with a silver frame
    hand_arch(kit, a, t, n, u, z0, w, h) the White Hand in a pointed-arch slot (the citadel's)
    ember_slit(kit, a, t, n, u, z0, w, h) a narrow pointed ember window
    crown_blades(kit, pts, z, h)        pointed merlons along a closed polygon's edges (a crown)
    cauldron(kit, c, r, h)              a faceted iron fire-pot: eight hard sides, a spiked rim,
                                        glowing coals
    spur(kit, a, out, z, length)        a leaning iron spur (EA's wall spikes)

Placement as in the kit: a, t, n a face (anchor, along, out), u along it, z up, d out.
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz

POINT = math.radians(35.0)                  # EA's wedge point


def _h(v):
    return V((v[0], v[1], 0.0))


FRONT = 4                                   # the arris: pier_ring's middle point


def pier_ring(m, n, t, hw, proj, z, back=0.6, flute=True):
    """A pier's section at height z (9 points): back corners sunk `back` into the face hw either
    side of m, a shoulder, a flute cut into each cheek, the cheeks, the arris `proj` out (FRONT).
    flute=False: the flutes filled (a plain seven-sided pier with two extra points)."""
    m, n, t = _h(m) + Z * z, _h(n).normalized(), _h(t).normalized()
    k = 0.3 if flute else 0.42
    half = [(1.0, -back / max(proj, 1e-3)), (0.96, 0.3), (0.74, k), (0.58, 0.64)]
    left = [m - t * hw * u + n * proj * d for u, d in half]
    right = [m + t * hw * u + n * proj * d for u, d in reversed(half)]
    return left + [m + n * proj] + right


def pier(kit, rings, tag="stoneA", arris="trim", cap=True):
    """A pier lofted through pier_ring sections (bottom up): its back (the last side) buried, a
    silver beam along the arris from ring to ring."""
    k = len(rings[0])
    tags = [[tag] * (k - 1) + [None]] * (len(rings) - 1)
    out = [loft(rings, tags, cap0=(tag, False), cap1=(tag, cap))]
    if arris:
        f = k // 2
        for i, (r0, r1) in enumerate(zip(rings, rings[1:])):
            if (r1[f] - r0[f]).length > 0.3:
                out.append(kit.beam(r0[f] + Z * (0.3 if i == 0 else 0.0), r1[f], 0.28, arris))
    return out


def horn(kit, m, n, t, z0, z1, hw, proj, lean=0.14, curl=0.1, flare=1.35, tag="stoneA", steps=7, arris="trim"):
    """A horn out of a pier's top: its section at z0 is pier_ring(m, n, t, hw, proj) (so it sits on
    the pier), widening by `flare` low down, its back corners closing into an inner knife edge,
    its centre leaning out along n by `lean` of the height and curling back by `curl`, tapering to
    a point at z1."""
    m, n, t = _h(m), _h(n).normalized(), _h(t).normalized()
    H = z1 - z0
    rings = []
    for i in range(steps + 1):
        f = i / steps
        z = z0 + H * f
        off = n * H * (lean * math.sin(math.pi * f * 0.85) - curl * f * f)
        c = m + off
        if i == steps:
            rings.append([c + n * proj * 0.4 + Z * z] * 9)
            continue
        bump = math.sin(math.pi * min(f * 2.2, 1.0))
        w = hw * (1.0 + (flare - 1.0) * bump) * (1 - f) ** 0.75
        p = proj * (1.0 + 0.25 * bump) * (1 - f) ** 0.5
        ring = pier_ring(c, n, t, w, p, z)
        close = min(1.0, f * 1.6)                    # the back corners close into an inner edge
        for j in (0, 8):
            q = ring[j]
            ring[j] = c + Z * z - n * (0.6 + close * p * 0.6) + (q - c - Z * z).project(t) * (1 - close * 0.92)
        rings.append(ring)
    out = [loft(rings, [[tag] * 9] * steps, cap0=(tag, False), cap1=(tag, False))]
    if arris:
        for r0, r1 in zip(rings[:-2], rings[1:-1]):
            out.append(kit.beam(r0[FRONT], r1[FRONT], 0.26, arris))
        out.append(kit.beam(rings[-2][FRONT], rings[-1][FRONT], 0.26, arris, 0.0))
    return out


def extrude(poly, off0, off1, tags, cap0, cap1):
    """A convex polygon (3D points) swept from poly + off0 to poly + off1, wound so that its caps
    face out whatever the polygon's order (loft needs the ring's normal along the sweep)."""
    poly = [V(p) for p in poly]
    nrm = V((0, 0, 0))
    for a, b in zip(poly, poly[1:] + poly[:1]):
        nrm += a.cross(b)
    if nrm.dot(V(off1) - V(off0)) < 0:
        poly = list(reversed(poly))
        tags = list(reversed(tags[:-1])) + [tags[-1]] if isinstance(tags, list) else tags
    return loft([[p + V(off0) for p in poly], [p + V(off1) for p in poly]], [tags], cap0=cap0, cap1=cap1)


def arch(u0, u1, z0, h):
    """A pointed arch from u0 to u1, its springing at z0 + h - head, its point at z0 + h."""
    w = u1 - u0
    head = min(h * 0.45, (w / 2) / math.tan(POINT / 2) * 0.5)
    m = (u0 + u1) / 2
    return [(u0, z0), (u1, z0), (u1, z0 + h - head), (m, z0 + h), (u0, z0 + h - head)]


def arch_slot(kit, a, t, n, u, z0, w, h, d0=-0.6, d1=0.5, tag="soot", frame="trim", fw=0.3, bat=0.0):
    """A pointed-arch panel (tag) on a face, standing d1 out of it, framed in `frame` beams."""
    poly = arch(u - w / 2, u + w / 2, z0, h)
    a, t, n = V(a), V(t), V(n)
    out = [prism_uz(a, t, n, poly, d0, d1, [tag] * 5, tag, None, bat)]
    if frame:
        for (u0, za), (u1, zb) in zip(poly, poly[1:] + poly[:1]):
            lean0, lean1 = bat * (za - z0), bat * (zb - z0)
            out.append(kit.beam(a + t * u0 + Z * za + n * (d1 + 0.05 - lean0), a + t * u1 + Z * zb + n * (d1 + 0.05 - lean1),
                                fw, frame))
    return out


def hand_arch(kit, a, t, n, u, z0, w, h, d0=-0.6, d1=0.9, bat=0.0):
    """The White Hand in a pointed-arch slot (the citadel's big_hands): a black panel, a silver
    frame, the Hand standing on it."""
    out = arch_slot(kit, a, t, n, u, z0, w, h, d0, d1, "stoneB", "trim", 0.3, bat)
    size = min(w * 0.95, h * 0.62)
    lean = bat * (h * 0.1)
    a2 = V(a) - V(n) * lean
    out += kit.hand(a2, t, n, u, z0 + h * 0.1, size, d1, th=0.4, back="mark")
    return out


def ember_slit(kit, a, t, n, u, z0, w, h, d0=-0.8, d1=0.25, bat=0.0):
    """A narrow pointed window glowing from within (no frame)."""
    return [prism_uz(V(a), V(t), V(n), arch(u - w / 2, u + w / 2, z0, h), d0, d1, ["ember"] * 5, "ember", None, bat)]


def crown_blades(kit, pts, z, h, per_edge=2, w=0.6, back=1.0, lean=0.12, tag="stoneA", edge="trim", corners=True,
                 width=None, closed=True, centre=None):
    """Pointed merlons standing on a closed polygon's edges at z (pts: its corners, 2D, in order):
    `per_edge` on each edge - plates `width` wide along the edge (default a fifth of it, at most
    4), h tall, 2 * w thick, a long pointed head (the top 58 %) with silver on its slopes - and
    one knife fin on each corner along the corner's bisector (corners=True). closed=False: an open
    run of edges (pts in order), `centre` the point inside it (default the points' mean)."""
    P = [_h(p) for p in pts]
    ctr = _h(centre) if centre is not None else sum(P, V((0, 0, 0))) / len(P)
    out = []
    for i, p in enumerate(P):
        if not closed and i == len(P) - 1:
            break
        q = P[(i + 1) % len(P)]
        d = (q - p).normalized()
        nrm = V((d.y, -d.x, 0))
        if nrm.dot((p + q) / 2 - ctr) < 0:
            nrm = -nrm
        L = (q - p).length
        wd = width or min(4.0, L / 5.0)
        for k in range(per_edge):
            u = L * (k + 1) / (per_edge + 1)
            poly = [(u - wd / 2, z - 0.3), (u + wd / 2, z - 0.3), (u + wd / 2, z + h * 0.42), (u, z + h),
                    (u - wd / 2, z + h * 0.42)]
            out.append(prism_uz(p, d, nrm, poly, -w, w, [tag, tag, edge, edge, tag], tag, tag, lean))
        if not corners:
            continue
        bis = (p - ctr).normalized()
        out += kit.blade(p - bis * back * 0.5, bis, z, z + h * 1.25, 0.9, 0.9 + h * lean * 1.3, w=w * 1.2, tip=h * 0.55,
                         back=back, tag=tag, edge=edge)
    return out


def cauldron(kit, c, r, h, k=8, spikes=True, legs=True):
    """A faceted iron fire-pot at c (its foot): k hard sides flaring to a thick silver rim, coals
    glowing inside, iron spikes round the rim, three splayed legs."""
    c = V(c)
    ph = math.pi / k
    ring = lambda rr, z: [c + V((rr * math.cos(ph + 2 * math.pi * i / k), rr * math.sin(ph + 2 * math.pi * i / k), z))  # noqa: E731
                          for i in range(k)]
    out = [loft([ring(r * 0.45, 0.0), ring(r * 0.9, h * 0.35), ring(r, h * 0.8), ring(r * 1.12, h * 0.86),
                 ring(r * 1.12, h), ring(r * 0.86, h), ring(r * 0.86, h * 0.72)],
                ["iron", "iron", "iron", "trim", "trim", "ember"], cap0=("iron", False), cap1=("ember", True))]
    if spikes:
        for i in range(k):
            ang = 2 * math.pi * i / k + ph
            d = V((math.cos(ang), math.sin(ang), 0))
            p = c + d * r * 1.05 + Z * (h - 0.2)
            out.append(kit.beam(p, p + (d * 0.35 + Z).normalized() * r * 0.8, r * 0.09, "iron", 0.0))
    if legs:
        for i in range(3):
            ang = 2 * math.pi * i / 3
            d = V((math.cos(ang), math.sin(ang), 0))
            out.append(kit.beam(c + d * r * 0.7 + Z * h * 0.4, c + d * r * 1.05 - Z * 0.3, r * 0.1, "iron"))
    return out


def spur(kit, a, out, z, length, r=0.45, lean=0.5, tag="iron"):
    """An iron spur from a (a face or edge) along the horizontal `out`, rising by `lean`."""
    o = _h(out).normalized()
    p = _h(a) + Z * z
    return [kit.beam(p - o * 0.6, p + (o + Z * lean).normalized() * length, r, tag, 0.0)]
