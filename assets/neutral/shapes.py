"""The neutral shape vocabulary (Blender side): the wilderland wayside, built as EA's Inn is built.
Squared timber and pale logs, fieldstone laid dry, silvered shingles, a faded madder cloth, black
iron straps and brass lamps. Every piece returns closed solids (sagekit.blender.geometry.Solid) in
design coordinates, tagged with NeutralAtlas regions (assets/neutral/atlas.py).

    beam(p, q, r, tag)              a squared timber or bar between two points
    post(cx, cy, z0, z1, r)         an upright squared post (the pale post texture)
    stack(cx, cy, w, d, z0, z1)     a fieldstone chimney stack, its coping and two pots
    signboard(a, t, n, u, z, w, h)  EA's painted sign on a plank board, iron-banded, both faces
    gallows_sign(p, arm, ...)       a sign gallows: post, arm, brace, chains, the board, a lamp
    lantern(p, s)                   a brass-framed lamp hanging from p, glowing panes
    awning(a, t, n, u0, u1, ...)    a cloth canopy on timber brackets over a door
    lean_to(x, y0, y1, ...)         a shingled stable lean-to on posts against a wall
    barrel(cx, cy, z, r, h)         an iron-hooped barrel
    hearth(cx, cy, r)               a fieldstone fire ring, a spit on forked posts, a kettle on a crane
    log_stack(c, t, length, r)      a stack of split logs between stakes (rows of round logs)
    stall(c, t, w, d, h)            a market stall: four posts, a counter and a sloped cloth canopy
    platform(c, t, w, d, z, ...)    a squared-timber lookout platform on legs with a rail and a roof
    hull(x0, x1, y, z0, z1, ...)    a ship's frame building on a slipway: keel on blocks, ribs, stem,
                                    sternpost and the first strakes along the bottom
Sizes are for the RTS camera: a detail stands 1.5-4 units proud to read at the game's zoom.
"""
import math

from mathutils import Vector as V

from sagekit.blender.geometry import Z, box, loft, prism_uz

from assets.men.shapes import beam, rail, ring, turned


class NeutralShapes:
    Z, V = Z, V
    beam = staticmethod(beam)
    ring = staticmethod(ring)
    turned = staticmethod(turned)
    box = staticmethod(box)
    prism_uz = staticmethod(prism_uz)

    @staticmethod
    def post(cx, cy, z0, z1, r=0.7, tag="post|v"):
        return box(cx - r, cx + r, cy - r, cy + r, z0, z1, tags=tag, cap0=("post", False), cap1=("post", True))

    @staticmethod
    def stack(cx, cy, w, d, z0, z1, pots=2):
        """A fieldstone chimney stack w by d from z0 (buried in what it rises from) to z1: a
        coping slab proud all round, two clay pots on it."""
        out = [box(cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0, z1, "stoneA", ("stoneA", False), ("top", False)),
               box(cx - w / 2 - 0.7, cx + w / 2 + 0.7, cy - d / 2 - 0.7, cy + d / 2 + 0.7, z1, z1 + 1.3, "log|a",
                   ("log", True), ("top", True))]
        for i in range(pots):
            x = cx + (i - (pots - 1) / 2) * w * 0.42
            out.append(turned(x, cy, [(0.95, z1 + 1.2), (1.1, z1 + 2.6), (0.85, z1 + 3.4), (1.05, z1 + 3.8)],
                              ["planks", "planks", "brass"], 8, cap0=("planks", False), cap1=("iron", True)))
        return out

    @staticmethod
    def signboard(a, t, n, u, z, w, h, th=0.7):
        """The inn's sign: EA's painted board (the 'sign' region) on both faces of a plank w by h,
        bottom at z, an iron band across top and foot."""
        a, t, n = V(a), V(t), V(n)
        out = [prism_uz(a, t, n, [(u - w / 2, z), (u + w / 2, z), (u + w / 2, z + h), (u - w / 2, z + h)], -th / 2, th / 2,
                        ["planks"] * 4, "sign", "sign")]
        for zz in (z + 0.25, z + h - 0.25):
            out.append(prism_uz(a, t, n, [(u - w / 2 - 0.15, zz - 0.3), (u + w / 2 + 0.15, zz - 0.3), (u + w / 2 + 0.15, zz + 0.3),
                                          (u - w / 2 - 0.15, zz + 0.3)], -th / 2 - 0.12, th / 2 + 0.12, ["iron"] * 4, "iron", "iron"))
        return out

    def lantern(self, p, s=1.0, chain=1.5):
        """A brass-framed lamp hanging from p: a ring and chain, a pyramid cap, four glowing panes
        between corner posts, a foot."""
        p = V(p)
        top = p.z - chain
        out = [beam(p, p - Z * chain, 0.1, "iron")]
        out.append(turned(p.x, p.y, [(0.9 * s, top - 0.2 * s), (0.25 * s, top + 0.5 * s)], ["brass"], 4,
                          cap0=("brass", True), cap1=("brass", True), phase=math.pi / 4))
        zb = top - 2.1 * s
        out.append(box(p.x - 0.62 * s, p.x + 0.62 * s, p.y - 0.62 * s, p.y + 0.62 * s, zb + 0.3 * s, top - 0.2 * s,
                       "glow|v", ("glow", True), ("glow", True)))
        for ex in (-1, 1):
            for ey in (-1, 1):
                c = V((p.x + ex * 0.68 * s, p.y + ey * 0.68 * s, 0))
                out.append(box(c.x - 0.12 * s, c.x + 0.12 * s, c.y - 0.12 * s, c.y + 0.12 * s, zb + 0.2 * s, top - 0.15 * s,
                               "brass", ("brass", True), ("brass", True)))
        out.append(box(p.x - 0.82 * s, p.x + 0.82 * s, p.y - 0.82 * s, p.y + 0.82 * s, zb, zb + 0.32 * s, "brass",
                       ("brass", True), ("brass", True)))
        return out

    def gallows_sign(self, p, arm, height, reach, w, h, facing=(0, -1, 0), cap=True):
        """A sign gallows standing at p: a squared post `height` tall on a fieldstone footing, an arm
        `reach` long along `arm`, a brace under it, the board hung from it on two iron chains at
        mid-reach and a lantern at the arm's end. The board faces `facing`."""
        p, arm = V(p), V(arm).normalized()
        out = [box(p.x - 1.8, p.x + 1.8, p.y - 1.8, p.y + 1.8, -0.03, 1.6, "stoneA", ("stoneA", False), ("top", True)),
               self.post(p.x, p.y, 1.2, height, 0.75)]
        za = height - 2.2
        end = p + arm * reach
        out.append(beam(V((p.x, p.y, za)) - arm * 0.6, V((end.x, end.y, za)), 0.55, "beam|a"))
        out.append(beam(V((p.x, p.y, za - 6.0)), V((p.x, p.y, za)) + arm * 5.0, 0.4, "beam|a"))
        if cap:                                                     # a pointed cap (or a flat one: a finial goes there)
            out.append(beam(V((p.x, p.y, height)), V((p.x, p.y, height + 1.0)), 0.95, "post", 0.0))
        else:
            out.append(box(p.x - 0.95, p.x + 0.95, p.y - 0.95, p.y + 0.95, height - 0.6, height, "iron", ("iron", False), ("iron", True)))
        mid = p + arm * (reach * 0.45)
        t = arm
        n = V(facing).normalized()
        zt = za - 1.0 - h
        for e in (-1, 1):
            q = mid + t * e * (w / 2 - 0.6)
            out.append(beam(V((q.x, q.y, za - 0.5)), V((q.x, q.y, zt + h)), 0.1, "iron"))
        a = V((mid.x, mid.y, 0))
        out += self.signboard(a, t, n, 0.0, zt, w, h)
        out += self.lantern(V((end.x, end.y, za - 0.5)) + arm * -0.6, 1.1)
        return out

    @staticmethod
    def awning(a, t, n, u0, u1, z_wall, z_edge, depth, brackets=3):
        """A cloth canopy over a door on face (a, t, n): from z_wall at the face out `depth` to
        z_edge, a timber edge rail, and squared brackets back to the wall under it."""
        a, t, n = V(a), V(t), V(n)
        P = lambda u, d, z: a + t * u + n * d + Z * z                        # noqa: E731
        th = 0.35
        lo = [P(u0, 0.2, z_wall - th), P(u1, 0.2, z_wall - th), P(u1, depth, z_edge - th), P(u0, depth, z_edge - th)]
        hi = [P(u0, 0.2, z_wall), P(u1, 0.2, z_wall), P(u1, depth, z_edge), P(u0, depth, z_edge)]
        out = [loft([lo, hi], [["cloth", "cloth", "cloth", "cloth"]], cap0=("cloth", True), cap1=("cloth", True))]
        out.append(beam(P(u0 - 0.6, depth, z_edge - 0.6), P(u1 + 0.6, depth, z_edge - 0.6), 0.45, "beam|a"))
        for i in range(brackets):
            u = u0 + 0.8 + (u1 - u0 - 1.6) * i / max(brackets - 1, 1)
            out.append(beam(P(u, -0.3, z_edge - 4.0), P(u, depth - 0.2, z_edge - 0.8), 0.32, "beam|a"))
        return out

    def lean_to(self, x_wall, x_out, y0, y1, z_wall, z_eave, posts=4, stalls=3):
        """A stable lean-to against a wall at x_wall reaching out to x_out (either side), y0..y1:
        squared posts on stone pads, a log plate along the eave, a shingle roof falling from z_wall
        to z_eave, plank stall partitions and a hay rack."""
        s = 1 if x_out > x_wall else -1
        out = []
        for i in range(posts):
            y = y0 + 0.8 + (y1 - y0 - 1.6) * i / (posts - 1)
            out.append(box(x_out - 1.1, x_out + 1.1, y - 1.1, y + 1.1, -0.03, 0.8, "stoneA", ("stoneA", False), ("top", True)))
            out.append(self.post(x_out, y, 0.6, z_eave - 0.6, 0.55))
        out.append(beam(V((x_out, y0 - 0.6, z_eave - 0.3)), V((x_out, y1 + 0.6, z_eave - 0.3)), 0.6, "log|a"))
        lo, hi = (x_wall - s * 0.2, z_wall), (x_out + s * 1.4, z_eave - 0.4)
        roof = [[V((lo[0], y0 - 1.2, lo[1] - 0.6)), V((hi[0], y0 - 1.2, hi[1] - 0.6)),
                 V((hi[0], y1 + 1.2, hi[1] - 0.6)), V((lo[0], y1 + 1.2, lo[1] - 0.6))],
                [V((lo[0], y0 - 1.2, lo[1])), V((hi[0], y0 - 1.2, hi[1])),
                 V((hi[0], y1 + 1.2, hi[1])), V((lo[0], y1 + 1.2, lo[1]))]]
        out.append(loft(roof, [["beam", "beam", "beam", None]], cap0=("planks", True), cap1=("shingle", True)))
        for i in range(1, stalls):
            y = y0 + (y1 - y0) * i / stalls
            out.append(box(min(x_wall, x_out + s * 2.5), max(x_wall, x_out + s * 2.5), y - 0.3, y + 0.3, 0.0, 6.5,
                           "planks|v", ("planks", False), ("beam", True)))
        xr = x_wall + s * 1.0
        out.append(beam(V((xr, y0 + 1.5, 7.5)), V((xr, y1 - 1.5, 7.5)), 0.3, "beam|a"))
        for i in range(9):
            y = y0 + 2.0 + (y1 - y0 - 4.0) * i / 8
            out.append(beam(V((x_wall + s * 0.2, y, 5.0)), V((xr, y, 7.5)), 0.12, "beam|a"))
        return out

    @staticmethod
    def barrel(cx, cy, z=0.0, r=1.5, h=3.4):
        out = [turned(cx, cy, [(r * 0.86, z), (r, z + h * 0.5), (r * 0.86, z + h)], ["planks|v", "planks|v"], 10,
                      cap0=("planks", False), cap1=("planks", True))]
        for zz in (0.18, 0.82):
            rr = r * (0.86 + 0.14 * (1 - abs(zz - 0.5) * 2)) + 0.08
            out.append(turned(cx, cy, [(rr, z + h * zz - 0.22), (rr, z + h * zz + 0.22)], ["iron"], 10,
                              cap0=("iron", True), cap1=("iron", True)))
        return out

    def hearth(self, cx, cy, r=3.2, kettle=True):
        """An open hearth in the yard: a ring of fieldstones round a low ash bed, a spit on two
        forked posts across it, and a kettle hung from a crane. Its fire is EA's (fire_points)."""
        out = []
        k = 9
        for i in range(k):
            a = 2 * math.pi * i / k
            c = V((cx + r * math.cos(a), cy + r * math.sin(a), 0))
            out.append(box(c.x - 0.8, c.x + 0.8, c.y - 0.8, c.y + 0.8, -0.03, 1.0 + 0.25 * (i % 2), "stoneA",
                           ("stoneA", False), ("top", True)))
        out.append(turned(cx, cy, [(r - 0.6, 0.0), (r - 0.9, 0.35)], ["log"], 9, cap0=("log", False), cap1=("iron", True)))
        for e in (-1, 1):
            x = cx + e * (r + 1.4)
            out.append(beam(V((x, cy, 0)), V((x, cy, 4.2)), 0.28, "post|v"))
            out.append(beam(V((x, cy, 3.6)), V((x - 0.7, cy, 4.8)), 0.16, "post"))
            out.append(beam(V((x, cy, 3.6)), V((x + 0.7, cy, 4.8)), 0.16, "post"))
        out.append(beam(V((cx - r - 2.2, cy, 4.2)), V((cx + r + 2.2, cy, 4.2)), 0.16, "iron"))
        if kettle:
            out.append(turned(cx, cy + 0.0, [(0.5, 1.6), (1.15, 2.0), (1.2, 2.8), (0.95, 3.25)], ["iron", "iron", "iron"],
                              8, cap0=("iron", True), cap1=("iron", True)))
        return out

    def log_stack(self, c, t, length, r, rows=3, z=0.0):
        """Rows of round logs `length` long along t, a pyramid of them, held by two stakes a side."""
        c, t = V((c[0], c[1], 0)), V((t[0], t[1], 0)).normalized()
        n = V((-t.y, t.x, 0))
        out = []
        for row in range(rows):
            k = rows - row + 1
            for i in range(k):
                off = (i - (k - 1) / 2) * 2 * r
                p = c + n * off + Z * (z + r + row * 1.7 * r)
                out.append(turned_along(p - t * length / 2, p + t * length / 2, r * (0.9 + 0.1 * ((i + row) % 2))))
        for e in (-1, 1):
            for f in (-0.35, 0.35):
                b = c + n * e * ((rows + 1) * r + 0.3) + t * f * length
                out.append(beam(b + Z * z, b + Z * (z + rows * 1.7 * r + 0.8), 0.28, "post", 0.0))
        return out

    def stall(self, c, t, w, d, h, cloth="cloth"):
        """A market stall w along t by d deep: four squared posts, a plank counter at 3.4, and a
        cloth canopy sloping from h at the back to h - 2 over the front."""
        c, t = V((c[0], c[1], 0)), V((t[0], t[1], 0)).normalized()
        n = V((-t.y, t.x, 0))
        out = []
        for eu in (-1, 1):
            for ed in (-1, 1):
                p = c + t * eu * w / 2 + n * ed * d / 2
                out.append(self.post(p.x, p.y, 0.0, h - (1.6 if ed > 0 else 0.0) + 0.3, 0.32))
        P = lambda u, dd, zz: c + t * u + n * dd + Z * zz       # noqa: E731
        out.append(loft([[P(-w / 2 + 0.2, d / 2 - 0.4, 2.9), P(w / 2 - 0.2, d / 2 - 0.4, 2.9),
                          P(w / 2 - 0.2, d / 2 + 0.6, 2.9), P(-w / 2 + 0.2, d / 2 + 0.6, 2.9)],
                         [P(-w / 2 + 0.2, d / 2 - 0.4, 3.4), P(w / 2 - 0.2, d / 2 - 0.4, 3.4),
                          P(w / 2 - 0.2, d / 2 + 0.6, 3.4), P(-w / 2 + 0.2, d / 2 + 0.6, 3.4)]],
                        [["planks"] * 4], cap0=("planks", True), cap1=("planks", True)))
        lo = [P(-w / 2 - 0.6, -d / 2 - 0.4, h), P(w / 2 + 0.6, -d / 2 - 0.4, h), P(w / 2 + 0.6, d / 2 + 1.2, h - 2.0),
              P(-w / 2 - 0.6, d / 2 + 1.2, h - 2.0)]
        out.append(loft([lo, [q + Z * 0.3 for q in lo]], [[cloth] * 4], cap0=(cloth, True), cap1=(cloth, True)))
        return out

    def platform(self, c, t, w, d, z, legs=True, roof=True):
        """A squared-timber lookout platform w by d at z: legs to the ground (or none, on a wall),
        a plank floor, a rail, and a shingled pent roof on four posts."""
        c, t = V((c[0], c[1], 0)), V((t[0], t[1], 0)).normalized()
        n = V((-t.y, t.x, 0))
        P = lambda u, dd, zz: c + t * u + n * dd + Z * zz       # noqa: E731
        out = []
        ring = lambda zz: [P(-w / 2, -d / 2, zz), P(w / 2, -d / 2, zz), P(w / 2, d / 2, zz), P(-w / 2, d / 2, zz)]   # noqa: E731
        out.append(loft([ring(z - 0.7), ring(z)], [["log|a"] * 4], cap0=("planks", True), cap1=("planks", True)))
        for eu in (-1, 1):
            for ed in (-1, 1):
                p = P(eu * (w / 2 - 0.5), ed * (d / 2 - 0.5), 0)
                if legs:
                    out.append(beam(V((p.x, p.y, 0)), V((p.x, p.y, z - 0.6)), 0.55, "post|v"))
                out.append(beam(V((p.x, p.y, z)), V((p.x, p.y, z + 6.5)), 0.4, "post|v"))
        for zz in (z + 1.6, z + 3.0):
            for a, b in ((P(-w / 2 + 0.5, -d / 2 + 0.5, zz), P(w / 2 - 0.5, -d / 2 + 0.5, zz)),
                         (P(w / 2 - 0.5, -d / 2 + 0.5, zz), P(w / 2 - 0.5, d / 2 - 0.5, zz)),
                         (P(w / 2 - 0.5, d / 2 - 0.5, zz), P(-w / 2 + 0.5, d / 2 - 0.5, zz)),
                         (P(-w / 2 + 0.5, d / 2 - 0.5, zz), P(-w / 2 + 0.5, -d / 2 + 0.5, zz))):
                out.append(beam(a, b, 0.22, "beam|a"))
        if roof:
            lo = [P(-w / 2 - 1.0, -d / 2 - 1.0, z + 7.6), P(w / 2 + 1.0, -d / 2 - 1.0, z + 7.6),
                  P(w / 2 + 1.0, d / 2 + 1.0, z + 6.0), P(-w / 2 - 1.0, d / 2 + 1.0, z + 6.0)]
            out.append(loft([lo, [q + Z * 0.5 for q in lo]], [["beam"] * 4], cap0=("planks", True), cap1=("shingle", True)))
        return out


def turned_along(p, q, r, k=8, tag="log|a"):
    """A round log from p to q (end grain capped)."""
    d = (q - p).normalized()
    u = d.cross(Z)
    u = u.normalized() if u.length > 1e-3 else V((1, 0, 0))
    v = d.cross(u).normalized()
    rings = [[c + (u * math.cos(2 * math.pi * i / k) + v * math.sin(2 * math.pi * i / k)) * r for i in range(k)] for c in (p, q)]
    return loft(rings, [tag], cap0=("planks", True), cap1=("planks", True))


def hull(x0, x1, y, z0, z1, beam_=9.0, depth=11.0, ribs=8, planked=0.45):
    """A ship in frame along x from its stern at x0 to its bow at x1, the keel on blocks from z0
    (stern) to z1 (bow): ribs curving out to `beam_` across and `depth` up, the stem rising at the
    bow, the sternpost at the stern, strakes planked over the first `planked` of the length."""
    z = lambda x: z0 + (z1 - z0) * (x - x0) / (x1 - x0)          # noqa: E731
    out = []
    for i in range(4):                                          # keel blocks
        x = x0 + (x1 - x0) * (i + 0.5) / 4
        out.append(box(x - 1.2, x + 1.2, y - 1.4, y + 1.4, z(x) - 1.6, z(x) + 0.2, "log|a", ("log", False), ("planks", True)))
    out.append(beam(V((x0, y, z(x0) + 0.7)), V((x1, y, z(x1) + 0.7)), 0.7, "beam|a"))
    out.append(rail([V((x1 - 1.0, y, z(x1) + 0.7)), V((x1 + 2.2, y, z(x1) + depth * 0.5)), V((x1 + 3.4, y, z(x1) + depth + 4.0))],
                    0.6, "beam|a"))
    out.append(beam(V((x0, y, z(x0) + 0.7)), V((x0 - 1.4, y, z(x0) + depth + 2.5)), 0.6, "beam|a"))
    for i in range(ribs):
        f = (i + 0.5) / ribs
        x = x0 + (x1 - x0) * f
        w = beam_ * (0.55 + 0.45 * math.sin(math.pi * min(1.0, 0.25 + f * 0.9)))
        zk = z(x) + 0.7
        for e in (-1, 1):
            pts = [V((x, y + e * 0.4, zk)), V((x, y + e * w * 0.55, zk + depth * 0.12)), V((x, y + e * w * 0.9, zk + depth * 0.45)),
                   V((x, y + e * w, zk + depth))]
            out.append(rail(pts, 0.32, "beam"))
    for e in (-1, 1):                                           # the first strakes and the gunwale
        for k, (fw, fz) in enumerate(((0.62, 0.16), (0.88, 0.42))):
            xs = (x0 + 1.0, x0 + (x1 - x0) * planked)
            pts = [V((x, y + e * beam_ * fw * (0.55 + 0.45 * math.sin(math.pi * min(1.0, 0.25 + (x - x0) / (x1 - x0) * 0.9))),
                      z(x) + 0.7 + depth * fz)) for x in (xs[0], (xs[0] + xs[1]) / 2, xs[1])]
            out.append(rail(pts, 0.55, "planks|a"))
        out.append(rail([V((x0 + 0.5, y + e * beam_ * 0.62, z(x0) + 0.7 + depth)), V(((x0 + x1) / 2, y + e * beam_, z((x0 + x1) / 2) + 0.7 + depth)),
                         V((x1 - 2.0, y + e * beam_ * 0.6, z(x1) + 0.7 + depth))], 0.4, "beam"))
    return out
