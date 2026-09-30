"""The Harad group's pieces (Blender side): the Haradrim palace, the mumakil pen, the battle tower
and the barricade. Functions of the Mordor kit (assets/mordor/shapes.py), tagged with MordorAtlas
regions only. The citadel's family: claws of jagged spikes rising from inside a bowl round real
fire, black basalt split by lava, hard steel on the blades only. The Haradrim's own twist on it
(the palace and the pen): brass on rims and bands, war-paint red behind the suns, ivory tusk
trophies shod in steel, spiked howdah frames, sun-and-serpent banners whose cloth takes the
player's colour.

    claw(kit, c, specs, count, phase)          Horn spikes on a ring round c, leaning in over it
                                               (the citadel's crowns): tall and short by turns,
                                               a steel outer edge, teeth up, a hook down, lava seams
    jag_bowl(kit, c, z0, z1, r, kind, lip)     a jagged seven-sided iron fire bowl, a lit rim,
                                               hooked teeth up round it, embers in it; its fire
    tusk(kit, base, d0, d1, length, r)         a tusk trophy curving from d0 to d1: ivory (TUSK),
                                               brass bands, a steel-shod point
    tusk_through(kit, base, tip, out, bulge)   a tusk from base to tip, bowing out along `out`
    sun_serpent(kit, a, t, n, u, z, s, d)      the Harad sun (a disc and wavy rays) over a serpent
                                               in brass on a face
    harad_banner(kit, a, t, n, u, z_top, w, l)  a banner (cloth: the player's colour) on an iron
                                               frame with the sun and serpent in brass on it
    pier(kit, c, z0, z1, r, seams)             a jagged basalt pier (seven uneven sides) with lava
                                               seams: what the fire claws stand on
    tusk_claw(kit, c, z0, r0, count, L, r)     tusks rising round the axis c and curving in over it
                                               (the Harad claw round a fire bowl)
    howdah(kit, c, t, w, d, h)                 a spiked howdah frame: a charred timber deck and
                                               posts, brass rails, a pointed hood of ribs, steel
                                               spikes jutting from its corners
    stepped_plinth(kit, c, z0, tiers)          a stepped basalt plinth (uneven seven-sided tiers,
                                               ash treads, a lava seam): what a fire bowl sits on
    sun_plate(kit, a, t, n, u, z, s)           the Harad sun on a pointed war-paint plate

TUSK is the tusks' tag: the atlas's "bone" (ivory) when it has one, else "rock" (ash-grey); BRASS
the Harad brass ("brass", else the fire-lit "trim"), RED the Harad war-paint ("warpaint", else iron).
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz

from .atlas import MordorAtlas

TUSK = "bone" if "bone" in MordorAtlas.regions else "rock"
BRASS = "brass" if "brass" in MordorAtlas.regions else "trim"
RED = "warpaint" if "warpaint" in MordorAtlas.regions else "iron"


def _v(p):
    return V((p[0], p[1], p[2] if len(p) > 2 else 0.0))


# ---------------------------------------------------------------------- the claw round the fire
def claw(kit, c, specs, count=8, phase=45.0, seam=True, only=None):
    """`count` spikes round the axis c (x, y), by turns specs["tall"] and specs["short"], the first
    at `phase` degrees. A spec is ([(z, r, (outer, inner, half depth))], (tip r, tip z)): the spine
    at radius r from the axis at each z, leaning in to its tip. Teeth hook up the inner edge, a hook
    down the outer (steel) edge; the tall ones carry a lava seam up their outer face. only: the
    indices to build (others skipped: a spike that would stand in something)."""
    out = []
    cx, cy = c[0], c[1]
    for k in range(count):
        if only is not None and k not in only:
            continue
        size = "tall" if k % 2 == 0 else "short"
        keys, (rt, zt) = specs[size]
        a = math.radians(phase + 360.0 * k / count)
        e = V((math.cos(a), math.sin(a), 0))
        f = V((-e.y, e.x, 0))
        t = V((cx, cy, 0))
        h = kit.Horn([(z, tuple((t + e * r)[:2]), sec) for z, r, sec in keys], e, f, t + e * rt + V((0, 0, zt)))
        z0 = keys[0][0]
        H = zt - z0
        teeth = [(z0 + H * 0.5, 0.55), (z0 + H * 0.72, 0.5)] if size == "tall" else [(z0 + H * 0.6, 0.45)]
        hooks = [(z0 + H * 0.62, 0.35)]
        out += kit.horn(h, teeth=teeth, hooks=hooks, outer="steel", edge="stoneB", tag="stoneA")
        if seam and size == "tall":
            pts = []
            for i in range(5):
                z = z0 + H * (0.12 + 0.55 * i / 4)
                Wo, _, D = h.section(z)
                s = (0.35, 0.6, 0.4, 0.65, 0.5)[i]
                pts.append(h.point(z, Wo * (1 - 0.6 * s), D * s))
            out += kit.face_crack(pts, h.e, w=0.5, depth=0.22)
    return out


def jag_bowl(kit, c, z0, z1, r, kind="furnace", smoke=True, seed=0.0, teeth=7, lip="trim"):
    """A jagged fire bowl on the axis c from its foot at z0 to its rim at z1, r across the rim:
    seven uneven sides (never round), a lip of `lip` (the fire-lit trim; BRASS on the Harad pieces),
    embers heaped in it, hooked iron teeth rising
    from the rim and curling in; its fire (kind) and, if `smoke`, a dark smoke column above it."""
    c = V((c[0], c[1], 0))
    k = 7
    jit = [0.86 + 0.28 * (0.5 + 0.5 * math.sin(seed * 2.7 + i * 2.39)) for i in range(k)]

    def ring_(s, z, twist=0.0):
        return [c + V((r * s * jit[i] * math.cos(2 * math.pi * i / k + twist + seed),
                       r * s * jit[i] * math.sin(2 * math.pi * i / k + twist + seed), z)) for i in range(k)]
    h = z1 - z0
    rings = [ring_(0.3, z0), ring_(0.55, z0 + h * 0.3), ring_(0.86, z0 + h * 0.7), ring_(1.0, z1 - 0.5),
             ring_(1.04, z1), ring_(0.86, z1 + 0.15), ring_(0.8, z1 - 0.7)]
    out = [loft(rings, ["iron", "iron", "iron", lip, lip, lip], cap0=("iron", False), cap1=("ember", True))]
    out.append(kit.facet_lump(c + Z * (z1 - 0.2), r * 0.5, "ember"))
    rim = ring_(0.97, z1 - 0.2)
    for i in range(min(teeth, k)):                      # hooked teeth up round the rim, curling in
        p = rim[i]
        o = V((p.x - c.x, p.y - c.y, 0)).normalized()
        L = r * (0.9 + 0.35 * (i % 2))
        out.append(kit.tube([p - Z * 0.6, p + o * 0.35 + Z * L * 0.55, p - o * L * 0.3 + Z * L],
                            [r * 0.12, r * 0.08, 0.0], "iron", k=4, cap0="iron", cap1=None, phase=math.pi / 4))
    kit.fire(c + Z * (z1 + 0.3), kind)
    if smoke:
        kit.fire(c + Z * (z1 + 3.0), "smoke")
    return out


# ---------------------------------------------------------------------- tusk trophies
def tusk(kit, base, d0, d1, length, r, bands=2, tag=None, n=6):
    """A tusk from `base` leaving along d0 and ending along d1, `length` long, r thick at its root
    tapering to a steel-shod point; `bands` brass bands round it."""
    return tusk_path(kit, kit.arc(_v(base), _v(d0), _v(d1), length, n), r, bands, tag)


def tusk_through(kit, base, tip, out, bulge=0.25, r=1.5, bands=2, tag=None, n=7):
    """A tusk from `base` to `tip`, rising first and bowing out along the horizontal `out` by
    `bulge` of its rise before it turns in to its point."""
    base, tip, out = _v(base), _v(tip), V((out[0], out[1], 0)).normalized()
    h = tip.z - base.z
    p1 = base + Z * h * 0.45 + out * h * bulge
    p2 = tip - Z * h * 0.3 + out * h * bulge * 0.8
    pts = [base * (1 - s) ** 3 + p1 * 3 * s * (1 - s) ** 2 + p2 * 3 * s * s * (1 - s) + tip * s ** 3
           for s in (i / n for i in range(n + 1))]
    return tusk_path(kit, pts, r, bands, tag)


def tusk_path(kit, pts, r, bands=2, tag=None):
    """A tusk along pts: r thick at its root tapering to a steel-shod point, `bands` brass bands."""
    tag = tag or TUSK
    n = len(pts) - 1
    radii = [r * (1 - 0.8 * (i / n) ** 1.3) for i in range(n + 1)]
    radii[-1] = r * 0.24
    out = [kit.tube(pts, radii, tag, k=6, cap0=tag, cap1=tag)]
    tip_d = (pts[-1] - pts[-2]).normalized()
    out.append(kit.tube([pts[-1] - tip_d * 0.2, pts[-1] + tip_d * r * 2.6], [r * 0.3, 0.0], "steel", k=4, cap0="steel",
                        cap1=None, phase=math.pi / 4))
    for j in range(bands):
        i = 1 + j * max(1, (n - 2) // max(bands, 1))
        p, q = pts[i], pts[i + 1]
        dd = (q - p).normalized()
        rr = radii[i] + (radii[i + 1] - radii[i]) * 0.3
        out.append(kit.tube([p + dd * 0.2, p + (q - p) * 0.45], [rr * 1.12, rr * 1.1], BRASS, k=6, cap0=BRASS,
                            cap1=BRASS))
    return out


# ---------------------------------------------------------------------- the sun and the serpent
def _stroke(p, q, w):
    """A convex quad w wide from p to q (points in u, z)."""
    du, dz = q[0] - p[0], q[1] - p[1]
    L = math.hypot(du, dz) or 1.0
    nu, nz = -dz / L * w / 2, du / L * w / 2
    return [(p[0] + nu, p[1] + nz), (p[0] - nu, p[1] - nz), (q[0] - nu, q[1] - nz), (q[0] + nu, q[1] + nz)]


def sun_serpent(kit, a, t, n, u, z, s, d=0.0, th=0.35, tag=None, serpent=True, back=None, closed=True):
    """The Harad sun `s` across centred at (u, z) on a face (a, t, n), standing th proud of d: a
    ten-sided disc and ten wavy rays; under it a serpent in an S, its head raised. back: the tag
    closing it behind (None: buried in what it stands on; on cloth, which leaves for the house-colour
    model, it must be closed)."""
    tag = tag or BRASS
    back = back or (tag if closed else None)
    a, t, n = V(a), V(t), V(n)
    out = []
    R = s * 0.28
    disc = [(u + R * math.cos(2 * math.pi * i / 10), z + R * math.sin(2 * math.pi * i / 10)) for i in range(10)]
    out.append(prism_uz(a, t, n, disc, d - 0.1, d + th, [tag] * 10, tag, back))
    for i in range(10):                                  # rays: flame tongues, alternately long and short
        ang = 2 * math.pi * (i + 0.5) / 10
        L = s * (0.5 if i % 2 == 0 else 0.4)
        cu, sz = math.cos(ang), math.sin(ang)
        tu, tz = -sz, cu
        b = (u + R * 1.05 * cu, z + R * 1.05 * sz)
        mid = (u + (R + (L - R) * 0.55) * cu + tu * s * 0.05, z + (R + (L - R) * 0.55) * sz + tz * s * 0.05)
        tip = (u + L * cu, z + L * sz)
        w = s * 0.07
        out.append(prism_uz(a, t, n, [(b[0] - tu * w, b[1] - tz * w), (b[0] + tu * w, b[1] + tz * w), mid], d - 0.1, d + th,
                            [tag] * 3, tag, back))
        out.append(prism_uz(a, t, n, [(mid[0] - tu * w * 0.7, mid[1] - tz * w * 0.7), (mid[0] + tu * w * 0.7,
                                                                                        mid[1] + tz * w * 0.7), tip],
                            d - 0.1, d + th, [tag] * 3, tag, back))
    if serpent:                                          # an S of strokes under the sun, the head at the right
        zs = z - s * 0.62
        pts = [(u - s * 0.5 + s * i / 8, zs + s * 0.12 * math.sin(i * math.pi / 2.6)) for i in range(9)]
        for i, (p, q) in enumerate(zip(pts, pts[1:])):
            out.append(prism_uz(a, t, n, _stroke(p, q, s * (0.08 + 0.05 * i / 8)), d - 0.1, d + th, [tag] * 4, tag,
                                back))
        hu, hz = pts[-1]
        head = [(hu - s * 0.02, hz - s * 0.07), (hu + s * 0.15, hz - s * 0.02), (hu + s * 0.16, hz + s * 0.05),
                (hu - s * 0.02, hz + s * 0.09)]
        out.append(prism_uz(a, t, n, head, d - 0.1, d + th, [tag] * 4, tag, back))
    return out


def harad_banner(kit, a, t, n, u, z_top, width, length, d=1.2):
    """A banner of the player's colour (cloth) `width` wide hung `length` from an iron frame d out
    from a face (the kit's banner), the sun and serpent in brass on it."""
    a, t, n = V(a), V(t), V(n)
    out = kit.banner(a, t, n, u, z_top, width, length, d=d, mark=False)
    s = min(width * 0.8, length * 0.5)
    out += sun_serpent(kit, a, t, n, u, z_top - length * 0.36, s, d=d + 0.15, th=0.25)
    return out


# ---------------------------------------------------------------------- the howdah
def howdah(kit, c, t, w=7.0, d=5.0, h=6.0, spikes=True, hood=True, cloth=True, legs=0.0, spike_sides=(-1, 1),
           walls=False, canopy=False):
    """A spiked howdah frame at c (its foot), its long axis along t: a charred timber deck on
    cross-beams, four iron-shod corner posts, brass rails at two heights, a pointed hood of four
    ribs meeting in an iron finial, a cloth hanging (the player's colour) on the side facing -n,
    and long steel spikes jutting out and up from the deck's corners on `spike_sides` of it (-1: the
    -n side); `legs` > 0: timber cribs under the deck's corners that far down; `walls`: charred
    timber walls up to the lower rail; `canopy`: the hood a solid pointed canopy of the player's
    colour (cloth) instead of bare ribs."""
    c, t = _v(c), V((t[0], t[1], 0)).normalized()
    n = V((-t.y, t.x, 0))
    P = lambda u, v, z: c + t * u + n * v + Z * z          # noqa: E731
    hw, hd = w / 2, d / 2
    out = [prism_uz(c, t, n, [(-hw, 0.9), (hw, 0.9), (hw, 1.8), (-hw, 1.8)], -hd, hd, ["wood"] * 4, "wood", "wood")]
    for s in (-1, 1):                                    # cross-beams under the deck
        out.append(kit.beam(P(s * hw * 0.6, -hd - 0.4, 0.5), P(s * hw * 0.6, hd + 0.4, 0.5), 0.45, "wood"))
    corners = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
    for cu, cv in corners:                               # corner posts, iron-capped
        out.append(kit.beam(P(cu, cv, 0.0), P(cu, cv, h), 0.32, "wood"))
        out.append(kit.beam(P(cu, cv, h - 0.4), P(cu, cv, h + 0.9), 0.4, "iron", 0.0))
    for z in (h * 0.45, h * 0.85):                       # brass rails
        for (u0, v0), (u1, v1) in zip(corners, corners[1:] + corners[:1]):
            out.append(kit.beam(P(u0, v0, z), P(u1, v1, z), 0.2, BRASS))
    if walls:                                            # charred timber walls to the lower rail
        for (u0, v0), (u1, v1) in zip(corners, corners[1:] + corners[:1]):
            a0, a1 = P(u0, v0, 1.8), P(u1, v1, 1.8)
            tt = (a1 - a0).normalized()
            nn = V((tt.y, -tt.x, 0))
            L = (a1 - a0).length
            out.append(prism_uz(a0, tt, nn, [(0.3, 1.8), (L - 0.3, 1.8), (L - 0.3, h * 0.45), (0.3, h * 0.45)], -0.25, 0.25,
                                ["wood"] * 4, "wood", "wood"))
    if hood:                                             # a pointed hood of ribs
        apex = P(0, 0, h + d * 0.9)
        for cu, cv in corners:
            out.append(kit.beam(P(cu, cv, h + 0.6), apex, 0.24, "iron"))
        if canopy:
            ring = [P(cu * 1.08, cv * 1.08, h + 0.5) for cu, cv in corners]
            out.append(loft([ring, [apex - Z * 0.4] * 4], ["cloth"], cap0=("cloth", True), cap1=("cloth", False)))
        out.append(kit.beam(apex - Z * 0.3, apex + Z * 2.4, 0.36, BRASS, 0.0))
    if cloth:                                            # a hanging on the -n side, under the upper rail
        out.append(prism_uz(c, t, n, [(-hw + 0.5, h * 0.3), (hw - 0.5, h * 0.3), (hw - 0.5, h * 0.8), (0, h * 0.86),
                                      (-hw + 0.5, h * 0.8)], -hd - 0.15, -hd + 0.1, ["cloth"] * 5, "cloth", "cloth"))
    if legs > 0:                                         # timber cribs under the corners
        for cu, cv in corners:
            out.append(prism_uz(c, t, n, [(cu - 0.7, 1.0 - legs), (cu + 0.7, 1.0 - legs), (cu + 0.7, 1.0), (cu - 0.7, 1.0)],
                                cv - 0.7, cv + 0.7, ["wood"] * 4, "wood", "wood"))
    if spikes:                                           # steel spikes jutting from the deck's corners
        for cu, cv in corners:
            if math.copysign(1, cv) not in spike_sides:
                continue
            o = (t * math.copysign(1, cu) + n * math.copysign(1, cv)).normalized()
            p = P(cu, cv, 1.4)
            out.append(kit.tube([p - o * 0.5, p + o * w * 0.28 + Z * 0.8, p + o * w * 0.5 + Z * 2.4], [0.4, 0.26, 0.0],
                                "steel", k=4, cap0="steel", cap1=None, phase=math.pi / 4))
    return out


# ---------------------------------------------------------------------- piers and tusk claws
def pier(kit, c, z0, z1, r, seams=2, seed=0.0):
    """A jagged basalt pier on c from z0 (buried) to z1, r across its top: seven uneven sides
    battered out to its foot, a rock cap, lava seams glowing up `seams` of its faces."""
    c = V((c[0], c[1], 0))
    k = 7
    jit = [0.84 + 0.3 * (0.5 + 0.5 * math.sin(seed * 1.9 + i * 2.13)) for i in range(k)]

    def ring_(s, z):
        return [c + V((r * s * jit[i] * math.cos(2 * math.pi * i / k + seed), r * s * jit[i] * math.sin(2 * math.pi * i / k + seed),
                       z)) for i in range(k)]
    out = [loft([ring_(1.3, z0), ring_(1.12, z0 + (z1 - z0) * 0.55), ring_(1.0, z1 - 0.6), ring_(0.9, z1)],
                ["stoneA", "stoneA", "rock"], cap0=("stoneA", False), cap1=("rock", True))]
    for j in range(seams):
        i = (2 * j + 1) % k
        a0, a1 = ring_(1.0, 0), ring_(1.0, 0)
        p, q = a0[i], a1[(i + 1) % k]
        mid = (p + q) / 2 - c
        n = V((mid.x, mid.y, 0)).normalized()
        pts = []
        for m in range(5):
            f = m / 4
            s = 1.3 - 0.3 * f
            ang = 2 * math.pi * (i + 0.5 + 0.18 * math.sin(m * 1.7 + j)) / k + seed
            z = z0 + 0.5 + (z1 - z0 - 1.2) * f
            pts.append(c + V((r * s * math.cos(ang) * 0.98, r * s * math.sin(ang) * 0.98, z)))
        out += kit.face_crack(pts, n, w=0.7, depth=0.3)
    return out


def tusk_claw(kit, c, z0, r0, count=6, length=14.0, r=0.9, phase=0.0, short=0.75, splay=0.35, inward=0.45):
    """`count` tusks rising from a ring r0 round the axis c at z0, leaving upward and a little out
    (`splay`) and curving in over the axis, by turns full and `short` length: the Harad claw round a
    fire."""
    c = V((c[0], c[1], z0))
    out = []
    for i in range(count):
        a = math.radians(phase + 360.0 * i / count)
        e = V((math.cos(a), math.sin(a), 0))
        L = length * (1.0 if i % 2 == 0 else short)
        out += tusk(kit, c + e * r0 - Z * 1.2, e * splay + Z, -e * inward + Z * 0.9, L, r * (1.0 if i % 2 == 0 else 0.85),
                    bands=2 if i % 2 == 0 else 1)
    return out


# ---------------------------------------------------------------------- plinths and gable suns
def stepped_plinth(kit, c, z0, tiers, seed=0.0, k=7, seam=True):
    """A stepped basalt plinth on the axis c from z0 (buried): tiers [(r, z_top)] from the widest
    up, each an uneven seven-sided block (never round) battered a little, black basalt sides ("stoneA"), ash
    treads ("rock"); a lava seam glowing down the lowest tier's front."""
    c = V((c[0], c[1], 0))
    jit = [0.8 + 0.36 * (0.5 + 0.5 * math.sin(seed * 2.3 + i * 2.7)) for i in range(k)]

    def ring_(r, z):
        return [c + V((r * jit[i] * math.cos(2 * math.pi * (i + 0.5) / k + seed), r * jit[i] * math.sin(2 * math.pi * (i + 0.5) / k + seed),
                       z)) for i in range(k)]
    out = []
    zb = z0
    for j, (r, zt) in enumerate(tiers):
        out.append(loft([ring_(r * 1.06, zb), ring_(r, zt - 0.4), ring_(r * 0.96, zt)], ["stoneA", "rock"],
                        cap0=("stoneA", False), cap1=("rock", True)))
        if seam and j == 0:
            for i in (1, 4):
                a = 2 * math.pi * (i + 0.5) / k + seed
                e = V((math.cos(a), math.sin(a), 0))
                pts = [c + e * (r * jit[i] * (1.07 - 0.06 * f)) + V((0, 0, zt - 0.6 - (zt - max(zb, z0 + 0.5) - 0.8) * f))
                       + V((-e.y, e.x, 0)) * (0.6 * math.sin(f * 5 + i)) for f in (0.0, 0.3, 0.6, 1.0)]
                out += kit.face_crack(pts, e, w=0.8, depth=0.3)
        zb = zt - 0.5
    return out


def sun_plate(kit, a, t, n, u, z, s, d=0.0, serpent=False):
    """The Harad sun `s` across at (u, z) on a face (a, t, n) on a pointed plate of war-paint red a little
    larger than it (its foot 0.62 s below the centre, its point 0.75 s above)."""
    a, t, n = V(a), V(t), V(n)
    w = s * 1.1
    poly = [(u - w / 2, z - s * 0.62), (u + w / 2, z - s * 0.62), (u + w / 2, z + s * 0.25), (u, z + s * 0.75),
            (u - w / 2, z + s * 0.25)]
    out = [prism_uz(a, t, n, poly, d - 0.8, d, [RED] * 5, RED, RED)]
    out += sun_serpent(kit, a, t, n, u, z, s, d=d, th=0.5, serpent=serpent, closed=False)
    return out
