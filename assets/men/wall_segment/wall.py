"""The Gondor walls' shared profile (Blender side, mathutils only): the crown, the string course
and the battered foot every wall piece carries - wall_segment, wall_end, wall_postern, the gate's
curtain and the wall stubs of the tower and the upgradeable plot. Owned by the walls group
(assets/men/ROLLOUT.md); functions are added, never renamed or re-signed.

EA's Gondor wall section (GBWallN, measured; symmetric about the wall's axis, d = distance from
it): the wall face at d 4.98 from the ground to 42.0; piers at the segment's ends (the last 2.09
of each end, so two segments make one pier 4.18 wide) standing out to d 7.45 (the footprint) up
to 34.88, weathered back to 6.72 at 38.46 and 5.98 at 42.04; a cornice with EA's painted corbel
arcade, 5.86..5.98 out, from 42.04 to the paved walk at TOP 49.5 (no parapet).

Our crown is the citadel's machicolated gallery carried along the walls, at the same heights on
every piece so the line runs on through segments, ends, gate and stubs:

    corbels      two-step corbels on EA's cornice from 43.0, every CORBEL_PITCH
    slab         a machicolation slab 46.6..49.55 out to d 7.15, its front a black enamel band
                 (StarBand paints silver stars on it, the citadel's gallery front)
    breastwork   49.4..51.6, front at 7.05, a coping course over it (51.6..52.2, 7.2 out)
    merlons      square merlons with capstones, 52.2..55.35, in Gondor's even rhythm: PITCH
                 divides each run evenly with half a gap at each end, so neighbours continue it
    pinnacles    over the pilasters, a square pedestal and a steel-tipped spirelet (to 59.1)

and down the face:

    pilaster     1.1 proud in the middle of a bay, from the battered foot to the slab, a steel-
                 framed shield with the White Tree on it (d <= 7.3: inside EA's piers)
    slits        arrow slits in stone surrounds with a lintel and a sill
    string course  a moulded band at 24 (EA's own course line on the piers)
    battered foot  a talus 1.5 proud at the ground back to the face at 6.0, a course over it

Nothing passes EA's piers (d 7.45); every run is laid on the wall's axis anchor `a`, along the
unit vector `t` (u), with the face's outward normal `n` (d): the segment runs along y
(a = origin, t = +y, n = +-x), the gate's curtain along x.
"""
from mathutils import Vector as V

from sagekit.blender.geometry import prism_uz, sweep

# ---- EA's section (measured on GBWallN, the same on GBWallNE) ----
FACE = 4.98
PIER = 7.45
PIER_W = 2.09                      # the half pier at each segment end (u 16.91..19)
CORNICE = 5.86                     # the cornice's face, 42.04..49.5
TOP = 49.5

# ---- our crown (heights shared by every piece) ----
CORBEL_Z, CORBEL_PITCH = 43.0, 2.4
SLAB = (46.6, 49.55, 7.15)         # underside, top, front
BREAST = (49.4, 51.6, 5.0, 7.05)   # z0, z1, inner d, front d
COPE = (51.6, 52.2, 4.85, 7.2)
MERLON = dict(z=52.2, h=2.6, cap=0.55, w=2.3, d=(5.25, 6.95), lip=0.2)
PITCH = 4.2                        # merlon + gap
STAR_BAND = (46.8, 49.4)           # StarBand's zrange (the slab's front)
# ---- down the face ----
COURSE_Z = 24.0
FOOT = (6.0, 1.5)                  # talus height, proud at the ground
PILASTER = (1.3, 1.1)              # half width, proud of the face
SHIELD = (29.6, 2.0, 6.6)          # point z, half width, height
SLIT = (27.6, 35.4, 0.42)          # sill, head, half width of the opening


def _pt(a, t, n, u, d):
    p = a + t * u + n * d
    return V((p.x, p.y, 0.0))


def run_sweep(a, t, n, u0, u1, profile, tags, caps=True):
    """Sweep a (d, z) profile along a straight run u0..u1 (d from the wall's axis along n)."""
    path = [_pt(a, t, n, u0, 0.0).to_2d(), _pt(a, t, n, u1, 0.0).to_2d()]
    c = _pt(a, t, n, (u0 + u1) / 2, -1.0).to_2d()
    return sweep(path, profile, tags, caps, caps, center=c)[0]


def merlon_centres(u0, u1, pitch=PITCH):
    """Merlon centres dividing u0..u1 evenly with half a gap at each end."""
    L = u1 - u0
    k = max(1, round(L / pitch))
    return [u0 + (i + 0.5) * L / k for i in range(k)]


def merlon_row(a, t, n, u0, u1, skip=(), pitch=PITCH, m=MERLON):
    """Square merlons with overhanging capstones on u0..u1; skip: [(ua, ub)] left clear."""
    out = []
    w, z0, h, cap, lip = m["w"], m["z"], m["h"], m["cap"], m["lip"]
    d0, d1 = m["d"]
    for c in merlon_centres(u0, u1, pitch):
        s, e = c - w / 2, c + w / 2
        if any(s < ub and e > ua for ua, ub in skip):
            continue
        out.append(prism_uz(a, t, n, [(s, z0), (e, z0), (e, z0 + h), (s, z0 + h)], d0, d1,
                            [None, "stoneA", None, "stoneA"], "stoneA", "stoneA"))
        zc = z0 + h
        out.append(prism_uz(a, t, n, [(s - lip, zc), (e + lip, zc), (e + lip, zc + cap), (s - lip, zc + cap)],
                            d0 - lip, d1 + lip, ["stoneB", "stoneB", "top", "stoneB"], "course", "stoneB"))
    return out


def crown(kit, a, t, n, u0, u1, skip=(), caps=True, merlons=True):
    """The machicolated crown on one face of a run u0..u1: corbels, the enamel slab, breastwork,
    coping course and merlons (skip: [(ua, ub)] spans without merlons, e.g. a pinnacle's)."""
    zs0, zs1, ds = SLAB
    out = run_sweep(a, t, n, u0, u1, [(CORNICE - 0.2, zs0), (ds, zs0), (ds, zs1), (CORNICE - 0.2, zs1)],
                    ["stoneB", "enamel", "top", None], caps)
    z0, z1, di, df = BREAST
    out += run_sweep(a, t, n, u0, u1, [(di, z0), (df, z0), (df, z1), (di, z1)], [None, "stoneA", None, "stoneA"], caps)
    c0, c1, ci, cf = COPE
    out += run_sweep(a, t, n, u0, u1, [(ci, c0), (cf, c0), (cf, c1 - 0.15), (cf - 0.2, c1), (ci + 0.1, c1), (ci, c1 - 0.2)],
                     ["stoneB", "course", "course", "top", "course", "stoneB"], caps)
    k = max(1, int((u1 - u0 - 5.2) // CORBEL_PITCH) + 1)      # 2.6 clear of the run's ends (EA's piers)
    first = (u0 + u1) / 2 - (k - 1) * CORBEL_PITCH / 2
    ac = a + n * CORNICE
    for j in range(k):
        out += kit.corbel(ac, t, n, first + j * CORBEL_PITCH, CORBEL_Z, w=0.5, z1=CORBEL_Z + 1.8, z2=zs0,
                          d1=0.6, d2=ds - CORNICE - 0.02)
    if merlons:
        out += merlon_row(a, t, n, u0, u1, skip)
    return out


def string_course(a, t, n, u0, u1, z=COURSE_Z, caps=True):
    """A moulded band across the face at z (a bevelled top sheds the rain)."""
    return run_sweep(a, t, n, u0, u1, [(FACE - 0.3, z - 0.55), (FACE + 0.55, z - 0.55), (FACE + 0.7, z),
                                       (FACE + 0.45, z + 0.45), (FACE - 0.3, z + 0.7)],
                     ["stoneB", "course", "course", "top", None], caps)


def pier_cap(a, t, n, u0, u1, z=34.4):
    """A moulded cap across the front of EA's pier (u0..u1: the pier and 0.2 past its side), where
    its face weathers back: flush with the pier's front (the footprint), a lip under it."""
    return [prism_uz(a, t, n, [(u0, z), (u1, z), (u1, z + 1.1), (u0, z + 1.1)], PIER - 1.4, PIER,
                     ["stoneB", "course", "top", "course"], "course", None),
            prism_uz(a, t, n, [(u0 + 0.2, z - 0.7), (u1 - 0.2, z - 0.7), (u1 - 0.2, z), (u0 + 0.2, z)], PIER - 1.4,
                     PIER - 0.25, ["stoneB", "stoneB", None, "stoneB"], "course", None)]


def foot(a, t, n, u0, u1, caps=True):
    """The battered foot: a talus FOOT[1] proud at the ground back to the face at FOOT[0], and a
    course over it."""
    h, p = FOOT
    out = run_sweep(a, t, n, u0, u1, [(FACE - 0.3, 0.0), (FACE + p, 0.0), (FACE + p, 0.4), (FACE + 0.12, h),
                                      (FACE - 0.3, h)], ["stoneB", "stoneB", "stoneB", "top", None], caps)
    out += run_sweep(a, t, n, u0, u1, [(FACE - 0.3, h - 0.1), (FACE + 0.55, h - 0.1), (FACE + 0.55, h + 0.5),
                                       (FACE + 0.3, h + 0.75), (FACE - 0.3, h + 0.75)],
                     ["stoneB", "course", "top", "top", None], caps)
    return out


def pilaster(kit, a, t, n, u, shield=True, pinnacle=True, z_top=None):
    """A pilaster in the middle of a bay from the foot to the slab (z_top), the White Tree shield
    on it, and a pinnacle over it on the breastwork. Returns (solids, (ua, ub) its merlon gap)."""
    hw, pr = PILASTER
    zt = SLAB[0] if z_top is None else z_top
    out = [prism_uz(a, t, n, [(u - hw, 0.0), (u + hw, 0.0), (u + hw, zt), (u - hw, zt)], FACE - 0.3, FACE + pr,
                    ["stoneB", "stoneB", None, "stoneB"], "stoneB", None),     # EA's wall ashlar (stoneB) on its face
           prism_uz(a, t, n, [(u - hw - 0.35, 0.0), (u + hw + 0.35, 0.0), (u + hw + 0.35, FOOT[0] + 1.6),
                              (u - hw - 0.35, FOOT[0] + 1.6)], FACE - 0.3, FACE + FOOT[1] + 0.05,
                    ["stoneB", "stoneB", "top", "stoneB"], "stoneB", None)]
    for z in (COURSE_Z - 0.6,):                                   # the string course wraps it
        out.append(prism_uz(a, t, n, [(u - hw - 0.25, z), (u + hw + 0.25, z), (u + hw + 0.25, z + 1.2),
                                      (u - hw - 0.25, z + 1.2)], FACE, FACE + pr + 0.3,
                            ["stoneB", "course", "top", "course"], "course", None))
    if shield:
        zp, half, height = SHIELD
        out += kit.shield(a + n * (FACE + pr), t, n, u, zp, half, height, d=0.0)
    gap = (u - 1.6, u + 1.6)
    if pinnacle:
        c = a + t * u + n * 6.0                                    # its moulded cap to d 7.35
        out += kit.pinnacle(c.x, c.y, COPE[1] - 0.1, 55.4, half=1.05, spire=3.0, orb=False)
        out.append(kit_tip(c.x, c.y, 55.4 + 0.7 + 3.0 - 0.9, 59.2))
    return out, gap


def kit_tip(cx, cy, z0, z1):
    """A slender steel spike on a spirelet's point."""
    from assets.men.shapes import turned
    return turned(cx, cy, [(0.28, z0), (0.36, z0 + 0.5), (0.14, z0 + 0.9), (0.0, z1)], ["trim"] * 3, k=6,
                  cap0=("trim", False), cap1=("trim", False))


def slit(a, t, n, u, z0=None, z1=None):
    """An arrow slit in a stone surround: the slit (atlas 'slit'), jambs, a lintel and a sill."""
    s0, s1, w = SLIT
    z0 = s0 if z0 is None else z0
    z1 = s1 if z1 is None else z1
    f = FACE
    out = [prism_uz(a, t, n, [(u - w, z0), (u + w, z0), (u + w, z1), (u - w, z1)], f - 0.3, f + 0.12,
                    [None] * 4, "slit", None)]
    for e in (-1, 1):
        ua, ub = sorted((u + e * w, u + e * (w + 0.55)))
        out.append(prism_uz(a, t, n, [(ua, z0), (ub, z0), (ub, z1), (ua, z1)], f - 0.3, f + 0.55,
                            ["stoneB"] * 4, "stoneA", None))
    out.append(prism_uz(a, t, n, [(u - w - 0.85, z1), (u + w + 0.85, z1), (u + w + 0.6, z1 + 1.0), (u - w - 0.6, z1 + 1.0)],
                        f - 0.3, f + 0.75, ["stoneB", "stoneB", "top", "stoneB"], "stoneB", None))
    out.append(prism_uz(a, t, n, [(u - w - 0.8, z0 - 0.55), (u + w + 0.8, z0 - 0.55), (u + w + 0.8, z0), (u - w - 0.8, z0)],
                        f - 0.3, f + 0.8, ["stoneB", "stoneB", "top", "stoneB"], "course", None))
    return out


def face(kit, a, t, n, u0, u1, bays, pilasters=None, slits=None, caps=True, crown_run=None, foot_run=None,
         with_foot=True):
    """Everything on one face of a straight wall: the crown over u0..u1 (crown_run overrides), and
    for each bay (ua, ub) between EA's piers the foot, the string course, a pilaster (pilasters:
    their u; default each bay's middle) and slits (slits: their u; default a third of the way in
    from the pilaster to each pier); with_foot=False leaves the foot off (a face running on below
    the ground, as the wall end's down its cliff)."""
    out, skip = [], []
    for ua, ub in bays:
        mid = (ua + ub) / 2
        for u in ([mid] if pilasters is None else [p for p in pilasters if ua < p < ub]):
            ss, gap = pilaster(kit, a, t, n, u)
            out += ss
            skip.append(gap)
        for u in ([mid - (ub - ua) / 4, mid + (ub - ua) / 4] if slits is None else [s for s in slits if ua < s < ub]):
            out += slit(a, t, n, u)
        fr = foot_run or (ua, ub)
        if with_foot:
            out += foot(a, t, n, max(ua, fr[0]), min(ub, fr[1]), caps)
        out += string_course(a, t, n, ua, ub, caps=caps)
    cr = crown_run or (u0, u1)
    out += crown(kit, a, t, n, cr[0], cr[1], skip=skip, caps=caps)
    return out


def straight(kit, u0, u1, bays, a=None, t=None, sides=(1, -1), **kw):
    """Both faces of a straight wall on the axis a + t u (default: the segment's, along y)."""
    a = V((0.0, 0.0, 0.0)) if a is None else V(a)
    t = V((0.0, 1.0, 0.0)) if t is None else V(t)
    nx = V((t.y, -t.x, 0.0))
    out = []
    for s in sides:
        out += face(kit, a, t, nx * s, u0, u1, bays, **kw)
    return out


