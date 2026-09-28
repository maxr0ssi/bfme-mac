"""Gondor's domed tower tops (Blender side, mathutils only): the drum, ribbed dome, lantern and spire
EA repeats on the wall hub, the upgradeable plot, the wall tower, the fortress wall hub and the
arrow and garrison towers, in the citadel's language (men/fortress/crown.py): machicolated
galleries or flush parapets of square merlons, corbelled bartizans with slate spirelets on the
corners, a steel eave band, bold steel ribs, a lantern cupola, a gilt orb and a steel spike.

Owned by the walls group (assets/men/ROLLOUT.md); imported by the expansions. The API below is
stable: functions are added, never renamed or re-signed.

Every piece is laid out on a `Section`: the horizontal outline family of one tower (a regular
k-gon, or a chamfered square like the citadel's towers and EA's wall tower), centred at (cx, cy)
and measured by its HALF width across the flats (the apothem), so one Section serves every level
of a tower (shaft, belfry, eave, dome rings). Heights are the caller's (mesh coordinates of the
target, whatever its ground is).

    Section(cx, cy, k=8, phase=None, chamfer=None)
        .ring(half, z)          [V] the outline at z, counter-clockwise
        .path(half)             [(x, y)] the same, closed (first point repeated), for sweep()
        .faces(half)            [(a, t, n, L)] per face: start corner, along, outward normal, length
        .corners(half)          [(x, y, angle)] corner points and their outward angle (radians)
        .radius(half)           the corner radius
    Outline(points, base_half, cx, cy)   an explicit convex outline, scaled by half / base_half

    drum(sec, half, z0, z1, tags)                            a plain k-faceted drum
    moulding(sec, half, z, profile, tags)                    a ring moulding: [(d, dz)] out of the face
    eave_band(sec, half, z, h=1.0, d=(-0.5, 0.25))           the citadel's steel eave band
    dome(sec, levels, tag="slate", point=None)               a dome shell over [(z, half)]
    ribs(sec, levels, r=(0.34, 0.2), proud=0.2, mid=True)    steel ribs up the corners (and mid faces)
    parapet(kit, sec, half, z0, z1, d_in=-2.2, ...)          a flush parapet ring with square merlons
    gallery(kit, sec, half, z_corbel, ...)                   the citadel's machicolated gallery
    bartizans(kit, sec, R, z0, ...)                          corner turrets at radius R on the corners
    pilasters(sec, half, z0, z1, w=0.9, d=(-0.6, 0.9))       flat pilasters up the corners
    window_frames(kit, sec, half, z0, z1, w, ...)            arched window frames on the faces
                                                             (panel=False: round EA's real openings)
    crown(kit, sec, eave, levels, lantern, finial, ...)      eave band + ribs + lantern + finial
    spire(kit, cx, cy, z0, orb_z, tip, s=None)               mast, gilt orb, spike (scaled to fit)

`kit` is the faction's MenShapes (design(kit) receives it). Faces carry the Men atlas tags
(stoneA, stoneB, top, course, trim, gilt, slate, enamel, window, arcade).
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import box_rings, loft, prism_uz, sweep


class Section:
    """A tower's outline family. A regular k-gon (chamfer None): corners at phase + 2 pi i / k
    (default: faces toward the axes when k is 4 or 8, as shapes.ring). A chamfered square
    (chamfer = the chamfer's length as a fraction of `half`, the citadel's towers 0.28): 8 corners,
    long faces toward the axes, as box_rings."""

    def __init__(self, cx=0.0, cy=0.0, k=8, phase=None, chamfer=None):
        self.cx, self.cy, self.k, self.chamfer = cx, cy, (8 if chamfer else k), chamfer
        self.phase = math.pi / k if phase is None else phase

    def radius(self, half):
        if self.chamfer:
            return math.hypot(half, half * (1 - self.chamfer))
        return half / math.cos(math.pi / self.k)

    def ring(self, half, z):
        if self.chamfer:
            c = self.cx, self.cy
            return box_rings((c[0] - half, c[0] + half), (c[1] - half, c[1] + half), z, half * self.chamfer)
        r = self.radius(half)
        return [V((self.cx + r * math.cos(self.phase + 2 * math.pi * i / self.k),
                   self.cy + r * math.sin(self.phase + 2 * math.pi * i / self.k), z)) for i in range(self.k)]

    def path(self, half):
        pts = [(p.x, p.y) for p in self.ring(half, 0.0)]
        return pts + pts[:1]

    def faces(self, half):
        pts = self.ring(half, 0.0)
        out = []
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]
            t = (b - a).normalized()
            n = V((t.y, -t.x, 0))
            if n.dot((a + b) / 2 - V((self.cx, self.cy, 0))) < 0:
                n = -n
            out.append((a, t, n, (b - a).length))
        return out

    def corners(self, half):
        return [(p.x, p.y, math.atan2(p.y - self.cy, p.x - self.cx)) for p in self.ring(half, 0.0)]


class Outline(Section):
    """An explicit convex outline (points counter-clockwise about (cx, cy)) for an irregular tower
    (the wall trebuchet's platform): ring(half, z) scales it about its centre by half / base_half,
    so ring(base_half, z) is the outline itself. Everything laid on a Section takes it."""

    def __init__(self, points, base_half, cx=0.0, cy=0.0):
        super().__init__(cx, cy, k=len(points))
        self.points, self.base_half = [tuple(p) for p in points], base_half

    def radius(self, half):
        return max(math.hypot(x - self.cx, y - self.cy) for x, y in self.points) * half / self.base_half

    def ring(self, half, z):
        s = half / self.base_half
        return [V((self.cx + (x - self.cx) * s, self.cy + (y - self.cy) * s, z)) for x, y in self.points]


# ------------------------------------------------------------------ drums and mouldings
def drum(sec, half, z0, z1, tags="stoneA", cap0=("stoneB", False), cap1=("top", False)):
    """A plain drum from z0 to z1 (tags: one tag, or one per face)."""
    return [loft([sec.ring(half, z0), sec.ring(half, z1)], [tags], cap0=cap0, cap1=cap1)]


def moulding(sec, half, z, profile, tags, inner=-0.6):
    """A ring moulding round the face line at `half`: `profile` [(d, dz)] out of the face (d > 0 is
    proud), from z + dz; its inner side at d = inner (buried). One tag per profile edge (the last
    edge closes back to the start along the inside, buried)."""
    prof = [(inner, z + profile[0][1])] + [(d, z + dz) for d, dz in profile] + [(inner, z + profile[-1][1])]
    tg = [None] + list(tags) + [None, None]
    return sweep(sec.path(half), prof, tg, center=(sec.cx, sec.cy))[0]


def eave_band(sec, half, z, h=1.0, d=(-0.5, 0.25), tag="trim"):
    """The citadel's steel band round a dome's eave: from z - h/2 to z + h/2, d proud of `half`."""
    d0, d1 = d
    prof = [(d0, z - h / 2), (d1, z - h / 2), (d1, z + h / 2), (d0, z + h / 2 + 0.3)]
    return sweep(sec.path(half), prof, [tag] * 4, center=(sec.cx, sec.cy))[0]      # inner side kept: open above EA's eave


# ------------------------------------------------------------------ domes
def dome(sec, levels, tag="slate", point=None, base=("stoneB", False)):
    """A dome shell over rings [(z, half)] from the eave up; `point` (z) closes it in a point, else
    a flat top (buried: a lantern stands there)."""
    rings = [sec.ring(h, z) for z, h in levels]
    if point is not None:
        rings.append([V((sec.cx, sec.cy, point))] * len(rings[0]))
    return [loft(rings, [tag] * (len(rings) - 1), cap0=base, cap1=("top", point is None))]


def ribs(sec, levels, r=(0.34, 0.2), proud=0.2, mid=True, tag="trim"):
    """Steel ribs up a dome given as [(z, half)] from the eave up: one up every corner edge and
    (mid) one up the middle of every long face (for a chamfered square: the four long faces)."""
    from assets.men.shapes import rail
    rings = [sec.ring(h, z) for z, h in levels]
    k = len(rings[0])
    lines = [[rg[i] for rg in rings] for i in range(k)]
    if mid:
        L = [(rings[0][(i + 1) % k] - rings[0][i]).length for i in range(k)]
        for i in range(k):
            if L[i] > 0.6 * max(L):
                lines.append([(rg[i] + rg[(i + 1) % k]) / 2 for rg in rings])
    out = []
    for line in lines:
        pts = []
        for p in line:
            rad = V((p.x - sec.cx, p.y - sec.cy, 0))
            pts.append(p + (rad.normalized() * proud if rad.length > 1e-6 else V()) + V((0, 0, 0.08)))
        out.append(rail(pts, r[0], tag, r[1]))
    return out


# ------------------------------------------------------------------ parapets and galleries
def parapet(kit, sec, half, z0, z1, d_in=-2.2, d_out=0.0, band=None, merlon=None, skip=(), trim=0.15):
    """A parapet ring whose front is the face line at `half` + d_out (flush by default: nothing
    passes the tower's faces), from z0 (buried below) to z1, and square merlons with capstones on
    it. band: (z_a, z_b, tag) a band across the front (e.g. black enamel for StarBand's stars);
    merlon: kwargs for kit.merlons (w, gap, h, cap); skip: face indices without merlons (a
    turret or a wall stands there); trim: merlons kept this far from each face's corners."""
    c = (sec.cx, sec.cy)
    out = []
    if band:
        za, zb, tag = band
        prof = [(d_in, z0), (d_out, z0), (d_out, za), (d_out, zb), (d_out, z1), (d_in, z1)]
        tags = [None, "stoneA", tag, "stoneA", "top", "stoneB"]
    else:
        prof = [(d_in, z0), (d_out, z0), (d_out, z1), (d_in, z1)]
        tags = [None, "stoneA", "top", "stoneB"]
    prof, tags = _drop_flat(prof, tags)
    out += sweep(sec.path(half), prof, tags, center=c)[0]
    m = dict(w=2.4, gap=1.8, h=2.8, cap=0.55)
    m.update(merlon or {})
    for i, (a, t, n, L) in enumerate(sec.faces(half)):
        if i in skip or L < 2 * trim + m["w"]:
            continue
        a3 = V((a.x, a.y, 0))
        out += kit.merlons(a3, t, n, trim, L - trim, z1, d_out - 1.4, d_out - 0.2, **m)
    return out


def _drop_flat(prof, tags):
    """Drop repeated profile points (a band of zero height) with their edges."""
    p2, t2 = [], []
    for i, p in enumerate(prof):
        q = prof[(i + 1) % len(prof)]
        if abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6:
            continue
        p2.append(p)
        t2.append(tags[i])
    return p2, t2


def gallery(kit, sec, half, z_corbel, z_slab=None, z_walk=None, z_parapet=None, out=2.0, corbel_pitch=3.2,
            merlon=None, skip=(), enamel=True):
    """The citadel's machicolated gallery round a shaft of face line `half`: two-step corbels from
    z_corbel under a slab `out` proud (its front a black enamel band for StarBand's stars when
    `enamel`), a parapet on its edge and square merlons with capstones. Heights default to the
    citadel's spacing (slab 3.6 over the corbels' foot, walk 2.5 over it, parapet 1.7). skip: face
    indices left bare (a turret or a wall there); short faces (chamfers) carry no corbels."""
    zs = z_corbel + 3.6 if z_slab is None else z_slab
    zw = zs + 2.5 if z_walk is None else z_walk
    zp = zw + 1.7 if z_parapet is None else z_parapet
    c = (sec.cx, sec.cy)
    res = []
    slab = [(-2.5, zw - 0.7), (0.0, zs), (out, zs), (out, zw), (-2.5, zw)]
    res += sweep(sec.path(half), slab, ["stoneB", "stoneB", "enamel" if enamel else "stoneA", "top", None], center=c)[0]
    para = [(0.6, zw - 0.1), (out - 0.15, zw - 0.1), (out - 0.15, zp), (0.6, zp)]
    res += sweep(sec.path(half), para, [None, "stoneA", "top", "stoneA"], center=c)[0]
    m = dict(w=2.4, gap=1.75, h=2.8)
    m.update(merlon or {})
    faces = sec.faces(half)
    Lmax = max(f[3] for f in faces)
    for i, (a, t, n, L) in enumerate(faces):
        if i in skip:
            continue
        a3 = V((a.x, a.y, 0))
        if L > 0.6 * Lmax:
            k = max(1, int((L - 1.2) // corbel_pitch))
            u0 = (L - (k - 1) * corbel_pitch) / 2
            for j in range(k):
                res += kit.corbel(a3, t, n, u0 + j * corbel_pitch, z_corbel, z1=z_corbel + 1.8, z2=zs,
                                  d1=0.45 * out, d2=out - 0.05)
        if L >= 2.4 + 0.3:
            res += kit.merlons(a3, t, n, 0.15, L - 0.15, zp, 0.6, out - 0.15, **m)
    return res


# ------------------------------------------------------------------ corners
def bartizans(kit, sec, R, z0, r=2.05, h=9.8, spire=7.2, which=None):
    """Corbelled corner turrets (kit.bartizan: slit windows, a steel-banded cornice, a slate
    spirelet and a steel spike) on the Section's corners, their centres at radius R along each
    corner's direction, facing out: a k-gon's corners, or a chamfered square's four chamfers (the
    diagonals, as the citadel's). which: indices into those (default all). The turret's widest
    ring is r + 0.35 round its centre: keep R + r + 0.35 inside the footprint."""
    out = []
    if sec.chamfer:
        corners = [(0, 0, math.pi / 4 + i * math.pi / 2) for i in range(4)]
    else:
        corners = sec.corners(1.0)
    for i, (_, _, ang) in enumerate(corners):
        if which is not None and i not in which:
            continue
        x, y = sec.cx + R * math.cos(ang), sec.cy + R * math.sin(ang)
        out += kit.bartizan(x, y, z0, r=r, h=h, spire=spire, facing=ang)
    return out


def pilasters(sec, half, z0, z1, w=0.9, d=(-0.6, 0.9), base=True, which=None):
    """Flat pilasters up the corners of the face line `half` from z0 to z1 (w: half width across,
    d: from buried to proud along the corner's direction), a moulded base block when `base`."""
    out = []
    for i, (x, y, ang) in enumerate(sec.corners(half)):
        if which is not None and i not in which:
            continue
        n = V((math.cos(ang), math.sin(ang), 0))
        t = V((-n.y, n.x, 0))
        a = V((x, y, 0))
        out.append(prism_uz(a, t, n, [(-w, z0), (w, z0), (w, z1), (-w, z1)], d[0], d[1],
                            [None, "stoneB", "top", "stoneB"], "stoneA", None))
        if base:
            out.append(prism_uz(a, t, n, [(-w - 0.3, z0), (w + 0.3, z0), (w + 0.3, z0 + 1.2), (-w - 0.3, z0 + 1.2)],
                                d[0], d[1] + 0.3, ["stoneB", "stoneB", "top", "stoneB"], "course", None))
    return out


def window_frames(kit, sec, half, z0, z1, w, faces=None, d=(0.0, 0.7), glass=0.25, key=True, panel=True, rim=0.55):
    """A round-arched window on the middle of each face (faces: indices, default all long ones):
    a stone surround `rim` wide from z0 (sill) to the arch's crown z1, its opening (half width w)
    painted as EA's arched window (atlas 'window'; panel=False leaves the opening alone: a frame
    round one of EA's real openings), a moulded sill and a keystone."""
    out = []
    allf = sec.faces(half)
    Lmax = max(f[3] for f in allf)
    rise = min(w, (z1 - z0) * 0.4)
    spring = z1 - rise
    for i, (a, t, n, L) in enumerate(allf):
        if (faces is None and L < 0.6 * Lmax) or (faces is not None and i not in faces):
            continue
        a3, u = V((a.x, a.y, 0)) + t * (L / 2), 0.0      # anchored at the face's middle (voussoirs centre on u 0)
        arch = [(u + w * math.cos(math.pi * j / 8), spring + rise * math.sin(math.pi * j / 8)) for j in range(9)]
        opening = [(u - w, z0), (u + w, z0)] + arch
        if panel:
            out.append(prism_uz(a3, t, n, opening, d[0] - 0.3, d[0] + glass, [None] * len(opening), "window", None))
        for e in (-1, 1):
            out.append(prism_uz(a3, t, n, [(u + e * w, z0), (u + e * (w + rim), z0), (u + e * (w + rim), spring),
                                           (u + e * w, spring)], d[0] - 0.3, d[1],
                                ["stoneB"] * 4, "stoneA", None))
        out += kit.voussoirs(a3, t, n, (w, rise, spring), (w + rim, rise + rim, spring), d[0] - 0.3, d[1],
                             count=5, gap=0.06, key=(0.45, z1 + 0.9, 0.3) if key else None)
        out.append(prism_uz(a3, t, n, [(u - w - rim - 0.25, z0 - 0.6), (u + w + rim + 0.25, z0 - 0.6),
                                       (u + w + rim + 0.25, z0), (u - w - rim - 0.25, z0)], d[0] - 0.3, d[1] + 0.3, ["stoneB", "stoneB", "top", "stoneB"],
                            "course", None))
    return out


# ------------------------------------------------------------------ the citadel's dome crown
def crown(kit, sec, eave, levels, lantern=None, finial=None, rib=(0.34, 0.2), mid=True):
    """The citadel's dome crown on a dome given as [(z, half)] from its eave up: a steel eave band
    (eave: (half, z)), steel ribs, and optionally a lantern cupola (lantern: (z0, r, top), on the
    dome where it is about r + 0.8 across) and a steel mast, gilt orb and spike (finial:
    (orb_z, tip), from the lantern's top or the dome's last level)."""
    out = eave_band(sec, eave[0], eave[1])
    out += ribs(sec, levels, r=rib, mid=mid)
    z = levels[-1][0]
    if lantern:
        z0, r, top = lantern
        out += kit.lantern(sec.cx, sec.cy, z0, r=r, top=top)
        z = top - 0.1
    if finial:
        orb_z, tip = finial
        out += spire(kit, sec.cx, sec.cy, z, orb_z, tip)
    return out


def spire(kit, cx, cy, z0, orb_z, tip, s=None):
    """A steel mast from z0, a gilt orb at orb_z and a ringed steel spike to `tip`: the citadel's
    finial (kit.finial) when there is room (tip >= orb_z + 7.5), else the same scaled down by s
    (default: to fit) so its ring stays below the tip."""
    from assets.men.shapes import turned
    if s is None:
        s = min(1.0, max(0.35, (tip - orb_z) / 7.5))
    if s >= 1.0:
        return kit.finial(cx, cy, z0, orb_z, tip)
    return [turned(cx, cy, [(0.62 * s, z0), (0.62 * s, orb_z - 1.6 * s), (1.0 * s, orb_z - 1.4 * s), (1.0 * s, orb_z - s)],
                   ["trim"] * 3, k=6, cap0=("trim", False), cap1=("trim", True)),
            turned(cx, cy, [(0.8 * s, orb_z - s), (1.3 * s, orb_z - 0.4 * s), (1.3 * s, orb_z + 0.4 * s), (0.8 * s, orb_z + s),
                            (0.45 * s, orb_z + 1.3 * s)], ["gilt"] * 4, k=8, cap0=("gilt", True), cap1=("gilt", True)),
            turned(cx, cy, [(0.45 * s, orb_z + 1.2 * s), (0.3 * s, orb_z + 5.0 * s), (0.75 * s, orb_z + 5.3 * s),
                            (0.75 * s, orb_z + 5.8 * s), (0.28 * s, orb_z + 6.1 * s), (0.0, tip)],
                   ["trim"] * 5, k=6, cap0=("trim", True), cap1=("trim", False))]
