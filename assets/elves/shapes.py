"""The Elven shape vocabulary: slender, curving, pointed - the Dwarven kit's opposite. Where the
Dwarves step and batter, the Elves sweep: arches rise to a point or turn back into an ogee, roofs
curve up at the eaves, columns are thin and flower into leaves, and every tip ends in a gilt leaf.

Conventions as the Dwarven kit (assets/dwarves/shapes.py): a wall-face piece takes an anchor `a`, the
face's direction `t`, its outward normal `n` (t x n = -z) and a position `u` along it, with z
absolute; a free-standing piece takes a centre (cx, cy). Every piece returns a list of closed
solids (sagekit.blender.geometry: buried faces are kept in the solid, dropped from the mesh), each
polygon convex (the mesh triangulates fans). Curves are sampled; `k` sets how finely.

    arch_outline     half an arch [(u, z)]: pointed (ogee 0) through to a full ogee (1)
    arch             a pointed or ogee arch frame round an opening: jambs, voussoirs, a leaf at the tip
    ogee_gable       a house-front gable whose outline is an ogee, enamel-edged, with a finial
    lancet_parapet   a wall's parapet of merlons, each topped with a leaf blade (silver-rimmed)
    coping_run       a moulded coping swept along a wall run
    filigree_band    a knotwork band between two gilt beads along a wall run
    column           a slender round column: moulded base, shaft, bell capital wrapped in leaves
    leaf_blade       one lanceolate blade, the motif every finial and capital is made of
    leaf_finial      crossed gilt leaf blades on a collar: the tip of every roof, arch and pole
    swept_roof       a round or polygonal roof with a concave sweep and up-turned eaves, gilt lip
                     (its corner quads are slightly warped where the eaves turn up: fan-split by the mesh;
                     the soffit cap keeps the plan's corners only, no in-line points)
    swan_neck        a curved bracket (the swan's neck): carries lanterns, props eaves and prows
    crystal_lantern  a crystal in a gilt cup under a gilt cap (the night lights' motif)
    hung_lantern     a crystal lantern hanging from a swan-neck bracket on a wall
    balustrade       a curved-friendly balustrade: plinth, turned balusters, rounded rail
    terrace          stacked rounded platforms (superellipse plan), each with a coping lip
    leaf_banner      a leaf-shaped hanging banner with a gilt midrib on a gilt rod (house colour)
    pennant          a long leaf pennant flying from a pole (house colour)
    banner_pole      a slender gilt pole with a leaf finial, flying a leaf banner and a pennant
    arc, ring        path and ring helpers (arcs for curved walls; ellipse / superellipse rings)
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import loft, prism_uz, sweep


# ------------------------------------------------------------------ helpers
def arc(cx, cy, r, a0, a1, k=12):
    """Points of an arc (degrees, counter-clockwise from a0 to a1): a path for sweeps and balustrades."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / k)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / k)))
            for i in range(k + 1)]


def ring(cx, cy, rx, z, k=12, ry=None, sq=2.0, phase=0.0):
    """A closed ring in the plane z: an ellipse (rx, ry), or a superellipse squared off by sq > 2."""
    ry, e = ry if ry is not None else rx, 2.0 / sq
    out = []
    for i in range(k):
        c, s = math.cos(phase + 2 * math.pi * i / k), math.sin(phase + 2 * math.pi * i / k)
        out.append(V((cx + rx * math.copysign(abs(c) ** e, c), cy + ry * math.copysign(abs(s) ** e, s), z)))
    return out


def bezier(p0, p1, p2, p3, k):
    out = []
    for i in range(k + 1):
        s = i / k
        w = ((1 - s) ** 3, 3 * s * (1 - s) ** 2, 3 * s * s * (1 - s), s ** 3)
        out.append(tuple(sum(wi * p[j] for wi, p in zip(w, (p0, p1, p2, p3))) for j in range(2)))
    return out


def turned(cx, cy, profile, tags, k=10, cap0=("top", False), cap1=("top", True)):
    """A solid of revolution from [(r, z)] (bottom to top); tags per interval."""
    return loft([ring(cx, cy, r, z, k) for r, z in profile], tags, cap0=cap0, cap1=cap1)


def corners(pts, eps=1e-3):
    """A flat convex polygon without its in-line points: a cap over a ring subdivided along straight
    sides (swept_roof's soffit) would otherwise fan into zero-width slivers there, which the checks
    see back-on from the sky and whose vertices the mesh left loose. float32 in-line within 0.1 %."""
    n = len(pts)
    keep = [p for i, p in enumerate(pts)
            if (p - pts[i - 1]).normalized().cross((pts[(i + 1) % n] - p).normalized()).length > eps]
    return keep if len(keep) >= 3 else pts


def _norm(u, z):
    L = math.hypot(u, z) or 1.0
    return u / L, z / L


# the longest single leaf-blade face: the gilt region's tile on EBFortress is 24 px at 5.6 px a unit
# (4.29 units): a longer blade is built in pieces under it
BLADE_PIECE = 4.25


class ElvenShapes:
    # ------------------------------------------------------------------ arches
    @staticmethod
    def arch_outline(half, spring, apex, ogee=0.0, k=8):
        """Half an arch, from the springing (half, spring) to the tip (0, apex), leaving the jamb
        upright. ogee 0: a pointed arch (two circle arcs meeting at the tip; a round or elliptic arch
        when the rise is at most `half`), convex; ogee 1: the Elvish leaf arch, the curve turning
        back to rise to the tip upright (an S, so not convex: frames, not slabs); between: a blend."""
        H = apex - spring
        if H > half:
            R = (half * half + H * H) / (2 * half)
            end = math.atan2(H, R - half)
            pts = [(half - R + R * math.cos(end * i / k), spring + R * math.sin(end * i / k)) for i in range(k + 1)]
        else:
            pts = [(half * math.cos(math.pi / 2 * i / k), spring + H * math.sin(math.pi / 2 * i / k)) for i in range(k + 1)]
        pts[-1] = (0.0, apex)
        if ogee <= 0:
            return pts
        s_curve = bezier((half, spring), (half, spring + 0.8 * H), (0.0, spring + 0.45 * H), (0.0, apex), k)
        return [(p[0] + (q[0] - p[0]) * ogee, p[1] + (q[1] - p[1]) * ogee) for p, q in zip(pts, s_curve)]

    @staticmethod
    def _offset(outline, w):
        """The outline moved w away from the opening; its last point closes on the axis, above the
        tip (how far above follows the angle the arch meets the axis at)."""
        out = []
        for i, (u, z) in enumerate(outline):
            a, b = outline[max(i - 1, 0)], outline[min(i + 1, len(outline) - 1)]
            nu, nz = _norm(b[1] - a[1], -(b[0] - a[0]))
            out.append((u + w * nu, z + w * nz))
        (u0, z0), (u1, z1) = outline[-2], outline[-1]
        slope = abs(z1 - z0) / max(abs(u1 - u0), 1e-6)
        out[-1] = (0.0, outline[-1][1] + min(w * math.hypot(1, slope), 3.0 * w))
        return out

    def arch(self, a, t, n, u, half, z0, spring, apex, w=1.2, d0=0.0, d1=1.0, ogee=0.0, k=8, free=False,
             finial=True):
        """A frame round an opening centred at u on a wall face: two jambs from z0 to the springing
        and voussoirs following arch_outline to the tip, fronts in silver moulding, the reveal and
        soffit in sea-green enamel; a leaf finial over the tip. The back lies on the wall unless
        `free` (a free-standing arch: every face kept)."""
        back = "stoneB" if free else None
        inner = self.arch_outline(half, spring, apex, ogee, k)
        outer = self._offset(inner, w)
        # the first voussoir sits square on its jamb: _offset moves the springing out along the first
        # chord's normal, a little above the jamb's top, which left a wedge open between the two (seen
        # through on a free-standing arch, whose back is drawn, and on flat arches)
        outer[0] = (half + w, spring)
        out = []
        for s in (1, -1):
            def U(p):
                return (u + s * p[0], p[1])
            jamb = [U((half, z0)), U((half + w, z0)), U((half + w, spring)), U((half, spring))]
            out.append(prism_uz(a, t, n, jamb, d0, d1, [None, "stoneB", None, "enamel"], "trim|v", back))
            for i in range(k):
                q = [U(inner[i]), U(inner[i + 1]), U(outer[i + 1]), U(outer[i])]
                out.append(prism_uz(a, t, n, q, d0, d1, ["enamel", None, "stoneB", None], "trim|a", back))
        if finial:
            tip = outer[-1][1]
            out += self.leaf_finial_on(a, t, n, u, tip - 0.2, 2.4 * w, (d0 + d1) / 2, w * 0.9)
        return out

    def ogee_gable(self, a, t, n, u, half, z0, apex, w=0.55, d0=0.0, d1=0.8, k=10, ogee=0.7):
        """A house-front gable (over a door, a bay, a stable front): an ogee outline from (u +- half,
        z0) to the tip (arch_outline's `ogee`: 1 is a full onion-like S, 0.7 a leaf), edged in enamel
        standing 0.25 proud, a leaf finial on the tip. The fill is one stone slab up to where the
        outline turns back (the convex part) and upright strips above."""
        inner = self.arch_outline(half, z0, apex, ogee, k)
        outer = self._offset(inner, w)
        turn = next((i for i in range(1, k) if (inner[i][0] - inner[i - 1][0]) * (inner[i + 1][1] - inner[i][1])
                     - (inner[i][1] - inner[i - 1][1]) * (inner[i + 1][0] - inner[i][0]) < 0), k)
        zt = inner[turn][1]
        low = [(u + x, z) for x, z in inner[:turn + 1]] + [(u - x, z) for x, z in reversed(inner[:turn + 1])]
        out = [prism_uz(a, t, n, low, d0, d1, [None] * len(low), "stoneB", None)]
        for s in (1, -1):
            def U(p):
                return (u + s * p[0], p[1])
            for i in range(k):
                if i >= turn:
                    strip = [U((inner[i][0], zt)), U((inner[i + 1][0], zt)), U(inner[i + 1]), U(inner[i])]
                    out.append(prism_uz(a, t, n, strip, d0, d1, [None] * 4, "stoneB", None))
                q = [U(inner[i]), U(inner[i + 1]), U(outer[i + 1]), U(outer[i])]
                out.append(prism_uz(a, t, n, q, d0, d1 + 0.25, ["enamel", None, "enamel", None], "enamel|a", None))
        out += self.leaf_finial_on(a, t, n, u, outer[-1][1] - 0.2, 5.0 * w, (d0 + d1) / 2, 1.6 * w)
        return out

    # ------------------------------------------------------------------ walls
    def lancet_parapet(self, a, t, n, L, z0, h=4.6, w=2.4, gap=1.6, d0=-1.0, d1=0.6):
        """Merlons along (a, t) from 0 to L, spaced evenly, each topped with a leaf: a stone shaft
        pinched to a stalk, over it a blade a little wider than the shaft, rounded at the shoulder and
        tapering to a point (a leaf, not the Gondor or Gothic spike). Fronts in dressed stone, the
        blade's upper rim in silver, a silver fillet at the foot. Shaft, stalk and blade are each one
        convex slab; the blade stays inside its pitch (the run's ends included)."""
        k = max(1, round(L / (w + gap)))
        pitch = L / k
        blade_half = w / 2 + min(0.1 * w, 0.3 * (pitch - w))
        blade = self._leaf_blade_outline(w * 0.3, blade_half, z0 + h * 0.38, z0 + h)
        widest = max(range(len(blade)), key=lambda j: blade[j][0])
        out = []
        for i in range(k):
            c = (i + 0.5) * pitch
            zs, zn = z0 + h * 0.3, blade[0][1]
            out.append(prism_uz(a, t, n, [(c - w / 2, z0), (c + w / 2, z0), (c + w / 2, zs), (c - w / 2, zs)], d0, d1,
                                [None, "stoneB", None, "stoneB"], "stoneA", "stoneA"))
            out.append(prism_uz(a, t, n, [(c - w / 2, zs), (c + w / 2, zs), (c + blade[0][0], zn), (c - blade[0][0], zn)],
                                d0, d1, [None, "top", None, "top"], "stoneA", "stoneA"))
            right = [(c + x, z) for x, z in blade[:-1]]
            poly = [(c - blade[0][0], zn)] + right + [(c, blade[-1][1])] + [(c - x, z) for x, z in reversed(blade[1:-1])]
            m = len(blade) - 1                  # edges up the right side: 1..m, down the left: m+1..2m
            tags = [None] + ["stoneB" if j < widest else "trim" for j in range(m)] + \
                   ["trim" if j < m - widest else "stoneB" for j in range(m)]
            out.append(prism_uz(a, t, n, poly, d0, d1, tags, "stoneA", "stoneA"))
            out.append(prism_uz(a, t, n, [(c - w / 2 - 0.1, z0 - 0.05), (c + w / 2 + 0.1, z0 - 0.05), (c + w / 2 + 0.1, z0 + 0.35),
                                          (c - w / 2 - 0.1, z0 + 0.35)], d0 - 0.1, d1 + 0.1, [None, "trim", "top", "trim"],
                                "trim", "trim"))
        return out

    @staticmethod
    def _leaf_blade_outline(stalk, half, z0, tip, shoulder=0.3, taper=1.4):
        """The right half of a leaf blade [(x, z)] from its stalk (stalk, z0) to its tip (0, tip): out
        to `half` at `shoulder` of the length on a quarter sine, then in to the point on 1 - s**taper
        (taper > 1: a full leaf, straight near the tip). Both parts are concave, so the whole blade
        is one convex polygon."""
        H = tip - z0
        out = []
        for s in (0.0, 0.1, 0.2, shoulder, 0.45, 0.6, 0.74, 0.87, 1.0):
            if s <= shoulder:
                x = stalk + (half - stalk) * math.sin(math.pi / 2 * s / shoulder)
            else:
                x = half * (1 - ((s - shoulder) / (1 - shoulder)) ** taper)
            out.append((x, z0 + H * s))
        return out

    @staticmethod
    def coping_run(path, z, d_out=1.1, d_in=-2.0, center=(0, 0)):
        """A moulded coping along a wall run: a rounded nose d_out proud over a fillet, the top at z."""
        prof = [(0.0, z - 1.6), (d_out * 0.55, z - 1.6), (d_out, z - 1.1), (d_out, z - 0.45), (d_out * 0.7, z),
                (d_in, z), (d_in, z - 1.6)]
        return sweep(path, prof, ["trim", "trim", "coping", "trim", "top", "stoneB", None], center=center)[0]

    @staticmethod
    def filigree_band(path, z0, z1, d=0.3, center=(0, 0)):
        """A knotwork band (silver knots on sea-green enamel) between two gilt beads, d proud of the
        wall face along a run."""
        out = sweep(path, [(-0.1, z0), (d, z0), (d, z1), (-0.1, z1)], [None, "knot", "top", None], center=center)[0]
        for zb in (z0, z1):
            out += sweep(path, [(-0.1, zb - 0.22), (d + 0.12, zb - 0.22), (d + 0.18, zb), (d + 0.12, zb + 0.22),
                                (-0.1, zb + 0.22)], [None, "gilt", "gilt", "gilt", None], center=center)[0]
        return out

    # ------------------------------------------------------------------ columns and leaves
    @staticmethod
    def leaf_blade(a, t, n, u0, z0, length, width, lean=0.0, thick=0.12, d=0.0, tag="gilt", k=4):
        """A lanceolate blade in the plane (t, z) at offset d along n: from its foot (u0, z0) along a
        direction `lean` radians off the vertical (towards +t), widest two fifths of the way up. A
        blade longer than BLADE_PIECE is built as a stack of pieces (joints buried), each under the
        gilt region's tile height: the atlas mapper tiles a longer face, and the tile cut near the
        pointed tip left slivers the checks saw back-on from the sky. -> one Solid (the pieces' shells)."""
        du, dz = math.sin(lean), math.cos(lean)
        pu, pz = dz, -du

        def hw(x):
            return 0.5 * width * math.sin(math.pi * (x / length) ** 0.75) if 0 < x < length else 0.0

        def P(x, side):
            return (u0 + du * x + side * pu * hw(x), z0 + dz * x + side * pz * hw(x))
        xs = [length * i / (k + 1) for i in range(k + 2)]
        m = math.ceil(length / BLADE_PIECE - 1e-9)
        if m <= 1:
            pts = [P(0.0, 1)] + [P(x, 1) for x in xs[1:-1]] + [P(length, 1)] + [P(x, -1) for x in reversed(xs[1:-1])]
            return prism_uz(a, t, n, pts, d - thick / 2, d + thick / 2, [tag] * len(pts), tag, tag)
        cuts = [length * j / m for j in range(m + 1)]
        xs = sorted(set(xs) | set(cuts))
        out = []
        for xa, xb in zip(cuts, cuts[1:]):
            seg = [x for x in xs if xa - 1e-9 <= x <= xb + 1e-9]
            left = [P(x, 1) for x in seg]
            right = [P(x, -1) for x in reversed(seg)]
            if hw(xb) == 0:                     # the tip: one point
                right = right[1:]
            if hw(xa) == 0:                     # the foot: one point
                right = right[:-1]
            pts = left + right
            tags = [tag] * len(pts)
            if hw(xb) > 0:
                tags[len(left) - 1] = None      # the joint with the piece above
            if hw(xa) > 0:
                tags[-1] = None                 # the joint with the piece below
            out.append(prism_uz(a, t, n, pts, d - thick / 2, d + thick / 2, tags, tag, tag))
        solid = out[0]
        for piece in out[1:]:
            solid.polys += piece.polys
        return solid

    def leaf_finial(self, cx, cy, z, height, width=None):
        """Two crossed gilt leaf blades on a gilt collar, rising from z: the tip of every roof, pole
        and pinnacle."""
        width = width or height * 0.34
        out = [turned(cx, cy, [(width * 0.34, z - 0.1), (width * 0.42, z + 0.12 * height), (width * 0.2, z + 0.2 * height)],
                      ["gilt", "gilt"], k=8, cap0=("gilt", False), cap1=("gilt", True))]
        c = V((cx, cy, 0))
        for t, n in ((V((1, 0, 0)), V((0, 1, 0))), (V((0, 1, 0)), V((-1, 0, 0)))):
            out.append(self.leaf_blade(c, t, n, 0.0, z + 0.1 * height, height * 0.9, width, thick=width * 0.14))
        return out

    def leaf_finial_on(self, a, t, n, u, z, height, d, width=None):
        """A leaf finial at (u, d) of a wall-face frame: two crossed blades, one in the face."""
        p = V((a.x + t.x * u + n.x * d, a.y + t.y * u + n.y * d, 0))
        return self.leaf_finial(p.x, p.y, z, height, width)

    def column(self, cx, cy, z0, z1, r=0.8, k=12, leaves=6, base=True, capital=True, leaf_tag="gilt"):
        """A slender column from z0 to z1: a moulded base, a shaft with a faint swell, and a bell
        capital wrapped in `leaves` blades under a square abacus."""
        zb = z0 + (1.1 * r if base else 0.0)
        hc = 2.6 * r if capital else 0.0
        zc = z1 - hc
        out = []
        if base:
            out.append(turned(cx, cy, [(1.55 * r, z0), (1.55 * r, z0 + 0.3 * r), (1.3 * r, z0 + 0.5 * r), (1.12 * r, zb)],
                              ["stoneB", "coping", "trim"], k, cap0=("stoneB", False), cap1=("top", True)))   # its
        # top ring (1.12 r) is wider than the shaft (r): the cap shows round the shaft's foot
        out.append(turned(cx, cy, [(r, zb), (1.04 * r, zb + 0.35 * (zc - zb)), (0.94 * r, zc)], ["column", "column"], k,
                          cap0=("top", False), cap1=("top", False)))
        if not capital:
            return out
        za = z1 - 0.45 * r
        out.append(turned(cx, cy, [(0.94 * r, zc), (1.0 * r, zc + 0.25 * hc), (1.45 * r, za)], ["capital", "capital"], k,
                          cap0=("top", False), cap1=("top", False)))
        h = 1.75 * r
        out.append(loft([ring(cx, cy, h, za, 4, sq=6.0, phase=math.pi / 4), ring(cx, cy, h, z1, 4, sq=6.0, phase=math.pi / 4)],
                        ["coping"], cap0=("stoneB", True), cap1=("top", True)))
        for i in range(leaves):
            ang = 2 * math.pi * (i + 0.5) / leaves
            tt, nn = V((math.cos(ang), math.sin(ang), 0)), V((-math.sin(ang), math.cos(ang), 0))
            out.append(self.leaf_blade(V((cx, cy, 0)), tt, nn, 0.9 * r, zc + 0.1 * hc, hc * 0.95, 1.1 * r, lean=0.42,
                                       thick=0.1, tag=leaf_tag))
        return out

    # ------------------------------------------------------------------ roofs and brackets
    def swept_roof(self, cx, cy, r, z, h, k=8, sq=2.0, per_side=3, upturn=0.9, lip=0.35, sweep_pow=1.7, finial=True,
                   phase=0.0):
        """A roof over a round (k large) or polygonal plan of radius r: a concave sweep from the eaves
        at z to a point h above, the eaves turned up at every corner by `upturn` (swan-neck eaves), a
        gilt lip along the eave, pale birch soffit underneath; a leaf finial at the top. The plan's
        corners sit at angles phase + 360/k * i (k=4, phase=pi/4: a square roof over an x/y box)."""
        m = k * per_side

        def lift(i):                      # 1 at a corner, 0 mid-side
            f = (i % per_side) / per_side
            return (1 - 2 * min(f, 1 - f)) ** 2

        def R(rad, zz, up):
            base = ring(cx, cy, rad, zz, k, sq=sq, phase=phase)
            pts = []
            for j in range(k):
                p, q = base[j], base[(j + 1) % k]
                for s in range(per_side):
                    pts.append(p.lerp(q, s / per_side))
            return [V((p.x, p.y, p.z + up * lift(i))) for i, p in enumerate(pts)]
        rings = [R(r * 0.8, z, 0.0), R(r, z, upturn), R(r, z + lip, upturn)]
        tags = ["birch", "gilt"]
        steps = 6
        for i in range(1, steps + 1):
            s = i / steps
            fade = max(0.0, 1 - 3 * s)
            rings.append(R(r * (1 - s) ** sweep_pow if i < steps else 0.0, z + lip + h * s, upturn * fade))
            tags.append("roof")
        rings[-1] = [V((cx, cy, z + lip + h))] * m
        roof = loft(rings, tags, cap0=("birch", True), cap1=("top", False))
        for e in roof.polys:              # the soffit cap: only the eave ring's corners (see below)
            if e[1] == "birch" and len(e[0]) > 4:
                e[0] = corners(e[0])
        out = [roof]
        if finial:
            out += self.leaf_finial(cx, cy, z + lip + h - 0.3, max(1.8, h * 0.28))
        return out

    @staticmethod
    def swan_neck(a, t, n, u, z0, height, reach, size=0.35, d=0.0, k=10, tag="gilt"):
        """A curved bracket in the plane (t, z) at offset d: it leaves (u, z0) upright, arches over
        towards +t by `reach` and droops its head, tapering from `size` (half thickness) to half."""
        pts = bezier((u, z0), (u, z0 + 0.7 * height), (u + reach, z0 + 1.15 * height), (u + reach, z0 + 0.72 * height), k)

        def P(uu, dd, zz):
            return V((a.x + t.x * uu + n.x * dd, a.y + t.y * uu + n.y * dd, zz))
        rings = []
        for i, (uu, zz) in enumerate(pts):
            p, q = pts[max(i - 1, 0)], pts[min(i + 1, k)]
            tu, tz = _norm(q[0] - p[0], q[1] - p[1])
            h = size * (1 - 0.5 * i / k)
            nu, nz = tz * h, -tu * h
            rings.append([P(uu - nu, d - h, zz - nz), P(uu + nu, d - h, zz + nz), P(uu + nu, d + h, zz + nz), P(uu - nu, d + h, zz - nz)])
        return [loft(rings, [tag] * k, cap0=(tag, False), cap1=(tag, True))]

    # ------------------------------------------------------------------ lanterns
    def crystal_lantern(self, cx, cy, z, h=3.0, r=0.7, k=8, finial=True):
        """A long crystal (a bipyramid) seated in a gilt cup, under a small gilt cap and leaf tip,
        standing on z. Where a light is (the night lights' crystal motif)."""
        out = [turned(cx, cy, [(0.35 * r, z), (0.55 * r, z + 0.08 * h), (1.05 * r, z + 0.22 * h), (0.9 * r, z + 0.26 * h)],
                      ["gilt", "gilt", "gilt"], k, cap0=("gilt", True), cap1=("gilt", True))]
        out.append(turned(cx, cy, [(0.2 * r, z + 0.2 * h), (0.85 * r, z + 0.5 * h), (0.3 * r, z + 0.84 * h)],
                          ["crystal", "crystal"], k, cap0=("crystal", False), cap1=("crystal", False)))
        out.append(turned(cx, cy, [(0.42 * r, z + 0.8 * h), (0.62 * r, z + 0.86 * h), (0.25 * r, z + 0.93 * h)],
                          ["gilt", "gilt"], k, cap0=("gilt", True), cap1=("gilt", True)))
        if finial:
            out += self.leaf_finial(cx, cy, z + 0.92 * h, 0.35 * h, 0.5 * r)
        return out

    def hung_lantern(self, a, t, n, u, z, reach=2.4, h=2.6):
        """A crystal lantern hanging from a swan-neck bracket set into a wall face at (u, z): the
        bracket rises in the plane of n (out of the wall), the lantern hangs on a gilt rod."""
        out = self.swan_neck(a, n, t, 0.0, z, h * 0.9, reach, size=0.22, d=u, k=8)
        p = V((a.x + n.x * reach + t.x * u, a.y + n.y * reach + t.y * u, 0))
        zt = z + 0.72 * h * 0.9
        out.append(turned(p.x, p.y, [(0.07, zt - 0.9), (0.07, zt + 0.1)], ["gilt"], 6, cap0=("gilt", True), cap1=("gilt", False)))
        out += self.crystal_lantern(p.x, p.y, zt - 0.9 - h, h, 0.5, finial=False)
        return out

    # ------------------------------------------------------------------ balustrades and terraces
    @staticmethod
    def balustrade(path, z0, height=3.0, pitch=1.4, center=(0, 0), r=0.26):
        """A balustrade along a path (straight runs or arc(): it follows curves): a plinth, turned
        balusters every `pitch`, and a rounded silver rail."""
        zt = z0 + height
        out = sweep(path, [(-0.45, z0), (0.45, z0), (0.45, z0 + 0.45), (-0.45, z0 + 0.45)], [None, "stoneB", "top", "stoneB"],
                    center=center)[0]
        out += sweep(path, [(-0.42, zt - 0.4), (0.42, zt - 0.4), (0.52, zt - 0.18), (0.36, zt + 0.08), (-0.36, zt + 0.08),
                            (-0.52, zt - 0.18)], ["trim", "trim", "top", "top", "trim", "trim"], center=center)[0]
        prof = [(0.8 * r, z0 + 0.45), (1.25 * r, z0 + 0.45 + 0.28 * (height - 0.85)), (0.62 * r, z0 + 0.45 + 0.72 * (height - 0.85)),
                (1.0 * r, zt - 0.4)]
        for (x0, y0), (x1, y1) in zip(path, path[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            m = max(1, round(L / pitch))
            for i in range(m):
                f = (i + 0.5) / m
                out.append(turned(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, prof, ["stoneB", "trim", "stoneB"], 8,
                                  cap0=("top", False), cap1=("top", False)))
        return out

    @staticmethod
    def terrace(cx, cy, rx, ry, z0, tiers, k=32, sq=2.6):
        """Stacked platforms of a rounded plan (superellipse rx x ry, squared by sq), bottom up:
        tiers [(height, inset)] - each rises `height` from the last one's top, `inset` in from its
        edge (the first from rx, ry), with a slight batter and a coping lip (0.35 out) under a pale top."""
        out, z, ix, iy = [], z0, rx, ry
        for hgt, inset in tiers:
            ix, iy = ix - inset, iy - inset

            def R(e, zz):
                return ring(cx, cy, ix + e, zz, k, ry=iy + e, sq=sq)
            rings = [R(0.0, z), R(-0.25, z + hgt - 0.5), R(0.35, z + hgt - 0.35), R(0.35, z + hgt - 0.1), R(0.0, z + hgt)]
            out.append(loft(rings, ["stoneA", "course", "coping", "trim"], cap0=("stoneB", False), cap1=("top", True)))
            z += hgt
        return out

    # ------------------------------------------------------------------ cloth (house colour)
    @staticmethod
    def leaf_banner(a, t, n, u, z_top, width, length, d=0.0, free=False, k=4):
        """A leaf-shaped banner hanging on a wall face (a, t, n) centred at u: the cloth widest near
        the top and drawn to a point, a gilt midrib down it and a gilt rod with leaf-bud ends. The
        cloth's back lies on the face unless `free`. Gilt parts are separate solids: the cloth leaves
        the body for the house-colour model and takes the player's colour."""
        back = "cloth" if free else None
        h, zb = width / 2, z_top - length
        # half width (1 - y)(y + 0.4) / 0.49: widest (h) three tenths down, pointed at the tip; concave in y,
        # so the cloth stays one convex polygon (one banner motif, one fan)
        side = [(h * (1 - y) * (y + 0.4) / 0.49, z_top - length * y) for y in (i / (k + 1) for i in range(1, k + 1))]
        cloth = [(u - 0.816 * h, z_top), (u + 0.816 * h, z_top)] + [(u + x, zz) for x, zz in side] + [(u, zb)] + \
                [(u - x, zz) for x, zz in reversed(side)]
        tags = [None] + ["cloth"] * (len(cloth) - 1)
        out = [prism_uz(a, t, n, cloth, d - 0.05, d + 0.25, tags, "cloth", back)]
        out.append(prism_uz(a, t, n, [(u - 0.14, zb + 0.25 * length), (u + 0.14, zb + 0.25 * length), (u + 0.14, z_top - 0.4),
                                      (u - 0.14, z_top - 0.4)], d + 0.1, d + 0.4, ["gilt"] * 4, "gilt", "gilt"))
        out.append(prism_uz(a, t, n, [(u - h - 0.5, z_top), (u + h + 0.5, z_top), (u + h + 0.5, z_top + 0.55), (u - h - 0.5, z_top + 0.55)],
                            d - (0.9 if free else 0.1), d + 0.7, ["gilt"] * 4, "gilt", "gilt"))
        for s in (1, -1):                       # leaf-bud rod ends
            out.append(ElvenShapes.leaf_blade(a, t, n, u + s * (h + 0.4), z_top + 0.27, 1.4, 0.7, lean=s * 1.3, thick=0.3,
                                              d=d + 0.3))
        return out

    @staticmethod
    def pennant(a, t, n, u, z, length, width, d=0.0, k=5):
        """A long leaf pennant flying along +t from a pole at u, its top edge at z, drooping gently
        and tapering to a point: k upright strips (the whole outline is not convex), cloth on both
        sides (house colour)."""
        def edge(s):
            top = z - 0.12 * length * s * s
            return u + length * s, top, top - width * (1 - s) ** 0.9
        out = []
        for i in range(k):
            (u0, t0, b0), (u1, t1, b1) = edge(i / k), edge((i + 1) / k)
            tags = ["cloth", "cloth" if i == k - 1 else None, "cloth", "cloth" if i == 0 else None]
            out.append(prism_uz(a, t, n, [(u0, b0), (u1, b1), (u1, t1), (u0, t0)], d - 0.08, d + 0.08, tags, "cloth", "cloth"))
        return out

    def banner_pole(self, a, t, n, u, height, width, length, pennant=True):
        """A free-standing slender gilt pole at u on (a, t) on a two-ring stone foot, a leaf finial
        at the top, a leaf banner facing n from a crossbar and a pennant flying from its head."""
        p = V((a.x + t.x * u, a.y + t.y * u, 0))
        out = [turned(p.x, p.y, [(1.4, 0.0), (1.4, 0.7), (1.0, 1.0), (0.8, 1.6)], ["stoneB", "coping", "trim"], 10,
                      cap0=("stoneB", False), cap1=("top", True)),
               turned(p.x, p.y, [(0.26, 1.5), (0.2, height)], ["gilt"], 8, cap0=("gilt", False), cap1=("gilt", True))]
        out += self.leaf_finial(p.x, p.y, height - 0.1, 2.4, 0.9)
        out += self.leaf_banner(a, t, n, u, height - 2.2, width, length, d=0.45, free=True)
        if pennant:
            out += self.pennant(a, t, n, u + 0.3, height - 0.3, length * 0.8, width * 0.22)
        return out
