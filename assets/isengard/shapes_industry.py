"""The Isengard production group's shared pieces (Blender side): the armory, furnace, lumber
mill, siege works, uruk pit, warg pit and the Dunlending hall (tavern). Functions of the kit
(`kit` is the faction's IsengardShapes, assets/isengard/shapes.py), not a mixin: the citadel's
kit stays as it is. Every piece returns closed solids tagged with IsengardAtlas regions; every
fire it lights records its point through kit.fire (a recipe copies them into `fire_points`).

Placement as in the kit: c a ground point, t a horizontal direction along the piece, n = t
turned +90 degrees (its front), z up.

    blade_post(kit, c, h, w)                 a lozenge iron post rising to a needle, a silver edge
    banner_frame(kit, c, t, w, length, h)    a heavy player-colour banner on a free-standing iron
                                             frame: two blade posts, braced feet, the Hand on it
    quench_trough(kit, c, t, L, w)           an iron-banded trough of dark water
    forge_bay(kit, c, t, s)                  hearth, anvil with white-hot work, bellows, a square
                                             crucible, quench trough, ingots and a tool rack
    birth_pit(kit, c, r)                     an iron-kerbed glowing pit, grate bars, blade posts
                                             and chains: where the Uruk-hai are pulled from the mud
    pickets(kit, pts, h)                     a row of iron pickets, lozenge blades on two rails
    roof_crest(kit, p, q, count, h)          knife-edge iron blades along a ridge
    hook_rail(kit, p, q, count)              an iron bar on its end posts, meat hooks on chains
    armour_stand(kit, c, t, s)               an Uruk harness on a cross: breastplate, pointed
                                             helm, a shield with the Hand, a pike behind
    blade_rack(kit, c, t, w, count)          an A-frame rack of cleavers and pointed blades
    fin(kit, c, out, r0, prof, w)            a knife-edge fin from any convex (r, z) outline, silver
                                             on its front edges, ember slits in its faces
    layered_fin(kit, c, out, rb, rf, rt, zt) a buttress of two layered fins leaning on a mound
    logged(kit, pieces)                      run a design with the fire log on; prints FIRE_POINTS

The big pointed masses (pass 2) are in shapes_industry_big.py.
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz


def _v(p):
    return V((p[0], p[1], p[2] if len(p) > 2 else 0.0))


def _tn(t):
    t = V((t[0], t[1], 0)).normalized()
    return t, V((-t.y, t.x, 0))


def blade_post(kit, c, h, w=0.55, edge="trim", z0=None):
    """A lozenge iron post from the ground at c (or z0) to h above it, tapering in its top third to
    a needle; a silver fin up its front edge."""
    c = _v(c)
    zb = c.z if z0 is None else z0
    a, b = V((c.x, c.y, zb - 0.4)), V((c.x, c.y, zb + h * 0.72))
    out = [kit.beam(a, b, w, "iron"), kit.beam(b, V((c.x, c.y, zb + h)), w * 1.05, "iron", 0.0)]
    out.append(kit.beam(b - Z * 0.4, b + Z * 0.5, w * 1.5, edge))            # a silver collar at the taper
    return out


def banner_frame(kit, c, t, w=7.0, length=16.0, h=None, mark=True):
    """A banner `w` wide and `length` long on a free-standing iron frame at c (ground), the cloth
    along t facing n: two blade posts, splayed braces at their feet, kit.banner's top bar, rods
    and weighted foot between them. The cloth takes the player's colour."""
    c = _v(c)
    t, n = _tn(t)
    top = c.z + (h if h is not None else length + 6.0)
    out = []
    for s in (-1, 1):
        p = c + t * (s * (w / 2 + 1.0))
        out += blade_post(kit, p, top - c.z + 3.5, w=0.42)
        for e in (-1, 1):                                    # braced feet, fore and aft
            out.append(kit.beam(p + Z * 3.2, p + n * (e * 2.6) - Z * 0.3, 0.26, "iron"))
    out += kit.banner(c, t, n, 0.0, top, w, length, d=0.0, mark=mark)
    return out


def quench_trough(kit, c, t, L=4.4, w=1.8, h=1.4):
    """An iron trough L long along t, dark water to its brim, two silver bands."""
    c = _v(c)
    t, n = _tn(t)
    ring = lambda s, z: [c + t * (-L / 2 * s) + n * (-w / 2 * s) + Z * z, c + t * (L / 2 * s) + n * (-w / 2 * s) + Z * z,  # noqa: E731
                         c + t * (L / 2 * s) + n * (w / 2 * s) + Z * z, c + t * (-L / 2 * s) + n * (w / 2 * s) + Z * z]
    out = [loft([ring(0.9, -0.3), ring(1.0, h), ring(0.85, h), ring(0.85, h - 0.3)], ["iron", "trim", "water"],
                cap0=("iron", False), cap1=("water", True))]
    for u in (-L * 0.3, L * 0.3):
        p = c + t * u
        out.append(kit.beam(p - n * (w / 2 + 0.12) + Z * 0.1, p - n * (w / 2 + 0.12) + Z * (h - 0.1), 0.14, "trim"))
        out.append(kit.beam(p + n * (w / 2 + 0.12) + Z * 0.1, p + n * (w / 2 + 0.12) + Z * (h - 0.1), 0.14, "trim"))
    return out


def forge_bay(kit, c, t, s=1.0, bellows=True, crucible=True, rack=True, trough=True):
    """A forge at c, its front toward n (t along it): a stone hearth (glowing bed, hood, flue) with
    an anvil and white-hot work before it, the bellows at its +t side, a crucible and ingots at
    its -t side, a quench trough by the anvil and a tool rack behind. Fire: hearth, crucible."""
    c = _v(c)
    t, n = _tn(t)
    out = kit.hearth(c, t, n, w=5.0 * s, d=3.4 * s, h=2.6 * s, hood=4.2 * s)
    anvil = c + n * (4.8 * s) + t * (1.2 * s)
    out += kit.anvil(anvil, t, 1.1 * s) + kit.glowing_work(anvil + Z * (3.1 * s), t, 1.1 * s)
    if bellows:
        out += kit.bellows(c + t * (4.4 * s) + n * (0.4 * s), -t, 1.0 * s)
    if crucible:
        from .shapes_industry_big import square_crucible
        out += square_crucible(kit, c - t * (4.4 * s) + n * (2.2 * s), 1.3 * s, 2.2 * s)
        out += kit.ingots(c - t * (4.0 * s) + n * (5.4 * s), t, 3, 0.9 * s)
    if trough:
        out += quench_trough(kit, anvil + t * (3.6 * s) + n * (0.6 * s), n, 3.6 * s, 1.5 * s, 1.3 * s)
    if rack:
        out += kit.tool_rack(c - n * (2.6 * s) - t * (4.0 * s), t, n, 3.6 * s, 3.6 * s)
    return out


def birth_pit(kit, c, r, k=8, posts=4, bars=3):
    """A birthing pit r across at c (ground): an iron kerb of k sides, glowing mud sunk inside,
    grate bars across, blade posts round it with chains slung between. Fire: embers."""
    c = _v(c)
    ring = lambda rr, z: kit.ring(c.x, c.y, rr, c.z + z, k)                     # noqa: E731
    out = [loft([ring(r * 1.12, -0.4), ring(r * 1.05, 1.2), ring(r * 0.86, 1.2), ring(r * 0.86, 0.6)],
                ["iron", "trim", "ember"], cap0=("iron", False), cap1=("ember", True))]
    for i in range(bars):
        y = -r * 0.6 + r * 1.2 * (i + 0.5) / bars
        out.append(kit.beam(c + V((-r * 0.9, y, 1.3)), c + V((r * 0.9, y, 1.3)), 0.2, "iron"))
    tops = []
    for i in range(posts):
        a = 2 * math.pi * (i + 0.5) / posts
        p = c + V((math.cos(a), math.sin(a), 0)) * r * 1.22
        out += blade_post(kit, p, 6.5, w=0.4)
        tops.append(p + Z * 4.6)
    for i in range(posts):
        out += kit.chain(tops[i], tops[(i + 1) % posts], link=1.3)
    kit.fire(c + Z * 1.0, "embers")
    return out


def pickets(kit, pts, h, pitch=2.8, w=0.9, rails=(0.3, 0.7)):
    """Iron pickets along the polyline pts (ground points): lozenge blades `pitch` apart rising to
    points (silver front edges), two iron rails through them."""
    P = [_v(p) for p in pts]
    out = []
    for a, b in zip(P, P[1:]):
        d = b - a
        L = d.length
        t = d.normalized()
        n = V((-t.y, t.x, 0))
        m = max(1, int(L / pitch))
        for i in range(m + 1):
            p = a + d * (i / m)
            hh = h * (0.9 + 0.1 * math.sin(i * 1.7))
            out.append(prism_uz(p, n, t, [(-w, a.z - 0.4), (w, a.z - 0.4), (w * 0.8, a.z + hh * 0.8), (0, a.z + hh),
                                         (-w * 0.8, a.z + hh * 0.8)], -0.28, 0.28, ["iron", "trim", "trim", "trim", "iron"],
                                "iron", "iron"))
        for f in rails:
            out.append(kit.beam(a + Z * (h * f), b + Z * (h * f), 0.26, "iron"))
    return out


def roof_crest(kit, p, q, count, h, w=0.35, d=1.4):
    """`count` knife-edge iron blades standing along a ridge from p to q (their feet at the
    ridge), `h` tall, leaning back, a silver edge; a bar along their feet."""
    p, q = _v(p), _v(q)
    t = (q - p).normalized()
    out = [kit.beam(p, q, 0.35, "iron")]
    for i in range(count):
        f = (i + 0.5) / count
        c = p.lerp(q, f)
        hh = h * (1.0 if i % 2 == 0 else 0.7)
        out.append(prism_uz(V((c.x, c.y, 0)), t, V((-t.y, t.x, 0)), [(-d, c.z - 0.3), (d, c.z - 0.3), (d * 0.3, c.z + hh * 0.7),
                                                                   (-d * 0.2, c.z + hh)],
                            -w, w, ["iron", "trim", "trim", "iron"], "iron", "iron"))
    return out


def hook_rail(kit, p, q, count=3, drop=2.2):
    """An iron bar from p to q on two end posts, `count` meat hooks on chains under it."""
    p, q = _v(p), _v(q)
    out = [kit.beam(p, q, 0.3, "iron")]
    for e in (p, q):
        out.append(kit.beam(V((e.x, e.y, 0)) - Z * 0.3, e + Z * 0.6, 0.32, "iron"))
        out.append(kit.beam(e + Z * 0.6, e + Z * 2.2, 0.36, "trim", 0.0))
    for i in range(count):
        out += kit.hook(p.lerp(q, (i + 0.5) / count) - Z * 0.3, 1.3, chain=drop)
    return out


def armour_stand(kit, c, t, s=1.0):
    """An Uruk harness on a cross stand at c facing n: a black breastplate with a silver ridge,
    pauldron blades, a pointed helm, a shield with the White Hand, a pike standing behind."""
    c = _v(c)
    t, n = _tn(t)
    out = [kit.beam(c - Z * 0.3, c + Z * 7.4 * s, 0.22 * s, "timber"),
           kit.beam(c + Z * 5.6 * s - t * 1.9 * s, c + Z * 5.6 * s + t * 1.9 * s, 0.2 * s, "timber")]
    body = c + Z * 3.4 * s
    ring = lambda z, sw, sd, fr: [body + t * (-sw) + Z * z, body + n * fr + Z * z, body + t * sw + Z * z,     # noqa: E731
                                  body - n * sd + Z * z]
    out.append(loft([ring(0.0, 1.1 * s, 0.7 * s, 0.9 * s), ring(1.6 * s, 1.4 * s, 0.8 * s, 1.2 * s),
                     ring(2.6 * s, 1.5 * s, 0.8 * s, 1.0 * s)], ["stoneB", "stoneB"], cap0=("iron", True), cap1=("iron", True)))
    out.append(kit.beam(body + n * 1.25 * s + Z * 0.2 * s, body + n * 1.05 * s + Z * 2.5 * s, 0.14 * s, "trim"))
    for e in (-1, 1):                                        # pauldrons: blades out over the shoulders
        sh = body + t * (e * 1.5 * s) + Z * 2.5 * s
        out.append(kit.beam(sh - t * e * 0.4 * s, sh + t * e * 1.2 * s + Z * 0.9 * s, 0.4 * s, "iron", 0.05))
    helm = body + Z * 3.4 * s
    out.append(loft([[helm + t * (-0.7 * s), helm + n * 0.8 * s, helm + t * 0.7 * s, helm - n * 0.7 * s],
                     [helm + t * (-0.6 * s) + Z * 1.1 * s, helm + n * 0.7 * s + Z * 1.1 * s, helm + t * 0.6 * s + Z * 1.1 * s,
                      helm - n * 0.6 * s + Z * 1.1 * s], [helm + Z * 2.6 * s - n * 0.3 * s] * 4],
                    ["iron", "iron"], cap0=("iron", True), cap1=("iron", False)))
    out += kit.shield(c + n * 1.4 * s + t * 1.6 * s, t, n, 0.0, c.z + 0.2, 3.6 * s, d=0.0)
    p = c - n * 0.8 * s - t * 1.0 * s
    out.append(kit.beam(p - Z * 0.3, p + Z * 9.0 * s, 0.14 * s, "timber"))
    out.append(kit.beam(p + Z * 9.0 * s, p + Z * 11.0 * s, 0.3 * s, "iron", 0.0))
    return out


def blade_rack(kit, c, t, w=5.0, count=4, h=4.2):
    """An A-frame rack w long along t: two iron A-frames and a top bar, `count` cleavers and
    pointed blades hung from it (silver edges)."""
    c = _v(c)
    t, n = _tn(t)
    out = []
    for e in (-1, 1):
        top = c + t * (e * w / 2) + Z * h
        for s in (-1, 1):
            out.append(kit.beam(c + t * (e * w / 2) + n * (s * 1.4) - Z * 0.3, top, 0.2, "iron"))
    out.append(kit.beam(c - t * (w / 2 + 0.4) + Z * h, c + t * (w / 2 + 0.4) + Z * h, 0.22, "iron"))
    for i in range(count):
        u = -w / 2 + w * (i + 0.5) / count
        a = c + t * u + Z * (h - 0.3)
        for s in (-1, 1):
            poly = [(-0.35, -h * 0.72), (0.35, -h * 0.55), (0.35, 0.0), (-0.35, 0.0)] if i % 2 else \
                [(0.0, -h * 0.8), (0.4, -h * 0.5), (0.35, 0.0), (-0.35, 0.0), (-0.4, -h * 0.5)]
            out.append(prism_uz(a + n * (s * 0.5), t, n, [(x, a.z + z) for x, z in poly], -0.06, 0.06, ["trim"] * len(poly),
                                "iron", "iron"))
    return out


def logged(kit, pieces):
    """Run a design with the kit's fire log on: `pieces` a function of the kit returning solids.
    Prints the fire points the design lit ("FIRE_POINTS [...]", in the geometry log) for the
    recipe's `fire_points`; returns the solids."""
    kit.fire_log = []
    try:
        out = pieces(kit)
        print("FIRE_POINTS", kit.fire_log)
    finally:
        kit.fire_log = None
    return out


def fin(kit, c, out, r0, prof, w, slits=(), tag="stoneA", edge="trim"):
    """A knife-edge fin of black stone standing out from c along `out`: prof a convex (r, z)
    polygon from the back foot round the front edge to the back top (r measured from c), w thick,
    silver on its front edges (every edge whose r is past r0 on both ends), ember slits
    ((r, z0, z1) each) sunk into both its faces."""
    c = _v(c)
    o = V((out[0], out[1], 0)).normalized()
    s = V((-o.y, o.x, 0))
    tags = [edge if a[0] > r0 and b[0] > r0 else tag for a, b in zip(prof, prof[1:] + prof[:1])]
    res = [prism_uz(V((c.x, c.y, 0)), o, s, prof, -w / 2, w / 2, tags, tag, tag)]
    for r, z0, z1 in slits:
        for e in (-1, 1):
            res.append(prism_uz(V((c.x, c.y, 0)) + s * (e * w / 2), o, s * e,
                                [(r - 0.5, z0), (r + 0.5, z0), (r + 0.5, z1 - 1.0), (r, z1), (r - 0.5, z1 - 1.0)],
                                -0.6, 0.18, ["ember"] * 5, "ember", None))
    return res


def layered_fin(kit, c, out, r_back, r_foot, r_top, z_top, w=2.4, slits=True, z0=-0.4):
    """A buttress of two layered fins (Isengard's faces in layers): a tall thin knife reaching
    to z_top, and a lower, thicker one before it; the tall one's front edge runs from r_foot at
    the ground to r_top at z_top (its point), its back in what it leans on (r_back)."""
    tall = [(r_back, z0), (r_foot, z0), (r_top, z_top), (r_back, z_top * 0.78)]
    zs = z_top * 0.42
    low = [(r_back + 2.0, z0), (r_foot + 3.0, z0), (r_foot + (r_top - r_foot) * 0.42 - 1.0, zs),
           (r_back + 2.0, zs * 0.9)]
    sl = [(r_foot + (r_top - r_foot) * f - 1.2, z_top * f - 3.5, z_top * f + 3.5) for f in (0.55, 0.72)] if slits else ()
    return fin(kit, c, out, r_back + 0.5, tall, w, slits=sl) + fin(kit, c, out, r_back + 2.5, low, w * 1.7)

