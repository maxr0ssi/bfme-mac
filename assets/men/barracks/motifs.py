"""Motifs the Men production and economy buildings share (barracks, archer range, stable, forge,
workshop, farm, market place, stoneworks, and their level-up meshes), built on the citadel's kit
(assets/men/shapes.py, MenShapes: `kit`). Blender side (mathutils).

The API is stable: other recipes import it. Add functions and keyword arguments; never rename or
reorder positional ones.

Conventions (the kit's): a wall face is (a, t, n): an anchor `a` on it (z = 0), `t` along it and
`n` out of it, horizontal unit vectors with t x n = -z (seen from outside, u grows to the right).
u is measured along t from a, z is absolute, d along n (0 = the face; negative = into the wall,
used to bury backs). Every function returns a list of closed solids (sagekit.blender.geometry).
Tags are atlas regions (assets/men/atlas.py): stoneA plain, stoneB dressed, top / course bands,
slate, roof, window / slit glass, trim steel, gilt, enamel sable, relief white stone, iron, cloth
(the player's colour: leaves for the house model on a body; never on a level-up mesh).

    face            (a, t, n) of a vertical face through a point with an outward normal
    box, slab       an axis-aligned block; a block on a face (u0..u1, z0..z1, d0..d1)
    closed          keep every face of some solids (for pieces on a one-sided shell)
    octagon         a chamfered square outline (for sweeps round towers and domes)
  windows
    window_surround jambs, a voussoir arch (or flat lintel) and keystone, a sill on corbels, an
                    optional drip hood - framed round a window EA painted on the wall
    window          a new window: a glass pane (EA's painted window or slit) and its surround
    window_pediment a little triangular pediment on two consoles over a window
  courses, cornices, parapets
    course          a string course (a band standing out of a face)
    cornice         fillet, dentils, corona and cymatium along a face
    band_path       one step of a moulding swept round a polyline (closed or open)
    corbel_table    a row of the kit's two-step corbels
    parapet         a parapet wall with square merlons and capstones
    machicolation   corbels, a slab standing out, a sable band, parapet and merlons (the citadel's)
    plinth          a battered base course
    quoins          alternating long and short corner stones up an edge
    pilaster        a flat pilaster with a moulded base and capital
  roofs
    ridge           a steel ridge roll with cresting spikes and gilt end knobs
    eave            a fascia with steel edge and brackets under a roof's edge
    raking_coping   coping stones up a gable's rakes, acroteria at the eaves and apex
    crown_dome      the citadel's dome dress: steel eave band, ribs, lantern, mast, orb and spike
  heraldry and banners
    roundel         the White Tree on a sable disc in a steel ring, seven gilt studs round it
    star_frieze     a sable band with the seven gilt stars
    banner_mount    a house-colour banner (kit.banner) on two stone consoles, a steel spear crest
    mast            a free-standing flag mast: stone socle, steel mast, gilt orb, spike
    knob            a short finial for low tops: steel collar, gilt orb, steel spike (to `top`)
    pennant         a swallow-tailed cloth pennant flying from a mast
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import box_rings, loft, prism_uz, sweep

Z = V((0, 0, 1))


# ---------------------------------------------------------------------------------------- frames
def face(point, normal):
    """(a, t, n) for a vertical face through `point` (x, y) with outward normal (nx, ny)."""
    n = V((normal[0], normal[1], 0)).normalized()
    return V((point[0], point[1], 0)), V((-n.y, n.x, 0)), n


def box(x0, x1, y0, y1, z0, z1, tags="stoneA", cap0=("stoneB", False), cap1=("top", True)):
    """An axis-aligned block; tags per side (0: -y, 1: +x, 2: +y, 3: -x) or one for all."""
    return loft([box_rings((x0, x1), (y0, y1), z0, 0), box_rings((x0, x1), (y0, y1), z1, 0)], [tags],
                cap0=cap0, cap1=cap1)


def slab(a, t, n, u0, u1, z0, z1, d0, d1, tags=("stoneB", "stoneB", "top", "stoneB"), front="stoneA", back=None):
    """A block on a face: u0..u1, z0..z1, d0..d1; tags bottom, right, top, left."""
    return prism_uz(a, t, n, [(u0, z0), (u1, z0), (u1, z1), (u0, z1)], d0, d1, list(tags), front, back)


def closed(solids):
    """Keep every face of `solids`, the buried ones too. EA's level-up walls are one-sided shells
    (nothing behind their outer faces), so a piece with an open back lets the sky check look in
    behind the shell and see the backs of its own faces; closed, it cannot."""
    for s in solids:
        for p in s.polys:
            p[2] = True
    return solids


def octagon(cx, cy, half, ch, closed=True):
    """A chamfered square outline [(x, y)] round (cx, cy) (the kit's domes and towers)."""
    ring = box_rings((cx - half, cx + half), (cy - half, cy + half), 0.0, ch)
    pts = [(p.x, p.y) for p in ring]
    return pts + [pts[0]] if closed else pts


# ---------------------------------------------------------------------------------------- windows
def window_surround(kit, a, t, n, u, half, z0, spring, rise=None, w=0.6, d=0.55, key=True, sill=True,
                    hood=False, count=7, back=-0.25):
    """A frame round a window of half-width `half` whose sill is at z0 and whose arch springs at
    `spring` and rises `rise` (default: a round arch, rise = half; 0: a flat lintel). Jambs w wide
    and d proud either side, voussoirs and a raised keystone, a sill on two corbels; `hood` adds a
    drip moulding over the arch. Nothing covers the opening itself. `back`: how deep the pieces
    reach into the wall (deeper on a battered face, whose top leans away from them)."""
    rise = half if rise is None else rise
    count = max(3, min(count, int(math.pi * half / 0.36)))      # the kit's 0.12 joints need room
    c = a + t * u
    out = []
    for e in (-1, 1):
        u0, u1 = sorted((e * half, e * (half + w)))
        out.append(slab(a, t, n, u + u0, u + u1, z0, spring, back, d, ("stoneB", "stoneB", None, "stoneB"), "stoneB"))
    if rise > 0.05:
        top = spring + rise + w
        kz = (0.5 * w + 0.3, top + 0.5, 0.3) if key else None
        out += kit.voussoirs(c, t, n, (half, rise, spring), (half + w, rise + w, spring), back, d, count=count, key=kz)
        if hood:
            out += kit.voussoirs(c, t, n, (half + w + 0.05, rise + w + 0.05, spring), (half + w + 0.45, rise + w + 0.45, spring),
                                 back, d + 0.25, count=9, gap=0.0)
            for e in (-1, 1):
                out.append(slab(a, t, n, u + e * (half + w + 0.25) - 0.35, u + e * (half + w + 0.25) + 0.35,
                                spring - 0.9, spring, back, d + 0.3, front="course"))
    else:
        top = spring + 1.3 * w
        out.append(slab(a, t, n, u - half - w - 0.15, u + half + w + 0.15, spring, top, back, d, front="stoneB"))
        if key:
            out.append(prism_uz(a, t, n, [(u - 0.45 * w - 0.2, spring - 0.25), (u + 0.45 * w + 0.2, spring - 0.25),
                                          (u + 0.6 * w + 0.3, top + 0.35), (u - 0.6 * w - 0.3, top + 0.35)],
                                back, d + 0.3, ["stoneB", "stoneB", "top", "stoneB"], "stoneA", None))
    if sill:
        s = half + w + 0.35
        out.append(slab(a, t, n, u - s, u + s, z0 - 0.55, z0, back, d + 0.35, front="course"))
        for e in (-1, 1):
            m = u + e * (half + 0.5 * w)
            out.append(slab(a, t, n, m - 0.45, m + 0.45, z0 - 1.5, z0 - 0.55, back, d, ("stoneB", "stoneB", None, "stoneB"), "stoneB"))
    return out


def window(kit, a, t, n, u, half, z0, spring, rise=None, glass="window", pane=0.12, **surround):
    """A new window at u: a glass pane (atlas `glass`: EA's arched window, or "slit") on a slab
    `pane` proud of the face, framed by window_surround (its keyword arguments pass through)."""
    rise = half if rise is None else rise
    k = 8
    poly = [(u - half, z0), (u + half, z0)]
    if rise > 0.05:
        poly += [(u + half * math.cos(math.pi * i / k), spring + rise * math.sin(math.pi * i / k)) for i in range(k + 1)]
    else:
        poly += [(u + half, spring), (u - half, spring)]
    out = [prism_uz(a, t, n, poly, min(-0.3, surround.get("back", -0.3)), pane, [None] * len(poly), glass, None)]
    return out + window_surround(kit, a, t, n, u, half, z0, spring, rise, **surround)


def window_pediment(a, t, n, u, half, z, rise=None, d=0.7, tympanum="enamel"):
    """A triangular pediment `half` wide at its base z (over a window's lintel or arch), on two
    consoles hanging below its ends; the tympanum sable, the raking cornices in moulding."""
    rise = 0.45 * half if rise is None else rise
    out = [prism_uz(a, t, n, [(u - half, z), (u + half, z), (u, z + rise)], -0.25, d - 0.2, [None, "stoneB", "stoneB"], tympanum, None),
           slab(a, t, n, u - half - 0.3, u + half + 0.3, z - 0.5, z, -0.25, d + 0.1, front="course")]
    for e in (-1, 1):
        out.append(prism_uz(a, t, n, [(u, z + rise), (u + e * half, z), (u + e * (half + 0.9), z), (u, z + rise + 0.9)],
                            -0.25, d, ["stoneB", "stoneB", "top", None], "course", None))
        m = u + e * (half - 0.2)
        out.append(prism_uz(a, t, n, [(m - 0.35, z - 1.8), (m + 0.35, z - 1.8), (m + 0.45, z - 0.5), (m - 0.45, z - 0.5)],
                            -0.25, d - 0.1, ["stoneB", "stoneB", None, "stoneB"], "stoneB", None))
    return out


# ---------------------------------------------------------------------------------------- courses
def course(a, t, n, u0, u1, z, h=0.8, d=0.6, tag="course", back=-0.25):
    """A string course: a band h high standing d out of the face from u0 to u1, ends closed."""
    return [slab(a, t, n, u0, u1, z, z + h, back, d, ("stoneB", "stoneB", "top", "stoneB"), tag)]


def cornice(a, t, n, u0, u1, z, depth=1.5, dentils=True, pitch=1.1, back=-0.25):
    """A moulded cornice from z up (about 2 high): a fillet, a row of dentils, the corona standing
    `depth` out and a cymatium on top; the ends run out `depth` past u0..u1 are not added (the
    cornice stops square with the face)."""
    out = [slab(a, t, n, u0, u1, z, z + 0.4, back, 0.4 * depth, front="course")]
    if dentils:
        k = max(1, int((u1 - u0 - 0.3) / pitch))
        g = (u1 - u0 - 0.3) / k
        for i in range(k):
            s = u0 + 0.15 + i * g + 0.2 * g
            out.append(slab(a, t, n, s, s + 0.55 * g, z + 0.4, z + 0.95, back, 0.62 * depth,
                            ("stoneB", "stoneB", None, "stoneB"), "stoneB"))
    else:
        out.append(slab(a, t, n, u0, u1, z + 0.4, z + 0.95, back, 0.62 * depth, front="stoneB"))
    out.append(slab(a, t, n, u0, u1, z + 0.95, z + 1.75, back, depth, ("stoneB", "stoneB", None, "stoneB"), "course"))
    out.append(prism_uz(a, t, n, [(u0, z + 1.75), (u1, z + 1.75), (u1, z + 2.15), (u0, z + 2.15)], back, depth - 0.15,
                        ["stoneB", "stoneB", "top", "stoneB"], "top", None, bat=0.3))
    return out


def band_path(path, z0, z1, d0, d1, tags="course", center=(0, 0), top="top", ends=True):
    """One step of a moulding swept along a polyline (closed when its ends meet): z0..z1, from d0
    to d1 out of the path (away from `center`). tags: the front tag or [bottom, front, top, back]."""
    if isinstance(tags, str):
        tags = ["stoneB", tags, top, None]
    prof = [(d0, z0), (d1, z0), (d1, z1), (d0, z1)]
    return sweep(path, prof, tags, cap_start=ends, cap_end=ends, center=center)[0]


def corbel_table(kit, a, t, n, u0, u1, z, pitch=3.2, w=0.5, d1=0.8, d2=1.7, h=1.5):
    """A row of the kit's two-step corbels from u0 to u1 (first and last `pitch`/2 in), from z up."""
    k = max(1, int(round((u1 - u0) / pitch)))
    g = (u1 - u0) / k
    out = []
    for i in range(k):
        out += kit.corbel(a, t, n, u0 + (i + 0.5) * g, z, w=w, z1=z + h, z2=z + 2 * h, d1=d1, d2=d2)
    return out


def parapet(kit, a, t, n, u0, u1, z, d0, d1, h=1.2, merlon=2.6, w=2.2, gap=1.6, cap=0.5):
    """A parapet wall d0..d1 from z to z+h with square merlons (and capstones) on it."""
    out = [slab(a, t, n, u0, u1, z, z + h, d0, d1, (None, "stoneA", "top", "stoneA"), "stoneA", "stoneA")]
    return out + kit.merlons(a, t, n, u0, u1, z + h, d0, d1, w=w, gap=gap, h=merlon, cap=cap)


def machicolation(kit, a, t, n, u0, u1, z, out=1.8, pitch=3.2, band=True, merlon=2.4, stars=False):
    """The citadel's gallery on a straight run: two-step corbels from z, a slab standing `out`
    (its front a sable band when `band`, silver stars painted on it by StarBand if the recipe adds
    that layer), a parapet and square merlons. About 7.5 high."""
    zs, zw = z + 3.4, z + 5.4
    res = corbel_table(kit, a, t, n, u0, u1, z, pitch=pitch, d1=0.45 * out, d2=out, h=1.7)
    res.append(slab(a, t, n, u0, u1, zs, zw, -0.4, out, ("stoneB", "stoneB", "top", "stoneB"), "enamel" if band else "course"))
    res += parapet(kit, a, t, n, u0, u1, zw, out - 1.3, out - 0.1, h=0.9, merlon=merlon, w=2.0, gap=1.5)
    return res


def plinth(a, t, n, u0, u1, z0, h=2.4, out=0.9, back=-0.25):
    """A battered base course: out at the foot, leaning back to the face at z0+h, a band on top."""
    return [prism_uz(a, t, n, [(u0, z0), (u1, z0), (u1, z0 + h), (u0, z0 + h)], back, out, ["stoneB", "stoneB", "top", "stoneB"],
                     "stoneB", None, bat=(out - 0.2) / h),
            slab(a, t, n, u0, u1, z0 + h, z0 + h + 0.5, back, 0.45, front="course")]


def quoins(a, t, n, u, z0, z1, side=1, long=2.4, short=1.4, h=1.6, d=0.35, gap=0.15):
    """Alternating long and short corner stones up the edge at u (the stones reach inwards along
    -side*t), d proud: the dressed corners of Minas Tirith's houses."""
    out = []
    z, i = z0, 0
    while z + h <= z1 + 0.01:
        L = long if i % 2 == 0 else short
        u0, u1 = sorted((u, u - side * L))
        out.append(slab(a, t, n, u0, u1, z, z + h - gap, -0.25, d, front="stoneB"))
        z, i = z + h, i + 1
    return out


def pilaster(a, t, n, u, z0, z1, half=1.0, d=0.6, base=True, cap=True):
    """A flat pilaster centred at u from z0 to z1, with a moulded base and capital."""
    out = [slab(a, t, n, u - half, u + half, z0, z1, -0.25, d, ("stoneB", "stoneB", None, "stoneB"), "stoneA")]
    if base:
        out.append(slab(a, t, n, u - half - 0.35, u + half + 0.35, z0, z0 + 0.9, -0.25, d + 0.3, front="course"))
    if cap:
        out.append(slab(a, t, n, u - half - 0.4, u + half + 0.4, z1, z1 + 0.8, -0.25, d + 0.35, front="course"))
    return out


# ---------------------------------------------------------------------------------------- roofs
def ridge(p, q, r=0.3, cresting=2.8, spike=1.8, tag="trim", knobs=True):
    """A steel ridge roll along a roof's ridge from p to q (3D), cresting spikes every `cresting`
    (0: none) and a gilt knob on each end."""
    from ..shapes import beam, turned
    p, q = V(p), V(q)
    out = [beam(p + Z * r * 0.6, q + Z * r * 0.6, r, tag)]
    L = (q - p).length
    if cresting:
        k = max(1, int(L / cresting))
        for i in range(1, k):
            c = p + (q - p) * (i / k) + Z * r * 1.4
            out.append(beam(c - Z * 0.3, c + Z * spike, 0.22, tag, 0.0))
    if knobs:
        for c in (p, q):
            z = c.z + r
            out.append(turned(c.x, c.y, [(0.2, z), (0.55, z + 0.4), (0.55, z + 0.9), (0.2, z + 1.3), (0.0, z + 2.2)],
                              ["gilt"] * 4, k=6, cap0=("gilt", True), cap1=("gilt", False)))
    return out


def eave(a, t, n, u0, u1, z, out=1.2, h=0.6, brackets=2.8, soffit="stoneB"):
    """A fascia along a roof's edge at z (its top), `out` from the face, with a steel edge and
    stone brackets under it every `brackets` (0: none)."""
    res = [slab(a, t, n, u0, u1, z - h, z, -0.25, out, (soffit, "stoneB", "top", "stoneB"), "course"),
           slab(a, t, n, u0, u1, z - 0.2, z + 0.15, out - 0.3, out + 0.15, ("trim", "trim", "trim", "trim"), "trim", None)]
    if brackets:
        k = max(1, int(round((u1 - u0) / brackets)))
        g = (u1 - u0) / k
        for i in range(k):
            m = u0 + (i + 0.5) * g
            res.append(prism_uz(a, t, n, [(m - 0.3, z - h - 1.2), (m + 0.3, z - h - 1.2), (m + 0.3, z - h), (m - 0.3, z - h)],
                                -0.25, 0.4, ["stoneB", "stoneB", None, "stoneB"], "stoneB", None, bat=-(out - 0.6) / 1.2))
    return res


def raking_coping(a, t, n, u, half, z_eave, z_apex, d0, d1, w=0.9, tag="course", kit=None, acroteria=True):
    """Coping stones up both rakes of a gable (centred at u, `half` wide at z_eave, its apex at
    z_apex) on a face, d0..d1; with the kit, a small pinnacle on the apex and blocks at the eaves."""
    out = []
    for e in (-1, 1):
        poly = [(u, z_apex), (u + e * half, z_eave), (u + e * (half + w), z_eave), (u, z_apex + w * 1.2)]
        out.append(prism_uz(a, t, n, poly, d0, d1, ["stoneB", "stoneB", "top", None], tag, "stoneB"))
    if kit and acroteria:
        c = a + t * u + n * ((d0 + d1) / 2)
        out += kit.pinnacle(c.x, c.y, z_apex + 0.3, z_apex + 1.6, half=0.8, spire=2.6)
        for e in (-1, 1):
            out.append(slab(a, t, n, u + e * (half + 0.2) - 0.75, u + e * (half + 0.2) + 0.75, z_eave - 0.6, z_eave + 1.2,
                            d0, d1 + 0.2, front="stoneB", back="stoneB"))
    return out


def crown_dome(kit, cx, cy, levels, eave=None, lantern=None, finial=None):
    """The citadel's dome dress on a chamfered-square dome given as [(z, half, chamfer)] from the
    eave up: a steel eave band (eave: (z, half, chamfer)), steel ribs up its edges, a lantern
    cupola (lantern: (z0, r, top)) and a steel mast, gilt orb and spike (finial: (orb_z, tip))."""
    out = []
    if eave:
        z, h, ch = eave
        out += band_path(octagon(cx, cy, h, ch), z - 0.5, z + 0.5, -0.5, 0.3, "trim", center=(cx, cy), top="trim")
    out += kit.ribs(cx, cy, levels, r=(0.3, 0.18))
    top = levels[-1][0]
    if lantern:
        z0, r, top = lantern
        out += kit.lantern(cx, cy, z0, r=r, top=top)
    if finial:
        orb_z, tip = finial
        out += kit.finial(cx, cy, top - 0.1, orb_z, tip)
    return out


# ---------------------------------------------------------------------------------------- heraldry
def roundel(kit, a, t, n, u, z, r, d=0.2, k=16, studs=True, ring="trim", back=-0.25):
    """The White Tree on a sable disc of radius r centred at (u, z), in a steel ring (0.18 r wide,
    standing to d + 0.5), seven gilt studs round its upper half; the tree raised in white stone."""
    out = []
    ri, ro = 0.82 * r, r
    disc = [(u + ri * math.cos(2 * math.pi * i / k), z + ri * math.sin(2 * math.pi * i / k)) for i in range(k)]
    out.append(prism_uz(a, t, n, disc, back, d, [None] * k, "enamel", None))
    for i in range(k):
        t0, t1 = 2 * math.pi * i / k, 2 * math.pi * (i + 1) / k
        q = [(u + ri * math.cos(t0), z + ri * math.sin(t0)), (u + ro * math.cos(t0), z + ro * math.sin(t0)),
             (u + ro * math.cos(t1), z + ro * math.sin(t1)), (u + ri * math.cos(t1), z + ri * math.sin(t1))]
        out.append(prism_uz(a, t, n, q, back, d + 0.5, [None, ring, None, ring], ring, None))
    h = 1.25 * r
    out += kit.white_tree(a, t, n, u, z - 0.62 * r, h, d + 0.05, r=max(0.12, 0.028 * h))
    if studs:
        for i in range(7):
            th = math.pi * (0.1 + 0.8 * i / 6)
            su, sz = u + 0.91 * r * math.cos(th), z + 0.91 * r * math.sin(th)
            s = 0.13 * r
            out.append(prism_uz(a, t, n, [(su - s, sz - s), (su + s, sz - s), (su + s, sz + s), (su - s, sz + s)],
                                d + 0.3, d + 0.8, ["gilt"] * 4, "gilt", None))
    return out


def star_frieze(kit, a, t, n, u0, u1, z, h=1.8, d0=-0.25, d1=0.5, pitch=3.0, count=None):
    """A sable band u0..u1, z..z+h standing to d1, with gilt seven-pointed stars along it (`count`
    of them, centred; default one every `pitch`)."""
    out = [slab(a, t, n, u0, u1, z, z + h, d0, d1, front="enamel")]
    k = count or max(1, int((u1 - u0) / pitch))
    step = (u1 - u0) / k
    for i in range(k):
        out += kit.star(a, t, n, u0 + (i + 0.5) * step, z + h / 2, min(0.42 * h, 0.4 * step), d1 - 0.1, d1 + 0.3)
    return out


def banner_mount(kit, a, t, n, u, z_top, width, length, d=1.0, crest=True):
    """kit.banner (the cloth goes to the house-colour model on a body) with two stone consoles
    under its rod's ends and, over the rod, a steel spear crest on a small gilt boss."""
    out = kit.banner(a, t, n, u, z_top, width, length, d)
    h = width / 2 + 1.4
    for e in (-1, 1):
        m = u + e * h
        out.append(prism_uz(a, t, n, [(m - 0.5, z_top - 1.8), (m + 0.5, z_top - 1.8), (m + 0.6, z_top - 0.3), (m - 0.6, z_top - 0.3)],
                            -0.25, d + 0.3, ["stoneB", "stoneB", "top", "stoneB"], "stoneB", None, bat=-0.25))
    if crest:
        c = a + t * u + n * (d * 0.5 + 0.1)
        z = z_top + 0.8
        out.append(slab(a, t, n, u - 0.5, u + 0.5, z - 0.1, z + 0.8, -0.1, d * 0.5 + 0.6, ("gilt",) * 4, "gilt"))
        from ..shapes import beam
        out.append(beam((c.x, c.y, z + 0.7), (c.x, c.y, z + 3.6), 0.2, "trim", 0.0))
        out.append(beam((c.x, c.y, z + 1.5), (c.x, c.y, z + 2.2), 0.45, "trim", 0.15))
    return out


def mast(kit, cx, cy, z0, z1, base=1.3, orb=True):
    """A free-standing flag mast from z0 to z1: a stepped stone socle, a steel mast, a collar,
    and (orb) a gilt orb and a steel spike above z1."""
    from ..shapes import turned
    out = [box(cx - base, cx + base, cy - base, cy + base, z0, z0 + 1.4, "stoneB"),
           box(cx - 0.7 * base, cx + 0.7 * base, cy - 0.7 * base, cy + 0.7 * base, z0 + 1.4, z0 + 2.6, "course"),
           turned(cx, cy, [(0.32, z0 + 2.5), (0.26, z1)], ["trim"], k=6, cap0=("trim", False), cap1=("trim", True))]
    if orb:
        out.append(turned(cx, cy, [(0.2, z1 - 0.1), (0.55, z1 + 0.35), (0.55, z1 + 0.85), (0.2, z1 + 1.3)],
                          ["gilt"] * 3, k=6, cap0=("gilt", True), cap1=("gilt", True)))
        out.append(turned(cx, cy, [(0.2, z1 + 1.2), (0.0, z1 + 3.2)], ["trim"], k=6, cap0=("trim", True), cap1=("trim", False)))
    return out


def pennant(cx, cy, z_top, length, width, direction=(1, 0), thick=0.25, tails=True):
    """A swallow-tailed cloth pennant flying from a mast at (cx, cy) along `direction`, its hoist
    `width` tall from z_top down; closed solids, tag cloth (the house model takes it on a body)."""
    t = V((direction[0], direction[1], 0)).normalized()
    n = V((-t.y, t.x, 0))
    a = V((cx, cy, 0)) - n * (thick / 2)
    zb = z_top - width
    if not tails:
        poly = [(0.3, zb), (length, z_top - width * 0.5 - 0.3), (length, z_top - width * 0.5 + 0.3), (0.3, z_top)]
        return [prism_uz(a, t, n, poly, 0, thick, ["cloth"] * 4, "cloth", "cloth")]
    m, cut = z_top - width / 2, length * 0.72
    upper = [(0.3, m), (cut, m), (length, z_top - width * 0.15), (0.3, z_top)]
    lower = [(0.3, zb), (length, zb + width * 0.15), (cut, m), (0.3, m)]
    return [prism_uz(a, t, n, upper, 0, thick, ["cloth"] * 4, "cloth", "cloth"),
            prism_uz(a, t, n, lower, 0, thick, ["cloth"] * 4, "cloth", "cloth")]


def knob(cx, cy, z0, top, r=0.6):
    """A short finial from z0 to `top` (kit.finial needs 6 units over its orb): a steel collar, a
    gilt orb of radius about r and a steel spike."""
    from ..shapes import turned
    h = top - z0
    zo = z0 + 0.25 * h
    return [turned(cx, cy, [(0.7 * r, z0), (0.7 * r, zo - 0.9 * r), (1.1 * r, zo - 0.7 * r)], ["trim", "trim"], k=6,
                   cap0=("trim", False), cap1=("trim", True)),
            turned(cx, cy, [(0.7 * r, zo - 0.75 * r), (1.5 * r, zo), (1.5 * r, zo + 0.6 * r), (0.6 * r, zo + 1.3 * r)],
                   ["gilt"] * 3, k=8, cap0=("gilt", True), cap1=("gilt", True)),
            turned(cx, cy, [(0.4 * r, zo + 1.2 * r), (0.0, top)], ["trim"], k=6, cap0=("trim", True), cap1=("trim", False))]

