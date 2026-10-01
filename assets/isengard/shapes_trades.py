"""The Isengard production group's trade pieces (pass 4, 2026-09-30): each building's own work in
place of the needle stacks and blade pairs pass 3 stamped on everything ("our furnace towers on
everything look a lil stupid", Max). Functions of the kit (`kit` is the faction's IsengardShapes,
assets/isengard/shapes.py), as in shapes_industry.py: closed solids tagged with IsengardAtlas
regions; every fire records its point through kit.fire. Machined, black and silver, the Hand.

    smelter_stack(kit, c, r, z0, z1, rot)    a heavy square smelter stack rising out of a building's
                                             own mass: stepped stone courses, riveted iron plates
                                             between riveted bands, a heavy collar on brackets, a
                                             flared mouth round a glowing throat, a charging jib
                                             and ore skip (fire: chimney)
    grind_wheel(kit, c, t, r)                a grinding wheel: a stone disc with a silver rim on an
                                             iron axle between two A-frames, a crank, a trough of
                                             water under it, a blade on the rest (fire: embers)
    bone_heap(kit, c, r, seed)               gnawed bones on a trodden mound: long bones with
                                             knuckled ends, a standing ribcage, skulls
    tether(kit, c, r, chains)                an iron-shod stake with a ring, chains out to spiked
                                             collars lying in the dirt
    hide_frame(kit, c, t, w, h)              a crude orc hide laced into an iron frame, the White
                                             Hand daubed on it
    roof_hide(kit, top, t, down, w, L)       a crude hide pinned flat on a roof slope by iron pegs
    spit_fire(kit, c, t, r)                  a cook-fire with a spit and a haunch (fire: hearth)
    mud_pool(kit, c, r, seed)                a pool of birthing mud: a ragged soot kerb, wet black
                                             mud sunk inside, slick puddles
    fangorn_trunk(kit, p, q, r)              a felled giant of Fangorn: its root plate, a tapering
                                             trunk, broken limbs, iron dogs and a chain
    trunk_saw(kit, c, t, top, h)             a great frame saw straddling a trunk, the blade in the cut
    slash_pyre(kit, c, r)                    Fangorn's limbs burning on a glowing bed (fire: hearth)
    pit_gantry(kit, c, t, span, h, drop)     an iron gantry: two A-frames, a riveted top beam, a
                                             winch, a chain to a great hook (or a slung log)
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz

from .shapes_industry import _tn, _v, quench_trough


def smelter_stack(kit, c, r, z0, z1, rot=52.0, jib=None, crown=None, rivets=True):
    """A heavy smelter stack on c, square in plan with a corner at `rot` degrees, r the shaft's
    half-diagonal, from z0 (inside what it rises out of) to its mouth at z1:

        base    two battered, stepped courses of black stone flaring into the building (r * 1.4
                at z0), silver ledges
        shaft   straight iron faces clad in riveted plates in three courses between riveted bands
        collar  a heavy riveted collar under the mouth on corner brackets
        mouth   a flared rim, a silver lip round a deep glowing throat, short iron blades at the
                rim's corners (fire: chimney)
        jib     (angle, reach, drop): a charging jib out of the collar, a chain down to a skip of
                glowing ore

    rivets=False: the plates, bands and collar without rivet heads (a smaller stack seen from afar,
    about 1,400 triangles less). shapes_spire.needle_stack is not this."""
    c = _v(c)
    a = math.radians(rot)
    sq = lambda s, z: kit.square(c, r * s, z, a)                                  # noqa: E731
    H = z1 - z0
    zb1, zb2 = z0 + H * 0.12, z0 + H * 0.3
    zr = z1 - 3.4                                            # the rim's foot
    zc = zr - 3.6                                            # the collar's middle
    out = [loft([sq(1.40, z0 - 0.4), sq(1.28, zb1), sq(1.18, zb1), sq(1.12, zb2), sq(1.12, zb2 + 0.9), sq(1.0, zb2 + 0.9),
                 sq(1.0, zr), sq(1.16, zr + 1.4), sq(1.2, z1), sq(0.84, z1), sq(0.8, z1 - 3.6)],
                ["stoneA", "trim", "stoneA", "trim", "trim", "iron", "iron", "iron", "trim", "ember"],
                cap0=("stoneA", False), cap1=("ember", True))]
    band = lambda z, h, g: loft([sq(0.96, z - h / 2 - 0.2), sq(1.0 + g, z - h / 2), sq(1.0 + g, z + h / 2),    # noqa: E731
                                 sq(0.96, z + h / 2 + 0.2)], ["iron"] * 3, cap0=("iron", False), cap1=("iron", False))
    zs = zb2 + 0.9
    bands = [zs + (zc - 1.6 - zs) * f for f in (1 / 3, 2 / 3)]
    out += [band(z, 1.0, 0.05) for z in bands] + [band(zc, 3.0, 0.14)]
    hw = r * 0.7071
    courses = [(zs + 0.2, bands[0] - 0.6), (bands[0] + 0.6, bands[1] - 0.6), (bands[1] + 0.6, zc - 1.8)]
    for k in range(4):                                       # each face: plates, the collar's rivets, a corbel
        dm = V((math.cos(a + math.pi / 4 + math.pi / 2 * k), math.sin(a + math.pi / 4 + math.pi / 2 * k), 0))
        t = V((-dm.y, dm.x, 0))
        m = V((c.x, c.y, 0)) + dm * hw
        for za, zb in courses:
            out += kit.plate(m, t, dm, -hw + 0.7, hw - 0.7, za, zb, d=0.0, th=0.35, pitch=2.6, rivet=0.26 if rivets else 0)
        if rivets:
            out += kit.rivets(m, t, dm, [(u * hw, zc) for u in (-0.6, -0.2, 0.2, 0.6)], (1.14 - 1.0) * hw * 1.0 + 0.0, 0.34)
            out += kit.rivets(m, t, dm, [(u * hw, z) for u in (-0.55, 0.0, 0.55) for z in bands], 0.05 * hw, 0.24)
        out.append(prism_uz(m, t, dm, [(-1.0, zs + 1.0), (1.0, zs + 1.0), (1.0, zs + 3.4), (0.0, zs + 5.0), (-1.0, zs + 3.4)],
                            -0.4, 0.3, ["ember"] * 5, "ember", "ember"))              # a pointed tap-hole
        cr = V((math.cos(a + math.pi / 2 * k), math.sin(a + math.pi / 2 * k), 0))
        p = V((c.x, c.y, 0)) + cr * (r * 1.0)
        out.append(kit.beam(p + Z * (zc - 7.0) - cr * 0.6, p + Z * (zc - 1.4) + cr * 1.0, 0.45, "iron"))   # a corner bracket
    crown = r * 0.6 if crown is None else crown
    for k in range(4):                                       # short iron blades at the rim's corners
        d = V((math.cos(a + math.pi / 2 * k), math.sin(a + math.pi / 2 * k), 0))
        p = V((c.x, c.y, 0)) + d * (r * 1.12)
        out += kit.blade(p - d * 1.4, d, z1 - 2.0, z1 + crown * 0.3, 1.2, 0.6, w=1.1, tip=crown * 0.7, back=1.8,
                         tag="iron", edge="trim")
    if jib:                                                  # a charging jib out of the collar, an ore skip on its chain
        ang, reach, drop = jib
        d = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
        s = V((-d.y, d.x, 0))
        root = V((c.x, c.y, zc + 1.0)) + d * (hw * 1.1)
        tip = root + d * reach
        for e in (-1, 1):
            out.append(kit.beam(root + s * (e * 0.8), tip + s * (e * 0.5), 0.4, "iron"))
            out.append(kit.beam(root + s * (e * 0.8) - Z * 8.0, tip + s * (e * 0.4) - Z * 0.4, 0.3, "iron"))
        out.append(kit.beam(tip - s * 0.9, tip + s * 0.9, 0.5, "trim"))
        out += kit.chain(tip - Z * 0.5, tip - Z * drop, link=1.4)
        sk = tip - Z * (drop + 2.4)
        skr = lambda w, z: [sk + d * w + s * w + Z * z, sk - d * w + s * w + Z * z, sk - d * w - s * w + Z * z,   # noqa: E731
                            sk + d * w - s * w + Z * z]
        out.append(loft([skr(1.0, 0.0), skr(1.6, 2.4), skr(1.8, 2.4), skr(1.8, 2.8), skr(1.4, 2.8), skr(1.4, 2.2)],
                        ["iron", "iron", "trim", "iron", "ember"], cap0=("iron", True), cap1=("ember", True)))
        out.append(kit.facet_lump(sk + Z * 2.8, 1.1, "ember"))
        for e in (-1, 1):
            out += kit.chain(tip - Z * drop, sk + s * (e * 1.6) + Z * 2.8, link=1.0)
    kit.fire(V((c.x, c.y, z1 - 0.8)), "chimney")
    return out


def grind_wheel(kit, c, t, r=3.2, w=1.5):
    """A grinding wheel at c (ground), turning in the plane of t: a stone disc r across with silver
    rims on an iron axle (along n) between two iron A-frames, a crank on its +n end, a trough of
    water under its foot, and a blade laid on an iron rest against its +t face, where the sparks
    fly (fire: embers)."""
    c = _v(c)
    t, n = _tn(t)
    hub = c + Z * (r + 1.0)
    out = [kit.tube([hub - n * (w / 2), hub + n * (w / 2)], [r, r], "stoneB", k=12, cap0="stoneA", cap1="stoneA")]
    for e in (-1, 1):                                        # silver rims either side of the stone
        m = hub + n * (e * (w / 2 + 0.1))
        out.append(kit.tube([m - n * 0.15, m + n * 0.15], [r * 1.04, r * 1.04], "trim", k=12, cap0="trim", cap1="trim"))
    out.append(kit.beam(hub - n * (w / 2 + 2.2), hub + n * (w / 2 + 2.4), 0.28, "iron"))
    for e in (-1, 1):                                        # the A-frames
        m = hub + n * (e * (w / 2 + 1.4))
        for s in (-1, 1):
            out.append(kit.beam(m + t * (s * r * 0.95) - Z * (r + 1.3), m + Z * 0.3, 0.3, "iron"))
        out.append(kit.beam(m + Z * 0.3, m + Z * 1.6, 0.34, "trim", 0.0))
    k = hub + n * (w / 2 + 2.4)                              # the crank
    out.append(kit.beam(k, k - Z * 1.6, 0.18, "iron"))
    out.append(kit.beam(k - Z * 1.6, k - Z * 1.6 + n * 1.2, 0.16, "timber"))
    out += quench_trough(kit, c + Z * 0.0, t, r * 1.3, w + 1.4, 1.2)
    bite = hub + t * (r + 0.1)
    rest = bite + t * 0.4 - Z * 0.5
    out.append(kit.beam(rest + t * 0.2 - n * 1.2, rest + t * 0.2 + n * 1.2, 0.2, "iron"))
    out.append(kit.beam(rest + t * 1.8 - Z * (rest.z - c.z + 0.3), rest + t * 0.2, 0.24, "iron"))
    out.append(kit.beam(bite + t * 0.15 - n * 0.2, bite + t * 2.6 + Z * 0.5 - n * 0.2, 0.16, "trim"))
    kit.fire(bite + t * 0.3, "embers")
    return out


def _jit(seed, i, j=0):
    return 0.5 + 0.5 * math.sin(seed * 3.7 + i * 2.3 + j * 1.9)


def bone_heap(kit, c, r, seed=0.0, bones=9, skulls=3, ribs=True, tag="rock"):
    """Gnawed bones heaped on a low trodden mound r across at c: `bones` long bones lying every
    way with knuckled ends, a ribcage standing out of the heap (ribs), `skulls` skulls. Grey, not
    the Goblins' bleached bone (tag)."""
    c = _v(c)
    k = 7
    rings = [[c + V((r * (0.85 + 0.25 * _jit(seed, i)) * math.cos(2 * math.pi * i / k),
                     r * (0.85 + 0.25 * _jit(seed, i)) * math.sin(2 * math.pi * i / k), -0.2)) for i in range(k)],
             [c + V((r * 0.45 * math.cos(2 * math.pi * i / k + 0.3), r * 0.45 * math.sin(2 * math.pi * i / k + 0.3),
                     r * 0.22)) for i in range(k)]]
    out = [loft(rings, ["soot"], cap0=("soot", False), cap1=("soot", True))]
    for i in range(bones):
        ang = seed + i * 2.39
        d = V((math.cos(ang), math.sin(ang), 0))
        p = c + d * (r * 0.55 * _jit(seed, i, 1)) + Z * (r * 0.12 + 0.3 * (i % 3))
        L = r * (0.45 + 0.35 * _jit(seed, i, 2))
        q = V((-d.y, d.x, 0)) * math.cos(ang * 1.3) + d * math.sin(ang * 1.3)
        a, b = p - q * L / 2, p + q * L / 2 + Z * (0.4 * math.sin(ang))
        out.append(kit.beam(a, b, 0.22 + r * 0.02, tag))
        for e in (a, b):
            out.append(kit.facet_lump(e, 0.45 + r * 0.03, tag))
    if ribs:                                                 # a ribcage standing out of the heap
        spine_a = c + V((-r * 0.35, -r * 0.1, r * 0.25))
        spine_b = c + V((r * 0.3, r * 0.15, r * 0.3))
        out.append(kit.beam(spine_a, spine_b, 0.3, tag))
        ax = (spine_b - spine_a).normalized()
        side = V((-ax.y, ax.x, 0))
        for i in range(5):
            m = spine_a.lerp(spine_b, (i + 0.5) / 5)
            h = r * (0.55 - 0.06 * abs(i - 2))
            for s in (-1, 1):
                pts = [m, m + side * (s * h * 0.45) + Z * (h * 0.35), m + side * (s * h * 0.55) - Z * (h * 0.2),
                       m + side * (s * h * 0.35) - Z * (h * 0.5)]
                out.append(kit.tube(pts, [0.2, 0.18, 0.15, 0.06], tag, k=4, cap0=tag, cap1=None))
    for i in range(skulls):
        ang = seed + 1.1 + i * 2.1
        p = c + V((math.cos(ang), math.sin(ang), 0)) * (r * 0.7) + Z * 0.5
        out.append(kit.facet_lump(p, 1.0, tag))
        out.append(kit.beam(p, p + V((math.cos(ang), math.sin(ang), 0)) * 1.4 - Z * 0.3, 0.42, tag, 0.2))   # the snout
    return out


def tether(kit, c, r=6.0, chains=3, seed=0.0, h=7.0):
    """An iron-shod stake at c, h tall, a ring near its top, `chains` chains slung out to spiked
    collars lying in the dirt r out."""
    c = _v(c)
    out = [kit.beam(c - Z * 0.25, c + Z * h, 0.55, "iron"), kit.beam(c + Z * h, c + Z * (h + 2.0), 0.6, "trim", 0.0)]
    out += kit.hoop((c.x, c.y), c.z + h * 0.7, 0.9, h=0.7, th=0.35, inner=0.3, k=6, rivets=False, tag="trim", closed=True)
    for i in range(chains):
        ang = seed + 2 * math.pi * i / chains
        d = V((math.cos(ang), math.sin(ang), 0))
        end = c + d * (r * (0.8 + 0.3 * _jit(seed, i))) + Z * 0.4
        out += kit.chain(c + Z * (h * 0.7) + d * 1.1, end, link=1.4)
        out += kit.hoop((end.x, end.y), end.z, 1.1, h=0.6, th=0.35, inner=0.3, k=6, rivets=False, tag="iron", closed=True)
        for j in range(3):                                   # the collar's spikes
            b = ang + 2 * math.pi * j / 3
            e = V((math.cos(b), math.sin(b), 0))
            p = end + e * 1.3
            out.append(kit.beam(p, p + (e + Z * 0.4).normalized() * 1.2, 0.16, "iron", 0.0))
    return out


def hide_frame(kit, c, t, w=6.0, h=8.0, hand=True, seed=0.0):
    """A crude orc hide laced into an iron frame at c (ground), the hide's face toward n: two iron
    posts with pointed silver tips, top and foot bars, the hide's ragged outline stretched between
    them on lacing, the White Hand daubed on it."""
    c = _v(c)
    t, n = _tn(t)
    out = []
    z0, z1 = c.z + 1.2, c.z + h
    for e in (-1, 1):
        p = c + t * (e * (w / 2 + 0.6))
        out.append(kit.beam(p - Z * 0.4, p + Z * (h + 0.6), 0.3, "iron"))
        out.append(kit.beam(p + Z * (h + 0.6), p + Z * (h + 2.4), 0.36, "trim", 0.0))
    for z in (z0 - 0.4, z1 + 0.4):
        out.append(kit.beam(V((c.x, c.y, z)) - t * (w / 2 + 0.9), V((c.x, c.y, z)) + t * (w / 2 + 0.9), 0.22, "iron"))
    hw = w / 2 - 0.2                                         # the hide: a ragged, roughly stretched outline
    poly = [(-hw * 0.8, z0), (-hw * 0.15, z0 + 0.6), (hw * 0.5, z0 - 0.1), (hw, z0 + 0.8), (hw * 0.9, (z0 + z1) * 0.5),
            (hw * 1.05, z1 - 0.6), (hw * 0.3, z1), (-hw * 0.4, z1 - 0.4), (-hw, z1 - 0.2), (-hw * 0.92, (z0 + z1) * 0.45)]
    poly = [(u + 0.25 * math.sin(seed + i), z) for i, (u, z) in enumerate(poly)]
    m = V((c.x, c.y, 0))
    out.append(prism_uz(m, t, n, poly, -0.15, 0.15, ["timber"] * len(poly), "timber", "timber"))
    for u, z in (poly[0], poly[3], poly[5], poly[8]):         # lacing from the hide's corners to the frame
        p = m + t * u + Z * z
        q = m + t * ((w / 2 + 0.6) * (1 if u > 0 else -1)) + Z * (z + (0.3 if z > c.z + h / 2 else -0.3))
        out.append(kit.beam(p, q, 0.08, "chain"))
    if hand:
        out += kit.hand(m, t, n, 0.0, z0 + (z1 - z0) * 0.22, (z1 - z0) * 0.55, 0.15, th=0.05)
    return out


def roof_hide(kit, top, t, down, w, L, seed=0.0, pegs=True):
    """A crude hide pinned flat on a roof slope: its top edge's middle at `top` (on the roof), t
    along the ridge, `down` the unit vector down the slope; w wide, L long, a ragged outline, an
    iron peg with a silver head through each corner."""
    top, t, down = _v(top), V(t).normalized(), V(down).normalized()
    nrm = t.cross(down).normalized()
    if nrm.z < 0:
        nrm = -nrm
    k = 10
    pts = []
    for i in range(k):                                       # a rough oval with ragged edges
        a = 2 * math.pi * i / k
        rr = 0.82 + 0.25 * _jit(seed, i)
        pts.append((math.cos(a) * w / 2 * rr, (1 - math.sin(a)) * L / 2 * (0.9 + 0.1 * rr)))
    ring = lambda off: [top + t * u + down * v + nrm * off for u, v in pts]          # noqa: E731
    out = [loft([ring(0.1), ring(0.45)], ["timber"], cap0=("timber", False), cap1=("timber", True))]
    if pegs:
        for i in (1, 4, 6, 9):
            u, v = pts[i]
            p = top + t * (u * 0.85) + down * (v * 0.92 + L * 0.04)
            out.append(kit.beam(p - nrm * 0.6, p + nrm * 1.2, 0.22, "iron"))
            out.append(kit.beam(p + nrm * 1.2, p + nrm * 1.9, 0.38, "trim", 0.1))
    return out


def spit_fire(kit, c, t, r=3.0):
    """A cook-fire at c: a ring of charred stones round a glowing bed, two forked iron posts
    either side along t, a spit across them with a haunch on it and a crank (fire: hearth)."""
    c = _v(c)
    t, n = _tn(t)
    out = [loft([kit.ring(c.x, c.y, r * 1.05, c.z - 0.3, 7), kit.ring(c.x, c.y, r * 0.95, c.z + 0.8, 7),
                 kit.ring(c.x, c.y, r * 0.72, c.z + 0.8, 7), kit.ring(c.x, c.y, r * 0.72, c.z + 0.3, 7)],
                ["soot", "soot", "ember"], cap0=("soot", False), cap1=("ember", True))]
    h = r * 1.6
    for e in (-1, 1):
        p = c + t * (e * (r + 0.6))
        out.append(kit.beam(p - Z * 0.4, p + Z * h, 0.26, "iron"))
        for s in (-1, 1):                                    # the fork
            out.append(kit.beam(p + Z * h, p + Z * (h + 1.0) + n * (s * 0.5), 0.16, "iron", 0.05))
    a, b = c - t * (r + 1.6) + Z * (h + 0.3), c + t * (r + 1.6) + Z * (h + 0.3)
    out.append(kit.beam(a, b, 0.14, "iron"))
    out.append(kit.beam(b, b - Z * 1.0, 0.12, "iron"))
    m = c + Z * (h + 0.3)
    out.append(kit.tube([m - t * (r * 0.5), m, m + t * (r * 0.45)], [r * 0.2, r * 0.32, r * 0.16], "timber", k=6,
                        cap0="timber", cap1="timber"))
    kit.fire(c + Z * 1.0, "hearth")
    return out


def mud_pool(kit, c, r, seed=0.0, puddles=4):
    """A pool of birthing mud r across at c: a ragged kerb of soot-black spoil, wet black mud sunk
    inside it, slick puddles catching the light."""
    c = _v(c)
    k = 9
    rr = [r * (0.85 + 0.3 * _jit(seed, i)) for i in range(k)]
    ring = lambda s, z, ph=0.0: [c + V((rr[i] * s * math.cos(2 * math.pi * i / k + ph), rr[i] * s * math.sin(2 * math.pi * i / k + ph),
                                        z)) for i in range(k)]                    # noqa: E731
    out = [loft([ring(1.15, -0.3), ring(1.0, 1.0), ring(0.82, 1.1), ring(0.78, 0.4)], ["soot", "soot", "soot"],
                cap0=("soot", False), cap1=("soot", True))]
    for i in range(puddles):
        ang = seed + i * 2.5
        p = c + V((math.cos(ang), math.sin(ang), 0)) * (r * 0.4 * _jit(seed, i, 3)) + Z * 0.45
        s = r * (0.16 + 0.08 * _jit(seed, i, 4))
        out.append(loft([kit.ring(p.x, p.y, s, p.z - 0.1, 6), kit.ring(p.x, p.y, s * 0.8, p.z + 0.08, 6)], ["water"],
                        cap0=("water", False), cap1=("water", True)))
    return out


def fangorn_trunk(kit, p, q, r, roots=7, seed=0.0):
    """A felled giant of Fangorn from its root plate at p to its sawn crown end at q (r: the
    trunk's radius at the roots): a seven-sided trunk tapering to q, gnarled roots splaying from
    the plate, two broken limbs, iron dogs (staples) driven in along it and a chain round it."""
    p, q = _v(p), _v(q)
    ax = (q - p).normalized()
    side = V((-ax.y, ax.x, 0)).normalized()
    up = ax.cross(side).normalized()
    if up.z < 0:
        up = -up
    out = [kit.tube([p, p.lerp(q, 0.15), q], [r * 1.25, r, r * 0.72], "timber", k=7, cap0="timber", cap1="timber",
                    phase=seed)]
    for i in range(roots):                                   # the root plate: roots splaying round p
        a = seed + 2 * math.pi * i / roots
        d = (side * math.cos(a) + up * math.sin(a)).normalized()
        L = r * (1.8 + 0.8 * _jit(seed, i))
        pts = [p + ax * (r * 0.6), p + d * (r * 1.2) - ax * (r * 0.2), p + d * L - ax * (r * 0.6) + Z * (-0.4 * r)]
        if pts[-1].z < 0.2 + min(p.z, q.z) - r:
            pts[-1].z = 0.2 + min(p.z, q.z) - r
        out.append(kit.tube(pts, [r * 0.42, r * 0.28, r * 0.08], "timber", k=5, cap0="timber", cap1="timber"))
    for f, s in ((0.45, 1), (0.7, -1)):                      # broken limbs, stubs up and out
        b = p.lerp(q, f)
        d = (up * 0.8 + side * (s * 0.6)).normalized()
        rr = r * (1.0 - 0.28 * f)
        out.append(kit.tube([b, b + d * (rr * 1.6), b + d * (rr * 2.4) + ax * (rr * 0.4)], [rr * 0.45, rr * 0.36, rr * 0.3],
                            "timber", k=5, cap0="timber", cap1="timber"))
    for f in (0.3, 0.58, 0.86):                              # iron dogs, and a chain round the trunk
        b = p.lerp(q, f)
        rr = r * (1.0 - 0.28 * f) + 0.15
        out.append(kit.beam(b + up * rr - side * 0.8, b + up * rr + side * 0.8, 0.22, "iron"))
    b = p.lerp(q, 0.72)
    rr = r * 0.8 + 0.3
    ring = [b + (side * math.cos(2 * math.pi * i / 6) + up * math.sin(2 * math.pi * i / 6)) * rr for i in range(7)]
    for a, b2 in zip(ring, ring[1:]):
        out += kit.chain(a, b2, link=1.0, w=0.35, th=0.15)
    return out


def trunk_saw(kit, c, t, top, h, w=2.8):
    """A great frame saw straddling a trunk at c (ground), cutting across t (the trunk's axis): two
    iron-shod timber posts either side, a top beam, a tensioning bar, the silver blade down into
    the cut at z top (the trunk's top), wedges driven in behind it."""
    c = _v(c)
    t, n = _tn(t)
    out = []
    for s in (-1, 1):
        out.append(kit.beam(c + n * (s * w) - Z * 0.4, c + n * (s * w) + Z * h, 0.45, "timber"))
        out.append(kit.beam(c + n * (s * w) - Z * 0.4, c + n * (s * w) + Z * 2.0, 0.6, "iron"))
        out.append(kit.beam(c + n * (s * w) + Z * h, c + n * (s * w) + Z * (h + 1.8), 0.4, "trim", 0.0))
    out.append(kit.beam(c - n * (w + 0.8) + Z * h, c + n * (w + 0.8) + Z * h, 0.5, "timber"))
    out.append(kit.beam(c - n * w + Z * (h * 0.78), c + n * w + Z * (h * 0.78), 0.3, "iron"))
    out.append(prism_uz(V((c.x, c.y, 0)), n, t, [(-w + 0.4, top - 1.2), (w - 0.4, top - 1.2), (w - 0.4, h - 0.5),
                                                 (-w + 0.4, h - 0.5)], -0.12, 0.12, ["trim"] * 4, "trim", "trim"))
    for s in (-1, 1):                                        # iron wedges in the cut behind the blade
        out.append(kit.beam(c + t * 0.5 + n * (s * 0.8) + Z * (top + 1.2), c + t * 0.5 + n * (s * 0.8) + Z * (top - 0.6),
                            0.35, "iron", 0.05))
    return out


def slash_pyre(kit, c, r, seed=0.0, limbs=8):
    """Fangorn's limbs burning: a heap of crossed branches r across at c on a ring of charred
    stones, a glowing bed under them (fire: hearth)."""
    c = _v(c)
    out = [loft([kit.ring(c.x, c.y, r * 1.05, c.z - 0.3, 7), kit.ring(c.x, c.y, r * 0.95, c.z + 0.6, 7),
                 kit.ring(c.x, c.y, r * 0.7, c.z + 0.6, 7), kit.ring(c.x, c.y, r * 0.7, c.z + 0.2, 7)],
                ["soot", "soot", "ember"], cap0=("soot", False), cap1=("ember", True))]
    for i in range(limbs):
        a = seed + i * 2.4
        d = V((math.cos(a), math.sin(a), 0))
        p = c + d * (r * 0.95) + Z * 0.2
        q = c - d * (r * 0.25) + Z * (r * (0.7 + 0.4 * _jit(seed, i)))
        out.append(kit.tube([p, q], [0.45, 0.25], "timber", k=5, cap0="timber", cap1="timber"))
    out.append(kit.facet_lump(c + Z * 1.0, r * 0.35, "ember"))
    kit.fire(c + Z * 1.0, "hearth")
    return out


def pit_gantry(kit, c, t, span, h, drop=None, hook=3.0, log=None):
    """An iron gantry over a pit at c: an A-frame of iron at each end (pointed silver caps), a
    riveted top beam with a silver lip, a winch at one foot with its cable up the frame, a trolley
    and a chain down `drop` to a great hook (or, log=(length, r), a trunk slung across n)."""
    c = _v(c)
    t, n = _tn(t)
    out = []
    for e in (-1, 1):
        top = c + t * (e * span / 2) + Z * h
        for s in (-1, 1):
            out.append(kit.beam(c + t * (e * span / 2) + n * (s * h * 0.3) + Z * 0.1, top, 0.5, "iron"))
        out.append(kit.beam(c + t * (e * span / 2) - n * h * 0.2 + Z * h * 0.35,
                            c + t * (e * span / 2) + n * h * 0.2 + Z * h * 0.35, 0.35, "iron"))
        out.append(kit.beam(top + Z * 0.9, top + Z * 3.6, 0.6, "trim", 0.0))
    a, b = c - t * (span / 2 + 1.0) + Z * (h + 0.6), c + t * (span / 2 + 1.0) + Z * (h + 0.6)
    out.append(kit.beam(a, b, 0.75, "iron"))
    out.append(kit.beam(a + Z * 0.75, b + Z * 0.75, 0.3, "trim"))
    m = c + t * (span * 0.08) + Z * (h - 0.3)
    out.append(kit.beam(m - t * 1.0 - Z * 0.2, m + t * 1.0 - Z * 0.2, 0.55, "iron"))
    drop = drop if drop is not None else h * 0.55
    out += kit.chain(m - Z * 0.7, m - Z * drop, link=1.8, w=0.6, th=0.25)
    if log:
        length, r = log
        lg = m - Z * (drop + r + 1.2)
        out.append(kit.tube([lg - n * length / 2, lg + n * length / 2], [r, r * 0.9], "timber", k=7, cap0="timber",
                            cap1="timber"))
        for s in (-1, 1):
            out += kit.chain(m - Z * drop, lg + n * (s * length * 0.25) + Z * r, link=1.2)
    else:
        out += kit.hook(m - Z * drop, hook, chain=0.0)
    foot = c + t * (span / 2) + n * (h * 0.3 + 2.4)
    out += kit.cable_drum(foot, t, 1.2, 3.0)
    out.append(kit.cable(foot + Z * 2.4, c + t * (span / 2) + Z * h, sag=0.6))
    return out
