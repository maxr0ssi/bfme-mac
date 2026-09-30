"""The Mordor production buildings' pieces (Blender side): the citadel's family at the scale of an
orc pit, a slaughter house, a lumber mill, the siege works, the troll cage and the tavern. Module
functions of the kit (assets/mordor/shapes.py), every solid tagged with MordorAtlas regions.

The citadel's signature (assets/mordor/fortress/crown.py), sized for a building a fifth its height:
a claw of jagged hooked spikes rising from INSIDE a ring, a pit or a stack's mouth and closing round
real orange fire; never a bowl perched on a roof (it reads stuck on), never torches on prong tips,
never horns wrapping the outside. The big pieces (grounded stacks, the siege tower, the smoke rack,
the log ramp) are in shapes_production_big.py.

    claw(c, r0, z0, H, n, s)          n spikes round c from radius r0 at z0 leaning in to tips over the
                                      middle, H tall; tall and short in turn, a lava seam up each
                                      tall one's outer face, a steel outer edge, teeth hooking up
    ember_shelf(c, deg, r, z)         a basalt shelf heaped with coals, jutting in from a pit's wall
    claw_bar(base, centre, ...)       a hooked iron bar up a pen's wall and in over it, two barbs
    boss(c, s)                        a spiked iron boss (where a claw's chains meet)
    great_saw(c, t, top)              a two-man saw hung from a timber gantry across a log
    catapult(c, t)                    a half-built orc catapult: rails, A-frames, a clawed arm
    fire_pit(c, r, kind)              a ground fire in a ring of broken basalt teeth, a spit over it
    butcher_block(c, t)               a charred block, a steel cleaver bitten into it
    bone_heap(c, r)                   ash-grey bones and skulls heaped round a spike
    whip_post(c, h)                   a crooked iron post: a barbed head, a hanging chain and whip
    slope_crack(points)               a lava crack down a sloping face (3D points on it)
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz


def _v(p):
    return V((p[0], p[1], p[2] if len(p) > 2 else 0.0))


def _jit(seed, i, amp=0.18):
    return 1.0 + amp * math.sin(seed * 3.1 + i * 2.39)


# ------------------------------------------------------------------ the claw
def spike(kit, c, ang, r0, z0, r1, H, s=1.0, tall=True, seam=True):
    """One claw spike at `ang` degrees round c: from radius r0 at z0 up and in to its tip at r1,
    z0 + H; its section (outer, inner, half depth) s times the citadel's corner spikes'."""
    a = math.radians(ang)
    e = V((math.cos(a), math.sin(a), 0))
    f = V((-e.y, e.x, 0))
    c = V((c[0], c[1], 0))
    L = r0 - r1
    keys = [(z0 - 0.6, r0, (1.25 * s, 1.0 * s, 0.9 * s)), (z0 + 0.42 * H, r0 - 0.04 * L, (1.1 * s, 0.9 * s, 0.8 * s)),
            (z0 + 0.69 * H, r0 - 0.3 * L, (0.8 * s, 0.7 * s, 0.6 * s)), (z0 + 0.86 * H, r0 - 0.66 * L, (0.5 * s, 0.45 * s, 0.4 * s))]
    h = kit.Horn([(z, tuple((c + e * r)[:2]), sec) for z, r, sec in keys], e, f, c + e * r1 + V((0, 0, z0 + H)))
    teeth = [(z0 + 0.5 * H, 0.6), (z0 + 0.7 * H, 0.6)] if tall else [(z0 + 0.55 * H, 0.5)]
    hooks = [(z0 + (0.62 if tall else 0.7) * H, 0.35)]
    out = kit.horn(h, teeth=teeth, hooks=hooks, outer="steel", edge="stoneB", tag="stoneA")
    if tall and seam:
        pts = []
        for i in range(5):
            z = z0 + 0.12 * H + (0.62 * H) * i / 4
            Wo, _, D = h.section(z)
            k = (0.35, 0.6, 0.4, 0.65, 0.5)[i]
            pts.append(h.point(z, Wo * (1 - 0.6 * k), D * k))
        out += kit.face_crack(pts, h.e, w=0.55 * s, depth=0.25 * s)
    return out


def claw(kit, c, r0, z0, H, n=8, s=1.0, r1=None, phase=None, short=0.72, skip=()):
    """n spikes round c from radius r0 at z0, leaning in to tips at r1 (default 0.45 r0) H above;
    every other one `short` as tall and a little further out. `skip`: indices left out (a gap)."""
    r1 = r0 * 0.45 if r1 is None else r1
    phase = 180.0 / n if phase is None else phase
    out = []
    for k in range(n):
        if k in skip:
            continue
        tall = k % 2 == 0
        hh = H if tall else H * short
        rr = r1 if tall else r1 + (r0 - r1) * 0.3
        out += spike(kit, c, phase + 360.0 * k / n, r0, z0, rr, hh, s if tall else s * 0.8, tall)
    return out


# ------------------------------------------------------------------ pits
def _poly(c, r, z, k, seed, phase=0.0, amp=0.16):
    return [V((c[0] + r * _jit(seed, i, amp) * math.cos(2 * math.pi * i / k + phase),
               c[1] + r * _jit(seed, i, amp) * math.sin(2 * math.pi * i / k + phase), z)) for i in range(k)]


def ember_shelf(kit, c, deg, r, z, w=7.0, h=4.0, depth=6.0, seed=0.0):
    """A shelf of black basalt jutting in from a pit's wall at `deg` round c: its inner lip at r,
    its top at z heaped with glowing coals, w wide, h deep below its top, `depth` back into the wall."""
    a = math.radians(deg)
    e = V((math.cos(a), math.sin(a), 0))
    t = V((-e.y, e.x, 0))
    base = V((c[0], c[1], 0)) + e * r
    j = [_jit(seed, i, 0.25) for i in range(6)]
    poly = [(-w / 2, z - h), (w / 2 * j[0], z - h * 0.6), (w / 2 * j[1], z), (w * 0.15, z + 0.4 * j[2]), (-w / 2 * j[3], z)]
    out = [prism_uz(base, t, -e, poly, -depth, 1.2, ["stoneA", "stoneA", "ember", "ember", "stoneA"], "stoneB", "stoneA")]
    for i in range(3):
        u = (-0.3 + 0.3 * i) * w
        p = base + t * u - e * (0.2 + 0.4 * (i % 2)) + Z * (z + 0.2)
        out.append(kit.facet_lump(p, 0.9 + 0.3 * j[i + 2], "ember"))
    return out


# ------------------------------------------------------------------ ground fire
def fire_pit(kit, c, r, kind="hearth", smoke="smoke", spit=True, seed=0.0):
    """A ground fire at c in a ring of broken basalt teeth r across, a glowing bed, a spit on two
    forked iron posts over it (along x)."""
    c = _v(c)
    k = 7
    out = [loft([_poly(c, r * 0.95, c.z - 0.3, k, seed), _poly(c, r * 0.9, c.z + 0.5, k, seed)], ["rock"],
                cap0=("rock", False), cap1=("ember", True))]
    for i in range(k + 2):                               # the ring of teeth
        a = 2 * math.pi * i / (k + 2) + seed
        d = V((math.cos(a), math.sin(a), 0))
        p = c + d * r * _jit(seed, i, 0.1)
        hh = r * (0.45 + 0.25 * (0.5 + 0.5 * math.sin(seed + i * 1.7)))
        out.append(kit.tube([p - Z * 0.4, p + Z * hh * 0.6 + d * 0.2, p + Z * hh - d * r * 0.08],
                            [r * 0.2, r * 0.15, 0.0], "rock", k=4, cap0="rock", cap1=None, phase=a))
    for i in range(3):
        a = seed + i * 2.2
        out.append(kit.facet_lump(c + V((r * 0.35 * math.cos(a), r * 0.35 * math.sin(a), 0.6)), r * 0.22, "ember"))
    if spit:
        for sx in (-1, 1):
            f = c + V((sx * r * 1.15, 0, 0))
            out.append(kit.beam(f - Z * 0.4, f + Z * r * 1.1, 0.22, "iron"))
            out.append(kit.beam(f + Z * r * 1.1, f + Z * r * 1.45 + V((sx * 0.4, 0.5, 0)), 0.14, "iron", 0.0))
            out.append(kit.beam(f + Z * r * 1.1, f + Z * r * 1.45 + V((sx * 0.4, -0.5, 0)), 0.14, "iron", 0.0))
        out.append(kit.beam(c + V((-r * 1.35, 0, r * 1.15)), c + V((r * 1.35, 0, r * 1.15)), 0.14, "iron"))
        out.append(kit.tube([c + V((-r * 0.5, 0, r * 1.05)), c + V((0, 0, r * 0.95)), c + V((r * 0.5, 0, r * 1.05))],
                            [r * 0.2, r * 0.3, r * 0.18], "soot", k=5, cap0="soot", cap1="soot"))
    kit.fire(c + Z * 0.7, kind)
    if smoke:
        kit.fire(c + Z * (r * 1.6), smoke)
    return out


# ------------------------------------------------------------------ the butcher's yard
def great_saw(kit, c, t, top, span=8.5, h=26.0, blade=4.2):
    """A great two-man saw across a log at c (on the ground under the log's axis, t along the log,
    `top` the log's top z): two A-frames of charred timber either side (span out along the log's
    normal), a beam across at h with hooked barbs at its ends, the steel blade hung from it on two
    chains, `blade` tall, its hooked teeth bitten into the log's top."""
    c, t = _v(c), _v(t).normalized()
    n = V((-t.y, t.x, 0))
    out = []
    for s in (-1, 1):
        f = c + n * (s * span)
        for e in (-1, 1):
            out.append(kit.beam(f + t * (e * 3.2) + Z * 0.3, f + Z * h, 0.45, "wood"))
        out.append(kit.beam(f + t * -2.0 + Z * (h * 0.4), f + t * 2.0 + Z * (h * 0.4), 0.3, "iron"))
        tip = f + n * (s * 1.2) + Z * (h + 0.2)
        out += kit.barb(tip, n * s + Z * 0.8, 3.2, 0.35, tip="steel")
    out.append(kit.beam(c - n * (span + 1.2) + Z * h, c + n * (span + 1.2) + Z * h, 0.55, "wood"))
    zb, zt = top - 1.4, top + blade
    u0, u1 = -span + 1.6, span - 1.6
    a = V((c.x, c.y, 0))
    out.append(prism_uz(a, n, t, [(u0, zb), (u1, zb), (u1 - 0.6, zt), (u0 + 0.6, zt)], -0.18, 0.18, ["steel"] * 4,
                        "steel", "steel"))
    out.append(kit.beam(a + n * (u0 + 0.4) + Z * zt, a + n * (u1 - 0.4) + Z * zt, 0.3, "iron"))
    k = int((u1 - u0) / 1.1)
    for i in range(k):                                  # hooked teeth along its edge
        u = u0 + (u1 - u0) * (i + 0.5) / k
        out.append(prism_uz(a, n, t, [(u - 0.5, zb + 0.05), (u + 0.5, zb + 0.05), (u + 0.35, zb - 1.1)], -0.14, 0.14,
                            ["steel"] * 3, "steel", "steel"))
    for u in (u0 + 1.0, u1 - 1.0):                      # hung on chains from the beam
        out += kit.chain(a + n * u + Z * (h - 0.4), a + n * u + Z * (zt + 0.2), link=1.2, w=0.4, th=0.15)
    for u in (u0 - 0.2, u1 + 0.2):                      # handles
        out.append(kit.beam(a + n * u + Z * (zb + 1.0), a + n * (u * 1.12) + Z * (zt + 1.5), 0.28, "wood"))
    return out


def catapult(kit, c, t=(1, 0, 0), s=1.0):
    """A half-built orc catapult at c throwing along t: two charred rails, braced A-frames to an iron
    axle, the throwing arm cocked back and up with a hooked iron claw for its cup, a spiked iron
    counterweight on its short end, a chain winding it down to the rear."""
    c, t = _v(c), _v(t).normalized()
    n = V((-t.y, t.x, 0))
    P_ = lambda u, v, z: c + t * (u * s) + n * (v * s) + Z * (z * s)          # noqa: E731
    out = []
    for v in (-3.2, 3.2):
        out.append(kit.beam(P_(-8.5, v, 0.6), P_(8.5, v, 0.6), 0.5 * s, "wood"))
        for u in (-5.0, 5.0):
            out.append(kit.beam(P_(u, v, 0.6), P_(0.0, v, 9.0), 0.4 * s, "wood"))
        out.append(kit.beam(P_(-2.6, v, 4.8), P_(2.6, v, 4.8), 0.3 * s, "iron"))
    for u in (-7.5, 7.5):
        out.append(kit.beam(P_(u, -3.2, 0.8), P_(u, 3.2, 0.8), 0.35 * s, "wood"))
    out.append(kit.beam(P_(0.0, -4.2, 9.0), P_(0.0, 4.2, 9.0), 0.45 * s, "iron"))      # the axle
    top = P_(-9.0, 0.0, 23.0)
    out.append(kit.beam(P_(3.2, 0.0, 5.2), top, 0.6 * s, "wood", 0.42 * s))          # the arm
    d = (top - P_(3.2, 0.0, 5.2)).normalized()
    for k in range(3):                                   # the claw for a cup
        a = 2 * math.pi * k / 3 + 0.4
        o = (n * math.cos(a) + d.cross(n) * math.sin(a)).normalized()
        out += kit.barb(top - d * 0.6, (o + d * 0.6).normalized(), 3.2 * s, 0.3 * s, curl=0.7)
    w = P_(3.6, 0.0, 4.4)                                # the counterweight: a spiked iron block
    out.append(loft([_poly(w - Z * 2.2 * s, 2.2 * s, w.z - 2.2 * s, 4, 0.3, 0.4, 0.1),
                     _poly(w, 2.6 * s, w.z, 4, 0.3, 0.4, 0.1), _poly(w, 2.0 * s, w.z + 1.8 * s, 4, 0.3, 0.4, 0.1)],
                    ["iron", "iron"], cap0=("iron", True), cap1=("iron", True)))
    for k in range(4):
        a = math.pi / 2 * k + 0.4
        o = V((math.cos(a), math.sin(a), 0.3)).normalized()
        out.append(kit.beam(w + o * 2.0 * s, w + o * 3.8 * s, 0.25 * s, "steel", 0.0))
    out += kit.chain(top - d * 2.0, P_(-8.2, 0.0, 1.2), link=1.4, w=0.45, th=0.18)
    return out


def claw_bar(kit, base, centre, rise=36.0, tip=12.0, ztip=52.0, r=0.9):
    """A hooked iron claw bar from `base` (inside a pen's wall) up the wall's face to z `rise`, then in
    over the pen toward `centre` to a steel point `tip` from it at ztip, hooking down; two barbs."""
    base, centre = _v(base), _v(centre)
    e = V((base.x - centre.x, base.y - centre.y, 0))
    r0 = e.length
    e.normalize()
    C = V((centre.x, centre.y, 0))
    pts = [base, C + e * (r0 + 0.4) + Z * rise, C + e * (r0 * 0.78 + tip * 0.22) + Z * (ztip - 3.0),
           C + e * (tip + 3.0) + Z * (ztip + 0.6), C + e * tip + Z * (ztip - 1.4)]
    out = [kit.tube(pts, [r, r * 0.9, r * 0.75, r * 0.5, 0.0], ["iron", "iron", "iron", "steel"], k=4, cap0="iron",
                    cap1=None, phase=math.pi / 4)]
    for f, dz in ((0.45, 0.9), (0.75, 0.4)):
        p = pts[1].lerp(pts[2], f) if f < 0.6 else pts[2].lerp(pts[3], f - 0.3)
        out += kit.barb(p, (-e + Z * dz).normalized(), 3.4 * r, 0.32 * r, curl=0.6)
    return out


def boss(kit, c, s=2.0):
    """A spiked iron boss hanging at c: a faceted iron knot, steel spikes down and out."""
    c = _v(c)
    out = [kit.facet_lump(c, s, "iron")]
    for k in range(5):
        a = 2 * math.pi * k / 5
        d = V((math.cos(a), math.sin(a), -0.6)).normalized()
        out.append(kit.beam(c + d * s * 0.5, c + d * s * 2.2, 0.3 * s, "steel", 0.0))
    out.append(kit.beam(c - Z * s * 0.3, c - Z * s * 3.0, 0.35 * s, "steel", 0.0))
    return out


def butcher_block(kit, c, t=(1, 0, 0), s=1.0):
    """A charred block at c, its top stained, a steel cleaver bitten into it along t."""
    c, t = _v(c), _v(t).normalized()
    n = V((-t.y, t.x, 0))
    out = [loft([_poly(c, 1.5 * s, c.z - 0.3, 6, 1.0), _poly(c, 1.4 * s, c.z + 2.4 * s, 6, 1.0, 0.1)], ["wood"],
                cap0=("wood", False), cap1=("soot", True))]
    top = c + Z * (2.4 * s)
    blade = [(-1.3 * s, 2.3 * s - 0.6), (0.9 * s, 2.3 * s - 0.6), (1.1 * s, 2.3 * s + 1.4 * s), (-1.1 * s, 2.3 * s + 1.1 * s)]
    out.append(prism_uz(V((c.x, c.y, 0)) + n * 0.2, t, n, [(u, c.z + z) for u, z in blade], -0.12, 0.12,
                        ["steel"] * 4, "steel", "steel"))
    out.append(kit.beam(top + t * (-1.0 * s) + Z * (1.3 * s) + n * 0.2, top + t * (-2.6 * s) + Z * (2.0 * s) + n * 0.2,
                        0.18 * s, "wood"))
    return out


def bone_heap(kit, c, r=3.0, seed=0.0, spike=True):
    """Ash-grey bones and skulls heaped round a spike at c: a low heap, long bones jutting out of it."""
    c = _v(c)
    k = 7
    out = [loft([_poly(c, r, c.z - 0.2, k, seed, 0, 0.25), _poly(c, r * 0.6, c.z + r * 0.35, k, seed, 0.3, 0.25),
                 _poly(c, r * 0.2, c.z + r * 0.6, k, seed, 0.1, 0.25)], ["rock", "rock"], cap0=("rock", False),
                cap1=("rock", True))]
    for i in range(6):                                   # long bones, knobbed
        a = seed + i * 1.05
        d = V((math.cos(a), math.sin(a), 0.35 + 0.25 * math.sin(i * 2.0))).normalized()
        p = c + V((r * 0.3 * math.cos(a + 0.8), r * 0.3 * math.sin(a + 0.8), r * 0.3))
        q = p + d * r * (0.9 + 0.3 * math.sin(i))
        out.append(kit.beam(p, q, r * 0.07, "rock"))
        out.append(kit.facet_lump(q, r * 0.13, "rock"))
    for i in range(2):                                   # skulls
        a = seed + 0.5 + i * 3.1
        out.append(kit.facet_lump(c + V((r * 0.45 * math.cos(a), r * 0.45 * math.sin(a), r * 0.45)), r * 0.25, "stoneB"))
    if spike:
        out += kit.stake(c + V((0, 0, 0.5)), V((0.1, -0.05, 1.0)), r * 2.6, r=r * 0.14, barbs=1, seed=seed)
    return out


def whip_post(kit, c, h=9.0, seed=0.0):
    """A crooked iron post at c, h tall: a barbed head, an iron ring, a chain and a whip hanging."""
    c = _v(c)
    out = kit.stake(c, V((0.08, 0.05, 1.0)), h, r=0.45, barbs=2, seed=seed)
    ring = c + V((0.3, 0.2, h * 0.62))
    out += kit.chain(ring, ring + V((1.4, -0.6, -h * 0.45)), link=0.9, w=0.3, th=0.12)
    out.append(kit.tube([ring + V((-0.3, 0.3, 0)), ring + V((-0.9, 0.9, -h * 0.25)), ring + V((-0.6, 1.8, -h * 0.5))],
                        [0.14, 0.1, 0.0], "wood", k=4, cap0="wood", cap1=None))
    return out


def slope_crack(kit, points, w=1.2, depth=0.35, tag="ember", floor=0.0):
    """A lava crack over a sloping (or flat) surface through 3D points on it: a ribbon w wide at the
    first point tapering to a point at the last, its width level and square to the run, standing
    `depth` above the surface and sunk 0.5 below it (never below `floor`)."""
    pts = [_v(p) for p in points]
    out = []
    m = len(pts) - 1
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        s = V((q.y - p.y, p.x - q.x, 0))
        if s.length < 1e-6:
            continue
        s.normalize()
        w0, w1 = (w * (1 - i / m) + 0.15) / 2, (w * (1 - (i + 1) / m) + 0.15) / 2
        def ring(c, hw):
            lo = V((0, 0, max(c.z - 0.5, floor + 0.03) - c.z))     # never below the ground (floor)
            return [c - s * hw + lo, c + s * hw + lo, c + s * hw + Z * depth, c - s * hw + Z * depth]
        out.append(loft([ring(p, w0), ring(q, w1)], [tag], cap0=(tag, True), cap1=(tag, True)))
    return out
