"""The Dwarven shape vocabulary: heavy, angular, stepped. Every piece is a function of where it
goes; `dz` lifts a whole motif for buildings of another height (0 keeps the fortress's numbers).

    parapet_run      a wall's coping + solid chevron-topped parapet + corbels under it
    chevron_parapet  slabs with stepped-triangle tops (instead of European merlons)
    corbel           the angular bracket under a band
    step_pyramid     a battered, stepped corner block ending in a squat point
    step_gable       a stepped triangle rising over a crown ring
    pointed_arch     the gate's deep stepped pointed frame (the most Dwarven element)
    king_pillar      a tall angular pillar carrying the statue relief
    talus            a battered plinth along a wall, with a string course
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import box_rings, loft, prism_uz, sweep

# (d outward from the wall face, z) profiles; tags per edge, None = buried
PARAPET = [(0, 51.0), (1.2, 52.2), (1.2, 56.6), (0.8, 57.0), (-2.2, 57.0), (-2.2, 52.0)]
PARAPET_TAGS = ["trim", "stoneA", "trim", "top", "stoneA", None]
TALUS = [(0, 0), (3.4, 0), (3.4, 0.9), (1.2, 11.0), (0.0, 11.6)]
TALUS_TAGS = [None, "stoneB", "stoneA", "top", None]
COURSE = [(0, 10.9), (1.6, 10.9), (1.6, 12.3), (1.2, 12.7), (0, 12.7)]
COURSE_TAGS = ["trim", "trim", "trim", "top", None]
LOW_TALUS = [(0, 0), (3.0, 0), (3.0, 0.8), (1.0, 5.8), (0.0, 6.3)]


def lifted(profile, dz):
    return [(d, z + dz) for d, z in profile]


class DwarvenShapes:
    # ------------------------------------------------------------------ walls
    def parapet_run(self, path, chevron_segments, dz=0.0, pitch=8.6):
        """Coping swept along `path`; on the listed segments a solid chevron parapet with a corbel
        every `pitch` units."""
        solids, segs = sweep(path, lifted(PARAPET, dz), PARAPET_TAGS)
        for si in chevron_segments:
            a, b, t, n = segs[si]
            L = (b - a).length
            solids += self.chevron_parapet(a, t, n, L, dz=dz)
            k = max(1, round(L / pitch))
            for i in range(k):
                solids.append(self.corbel(a, t, n, (i + 0.5) * L / k, dz=dz))
        return solids

    def chevron_parapet(self, a, t, n, L, w=8.6, d0=-2.0, d1=1.2, dz=0.0):
        z0, zb, z1, z2, za = (z + dz for z in (56.6, 59.4, 60.7, 62.0, 63.6))
        k = max(1, round(L / w))
        w = L / k
        out = []
        for i in range(k):
            u0, u1 = i * w, (i + 1) * w
            eL = "stoneB" if i == 0 else None
            eR = "stoneB" if i == k - 1 else None
            out.append(prism_uz(a, t, n, [(u0, z0), (u1, z0), (u1, zb), (u0, zb)], d0, d1,
                                [None, eR, "top", eL], "stoneB", "stoneA", bat=0.12))
            g1, g2 = 1.35, 2.7
            out.append(prism_uz(a, t, n, [(u0 + g1, zb), (u1 - g1, zb), (u1 - g1, z1), (u0 + g1, z1)], d0 + 0.3, d1 - 0.5,
                                [None, "stoneB", "top", "stoneB"], "stoneA", "stoneA"))
            out.append(prism_uz(a, t, n, [(u0 + g2, z1), (u1 - g2, z1), (u1 - g2, z2), (u0 + g2, z2)], d0 + 0.6, d1 - 0.8,
                                [None, "stoneB", "top", "stoneB"], "trim", "stoneA"))
            out.append(prism_uz(a, t, n, [(u0 + g2, z2), (u1 - g2, z2), ((u0 + u1) / 2, za)], d0 + 0.6, d1 - 0.8,
                                [None, "top", "top"], "stoneA", "stoneA"))
        return out

    def corbel(self, a, t, n, s, half=0.8, dz=0.0):
        """A wedge from the wall face out to the band's outer edge, under the parapet band."""
        def P(u, d, z):
            return V((a.x + t.x * u + n.x * d, a.y + t.y * u + n.y * d, z + dz))

        def ring(u):
            return [P(u, 0.0, 49.2), P(u, 1.25, 52.3), P(u, 0.0, 52.3)]
        return loft([ring(s - half), ring(s + half)], [["stoneB", None, None]], cap0=("stoneB", True), cap1=("stoneB", True))

    def talus(self, path, course=True, low=False):
        """A battered plinth along a wall run (low: under reliefs that start near the ground),
        optionally with a string course above it."""
        out = sweep(path, LOW_TALUS if low else TALUS, TALUS_TAGS, center=(0, 0))[0]
        if course:
            out += sweep(path, COURSE, COURSE_TAGS, center=(0, 0))[0]
        return out

    # ------------------------------------------------------------------ crowns
    def step_pyramid(self, cx, cy, dz=0.0):
        """Tower-crown corner: three battered tiers stepping inward, then a squat pyramid point."""
        out = []
        tiers = [(3.9, 3.5, 110.8, 116.8, "stoneB"), (2.9, 2.7, 116.8, 119.2, "stoneA"), (1.9, 1.8, 119.2, 120.9, "stoneA")]
        for h0, h1, z0, z1, tg in tiers:
            r0 = box_rings((cx - h0, cx + h0), (cy - h0, cy + h0), z0 + dz, 0.35)
            r1 = box_rings((cx - h1, cx + h1), (cy - h1, cy + h1), z1 + dz, 0.35)
            out.append(loft([r0, r1], [tg], cap0=("top", False), cap1=("top", True)))
        r0 = box_rings((cx - 1.8, cx + 1.8), (cy - 1.8, cy + 1.8), 120.9 + dz, 0.3)
        out.append(loft([r0, [V((cx, cy, 123.0 + dz))] * len(r0)], ["trim"], cap0=("top", False), cap1=("top", False)))
        return out

    def step_gable(self, a, t, n, s, dz=0.0):
        """Mid-side of a crown: a stepped triangle rising over the crown ring."""
        z = [x + dz for x in (117.4, 118.6, 119.8, 121.9)]
        out = []
        for poly, tags, front in (
                ([(s - 6.0, z[0]), (s + 6.0, z[0]), (s + 6.0, z[1]), (s - 6.0, z[1])], ["stoneB", "stoneB", "top", "stoneB"], "trim"),
                ([(s - 3.8, z[1]), (s + 3.8, z[1]), (s + 3.8, z[2]), (s - 3.8, z[2])], [None, "stoneB", "top", "stoneB"], "stoneA"),
                ([(s - 3.8, z[2]), (s + 3.8, z[2]), (s, z[3])], [None, "top", "top"], "stoneA")):
            out.append(prism_uz(a, t, n, poly, -1.4, 0.6, tags, front, "stoneA"))
        return out

    # ------------------------------------------------------------------ gates
    @staticmethod
    def arch_offset(arch, d):
        """`arch` (half outline from the axis: jamb foot, ..., point on the axis) offset outward by d:
        each edge moved along its outward normal, corners re-intersected; the first point stays on
        the ground, the last on the axis."""
        E = []
        for (y0, z0), (y1, z1) in zip(arch, arch[1:]):
            dy, dz = y1 - y0, z1 - z0
            L = math.hypot(dy, dz)
            ny, nz = dz / L, -dy / L
            E.append(((y0 + ny * d, z0 + nz * d), (dy, dz)))

        def meet(e, f):
            (py, pz), (dy, dz) = e
            (qy, qz), (ey, ez) = f
            s = ((qy - py) * ez - (qz - pz) * ey) / (dy * ez - dz * ey)
            return (py + dy * s, pz + dz * s)
        pts = [(E[0][0][0], 0.0)]
        for e, f in zip(E, E[1:]):
            pts.append(meet(e, f))
        (py, pz), (dy, dz) = E[-1]
        pts.append((0.0, pz + dz * (-py / dy)))
        return pts

    def pointed_arch(self, arch, axis_y, outer_y, lintel_z, depths, xs):
        """Rings stepping forward (along +X) around a gate opening, each following the arch and closing
        in a point: ring fronts carry the triangle frieze, inner reveals a bronze band; the last ring
        fills out to `outer_y` and up to `lintel_z`. depths[i]: offset of ring i; xs: ring x planes."""
        out = []

        def piece(poly, x0, x1, tags, front):
            for side in (1, -1):
                def Y(y):
                    return side * outer_y if abs(abs(y) - outer_y) < 1e-6 else axis_y + side * y
                r0 = [V((x0, Y(y), z)) for y, z in poly]
                r1 = [V((x1, Y(y), z)) for y, z in poly]
                out.append(loft([r0, r1], [tags], cap0=("stoneB", False), cap1=(front, front is not None)))
        for i in range(len(depths)):
            inner = self.arch_offset(arch, depths[i])
            x0, x1 = xs[i], xs[i + 1]
            if i < len(depths) - 1:
                outer = self.arch_offset(arch, depths[i + 1])
                for k in range(3):
                    piece([inner[k], outer[k], outer[k + 1], inner[k + 1]], x0, x1, [None, None, None, "trim|a"], "tri|a")
            else:
                j0, j1, sh, ap = inner
                piece([j0, (outer_y, 0.0), (outer_y, j1[1]), j1], x0, x1, [None, None, None, "trim|a"], "stoneB")
                piece([j1, (outer_y, j1[1]), (outer_y, lintel_z), (sh[0], lintel_z), sh], x0, x1,
                      [None, None, None, None, "trim|a"], "stoneB")
                piece([sh, (sh[0], lintel_z), (0.0, lintel_z), ap], x0, x1, [None, None, None, "trim|a"], "stoneB")
        return out

    def king_pillar(self, x0, y0, y1, dz=0.0):
        """A tall angular pillar on a wall front (facing +X at x0) carrying the statue relief, with
        a stepped capital."""
        a, t, n = V((x0, (y0 + y1) / 2, 0)), V((0, 1, 0)), V((1, 0, 0))
        hw = (y1 - y0) / 2
        z = [v + dz for v in (0, 3.2, 31.0, 33.0, 35.6, 38.4)]
        return [
            prism_uz(a, t, n, [(-hw - 0.5, z[0]), (hw + 0.5, z[0]), (hw + 0.5, z[1]), (-hw - 0.5, z[1])], 0, 6.2,
                     [None, "stoneB", "top", "stoneB"], "stoneB", None),
            prism_uz(a, t, n, [(-hw, z[1]), (hw, z[1]), (hw, z[2]), (-hw, z[2])], 0, 5.4,
                     [None, "stoneB", None, "stoneB"], "statue", None, bat=0.02),
            prism_uz(a, t, n, [(-hw - 0.4, z[2]), (hw + 0.4, z[2]), (hw + 0.4, z[3]), (-hw - 0.4, z[3])], 0, 5.7,
                     ["stoneB", "trim", "top", "trim"], "trim", None),
            prism_uz(a, t, n, [(-hw + 0.6, z[3]), (hw - 0.6, z[3]), (hw - 0.6, z[4]), (-hw + 0.6, z[4])], 0, 4.8,
                     [None, "stoneB", "top", "stoneB"], "stoneA", None),
            prism_uz(a, t, n, [(-hw + 0.6, z[4]), (hw - 0.6, z[4]), (0, z[5])], 0, 4.8,
                     [None, "top", "top"], "stoneA", None),
        ]
