"""The Angmar walls' shared pieces (Blender side): what every wall piece carries, so a hub, a
segment, the gate, the towers and a wall end read as one frozen wall of Carn Dum and join without
a seam (the walls group: wall_segment, wall_hub, wall_gate, wall_end, wall_postern, wall_tower,
wall_trebuchet, fortress_wall_hub).

The family (every piece, at its own scale):
    merlons     the battlement: broad stone teeth along the outer edge of every walk and roof, each
                rising to an off-centre point (left and right in turn: the jagged rhythm of the
                Witch-king's crown), the two top slopes rimed white; one pitch (MERLON_PITCH) on
                every piece, so a run of segments keeps the beat through its joints
    corbel      a stone string course just under the walk, corbelled out on a sloped underside, a
                rime crust along its front edge and icicles hanging under it ("icicles under the
                walk")
    foot_ice    ice crystals growing up the wall's foot in drifts, leaning against the face and
                along it (never out past EA's footprint), a black stone shard among them
    peaks       where a tower or hub calls for a peak: EA's own crown of horns frozen from the
                tips down (freeze: the citadel tines' frozen tips), no new spike; never on a
                segment
    fire        cold braziers (shapes_crown.cold_brazier) on the towers' and hubs' tops: the fire
                out of its own iron claw ("coldflame")
    the gate    a barbed iron portcullis (grille) in each mouth of the gateway under a lintel,
                the Witch-king's sigil inset on the keystone set into its middle (keystone)

Pieces: merlons, merlon_us, corbel, foot_ice, run (a straight run of curtain, both faces), freeze,
keystone, grille, hub (the hubs' dress, model space), framed (model space into a mesh's frame).

Placement: a face is (a, t, n): anchor a, t along the face, n out of it, heights absolute (the
anchor's z is dropped); u along t, d along n from a.
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz

MERLON_PITCH = 5.4          # every piece's battlement beat (a segment's 38 holds seven: three a side
                            # of EA's middle rib, the ends a half pitch from the joint)
MERLON = (3.6, 7.0)         # width, height of a merlon (the taller of a pair; the other 0.75 of it)


def _h(*xs):
    v = math.sin(sum(x * (12.9898 + 7.233 * i) for i, x in enumerate(xs))) * 43758.5453
    return v - math.floor(v)


def _face(a, t, n):
    return V((a[0], a[1], 0.0)), V(t).normalized(), V(n).normalized()


def merlons(kit, a, t, n, us, z, w=MERLON[0], h=MERLON[1], d0=-1.6, d1=0.4, tag="stoneA", phase=0):
    """Merlons at each u of `us` on the top edge (z) of a face (a, t, n): stone teeth w wide from
    d0 (over the walk) to d1 (just proud of the face), their tops two slopes from low shoulders up
    to a fang-like point 0.28 of the width off centre, left and right in turn, every other one 0.75
    as tall; the slopes rimed.
    phase: which hand the first one leans (0 or 1), so a run keeps the alternation."""
    a, t, n = _face(a, t, n)
    out = []
    for i, u in enumerate(us):
        k = (i + phase) % 2
        off = (0.28 if k else -0.28) * w
        hh = h * (1.0 if k == 0 else 0.75)
        lo, hi = (0.42, 0.3) if k else (0.3, 0.42)          # the shoulder under the point is the higher one
        poly = [(u - w / 2, z - 0.5), (u + w / 2, z - 0.5), (u + w / 2, z + hh * lo), (u + off, z + hh),
                (u - w / 2, z + hh * hi)]
        out.append(prism_uz(a, t, n, poly, d0, d1, [None, tag, "rime", "rime", tag], tag, tag))
    return out


def merlon_us(u0, u1, pitch=MERLON_PITCH, skip=()):
    """Merlon centres from u0 to u1, a half pitch in from each end (so neighbours keep the beat),
    leaving out any within the (lo, hi) spans of `skip`."""
    k = max(1, int(round((u1 - u0) / pitch)))
    p = (u1 - u0) / k
    return [u0 + p * (i + 0.5) for i in range(k) if not any(lo <= u0 + p * (i + 0.5) <= hi for lo, hi in skip)]


def corbel(kit, a, t, n, u0, u1, z, out=1.4, h=2.4, icicles=True, length=6.0, seed=0.0, ends=True):
    """A string course along a face (a, t, n) from u0 to u1, its top at z: corbelled `out` from the
    face on a sloped underside (h tall), a rime crust along its front's lower edge and icicles
    under it (about `length` long, one every 2.2). ends: its end caps visible (one flag for both,
    or (start, end): a run of chords round a curve hides the caps at its joints)."""
    a, t, n = _face(a, t, n)
    P = lambda u, d, zz: a + t * u + n * d + Z * zz            # noqa: E731
    sec = [(-0.6, z - h), (0.3, z - h), (out, z - h * 0.45), (out, z), (-0.6, z)]
    rings = [[P(u0, d, zz) for d, zz in sec], [P(u1, d, zz) for d, zz in sec]]
    e0, e1 = ends if isinstance(ends, tuple) else (ends, ends)
    res = [loft(rings, [[None, "stoneB", "stoneB", "stoneB", None]], cap0=("stoneB", e0), cap1=("stoneB", e1))]
    if icicles and u1 - u0 > 2.0:
        cnt = max(2, int((u1 - u0) / 2.2))
        res += kit.icicles(a, t, n, u0 + 0.4, u1 - 0.4, z - h * 0.45, length, cnt, d=out, crust=1.0, w=1.2,
                           seed=seed)
    return res


def foot_ice(kit, a, t, n, u, w=5.0, h=11.0, reach=1.8, floor=0.0, seed=0.0, k=5, rock=True):
    """A drift of ice crystals growing up a wall's foot at u on the face (a, t, n): k shards spread
    over w along the face, the tallest h in the middle, leaning along the face and a touch into it
    (nothing passes `reach` out of the face: EA's footprint), one black stone shard among them.
    floor: EA's ground (no buried point below it; kept 0.04 above, EA's exact floats)."""
    a, t, n = _face(a, t, n)
    floor += 0.04
    out = []
    for i in range(k):
        f = (i - (k - 1) / 2) / ((k - 1) / 2)
        L = h * (1.0 - 0.5 * abs(f)) * (0.85 + 0.3 * _h(seed, i))
        r = min(max(0.55, L * 0.085), reach * 0.55)
        base = a + t * (u + f * w / 2) + n * (reach - r) + Z * floor
        d = (Z + t * (0.42 * f + 0.12 * (_h(seed + 1, i) - 0.5)) - n * 0.05).normalized()
        tag = "rock" if rock and i == (k // 2 + 1) else "ice"
        out += kit.shard(base, d, L, r, k=4 + i % 2, seed=seed + i, bury=1.0, floor=floor, tag=tag)
    return out


# EA's curtain (KBWALL01, the segment; the wall end's DWARF is the same profile 8.5 lower, measured
# 2026-10-01): faces at x +8.29 / -8.39 to the top (z 53.1), ribs |y - rib| < 3 proud to |x| 10.2,
# the footprint |x| 10.34 (the ribs)
WALL_FACE = {1: 8.29, -1: 8.39}
WALL_REACH = 10.3
WALL_TOP = 53.1


def run(kit, y0, y1, top=WALL_TOP, ribs=(0.0,), ground=-0.06, bays=(), ends=True):
    """The frozen wall on both faces of a straight run from y0 to y1 (the wall along y, faces at
    +-x): Carn Dum merlons on the top edges (none over EA's ribs), a corbel with icicles just under
    the walk between the ribs, ice drifts up the foot at each u of `bays`."""
    out = []
    holes = [(r - 3.3, r + 3.3) for r in ribs]
    for s in (1, -1):
        a, t, n = V((s * WALL_FACE[s], 0, 0)), V((0, 1, 0)), V((s, 0, 0))
        out += merlons(kit, a, t, n, merlon_us(y0, y1, skip=holes), top)
        cuts = [y0] + [x for h in sorted(holes) for x in h] + [y1]
        for u0, u1 in zip(cuts[::2], cuts[1::2]):
            if u1 - u0 > 2.0:
                out += corbel(kit, a, t, n, u0, u1, top - 1.9, out=1.35, seed=u0 * s, ends=ends)
        for i, u in enumerate(bays):
            out += foot_ice(kit, a, t, n, u, w=6.0, h=12.0, reach=WALL_REACH - WALL_FACE[s] - 0.05, floor=ground,
                            seed=3.0 * i + s)
    return out

def freeze(kit, path, radii, seed=0.0, crystals=3, rime=2):
    """EA's own horn frozen from its tip down, the citadel tines' "frozen tips" on a horn that is
    already there: an ice casing along `path` (the horn's centres from the frost line up to its
    point, measured) `radii` round, six-sided with uneven facets, its lower edge ragged, white rime
    on the last `rime` stretches, a point 1.2 past the horn's own; crystals growing up and out of
    the casing's lower half. The horn stays whole inside it."""
    pts = [V(p) for p in path]
    out, rings = [], []
    for i, (p, r) in enumerate(zip(pts, radii)):
        d = kit.unit((pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]))
        s0 = kit.side_of(d)
        s1 = d.cross(s0).normalized()
        ring = []
        for j in range(6):
            a = 2 * math.pi * j / 6 + seed
            rr = r * (0.8 + 0.4 * _h(seed, i, j))
            q = p + (s0 * math.cos(a) + s1 * math.sin(a)) * rr
            if i == 0:
                q = q - Z * (1.6 * r * _h(seed + 7, j) / max(radii))      # the frost line: ragged
            ring.append(q)
        rings.append(ring)
    tip = pts[-1] + kit.unit(pts[-1] - pts[-2]) * 1.2
    rings.append([tip] * 6)
    n = len(rings) - 1
    out.append(loft(rings, ["rime" if i >= n - rime else "ice" for i in range(n)], cap0=("ice", False),
                    cap1=("rime", False)))
    for k in range(crystals):
        f = 0.1 + 0.55 * k / max(crystals - 1, 1)
        i = min(int(f * (len(pts) - 1)), len(pts) - 2)
        p = pts[i].lerp(pts[i + 1], f * (len(pts) - 1) - i)
        r = radii[i] + (radii[i + 1] - radii[i]) * (f * (len(pts) - 1) - i)
        d = kit.unit(pts[i + 1] - pts[i])
        a = 2 * math.pi * (k * 0.382 + 0.1 * _h(seed, k)) + seed
        o = kit.side_of(d) * math.cos(a) + d.cross(kit.side_of(d)).normalized() * math.sin(a)
        out += kit.shard(p + o * r * 0.7, d + o * 0.32, r * (2.0 + 0.8 * _h(seed + 3, k)), max(0.35, r * 0.32), k=4,
                         seed=seed + k, bury=r * 0.5)
    return out

def keystone(kit, c, t, half, s=0.5):
    """A pointed keystone set into a lintel's middle, c the middle of its foot (the lintel's
    underside), t along the lintel, its faces 0.4 proud of the lintel's (+-half from c): a wedge
    8.4 wide at the foot, 12 at its shoulders (12 up), its point 17 up, the slopes rimed; on both
    faces, inset, the Witch-king's sigil at scale s: an iron kite plate (pointed below) with a steel
    rim, the faceless helm in black iron with its eye-slit glowing cold, and over it the crown, a
    band and seven jagged steel tines (the middle tallest, the outer ones leaning out)."""
    c, t = V(c), V((t[0], t[1], 0)).normalized()
    n = V((t.y, -t.x, 0))
    a = V((c.x, c.y, 0))
    z0 = c.z
    block = [(-4.2, 0.0), (4.2, 0.0), (6.0, 12.0), (0.0, 17.0), (-6.0, 12.0)]
    out = [prism_uz(a, t, n, [(u, z0 + z) for u, z in block], -half, half, [None, "stoneA", "rime", "rime", "stoneA"],
                    "stoneA", "stoneA")]
    zs = z0 + 2.6                                            # the sigil's foot on the keystone's face
    pts = lambda poly: [(u * s, zs + z * s) for u, z in poly]          # noqa: E731
    plate = [(0.0, 0.5), (5.8, 4.7), (6.5, 11.0), (-6.5, 11.0), (-5.8, 4.7)]
    helm = [(0.0, 2.4), (3.0, 4.4), (3.4, 8.2), (2.2, 9.8), (-2.2, 9.8), (-3.4, 8.2), (-3.0, 4.4)]
    slit = [(-2.6, 6.6), (2.6, 6.6), (2.2, 7.5), (-2.2, 7.5)]
    band = [(-6.6, 10.8), (6.6, 10.8), (6.6, 12.6), (-6.6, 12.6)]
    for sd in (1, -1):                                       # both faces: the sigil inset, just proud of the stone
        nn, tt, f = n * sd, t * sd, half
        mir = lambda poly: [(sd * u, z) for u, z in poly]                # noqa: E731
        P = lambda u, d, z: a + t * (u * s) + nn * (f + d) + Z * (zs + z * s)          # noqa: E731
        out.append(prism_uz(a, tt, nn, pts(mir(plate)), f - 0.3, f + 0.25, ["iron"] * 5, "iron", None))
        for (u0, za), (u1, zb) in zip(plate, plate[1:] + plate[:1]):            # the steel rim
            out.append(kit.beam(P(u0, 0.25, za), P(u1, 0.25, zb), 0.28, "steel"))
        out.append(prism_uz(a, tt, nn, pts(mir(helm)), f + 0.1, f + 0.45, ["soot"] * 7, "soot", None))
        out.append(prism_uz(a, tt, nn, pts(mir(slit)), f + 0.3, f + 0.6, ["ember"] * 4, "ember", None))
        out.append(prism_uz(a, t, nn, pts(band), f - 0.3, f + 0.45, ["steel"] * 4, "steel", None))
        for i in range(7):                                   # the tines: middle tallest, outer ones leaning out
            u = -5.4 + 1.8 * i
            k = abs(i - 3)
            hgt = (7.5, 5.0, 6.0, 4.2)[k]
            lean = (0.0, 0.5, 0.9, 1.5)[k] * (1 if i > 3 else -1)
            w = 0.8 if k else 1.0
            tri = [(u - w, 12.4), (u + w, 12.4), (u + lean, 12.4 + hgt)]
            out.append(prism_uz(a, t, nn, pts(tri), f - 0.3, f + 0.45, ["steel"] * 3, "steel", None))
    return out


def grille(kit, a, t, n, u0, u1, z0, z1, bars=15, rails=(0.45, 0.75), d=0.0, r=0.6, teeth=4.2, ext=2.5):
    """A barbed iron portcullis raised in a gateway (face a, t, n) from u0 to u1: heavy bars from
    its bottom rail (z0 + 1.6) up to a riveted top beam at z1, each bar ending below z0 in a steel
    tooth `teeth` long with a barb hooking up each side; more rails at `rails` of its height, every
    rail rimed along its top. Nothing below z0 - teeth. ext: how far the top beam runs on past the
    bars into what holds it."""
    a, t, n = _face(a, t, n)
    P = lambda u, z: a + t * u + n * d + Z * z              # noqa: E731
    out = [kit.beam(P(u0 - 0.6, z0 + 1.6), P(u1 + 0.6, z0 + 1.6), r + 0.15, "iron"),
           kit.beam(P(u0 - ext, z1), P(u1 + ext, z1), r * 2.1, "iron")]
    for f in rails:
        out.append(kit.beam(P(u0 - 0.6, z0 + (z1 - z0) * f), P(u1 + 0.6, z0 + (z1 - z0) * f), r, "iron"))
    for z, rr in [(z0 + 1.6, r + 0.15)] + [(z0 + (z1 - z0) * f, r) for f in rails]:   # rime on the crossbars
        out.append(kit.beam(P(u0 - 0.3, z + rr * 0.85), P(u1 + 0.3, z + rr * 0.85), rr * 0.55, "rime"))
    for i in range(bars):
        u = u0 + (u1 - u0) * (i + 0.5) / bars
        out.append(kit.beam(P(u, z0 + 0.2), P(u, z1 - r), r, "iron"))
        L = teeth * (0.85 + 0.15 * (1 - abs((i + 0.5) / bars - 0.5) * 2))
        out.append(kit.beam(P(u, z0 + 0.4), P(u, z0 - L), r * 1.05, "steel", 0.0))
        for sd in (-1, 1):                                  # a barb each side, hooking up
            b = P(u + sd * r * 0.6, z0 - L * 0.4)
            out.append(kit.beam(b, b + t * (sd * 1.2) + Z * 1.3, r * 0.45, "steel", 0.0))
    for sd in (1, -1):                                      # rivets on the top beam, both faces
        out += kit.rivets(a + n * d, t, n * sd, [(u0 + (u1 - u0) * (i + 0.5) / bars, z1) for i in range(bars)],
                          r * 2.1, r=0.45)
    return out


# ------------------------------------------------------------------------------------------- the hubs
# EA's wall hub (KBWallHubN's WALL HUB, model space: the mesh hangs on a bone turned 90 degrees about z
# and lifted 48.1; KBHTow's HUBTOWER is the same tower in model space, identity bone; measured
# 2026-10-01): an octagonal shaft, its faces 20.3 (x) and 20.7 (y) from the axis and on the diagonals,
# from the ground to z 53.5; a parapet corbelled out to 21.7 (z 54.5..61.5), chamfered in to 20.5 at
# the flat roof, z 62.4; EA's horns: a pair over the +y side's corners at (+-15, 8) to z 96, a third
# leaning out over -y from (0, -11) to z 95 (its point at y -32), two small hooks at (+-27, 16), z 75.
HUB_APOTHEM, HUB_PARAPET, HUB_ROOF, HUB_UNDER = 20.5, 21.7, 62.4, 53.8
HUB_HORNS = [(15.0, 8.0, 8.5), (-15.0, 8.0, 8.5), (0.0, -20.0, 6.0), (24.0, 14.0, 5.0), (-24.0, 14.0, 5.0)]
HUB_BRAZIER = (0.0, 0.0, HUB_ROOF, 3.4, 11.0)      # c x, y, z, r, h: the cold fire's claw in the roof's middle
HUB_ICE = (45.0, 135.0, 225.0, 315.0)              # foot ice on the diagonal faces (clear of walls run in on the axes)
# EA's three horns stand 120 degrees apart (bearings 30, 150, 270) and curve in over the roof to points
# round the axis: the last stretch of the one at 30 degrees (the others the same turned), centres from
# z 84 to its point at (7.6, 4.4, 96.1) (sections measured 2026-10-01: a blade ~8 across at z 84)
HUB_HORN_TIP = ([(14.6, 8.5, 84.0), (12.6, 7.3, 88.0), (10.4, 6.1, 92.0), (7.6, 4.4, 96.1)], [3.8, 3.0, 2.1, 0.9])


def _octagon():
    """(normal, along) of the hub's eight faces, the first facing +x."""
    out = []
    for i in range(8):
        a = math.radians(45.0 * i)
        n = V((math.cos(a), math.sin(a), 0))
        out.append((n, V((-n.y, n.x, 0))))
    return out


def _clear(p, holes):
    return all((p.x - x) ** 2 + (p.y - y) ** 2 > r * r for x, y, r in holes)


def hub(kit, ground=0.0, holes=HUB_HORNS, faces=range(8), ice=HUB_ICE):
    """The hubs' frozen top, in model space: Carn Dum merlons on the parapet of every face (none
    where EA's horns stand: `holes` [(x, y, r)]), icicles under the parapet's overhang, foot ice on
    the diagonal faces, EA's three horns frozen from their tips down (the hub's peak), and the cold
    brazier in the roof's middle under the horns' points (its fire: the recipes' HUB_FIRE)."""
    out = []
    side = 2 * HUB_PARAPET * math.tan(math.radians(22.5))
    for i, (n, t) in enumerate(_octagon()):
        if i not in faces:
            continue
        a = n * HUB_PARAPET
        us = [u for u in merlon_us(-side / 2, side / 2) if _clear(a + t * u, holes)]
        out += merlons(kit, a, t, n, us, HUB_ROOF - 0.3, d0=-2.2, d1=0.15, phase=i)
        side0 = 2 * HUB_APOTHEM * math.tan(math.radians(22.5))
        out += kit.icicles(n * HUB_APOTHEM, t, n, -side0 / 2 + 0.8, side0 / 2 - 0.8, HUB_UNDER, 6.5, 6, d=1.0,
                           crust=0.9, w=1.3, seed=i * 1.3)
        deg = 45.0 * i
        if any(abs(deg - e) < 1 for e in ice):
            out += foot_ice(kit, n * HUB_APOTHEM, t, n, 0.0, w=10.0, h=17.0, reach=3.0, floor=ground, seed=i * 2.1,
                            k=6)
    path, radii = HUB_HORN_TIP
    for k in range(3):                                  # EA's three horns frozen from the tips down
        c, s = math.cos(math.radians(120.0 * k)), math.sin(math.radians(120.0 * k))
        out += freeze(kit, [(c * x - s * y, s * x + c * y, z) for x, y, z in path], radii, seed=1.0 + k)
    x, y, z, r, h = HUB_BRAZIER
    out += kit.cold_brazier((x, y, z), r=r, h=h, seed=1.5)
    return out


def framed(solids, frame):
    """Model-space solids into a mesh's own frame (R, T: model = R mesh + T); winding holds."""
    R, T = frame
    T = V(T)
    for sol in solids:
        for e in sol.polys:
            e[0] = [V([sum(R[k][i] * (p - T)[k] for k in range(3)) for i in range(3)]) for p in e[0]]
    return solids
