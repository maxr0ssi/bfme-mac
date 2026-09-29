"""Motifs the Goblin production and economy buildings share (cave, fissure, spider pit, treasure
trove, mine shaft, lumber mill), built on the citadel's kit (assets/goblins/shapes.py,
GoblinShapes: `kit`). Blender side (mathutils). Crude, lashed and trophy-hung: charcoal timber,
leather thongs, gritty silver iron, bleached bone, the player's colour on the cloth.

The API is stable: other recipes import it (`from ..cave import motifs as M`). Add functions and
keyword arguments; never rename or reorder positional ones.

Points are 3D (x, y, z) in the recipe's design coordinates; a foot is where a post meets the
ground or rock (it is sunk `sink` below it). `facing` is a horizontal direction: where a banner's
or a skull's face looks (toward the RTS camera: +X and -Y). Every function returns a list of
closed solids (sagekit.blender.geometry).

  timber
    post            a rough upright log sunk into the ground, its top cut to a point or flat
    prop            a raking timber shore from a foot to the thing it holds up: an iron shoe,
                    a lashing, an iron cap
    lashed_x        two poles crossed and lashed where they meet (a trestle's leg pair)
    gate_frame      two posts and a lintel lashed across, bone fangs hanging from the lintel,
                    a skull on each post's point (a mouth, a shaft, a yard's gate)
    stakes          sharpened stakes along a polyline of feet on uneven ground, leaning out
    ladder          two rough rails and lashed rungs from a foot up to a top (a climb up rock)
  bone
    bone_spar       long bones lashed end to end (a crossbar, a yard, a spar)
  cloth
    pole_banner     a ragged house-colour banner on a bone yard lashed to a tall post, the
                    war-paint mark on it, a skull or horned skull on the post's point
  fire
    torch           a haft wound with thong, an iron basket of coals ("ember") at its head
    torch_bracket   an iron arm out of a post or face holding a torch upright
  trophies
    hide_frame      a crimson hide laced into a frame of two posts and two bars, painted
  plunder
    chest           a timber strongbox bound in riveted iron, its lid domed
    ring_stake      an iron stake driven into the ground with a ring at its head (a chain's anchor)
    windlass        two lashed trestles and a log drum with a crank, rope wound on it
    cart            a timber ore cart on four iron-rimmed wheels, heaped with black ore
  mining
    wheel           a big spoked wheel: an iron rim, timber spokes, an iron hub (a headframe's sheave)
    bucket          an iron-banded timber tub hung on a chain's end
    plank_wall      upright planks side by side on a face, bound by two iron straps (shoring)
    heap            a spoil or ore heap: an irregular low cone of black rock with lumps round it
    watchtower      four lashed posts leaning in, girts, X braces, a plank deck with a parapet of
                    stakes (a winch tower, a gate tower)
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz


def _h(v):
    """The horizontal unit vector of v."""
    v = V((v[0], v[1], 0.0))
    return v.normalized() if v.length > 1e-6 else V((1, 0, 0))


# ------------------------------------------------------------------ timber
def post(kit, foot, height, r, sink=1.0, point=True, lean=(0, 0), tag="timber", k=5):
    """A rough log from `sink` below foot up `height`, leaning by (dx, dy) at its top; its top cut
    to a point (point) or flat."""
    foot = V(foot)
    base = foot - Z * sink
    top = foot + Z * height + V((lean[0], lean[1], 0))
    if point:
        return kit.stake(base, top, r, tag=tag, k=k)
    return kit.pole(base, top, r, tag=tag, k=k)


def prop(kit, foot, top, r, sink=0.8):
    """A raking timber shore from foot to top: an iron shoe at its foot, a thong lashing a third up
    and an iron cap where it meets what it props."""
    foot, top = V(foot), V(top)
    d = kit.unit(top - foot)
    out = kit.pole(foot - d * sink, top, r)
    out.append(kit.tube([foot - d * 0.3, foot + d * 1.4], [r + 0.3, r + 0.22], "iron", k=5, cap0="iron", cap1="iron"))
    out.append(kit.tube([top - d * 1.6, top - d * 0.1], [r + 0.22, r + 0.3], "iron", k=5, cap0="iron", cap1="iron"))
    out += kit.lashing(foot.lerp(top, 0.38), d, r, turns=2, w=0.35)
    return out


def lashed_x(kit, p0, q0, p1, q1, r):
    """Two poles, p0-q0 and p1-q1, crossed and lashed at the point where they pass closest."""
    p0, q0, p1, q1 = V(p0), V(q0), V(p1), V(q1)
    out = kit.pole(p0, q0, r) + kit.pole(p1, q1, r)
    best = min(((p0.lerp(q0, i / 20), p1.lerp(q1, j / 20)) for i in range(21) for j in range(21)),
               key=lambda ab: (ab[0] - ab[1]).length)
    out += kit.lashing(best[0].lerp(best[1], 0.5), q0 - p0, r * 1.25, turns=2, w=0.35)
    return out


def gate_frame(kit, a, t, n, u0, u1, z0, z_top, r=1.1, fangs=5, fang=3.5, skulls=True, d=0.0):
    """A gate of lashed timber on the face (a, t, n): posts at u0 and u1 from z0 (sunk 1) to
    z_top + 2.5 (cut to points, a skull on each), a lintel lashed across at z_top, `fangs` bone
    teeth `fang` long hanging from it (the outer ones longest)."""
    a, t, n = V(a), V(t), V(n)
    out = []
    for u in (u0, u1):
        foot = a + t * u + n * d + Z * z0
        out += kit.stake(foot - Z * 1.0, foot + Z * (z_top - z0 + 3.5), r)
        out += kit.lashing(foot + Z * (z_top - z0), Z, r, turns=2, w=0.4)
        if skulls:
            out += kit.skull(foot + Z * (z_top - z0 + 2.4) + n * 0.2, n, 2.3, detail=1, tusks=True)
    p = a + t * (u0 - 1.4) + n * (d + r * 1.3) + Z * z_top
    q = a + t * (u1 + 1.4) + n * (d + r * 1.3) + Z * z_top
    out += kit.pole(p, q, r * 0.95)
    if fangs:
        inset = (u1 - u0) * 0.08
        out += kit.fangs(a, t, n, u0 + inset, u1 - inset, z_top - r * 0.6, fang, fangs, d + r * 0.7, d + r * 1.9,
                         down=True)
    return out


def stakes(kit, feet, h, r=0.6, lean=(0, 0, 0), pitch=2.4, skulls=(), skull=2.0, seed=1):
    """Sharpened stakes along the polyline `feet` [(x, y, ground z)], about `pitch` apart, each
    about h tall (a little different), leaning by `lean` per unit of height (a horizontal
    vector: outward), every third point bloodied; a goblin skull on the stakes whose index is in
    `skulls`."""
    feet = [V(p) for p in feet]
    pts = []
    for p, q in zip(feet, feet[1:]):
        m = max(1, int(round((q - p).length / pitch)))
        pts += [p.lerp(q, (i + 0.5) / m) for i in range(m)]
    lean = V(lean)
    out = []
    for i, p in enumerate(pts):
        hh = h * (0.84 + 0.3 * (0.5 + 0.5 * math.sin(seed * 5.3 + i * 2.39)))
        top = p + Z * hh + lean * hh
        out += kit.stake(p - Z * 1.0, top, r, tip="gore" if (i + seed) % 3 == 0 else None)
        if i in skulls:
            face = _h(lean) if lean.length > 1e-6 else V((1, 0, 0))
            out += kit.skull(top - Z * 1.1 * skull, face, skull, detail=1, tusks=True)
    return out


def ladder(kit, foot, top, width=3.0, pitch=2.2, r=0.4):
    """A crude ladder from foot to top: two rough rails `width` apart (square to the climb,
    horizontal), sticking out 1.5 past the top, and a rung lashed across every `pitch`."""
    foot, top = V(foot), V(top)
    d = kit.unit(top - foot)
    s = kit.side_of(d) * (width / 2)
    out = []
    for e in (-1, 1):
        out += kit.pole(foot + s * e - d * 0.6, top + s * e + d * 1.5, r)
    n = max(2, int((top - foot).length / pitch))
    for i in range(1, n):
        c = foot.lerp(top, i / n)
        out += kit.pole(c - s * 1.25, c + s * 1.25, r * 0.7)
    return out


# ------------------------------------------------------------------ bone
def bone_spar(kit, p, q, r, pieces=2):
    """`pieces` long bones end to end from p to q, overlapping and lashed at each joint."""
    p, q = V(p), V(q)
    d = q - p
    out = []
    for i in range(pieces):
        a = p + d * max(0.0, i / pieces - 0.06)
        b = p + d * min(1.0, (i + 1) / pieces + 0.06)
        out += kit.bone(a, b, r)
    for i in range(1, pieces):
        out += kit.lashing(p + d * (i / pieces), d, r * 1.2, turns=2, w=0.3)
    return out


# ------------------------------------------------------------------ cloth
def pole_banner(kit, foot, height, facing, width, length, mark="eye", top="skull", r=0.85, sink=1.0,
                side=1.0, skull=2.6):
    """A tall lashed post from foot, `height` high, and a ragged house-colour banner `width` wide
    hung `length` from a bone yard lashed across it near the top, its face toward `facing`, its
    foot torn into three tongues, the white war-paint `mark` on it. top: "skull" (a goblin skull
    driven onto the post's point), "horned" (a horned troll skull) or "spike" (an iron spike).
    side: which way the cloth hangs off the post (+1 / -1 along the yard; 0 centred). The cloth
    ("cloth") leaves for the house-colour model; the rest stays on the body."""
    foot = V(foot)
    n = _h(facing)
    t = V((-n.y, n.x, 0.0))                          # along the face, seen from the front: u to the right
    zt = foot.z + height
    out = kit.stake(foot - Z * sink, V((foot.x, foot.y, zt + 3.0)), r)
    yard_z = zt - 1.2
    c = V((foot.x, foot.y, yard_z)) + n * (r + 0.35)
    shift = side * (width / 2 + 0.6)
    p, q = c + t * (shift - width / 2 - 1.3), c + t * (shift + width / 2 + 1.3)
    out += bone_spar(kit, p, q, 0.3, pieces=1)
    out += kit.lashing(V((foot.x, foot.y, yard_z)), Z, r, turns=2, w=0.35)
    a = c - t * 0.0
    d = 0.55
    h, tail = width / 2, min(length * 0.28, width * 0.6)
    z_top, zb = yard_z - 0.2, yard_z - 0.2 - length
    u = shift
    out.append(prism_uz(a, t, n, [(u - h, zb + tail), (u + h, zb + tail), (u + h, z_top), (u - h, z_top)],
                        d - 0.15, d + 0.15, ["cloth"] * 4, "cloth", "cloth"))
    for x0, x1, tip in ((-h, -h / 3, -h * 0.72), (-h / 3, h / 3, 0.0), (h / 3, h, h * 0.68)):
        drop = tail * (1.0 if tip == 0.0 else 0.75)
        out.append(prism_uz(a, t, n, [(u + x0, zb + tail), (u + x1, zb + tail), (u + tip, zb + tail - drop)],
                            d - 0.15, d + 0.15, ["cloth"] * 3, "cloth", "cloth"))
    if mark:
        size = min(width * 0.75, (length - tail) * 0.8)
        out += kit.marking(a, t, n, u, zb + tail + (length - tail - size) * 0.45, size, d + 0.15, mark, back="paint")
    tip = V((foot.x, foot.y, zt + 2.2))
    if top == "skull":
        out += kit.skull(tip, n, skull, detail=1, tusks=True)
    elif top == "horned":
        out += kit.horned_skull(tip + Z * 0.3, n, skull, horn=1.3, detail=1)
    elif top == "spike":
        out += kit.spike(tip, Z, 5.0, 0.45, k=4, tip="gore")
    return out


# ------------------------------------------------------------------ fire
def torch(kit, base, d, length, r=0.32):
    """A torch from base along d: a timber haft wound with thong, an iron basket of glowing coals
    at its head."""
    base, d = V(base), kit.unit(d)
    head = base + d * length
    out = [kit.tube([base, head - d * 0.4], [r, r * 1.1], "timber", k=4, cap0="timber", cap1=None)]
    out += kit.lashing(base.lerp(head, 0.55), d, r, turns=2, w=0.3)
    out.append(kit.tube([head - d * 0.9, head - d * 0.3, head + d * 0.9, head + d * 1.3],
                        [r * 1.2, r * 2.6, r * 2.8, r * 2.4], ["iron", "iron", "iron"], k=5, cap0="iron", cap1="ember"))
    return out


def torch_bracket(kit, root, out_dir, reach=1.8, length=3.2, r=0.3):
    """An iron arm from `root` (on a post's or a face's surface) `reach` out along out_dir, a
    ring at its end and a torch standing in it."""
    root, o = V(root), _h(out_dir)
    tip = root + o * reach + Z * 0.5
    out = [kit.tube([root - o * 0.6, root + o * reach * 0.5 - Z * 0.2, tip], [0.28, 0.25, 0.22], "iron", k=4,
                    cap0="iron", cap1="iron")]
    out.append(kit.tube([tip - Z * 0.35, tip + Z * 0.35], [r + 0.3, r + 0.3], "iron", k=6, cap0="iron", cap1="iron"))
    out += torch(kit, tip - Z * (length * 0.35), Z, length, r)
    return out


# ------------------------------------------------------------------ trophies
def hide_frame(kit, foot, facing, width, height, z_hide=None, mark="claw", r=0.55):
    """A drying frame on the ground at foot: two posts `height` tall, bars at the top and near the
    foot, a crimson hide laced into it, the war-paint mark on the hide."""
    foot = V(foot)
    n = _h(facing)
    t = V((-n.y, n.x, 0.0))
    out = []
    for e in (-1, 1):
        p = foot + t * (e * width / 2)
        out += kit.stake(p - Z * 1.0, p + Z * (height + 1.2), r)
    for z in (height - 0.4, 1.4 if z_hide is None else z_hide):
        a = foot + t * (-width / 2 - 0.8) + n * (r + 0.1) + Z * z
        b = foot + t * (width / 2 + 0.8) + n * (r + 0.1) + Z * z
        out += kit.pole(a, b, r * 0.8)
    top, low = foot.z + height - 1.0, foot.z + (2.0 if z_hide is None else z_hide + 0.6)
    w = width / 2 - 0.6
    poly = [(-w, top), (w, top), (w * 0.95, (top + low) / 2), (w * 0.8, low), (-w * 0.7, low), (-w * 0.95, (top + low) / 2)]
    a = V((foot.x, foot.y, 0.0))
    out.append(prism_uz(a, t, n, poly, r * 0.4, r * 0.4 + 0.3, ["hide"] * 6, "hide", "hide"))
    for e in (-1, 1):
        for f in (0.2, 0.55, 0.85):
            z = low + (top - low) * f
            p = a + t * (e * w) + n * (r * 0.4 + 0.15) + Z * z
            q = a + t * (e * width / 2) + n * (r * 0.4 + 0.15) + Z * (z + 0.3)
            out.append(kit.tube([p, q], [0.12, 0.12], "rope", k=3, cap0="rope", cap1="rope"))
    if mark:
        size = min(w * 1.5, (top - low) * 0.7)
        out += kit.marking(a, t, n, 0.0, low + (top - low - size) * 0.5, size, r * 0.4 + 0.3, mark)
    return out


# ------------------------------------------------------------------ plunder
def chest(kit, c, facing, w=5.0, d=3.4, h=3.0):
    """A timber strongbox w wide, d deep and h tall standing on c, its front toward `facing`:
    a domed lid, iron straps over it and round its corners, a hasp on the front."""
    c = V(c)
    n = _h(facing)
    t = V((-n.y, n.x, 0.0))

    def P(u, v, z):
        return c + t * u + n * v + Z * z
    body = [[P(-w / 2, -d / 2, z), P(w / 2, -d / 2, z), P(w / 2, d / 2, z), P(-w / 2, d / 2, z)] for z in (-0.3, h)]
    out = [loft(body, ["timber"], cap0=("timber", False), cap1=("timber", True))]
    lid = []
    for i in range(5):                                   # the lid's arc along v, extruded along u
        a = math.pi * i / 4
        lid.append((-math.cos(a) * d / 2 * 1.02, h + math.sin(a) * d * 0.32))
    rings = [[P(u, v, z) for v, z in lid] for u in (-w / 2 * 1.02, w / 2 * 1.02)]
    out.append(loft(rings, ["timber"], cap0=("timber", True), cap1=("timber", True)))
    for u in (-w * 0.32, w * 0.32):                      # straps over the lid and down the front and back
        path = [P(u, v, z) for v, z in [(-d / 2 - 0.1, 0.2)] + [(v * 1.06, z + 0.1) for v, z in lid] + [(d / 2 + 0.1, 0.2)]]
        out.append(kit.tube(path, [0.3] * len(path), "iron", k=4, cap0="iron", cap1="iron", phase=math.pi / 4))
    for e in (-1, 1):                                    # iron corner posts
        for f in (-1, 1):
            p = P(e * w / 2, f * d / 2, 0.0)
            out.append(kit.tube([p - Z * 0.2, p + Z * (h + 0.1)], [0.32, 0.32], "iron", k=4, cap0="iron", cap1="iron",
                                phase=math.pi / 4))
    out.append(kit.tube([P(0, d / 2 + 0.1, h - 0.9), P(0, d / 2 + 0.1, h + 0.3)], [0.45, 0.45], "iron", k=4,
                        cap0="iron", cap1="iron"))
    return out


def ring_stake(kit, foot, r=0.5, height=2.5, ring=1.0):
    """An iron stake driven into the ground at foot, a ring (a closed hoop) at its head."""
    foot = V(foot)
    out = kit.spike(foot + Z * height, -Z, height + 1.5, r, k=4, sink=0.0)
    out += kit.hoop((foot.x, foot.y), foot.z + height + 0.3, ring, h=0.5, th=0.25, inner=0.3, k=6, rivets=False,
                    closed=True)
    return out


def windlass(kit, c, along, span=10.0, h=6.5, r=1.2):
    """A windlass centred on the ground at c: two lashed X trestles `span` apart along `along`,
    a log drum of radius r across them at height h wound with rope, an iron crank at one end."""
    c = V(c)
    a = _h(along)
    s = V((-a.y, a.x, 0.0))
    out = []
    for e in (-1, 1):
        m = c + a * (e * span / 2)
        top = m + Z * h
        out += lashed_x(kit, m + s * 2.6 - Z * 0.8, top - s * 0.6 + Z * 1.2, m - s * 2.6 - Z * 0.8, top + s * 0.6 + Z * 1.2, 0.45)
    p, q = c + a * (-span / 2 - 1.0) + Z * h, c + a * (span / 2 + 1.0) + Z * h
    out.append(kit.tube([p, q], [r, r], "timber", k=6, cap0="timber", cap1="timber"))
    for f in (0.3, 0.4, 0.5, 0.6):
        m = p.lerp(q, f)
        out.append(kit.tube([m - a * 0.35, m + a * 0.35], [r + 0.18, r + 0.18], "rope", k=6, cap0="rope", cap1="rope"))
    for f in (0.12, 0.88):
        out += kit.lashing(p.lerp(q, f), a, r, turns=1, w=0.5)
    end = q + a * 0.3
    arm = end + a * 0.6 + Z * 2.6
    out.append(kit.tube([q - a * 0.2, end + a * 0.6, arm], [0.28, 0.28, 0.26], "iron", k=4, cap0="iron", cap1="iron"))
    out.append(kit.tube([arm, arm + a * 1.8], [0.3, 0.3], "iron", k=4, cap0="iron", cap1="iron"))
    return out


def cart(kit, c, facing, w=4.2, l=6.0, h=2.6, wheel=1.3):
    """A crude timber ore cart standing on c (the ground) along `facing`: a box l long, w wide,
    raised on four iron-rimmed wheels, heaped with black ore."""
    c = V(c)
    n = _h(facing)
    t = V((-n.y, n.x, 0.0))
    z0 = wheel * 0.9

    def P(u, v, z):
        return c + t * u + n * v + Z * z
    out = []

    def ring(z, k):
        return [P(-w / 2 * k, -l / 2 * k, z), P(w / 2 * k, -l / 2 * k, z), P(w / 2 * k, l / 2 * k, z), P(-w / 2 * k, l / 2 * k, z)]
    out.append(loft([ring(z0, 0.92), ring(z0 + h, 1.0)], ["timber"], cap0=("timber", True), cap1=("rock", True)))
    heap = [P(-w * 0.35, -l * 0.35, z0 + h), P(w * 0.35, -l * 0.35, z0 + h), P(w * 0.3, l * 0.35, z0 + h),
            P(-w * 0.3, l * 0.35, z0 + h)]
    out.append(loft([heap, [P(-w * 0.1, -l * 0.08, z0 + h + 1.2), P(w * 0.12, -l * 0.1, z0 + h + 1.1),
                            P(w * 0.1, l * 0.12, z0 + h + 1.0), P(-w * 0.12, l * 0.1, z0 + h + 1.2)]],
                    ["rock"], cap0=("rock", False), cap1=("rock", True)))
    for e in (-1, 1):                                    # iron bands round the box
        for f in (-0.3, 0.3):
            out.append(kit.tube([P(e * (w / 2 + 0.05), f * l, z0 + 0.1), P(e * (w / 2 + 0.1), f * l, z0 + h)],
                                [0.22, 0.22], "iron", k=4, cap0="iron", cap1="iron"))
        for f in (-0.32, 0.32):                          # wheels: short iron-rimmed drums on the sides
            hub = P(e * (w / 2 + 0.3), f * l, wheel)
            out.append(kit.tube([hub - t * e * 0.35, hub + t * e * 0.35], [wheel, wheel], "iron", k=8, cap0="timber",
                                cap1="timber"))
    return out


# ------------------------------------------------------------------ mining
def wheel(kit, c, axle, r, spokes=6, rim=0.45, width=0.9):
    """A spoked wheel of radius r centred on c turning about `axle`: an iron rim of `spokes` * 2
    sides, timber spokes, an iron hub standing out either side."""
    c, ax = V(c), kit.unit(axle)
    u = kit.side_of(ax)
    w = ax.cross(u).normalized()
    k = spokes * 2
    ring = [c + (u * math.cos(2 * math.pi * i / k) + w * math.sin(2 * math.pi * i / k)) * r for i in range(k + 1)]
    out = []
    for a, b in zip(ring, ring[1:]):
        d = (b - a).normalized()
        out.append(kit.tube([a - d * rim * 0.4, b + d * rim * 0.4], [rim, rim], "iron", k=4, cap0="iron", cap1="iron",
                            phase=math.pi / 4, squash=width / (2 * rim)))
    for i in range(spokes):
        a = 2 * math.pi * i / spokes
        e = u * math.cos(a) + w * math.sin(a)
        out.append(kit.tube([c, c + e * (r - rim * 0.5)], [0.32, 0.28], "timber", k=4, cap0="timber", cap1="timber"))
    out.append(kit.tube([c - ax * (width + 0.5), c + ax * (width + 0.5)], [r * 0.14 + 0.3] * 2, "iron", k=6, cap0="iron",
                        cap1="iron"))
    return out


def bucket(kit, top, r=1.8, h=2.6):
    """An iron-banded timber tub hanging with its rim's centre at `top`, a bail over it."""
    top = V(top)
    out = [kit.tube([top - Z * h, top - Z * (h * 0.5), top], [r * 0.85, r * 0.95, r], "timber", k=8, cap0="timber",
                    cap1="rock")]
    for f in (0.2, 0.8):
        z = top - Z * (h * f)
        out.append(kit.tube([z - Z * 0.2, z + Z * 0.2], [r * (0.87 + 0.12 * (1 - f)) + 0.12] * 2, "iron", k=8,
                            cap0="iron", cap1="iron"))
    out.append(kit.tube([top + V((-r, 0, -0.3)), top + V((-r * 0.6, 0, r * 0.8)), top + V((r * 0.6, 0, r * 0.8)),
                         top + V((r, 0, -0.3))], [0.16] * 4, "iron", k=4, cap0="iron", cap1="iron"))
    return out


def plank_wall(kit, a, t, n, u0, u1, z0, z1, d=0.0, w=1.5, th=0.5, straps=True):
    """Upright planks from u0 to u1 on the face (a, t, n), each about w wide, from z0 up to about
    z1 (a little ragged), th thick standing at d; two iron straps across them."""
    a, t, n = V(a), V(t), V(n)
    m = max(1, int(round((u1 - u0) / w)))
    step = (u1 - u0) / m
    out = []
    for i in range(m):
        ua, ub = u0 + step * i + 0.06, u0 + step * (i + 1) - 0.06
        top = z1 + 0.6 * math.sin(i * 2.1 + u0)
        poly = [(ua, z0), (ub, z0), (ub, top - (0.3 if i % 2 else 0.0)), ((ua + ub) / 2, top + 0.35), (ua, top)]
        out.append(prism_uz(a, t, n, poly, d, d + th, ["timber"] * 5, "timber", "timber"))
    if straps:
        for f in (0.25, 0.75):
            z = z0 + (z1 - z0) * f
            out.append(prism_uz(a, t, n, [(u0 - 0.2, z - 0.3), (u1 + 0.2, z - 0.3), (u1 + 0.2, z + 0.3), (u0 - 0.2, z + 0.3)],
                                d + th - 0.05, d + th + 0.2, ["iron"] * 4, "iron", "iron"))
    return out


def heap(kit, c, r, h, lumps=5, seed=1, tag="rock"):
    """A spoil or ore heap on the ground at c: an irregular low cone r across and h high, and
    `lumps` loose chunks round its foot."""
    c = V(c)
    k = 7
    base, mid = [], []
    for i in range(k):
        a = 2 * math.pi * i / k + seed
        f = 0.85 + 0.3 * (0.5 + 0.5 * math.sin(seed * 3.7 + i * 2.3))
        e = V((math.cos(a), math.sin(a), 0))
        base.append(c + e * r * f - Z * 0.4)
        mid.append(c + e * r * f * 0.55 + Z * h * (0.55 + 0.1 * math.sin(i + seed)))
    top = [c + V((0.3 * math.sin(seed), 0.3 * math.cos(seed), h))] * k
    out = [loft([base, mid, top], [tag, tag], cap0=(tag, False), cap1=(tag, False))]
    for j in range(lumps):
        a = seed * 1.9 + j * 2.4
        p = c + V((math.cos(a), math.sin(a), 0)) * r * (1.05 + 0.15 * (j % 2))
        s = 0.7 + 0.35 * (j % 3)
        out.append(loft([[p + V((-s, -s * 0.8, -0.3)), p + V((s * 0.9, -s, -0.3)), p + V((s, s * 0.7, -0.3)), p + V((-s * 0.8, s, -0.3))],
                         [p + V((-s * 0.4, -s * 0.2, s * 1.1)), p + V((s * 0.3, -s * 0.4, s)), p + V((s * 0.4, s * 0.3, s * 0.9)),
                          p + V((-s * 0.3, s * 0.4, s * 1.2))]], [tag], cap0=(tag, False), cap1=(tag, True)))
    return out


def watchtower(kit, c, half, deck_z, girts=(9.0, 16.0), braces=((0, 1), (3, 0)), lean=0.12, r=1.05, parapet=4.0):
    """A tower of four lashed posts on the ground at c (x, y, ground z), `half` from its centre to
    each post's axis, leaning in by `lean`, rising 6 past a plank deck at deck_z; girts between
    the posts at `girts` heights, X braces on the faces `braces` (pairs of corner indices, from
    -x-y counter-clockwise), a parapet of sharpened stakes `parapet` tall round the deck (0: none).
    Returns (solids, the deck's four corners)."""
    c = V(c)
    cx, cy, z0 = c.x, c.y, c.z
    ctr = V((cx, cy, z0))
    corners = [V((cx + ex * half, cy + ey * half, z0)) for ex, ey in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    top = deck_z - z0 + 6.0

    def at(p, z):
        return p + (ctr - p) * lean * (z / top) + Z * z

    out = []
    for p in corners:
        out += kit.pole(p - Z * 0.8, at(p, top), r, k=6)
    for z in girts:
        for a, b in zip(corners, corners[1:] + corners[:1]):
            pa, pb = at(a, z), at(b, z)
            d = (pb - pa).normalized()
            out += kit.pole(pa - d * 1.2, pb + d * 1.2, r * 0.52)
    for i, j in braces:
        a, b = corners[i], corners[j]
        out += lashed_x(kit, at(a, 1.0), at(b, girts[0]), at(b, 1.0), at(a, girts[0]), r * 0.43)
    k = half * (1 - lean * (deck_z - z0) / top) + r + 0.6
    deck = [V((cx - k, cy - k, deck_z)), V((cx + k, cy - k, deck_z)), V((cx + k, cy + k, deck_z)), V((cx - k, cy + k, deck_z))]
    out.append(loft([[p - Z * 0.8 for p in deck], deck], ["timber"], cap0=("timber", True), cap1=("timber", True)))
    if parapet:
        feet = deck + [deck[0]]
        out += stakes(kit, [(p.x, p.y, deck_z + 1.0) for p in feet], parapet, r=0.45, lean=(0, 0, 0), pitch=1.6, seed=4)
    return out, deck
