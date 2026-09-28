"""The Elven castle walls' shared profile (wall_segment, wall_end, wall_hub, wall_gate; the fortress
wall hub reuses the hub). Blender side only (mathutils); the numbers are plain constants.

EA's Elven wall set shares one section (measured on EBWallN, EBWallNE and EBWallRmprtN): a wall
face (the segment's at |x| 3.06, the hub's round 20-gon at r 22.5..22.59), piers to |x| 4.9 (the
footprint) up to 38.81, pointed hoods over the lancet windows and a V cornice between the piers
(42.0 at the face, 46.22 at 1.39 out, back to the face at 49.1: the TOP_EDGE), then a low ridge to
51.2 (the segment) or a sloped rim to a walk at 51.45 round the dome (the hub). The gate's towers
meet it with their flared caps (47.4..52.37).

Our crown sits on that top edge, at the same heights on every piece, so the line runs on through
segments, ends, hubs and the gate bridge. It is the citadel's ring crown (elves/fortress) carried
along the walls: EA's wall kept whole below it, a silver coping on top, gold in the details.

    core        a stone block (or ring) from 48.9, buried in EA's cornice, burying EA's ridge
    band        filigree: silver knots on sea-green between two gilt beads, 49.3..50.9, 0.3 proud
                of the face line (beads 0.48): the gold accent along the wall
    coping      a mithril coping 51.2..53.0 like the citadel's ring coping: a chamfered underside,
                a short upright nose and a broad bevel up to the top (it catches the light, so the
                silver reads bright and not as a dark slab), a strip of the top in silver
                (COPING_SILVER in from the face line), the walk behind in stone
    merlons     a light cresting of leaf-tipped merlons 53.0..58.2 on both faces (straight runs
                only: the hub and the gate's tower heads carry lanterns and finials instead), 1.5
                wide at about PITCH 5.2: each run divides its length evenly, half a gap at each end,
                so neighbours continue the rhythm. Stone leaves edged in gold (the kit's
                lancet_parapet, its blades' silver rims gilt, as EA's gilded leaf-gable frames),
                slender and spaced over the silver line: a cresting, not a battlement

The face line may lie at most 0.35 in from EA's top edge: the hub's footprint (y +-22.83) leaves
its crown 0.24 past EA's rim, so every piece takes the same small nose (NOSE, beads 0.48).

Below the crown EA's walls stay as they are: the lancet windows (recess 2.1 deep, jambs to 30.81,
pointed top at 37.1, 9.8 wide at the face) with their lattice glass (its leading painted silver by
the style), the hoods with EA's gold leaf emblems, the ivy. No banners on the walls: they repeat
many times in game (the gate carries the run's two).
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import loft, sweep

# ---- EA's section (measured) ----
FACE_X = 3.06                     # the segment's wall face |x|
RECESS_X = 0.96                   # the lancet windows' back (the lattice)
PIER_X = 4.9                      # piers, and the footprint's |x|
TOP_EDGE = 49.1                   # EA's cornice meets the face again here

# ---- our crown (heights shared by every piece) ----
CORE_Z = 48.9
BAND = (49.3, 50.9)
BAND_D = 0.3
COPING = (51.2, 53.0)
NOSE = 0.45
COPING_SILVER = -1.4              # the coping's top is silver from the nose in to here
BEVEL = (0.95, -0.1)              # the nose's bevel: from this height over COPING[0] at NOSE to d -0.1 at the top
MERLON_Z, MERLON_H, MERLON_W = 53.0, 5.2, 1.5
MERLON_D = (-1.15, -0.25)         # on the coping's flat top, behind the bevel
PITCH = 5.2
ARCH_OGEE = 0.25                  # the leaf tip of the kit's arches (the gate's)


def coping_profile(d_in, inner="stoneB"):
    """(d, z) profile of the coping out of a face line (d = 0) and its edge tags: a chamfered
    underside, the moulded nose, a chamfer to the top, a silver strip of the top (to COPING_SILVER),
    the walk back to d_in in stone, the inner side. All the visible edge is mithril, as the
    citadel's ring coping."""
    z0, z1 = COPING
    prof = [(d_in, z0), (-0.05, z0), (NOSE, z0 + 0.45), (NOSE, z0 + BEVEL[0]), (BEVEL[1], z1)]
    tags = [None, "trim", "trim", "trim", "trim"]
    if d_in < COPING_SILVER - 0.3:
        prof.append((COPING_SILVER, z1))
        tags.append("top")
    prof.append((d_in, z1))
    return prof, tags + [inner]


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
    """Leaf-tipped merlons along one straight run from a (2D) along t, fronts facing n: the kit's
    lancet_parapet (per merlon a shaft, a stalk, a blade and a foot fillet), the blades' rims gilt."""
    out = kit.lancet_parapet(V((a.x, a.y, 0)), V((t.x, t.y, 0)), V((n.x, n.y, 0)), L, MERLON_Z, h=MERLON_H,
                             w=MERLON_W, gap=L / max(1, round(L / PITCH)) - MERLON_W, d0=MERLON_D[0], d1=MERLON_D[1])
    for blade in out[2::4]:
        for e in blade.polys:
            if e[1] == "trim":
                e[1] = "gilt"
    return out


def straight_crown(kit, y0, y1, half=FACE_X, caps=True):
    """The crown of a straight wall along y from y0 to y1, both faces at |x| = half: each face's
    coping reaches the axis, where the two meet back to back (buried)."""
    out = []
    for s in (1, -1):
        path = [(s * half, y0), (s * half, y1)]
        out += crown(kit, path, (0, (y0 + y1) / 2), -half, inner=None, caps=caps,
                     core_tags=[None, "stoneB", None, None])
    return out


def ring(r, k=20, phase=0.0):
    """A regular k-gon of corner radius r, counter-clockwise, closed (first point repeated)."""
    pts = [(r * math.cos(phase + 2 * math.pi * i / k), r * math.sin(phase + 2 * math.pi * i / k)) for i in range(k)]
    return pts + pts[:1]


def lantern_post(kit, cx, cy, z, h=5.2, r=0.85, post=2.6):
    """A crystal lantern on a slender silver post standing on z: the citadel's ring lantern (a
    moulded foot, a post flaring to a cup, the crystal in its gilt cup with a gilt leaf tip)."""
    from assets.elves.shapes import turned
    f = 1.1 * r
    foot = turned(cx, cy, [(1.3 * f, z - 0.2), (1.3 * f, z + 0.3), (0.85 * f, z + 0.65), (0.5 * f, z + 1.1),
                           (0.42 * f, z + post - 0.5), (0.85 * f, z + post)],
                  ["trim"] * 5, 8, cap0=("trim", False), cap1=("trim", True))
    return [foot] + kit.crystal_lantern(cx, cy, z + post - 0.1, h, r)


def box(x0, x1, y0, y1, z0, z1, tags, bottom=("stoneB", False), top=("top", True)):
    from sagekit.blender.geometry import box_rings
    return loft([box_rings((x0, x1), (y0, y1), z0, 0), box_rings((x0, x1), (y0, y1), z1, 0)], [tags],
                cap0=bottom, cap1=top)
