"""The Angmar army buildings' pieces (Blender side): the barracks, the den, the kennel, the Hall of
Twilight and the catapult works. Module functions of the kit (assets/angmar/shapes.py, the `kit`
argument), every solid tagged with AngmarAtlas regions; bone is "trim" (the palette's pale
slate-to-rime bone ramp), frost "rime", crystal "ice", black stone "rock", cold glow "ember".

Each building gets ONE bold piece of its own story (Max: the same motif on every building reads as
clones), its fire out of that piece (a pit, a crater, a maw), never on a tip like a torch:

    thrall_gantry(c, t, span, h, cages)  the thrall-master's gantry: A-frames of iron-banded legs on
                                        stone plinths, two beams under a rimed deck hung with icicles,
                                        iron cages with frozen captives, cold braziers at its feet
    fire_pit(c, r)                      a kerb of black stone blocks round an iron grate of coals
    warg_skull(c, f, L)                 a great frozen warg skull, L long, looking along f: faceted
                                        cranium and snout, open jaws with ice fangs, frost in the eye
                                        sockets, rime and crystals on the crown
    jaw_arch(c, n, span, h)             two warg tusks rising either side of a gate and crossing over
                                        it, iron-banded, teeth of ice along their inner edges
    rune_stone(c, out, w, d, h)         a rune stone or menhir: a leaning, slant-cut monolith of black
                                        stone, rime on its cut, cold runes (or one great rune,
                                        great_rune) down its outer face
    altar(c, out, s)                    a stepped black stone altar, rune bands, a crater of ice and
                                        stone shards on top for the cold fire
    hoarding(c, a0, a1, r0, r1, z0, z1)  a frozen timber gallery round a tower's top: plank floor and
                                        boards with loopholes, a shingled lean-to, icicles, struts
    gantry(c, t, span, h, loads)        the frozen timber gantry: A-frame trestles under a heavy rimed
                                        beam, ice boulders hanging from it in iron slings
    boulder(c, s), boulder_heap(c, r)   angular ice boulders (never round), heaped in a timber crib
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft


# EA's lowest z on the building being designed: nothing new goes below it (a footing sunk past EA's
# ground deepens the model, which the height check fails); a recipe sets it before its pieces
GROUND = [-1e9]


def floor(z):
    """Set EA's ground (the target's lowest z) for the pieces that follow."""
    GROUND[0] = z


def _f(z):
    return max(z, GROUND[0])


def _v(p):
    return V((p[0], p[1], p[2] if len(p) > 2 else 0.0))


def _h(*xs):
    v = math.sin(sum(x * (12.9898 + 7.233 * i) for i, x in enumerate(xs))) * 43758.5453
    return v - math.floor(v)


def _flat(d):
    """The horizontal unit of d and the unit square to it (left of it)."""
    f = V((d[0], d[1], 0)).normalized()
    return f, V((-f.y, f.x, 0))


def block(c, f, s, w, d, z0, z1, tag="stoneA", top=None, ch=0.0, taper=1.0):
    """A block w along f, d along s, round c (x, y) from z0 to z1, chamfered `ch`, its top
    `taper` times its foot; top: the top cap's tag (default `tag`)."""
    c = V((c[0], c[1], 0))

    def ring(z, k):
        a, b = w / 2 * k, d / 2 * k
        e = ch * k
        pts = [(a - e, -b), (a, -b + e), (a, b - e), (a - e, b), (-a + e, b), (-a, b - e), (-a, -b + e), (-a + e, -b)] \
            if ch > 0 else [(a, -b), (a, b), (-a, b), (-a, -b)]
        return [c + f * u + s * v + Z * z for u, v in pts]
    z0 = _f(z0)
    return loft([ring(z0, 1.0), ring(z1, taper)], [tag], cap0=(tag, False), cap1=(top or tag, True))


# ------------------------------------------------------------------ the barracks
def frozen_cage(kit, top, h, w, seed=0.0):
    """A gibbet cage hanging from `top` with a captive frozen inside: the figure cased in a column
    of ice crystals, rime on the cage's cap, icicles off its foot."""
    top = _v(top)
    out = kit.cage(top, h, w)
    foot = top - Z * (h - 1.0)
    body = foot + Z * 0.6
    out.append(kit.beam(body, body + V((0.15, 0.1, h * 0.5)), w * 0.32, "soot", w * 0.22))
    out.append(kit.facet_lump(body + V((0.2, 0.1, h * 0.58)), w * 0.24, "soot"))
    for i in range(4):                                  # the ice that holds him: crystals up through the cage
        a = 2 * math.pi * (i / 4 + 0.13 * _h(seed, i))
        p = body + V((math.cos(a) * w * 0.32, math.sin(a) * w * 0.26, 0.0))
        out += kit.shard(p, V((math.cos(a) * 0.12, math.sin(a) * 0.12, 1.0)), h * (0.45 + 0.2 * _h(seed + 1, i)),
                         w * 0.28, k=4 + i % 2, seed=seed + i, bury=0.4)
    for i in range(3):                                  # icicles off the foot
        a = 2 * math.pi * i / 3 + seed
        q = foot + V((math.cos(a) * w * 0.35, math.sin(a) * w * 0.3, 0.2))
        ring = [q + V((0.35, 0, 0)), q + V((-0.2, 0.3, 0)), q + V((-0.2, -0.3, 0))]
        out.append(loft([ring, [q - Z * (1.8 + 1.4 * _h(seed, i))] * 3], ["ice"], cap0=("ice", False),
                        cap1=("ice", False)))
    return out


def thrall_gantry(kit, c, t, span, h, cages, post=4.4, splay=5.0, braziers=(), reach=6.0, seed=0.0):
    """The thrall-master's gantry across c (x, y, ground z) along t, its front toward -n (n left of
    t): at each end a rimed stone plinth and an A-frame of two heavy iron-banded legs raking in from
    `splay` either side, a cross-tie; over them one heavy timber beam h up, iron-strapped, knee
    braces, rime along its top, icicles under it; cages [(u along t, drop, cage height)] hang on
    chains from iron arms reaching `reach` out of its front, each with a captive frozen inside;
    braziers [(u, out)] are cold-fire claws on stone plinths at its feet (out: toward the front)."""
    c, (t, n) = _v(c), _flat(t)
    out = []
    g = c.z
    deep = post * 1.2                                   # the beam's depth across
    for e in (-1, 1):
        p = c + t * (e * span / 2)
        out.append(block(p, t, n, post + 4.0, 2 * splay + post + 3.0, g - 0.8, g + 7.0, "stoneA", top="rime", ch=1.0,
                         taper=0.85))
        for k in (-1, 1):
            foot = p + n * (k * splay) + Z * (6.6 - p.z + g)
            head = p + n * (k * deep * 0.25) + Z * (h - p.z + g)
            out.append(kit.beam(foot, head, post / 2, "timber"))
            for f in (0.06, 0.5, 0.9):                  # iron bands
                q = foot.lerp(head, f)
                ax = (head - foot).normalized()
                out.append(kit.beam(q - ax * 0.8, q + ax * 0.8, post / 2 + 0.4, "iron"))
        tie = p + Z * (g + h * 0.5 - p.z)
        out.append(kit.beam(tie - n * (splay * 0.6 + 1.0), tie + n * (splay * 0.6 + 1.0), post * 0.38, "timber"))
        out.append(kit.beam(p + Z * (g + h - 13.0 - p.z), p - t * (e * 11.0) + Z * (g + h - p.z), post * 0.32,
                            "timber"))                  # a knee brace out along the beam
        out.append(block(p, t, n, post + 1.4, deep + 0.8, g + h - 0.5, g + h + post * 1.3 + 0.5, "iron", ch=0.25))
    L = span + 9.0
    top = g + h + post * 1.3
    out.append(block(c, t, n, L, deep, g + h, top, "timber", ch=0.4))
    out.append(block(c, t, n, L + 0.8, deep + 0.9, top - 0.2, top + 0.9, "rime", ch=0.4))
    for k in (-1, 1):
        out += kit.icicles(c - t * (L / 2 - 1.0) + n * (k * deep * 0.5), t, n * k, 0.0, L - 2.0, g + h + 0.2, 4.4,
                           int(L / 2.6), d=0.0, crust=0.8, w=1.2, seed=seed + k)
    for i, (u, drop, ch) in enumerate(cages):
        root = c + t * u - n * (deep * 0.5 - 0.6) + Z * (g + h + post * 0.65 - c.z)
        end = root - n * reach
        out.append(kit.beam(root + n * 1.4, end, 0.75, "iron"))                     # the arm out of the beam
        out.append(kit.beam(root - Z * (post * 0.65 + 4.0), end + n * 1.2, 0.5, "iron"))     # its brace
        out.append(kit.beam(end, end - n * 1.2 + Z * 1.6, 0.5, "steel", 0.0))          # a hooked point
        out += kit.chain(end, end - Z * drop, link=1.8, w=0.65, th=0.26)
        out += frozen_cage(kit, end - Z * drop, ch, ch * 0.29, seed=seed + i * 1.7)
    for i, (u, d) in enumerate(braziers):
        q = c + t * u - n * d
        out.append(block(q, t, n, 6.0, 6.0, g - 0.8, g + 4.2, "stoneA", top="rime", ch=0.8, taper=0.85))
        out += kit.cold_brazier((q.x, q.y, g + 4.2), r=2.4, h=7.5, seed=seed + 3 + i)
    return out


def fire_pit(kit, c, r=3.6, h=2.4, kind="coldflame", seed=0.0):
    """A ground fire pit at c: a kerb of seven black stone blocks round an iron grate heaped with
    coals; the fire's point over the coals."""
    c = _v(c)
    out = []
    for i in range(7):
        a = 2 * math.pi * (i + 0.3 * _h(seed, i)) / 7
        f = V((math.cos(a), math.sin(a), 0))
        out.append(block(c + f * r, f, V((-f.y, f.x, 0)), 2.2, r * 0.85, c.z - 0.6, c.z + h * (0.8 + 0.4 * _h(seed + 1, i)),
                         "rock", top="rime", ch=0.4, taper=0.8))
    for e in (-1, 0, 1):                                # the grate
        out.append(kit.beam(c + V((-r * 0.8, e * r * 0.38, h * 0.55)), c + V((r * 0.8, e * r * 0.38, h * 0.55)), 0.28,
                            "iron"))
    for i in range(5):                                  # the coals
        a = 2 * math.pi * i / 5 + seed
        out.append(kit.facet_lump(c + V((math.cos(a) * r * 0.35, math.sin(a) * r * 0.35, h * 0.55)), r * 0.28, "ember"))
    kit.fire(c + Z * (h * 0.75), kind)
    return out


# ------------------------------------------------------------------ the den and the kennel
def warg_skull(kit, c, f, L, pitch=0.0, gape=0.42, seed=0.0, kind="coldflame", jaw=0.66, chin=0.05,
               throat=None):
    """A great frozen warg skull: its occiput at c, looking along f (horizontal, tipped down by
    `pitch` radians), L long: a faceted cranium with a crest, a snout narrowing to the nose,
    cheekbones, dark eye sockets with frost crystals in them, the lower jaw dropped `gape` radians
    (`jaw` L long, its halves `chin` L apart at the front: wide apart, no chin bar), fangs and teeth
    of ice, rime and crystals on the crown; a cold fire in the maw (`throat`: a point of
    its own, low in the mouth, so the flames rise clear of the bone)."""
    c = _v(c)
    f0, s = _flat(f)
    f = (f0 * math.cos(pitch) - Z * math.sin(pitch)).normalized()
    u = f.cross(s).normalized()                          # up, square to the skull's axis

    def P(a, b, w):                                     # a along the skull, b to its side, w up
        return c + f * (a * L) + s * (b * L) + u * (w * L)

    # (along, half width, top, bottom): the skull's profile, back to front
    prof = [(0.0, 0.13, 0.16, -0.1), (0.1, 0.22, 0.27, -0.13), (0.28, 0.25, 0.31, -0.13), (0.42, 0.21, 0.25, -0.11),
            (0.5, 0.15, 0.17, -0.09), (0.7, 0.13, 0.14, -0.08), (0.88, 0.1, 0.1, -0.06), (1.0, 0.065, 0.06, -0.05)]
    rings = []
    for a, w, top, bot in prof:
        rings.append([P(a, w, 0.0), P(a, w * 0.82, top * 0.7), P(a, w * 0.35, top * 0.96), P(a, 0, top * 1.08),
                      P(a, -w * 0.35, top * 0.96), P(a, -w * 0.82, top * 0.7), P(a, -w, 0.0), P(a, -w * 0.6, bot),
                      P(a, w * 0.6, bot)])
    out = [loft(rings, ["trim"] * (len(rings) - 1), cap0=("trim", True), cap1=("trim", True))]
    for e in (-1, 1):
        out.append(kit.tube([P(0.18, e * 0.22, -0.03), P(0.32, e * 0.29, -0.01), P(0.48, e * 0.17, 0.02)],
                            [0.035 * L, 0.045 * L, 0.03 * L], "trim", k=5, cap0="trim", cap1="trim"))   # cheekbone
        eye = P(0.43, e * 0.13, 0.2)                   # the socket: a dark rim round a cold glow, on the top
        n = (s * e * 0.55 + f * 0.5 + u * 0.65).normalized()
        a1 = (n.cross(f)).normalized()
        a2 = n.cross(a1).normalized()
        rim = [eye + (a1 * math.cos(2 * math.pi * k / 6) * 0.8 + a2 * math.sin(2 * math.pi * k / 6)) * (0.075 * L)
               for k in range(6)]
        out.append(loft([[p - n * 0.04 * L for p in rim], rim, [eye + n * 0.012 * L] * 6], ["slit", "slit"],
                        cap0=("slit", True), cap1=("slit", False)))
        out += kit.ice_cluster(eye - n * 0.01 * L, 0.035 * L, 0.11 * L, n=4, up=n + u * 0.3, seed=seed + 20 + e,
                               lean=0.6, thick=0.24)          # frost in the socket
        out.append(kit.tube([P(0.34, e * 0.17, 0.25), P(0.42, e * 0.19, 0.24), P(0.5, e * 0.13, 0.17)],
                            [0.03 * L, 0.035 * L, 0.02 * L], "trim", k=5, cap0="trim", cap1="trim"))     # brow ridge
    out.append(kit.beam(P(0.04, 0, 0.19), P(0.4, 0, 0.3), 0.03 * L, "rime", 0.012 * L))          # frost on the crest
    for i, (a, b) in enumerate(((0.16, 0.08), (0.26, -0.12), (0.3, 0.15))):
        out += kit.ice_cluster(P(a, b, 0.2), 0.05 * L, 0.2 * L, n=4, up=(u + f * 0.2 * (1 if i % 2 else -1)),
                               seed=seed + i * 3.1, lean=0.5, thick=0.2)
    for e in (-1, 1):                                   # the upper fangs and teeth
        root = P(0.88, e * 0.06, -0.02)
        out += kit.shard(root, -u + f * 0.25, 0.24 * L, 0.03 * L, k=4, seed=seed + e, bury=0.05 * L)
        for i, a in enumerate((0.6, 0.69, 0.78)):
            out += kit.shard(P(a, e * (0.085 - 0.03 * (a - 0.58) / 0.2), -0.07), -u + s * (e * 0.15), 0.07 * L, 0.015 * L,
                             k=3, seed=seed + i, bury=0.045 * L)
    # the lower jaw: two mandibles hinged under the cheeks, dropped `gape`, joined at the chin
    jf = (f * math.cos(gape) - u * math.sin(gape)).normalized()
    ju = jf.cross(s).normalized()
    hinge = P(0.28, 0, -0.1)
    chin_c = hinge + jf * (jaw * L)
    for e in (-1, 1):
        a0 = hinge + s * (e * 0.17 * L)
        a1 = chin_c + s * (e * chin * L)
        out.append(loft([[a0 + ju * 0.05 * L, a0 + s * (e * 0.04 * L), a0 - ju * 0.08 * L, a0 - s * (e * 0.04 * L)],
                         [a1 + ju * 0.035 * L, a1 + s * (e * 0.032 * L), a1 - ju * 0.05 * L, a1 - s * (e * 0.032 * L)]],
                        ["trim"], cap0=("trim", True), cap1=("trim", True)))
        out += kit.shard(a1 - s * (e * 0.005 * L) - jf * 0.03 * L, ju + jf * 0.15, 0.15 * L, 0.025 * L, k=4,
                         seed=seed + 7 + e, bury=0.02 * L)
        for i in range(3):                              # teeth up off the mandible's ridge
            q = a0.lerp(a1, 0.45 + 0.17 * i) + ju * (0.03 * L)
            out += kit.shard(q, ju, 0.06 * L, 0.012 * L, k=3, seed=seed + 11 + i, bury=0.02 * L)
    nose = P(1.0, 0, 0.0)                               # the nasal opening: a dark notch in the nose
    out.append(loft([[nose + s * 0.045 * L - f * 0.02 * L, nose + u * 0.04 * L - f * 0.02 * L,
                      nose - s * 0.045 * L - f * 0.02 * L],
                     [p + f * 0.012 * L for p in (nose + s * 0.035 * L, nose + u * 0.03 * L, nose - s * 0.035 * L)]],
                    ["slit"], cap0=("slit", False), cap1=("slit", True)))
    if chin < 0.09:
        out.append(kit.beam(chin_c - s * (chin + 0.01) * L - ju * 0.01 * L, chin_c + s * (chin + 0.01) * L - ju * 0.01 * L,
                            0.035 * L, "trim"))
    kit.fire(_v(throat) if throat is not None else P(0.72, 0, -0.12) - u * 0.03 * L, kind)
    return out


def jaw_arch(kit, c, n, span, h, r=1.9, teeth=5, seed=0.0, ice=True):
    """Two great warg tusks rising from either side of a gate (c on the ground in front of it, n out
    of the gate, span between the feet) and curving in to cross over it at h, one a little in front
    of the other: each thick at its root (1.7 r), broad in the arch's plane, tapering to a point; an
    iron band binds them where they cross; teeth of ice along their inner edges low down, stone
    footings rimed, crystals at the feet (ice=True)."""
    c, (n, t) = _v(c), _flat(n)
    out = []
    for e in (-1, 1):
        b = c + t * (e * span / 2)
        p0 = b + Z * 1.2 + n * (e * r * 0.55)          # one tusk a little in front of the other
        pts = kit.arc(p0, Z + t * (e * 0.12), -t * e + Z * 0.15, h * 1.32, n=7)
        k = h / max(p.z - c.z for p in pts)            # the crossing at h above the ground
        pts = [p0 + (p - p0) * V((1.0, 1.0, k)) for p in pts]
        m = len(pts) - 1
        radii = [r * (1.7 - 1.0 * i / m) if i < m else 0.25 for i in range(len(pts))]
        out.append(kit.tube(pts, radii, "trim", k=6, cap0="trim", cap1="trim", squash=1.5))
        if e > 0:                                       # where this tusk passes over the arch's middle
            u = [(p - c).dot(t) for p in pts]
            j = next(i for i in range(m) if u[i] > 0 >= u[i + 1])
            cross = pts[j].lerp(pts[j + 1], u[j] / (u[j] - u[j + 1]))
            cross = V((c.x, c.y, cross.z))
        out.append(block(b, n, t, r * 3.6, r * 4.0, c.z - 0.8, c.z + 4.4, "rock", top="rime", ch=0.7, taper=0.75))
        if ice:
            out += kit.ice_cluster(b + n * (r * 2.2) + t * (e * r * 1.2), r * 1.4, 7.5, n=5, seed=seed + e * 2.0,
                                   lean=0.55, thick=0.22, floor=_f(c.z - 0.6))
        for i in range(teeth):                          # teeth along the inner edge, pointing into the arch
            j = 1 + i * 0.55
            q = int(j)
            p = pts[q].lerp(pts[q + 1], j - q)
            rr = r * (1.7 - 1.0 * j / m)
            inner = (-t * e + Z * 0.25).normalized()
            out += kit.shard(p + inner * rr * 1.2, inner + Z * 0.15, 5.5 - 0.5 * i, 0.9, k=4, seed=seed + i,
                             bury=rr * 0.9, tag="ice")
    top = cross                                         # the iron band where they cross
    out.append(block(top, n, t, r * 3.8, r * 2.6, top.z - 2.2, top.z + 2.2, "iron", ch=0.5))
    out += kit.rivets(V((top.x, top.y, 0)), t, n, [(-r * 0.7, top.z), (r * 0.7, top.z)], r * 1.9, r=0.45)
    out += kit.rivets(V((top.x, top.y, 0)), t, -n, [(-r * 0.7, top.z), (r * 0.7, top.z)], r * 1.9, r=0.45)
    return out


# ------------------------------------------------------------------ the Hall of Twilight
def runes(kit, a, t, n, u, z0, z1, w=0.55, d=0.0, tag="ember"):
    """A column of runes on a face (a, t, n) at u from z0 to z1, d out from it: strokes like the
    Cirth, a stem with branches, one rune every ~3.4."""
    out = []
    a = V((a[0], a[1], 0))
    k = max(1, int((z1 - z0) / 3.4))
    for i in range(k):
        zb = z0 + (z1 - z0) * i / k
        zt = zb + (z1 - z0) / k * 0.78
        P = lambda uu, zz: a + t * (u + uu) + n * d + Z * zz       # noqa: E731
        out.append(kit._stroke(P(0, zb), P(0, zt), n, w, tag))
        sgn = 1 if i % 2 else -1
        zm = zb + (zt - zb) * (0.4 + 0.25 * (i % 3) / 2)
        out.append(kit._stroke(P(0, zm), P(sgn * 1.2, zm + 1.0), n, w * 0.85, tag))
        if i % 3 == 2:
            out.append(kit._stroke(P(0, zm - 0.9), P(-sgn * 1.0, zm - 1.6), n, w * 0.85, tag))
    return out


def great_rune(kit, c, t, o, d, lean, z0, h, w, seed=0.0, tag="ember"):
    """A great rune cut in a standing stone's outer face (the face d out from c along o, leaning
    `lean` per unit up), glowing: a stem h tall, a chevron of two branches near its top, a pair of
    short ticks below, a diamond at its foot; strokes ~1.3 wide, a little proud of the face."""
    c = _v(c)
    P = lambda u, z: c + t * u + o * (d + lean * (z - c.z) + 0.15) + Z * z  # noqa: E731
    out = [kit._stroke(P(0, z0 + h * 0.18), P(0, z0 + h), o, 1.3, tag)]
    sg = 1 if _h(seed, 3) > 0.5 else -1
    for e in (-1, 1):
        out.append(kit._stroke(P(0, z0 + h * 0.86), P(e * w, z0 + h * 0.62), o, 1.15, tag))
    out.append(kit._stroke(P(0, z0 + h * 0.42), P(sg * w * 0.8, z0 + h * 0.3), o, 1.0, tag))
    dz = z0 + h * 0.07
    out.append(loft([[P(0, dz - 1.6), P(1.2, dz), P(0, dz + 1.6), P(-1.2, dz)],
                     [p + o * 0.5 for p in (P(0, dz - 1.0), P(0.7, dz), P(0, dz + 1.0), P(-0.7, dz))]],
                    [tag], cap0=(tag, False), cap1=(tag, True)))
    return out


def rune_stone(kit, c, out_dir, w, d, h, lean=0.06, seed=0.0, runed=True):
    """A rune stone at c (x, y, ground z): a monolith w wide (along the face), d deep, h tall,
    leaning `lean` outward, narrowing a little, its top cut on a slant (high on one side); a crust
    of rime on the cut, cold runes down its outer face, ice crystals at its foot."""
    c = _v(c)
    o, t = _flat(out_dir)
    sk = 1 if _h(seed) > 0.5 else -1

    def ring(z, k, cut=0.0):
        pts = [(w / 2, -d / 2), (w / 2, d / 2 * 0.7), (w * 0.3, d / 2), (-w * 0.35, d / 2), (-w / 2, d / 2 * 0.6),
               (-w / 2, -d / 2 * 0.8), (-w * 0.2, -d / 2), (w * 0.3, -d / 2)]
        return [c + t * (uu * k) + o * (vv * k + lean * (z - c.z)) + Z * (z + cut * uu / (w / 2) * sk) for vv, uu in
                [(p[1], p[0]) for p in pts]]
    top = c.z + h
    rings = [ring(_f(c.z - 1.0), 1.0), ring(c.z + h * 0.55, 0.93), ring(top - h * 0.12, 0.84, h * 0.06),
             ring(top, 0.72, h * 0.12)]
    out = [loft(rings, ["rock"] * 3, cap0=("rock", False), cap1=("rime", True))]
    cap = [p + Z * 0.7 + (p - (c + o * (lean * h) + Z * p.z)) * 0.06 for p in rings[-1]]
    out.append(loft([[p - Z * 1.2 for p in rings[-1]], cap], ["rime"], cap0=("rime", False), cap1=("rime", True)))
    if runed == "great":                                # one great rune glowing down its face
        out += great_rune(kit, c, t, o, d / 2 * 0.93, lean, c.z + h * 0.2, h * 0.5, w * 0.34, seed=seed)
    elif runed:
        a = c + o * (d / 2 + lean * h * 0.45)
        out += runes(kit, a + Z * 0, t, o, 0.0, c.z + h * 0.22, c.z + h * 0.72, w=0.6, d=0.05)
    out += kit.ice_cluster(c + o * (d * 0.7) + t * (sk * w * 0.4), 1.6, 5.5, n=4, seed=seed + 4, lean=0.5, thick=0.24,
                           floor=_f(c.z - 0.5))
    return out


def altar(kit, c, out_dir, s=1.0, kind="coldfire", seed=0.0):
    """A sorcerers' altar at c (x, y, ground z) facing out_dir: a broad step of dressed stone, a
    black stone block narrowing up with rune bands on its front and sides, a rimed top slab and a
    crater of ice and stone shards on it, the cold fire burning out of the crater."""
    c = _v(c)
    o, t = _flat(out_dir)
    out = [block(c, o, t, 14 * s, 17 * s, c.z - 0.8, c.z + 1.8 * s, "stoneA", top="stoneB", ch=1.0 * s),
           block(c, o, t, 10 * s, 12.5 * s, c.z + 1.6 * s, c.z + 8.5 * s, "rock", ch=1.2 * s, taper=0.86),
           block(c, o, t, 12 * s, 14.5 * s, c.z + 8.3 * s, c.z + 9.8 * s, "stoneB", top="rime", ch=0.8 * s)]
    a = c + o * (10 * s * 0.43 + 0.05)
    for u in (-3.4 * s, 0.0, 3.4 * s):
        out += runes(kit, a, t, o, u, c.z + 2.8 * s, c.z + 7.6 * s, w=0.55 * s, d=0.0)
    top = c + Z * (9.6 * s)
    out += kit.ice_cluster(top, 5.2 * s, 13.0 * s, n=10, seed=seed + 2.0, lean=0.42, thick=0.2, tag="ice", stone="rock",
                           hollow=3)
    for i in range(5):                                  # the crater's rim: shards leaning out
        p = kit.polar(top, 2.6 * s, i * 72.0 + 20.0, top.z + 1.0)
        dd = (p - V((top.x, top.y, p.z))).normalized() * 0.6 + Z
        out += kit.shard(p, dd, (5.0 + 2.0 * (i % 2)) * s, 1.1 * s, k=5, seed=seed + i, tag="rock" if i % 2 else "ice",
                         bury=1.2 * s)
    kit.fire(top + Z * (2.5 * s), kind)
    return out


# ------------------------------------------------------------------ the catapult works
def boulder(kit, c, s, seed=0.0, tag="ice"):
    """An angular ice boulder s across at c: two staggered rings of five facets between a flat foot
    and a cut top (crystal, never round)."""
    c = _v(c)
    a0 = seed * 2.1
    r0 = [c + V((math.cos(a0 + 2 * math.pi * i / 5) * s * (0.45 + 0.1 * _h(seed, i)),
                 math.sin(a0 + 2 * math.pi * i / 5) * s * (0.45 + 0.1 * _h(seed, i)), s * 0.12)) for i in range(5)]
    r1 = [c + V((math.cos(a0 + 2 * math.pi * (i + 0.5) / 5) * s * (0.5 + 0.12 * _h(seed + 1, i)),
                 math.sin(a0 + 2 * math.pi * (i + 0.5) / 5) * s * (0.5 + 0.12 * _h(seed + 1, i)), s * 0.5)) for i in range(5)]
    r2 = [c + V((math.cos(a0 + 2 * math.pi * i / 5) * s * 0.3, math.sin(a0 + 2 * math.pi * i / 5) * s * 0.3,
                 s * (0.82 + 0.1 * _h(seed + 2, i)))) for i in range(5)]
    foot = [c + V((math.cos(a0 + 2 * math.pi * i / 5) * s * 0.3, math.sin(a0 + 2 * math.pi * i / 5) * s * 0.3, 0.0))
            for i in range(5)]
    return [loft([foot, r0, r1, r2], [tag, tag, tag], cap0=(tag, False), cap1=("rime", True))]


def boulder_heap(kit, c, out_dir, w, d, s=4.0, n=7, seed=0.0, crib=True):
    """Ice boulders heaped in a low timber crib at c (x, y, floor z), w across out_dir and d along
    it: the crib's four rails iron-strapped at the corners, the boulders two deep."""
    c = _v(c)
    o, t = _flat(out_dir)
    out = []
    if crib:
        for e in (-1, 1):
            out.append(block(c + o * (e * d / 2), t, o, w + 1.6, 1.4, c.z - 0.5, c.z + s * 0.55, "timber", ch=0.25))
            out.append(block(c + t * (e * w / 2), t, o, 1.4, d - 1.4, c.z - 0.5, c.z + s * 0.5, "timber", ch=0.25))
            for e2 in (-1, 1):
                out.append(block(c + o * (e * d / 2) + t * (e2 * w / 2), t, o, 2.0, 2.0, c.z - 0.4, c.z + s * 0.62,
                                 "iron", ch=0.3))
    for i in range(n):
        layer = 0 if i < n * 0.6 else 1
        a = 2 * math.pi * (i * 0.382 + 0.1 * _h(seed, i))
        rr = (0.15 + 0.3 * _h(seed + 3, i)) * (1.0 if layer == 0 else 0.4)
        p = c + t * (math.cos(a) * rr * w) + o * (math.sin(a) * rr * d) + Z * (layer * s * 0.55)
        out += boulder(kit, p, s * (0.8 + 0.35 * _h(seed + 5, i)), seed=seed + i)
    return out


def sling(kit, top, zb, t, o, s=5.6, seed=0.0):
    """A rope from `top` down to an ice boulder s across in an iron sling at zb."""
    out = [kit.beam(top, V((top.x, top.y, zb + s - 0.2)), 0.24, "chain")]
    c = V((top.x, top.y, zb))
    for e in (-1, 1):                                   # the sling's straps under the boulder
        out.append(kit.beam(c + Z * (s - 0.2), c + t * (e * s * 0.46) + Z * 0.8, 0.24, "iron"))
        out.append(kit.beam(c + Z * (s - 0.2), c + o * (e * s * 0.46) + Z * 0.8, 0.24, "iron"))
    return out + boulder(kit, c - Z * 0.4, s, seed=seed)


def gantry(kit, c, t, span, h, loads, post=3.0, splay=4.0, seed=0.0):
    """The catapult works' frozen timber gantry at c (x, y, ground z) along t: an A-frame trestle of
    heavy raking legs (splayed `splay` either side at the foot) at each end, a cross-tie, a heavy
    beam over both, rimed on top and hung with icicles; loads [(u along t, drop)] are ice boulders
    in iron slings on ropes from the beam."""
    c = _v(c)
    t, o = _flat(t)
    out = []
    top = c.z + h
    for e in (-1, 1):
        a = c + t * (e * span / 2)
        for k in (-1, 1):
            foot = a + o * (k * splay)
            out.append(block(foot, o, t, post + 1.8, post + 1.8, c.z - 0.6, c.z + 2.4, "stoneA", top="rime", ch=0.4,
                             taper=0.8))
            out.append(kit.beam(foot + Z * 1.2, a + Z * (h - 0.4) + o * (k * 0.6), post / 2, "timber"))
        tie = a + Z * (h * 0.4)
        out.append(kit.beam(tie - o * (splay * 0.66 + 0.6), tie + o * (splay * 0.66 + 0.6), post * 0.36, "timber"))
        out.append(block(a, o, t, post + 1.2, post * 2.6, top - 2.0, top + 0.2, "iron", ch=0.3))      # the iron cap
    out.append(block(c, t, o, span + 6.0, post * 1.15, top, top + post * 1.1, "timber", top="rime", ch=0.3))
    out.append(block(c, t, o, span + 6.4, post * 1.15 + 0.5, top + post * 1.1 - 0.2, top + post * 1.1 + 0.8, "rime",
                     ch=0.3))
    out += kit.icicles(c - t * (span / 2 + 2.5) + o * (post * 0.55), t, o, 0.0, span + 5.0, top + 0.2, 3.4,
                       max(4, int(span / 2.2)), d=0.0, crust=0.6, w=1.0, seed=seed)
    for i, (u, drop) in enumerate(loads):
        out += sling(kit, c + t * u + Z * h, top - drop, t, o, s=5.4, seed=seed + 7 + i)
    return out


def hoarding(kit, c, a0, a1, r0, r1, z0, z1, ridge, seed=0.0):
    """A frozen timber hoarding round a tower's top from a0 to a1 degrees round c: a plank gallery
    from r0 (the wall) out to r1 on a floor at z0, its outer boards to z1 with dark loopholes, a
    lean-to of slate shingles from the boards' top up to the wall at `ridge`, rime along the eaves
    and icicles under them, raking struts under the floor down to the wall; in straight runs of
    about 12 degrees."""
    c = _v(c)
    out = []
    k = max(1, int(round(abs(a1 - a0) / 12.0)))
    for i in range(k):
        b0, b1 = a0 + (a1 - a0) * i / k, a0 + (a1 - a0) * (i + 1) / k
        p, q = kit.polar(c, r1, b0, 0.0), kit.polar(c, r1, b1, 0.0)
        t = (q - p).normalized()
        n = V((t.y, -t.x, 0))
        if n.dot(p - V((c.x, c.y, 0))) < 0:
            n = -n
        L = (q - p).length
        m = (p + q) / 2
        d = r1 - r0                                     # depth back to the wall
        P = lambda u, dd, z: m + t * u + n * dd + Z * z  # noqa: E731
        ring = lambda z, w: [P(-L / 2 - w, -d - 1.0, z), P(L / 2 + w, -d - 1.0, z), P(L / 2 + w, 0.4, z),  # noqa
                             P(-L / 2 - w, 0.4, z)]
        out.append(loft([ring(z0 - 1.0, 0.0), ring(z0, 0.0)], ["planks"], cap0=("timber", True), cap1=("planks", True)))
        out.append(loft([[P(-L / 2, -0.6, z0), P(L / 2, -0.6, z0), P(L / 2, 0.4, z0), P(-L / 2, 0.4, z0)],
                         [P(-L / 2, -0.6, z1), P(L / 2, -0.6, z1), P(L / 2, 0.4, z1), P(-L / 2, 0.4, z1)]],
                        ["planks|v"], cap0=("planks", False), cap1=("planks", True)))
        for u in (-L * 0.22, L * 0.22):                 # loopholes
            out.append(loft([[P(u - 0.7, 0.3, z0 + 3.0), P(u + 0.7, 0.3, z0 + 3.0), P(u + 0.7, 0.3, z1 - 2.2),
                              P(u - 0.7, 0.3, z1 - 2.2)],
                             [P(u - 0.7, 0.55, z0 + 3.0), P(u + 0.7, 0.55, z0 + 3.0), P(u + 0.7, 0.55, z1 - 2.2),
                              P(u - 0.7, 0.55, z1 - 2.2)]], ["slit"], cap0=("slit", False), cap1=("slit", True)))
        eave = [P(-L / 2 - 0.4, 1.6, z1 - 0.6), P(L / 2 + 0.4, 1.6, z1 - 0.6)]
        back = [P(L / 2 + 0.4, -d - 1.5, ridge), P(-L / 2 - 0.4, -d - 1.5, ridge)]
        roof = eave + back
        out.append(loft([[v - Z * 0.9 for v in roof], roof], ["roof"], cap0=("timber", True), cap1=("roof", True)))
        out.append(kit.beam(P(-L / 2 - 0.4, 1.6, z1 - 0.1), P(L / 2 + 0.4, 1.6, z1 - 0.1), 0.6, "rime"))
        out += kit.icicles(P(-L / 2, 0.0, 0.0), t, n, 0.0, L, z1 - 1.4, 3.2, max(3, int(L / 2.0)), d=1.6, crust=0.7,
                           w=0.9, seed=seed + i)
        out.append(kit.beam(P(0, -d + 0.3, z0 - 9.0), P(0, -0.4, z0 - 0.8), 0.9, "timber"))     # a strut
        out.append(block(P(0, -d - 0.2, 0), t, n, 2.6, 1.4, z0 - 10.4, z0 - 8.0, "iron", ch=0.2))
    return out
