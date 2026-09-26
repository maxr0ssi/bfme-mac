"""The old castle walls' upgrade pieces (oldwall_postern, oldwall_tower, oldwall_trebuchet): EA's
three Gondor placeholders the Dwarven castle walls draw, rebuilt as one long wall piece in the
section of wall.py with the upgrade in the middle. Blender side only.

EA's three models (GBWallPG, GBWallTwr, GBWallTreb) share their wall: GBWALLGATE, a core
x +-21.7 with a ramp at each end from the walkway (z 51.91 at |y| 98.9) to the ground at |y| 140.9,
and GBWALLUPGRD, the castle-wall section (core x +-23.77, overhang from z 45.44, parapets x 23.77..28.1
to 64.67, walkway 53.59) along |y| <= 99.5 whose parapets stop at y -25.2 / 26.6 for a block in
the middle (x +-38.02, its parapet to +-42.36: the section's own 4.33 overhang, 14.25 further out).
The postern adds a label box BOX01 (x +-52.05, y +-23.26, to 37.04), the tower a label cylinder
CYLINDER01 (r 25, to 100). Our target is GBWALLGATE (its bone is the identity: mesh coordinates
are model coordinates); the other visible meshes are `replaces` (owncopy.py), so their volume
bounds the redesign too. P1 (the wall-bounds card, z 52), R1 and R2 (the ramp cards) stay EA's.

    section         wall.run at the upgrade walkway (53.59) from the middle out to |y| 99.5,
                    a corbel under every chevron slab, a statue pilaster and two banners per face
    stairs          wall.stair down EA's ramps, from EA's ramp top 51.91 at |y| 99.5 to 140.86
    bastion         the middle block in the section's profile: body face +-38.02, the rune band,
                    drip band and coping 4.33 out (to 42.35), chevrons on its rim and returns,
                    a stepped pyramid on each outer corner; its top is an open platform at 53.59
"""
from mathutils import Vector as V

from sagekit.blender.geometry import box_rings, loft, prism_uz, sweep

from ..wall_tower.crown import step_pyramid
from .wall import CORE_X, WALK, pilaster, run, stair

UP_WALK = 53.59                   # EA's walkway on GBWALLUPGRD (the segment's is 51.91)
RAMP_TOP = 51.91                  # EA's ramps (GBWALLGATE) meet the section at |y| 98.9
END, RAMP_END = 99.5, 140.86           # EA's ramps end at y -140.867 .. 140.98
RAMP_HALF, STEPS = 19.46, 18      # as the segment's stair (its side walls reach EA's 21.66)
BAST_X = 38.02                    # EA's middle block face; its parapet at 42.36
OVER = 4.33                       # the section's overhang: band 4.03, drip 4.33, coping face 4.23
FOOT = -0.05
SLAB = 8.6                        # chevron slab pitch (kit.chevron_parapet)


def bays(y0, y1):
    """(corbel y centres under the chevron slabs of y0..y1, pitch)."""
    k = max(1, round((y1 - y0) / SLAB))
    p = (y1 - y0) / k
    return [y0 + (i + 0.5) * p for i in range(k)], p


def section(kit, y0, y1, walk=UP_WALK, plinth=(None, None), clear=None, dress=True):
    """wall.run over y0..y1 (y0 < y1): corbels under the slabs (none with |y| in `clear`), and if
    `dress` a statue pilaster under the middle corbel and a banner in the bays either side of it."""
    cs, p = bays(y0, y1)
    corbels = [c for c in cs if not (clear and clear[0] <= abs(c) <= clear[1])]
    mid = cs[len(cs) // 2]
    banners = [(mid + e * 1.5 * p, walk - 13.71, 4.4, 17.0) for e in (-1, 1)] if dress else []
    return run(kit, y0, y1, walk, foot=FOOT, corbels=corbels, banners=banners, plinth=plinth,
               relief=mid if dress else None)


def stairs():
    """A Dwarven stair down each of EA's two ramps."""
    return stair(END, RAMP_END, RAMP_TOP, RAMP_HALF, STEPS) + stair(-END, -RAMP_END, RAMP_TOP, RAMP_HALF, STEPS)


def flanks(kit, hy, walk=UP_WALK):
    """The section from the bastion's returns (|y| hy + 4.23) out to EA's ends, the core under the
    walkway between (the returns cover its faces there), and both stairs."""
    y0 = hy + OVER - 0.1
    out = stairs()
    for sy in (1, -1):
        a, b = sorted((sy * y0, sy * END))
        pa, pb = sorted((sy * hy, sy * END))
        out += section(kit, a, b, walk, plinth=(pa, pb))
        c0, c1 = sorted((sy * hy, sy * y0))
        out.append(prism_uz(V((0, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), [(c0, FOOT), (c1, FOOT), (c1, walk), (c0, walk)],
                            -CORE_X, CORE_X, [None, None, "top", None], "stoneA", "stoneA"))
    return out


def rim_profiles(walk):
    """The section's overhang as (d out of the body face, z) convex pieces with edge tags, bottom
    up: plinth, rune band, bronze drip band, coping (its walkway side at d 0)."""
    w, bz = walk, walk - 7.22
    return [
        ([(0.0, FOOT), (2.3, FOOT), (2.3, 0.8), (0.8, 5.8), (0.0, 6.3)], [None, "stoneB", "stoneA", "top", None]),
        ([(0.0, bz), (4.03, bz), (4.03, w - 0.71), (0.0, w - 0.71)], ["stoneB", "rune", None, None]),
        ([(0.0, w - 0.71), (4.03, w - 0.71), (OVER, w - 0.41), (OVER, w + 0.69), (0.0, w + 0.69)],
         [None, "trim", "trim", "trim", "stoneA"]),
        ([(0.0, w + 0.69), (4.23, w + 0.69), (4.23, w + 4.69), (3.83, w + 5.09), (0.0, w + 5.09)],
         [None, "stoneA", "trim", "top", "stoneA"]),
    ]


def corbels(a, t, n, us, bz):
    """Three-step corbels under the band at u in `us` on the face (a, t, n)."""
    out = []
    for u in us:
        for k, (z0, z1, d, hw) in enumerate(((bz - 5.6, bz - 3.6, 1.5, 1.35), (bz - 3.6, bz - 1.8, 2.8, 1.25),
                                             (bz - 1.8, bz, 3.98, 1.15))):
            out.append(prism_uz(a, t, n, [(u - hw, z0), (u + hw, z0), (u + hw, z1), (u - hw, z1)], -0.5, d,
                                ["stoneB", "stoneB", None if k == 2 else "top", "stoneB"], "stoneB", None))
    return out


def bastion(kit, hy, walk=UP_WALK, hx=BAST_X, banners=True):
    """The middle block on both faces: body x +-hx, y +-hy from the ground to the platform at
    `walk`, the section's overhang round its front and returns (open to the walkway at |x| < 23.77),
    corbels, chevrons on the rim, stepped pyramids on the outer corners, banners on the fronts."""
    w, bz = walk, walk - 7.22
    r0, r1 = box_rings((-hx, hx), (-hy, hy), FOOT, 0), box_rings((-hx, hx), (-hy, hy), w, 0)
    out = [loft([r0, r1], ["stoneA"], cap0=("stoneB", False), cap1=("top", True))]
    dz = w - WALK
    for s in (1, -1):
        path = [(s * CORE_X, -hy), (s * hx, -hy), (s * hx, hy), (s * CORE_X, hy)]
        for prof, tags in rim_profiles(w):
            out += sweep(path, prof, tags)[0]
        front = (V((s * hx, 0, 0)), V((0, s, 0)), V((s, 0, 0)))
        out += kit.chevron_parapet(V((s * hx, -s * hy, 0)), front[1], front[2], 2 * hy, d0=0.2, d1=4.13, dz=dz)
        cs, p = bays(-hy, hy)
        out += corbels(*front, cs, bz)
        if banners:
            for u in (-p, p) if len(cs) % 2 else (-p / 2, p / 2):
                out += kit.banner(*front, u, walk - 13.71, 4.4, 17.0, d=0.05)
        for sy in (1, -1):
            a, t, n = V((s * CORE_X, sy * hy, 0)), V((s, 0, 0)), V((0, sy, 0))
            L = hx - CORE_X
            out += kit.chevron_parapet(a, t, n, L, d0=0.2, d1=4.13, dz=dz)
            out += corbels(a, t, n, [L / 2], bz)
            out += step_pyramid(s * (hx + 2.1), sy * (hy + 2.1), w + 5.09, 0.55)
    return out


def upper_rings(hx, hy, z0, w):
    """(rings, tags) of a closed block x +-hx, y +-hy from z0 in the section's profile, its
    platform at w: face, band underside, rune band, drip band, coping, walkway side down to w."""
    bz = w - 7.22
    prof = [(0.0, z0), (0.0, bz), (4.03, bz), (4.03, w - 0.71), (OVER, w - 0.41), (OVER, w + 0.69), (4.23, w + 0.79),
            (4.23, w + 4.69), (3.83, w + 5.09), (0.0, w + 5.09), (0.0, w)]
    tags = ["stoneA", "stoneB", "rune", "trim", "trim", "trim", "stoneA", "trim", "top", "stoneA"]
    return [box_rings((-hx - d, hx + d), (-hy - d, hy + d), z, 0) for d, z in prof], tags


def pilasters(ys, walk=UP_WALK):
    """Statue pilasters on both faces at y in ys (wall.pilaster under the band)."""
    return [p for s in (1, -1) for yc in ys for p in pilaster(s, yc, walk - 7.22 - 6.0)]
