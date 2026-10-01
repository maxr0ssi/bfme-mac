"""The Isengard production group's big masses (Blender side): the pointed pieces that change a
building's silhouette at the RTS view (pass 2, after "too modest": every building needed one or
two). Functions of the kit like assets/isengard/shapes_industry.py, whose small pieces they use.

    square_crucible(kit, c, r, h)            an iron crucible turned to a corner, molten to its brim
    pyramid_kiln(kit, c, r, h, rot)          a square steep charcoal kiln, iron bands, corner blades,
                                             pointed ember vents, a glowing throat
    trident(kit, c, axis, L, W, h)           a blade tower between two leaning horns on a saddle
    siege_tower(kit, c, t, w, h, built)      a half-built siege tower: timber, iron plate, drawbridge,
                                             a pointed roof frame
    ram(kit, c, t, length, h)                a ram slung from two iron A-frames, an iron wedge head
    birth_crown(kit, c, r0, z0, apex)        knife ribs rising from a pit's rim to a needle over it,
                                             a ring, meat hooks, a great hook into the pit
    blade_crane(kit, c, reach_to, h, drop)   a lozenge iron mast, a laced jib, a slung log
    ridge_fins(kit, p, q, heights)           a dorsal crest of layered knife fins along a ridge
    spire_stack(kit, c, axis, L, W, z0, z1)  a great blade-spire chimney, a crown of convex blades
    log_crib(kit, c, t, length, r, layers)   felled Fangorn in crossed courses, iron stakes

Pass 3, the citadel's recipe (assets/isengard/fortress/foundry.py):

    blade_pair(kit, m, half, L, W, z0, z1)   two matching blade towers either side of m along the
                                             RTS view's horizontal, mirrored, Hands on their outer faces
    blades_at(kit, cs, L, W, z0, z1)         the same pair at two given centres (a gable, a pit)
    blade_face(c, axis, L, W, z0, z1, ...)   a blade tower's face toward the camera at a height
    hand_slot(kit, m, t, n, z0, w, h)        the White Hand in a pointed-arch slot on a face
    birth_spire(kit, c, r0, z0, apex, rk, zk) the birthing-frame made pointed: four knife ribs on a
                                             square, four iron bars at the knee, a needle
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz

from .shapes_industry import _tn, _v, blade_post, fin


def square_crucible(kit, c, r, h):
    """An iron crucible r across at c, h deep, square and turned to show a corner (no round pot):
    a pointed foot, flared walls, a silver band, brim-full of molten metal, a spike at each corner.
    Fire: crucible at the brim."""
    c = _v(c)
    sq = lambda s, z: kit.square(c, r * s, c.z + z)                               # noqa: E731
    out = [loft([sq(0.45, 0.0), sq(0.95, h * 0.3), sq(1.05, h * 0.9), sq(1.15, h), sq(0.9, h), sq(0.9, h - 0.3)],
                ["iron", "iron", "trim", "iron", "ember"], cap0=("iron", True), cap1=("ember", True))]
    for p in sq(1.15, h):
        d = V((p.x - c.x, p.y - c.y, 0)).normalized()
        out.append(kit.beam(p, p + (d + Z).normalized() * r * 0.7, 0.18, "iron", 0.0))
    kit.fire(c + Z * h, "crucible")
    return out

def pyramid_kiln(kit, c, r, h, rot=0.0, vents=True, throat_fire=True):
    """A charcoal kiln r across at c, h high, square in plan and turned `rot` (a corner toward the
    camera): a battered stone plinth, a steep four-faced iron-banded pyramid, a glowing throat in
    its truncated top, a blade out of each corner past the throat, pointed ember vents on its
    faces. No round drum. Fire: chimney at the throat."""
    c = _v(c)
    sq = lambda s, z: kit.square(c, r * s, c.z + z, math.radians(rot) + math.pi / 4)       # noqa: E731
    top = h * 0.82
    out = [loft([sq(1.12, -0.4), sq(1.08, h * 0.1), sq(1.0, h * 0.12), sq(0.36, top), sq(0.42, top + 0.8),
                 sq(0.42, top + 2.0), sq(0.26, top + 2.0), sq(0.26, top - 1.0)],
                ["stoneA", "trim", "stoneA", "trim", "iron", "iron", "ember"], cap0=("stoneA", False), cap1=("ember", True))]
    for f in (0.34, 0.6):                                        # iron bands round the pyramid
        s = 1.0 + (0.36 - 1.0) * (f * h - h * 0.12) / (top - h * 0.12)
        out.append(loft([sq(s - 0.08, h * f - 0.7), sq(s + 0.06, h * f - 0.5), sq(s + 0.06, h * f + 0.5),
                         sq(s - 0.08, h * f + 0.7)], ["iron"] * 3, cap0=("iron", False), cap1=("iron", False)))
    for k in range(4):                                           # a blade out of each corner, past the throat
        ang = math.radians(rot) + math.pi / 4 + math.pi / 2 * k
        d = V((math.cos(ang), math.sin(ang), 0))
        out += fin(kit, c, d, r * 0.3, [(r * 0.2, c.z + top - 3.0), (r * 0.46, c.z + top - 3.0), (r * 0.5, c.z + top + 4.0),
                                        (r * 0.3, c.z + h + 3.0), (r * 0.2, c.z + top + 2.0)], 0.7, tag="iron")
        if vents:                                                # a pointed ember vent low on each face
            dm = V((math.cos(ang + math.pi / 4), math.sin(ang + math.pi / 4), 0))
            s = V((-dm.y, dm.x, 0))
            a = V((c.x, c.y, 0)) + dm * (r * 0.707 * 0.93)
            z0 = c.z + h * 0.14
            out.append(prism_uz(a, s, dm, [(-1.1, z0), (1.1, z0), (1.1, z0 + 2.6), (0, z0 + 4.4), (-1.1, z0 + 2.6)],
                                -1.2, 0.3, ["ember"] * 5, "ember", None))
            out.append(prism_uz(a, s, dm, [(-1.6, z0 - 0.4), (1.6, z0 - 0.4), (1.6, z0 + 2.9), (0, z0 + 5.2),
                                           (-1.6, z0 + 2.9)], 0.0, 0.45, ["trim"] * 5, "iron", "iron"))
    if throat_fire:
        kit.fire(c + Z * (top + 1.0), "chimney")
    return out


def trident(kit, c, axis, L, W, h, horn=0.72, spread=1.9, slits=(0.45, 0.62)):
    """A trident tower at c: a lozenge blade tower to h (flared, spurred, fins, ember slits, a
    needle) between two lesser blade horns set `spread` * L out along its axis, leaning out, to
    horn * h; a stone saddle joining their feet."""
    from .shapes_spire import BROAD
    c = V((c[0], c[1], 0))
    a = math.radians(axis)
    d = V((math.cos(a), math.sin(a), 0))
    out = kit.blade_tower((c.x, c.y), axis, L, W, 0.0, h, flare=1.25, fins=1, slits=slits, profile=BROAD,
                          fin_reach=1.2, slit_w=1.1)
    for e in (-1, 1):
        p = c + d * (e * L * spread)
        out += kit.blade_tower((p.x, p.y), axis, L * 0.5, W * 0.6, 0.0, h * horn, lean=(d.x * e * 2.2, d.y * e * 2.2),
                               flare=1.3, fins=1, spurs=False, slits=(0.5,), profile=BROAD, slit_w=0.8)
    out.append(loft([[c + d * (-L * spread) + V((0, 0, z)) + s for s in (V((-d.y, d.x, 0)) * W * 0.5, -V((-d.y, d.x, 0)) * W * 0.5)]
                     + [c + d * (L * spread) + V((0, 0, z)) + s for s in (-V((-d.y, d.x, 0)) * W * 0.5, V((-d.y, d.x, 0)) * W * 0.5)]
                     for z in (-0.3, h * 0.16)], ["stoneA"], cap0=("stoneA", False), cap1=("trim", True)))
    return out


def siege_tower(kit, c, t, w, h, built=0.7):
    """A half-built siege tower at c (its foot's centre), w square, h to its unfinished top: four
    timber posts leaning in, ledgers and braces every level, the lower levels skinned in riveted
    iron plate on its front (n), a drawbridge standing shut, a pointed roof frame of four iron
    rafters to a spike over the finished part."""
    c = _v(c)
    t, n = _tn(t)
    out = []
    levels = 4
    top = h * built
    lean = 0.12
    P = lambda u, d, z: c + t * (u * (1 - lean * z / h)) + n * (d * (1 - lean * z / h)) + Z * z   # noqa: E731
    for u in (-w / 2, w / 2):
        for d in (-w / 2, w / 2):
            out.append(kit.beam(P(u, d, -0.4), P(u, d, top), 0.6, "timber"))
    for i in range(1, levels + 1):
        z = h * i / levels
        if z > top + 0.1:
            break
        for (u0, d0), (u1, d1) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            out.append(kit.beam(P(u0 * w / 2, d0 * w / 2, z), P(u1 * w / 2, d1 * w / 2, z), 0.4, "timber"))
        zl = h * (i - 1) / levels
        out.append(kit.beam(P(-w / 2, -w / 2, zl + 0.5), P(w / 2, -w / 2, z - 0.5), 0.3, "timber"))    # braces
        out.append(kit.beam(P(-w / 2, w / 2, z - 0.5), P(-w / 2, -w / 2, zl + 0.5), 0.3, "timber"))
    for i in range(2):                                            # iron plate on the front's lower levels
        z0, z1 = h * i / levels + 0.6, h * (i + 1) / levels - 0.6
        a = P(0, w / 2, 0)
        out += kit.plate(V((a.x, a.y, 0)) + n * 0.4, t, n, -w / 2 + 0.6, w / 2 - 0.6, z0, z1, d=0.0, th=0.5, pitch=2.4)
    zb = h * 2 / levels                                           # the drawbridge, shut, on the third level
    a = P(0, w / 2, zb)
    out.append(prism_uz(V((a.x, a.y, 0)) + n * 0.3, t, n, [(-w * 0.34, zb + 0.3), (w * 0.34, zb + 0.3), (w * 0.34, zb + h / levels - 0.5),
                                                          (0, zb + h / levels + 1.5), (-w * 0.34, zb + h / levels - 0.5)],
                        0.0, 0.6, ["timber", "iron", "trim", "trim", "iron"], "timber", "timber"))
    apex = c + Z * (top + w * 0.9)                                # a pointed roof frame over the finished part
    for u in (-w / 2, w / 2):
        for d in (-w / 2, w / 2):
            out.append(kit.beam(P(u, d, top), apex, 0.35, "iron"))
    out.append(kit.beam(apex - Z * 0.5, apex + Z * 4.5, 0.55, "trim", 0.0))
    return out


def ram(kit, c, t, length=22.0, h=9.0):
    """A battering ram along t at c: a great trunk slung on chains from two iron A-frames, its
    head an iron wedge with blade fins (a wolf's snout in Isengard's angles), iron hoops along it."""
    c = _v(c)
    t, n = _tn(t)
    out = []
    zl = h * 0.52
    a, b = c - t * length * 0.5 + Z * zl, c + t * length * 0.42 + Z * zl
    out.append(kit.tube([a, b], [1.5, 1.35], "timber", k=6, cap0="timber", cap1="timber"))
    for f in (0.15, 0.5, 0.85):
        p = a.lerp(b, f)
        out.append(kit.tube([p - t * 0.5, p + t * 0.5], [1.7, 1.7], "iron", k=6, cap0="iron", cap1="iron"))
    head = b
    ring = [head + n * 1.9 + Z * 0.0, head + Z * 1.9, head - n * 1.9, head - Z * 1.9]
    out.append(loft([ring, [head + t * 2.0 + p - head for p in ring], [head + t * 7.0 + Z * 0.3] * 4], ["iron", "iron"],
                    cap0=("iron", True), cap1=("iron", False)))
    for s in (-1, 1):                                             # blade fins over the head, laid back
        out.append(prism_uz(head, t, n, [(0.0, head.z + 1.5), (4.0, head.z + 1.2), (-1.5, head.z + 4.5 + s * 0.0)],
                            s * 0.8 - 0.15, s * 0.8 + 0.15, ["trim", "trim", "iron"], "iron", "iron"))
    for e in (-0.32, 0.3):                                        # the A-frames and chains
        m = c + t * (length * e)
        topm = m + Z * (h + 1.0)
        for s in (-1, 1):
            out.append(kit.beam(m + n * (s * h * 0.45) - Z * 0.4, topm, 0.45, "iron"))
        out.append(kit.beam(topm - n * 0.6, topm + n * 0.6, 0.5, "iron"))
        out.append(kit.beam(topm + Z * 0.4, topm + Z * 3.4, 0.55, "trim", 0.0))
        out += kit.chain(topm - Z * 0.5, a.lerp(b, 0.5 + e) + Z * 1.4, link=1.2)
    return out


def birth_crown(kit, c, r0, z0, apex, ribs=6, r_knee=None, z_knee=None, w=1.3, hooks=True):
    """An iron birthing-frame over a pit: `ribs` knife-edged ribs rising from its rim (radius r0
    at z0), standing up to a knee and bending in to meet at a needle over the pit's middle; a
    riveted ring binding them at the knee, meat hooks hung round it on chains and a great hook
    from the apex into the pit."""
    c = _v(c)
    rk = r_knee if r_knee is not None else r0 * 1.05
    zk = z_knee if z_knee is not None else z0 + (apex - z0) * 0.45
    out = []
    for i in range(ribs):
        ang = 2 * math.pi * (i + 0.5) / ribs
        d = (math.cos(ang), math.sin(ang))
        out += fin(kit, c, d, r0 + 99.0, [(r0 - 1.6, z0 - 1.0), (r0 + 3.0, z0 - 1.0), (rk + 2.4, zk), (rk - 1.4, zk - 2.6)],
                   w, tag="iron")                        # dark below the ring, a silver edge above it
        out += fin(kit, c, d, 0.5, [(rk - 1.4, zk - 2.6), (rk + 2.4, zk), (0.8, apex - 0.5), (0.2, apex - 4.0)], w * 0.85,
                   tag="iron")
    out += kit.hoop((c.x, c.y), zk - 1.2, rk + 0.2, h=1.6, th=0.6, inner=1.0, k=ribs * 2, rivets=2, tag="trim", closed=True)
    out.append(kit.beam(V((c.x, c.y, apex - 2.0)), V((c.x, c.y, apex + 7.0)), 0.9, "iron", 0.0))
    out.append(kit.beam(V((c.x, c.y, apex - 1.5)), V((c.x, c.y, apex + 0.5)), 1.3, "trim"))
    if hooks:
        for i in range(ribs):
            ang = 2 * math.pi * i / ribs
            p = V((c.x + math.cos(ang) * (rk - 1.0), c.y + math.sin(ang) * (rk - 1.0), zk - 2.0))
            out += kit.hook(p, 1.4, chain=3.0 + 1.5 * (i % 2))
        out += kit.chain(V((c.x, c.y, apex - 3.0)), V((c.x, c.y, z0 + 5.0)), link=1.8, w=0.6, th=0.25)
        out += kit.hook(V((c.x, c.y, z0 + 5.0)), 2.6, chain=0.0)
    return out


def blade_crane(kit, c, reach_to, h, jib_top=None, drop=10.0):
    """A derrick crane: a lozenge iron mast at c to h with fins and a needle, a jib of two iron
    booms and lacing from the mast's foot-collar out to `reach_to` (x, y, z: the boom's head),
    stays from the mast head, a chain from the head down `drop` to a slung log."""
    c = _v(c)
    tip = _v(reach_to)
    out = kit.blade_tower((c.x, c.y), math.degrees(math.atan2(tip.y - c.y, tip.x - c.x)), 3.4, 2.3, c.z, c.z + h,
                          flare=1.5, fins=1, spurs=True, slits=(), collar=0.4)
    root = c + Z * (h * 0.3)
    d = (tip - root)
    side = V((-d.y, d.x, 0)).normalized()
    for s in (-1, 1):
        out.append(kit.beam(root + side * (s * 1.4), tip + side * (s * 0.4), 0.7, "iron"))
    for q in (0.2, 0.4, 0.6, 0.8):
        p = root.lerp(tip, q)
        out.append(kit.beam(p - side * 1.0, p + side * 1.0, 0.18, "trim"))
    out.append(kit.beam(tip, tip + d.normalized() * 2.5 + Z * 1.2, 0.6, "trim", 0.0))
    head = c + Z * (h * 0.92)
    out += kit.chain(head, tip, link=2.2, w=0.5)
    out += kit.chain(tip - Z * 0.6, tip - Z * drop, link=1.8, w=0.55, th=0.22)
    lg = tip - Z * (drop + 1.6)
    ax = side
    out.append(kit.tube([lg - ax * 7.0, lg + ax * 7.0], [1.4, 1.3], "timber", k=6, cap0="timber", cap1="timber"))
    for s in (-1, 1):
        out += kit.chain(tip - Z * drop, lg + ax * (s * 3.5) + Z * 1.2, link=1.2)
    return out


def ridge_fins(kit, p, q, heights, lengths=None, w=1.1):
    """A dorsal crest of layered knife fins standing on a ridge from p to q: one fin per height in
    `heights` (their tops above the ridge), each `lengths` long along the ridge, silver front edges,
    an ember slit in the tall ones."""
    p, q = _v(p), _v(q)
    t = (q - p).normalized()
    n = V((-t.y, t.x, 0))
    k = len(heights)
    lengths = lengths or [min(6.0, (q - p).length / k * 0.9)] * k
    out = []
    for i, (hh, L) in enumerate(zip(heights, lengths)):
        m = p.lerp(q, (i + 0.5) / k)
        poly = [(-L / 2, m.z - 1.5), (L / 2, m.z - 1.5), (L * 0.18, m.z + hh), (-L * 0.3, m.z + hh * 0.72)]
        tags = ["iron", "trim", "trim", "iron"]
        out.append(prism_uz(V((m.x, m.y, 0)), t, n, poly, -w / 2, w / 2, tags, "stoneA", "stoneA"))
        if hh > 8.0:
            for e in (-1, 1):
                out.append(prism_uz(V((m.x, m.y, 0)) + n * (e * w / 2), t, n * e,
                                    [(-0.5, m.z + hh * 0.2), (0.5, m.z + hh * 0.2), (0.5, m.z + hh * 0.5), (0.0, m.z + hh * 0.58),
                                     (-0.5, m.z + hh * 0.5)], -0.5, 0.15, ["ember"] * 5, "ember", None))
    return out


def spire_stack(kit, c, axis, L, W, z0, z1, collar=0.6, fins=True, crown=None, slits=(0.2, 0.46, 0.72)):
    """A great blade-spire stack (the needle chimney at a size its kit form cannot take): a lozenge
    shaft from a flared foot, a set-back step, tapering to a silver rim round a glowing mouth at
    z1, knife fins up its two sharp edges, an ember-lit band with spikes, and a crown of four
    convex knife blades rising from the rim's corners to points. Fire: chimney at the mouth."""
    prof = [(0.0, 1.45), (0.05, 1.0), (0.35, 0.84), (0.352, 0.76), (0.92, 0.5)]
    crown = crown if crown is not None else W * 2.4
    rings = kit._shaft(c, axis, L, W, z0, z1 - 2.0, (0, 0), prof)
    top = rings[-1]
    rim = kit._grow([p + Z * 1.0 for p in top], 0.8)
    lip = [p + Z * 2.0 for p in rim]
    throat = [p + Z * 2.0 for p in kit._grow(top, -0.3)]
    deep = [p - Z * 3.0 for p in throat]
    out = [loft(rings + [rim, lip, throat, deep], ["iron"] * len(rings) + ["trim", "iron", "ember"], cap0=("iron", False),
                cap1=("ember", True))]
    H = z1 - z0
    cc = V((c[0], c[1], 0))
    if fins:
        for k in (0, 2):
            v = rings[1][k]
            d = V((v.x - cc.x, v.y - cc.y, 0)).normalized()
            r = (V((v.x, v.y, 0)) - cc).length
            out += fin(kit, cc, d, r * 0.6, [(r * 0.7, z0 + 0.5), (r + 3.6, z0 + 0.5), (r * 0.62 + 1.0, z0 + H * 0.78),
                                              (r * 0.5, z0 + H * 0.84)], 0.6, tag="iron")
    zc = z0 + H * collar
    s = 0.76 + (0.5 - 0.76) * (collar - 0.352) / 0.568
    ring = kit.lozenge(c, axis, L * s, W * s, 0)
    out.append(loft([[p + Z * (zc - 0.9) for p in kit._grow(ring, -0.2)], [p + Z * (zc - 0.7) for p in kit._grow(ring, 0.6)],
                     [p + Z * (zc + 0.7) for p in kit._grow(ring, 0.6)], [p + Z * (zc + 0.9) for p in kit._grow(ring, -0.2)]],
                    ["iron", "ember", "iron"], cap0=("iron", False), cap1=("iron", False)))
    for k in range(4):
        v = ring[k]
        d = V((v.x - c[0], v.y - c[1], 0)).normalized()
        p = V((v.x, v.y, zc)) + d * 0.4
        out.append(kit.beam(p, p + (d + Z * 0.3).normalized() * (2.0 + L * 0.3), 0.3, "iron", 0.0))
        r = (V((lip[k].x, lip[k].y, 0)) - cc).length
        zl = lip[k].z
        tall = crown if k % 2 == 0 else crown * 0.62
        out += fin(kit, cc, d, r - 0.5, [(r - 1.6, zl - 0.5), (r + 0.8, zl - 0.5), (r + 0.5, zl + tall * 0.45), (r - 0.6, zl + tall),
                                          (r - 1.6, zl + tall * 0.45)], 0.7, tag="iron")
    for f in slits:                                    # ember slits, two on every face
        sc = next(s0 + (s1 - s0) * (f - f0) / (f1 - f0) for (f0, s0), (f1, s1) in zip(prof, prof[1:]) if f0 <= f <= f1)
        ring = kit.lozenge(c, axis, L * sc, W * sc, 0)
        zs = z0 + H * f
        for i in range(4):
            a, b = ring[i], ring[(i + 1) % 4]
            m = (a + b) / 2
            t = (b - a).normalized()
            n = V((t.y, -t.x, 0))
            if n.dot(m - cc) < 0:
                n = -n
            for u in (-0.22, 0.22):
                q = m + t * ((b - a).length * u)
                out.append(prism_uz(q, t, n, [(-0.6, zs), (0.6, zs), (0.6, zs + 5.0), (0.0, zs + 6.5), (-0.6, zs + 5.0)],
                                    -0.9, 0.2, ["ember"] * 5, "ember", None))
    kit.fire(sum(throat, V((0, 0, 0))) / 4, "chimney")
    return out


def log_crib(kit, c, t, length, r, layers=5, per=3):
    """Felled Fangorn stacked in a crib: `layers` courses of `per` trunks, each course crossing the
    one below, `length` square, pinned by a tall pointed iron stake at each corner."""
    c = _v(c)
    t, n = _tn(t)
    out = []
    for j in range(layers):
        a, b = (t, n) if j % 2 == 0 else (n, t)
        z = c.z + r * 0.95 + j * r * 1.85
        for i in range(per):
            off = (i - (per - 1) / 2) * (length - 2 * r) / (per - 1)
            m = c + b * off + Z * (z - c.z)
            rr = r * (0.9 + 0.1 * math.sin(i * 2.3 + j))
            out.append(kit.log(m - a * length / 2, m + a * length / 2, rr))
    top = c.z + layers * r * 1.85 + 4.0
    for s in (-1, 1):
        for e in (-1, 1):
            p = c + t * (s * (length / 2 + 0.8)) + n * (e * (length / 2 + 0.8))
            out += blade_post(kit, p, top - c.z, w=0.45)
    return out


# ------------------------------------------------------------------ pass 3: the citadel's pair
VIEW = 52.0                                     # the RTS view's horizontal (camera azimuth -38), as the citadel's


def _view_axes(view=VIEW):
    a = math.radians(view)
    d = V((math.cos(a), math.sin(a), 0))
    return d, V((d.y, -d.x, 0))                 # along the view, and toward the camera


def blade_face(c, axis, L, W, z0, z1, lean, z, side, profile=None):
    """(point on a blade tower's face at height z, t along it, n out): the face from its front
    vertex (toward the camera) to its +axis end (side 1) or -axis end (side -1)."""
    from .shapes_spire import BROAD, scale
    f = (z - z0) / (z1 - z0)
    s = scale(f, profile or BROAD)
    a = math.radians(axis)
    d, p = V((math.cos(a), math.sin(a), 0)), V((-math.sin(a), math.cos(a), 0))
    ctr = V((c[0] + lean[0] * f, c[1] + lean[1] * f, 0))
    front = ctr - p * W * s
    end = ctr + d * (side * L * s)
    t = (end - front).normalized()
    n = V((t.y, -t.x, 0))
    if n.dot((front + end) / 2 - ctr) < 0:
        n = -n
    return (front + end) / 2, t, n


def hand_slot(kit, m, t, n, z0, w, h, d0=-0.9, d1=1.2):
    """The White Hand in a pointed-arch slot (EA's 35-degree head) on a face at m: a sunk black
    field, a silver frame, the Hand raised in it."""
    head = (w / 2) / math.tan(math.radians(35.0) / 2) * 0.5
    poly = [(-w / 2, z0), (w / 2, z0), (w / 2, z0 + h - head), (0, z0 + h), (-w / 2, z0 + h - head)]
    out = [prism_uz(m, t, n, poly, d0, d1, ["trim"] * 5, "stoneB", None)]
    for (u0, za), (u1, zb) in zip(poly, poly[1:] + poly[:1]):
        out.append(kit.beam(m + t * u0 + Z * za + n * (d1 + 0.1), m + t * u1 + Z * zb + n * (d1 + 0.1), 0.3, "trim"))
    out += kit.hand(m, t, n, 0.0, z0 + h * 0.12, min(w * 0.95, h * 0.62), d1, th=0.35, back="mark")
    return out


def blade_pair(kit, m, half, L, W, z0, z1, lean=1.6, flare=1.15, slits=(0.42, 0.54, 0.66), hand=None, view=VIEW,
               fins=3, fin_reach=1.3, slit_w=1.0):
    """The citadel's pair: two matching blade towers either side of m (x, y) `half` out along the
    view's horizontal, mirrored about m: lozenges along the view (broad faces to the camera), a
    flared spurred foot, set-back steps, three layered fins a face, silver edges, ember slits, a
    needle; each leaning in toward m by `lean` at its tip. z0: one foot height or (left, right).
    hand (z, w, h): the White Hand in a pointed-arch slot on each one's outer face. Returns
    (solids, [(x, y) centres])."""
    from .shapes_spire import BROAD
    d, _ = _view_axes(view)
    zs = z0 if isinstance(z0, (tuple, list)) else (z0, z0)
    out, cs = [], []
    for e, zb in zip((-1, 1), zs):
        c = V((m[0], m[1], 0)) + d * (e * half)
        ln = (-d.x * e * lean, -d.y * e * lean)
        out += kit.blade_tower((c.x, c.y), view, L, W, zb, z1, lean=ln, flare=flare, fins=fins, slits=slits, profile=BROAD,
                               fin_reach=fin_reach, slit_w=slit_w)
        if hand:
            zh, w, h = hand
            p, t, n = blade_face((c.x, c.y), view, L, W, zb, z1, ln, zh + h / 2, e)
            out += hand_slot(kit, p, t, n, zh, w, h)
        cs.append((c.x, c.y))
    return out, cs


def blades_at(kit, cs, L, W, z0, z1, lean=1.2, hand=None, axis=VIEW, flare=1.15, fins=1, slits=(0.35, 0.5, 0.65),
              fin_reach=1.1, slit_w=0.9):
    """A matching pair of blade towers at the two centres `cs`, mirrored about their midpoint
    (a gable, a gate, a pit between them): lozenges along `axis` (the view's horizontal: broad
    faces to the camera), each leaning toward the midpoint by `lean` at its tip; hand (z, w, h)
    on each one's outer face (the face toward its own side along the axis)."""
    a = math.radians(axis)
    d = V((math.cos(a), math.sin(a), 0))
    mid = (V((cs[0][0], cs[0][1], 0)) + V((cs[1][0], cs[1][1], 0))) / 2
    zs = z0 if isinstance(z0, (tuple, list)) else (z0, z0)
    out = []
    for (x, y), zb in zip(cs, zs):
        c = V((x, y, 0))
        k = (mid - c)
        ln = tuple(k.normalized() * lean)[:2] if k.length > 1e-6 else (0.0, 0.0)
        out += kit.blade_tower((x, y), axis, L, W, zb, z1, lean=ln, flare=flare, fins=fins, slits=slits,
                               profile=_broad(), fin_reach=fin_reach, slit_w=slit_w)
        if hand:
            zh, w, h = hand
            side = 1 if (c - mid).dot(d) >= 0 else -1
            p, t, n = blade_face((x, y), axis, L, W, zb, z1, ln, zh + h / 2, side)
            out += hand_slot(kit, p, t, n, zh, w, h)
    return out


def _broad():
    from .shapes_spire import BROAD
    return BROAD


def birth_spire(kit, c, r0, z0, apex, rk, zk, rot=VIEW, w=1.8):
    """The birthing-frame made pointed (pass 3: pass 2's six ribs and ring read round): four knife
    ribs on the diagonals of a square turned to `rot`, rising from the pit's rim (r0, z0) to a knee
    (rk, zk), bound there by four iron bars with silver lips, then bending in to a needle at
    apex; a great hook on its chain down into the pit, meat hooks at the band's corners."""
    c = _v(c)
    out = []
    corners = []
    for i in range(4):
        ang = math.radians(rot + 45.0 + 90.0 * i)
        d = (math.cos(ang), math.sin(ang))
        out += fin(kit, c, d, r0 + 99.0, [(r0 - 1.6, z0 - 1.0), (r0 + 3.2, z0 - 1.0), (rk + 2.6, zk), (rk - 1.4, zk - 2.6)],
                   w, tag="iron")
        out += fin(kit, c, d, 0.5, [(rk - 1.4, zk - 2.6), (rk + 2.6, zk), (0.8, apex - 0.5), (0.2, apex - 4.0)], w * 0.85,
                   tag="iron")
        corners.append(V((c.x + d[0] * (rk + 0.4), c.y + d[1] * (rk + 0.4), 0)))
    for a, b in zip(corners, corners[1:] + corners[:1]):          # the band: four riveted iron bars, silver lips
        out.append(kit.beam(a + Z * (zk - 1.2), b + Z * (zk - 1.2), 0.75, "iron"))
        out.append(kit.beam(a + Z * (zk - 0.2), b + Z * (zk - 0.2), 0.3, "trim"))
    out.append(kit.beam(V((c.x, c.y, apex - 2.0)), V((c.x, c.y, apex + 7.0)), 0.9, "iron", 0.0))
    out.append(kit.beam(V((c.x, c.y, apex - 1.5)), V((c.x, c.y, apex + 0.5)), 1.3, "trim"))
    for p in corners:
        out += kit.hook(p + Z * (zk - 2.4), 1.5, chain=3.5)
    out += kit.chain(V((c.x, c.y, apex - 3.0)), V((c.x, c.y, z0 + 5.0)), link=1.8, w=0.6, th=0.25)
    out += kit.hook(V((c.x, c.y, z0 + 5.0)), 2.6, chain=0.0)
    return out
