"""The Isengard walls' shared pieces (Blender side): the profile every wall piece carries, so a
segment, a hub, the gate and a wall end read as one wall and join without a seam.

EA's wall (IBWALLN mesh coordinates, measured 2026-09-29; the wall runs along y, its faces at +-x,
both alike): the face at |x| 4.37 to z 17.5, a step in to 3.85, battered in to 2.22 at z 33.7;
a parapet corbelled out to a lip at |x| 5.49, z 38.7, its bevel to |x| 4.0 at 40.22, a gabled
roof to the ridge at z 46.77, pyramids on it at y 0, +-12.67 to z 51.57; knife fins (x 3.74..8.32
at the foot leaning back to 5.15 at z 25) at y +-1.66 (a whole one) and y 17.34..19 (a half one:
two neighbours make a whole); and at each end a thin fork plate (y 18.04..19.03) with two horns
to z 59.24 (the neighbour's plate completes it).

What every wall piece adds (`run`), per face and bay, all inside |x| 8.32 and never past the
run's ends, so neighbours and stretched segments still meet:

    short fins     at y +-9.5 between EA's: knife-edged, silver front, EA's lean (layered faces)
    buttress blade EA's middle fin carried up to the lip, its point just proud of it
    ember slits    two per bay, pointed, low on the face where the RTS camera sees them
    the lip        a silver edge along the lip and the ridge, iron spikes leaning out of the lip
    needles        lozenge needles out of EA's three pyramids: a tall one in the middle, two short
    fork edges     silver along the horns' outer edges (half a fork per end, as EA's plates)

Other pieces:
    needle(kit, c, z0, z1, L, W)       a lozenge needle: flared foot, silver collar, sharp arrises
    slit(kit, a, t, n, u, z, w, h)     a pointed ember slit sunk in a face
    short_stack(kit, c, axis, L, W, z0, z1)  kit.needle_stack on a short shaft, its collar gap closed
    hub(kit)                           the hubs' blade cluster: a needle stack between two blades
    brazier_point(c, r, h)             where kit.brazier's fire rises (for fire_points)
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft, prism_uz


# EA's wall profile (above)
FACE_X = 4.37
LIP = (5.49, 38.7)
BEVEL = (4.0, 40.22)
RIDGE_Z = 46.77
PYRAMIDS = (-12.67, 0.0, 12.67)
PYRAMID = (4.0, 3.17, 40.22, 51.57)          # half x, half y at the foot, foot z, apex z
FIN_Y = (-9.5, 9.5)                          # our short fins, between EA's (y 0 and the ends)
SLIT_Y = (-14.0, -5.3, 5.3, 14.0)
HORN = [(3.26, 59.24), (8.08, 49.33), (7.17, 49.33), (7.17, 38.94)]    # a horn's outer edge, top down
FORK_Y = (18.04, 19.03)
HALF = 19.0


def slit(kit, a, t, n, u, z, w=0.9, h=7.0, depth=0.9, lean=0.0):
    """A pointed ember slit w wide, h tall, its foot at (u, z) on the face (a, t, n), sunk depth;
    lean: the face leans back this much per unit up (the slit follows it)."""
    sw = w / 2
    poly = [(u - sw, z), (u + sw, z), (u + sw, z + h * 0.8), (u, z + h), (u - sw, z + h * 0.8)]
    if not lean:
        return [prism_uz(V(a), V(t), V(n), poly, -depth, 0.2, ["ember"] * 5, "ember", None)]
    a, t, n = V(a), V(t), V(n)
    rings = [[a + t * uu + n * (d - lean * (zz - z)) + Z * zz for uu, zz in poly] for d in (-depth, 0.2)]
    return [loft(rings, ["ember"], cap0=("ember", False), cap1=("ember", True))]


def needle(kit, c, z0, z1, L, W, axis=90.0, tag="stoneA", collar=0.35, edges=True):
    """A lozenge needle on c from z0 (buried foot) to a point at z1: L along `axis` (degrees), W
    across; a flared foot, a silver collar band at `collar` of the height, silver on the sharp
    arrises (the ends of the long axis) up to the collar."""
    H = z1 - z0
    prof = [(0.0, 1.35), (0.12, 1.0), (collar, 0.82), (collar + 0.01, 0.72), (0.8, 0.3), (1.0, 0.0)]
    rings = [kit.lozenge(c, axis, L * s, W * s, z0 + H * f) for f, s in prof]
    rings[-1] = [V((c[0], c[1], z1))] * 4
    out = [loft(rings, [tag] * (len(rings) - 1), cap0=(tag, False), cap1=(tag, False))]
    zc = z0 + H * collar
    band = [kit.lozenge(c, axis, L * s, W * s, z) for s, z in ((0.55, zc - 0.7), (0.95, zc - 0.5), (0.9, zc + 0.5),
                                                                (0.5, zc + 0.7))]
    out.append(loft(band, ["trim"] * 3, cap0=("trim", False), cap1=("trim", False)))
    if edges:
        for k in (0, 2):
            out.append(kit.beam(rings[1][k], rings[2][k], 0.2, "trim"))
            out.append(kit.beam(rings[3][k], rings[4][k], 0.18, "trim"))
    return out


def knife(kit, a, out, edge, back, w, tag="stoneA", arris=0.22):
    """A knife-edge fin: a triangular section (w wide at its back, `back` behind a, its sharp edge
    out along `out`) whose edge runs through edge = [(d, z)] bottom to top, the last point its
    tip; silver along the edge (arris: the beam's half size, 0 for none)."""
    a, o = V((a[0], a[1], 0)), kit.unit(V((out[0], out[1], 0)))
    s = V((-o.y, o.x, 0))
    rings = [[a - o * back - s * (w / 2) + Z * z, a + o * d + Z * z, a - o * back + s * (w / 2) + Z * z]
             for d, z in edge[:-1]]
    d, z = edge[-1]
    rings.append([a + o * d + Z * z] * 3)
    out_ = [loft(rings, [tag] * (len(rings) - 1), cap0=(tag, False), cap1=(tag, False))]
    if arris:
        pts = [a + o * d + Z * z for d, z in edge]
        for p, q in zip(pts, pts[1:]):
            out_.append(kit.beam(p, q, arris, "trim"))
    return out_


def face_fins(kit, s, ys=FIN_Y, foot=None):
    """Short knife fins on face s (+-1) at ys, EA's lean, silver edges; foot(y): where the face
    ends below the ground (a wall end's cliff face), None: at z 0."""
    out = []
    for y in ys:
        zb = foot(y) if foot else 0.0
        edge = ([(3.9, zb + 0.3)] if zb < -0.5 else []) + [(3.9, 0.0), (1.6, 15.0), (0.6, 19.0)]
        out += knife(kit, (s * 3.8, y), (s, 0), edge, 0.8, 2.4)
    return out


def buttress(kit, s, y=0.0):
    """EA's fin at y carried on up to the lip: a knife from its top (z 24) leaning out past the
    lip (z 38.7) to a point over the parapet's bevel (z 43)."""
    return knife(kit, (s * 3.2, y), (s, 0), [(1.9, 23.0), (2.9, 38.5), (0.9, 43.5)], 1.8, 2.8, arris=0.26)


def slits(kit, s, ys=SLIT_Y, z=6.0):
    a, t, n = V((s * FACE_X, 0, 0)), V((0, 1, 0)), V((s, 0, 0))
    out = []
    for y in ys:
        out += slit(kit, a, t, n, y, z, 1.2, 9.0)
    return out


def lip(kit, s, y0, y1, spikes=8):
    """A silver edge along the lip from y0 to y1 and iron spikes leaning out of its bevel."""
    x, z = LIP
    out = [kit.beam(V((s * (x - 0.15), y0, z + 0.1)), V((s * (x - 0.15), y1, z + 0.1)), 0.28, "trim")]
    if spikes:
        out += kit.spike_row(V((s * 4.9, 0, 0)), V((0, 1, 0)), V((s, 0, 0)), y0 + 0.8, y1 - 0.8, 40.1, 3.6, spikes,
                             lean=0.45, r=0.4)
    return out


def ridge(kit, y0, y1):
    return [kit.beam(V((0, y0, RIDGE_Z + 0.05)), V((0, y1, RIDGE_Z + 0.05)), 0.3, "trim")]


def crest_needles(kit, yc, tall=66.0, short=57.5, stop=None):
    """Needles out of EA's pyramids (centred on yc): the middle one tall, the other two short;
    none beyond y = stop."""
    out = []
    for dy in PYRAMIDS:
        if stop is not None and yc + dy > stop:
            continue
        top = tall if dy == 0 else short
        out += needle(kit, (0.0, yc + dy), 43.0, top, 1.9 if dy == 0 else 1.5, 1.5 if dy == 0 else 1.2, axis=90.0,
                      collar=(52.5 - 43.0) / (top - 43.0), edges=dy == 0)
    return out


def fork_edges(kit, y_end, yc=0.0):
    """Silver along the horns' outer edges of the fork plate at the end y_end of the run centred
    on yc (the plate lies 0.96 inside the end)."""
    y = y_end + (0.5 if y_end < yc else -0.5)
    out = []
    for s in (1, -1):
        pts = [V((s * (px - 0.25), y, pz)) for px, pz in HORN[:2]]
        out.append(kit.beam(pts[0] + Z * -0.3, pts[1], 0.24, "trim"))
    return out


def run(kit, yc, ends=(True, True), tall=66.0, foot=None, stop=None):
    """One segment's worth of the wall (EA's IBWALLN centred on y = yc, 38 long): every face
    motif on both faces, the lip, ridge and needles; `ends`: silver on the fork plates at
    yc -19 / yc +19 (EA's plates are there); foot(y): the face's foot below ground (wall end);
    stop: no spikes, needles or ridge line beyond this y (a wall end's tower stands there)."""
    out = []
    y1 = yc + HALF if stop is None else min(yc + HALF, stop)
    spikes = max(2, int(round(6 * (y1 - yc + HALF) / (2 * HALF))))
    for s in (1, -1):
        out += _moved(face_fins(kit, s, [yc + y for y in FIN_Y], foot), 0)
        out += _moved(buttress(kit, s), yc)
        out += _moved(slits(kit, s), yc)
        out += lip(kit, s, yc - HALF, y1, spikes)
    out += ridge(kit, yc - HALF + 1.0, y1 - 1.0)
    out += crest_needles(kit, yc, tall=tall, stop=stop)
    for e, y in zip(ends, (yc - HALF, yc + HALF)):
        if e:
            out += fork_edges(kit, y, yc)
    return out


def _moved(solids, dy):
    """The solids moved along y by dy (in place)."""
    if dy:
        off = V((0, dy, 0))
        for sol in solids:
            for e in sol.polys:
                e[0] = [p + off for p in e[0]]
    return solids


# EA's wall hub (IBFBALTOW01 mesh coordinates: it hangs on a bone at z 25.47, so model z = mesh z
# + 25.47): a hexagon, corners on the x axis, faces 19.26 from the axis (corners 22.24), from the
# ground (-25.47) to 31.04; bands proud to 19.67 at z -0.15..0.93 and 17.85..18.94; a parapet
# leaning out to 20.21 (z 31.04..37.04 at its front), the roof floor at 34.19; knife fins round
# its buried foot. Segments run into any face (the middle 16.6 of it, to model z 59.24).
HUB_FACE, HUB_CORNER, HUB_RIM, HUB_TOP = 19.26, 22.24, 20.21, 37.04
HUB_BONE_Z = 25.47
HUB_BLADE = (11.2, 7.4, 5.2, 33.4, 56.5, 1.1, 1.2)      # the pair (at +-x): centre r, half length (radial), half width,
                                                        # z0, z1, flare, lean out
HUB_STACK = (5.6, 4.1, 33.4, 47.6)                      # half length, half width, z0, z1 (its crown rises 2.7 W over z1)
HUB_CORNER_NEEDLE = 47.0                                # the six corner needles' tips (the segments' crest needles)


def short_stack(kit, c, axis, L, W, z0, z1, collar=0.6):
    """kit.needle_stack for a short stack (z1 - z0 under ~40): its collar band is placed by the
    height without the crown's 2 units, so on a short shaft the band stands off it and the sky
    sees through the gap; a closed iron sleeve under the band fills it."""
    out = kit.needle_stack(c, axis, L, W, z0, z1, collar=collar)
    zc = z0 + (z1 - z0) * collar
    s = 0.76 + (0.5 - 0.76) * (collar - 0.352) / 0.568 if collar > 0.352 else 1.0 + (0.84 - 1.0) * (collar - 0.05) / 0.3
    ring = kit._grow(kit.lozenge(c, axis, L * s, W * s, 0.0), -0.1)
    out.append(loft([[p + Z * (zc - 0.75) for p in ring], [p + Z * (zc + 0.75) for p in ring]], ["iron"],
                    cap0=("iron", True), cap1=("iron", True)))
    return out


def hub(kit):
    """The hub's blade cluster (mesh coordinates), the citadel's: on the roof a needle stack on the
    axis (spiked ember collar, a blade crown round an ember throat, no fire: hubs repeat) to mesh
    58.6 (model 84) between two matching lozenge blades (at +-x, sharp edges to the corners,
    three layered fins a face, silver edges, ember slits, a collar above the fins, leaning out as
    Orthanc's horns) to mesh 56.5, the three one mass nearly corner to corner; the walls' lozenge
    needles on the parapet's six corners to mesh 47; iron spikes leaning out of the parapet faces;
    silver corner arrises; a pair of ember slits a face."""
    r, L, W, z0, z1, flare, lean = HUB_BLADE
    out = []
    for s in (1, -1):
        out += kit.blade_tower((s * r, 0.0), 0.0, L, W, z0, z1, lean=(s * lean, 0.0), flare=flare, fins=3,
                               spurs=False, slits=(0.3, 0.44), collar=0.64, slit_w=1.1)
    L, W, z0, z1 = HUB_STACK
    out += short_stack(kit, (0.0, 0.0), 90.0, L, W, z0, z1, collar=0.6)
    for i in range(6):
        d = V((math.cos(math.pi / 3 * i), math.sin(math.pi / 3 * i), 0))
        c = d * (HUB_CORNER - 0.05)
        out.append(kit.beam(c + Z * -25.3, c + Z * 31.0, 0.3, "trim"))
        out += needle(kit, d * 20.9, 35.2, HUB_CORNER_NEEDLE, 2.3, 1.7, axis=60.0 * i, collar=0.3)
        a = math.radians(30 + 60 * i)                  # face normals between the corners
        n = V((math.cos(a), math.sin(a), 0))
        t = V((-n.y, n.x, 0))
        out += kit.spike_row(n * (HUB_RIM - 0.4), t, n, -7.0, 7.0, HUB_TOP + 0.3, 3.8, 3, lean=0.45, r=0.42)
        for u in (-2.6, 2.6):
            out += slit(kit, n * HUB_FACE, t, n, u, 3.0, 1.3, 11.0)
    return out


def _framed(solids, f):
    """The solids with every point p replaced by f(p) (f a rotation plus a move: winding holds)."""
    for sol in solids:
        for e in sol.polys:
            e[0] = [f(p) for p in e[0]]
    return solids


# EA's fortress wall hub's stub (IBFWHub, the same mesh coordinates as the hub): the wall's profile
# run along x from the citadel (-42.2) into the hub's -X corner, faces at +-y, 25.47 lower; EA's fins
# at x -42.2, -30.57, -18.94; pyramids at x -40.26, -32.51, -24.76; three small fork plates with
# horns to z 27.53 at x -36.4, -28.6, -20.9
STUB = (-42.2, -18.94)
FWHUB_STUB = dict(x0=-42.2, x1=-21.4, fins=(-36.4, -24.8), butt=-30.57, slit_u=(-39.3, -33.6, -27.6, -22.0),
                  pyramids=((-40.26, 57.5), (-32.51, 64.0), (-24.76, 57.5)), spikes_to=-23.0, dz=-HUB_BONE_Z)


def stub(kit, x0, x1, fins, butt, slit_u, pyramids, spikes_to, dz=0.0, spikes=5):
    """The wall profile on a stub running along x (faces at +-y) from x0 into a tower at x1, built
    in the segment's frame (u along the run = mesh x, z = mesh z - dz) and turned onto the stub:
    short fins at `fins`, a buttress on EA's fin at `butt`, slits at `slit_u`, the silver lip and
    ridge, lip spikes to `spikes_to`, needles [(u, top)] out of EA's pyramids."""
    out = []
    for s in (1, -1):
        out += face_fins(kit, s, fins)
        out += buttress(kit, s, butt)
        out += slits(kit, s, slit_u)
        out += lip(kit, s, x0 + 0.4, x1, 0)
        out += kit.spike_row(V((s * 4.9, 0, 0)), V((0, 1, 0)), V((s, 0, 0)), x0 + 0.8, spikes_to, 40.1, 3.6, spikes,
                             lean=0.45, r=0.4)
    out += ridge(kit, x0 + 0.5, x1 + 0.4)
    for u, top in pyramids:
        out += needle(kit, (0.0, u), 43.0, top, 1.35, 1.2, axis=90.0, collar=(52.5 - 43.0) / (top - 43.0),
                      edges=top > 60)
    return _framed(out, lambda p: V((p.y, -p.x, p.z + dz)))


def bracket_brazier(kit, a, n, reach=3.4, r=1.7):
    """A fire basket on an iron bracket out of a face: a is the point on the face (its height the
    bracket's), n out of it. An arm and a diagonal strut, a square basket pointed below, heaped
    with embers, spikes rising from its rim; its fire point recorded ('brazier')."""
    a, n = V(a), V((n[0], n[1], 0)).normalized()
    c = a + n * reach + Z * 0.9                      # the basket's rim centre
    out = [kit.beam(a - n * 0.5, a + n * (reach + 0.2), 0.36, "iron"),
           kit.beam(a - n * 0.4 - Z * 3.8, a + n * reach * 0.8, 0.3, "iron"),
           kit.tube([c - Z * r * 1.2, c, c + Z * 0.25], [r * 0.12, r * 1.2, r * 1.25], "iron", k=4, cap0="iron",
                    cap1="ember", phase=math.pi / 4)]
    for i in range(4):
        d = V((math.cos(math.pi / 2 * i), math.sin(math.pi / 2 * i), 0))
        p = c + Z * 0.15 + d * r * 1.1
        out.append(kit.beam(p, p + (d * 0.3 + Z).normalized() * r * 1.1, 0.12, "iron", 0.0))
    kit.fire(c + Z * 0.35, "brazier")
    return out


def brazier_point(c, r=1.2, h=3.2):
    """Where kit.brazier(c, r, h) records its fire (the embers' top)."""
    return (round(c[0], 1), round(c[1], 1), round(c[2] + h + 0.1, 1))
