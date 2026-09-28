"""The citadel's motifs as functions (Blender side), so the fortress add-ons match the approved
citadel (assets/men/fortress: crown.py, gate.py) without importing its recipe. Copied and
generalised from the pilot: any convex outline, any scale.

    polygon        a regular k-gon or a chamfered square as a closed 2D path
    cornice        a moulded cornice swept round an outline (the citadel's eave band)
    corbel_course  the two-step corbels under a gallery, spaced along one face
    gallery        the machicolated gallery of the citadel's towers: corbels, a slab whose front is a
                   black enamel band (silver stars painted by star_band), a parapet, square merlons
    star_band      the paint layer that puts the silver stars on a gallery's black band
    star_frieze    the gate's black frieze with gilt seven-pointed stars (solids), architrave, cornice
    tree_panel     a steel-framed black panel with a round head bearing the White Tree
    voussoirs      the gate's arch of wedge stones and keystone (backs closed), for window hoods
    finial         the domes' steel collar, gilt orb and ringed spike (with steel ribs up a spire)
    coping         a raised moulded coping along a vertical outline (a gable's edge), per segment

Every function returns a list of closed solids; tags are the Men atlas's (assets/men/atlas.py)."""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import box_rings, loft, prism_uz, sweep

# the citadel's gallery section, in units of its own (the towers' gallery: 2.0 out, z from the
# corbels' foot at 73.8 up to the parapet's top at 81.6): (d out of the face, z above the foot)
SLAB = [(-2.5, 5.4), (0.0, 3.6), (1.0, 3.6), (1.0, 6.1), (-2.5, 6.1)]
SLAB_TAGS = ["stoneB", "stoneB", "enamel", "top", None]
PARAPET = [(0.3, 6.0), (0.925, 6.0), (0.925, 7.8), (0.3, 7.8)]
PARAPET_TAGS = [None, "stoneA", "top", "stoneA"]


# ---------------------------------------------------------------------- outlines
def polygon(cx, cy, r, k, phase=None, apothem=True):
    """A closed k-gon path round (cx, cy): r its apothem (default) or circumradius; by default a
    face looks along +x (phase 0 puts a corner there)."""
    R = r / math.cos(math.pi / k) if apothem else r
    ph = math.pi / k if phase is None else phase
    pts = [(cx + R * math.cos(ph + 2 * math.pi * i / k), cy + R * math.sin(ph + 2 * math.pi * i / k)) for i in range(k)]
    return pts + [pts[0]]


def chamfered(cx, cy, half, ch):
    ring = box_rings((cx - half, cx + half), (cy - half, cy + half), 0.0, ch)
    return [(p.x, p.y) for p in ring] + [(ring[0].x, ring[0].y)]


# ---------------------------------------------------------------------- mouldings
def cornice(path, z, out=0.8, h=1.1, back=0.5, center=(0, 0), tag="course"):
    """A moulded cornice round `path` (closed or open): a cavetto rising from the wall face to a
    square nose `out` proud, h tall, its back `back` buried in the wall."""
    prof = [(-back, z), (out * 0.35, z), (out, z + h * 0.55), (out, z + h), (-back, z + h)]
    return sweep(path, prof, ["stoneB", tag, tag, "top", None], center=center)[0]


def corbel_course(kit, a, t, n, u0, u1, z0, pitch=3.2, s=1.0):
    """Two-step corbels (the kit's) evenly along u0..u1 of a face, the first and last half a pitch in."""
    k = max(1, int(round((u1 - u0) / pitch)))
    step = (u1 - u0) / k
    out = []
    for i in range(k):
        out += kit.corbel(a, t, n, u0 + step * (i + 0.5), z0, w=0.55 * s, z1=z0 + 1.8 * s, z2=z0 + 3.6 * s,
                          d1=0.9 * s, d2=1.95 * s)
    return out


def gallery(kit, path, center, z0, s=1.0, corbels=True, merlon_w=2.4, min_face=4.0):
    """The citadel towers' machicolated gallery round a convex outline, from z0 (the corbels' foot):
    corbels under a slab `2 s` out whose front is black enamel (star_band paints the stars), a
    parapet and square merlons with capstones. s scales the section (1 = the citadel's).
    Returns (solids, the parapet's top z)."""
    sl = [(d * 2 * s if d > 0 else d * s, z0 + z * s) for d, z in SLAB]
    pa = [(d * 2 * s, z0 + z * s) for d, z in PARAPET]
    closed = abs(path[0][0] - path[-1][0]) + abs(path[0][1] - path[-1][1]) < 1e-6
    slab, segs = sweep(path, sl, SLAB_TAGS[:-1] + [None if closed else "stoneB"], center=center)
    out = slab + sweep(path, pa, PARAPET_TAGS, center=center)[0]
    top = z0 + 7.8 * s
    for a, b, t, n in segs:
        L = (b - a).length
        if L < min_face:
            continue
        a3 = V((a.x, a.y, 0))
        if corbels:
            out += corbel_course(kit, a3, t, n, 0.0, L, z0, pitch=3.2 * s, s=s)
        out += kit.merlons(a3, t, n, 0.15 * s, L - 0.15 * s, top, 0.6 * s, 1.85 * s,
                           w=merlon_w * s, gap=1.75 * s, h=2.8 * s, cap=0.55 * s, lip=0.2 * s)
    return out, top


def star_band(zrange, pitch=3.2, r=0.95):
    """The paint layer for a gallery's black band: silver seven-pointed stars, one every `pitch`
    along each vertical enamel face with zrange (world z) round its middle."""
    from ..paint import men_layers
    return men_layers()[2](zrange=zrange, pitch=pitch, r=r)


def star_frieze(kit, a, t, n, u0, u1, z0, d_back, d_front, stars=7, h=3.6, gilt=True):
    """The gate's entablature: an architrave (z0..+0.9h/3.6), a black frieze with `stars` gilt
    seven-pointed stars, a moulded cornice on top. u0..u1 along t, d_back..d_front out along n."""
    k = h / 3.6
    za, zf, zc = z0 + 1.2 * k, z0 + 2.6 * k, z0 + h

    out = [prism_uz(a, t, n, [(u0, z0), (u1, z0), (u1, za), (u0, za)], d_back, d_front,
                    ["stoneB", "stoneB", "top", "stoneB"], "course", None),
           prism_uz(a, t, n, [(u0 + 0.1, za), (u1 - 0.1, za), (u1 - 0.1, zf), (u0 + 0.1, zf)], d_back, d_front - 0.3,
                    [None, "stoneB", None, "stoneB"], "enamel", None)]
    out.append(prism_uz(a, t, n, [(u0 - 0.35 * k, zf), (u1 + 0.35 * k, zf), (u1 + 0.6 * k, zf + 0.5 * k), (u1 + 0.6 * k, zc),
                                  (u0 - 0.6 * k, zc), (u0 - 0.6 * k, zf + 0.5 * k)],
                        d_back, d_front + 0.45 * k, ["stoneB", "course", "stoneB", "top", "stoneB", "course"], "course", None))
    if gilt and stars:
        pitch = (u1 - u0) / stars
        for i in range(stars):
            out += kit.star(a, t, n, u0 + pitch * (i + 0.5), (za + zf) / 2, 0.5 * (zf - za) * 0.95,
                            d_front - 0.35, d_front + 0.1)
    return out


def tree_panel(kit, a, t, n, u, z, half, height, d=0.0):
    """A steel-framed black panel with a round head bearing the White Tree (the citadel's shields
    as a wall panel): u, z its bottom middle, half-width, height to the crown of the head."""
    rise = min(half, height * 0.3)
    zs = z + height - rise
    head = [(u + half * math.cos(th), zs + rise * math.sin(th)) for th in (math.pi * i / 6 for i in range(1, 6))]
    shape = [(u - half, z), (u + half, z), (u + half, zs)] + head + [(u - half, zs)]
    inner = [(u + (x - u) * 0.84, z + height * 0.07 + (y - z) * 0.88) for x, y in shape]
    out = [prism_uz(a, t, n, shape, d - 0.1, d + 0.7, ["trim"] * len(shape), "trim", None),
           prism_uz(a, t, n, inner, d + 0.6, d + 0.9, ["enamel"] * len(inner), "enamel", None)]
    return out + kit.white_tree(a, t, n, u, z + height * 0.12, height * 0.72, d + 0.95, r=max(0.14, height * 0.018))


def finial(kit, cx, cy, z0, orb_z, tip, collar=None):
    """The citadel domes' finial: (collar: (r, z0, z1)) a steel collar, then the kit's steel mast,
    gilt orb and ringed spike."""
    from ..shapes import turned
    out = []
    if collar:
        r, za, zb = collar
        out.append(turned(cx, cy, [(r, za), (r, zb - 0.4), (r * 0.7, zb)], ["trim", "trim"], k=6,
                          cap0=("trim", True), cap1=("trim", True)))
    return out + kit.finial(cx, cy, z0, orb_z, tip)


def spire_ribs(kit, cx, cy, rings, r=(0.3, 0.16), proud=0.15):
    """Steel ribs up a spire's edges: rings [[(x, y, z), ...] per level] (the edge points, equal
    counts), each rib pushed `proud` out from the axis."""
    from ..shapes import rail
    out = []
    for i in range(len(rings[0])):
        pts = []
        for rg in rings:
            p = V(rg[i])
            rad = V((p.x - cx, p.y - cy, 0))
            pts.append(p + (rad.normalized() * proud if rad.length > 1e-3 else V((0, 0, 0))) + V((0, 0, 0.06)))
        out.append(rail(pts, r[0], "trim", r[1]))
    return out


# ---------------------------------------------------------------------- gables
def coping(a, t, n, outline, d0, d1, w=0.9, inner=0.25, tag="stoneA"):
    """A raised coping along a vertical outline [(u, z), ...] in the plane (t, z) at anchor a, from
    d0 to d1 along n: one solid per segment, `w` wide outward of the outline (its left: run a
    gable's outline from its left foot over the apex to its right foot) and `inner` inward, the
    segments mitred where they meet (the joints are buried; the two ends are closed)."""
    pts = [p for k, p in enumerate(outline) if k == 0 or math.hypot(p[0] - outline[k - 1][0], p[1] - outline[k - 1][1]) > 1e-3]
    nrm = []
    for (u0, z0), (u1, z1) in zip(pts, pts[1:]):
        L = math.hypot(u1 - u0, z1 - z0)
        nrm.append((-(z1 - z0) / L, (u1 - u0) / L))
    miter = [nrm[0]]
    for n0, n1 in zip(nrm, nrm[1:]):
        k = 1 + n0[0] * n1[0] + n0[1] * n1[1]
        miter.append(((n0[0] + n1[0]) / k, (n0[1] + n1[1]) / k))
    miter.append(nrm[-1])
    outer = [(u + m[0] * w, z + m[1] * w) for (u, z), m in zip(pts, miter)]
    inside = [(u - m[0] * inner, z - m[1] * inner) for (u, z), m in zip(pts, miter)]
    out = []
    last = len(pts) - 2
    for i in range(len(pts) - 1):
        poly = [inside[i], inside[i + 1], outer[i + 1], outer[i]]
        up = nrm[i][1] > 0.3
        side = "top" if up else "stoneA"
        tags = ["stoneA", "stoneA" if i == last else None, side, "stoneA" if i == 0 else None]
        area = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1]))
        if area < 0:
            poly, tags = poly[::-1], [tags[2], tags[1], tags[0], tags[3]]
        out.append(prism_uz(a, t, n, poly, d0, d1, tags, tag, "stoneB"))
    return out


def voussoirs(a, t, n, inner, outer, d0, d1, count=7, gap=0.12, key=None):
    """The gate's arch of wedge stones (the kit's voussoirs) with their backs closed, for a hood on
    a wall whose inside is open to the sky (a tower's shell): (half, rise, spring z) half-ellipses,
    alternately proud, and a raised keystone (key: (half_top, z_top, d_extra))."""
    from ..shapes import ellipse
    out = []
    for i in range(count):
        a0 = math.pi * i / count + (gap / inner[0] if i else 0.0)
        a1 = math.pi * (i + 1) / count - (gap / inner[0] if i < count - 1 else 0.0)
        poly = [ellipse(*inner, a0), ellipse(*outer, a0), ellipse(*outer, a1), ellipse(*inner, a1)]
        if key and i == count // 2:
            (u0, z0), (u1, z1) = ellipse(*inner, a1), ellipse(*inner, a0)
            hw, zt, dx = key
            out.append(prism_uz(a, t, n, [(u0, z0), (u1, z1), (hw, zt), (-hw, zt)], d0, d1 + dx,
                                ["stoneB", "stoneB", "top", "stoneB"], "stoneA", "stoneB"))
            continue
        dd = d1 if i % 2 == 0 else d1 - 0.2
        out.append(prism_uz(a, t, n, poly, d0, dd, ["stoneB", "top", "stoneB", "stoneB"], "stoneA", "stoneB"))
    return out


def stars_arc(kit, a, t, n, u, z, radius, d0, d1, r=0.8, count=7, spread=120.0):
    """The seven stars of Elendil in an arc over a point (u, z): gilt, on a face."""
    out = []
    for i in range(count):
        th = math.radians(90 - spread / 2 + spread * i / (count - 1))
        out += kit.star(a, t, n, u + radius * math.cos(th), z + radius * math.sin(th), r, d0, d1)
    return out


def box(x0, x1, y0, y1, z0, z1, tags, cap0=("stoneB", False), cap1=("top", True), ch=0.0):
    """An axis-aligned (optionally chamfered) block."""
    return loft([box_rings((x0, x1), (y0, y1), z0, ch), box_rings((x0, x1), (y0, y1), z1, ch)], [tags], cap0=cap0, cap1=cap1)
