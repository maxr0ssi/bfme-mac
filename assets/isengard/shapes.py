"""The Isengard shape vocabulary (Blender side): Saruman's war-works. Where the Goblins are jagged
and lashed and the Men square-cut, Isengard is faceted and forged: black Orthanc stone cut in hard
planes and sharp arrises (never rough rock), heavy riveted iron plate, furnace stacks with glowing
throats, and the machinery of industry - chains, pulleys, gear wheels, hooks - on the walls. Every
piece returns closed solids (sagekit.blender.geometry.Solid) tagged with IsengardAtlas regions
only (assets/isengard/atlas.py).

Two ways to say where a piece goes, as in the other kits:
    points      base / centre points and directions in 3D (horns, chimneys, chains, gears)
    a, t, n     a wall face: anchor a, along t, out along n; u along the face, z up, d out
                (sagekit.blender.geometry.prism_uz): plates, vents, racks, banners

Sizes are for the RTS camera: a detail stands 1.5-4 units proud to read at the game's zoom.

Core (this module; tube and arc as the Goblin kit's)
    tube(points, radii, tags)          a closed tube along a polyline
    beam(p, q, r)                      a square bar (tapering; r2=0 ends in a point)
    facet(cx, cy, profile, tags, k)    a faceted body of revolution: k hard planes, (r, z) profile
    orthanc_horn(base, d, h, w)        one of Orthanc's horns: a four-sided black blade, flared
                                       at the root, leaning out then up, knife-edged to its point
    orthanc_crown(c, z, half, h)       the four horns on the corners of a square, a faceted
                                       platform between them (the tower's crown)
    chimney(c, r, z0, z1)              a furnace stack: stepped faceted stone foot, riveted iron
                                       barrel with hoops (and a spiked collar), a flared lip
                                       crowned with spikes and a glowing throat
Works (shapes_works.py, WorksKit)
    rivets, plate, hoop, chain, gear, pulley, vent, slag_heap, hook, spike_row, pike_rack,
    hand, banner
Yard (shapes_yard.py, YardKit)
    stump, log, log_stack, trestle, saw_frame, hearth, anvil, bellows, crucible, gantry,
    water_wheel, sluice, scaffold, siege_ladder, shield, shield_rack, pipe, fire_grate
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, loft

from .shapes_works import WorksKit
from .shapes_yard import YardKit


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
    """Rings of k points round a polyline, their frames carried along it without twist."""
    pts = [V(p) for p in points]
    n = len(pts)
    u = t_prev = None
    rings = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        t = unit(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)])
        if u is None:
            u = side_of(t)
        else:
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


def tube(points, radii, tags, k=6, cap0="iron", cap1="iron", phase=0.0, squash=1.0):
    """A closed tube along points with a radius per point; tags one per interval (or a list of k;
    None = buried side); cap0/cap1: the end caps' tags (None: buried)."""
    tags = [tags] * (len(points) - 1) if isinstance(tags, str) else list(tags)
    return loft(rings_along(points, radii, k, phase, squash), tags,
                cap0=(cap0 or "iron", cap0 is not None), cap1=(cap1 or "iron", cap1 is not None))


def arc(p0, d0, d1, length, n=5):
    """n+1 points from p0, leaving along d0 and arriving along d1, about `length` long."""
    p0, d0, d1 = V(p0), unit(d0), unit(d1)
    chord = unit(d0 * 0.55 + d1 * 0.45)
    p3 = p0 + chord * length * 0.93
    p1, p2 = p0 + d0 * length * 0.4, p3 - d1 * length * 0.4
    return [p0 * (1 - s) ** 3 + p1 * 3 * s * (1 - s) ** 2 + p2 * 3 * s * s * (1 - s) + p3 * s ** 3
            for s in (i / n for i in range(n + 1))]


def ring(cx, cy, r, z, k=8, phase=None):
    """A regular k-gon (circumradius r) in the plane z; by default faces toward the axes."""
    phase = math.pi / k if phase is None else phase
    return [V((cx + r * math.cos(phase + 2 * math.pi * i / k), cy + r * math.sin(phase + 2 * math.pi * i / k), z))
            for i in range(k)]


def beam(p, q, r, tag="iron", r2=None):
    """A square bar from p to q (half-size r, tapering to r2; r2=0 ends in a point)."""
    p, q = V(p), V(q)
    d = unit(q - p)
    u = side_of(d)
    v = d.cross(u).normalized()
    r2 = r if r2 is None else r2
    rings = [[c + rr * (u * s + v * t) for s, t in ((-1, -1), (1, -1), (1, 1), (-1, 1))] for c, rr in ((p, r), (q, r2))]
    return loft(rings, [tag], cap0=(tag, True), cap1=(tag, r2 > 0.02))


class IsengardShapes(WorksKit, YardKit):
    """The Isengard kit. Stable API: add pieces, keep these signatures (every Isengard recipe uses them)."""

    Z = Z
    V = V
    tube = staticmethod(tube)
    arc = staticmethod(arc)
    unit = staticmethod(unit)
    side_of = staticmethod(side_of)
    ring = staticmethod(ring)
    beam = staticmethod(beam)

    # ------------------------------------------------------------------ Orthanc stone
    @staticmethod
    def facet(cx, cy, profile, tags, k=8, cap0=("stoneA", False), cap1=("stoneA", True), phase=None):
        """A faceted body of revolution: k hard planes, a (radius, z) profile, a tag per interval."""
        return loft([ring(cx, cy, r, z, k, phase) for r, z in profile], tags, cap0=cap0, cap1=cap1)

    @staticmethod
    def orthanc_horn(base, out, h, w, lean=0.22, curl=0.06, tag="stoneA", n=4):
        """One horn of Orthanc from `base` (on the crown's corner), `out` its horizontal outward
        direction: a four-sided blade w wide at the root (a diamond, its arris toward `out`),
        leaning out by `lean` of its height at the middle and curling back in by `curl` at the tip,
        tapering to a point at h."""
        base, o = V(base), unit(V((out[0], out[1], 0)))
        s = side_of(o)
        rings = []
        for i in range(n + 1):
            f = i / n
            off = o * h * (lean * math.sin(math.pi * f * 0.8) - curl * f * f)
            c = base + Z * (h * f) + off
            r = w * (1 - f) ** 0.8 * (1.0 + 0.25 * (1 - f) ** 4)       # flared at the root
            if i == n:
                rings.append([c.copy() for _ in range(4)])
                continue
            rings.append([c + o * r, c + s * r * 0.62, c - o * r * 0.8, c - s * r * 0.62])
        return loft(rings, [tag] * n, cap0=(tag, False), cap1=(tag, False))

    def orthanc_crown(self, c, z, half, h, w=None, platform=0.7, tag="stoneA"):
        """Orthanc's crown on a tower whose top is the square c +- half at height z: a faceted
        platform (a chamfered square, `platform` of half, h/10 high) and four horns h high on its
        corners, each leaning out along its diagonal."""
        cx, cy = c[0], c[1]
        w = w or half * 0.42
        out = [self.facet(cx, cy, [(half * 1.02, z - 1.0), (half * 1.02, z + 0.8), (half * platform, z + h * 0.1)],
                          [tag, tag], k=8, phase=0.0, cap0=(tag, False), cap1=(tag, True))]
        for i in range(4):
            a = math.pi / 4 + math.pi / 2 * i
            d = V((math.cos(a), math.sin(a), 0))
            base = V((cx, cy, z - 0.5)) + d * half * 1.02
            out.append(self.orthanc_horn(base, d, h, w, tag=tag))
        return out

    # ------------------------------------------------------------------ furnaces
    def chimney(self, c, r, z0, z1, k=8, bands=3, throat=0.72, glow=True, foot=None, spikes=8, collar=None):
        """A furnace stack from z0 to z1 at c: a faceted stone foot (to `foot`, default a quarter
        of the height), a riveted iron barrel with `bands` hoops, a flared lip, and a throat sunk
        into the top whose floor and walls glow ("ember")."""
        cx, cy = c[0], c[1]
        zf = foot if foot is not None else z0 + (z1 - z0) * 0.25
        zm = z0 + (zf - z0) * 0.55                     # a stepped plinth of faceted stone
        out = [self.facet(cx, cy, [(r * 1.55, z0), (r * 1.5, zm), (r * 1.3, zm + 0.8), (r * 1.25, zf - 1.0), (r * 1.08, zf)],
                          ["stoneA", "stoneB", "stoneA", "stoneA"], k=k, cap0=("stoneA", False), cap1=("stoneA", True))]
        lip = z1 - 1.2
        rim, inner, deep = r * 1.18, r * throat, max(1.6, r * 0.9)
        rings = [ring(cx, cy, r, zf - 0.2, k), ring(cx, cy, r * 0.92, lip - 0.6, k), ring(cx, cy, rim, lip, k),
                 ring(cx, cy, rim, z1, k), ring(cx, cy, inner, z1, k), ring(cx, cy, inner, z1 - deep, k)]
        s = loft(rings, ["iron", "iron", "iron", "iron", "ember" if glow else "iron"], cap0=("iron", False),
                 cap1=("ember" if glow else "iron", True))
        out.append(s)
        for i in range(bands):
            zb = zf + (lip - 1.5 - zf) * (i + 0.5) / bands
            rb = r + (r * 0.92 - r) * (zb - zf) / max(lip - zf, 1e-3)
            out += self.hoop((cx, cy), zb, rb, h=1.1, th=0.45, inner=0.8, k=k, rivets=2)
        if collar is not None:                          # a spiked iron collar round the barrel
            rc = r + (r * 0.92 - r) * (collar - zf) / max(lip - zf, 1e-3)
            out += self.hoop((cx, cy), collar, rc, h=1.6, th=0.6, inner=0.8, k=k, rivets=False, tag="trim")
            for i in range(k):
                a = 2 * math.pi * (i + 0.5) / k
                d = V((math.cos(a), math.sin(a), 0))
                p = V((cx, cy, collar)) + d * (rc + 0.4)
                out.append(self.beam(p, p + (d + Z * 0.35).normalized() * r * 0.7, r * 0.09, "iron", 0.0))
        for i in range(spikes):                         # a crown of iron spikes round the lip
            a = 2 * math.pi * (i + 0.5) / spikes
            d = V((math.cos(a), math.sin(a), 0))
            p = V((cx, cy, z1 - 0.4)) + d * rim * 0.97
            out.append(self.beam(p, p + (d * 0.45 + Z).normalized() * r * 0.75, r * 0.1, "iron", 0.0))
        return out
