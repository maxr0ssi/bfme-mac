"""The Gondor shape vocabulary (Blender side): Minas Tirith's white stone, forged steel and
heraldry. Square-cut and upright where the Dwarves are stepped and battered and the Elves are
pointed and slender. Every piece is a function of where it goes (anchor a, along t, out along n,
as sagekit.blender.geometry.prism_uz; or a centre (cx, cy)).

    beam, rail, turned     bars, polylines and turned (octagonal) bodies: the kit's building blocks
    corbel                 a two-step bracket under a gallery or cornice
    merlons                square crenellations with overhanging capstones along a run
    pinnacle               a square pedestal, a moulded cap, a pyramid spirelet and a steel orb
    bartizan               a corbelled corner turret: slit windows, a cornice, a slate spirelet
    ribs                   bold steel ribs up a dome's edges
    lantern                a lantern cupola on a dome: steel collar, arcaded drum, steel cap
    finial                 a steel mast, a gilt orb and a tall spike
    voussoirs              a round arch of separate wedge stones and a raised keystone
    star                   the seven-pointed star of Gondor (seven gilt kites)
    white_tree             the White Tree as raised strokes: trunk, roots, three tiers of limbs
    shield                 a steel-framed black shield bearing the White Tree
    winged_crest           a winged helm on a pedestal (the crown of the guard)
    banner                 a house-colour banner on a steel rod, silver piping, the White Tree
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import box_rings, loft, prism_uz

Z = V((0, 0, 1))


def beam(p, q, r, tag="trim", r2=None):
    """A square bar from p to q (half-size r, tapering to r2; r2=0 ends in a point)."""
    p, q = V(p), V(q)
    d = (q - p).normalized()
    u = d.cross(Z)
    if u.length < 0.01:
        u = V((1, 0, 0))
    u.normalize()
    v = d.cross(u).normalized()
    r2 = r if r2 is None else r2
    rings = [[c + rr * (u * s + v * t) for s, t in ((-1, -1), (1, -1), (1, 1), (-1, 1))] for c, rr in ((p, r), (q, r2))]
    return loft(rings, [tag], cap0=(tag, True), cap1=(tag, r2 > 0.02))


def rail(points, r, tag="trim", r_end=None):
    """A square bar along a polyline (the dome ribs): one loft, tapering from r to r_end."""
    pts = [V(p) for p in points]
    r_end = r if r_end is None else r_end
    rings = []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = d.cross(Z)
        u = u.normalized() if u.length > 0.01 else V((1, 0, 0))
        v = d.cross(u).normalized()
        rr = r + (r_end - r) * i / (len(pts) - 1)
        rings.append([p + rr * (u * s + v * t) for s, t in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    return loft(rings, [tag] * (len(pts) - 1), cap0=(tag, True), cap1=(tag, True))


def ring(cx, cy, r, z, k=8, phase=None):
    """A regular k-gon (circumradius r) in the plane z; by default faces toward the axes."""
    phase = math.pi / k if phase is None else phase
    return [V((cx + r * math.cos(phase + 2 * math.pi * i / k), cy + r * math.sin(phase + 2 * math.pi * i / k), z))
            for i in range(k)]


def turned(cx, cy, profile, tags, k=8, cap0=("top", False), cap1=("top", True), phase=None):
    """A body of revolution in k facets from a (radius, z) profile; tags per interval."""
    return loft([ring(cx, cy, r, z, k, phase) for r, z in profile], tags, cap0=cap0, cap1=cap1)


def ellipse(half, rise, z0, th):
    return half * math.cos(th), z0 + rise * math.sin(th)


class MenShapes:
    # ------------------------------------------------------------------ galleries and parapets
    @staticmethod
    def corbel(a, t, n, u, z0, w=0.55, z1=None, z2=None, d1=0.9, d2=1.95):
        """Two stacked blocks stepping out from the wall under a gallery (a flat ledge between)."""
        z1 = z0 + 1.8 if z1 is None else z1
        z2 = z1 + 1.8 if z2 is None else z2
        low = prism_uz(a, t, n, [(u - w, z0), (u + w, z0), (u + w, z1), (u - w, z1)], -0.1, d1,
                       ["stoneB", "stoneB", "top", "stoneB"], "stoneA", None)
        high = prism_uz(a, t, n, [(u - w, z1), (u + w, z1), (u + w, z2), (u - w, z2)], -0.1, d2,
                        ["stoneB", "stoneB", None, "stoneB"], "stoneA", None)
        return [low, high]

    @staticmethod
    def merlons(a, t, n, u0, u1, z0, d0, d1, w=2.4, gap=1.8, h=3.0, cap=0.55, lip=0.2):
        """Square merlons with overhanging capstones filling u0..u1 (ends flush with the run)."""
        L = u1 - u0
        k = max(1, round((L + gap) / (w + gap)))
        g = (L - k * w) / (k - 1) if k > 1 else 0.0
        if k == 1:
            u0, w = u0 + (L - w) / 2, w
        out = []
        for i in range(k):
            s = u0 + i * (w + g)
            out.append(prism_uz(a, t, n, [(s, z0), (s + w, z0), (s + w, z0 + h), (s, z0 + h)], d0, d1,
                                [None, "stoneA", None, "stoneA"], "stoneA", "stoneA"))
            zc = z0 + h
            out.append(prism_uz(a, t, n, [(s - lip, zc), (s + w + lip, zc), (s + w + lip, zc + cap), (s - lip, zc + cap)],
                                d0 - lip, d1 + lip, ["stoneB", "stoneB", "top", "stoneB"], "course", "stoneB"))
        return out

    @staticmethod
    def pinnacle(cx, cy, z0, z1, half=1.15, spire=4.4, orb=True):
        """A square pedestal from z0 to z1, a moulded cap, a pyramid spirelet and a steel orb."""
        def box(h, za, zb, tag):
            return loft([box_rings((cx - h, cx + h), (cy - h, cy + h), za, 0), box_rings((cx - h, cx + h), (cy - h, cy + h), zb, 0)],
                        [tag], cap0=("stoneB", True), cap1=("top", True))
        out = [box(half, z0, z1, "stoneA"), box(half + 0.3, z1, z1 + 0.7, "course"),
               loft([box_rings((cx - half, cx + half), (cy - half, cy + half), z1 + 0.7, 0), [V((cx, cy, z1 + 0.7 + spire))] * 4],
                    ["stoneA"], cap0=("stoneB", False), cap1=("top", False))]
        if orb:
            zo = z1 + 0.7 + spire * 0.82
            out.append(turned(cx, cy, [(0.2, zo - 0.2), (0.55, zo + 0.25), (0.55, zo + 0.75), (0.2, zo + 1.2), (0.0, zo + 2.4)],
                              ["trim"] * 4, k=6, cap0=("trim", True), cap1=("trim", False)))
        return out

    @staticmethod
    def bartizan(cx, cy, z0, r=2.05, h=9.8, spire=7.2, facing=0.0):
        """A corner turret corbelled out from z0: a stepped corbel cone, a shaft with slit windows
        toward `facing` (radians), a steel-banded cornice, a slate spirelet and a steel spike."""
        k = 8
        ph = facing - math.pi / k                  # face j looks toward facing + j * 45 degrees
        zs, zt = z0 + 4.0, z0 + 4.0 + h
        slit = ["slit" if i in (0, 2, 6) else "stoneA" for i in range(k)]
        out = [turned(cx, cy, [(0.45, z0), (1.3, z0 + 1.8), (r, zs), (r, zt), (r + 0.35, zt + 0.45), (r + 0.35, zt + 1.2)],
                      ["stoneB", "course", slit, "trim", "trim"], k=k, phase=ph,
                      cap0=("stoneB", True), cap1=("top", True))]
        z = zt + 1.2
        out.append(loft([ring(cx, cy, r + 0.2, z, k, ph), [V((cx, cy, z + spire))] * k], ["slate"],
                        cap0=("slate", True), cap1=("top", False)))
        out.append(beam((cx, cy, z + spire - 1.2), (cx, cy, z + spire + 2.2), 0.2, "trim", 0.0))
        out.append(turned(cx, cy, [(0.2, z + spire - 0.5), (0.45, z + spire), (0.45, z + spire + 0.5), (0.15, z + spire + 0.9)],
                          ["gilt"] * 3, k=6, cap0=("gilt", True), cap1=("gilt", True)))
        return out

    # ------------------------------------------------------------------ domes
    @staticmethod
    def ribs(cx, cy, levels, r=(0.34, 0.2), proud=0.2, mid=True):
        """Steel ribs up a chamfered-square dome given as [(z, half, chamfer)] from the eave up:
        one up every corner edge, and (mid) one up the middle of each long face."""
        rings = [box_rings((cx - h, cx + h), (cy - h, cy + h), z, ch) for z, h, ch in levels]
        lines = [[rg[i] for rg in rings] for i in range(8)]
        if mid:
            for s in (0, 2, 4, 6):
                lines.append([(rg[s] + rg[(s + 1) % 8]) / 2 for rg in rings])
        out = []
        for line in lines:
            pts = []
            for p in line:
                rad = V((p.x - cx, p.y - cy, 0))
                pts.append(p + rad.normalized() * proud + Z * 0.08)
            out.append(rail(pts, r[0], "trim", r[1]))
        return out

    @staticmethod
    def lantern(cx, cy, z0, r=4.4, top=105.3):
        """A lantern cupola sitting on a dome at z0 (where the dome is about r+0.8 across): a steel
        collar, a drum of little arches, a steel cornice and a low steel cap ending at `top`."""
        z = z0
        out = [turned(cx, cy, [(r + 0.9, z), (r + 0.9, z + 0.8), (r + 0.2, z + 1.1), (r + 0.2, z + 1.2)],
                      ["trim", "trim", "trim"], cap0=("trim", False), cap1=("top", True)),
               turned(cx, cy, [(r, z + 1.1), (r, top - 1.1)], ["arcade|a"], cap0=("stoneB", False), cap1=("top", False)),
               turned(cx, cy, [(r - 0.1, top - 1.2), (r + 0.55, top - 1.0), (r + 0.55, top - 0.55), (r + 0.1, top - 0.45)],
                      ["trim", "trim", "trim"], cap0=("trim", True), cap1=("top", True)),
               turned(cx, cy, [(r + 0.15, top - 0.5), (1.1, top)], ["trim"], cap0=("trim", False), cap1=("trim", True))]
        return out

    @staticmethod
    def finial(cx, cy, z0, orb_z, tip):
        """A steel mast from z0, a collar and a gilt orb at orb_z, a ringed steel spike to `tip`."""
        return [turned(cx, cy, [(0.62, z0), (0.62, orb_z - 1.6), (1.0, orb_z - 1.4), (1.0, orb_z - 1.0)],
                       ["trim", "trim", "trim"], k=6, cap0=("trim", False), cap1=("trim", True)),
                turned(cx, cy, [(0.8, orb_z - 1.0), (1.3, orb_z - 0.4), (1.3, orb_z + 0.4), (0.8, orb_z + 1.0), (0.45, orb_z + 1.3)],
                       ["gilt"] * 4, k=8, cap0=("gilt", True), cap1=("gilt", True)),
                turned(cx, cy, [(0.45, orb_z + 1.2), (0.3, orb_z + 5.0), (0.75, orb_z + 5.3), (0.75, orb_z + 5.8),
                                (0.28, orb_z + 6.1), (0.0, tip)],
                       ["trim"] * 5, k=6, cap0=("trim", True), cap1=("trim", False))]

    # ------------------------------------------------------------------ gates
    @staticmethod
    def voussoirs(a, t, n, inner, outer, d0, d1, count=11, gap=0.12, key=None):
        """A round arch of `count` wedge stones between two half-ellipses (half, rise, spring z),
        alternately proud, and a raised keystone (key: (half_top, z_top, d_extra)) at the crown."""
        out = []
        ti, to = inner, outer
        for i in range(count):
            a0 = math.pi * i / count + (gap / ti[0] if i else 0.0)
            a1 = math.pi * (i + 1) / count - (gap / ti[0] if i < count - 1 else 0.0)
            poly = [ellipse(*ti, a0), ellipse(*to, a0), ellipse(*to, a1), ellipse(*ti, a1)]
            if key and i == count // 2:
                (u0, z0), (u1, z1) = ellipse(*ti, a1), ellipse(*ti, a0)
                hw, zt, dx = key
                poly = [(u0, z0), (u1, z1), (hw, zt), (-hw, zt)]
                out.append(prism_uz(a, t, n, poly, d0, d1 + dx, ["stoneB", "stoneB", "top", "stoneB"], "stoneA", None))
                continue
            dd = d1 if i % 2 == 0 else d1 - 0.3
            out.append(prism_uz(a, t, n, poly, d0, dd, ["stoneB", "top", "stoneB", "stoneB"], "stoneA", None))
        return out

    # ------------------------------------------------------------------ heraldry
    @staticmethod
    def star(a, t, n, u, z, r, d0, d1, tag="gilt"):
        """The seven-pointed star: seven kites round a centre, each a closed solid."""
        out = []
        c = (u, z)
        for i in range(7):
            th = math.pi / 2 + 2 * math.pi * i / 7
            tip = (u + r * math.cos(th), z + r * math.sin(th))
            l = (u + 0.42 * r * math.cos(th - math.pi / 7), z + 0.42 * r * math.sin(th - math.pi / 7))
            rr = (u + 0.42 * r * math.cos(th + math.pi / 7), z + 0.42 * r * math.sin(th + math.pi / 7))
            out.append(prism_uz(a, t, n, [c, rr, tip, l], d0, d1, [None, tag, tag, None], tag, None))
        return out

    # the White Tree in a unit box, u -0.5..0.5, z 0..1: ((u0, z0), (u1, z1), thickness). Limbs fan out
    # from three points of the trunk to a rounded crown, with drooping twigs (not a candelabrum)
    TREE = [((0, 0.06), (0, 0.64), 1.5),                                        # trunk
            ((0, 0.14), (-0.22, 0.02), 1.0), ((0, 0.14), (0.22, 0.02), 1.0),    # roots
            ((0, 0.3), (-0.3, 0.44), 1.0), ((0, 0.3), (0.3, 0.44), 1.0),        # lower limbs, bending up
            ((-0.3, 0.44), (-0.44, 0.67), 0.8), ((0.3, 0.44), (0.44, 0.67), 0.8),
            ((-0.3, 0.44), (-0.48, 0.47), 0.6), ((0.3, 0.44), (0.48, 0.47), 0.6),
            ((0, 0.44), (-0.2, 0.62), 0.9), ((0, 0.44), (0.2, 0.62), 0.9),      # middle limbs
            ((-0.2, 0.62), (-0.3, 0.85), 0.7), ((0.2, 0.62), (0.3, 0.85), 0.7),
            ((0, 0.56), (-0.1, 0.78), 0.8), ((0, 0.56), (0.1, 0.78), 0.8),      # upper limbs
            ((-0.1, 0.78), (-0.15, 0.95), 0.6), ((0.1, 0.78), (0.15, 0.95), 0.6),
            ((0, 0.64), (0, 1.0), 0.8)]

    def white_tree(self, a, t, n, u, z, height, d, r=None, tag="relief", back=None):
        """The White Tree, `height` tall with its roots at z, as raised square strokes at d."""
        r = height * 0.03 if r is None else r
        out = []
        for (x0, y0), (x1, y1), k in self.TREE:
            p, q = (u + x0 * height, z + y0 * height), (u + x1 * height, z + y1 * height)
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            w = r * k
            ex, ez = (q[0] - p[0]) / L * w * 0.6, (q[1] - p[1]) / L * w * 0.6     # overlap the joints
            nx, nz = -(q[1] - p[1]) / L * w, (q[0] - p[0]) / L * w
            poly = [(p[0] - ex + nx, p[1] - ez + nz), (p[0] - ex - nx, p[1] - ez - nz),
                    (q[0] + ex - nx, q[1] + ez - nz), (q[0] + ex + nx, q[1] + ez + nz)]
            out.append(prism_uz(a, t, n, poly, d - 0.3, d + 2 * r, [tag] * 4, tag, back))
        return out

    def shield(self, a, t, n, u, z, half, height, d=0.0):
        """A steel-framed black heater shield (point down at z) bearing the White Tree."""
        shape = [(-half, height), (half, height), (half, height * 0.4), (0, 0), (-half, height * 0.4)]
        out = [prism_uz(a, t, n, [(u + x, z + y) for x, y in shape], d - 0.1, d + 0.8, ["trim"] * 5, "trim", None),
               prism_uz(a, t, n, [(u + x * 0.84, z + height * 0.1 + y * 0.84) for x, y in shape], d + 0.7, d + 0.95,
                        ["enamel"] * 5, "enamel", None)]
        return out + self.white_tree(a, t, n, u, z + height * 0.2, height * 0.66, d + 1.0)

    @staticmethod
    def winged_crest(a, t, n, u, z, d0, d1, s=1.0):
        """A winged helm on a pedestal: the helm a gilt-banded steel dome, two steel wings of two
        feathers each sweeping up and out."""
        c = V((a.x + t.x * u + n.x * (d0 + d1) / 2, a.y + t.y * u + n.y * (d0 + d1) / 2, 0))
        out = [prism_uz(a, t, n, [(u - 1.4 * s, z), (u + 1.4 * s, z), (u + 1.4 * s, z + 1.2 * s), (u - 1.4 * s, z + 1.2 * s)],
                        d0 - 0.3, d1 + 0.3, ["stoneB", "stoneB", "top", "stoneB"], "stoneA", "stoneA"),
               turned(c.x, c.y, [(1.15 * s, z + 1.2 * s), (1.15 * s, z + 2.0 * s), (0.85 * s, z + 2.9 * s), (0.0, z + 3.4 * s)],
                      ["gilt", "trim", "trim"], k=8, cap0=("trim", False), cap1=("trim", False))]
        for e in (-1, 1):
            for poly in ([(0.8, 1.6), (4.4, 4.2), (4.9, 5.6), (1.0, 2.9)], [(0.9, 1.3), (3.6, 2.6), (4.0, 3.6), (1.0, 2.2)]):
                out.append(prism_uz(a, t, n, [(u + e * x * s, z + y * s) for x, y in poly], (d0 + d1) / 2 - 0.25,
                                    (d0 + d1) / 2 + 0.25, ["trim"] * 4, "trim", "trim"))
        return out

    def banner(self, a, t, n, u, z_top, width, length, d=1.0):
        """A house-colour banner hung `d` out from a wall face, clear of what EA carved on it: a
        steel rod from the wall with gilt knobs, the cloth ending in a point, silver piping down
        both edges and a steel band across, the White Tree raised on it. The steel and the tree are
        solids of their own, so the cloth alone leaves for the house-colour model
        (Building.house_tags)."""
        h, tail = width / 2, min(2.8, width * 0.45)
        zb = z_top - length
        cloth = [(u, zb), (u + h, zb + tail), (u + h, z_top), (u - h, z_top), (u - h, zb + tail)]
        out = [prism_uz(a, t, n, cloth, d - 0.05, d + 0.3, ["cloth"] * 5, "cloth", "cloth")]
        for e in (-1, 1):
            u0, u1 = sorted((u + e * (h - 0.25), u + e * (h + 0.2)))
            out.append(prism_uz(a, t, n, [(u0, zb + tail), (u1, zb + tail), (u1, z_top), (u0, z_top)], d - 0.15, d + 0.5,
                                ["trim"] * 4, "trim", "trim"))
        zr = z_top - 2.2
        out.append(prism_uz(a, t, n, [(u - h, zr - 0.9), (u + h, zr - 0.9), (u + h, zr), (u - h, zr)], d + 0.1, d + 0.5,
                            ["trim"] * 4, "trim", "trim"))
        out.append(prism_uz(a, t, n, [(u - h - 1.0, z_top - 0.1), (u + h + 1.0, z_top - 0.1), (u + h + 1.0, z_top + 0.8),
                                      (u - h - 1.0, z_top + 0.8)], -0.1, d + 0.6, ["trim"] * 4, "trim", None))
        for e in (-1, 1):
            k = u + e * (h + 1.4)
            out.append(prism_uz(a, t, n, [(k - 0.5, z_top - 0.3), (k + 0.5, z_top - 0.3), (k + 0.5, z_top + 1.0), (k - 0.5, z_top + 1.0)],
                                -0.1, d + 0.7, ["gilt"] * 4, "gilt", None))
        tree_h = min(length * 0.55, width * 1.35)
        # closed behind too: the cloth they lie on leaves the body for the house-colour model
        out += self.white_tree(a, t, n, u, zr - 1.6 - tree_h, tree_h, d + 0.42, r=0.17, back="relief")
        return out
