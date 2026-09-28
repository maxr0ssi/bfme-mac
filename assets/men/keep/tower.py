"""A Gondor round tower's crown and dress (Blender side), shared by the keep (GBBtlTwrs) and the
sentry tower (GBBtlTwrM): the citadel's crown (fortress/crown.py) fitted to EA's round towers.

EA's battle towers have one plan at two sizes: an 18-sided shaft whose vertices stand at 0, 24,
36, 60, ... degrees (all at radius R), so every 60 degrees a flat pilaster (24..36, proud to P)
and between two pilasters two broad faces meeting at a fold (0, 60, 120, ...). A frieze band
proud to about P rings the shaft top and the dome springs from it. A `Spec` holds one tower's
numbers (a SimpleNamespace in the recipe: R the shaft radius at its vertices; out the gallery's
front out of R, bounded by the footprint where a fold faces it; corbel (z0, z1, z2) the two steps
under the frieze; band (z0, z1) the frieze the enamel band covers; parapet top, merlon (width,
gap, height); bartizan (r, centre radius, corbel foot, shaft height, spire); dome [(z, r)] EA's
rings at the folds; lantern (z0, r, top); finial (orb z, tip)). Every piece works in the target
mesh's coordinates about the tower axis (0, 0).

    gallery     corbels under EA's frieze, a black enamel band on it (silver stars: paint.StarBand),
                a parapet and square merlons with capstones on every broad face
    bartizans   corbelled turrets engaged on the six pilasters: slit windows, steel-banded cornice,
                slate spirelet and steel spike
    dome        steel ribs up the dome's folds (and pilasters), a lantern cupola, gilt orb, spike
    hoods       window dress: a sill, colonnettes and a pointed hood with a gilt knob
    course      a string course round the broad faces
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import loft, prism_uz, sweep

VERTS = [a + b for a in range(0, 360, 60) for b in (0, 24, 36)]      # EA's shaft vertex angles


def polar(r, deg, z=0.0):
    a = math.radians(deg)
    return V((r * math.cos(a), r * math.sin(a), z))


def ring_r(r, deg):
    """The radius of EA's 18-gon (vertices at r, VERTS) at angle deg: on the chord."""
    deg %= 360
    k = next(i for i in range(len(VERTS)) if VERTS[i] <= deg < (VERTS[i + 1] if i + 1 < len(VERTS) else 360))
    a0, a1 = VERTS[k], (VERTS[k + 1] if k + 1 < len(VERTS) else 360)
    half, mid = (a1 - a0) / 2, (a0 + a1) / 2
    return r * math.cos(math.radians(half)) / math.cos(math.radians(deg - mid))


def chords(R):
    """[(a, t, n, L, mid angle, pilaster?)] of the shaft's 18 edges: anchor at the edge's start
    (ground level), along t, out along n."""
    out = []
    for i, a0 in enumerate(VERTS):
        a1 = VERTS[(i + 1) % len(VERTS)] + (360 if i + 1 == len(VERTS) else 0)
        p, q = polar(R, a0), polar(R, a1)
        t = (q - p).normalized()
        mid = (a0 + a1) / 2
        out.append((p, t, V((math.cos(math.radians(mid)), math.sin(math.radians(mid)), 0)), (q - p).length,
                    mid % 360, (a1 - a0) < 20))
    return out


def face(R, deg):
    """(a, t, n) of the broad face whose chord holds angle deg, anchored at the point of the chord
    at deg (u = 0 there, d = 0 on the face)."""
    for p, t, n, L, mid, pil in chords(R):
        a0 = math.degrees(math.atan2(p.y, p.x)) % 360
        if (deg - a0) % 360 < (24 if not pil else 12) + 1e-6:
            r = ring_r(R, deg)
            return polar(r, deg), t, n
    raise ValueError(deg)


def fold(R, deg):
    """(a, t, n) of the plane tangent to the shaft at the fold `deg` (0, 60, ...): the two faces
    meeting there fall away behind it by R (1 - cos 24) over 2R sin 12 either side."""
    n = V((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0))
    return polar(R, deg), V((-n.y, n.x, 0)), n


def pilaster(P, deg):
    """(a, t, n) of the pilaster centred on deg (30, 90, ...), P its outer radius: anchored at
    the middle of its flat outer face."""
    n = V((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0))
    return n * (P * math.cos(math.radians(6))), V((-n.y, n.x, 0)), n


def shield(kit, a, t, n, u, z, half, height, d=0.0):
    """The kit's White Tree shield (MenShapes.shield) with the tree's strokes closed behind: on a
    narrow shield its limbs reach past the black field, and an open back there shows the sky."""
    from sagekit.blender.geometry import prism_uz as P
    shape = [(-half, height), (half, height), (half, height * 0.4), (0, 0), (-half, height * 0.4)]
    out = [P(a, t, n, [(u + x, z + y) for x, y in shape], d - 0.1, d + 0.8, ["trim"] * 5, "trim", None),
           P(a, t, n, [(u + x * 0.84, z + height * 0.1 + y * 0.84) for x, y in shape], d + 0.7, d + 0.95,
             ["enamel"] * 5, "enamel", None)]
    return out + kit.white_tree(a, t, n, u, z + height * 0.2, height * 0.66, d + 1.0, back="relief")


# ---------------------------------------------------------------------- the crown
def gallery(kit, s):
    """Corbels under the frieze, the enamel band on it, a parapet and merlons on its top."""
    R, out = s.R, s.out
    path = [(p.x, p.y) for p in (polar(R, a) for a in VERTS)]
    path.append(path[0])
    z0, z1 = s.band
    solids = []
    # the black band on EA's frieze (its front 0.3..0.4 proud of the frieze): stars painted on it
    band = [(s.frieze_d, z0 - 0.15), (out, z0 - 0.15), (out, z1), (s.frieze_d, z1)]
    solids += sweep(path, band, ["stoneB", "enamel", "top", None], center=(0, 0))[0]
    # a moulded lip under the band, over the corbels
    lo = getattr(s, "lip", 0.75)                     # the lip's depth under the band
    lip = [(-0.3, z0 - lo), (out + 0.1, z0 - lo), (out + 0.1, z0 - 0.15), (-0.3, z0 - 0.15)]
    solids += sweep(path, lip, ["stoneB", "course", "top", None], center=(0, 0))[0]
    zp = s.parapet
    parapet = [(s.par_d, z1 - 0.1), (out - 0.1, z1 - 0.1), (out - 0.1, zp), (s.par_d, zp)]
    solids += sweep(path, parapet, [None, "stoneA", "top", "stoneA"], center=(0, 0))[0]
    zc0, zc1, zc2 = s.corbel
    for a, t, n, L, mid, pil in chords(R):
        if pil:
            continue
        for u in s.corbel_u:
            solids += kit.corbel(a, t, n, L / 2 + u, zc0, w=s.corbel_w, z1=zc1, z2=zc2, d1=s.corbel_d[0], d2=s.corbel_d[1])
        solids += kit.merlons(a, t, n, 0.1, L - 0.1, zp, s.par_d, out - 0.1, w=s.merlon[0], gap=s.merlon[1],
                              h=s.merlon[2], cap=0.4, lip=0.15)
    return solids


def bartizans(kit, s):
    """A turret engaged on each pilaster, corbelled out from its foot; it swallows EA's pilaster
    capital and the foot of the dome rib above it."""
    r, rc, z0, h, spire = s.bartizan
    out = []
    for k in range(6):
        ang = 30 + 60 * k
        c = polar(rc, ang)
        out += kit.bartizan(c.x, c.y, z0, r=r, h=h, spire=spire, facing=math.radians(ang))
    return out


def dome_r(s, z):
    """EA's dome radius at the folds at height z (between its rings)."""
    for (za, ra), (zb, rb) in zip(s.dome, s.dome[1:]):
        if za <= z <= zb:
            return ra + (rb - ra) * (z - za) / (zb - za)
    raise ValueError(z)


def ribs(s, angles, proud=0.16, r=(0.3, 0.17), z_top=None, z_from=None):
    """Steel ribs up the dome along EA's rings s.dome [(z, r at the folds)], at `angles`, from
    z_from (the dome's foot) to z_top (its point)."""
    from ..shapes import rail
    out = []
    z0 = s.dome[0][0] if z_from is None else z_from
    z1 = s.dome[-1][0] if z_top is None else z_top
    prof = [(z0, dome_r(s, z0))] + [(z, rr) for z, rr in s.dome if z0 < z < z1] + [(z1, dome_r(s, z1))]
    for ang in angles:
        pts = [polar(ring_r(rr, ang) + proud, ang, z) for z, rr in prof]
        out.append(rail(pts, r[0], "trim", r[1]))
    return out


def dome(kit, s, rib_angles, z_from=None):
    z0, r, top = s.lantern
    orb, tip = s.finial
    return ribs(s, rib_angles, z_top=z0 + 0.4, z_from=z_from) + kit.lantern(0, 0, z0, r=r, top=top) + kit.finial(0, 0, top - 0.1, orb, tip)


# ---------------------------------------------------------------------- dress
def course(R, z, h=0.8, d=0.55, pil_d=None, skip=()):
    """A string course round the broad faces, z..z+h, `d` proud of their chords; with pil_d a
    collar round the pilasters too (pil_d proud of their chords), else they break it."""
    out = []
    for a, t, n, L, mid, pil in chords(R):
        if (pil and pil_d is None) or any(abs((mid - k + 180) % 360 - 180) < 13 for k in skip):
            continue
        e = 0.4 if pil else 0.13                     # wrapping the pilaster's radial sides; closing the fold's notch
        out.append(prism_uz(a, t, n, [(-e, z), (L + e, z), (L + e, z + h), (-e, z + h)], -0.3, pil_d if pil else d,
                            ["stoneB", "stoneB", "top", "stoneB"], "course", None))
    return out


def pilaster_bases(R, z0, z1, d):
    """A plinth block at each pilaster's foot, `d` proud of its chord, with a moulded cap."""
    out = []
    for a, t, n, L, mid, pil in chords(R):
        if not pil:
            continue
        out.append(prism_uz(a, t, n, [(-0.45, z0), (L + 0.45, z0), (L + 0.45, z1), (-0.45, z1)], -0.3, d,
                            [None, "stoneB", "top", "stoneB"], "stoneB", None))
        out.append(prism_uz(a, t, n, [(-0.6, z1), (L + 0.6, z1), (L + 0.45, z1 + 0.7), (-0.45, z1 + 0.7)], -0.3, d + 0.15,
                            ["stoneB", "stoneB", "top", "stoneB"], "course", None))
    return out


def fold_pinnacles(kit, s, half=0.45, h=2.4, spire=2.6):
    """A small pinnacle on the parapet over each fold, between the bartizans."""
    out = []
    for k in range(6):
        c = polar(s.R + s.out - 0.75 - half, 60 * k)           # its cap inside the gallery's front
        out += kit.pinnacle(c.x, c.y, s.parapet, s.parapet + h, half=half, spire=spire)
    return out


def hood(a, t, n, half, z_sill, z_spring, z_crown, d=0.5, col=True, knob=True, back=-0.3):
    """A window's dress on a wall plane (anchor a at the window's axis): a sill under it, slim
    colonnettes either side (col), and a pointed hood clear of the opening (a window `half` wide
    whose arch rises from z_spring at its sides to z_crown), a gilt knob at the apex. back: how
    deep the pieces sink into the wall (deeper on a fold's tangent plane, whose faces recede)."""
    out = []
    w = half + 0.75                                  # the hood's feet, outside the opening
    lo = z_spring                                    # the hood's lower edge at its feet
    slope = (z_crown + 0.5 - lo) / w                 # ...rising to clear the crown
    th = 0.85                                        # its depth up the wall
    for e in (-1, 1):
        poly = [(e * w, lo), (0.0, lo + slope * w), (0.0, lo + slope * w + th), (e * w, lo + th)]
        out.append(prism_uz(a, t, n, poly, back, d, ["stoneB", None, "top", "stoneB"], "course", None))
        # a short drop at each foot
        out.append(prism_uz(a, t, n, [(e * w - 0.3, lo - 0.9), (e * w + 0.3, lo - 0.9), (e * w + 0.3, lo + 0.3),
                                      (e * w - 0.3, lo + 0.3)], back, d - 0.05, ["stoneB"] * 4, "course", None))
        if col:
            u0, u1 = sorted((e * (half + 0.2), e * (half + 0.62)))
            out.append(prism_uz(a, t, n, [(u0, z_sill + 0.6), (u1, z_sill + 0.6), (u1, lo - 0.9), (u0, lo - 0.9)],
                                back, d * 0.7, [None, "stoneA", "top", "stoneA"], "stoneA", None))
    out.append(prism_uz(a, t, n, [(-w - 0.25, z_sill), (w + 0.25, z_sill), (w + 0.25, z_sill + 0.6), (-w - 0.25, z_sill + 0.6)],
                        back, d + 0.15, ["stoneB", "stoneB", "top", "stoneB"], "course", None))
    if knob:
        za = lo + slope * w + th
        c = a + n * (d * 0.55)
        out.append(loft([[c + t * x + n * y + V((0, 0, za - 0.1)) for x, y in ((-.32, -.32), (.32, -.32), (.32, .32), (-.32, .32))],
                         [c + V((0, 0, za + 1.3))] * 4], ["gilt"], cap0=("gilt", False), cap1=("gilt", False)))
    return out
