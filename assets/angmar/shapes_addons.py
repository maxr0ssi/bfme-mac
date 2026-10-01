"""The Angmar add-ons' shared pieces (Blender side): the citadel's upgrades (the House of
Lamentation, the sanctum, the spikes) and the two free-standing defences (the battle tower, the
sentry tower). Functions of the Angmar kit (`kit`, shapes.py), so the kit's own signatures stay
untouched; the citadel's own modules (assets/angmar/fortress/) are read, never changed.

The citadel's language carried to the add-ons: the forged tine with a frozen tip, small (the
towers' crowns); the cairn of black stone and ice with the cold fire burning out of its crater
(the crown's heart); ice crystal clusters; frost creeping over iron. Each building takes ONE of
them as its bold mass (Max: the same motif stamped on every building reads as clones).

    small_tine(kit, c, deg, r, z0, H, W, ...)   one forged tine of the citadel's crown at any size: its
                                        root at r from c on the ray at deg, H tall from z0 (the foot
                                        buried 0.12 H below), W its half width at the widest; barbs,
                                        a riveted band, the rune groove and a frozen tip scaled to it
    tine_crown(kit, c, z0, tines, H, W)  a few small tines round c (tines [(deg, r)])
    frozen_tip(kit, h, frost, barbs, s) the tine kit's frozen tip at scale s (crystals, icicles and the
                                        casing's ragged line shrink with the tine)
    cairn(kit, c, r, h, kind)           black stone and ice shards heaped round a crater, the cold fire
                                        in it (its point recorded)
    frozen_captive(kit, c, face, h)     a thrall frozen into a pillar of ice crystals, his head and
                                        raised arms breaking out of its top, shackled (chain_to: chained)
    frozen_spikes(kit, name, minz, frost)  EA's tall spikes on the target mesh frozen from `frost` of
                                        their height: casings following each spike's own section, read
                                        from EA's mesh at design time (the geometry step's scene)

Coordinates are each add-on's own mesh coordinates (the citadel's for the upgrades).
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft

from .shapes_tine import _h

# the citadel's tine above its walk (fortress/crown.py: z 52 to the tip at 120, widest 9.6 x 3.0 at z 64)
# as fractions: (height f, outward lean as a fraction of the height, half width, half depth as fractions of
# the widest); the foot runs 0.12 of the height below z0 into what the tine stands on
PROFILE = [(-0.12, 0.0, 0.80, 0.95), (0.0, 0.0, 0.86, 0.97), (0.18, 0.004, 1.0, 1.0), (0.44, 0.022, 0.83, 0.9),
           (0.68, 0.043, 0.5, 0.7)]
TIP_LEAN = 0.06
DEPTH = 0.36                        # half depth over half width (the citadel's 0.31, a touch fuller when small)


def small_tine(kit, c, deg, r, z0, H, W, barbs=None, band=True, rune=True, frost=0.62, seed=0.0):
    """One forged tine with a frozen tip: its spine at r from c (x, y) on the ray at deg, from z0 to
    the tip H above, W its half width at the widest (along the ring), its broad face outward.
    barbs [(f, edge, depth)] (f a fraction of H; default four alternating). Returns (solids,
    CrownTine)."""
    a = math.radians(deg)
    e = V((math.cos(a), math.sin(a), 0))
    ctr = V((c[0], c[1], 0))
    keys = [(z0 + H * f, tuple((ctr + e * (r + H * lean))[:2]), (W * fw, W * DEPTH * fd))
            for f, lean, fw, fd in PROFILE]
    h = kit.CrownTine(keys, e, ctr + e * (r + H * TIP_LEAN) + Z * (z0 + H))
    barbs = barbs if barbs is not None else [(0.30, 1, 0.6), (0.45, -1, 0.6), (0.62, 1, 0.62), (0.78, -1, 0.6)]
    bz = [(z0 + H * f, side, dep) for f, side, dep in barbs]
    out = kit.forged_tine(h, bz, (), (z0 + H * 0.2, z0 + H * 0.58) if rune else None, None, seed=seed)
    if band:
        out += kit.tine_band(h, z0 + H * 0.1, height=max(1.2, H * 0.05))
    zf = z0 + H * frost
    out += frozen_tip(kit, h, zf, [b for b in bz if b[0] >= zf - 1.0], H / 68.0, seed=seed)
    return out, h


def tine_crown(kit, c, z0, tines, H, W, seed=0.0, **kw):
    """Small tines round c: tines [(deg, r)] or [(deg, r, H)]; each a forged tine (small_tine)."""
    out = []
    for i, t in enumerate(tines):
        deg, r = t[0], t[1]
        hh = t[2] if len(t) > 2 else H
        s, _ = small_tine(kit, c, deg, r, z0, hh, W * hh / H, seed=seed + i * 2.3, **kw)
        out += s
    return out


def frozen_tip(kit, h, frost, barbs, s, seed=0.0):
    """The tine kit's frozen tip (shapes_tine.py TineKit.frozen_tip) at scale s: a casing of ice
    from `frost` to the point (ragged frost line, crystal facets), rime on its last stretch,
    crystals growing out of it and a few out of the iron below, icicles off the barbs."""
    out = []
    top = h.keys[-1][0]
    n = len(kit.tine_ring(h, frost))
    rings = [kit.tine_ring(h, frost - 5.5 * s, grow=0.98, dgrow=0.98)]
    ragged = kit.tine_ring(h, frost - 1.0 * s, grow=1.24, dgrow=1.55)
    D0 = h.section(frost)[1]
    rings.append([V((p.x, p.y, p.z - 3.6 * s * _h(seed, 7, j))) + h.n * (0.4 * D0 * (_h(seed, 0, j) - 0.4))
                  for j, p in enumerate(ragged)])
    for i, f in enumerate((0.3, 0.6, 0.88)):
        z = frost + (top - frost) * f
        W, D = h.section(z)
        ring = kit.tine_ring(h, z, grow=1.2 - 0.05 * i, dgrow=1.5)
        rings.append([p + h.n * (0.5 * D * (_h(seed, i + 1, j) - 0.4)) for j, p in enumerate(ring)])
    rings.append([h.tip + Z * (2.0 * s) + h.n * (0.3 * s)] * n)
    out.append(loft(rings, ["ice", "ice", "ice", "rime", "rime"], cap0=("ice", False), cap1=("rime", False)))
    up = (h.tip - h.point(frost, 0, 0)).normalized()
    for k in range(8):
        f = -0.2 + 0.85 * k / 7
        z = frost + (top - frost) * f
        j = (1, 4, 2, 5, 9, 7)[k % 6]
        side = 1 if j in (1, 2, 9) else -1
        out_d = -1 if j in (7, 9) else 1
        grow = (1.08, 1.25) if f > 0 else (0.9, 0.9)
        base = kit.tine_ring(h, z, grow=grow[0], dgrow=grow[1])[j]
        lean = h.t * side * 0.4 + h.n * 0.4 * out_d
        L = (8.5 - 3.5 * max(f, 0.0)) * s * (0.75 + 0.5 * _h(seed + 5, k))
        out += kit.shard(base, up + lean, L, max(0.35, (0.8 + 0.5 * (1 - abs(f))) * s), k=4 + k % 2, seed=seed + k,
                         bury=0.6 * s)
    for z, side, dep in barbs:
        W, D = h.section(z)
        p = h.point(z + 0.4 * s, side * W * (1.0 + dep) * 0.96, 0)
        for j, (du, L) in enumerate(((0.0, 4.5), (-side * 0.9, 3.0))):
            q = p + h.t * du * s
            w = max(0.25, 0.45 * s)
            ring = [q + h.t * w, q + h.n * w * 1.1, q - h.t * w, q - h.n * w * 1.1]
            out.append(loft([ring, [q - Z * L * s * (0.8 + 0.4 * _h(seed, z, j))] * 4], ["ice"], cap0=("ice", True),
                            cap1=("ice", False)))
    return out


def cairn(kit, c, r, h, kind="coldfire", seed=0.0, n=9, rim=5):
    """Black stone and ice shards heaped round c (r across, h tall), a ring of `rim` taller shards
    leaning out round a crater at its top; the cold fire in the crater (its point recorded)."""
    c = V((c[0], c[1], c[2]))
    out = kit.ice_cluster(c, r, h, n=n, seed=seed, lean=0.5, thick=0.24, tag="rock", stone="ice", hollow=2)
    for i in range(rim):
        p = kit.polar(c, r * 0.4, i * 360.0 / rim + 13.0 * seed, c.z + h * 0.8)
        d = (p - V((c.x, c.y, p.z))).normalized() * 0.55 + Z
        out += kit.shard(p, d, h * (0.32 + 0.1 * ((i * 5) % 3)), max(0.5, r * 0.15), k=5, seed=seed + i,
                         tag="ice" if i % 2 else "rock", bury=h * 0.1)
    if kind:
        kit.fire(c + Z * (h * 0.95), kind)
    return out


def frozen_captive(kit, c, face, h=15.0, seed=0.0, chain_to=None):
    """A thrall frozen standing into a pillar of ice crystals at c (on what he stands on), facing
    `face`: three or four big shards close round him to his chest, his head and arms raised in
    lament breaking out of the top (dark: soot), shackles on his wrists; chain_to: a point his
    wrists are chained to."""
    c = V((c[0], c[1], c[2]))
    f = V((face[0], face[1], 0)).normalized()
    s = V((-f.y, f.x, 0))
    k = h / 15.0
    out = []
    # the figure: legs and body as one tapering eight-sided column, a head, two raised arms
    body = [(0.0, 1.1), (5.5, 1.25), (8.6, 1.5), (9.8, 1.0)]
    rings = []
    for z, rr in body:
        rings.append([c + Z * (z * k) + (f * math.cos(math.pi * i / 4) * 0.75 + s * math.sin(math.pi * i / 4) * 1.15)
                      * rr * k for i in range(8)])
    out.append(loft(rings, ["soot"] * 3, cap0=("soot", False), cap1=("soot", False)))
    head = c + Z * (11.0 * k) + f * 0.3 * k
    hr = 0.95 * k
    out.append(loft([[head - Z * hr + (f * math.cos(2 * math.pi * i / 6) + s * math.sin(2 * math.pi * i / 6)) * 0.2 * hr
                      for i in range(6)],
                     [head + (f * math.cos(2 * math.pi * i / 6) + s * math.sin(2 * math.pi * i / 6)) * hr
                      for i in range(6)],
                     [head + Z * hr * 1.05] * 6], ["soot", "soot"], cap0=("soot", False), cap1=("soot", False)))
    wrists = []
    for side in (-1, 1):
        sh = c + Z * (9.4 * k) + s * side * 1.4 * k
        el = sh + s * side * 1.3 * k + Z * 2.0 * k + f * 0.2 * k
        wr = el + s * side * 0.3 * k + Z * 2.2 * k
        out.append(kit.tube([sh, el, wr], [0.45 * k, 0.38 * k, 0.32 * k], "soot", k=5, cap0="soot", cap1="soot"))
        out.append(kit.tube([wr - Z * 0.5 * k, wr + Z * 0.3 * k], [0.55 * k, 0.55 * k], "iron", k=6, cap0="iron",
                            cap1="iron"))
        wrists.append(wr)
    if chain_to is not None:
        for w in wrists:
            out += kit.chain(w, V(chain_to), link=1.2 * k, w=0.45 * k)
    # the ice: big shards closing round him to the chest, leaning in
    n = 4
    for i in range(n):
        a = 2 * math.pi * (i + 0.15 * _h(seed, i)) / n + math.pi / 4
        e = s * math.cos(a) + f * math.sin(a)
        base = c + e * (1.6 * k) - Z * (0.6 * k)
        d = (Z * 1.0 - e * 0.12).normalized()
        L = (10.6 + 2.4 * _h(seed + 1, i)) * k
        out += kit.shard(base, d, L, (2.6 + 0.5 * _h(seed + 2, i)) * k, k=5, point=0.24, flat=0.8, seed=seed + i,
                         bury=0.8 * k)
    for i in range(3):                                   # smaller crystals at the foot, leaning out
        a = 2 * math.pi * (i + 0.5) / 3 + seed
        e = s * math.cos(a) + f * math.sin(a)
        out += kit.shard(c + e * (2.6 * k), (Z + e * 0.6).normalized(), (4.0 + 1.5 * _h(seed + 3, i)) * k, 1.0 * k,
                         k=4, seed=seed + 7 + i, bury=0.6 * k, tag="ice" if i % 2 else "rime")
    return out


def _loose_parts(name):
    """EA's target mesh `name` (the geometry step's scene, before our solids join it) as loose parts:
    [(set of world vertex positions as tuples, edges as point pairs)], read at design time."""
    import bpy
    o = bpy.data.objects[name]
    mw = o.matrix_world
    me = o.data
    vs = [mw @ v.co for v in me.vertices]
    parent = list(range(len(vs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for p in me.polygons:
        a = find(p.vertices[0])
        for j in p.vertices[1:]:
            b = find(j)
            if a != b:
                parent[b] = a
    parts = {}
    for e in me.edges:
        r = find(e.vertices[0])
        parts.setdefault(r, []).append((vs[e.vertices[0]], vs[e.vertices[1]]))
    return list(parts.values())


def _slice(edges, z, pad, grow, k=8, phase=0.0):
    """The section of a spike (its edges) at height z: k points round its centroid, each at the
    section's support distance along its direction, grown by `grow` and `pad`."""
    pts = []
    for p, q in edges:
        if (p.z - z) * (q.z - z) < 0:
            t = (z - p.z) / (q.z - p.z)
            pts.append(p.lerp(q, t))
    if len(pts) < 3:
        return None
    c = sum(pts, V((0, 0, 0))) / len(pts)
    ring = []
    for i in range(k):
        a = phase + 2 * math.pi * i / k
        d = V((math.cos(a), math.sin(a), 0))
        hgt = max((p - c).dot(d) for p in pts)
        ring.append(c + d * (max(hgt, 0.2) * grow + pad))
    return ring


def frozen_spikes(kit, name, minz=30.0, frost=0.55, seed=0.0):
    """EA's tall spikes on the target mesh `name` (loose parts whose point is at least minz high; a
    part standing on another's point is taken as its extension) frozen from `frost` of their height
    to the point: a faceted casing of ice following each spike's own section (measured at design
    time), its lower edge ragged, rime on the last stretch, a few crystals growing out of it.
    Returns (solids, [(foot centre, point)] of the spikes frozen)."""
    parts, allp = [], []
    for edges in _loose_parts(name):
        allp += [p for e in edges for p in e]
        pts = [p for e in edges for p in e]
        z0 = min(p.z for p in pts)
        tip = max(pts, key=lambda p: p.z)
        parts.append([edges, z0, tip.copy()])
    tops = [p for p in parts if p[1] > 15.0]                      # extensions standing on a spike's point
    base = [p for p in parts if p[1] <= 15.0]
    for ext in tops:
        for b in base:
            if (V((b[2].x, b[2].y, 0)) - V((ext[0][0][0].x, ext[0][0][0].y, 0))).length < 4.0 \
                    and abs(b[2].z - ext[1]) < 3.0:
                b[0] = b[0] + ext[0]
                b[2] = ext[2]
                break
    lo = V((min(p.x for p in allp), min(p.y for p in allp), 0))
    hi = V((max(p.x for p in allp), max(p.y for p in allp), 0))

    def inside(q, m=0.05):                                   # EA's footprint: nothing new may stand outside it
        return V((min(max(q.x, lo.x + m), hi.x - m), min(max(q.y, lo.y + m), hi.y - m), q.z))
    out, frozen = [], []
    for n, (edges, z0, tip) in enumerate(sorted(base, key=lambda p: math.atan2(p[2].y, p[2].x))):
        if tip.z < minz:
            continue
        H = tip.z - z0
        zf = z0 + H * (frost + 0.06 * (_h(seed, n) - 0.5))
        ph = 2.0 * _h(seed + 1, n)
        rings = []
        foot = _slice(edges, zf - 1.6, 0.0, 0.96, phase=ph)
        lip = _slice(edges, zf, 0.45, 1.22, phase=ph)
        if foot is None or lip is None:
            continue
        rings.append(foot)
        rings.append([p - Z * (1.6 * _h(seed + 2, n, j)) for j, p in enumerate(lip)])
        for i, f in enumerate((0.3, 0.58, 0.82)):
            zz = zf + (tip.z - zf) * f
            r = _slice(edges, zz, 0.4 - 0.08 * i, 1.22, phase=ph)
            if r is None:
                break
            rings.append([p + (p - sum(r, V((0, 0, 0))) / len(r)) * 0.25 * (_h(seed + 3, n, i, j) - 0.4)
                          for j, p in enumerate(r)])
        rings.append([tip + Z * 1.2] * len(foot))
        rings = [[inside(q) for q in r] for r in rings]
        tags = ["ice"] * (len(rings) - 3) + ["rime", "rime"]
        out.append(loft(rings, tags, cap0=("ice", False), cap1=("rime", False)))
        axis = (tip - (sum(foot, V((0, 0, 0))) / len(foot))).normalized()
        for k in range(3):
            f = 0.15 + 0.25 * k
            zz = zf + (tip.z - zf) * f
            r = _slice(edges, zz, 0.3, 1.15, phase=ph)
            if r is None:
                continue
            p = r[(3 * k + n) % len(r)]
            c = sum(r, V((0, 0, 0))) / len(r)
            d = (axis + (p - c).normalized() * 0.7).normalized()
            L = 4.5 - 1.0 * k
            while L > 1.0 and (inside(p + d * (L + 0.8)) - (p + d * (L + 0.8))).length > 1e-6:
                L -= 0.5                                     # short enough to stay inside EA's footprint
            out += kit.shard(inside(p, 1.0), d, L, 0.75, k=4 + k % 2, seed=seed + n + k, bury=0.6)
        frozen.append((sum(foot, V((0, 0, 0))) / len(foot), tip))
    return out, frozen
