"""The Elven castle walls' shared profile (wall_segment, wall_end, wall_hub, wall_gate; the fortress
wall hub reuses the hub). Blender side only (mathutils); the numbers are plain constants.

EA's Elven wall set shares one section (measured on EBWallN, EBWallNE and EBWallRmprtN): a wall
face (the segment's at |x| 3.06, the hub's round 20-gon at r 22.5..22.59), piers to |x| 4.9 (the
footprint) up to 38.81, pointed hoods over the lancet windows and a V cornice between the piers
(42.0 at the face, 46.22 at 1.39 out, back to the face at 49.1: the TOP_EDGE), then a low ridge to
51.2 (the segment) or a sloped rim to a walk at 51.45 round the dome (the hub). The gate's towers
meet it with their flared caps (47.4..52.37).

Our crown sits on that top edge, at the same heights on every piece, so the line runs on through
segments, ends, hubs and the gate bridge:

    core        a stone block (or ring) from 48.9, buried in EA's cornice, burying EA's ridge
    band        filigree: silver knots on sea-green enamel between two gilt beads, 49.3..50.9,
                0.3 proud of the face line (beads 0.48)
    coping      a silver-moulded coping 51.2..53.0, its nose 0.45 out of the face line
    merlons     lancet merlons 53.0..59.0 on both faces, 2.0 wide, fronts 0.1 out of the face line,
                backs 1.1 in; each run divides its length by about PITCH (4.0), half a gap at each
                end, so neighbours continue the rhythm

The face line may lie at most 0.35 in from EA's top edge: the hub's footprint (y +-22.83) leaves
its crown 0.24 past EA's rim, so every piece takes the same small nose (NOSE, beads 0.48).

Windows: EA's lancet windows (recess 2.1 deep, jambs to 30.81, pointed top at 37.1, 9.8 wide at the
face) get a silver arch frame with sea-green enamel reveals and a slight leaf tip (ogee 0.25), and a
leaf banner in the player's colour hung in the recess in front of the lattice.
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import loft, sweep

# ---- EA's section (measured) ----
FACE_X = 3.06                     # the segment's wall face |x|
RECESS_X = 0.96                   # the lancet windows' back (the lattice)
PIER_X = 4.9                      # piers, and the footprint's |x|
TOP_EDGE = 49.1                   # EA's cornice meets the face again here
WINDOW = (4.9, 30.81, 37.1)       # half width at the face, spring, apex
SEG_WINDOWS = (-9.73, 9.73)       # window centres along a segment (y)

# ---- our crown (heights shared by every piece) ----
CORE_Z = 48.9
BAND = (49.3, 50.9)
BAND_D = 0.3
COPING = (51.2, 53.0)
NOSE = 0.45
MERLON_Z, MERLON_H, MERLON_W, MERLON_GAP = 53.0, 6.0, 2.0, 2.0
MERLON_D = (-1.1, 0.1)
PITCH = MERLON_W + MERLON_GAP

# ---- windows ----
ARCH_W, ARCH_D, ARCH_OGEE = 0.9, 0.8, 0.25
BANNER = (29.6, 5.0, 20.0, 1.5)   # in the recess: z_top, width, length, d out of the lattice
                                  # (forward in the recess, where the light reaches it)


def coping_profile(d_in, inner="stoneB"):
    """(d, z) profile of the coping out of a face line (d = 0) and its edge tags: a chamfered
    underside, the moulded nose, a chamfer to the top, the top back to d_in, the inner side."""
    z0, z1 = COPING
    prof = [(d_in, z0), (-0.05, z0), (NOSE, z0 + 0.55), (NOSE, z1 - 0.45), (NOSE - 0.35, z1), (d_in, z1)]
    return prof, [None, "trim", "coping", "trim", "top", inner]


def crown(kit, path, center, d_in, inner="stoneB", core_in=None, core_tags=None, caps=True, trim=0.0, parapet=True):
    """The crown along one face line `path` (2D polyline; d measured away from `center`): core,
    filigree band, coping, lancet merlons. d_in: how far in the coping reaches; core_in: how far in
    the core reaches (default d_in); trim: merlons kept this far from each run's ends (room for a
    lantern at a corner); parapet=False leaves the merlons to the caller. Returns [Solid]."""
    out = []
    ci = d_in if core_in is None else core_in
    core = [(ci, CORE_Z), (-0.02, CORE_Z), (-0.02, COPING[0] + 0.1), (ci, COPING[0] + 0.1)]
    out += sweep(path, core, core_tags or [None, "stoneB", None, None], caps, caps, center=center)[0]
    out += kit.filigree_band(path, BAND[0], BAND[1], d=BAND_D, center=center)
    prof, tags = coping_profile(d_in, inner)
    ss, segs = sweep(path, prof, tags, caps, caps, center=center)
    out += ss
    for a, b, t, n in segs if parapet else ():
        out += merlons(kit, a + t * trim, t, n, (b - a).length - 2 * trim)
    return out


def merlons(kit, a, t, n, L):
    """Lancet merlons along one straight run from a (2D) along t, fronts facing n."""
    return kit.lancet_parapet(V((a.x, a.y, 0)), V((t.x, t.y, 0)), V((n.x, n.y, 0)), L, MERLON_Z, h=MERLON_H,
                              w=MERLON_W, gap=L / max(1, round(L / PITCH)) - MERLON_W, d0=MERLON_D[0], d1=MERLON_D[1])


def straight_crown(kit, y0, y1, half=FACE_X, caps=True):
    """The crown of a straight wall along y from y0 to y1, both faces at |x| = half: each face's
    coping reaches the axis, where the two meet back to back (buried)."""
    out = []
    for s in (1, -1):
        path = [(s * half, y0), (s * half, y1)]
        out += crown(kit, path, (0, (y0 + y1) / 2), -half, inner=None, caps=caps,
                     core_tags=[None, "stoneB", None, None])
    return out


# ------------------------------------------------------------------ windows
def face_frame(s):
    """(a, t, n) of the segment's s face (t x n = -z; u along t is s * y)."""
    return V((s * FACE_X, 0, 0)), V((0, s, 0)), V((s, 0, 0))


def window_arch(kit, a, t, n, u, finial=True, d0=0.0, d1=ARCH_D):
    """The silver arch frame round one of EA's lancet windows centred at u on the face (a, t, n)."""
    half, spring, apex = WINDOW
    return kit.arch(a, t, n, u, half, 0.0, spring, apex, w=ARCH_W, d0=d0, d1=d1, ogee=ARCH_OGEE, finial=finial)


def window_banner(kit, a, t, n, u):
    """A leaf banner hung free in a window recess, a the recess back's anchor."""
    z_top, width, length, d = BANNER
    return kit.leaf_banner(a, t, n, u, z_top, width, length, d=d, free=True)


def segment_windows(kit, ys=SEG_WINDOWS):
    """Arch frames and banners for the straight wall's windows at ys, both faces."""
    out = []
    for s in (1, -1):
        a, t, n = face_frame(s)
        back = V((s * RECESS_X, 0, 0))
        for y in ys:
            out += window_arch(kit, a, t, n, s * y)
            out += window_banner(kit, back, t, n, s * y)
    return out


def ring(r, k=20, phase=0.0):
    """A regular k-gon of corner radius r, counter-clockwise, closed (first point repeated)."""
    pts = [(r * math.cos(phase + 2 * math.pi * i / k), r * math.sin(phase + 2 * math.pi * i / k)) for i in range(k)]
    return pts + pts[:1]


def lantern_post(kit, cx, cy, z, h=5.2, r=0.85):
    """A crystal lantern on a small moulded foot standing on z (the wall's starlight motif)."""
    from assets.elves.shapes import turned
    foot = turned(cx, cy, [(1.15 * r, z - 0.2), (1.15 * r, z + 0.35), (0.8 * r, z + 0.7), (0.6 * r, z + 1.1)],
                  ["coping", "trim", "trim"], 8, cap0=("stoneB", False), cap1=("top", True))
    return [foot] + kit.crystal_lantern(cx, cy, z + 1.0, h, r)


def box(x0, x1, y0, y1, z0, z1, tags, bottom=("stoneB", False), top=("top", True)):
    from sagekit.blender.geometry import box_rings
    return loft([box_rings((x0, x1), (y0, y1), z0, 0), box_rings((x0, x1), (y0, y1), z1, 0)], [tags],
                cap0=bottom, cap1=top)
