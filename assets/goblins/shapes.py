"""The Goblin shape vocabulary (Blender side): Goblin-town's crude warcraft. Where the Dwarves are
stepped and the Men square-cut, the Goblins are jagged, lashed and trophy-hung: crimson horn and
hide, gritty silver iron, black rock and charcoal timber, and bleached white bone as the contrast.
Every piece returns a list of closed solids (sagekit.blender.geometry.Solid) in the building's
design coordinates, tagged with GoblinAtlas regions only (assets/goblins/atlas.py).

Two ways to say where a piece goes, as in the other kits:
    points      base / centre points and directions in 3D (horns, bones, skulls, chains)
    a, t, n     a wall face: anchor a, along t, out along n; u along the face, z up, d out
                (sagekit.blender.geometry.prism_uz): plates, panels, palisades, markings, banners

Sizes are for the RTS camera: a detail must stand 1.5-4 units proud to read at the game's zoom.

Core (this module)
    tube(points, radii, tags)          a closed tube along a polyline (the building block)
    arc(p0, d0, d1, length)            points along a smooth bend from direction d0 to d1
    spike(base, d, length, r)          a straight jagged iron spike
    horn(base, d0, d1, length, r)      a curved horn: crimson hide at the root, bleached bone tip
    horn_crown(c, z, r, count, ...)    a ring of horns sweeping out and up round a spire or post
    tusk(base, d0, d1, length, r)      a bleached tusk with an iron collar at its root
Bone and gore (shapes_bone.py, BoneKit)
    bone, skull, horned_skull, skull_on_spike, skull_pile, spine, ribcage, skeleton, impaled,
    totem, carcass, drip
Crude work (shapes_crude.py, CrudeKit)
    rivets, plate, hoop, pole, lashing, stake, palisade, marking, hide_panel, fangs, chain, cage,
    brazier, banner
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft

from .shapes_bone import BoneKit
from .shapes_crude import CrudeKit



def unit(v):
    v = V(v)
    return v.normalized() if v.length > 1e-9 else V((0, 0, 1))


def side_of(d):
    """A unit vector square to d, horizontal where it can be."""
    u = V(d).cross(Z)
    if u.length < 1e-3:
        u = V(d).cross(V((1, 0, 0)))
    return u.normalized()


def rings_along(points, radii, k=6, phase=0.0, squash=1.0):
    """Rings of k points round a polyline, their frames carried along it without twist (so the
    quads between rings stay nearly flat). A radius of 0 closes the tube to a point there."""
    pts = [V(p) for p in points]
    n = len(pts)
    u = t_prev = None
    rings = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        t = unit(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)])
        if u is None:
            u = side_of(t)
        else:                               # parallel transport: turn u as the tangent turns
            u = t_prev.rotation_difference(t) @ u
            u = u - t * u.dot(t)
            if u.length < 1e-6:
                u = side_of(t)
        t_prev = t
        u.normalize()
        w = t.cross(u).normalized()
        if r <= 1e-4:
            rings.append([p.copy() for _ in range(k)])
            continue
        rings.append([p + (u * math.cos(phase + 2 * math.pi * j / k) + w * math.sin(phase + 2 * math.pi * j / k) * squash) * r
                      for j in range(k)])
    return rings


def tube(points, radii, tags, k=6, cap0="bone", cap1="bone", phase=0.0, squash=1.0):
    """A closed tube along points with a radius per point; tags: one per interval (a tag, or a
    list of k, None = buried side); cap0/cap1: the end caps' tags (None: buried)."""
    tags = [tags] * (len(points) - 1) if isinstance(tags, str) else list(tags)
    return loft(rings_along(points, radii, k, phase, squash), tags,
                cap0=(cap0 or "stoneA", cap0 is not None), cap1=(cap1 or "stoneA", cap1 is not None))


def arc(p0, d0, d1, length, n=5):
    """n+1 points from p0, leaving along d0 and arriving along d1, about `length` long (a cubic
    Bezier whose handles follow the two directions)."""
    p0, d0, d1 = V(p0), unit(d0), unit(d1)
    chord = unit(d0 * 0.55 + d1 * 0.45)
    p3 = p0 + chord * length * 0.93
    p1, p2 = p0 + d0 * length * 0.4, p3 - d1 * length * 0.4
    out = []
    for i in range(n + 1):
        s = i / n
        out.append(p0 * (1 - s) ** 3 + p1 * 3 * s * (1 - s) ** 2 + p2 * 3 * s * s * (1 - s) + p3 * s ** 3)
    return out


def taper(r, n, power=0.9, tip=0.0):
    """n+1 radii from r at the root to `tip` at the end."""
    return [tip + (r - tip) * (1 - i / n) ** power for i in range(n + 1)]


class GoblinShapes(BoneKit, CrudeKit):
    """The Goblin kit. Stable API: add pieces, keep these signatures (13 more buildings use them)."""

    Z = Z                                   # the helpers, for the mixins and the recipes
    V = V
    tube = staticmethod(tube)
    arc = staticmethod(arc)
    rings_along = staticmethod(rings_along)
    unit = staticmethod(unit)
    side_of = staticmethod(side_of)
    taper = staticmethod(taper)

    # ------------------------------------------------------------------ spikes, horns, tusks
    @staticmethod
    def spike(base, d, length, r, tag="iron", k=4, kink=0.0, sink=0.5, tip=None):
        """A straight spike of k sides from base along d (sunk `sink` of r into what it stands on),
        tapering to a point; kink bends its last third sideways by that fraction of length (a
        crude, hammered look); tip: another tag for its last third ("gore": a bloodied point)."""
        d = unit(d)
        b = V(base) - d * r * sink
        pts = [b, b + d * length * 0.62, b + d * length]
        if kink:
            pts[2] = pts[2] + side_of(d) * length * kink
        return [tube(pts, [r, r * 0.45, 0.0], [tag, tip or tag], k=k, cap0=tag, cap1=None, phase=math.pi / k)]

    @staticmethod
    def horn(base, d0, d1, length, r, n=5, k=6, root="hide", tip="bone", tip_from=0.5, sink=0.6, squash=1.0):
        """A curved horn from base, leaving along d0 and ending along d1: `root` tag (crimson
        hide) up to tip_from of its length, then `tip` (bleached bone) to the point."""
        d0 = unit(d0)
        pts = arc(V(base) - d0 * r * sink, d0, d1, length + r * sink, n)
        tags = [root if i / n < tip_from else tip for i in range(n)]
        return [tube(pts, taper(r, n, 0.85), tags, k=k, cap0=root, cap1=None, squash=squash)]

    def horn_crown(self, c, z, r, count, length, thick, rise=0.9, lean=0.35, phase=0.0, k=6, n=5,
                   root="hide", tip="bone", tip_from=0.45, skip=()):
        """`count` horns round the vertical axis through c, rooted at radius r and height z:
        each leaves outward with `lean` of upward slope and curls to `rise` (0 flat, 1 straight
        up). skip: indices left out (a banner or a window there)."""
        out = []
        for i in range(count):
            if i in skip:
                continue
            a = phase + 2 * math.pi * i / count
            radial = V((math.cos(a), math.sin(a), 0))
            base = V((c[0], c[1], z)) + radial * r
            out += self.horn(base, radial + Z * lean, radial * (1 - rise) + Z * rise * 1.6, length, thick,
                             n=n, k=k, root=root, tip=tip, tip_from=tip_from)
        return out

    @staticmethod
    def tusk(base, d0, d1, length, r, n=6, k=6, collar=True, sink=0.8):
        """A bleached tusk curving from d0 to d1, with a riveted iron collar round its root."""
        d0 = unit(d0)
        pts = arc(V(base) - d0 * r * sink, d0, d1, length + r * sink, n)
        out = [tube(pts, taper(r, n, 0.75, 0.0), "bone", k=k, cap0="bone", cap1=None)]
        if collar:
            c = pts[0].lerp(pts[1], 0.55)
            dd = unit(pts[1] - pts[0])
            out.append(tube([c - dd * r * 0.45, c + dd * r * 0.45], [r * 1.28, r * 1.22], "iron", k=k,
                            cap0="iron", cap1="iron"))
        return out
