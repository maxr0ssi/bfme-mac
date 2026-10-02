"""Primitives for Create-a-Hero gear, on sagekit.units.mesh.Mesh (sagekit's mesh writer).

A Gear is one new hidden skinned sub-object. Points are given in the design space (CHDW_TM_U_SKN's
rest space: +X front, +Y the dwarf's left, +Z up) and `place` maps them into the model being built;
each vertex is stored in its bone's rest space (Mesh does that), so a piece rides its bone in every
animation. UVs address one tile of a sheet of 8 x 4 tiles of 256 px (paint.py); `remap` swaps tiles
(a colour variant draws the same geometry from other tiles).

`lod` trims a piece toward EA's budgets: fewer sides on round sections, fewer sweep samples,
cheaper rivets; open sheets seen from both sides reuse their vertices (reversed triangles).
"""
import math

from sagekit.formats import w3dpose as P
from sagekit.formats.w3d import NORMALS, STAGE_TEXCOORDS, VERTICES
from sagekit.units.mesh import Mesh


# ------------------------------------------------------------------ vectors and fits
def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def mul(a, s):
    return [x * s for x in a]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def norm(a):
    n = math.sqrt(sum(x * x for x in a)) or 1.0
    return [x / n for x in a]


def _solve(A, b):
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def affine_fit(src, dst):
    """3 x 4 matrix X with dst ~= X [src, 1] (least squares) and its largest error."""
    A = [list(p) + [1.0] for p in src]
    AtA = [[sum(a[i] * a[j] for a in A) for j in range(4)] for i in range(4)]
    X = [_solve(AtA, [sum(a[i] * d[k] for a, d in zip(A, dst)) for i in range(4)]) for k in range(3)]
    err = max(abs(sum(x * a for x, a in zip(X[k], A[i])) - dst[i][k]) for i in range(len(A)) for k in range(3))
    return X, err


def affine(X, p):
    q = list(p) + [1.0]
    return tuple(sum(x * a for x, a in zip(X[k], q)) for k in range(3))


def tile_uv(tag, u, v):
    """(u, v) inside tile `tag` (row-major, 8 x 4) of a 2048 x 1024 sheet, inset 3 %."""
    u, v = min(max(u, 0), 1), min(max(v, 0), 1)
    return (((tag % 8) + .03 + .94 * u) / 8, 1 - ((tag // 8) + .97 - .94 * v) / 4)


def _normals(rows, wrap, fallback):
    """Grid normals by central differences: (along a row) x (across rows)."""
    R, C = len(rows), len(rows[0])
    out = []
    for k in range(R):
        nr = []
        for i in range(C):
            if wrap:
                a, b = rows[k][(i - 1) % (C - 1)], rows[k][(i + 1) % (C - 1)]
            else:
                a, b = rows[k][max(i - 1, 0)], rows[k][min(i + 1, C - 1)]
            c, d = rows[max(k - 1, 0)][i], rows[min(k + 1, R - 1)][i]
            n = cross(sub(b, a), sub(d, c))
            if math.sqrt(sum(x * x for x in n)) < 1e-9:
                n = fallback(k, i)
            nr.append(norm(n))
        out.append(nr)
    return out


class Gear(Mesh):
    def __init__(self, original, skeleton, names, place=lambda p: tuple(p), bone_map=None, remap=None, lod=1.0):
        super().__init__(original, skeleton, keep=False, names=names, bone="B_HEAD", skin=True)
        self.place, self.bone_map, self.remap, self.lod = place, bone_map or {}, remap or {}, lod
        self.pieces = 0

    def uv_for(self, tag, u, v):
        return tile_uv(self.remap.get(tag, tag), u, v)

    def _b(self, bone):
        return self._bone(self.bone_map.get(bone, bone))

    def _sides(self, sides, keep=8):
        """Fewer sides at a lower lod; faceted forms of `keep` or fewer sides stay as drawn."""
        return sides if sides <= keep else max(keep, int(round(sides * self.lod)))

    # ------------------------------------------------------------------ writers
    def quad_strip(self, rows, normals, tag, bone, uvs, double=False):
        b = self._b(bone)
        transform = P.invert(self.skeleton.rest[b])
        idx = []
        for row, nrow, urow in zip(rows, normals, uvs):
            ir = []
            for p, n, (u, v) in zip(row, nrow, urow):
                q = self.place(p)
                nn = norm(sub(self.place(add(p, n)), q))
                ir.append(len(self.verts))
                self.verts.append((0, [(0, 1)], transform, b,
                                   {VERTICES: tuple(q), NORMALS: tuple(nn), STAGE_TEXCOORDS: self.uv_for(tag, u, v)}))
            idx.append(ir)
        surf = self.original.surface[0]
        for r0, r1 in zip(idx, idx[1:]):
            for i in range(len(r0) - 1):
                a, b2, c, d = r0[i], r0[i + 1], r1[i + 1], r1[i]
                self.tris += [((a, b2, c), surf), ((a, c, d), surf)]
                if double:          # the back side on the same vertices (an open sheet)
                    self.tris += [((a, c, b2), surf), ((a, d, c), surf)]
        self.pieces += 1

    def flat(self, pts, tag, bone, uvs=None):
        a, b, c = pts[:3]
        n = norm(cross(sub(b, a), sub(c, a)))
        uv = uvs or [(.5 + .5 * math.cos(2 * math.pi * i / len(pts)), .5 + .5 * math.sin(2 * math.pi * i / len(pts)))
                     for i in range(len(pts))]
        bb = self._b(bone)
        transform = P.invert(self.skeleton.rest[bb])
        off = len(self.verts)
        for p, (u, v) in zip(pts, uv):
            q = self.place(p)
            nn = norm(sub(self.place(add(p, n)), q))
            self.verts.append((0, [(0, 1)], transform, bb,
                               {VERTICES: tuple(q), NORMALS: tuple(nn), STAGE_TEXCOORDS: self.uv_for(tag, u, v)}))
        surf = self.original.surface[0]
        self.tris += [((off, off + i, off + i + 1), surf) for i in range(1, len(pts) - 1)]

    def grid(self, rows, uvs, tag, bone, wrap=False, fallback=None, double=False):
        nrm = _normals(rows, wrap, fallback or (lambda k, i: [0, 0, 1]))
        self.quad_strip(rows, nrm, tag, bone, uvs, double=double)

    # ------------------------------------------------------------------ surfaces
    def shell(self, frame, profile, tag, bone, sides=24, arc=(0, 2 * math.pi), rim=None, double=False, bump=None,
              planar=None, keep=8):
        """Elliptic surface of revolution in frame (origin, X, Y, Z): profile [(rx, ry, z)] bottom to
        top. rim(t) offsets the lowest ring's z; bump(t, k) adds radius (folds, facets, scallops);
        planar=R maps UVs flat across X/Y over radius R (a shield face)."""
        o, X, Y, Z = frame
        a0, a1 = arc
        full = abs(a1 - a0 - 2 * math.pi) < 1e-9
        n = self._sides(sides, keep)
        th = [a0 + (a1 - a0) * i / n for i in range(n + 1)]
        rows, uvs = [], []
        K = len(profile)
        for k, (rx, ry, z) in enumerate(profile):
            row, urow = [], []
            for i, t in enumerate(th):
                b = bump(t, k) if bump else 0.0
                zz = z + (rim(t) if rim and k == 0 else 0)
                row.append(add(add(add(o, mul(X, (rx + b) * math.cos(t))), mul(Y, (ry + b) * math.sin(t))), mul(Z, zz)))
                urow.append((.5 + .5 * (rx + b) * math.cos(t) / planar, .5 + .5 * (ry + b) * math.sin(t) / planar)
                            if planar else (i / n, k / max(1, K - 1)))
            rows.append(row)
            uvs.append(urow)

        def fb(k, i):
            d = sub(rows[k][i], o)
            radial = sub(d, mul(Z, dot(d, Z)))
            return Z if k == K - 1 or math.sqrt(dot(radial, radial)) < 1e-6 else radial
        self.grid(rows, uvs, tag, bone, wrap=full, fallback=fb, double=double)
        return rows

    def sweep(self, path, radii, tag, bone, sides=8, squash=1.0, up=None, cap=True):
        """A smooth tube along a polyline (parallel-transported frame), radius radii[i], squash
        flattening its second axis; a closed path (first point == last) has no caps."""
        closed = math.dist(path[0], path[-1]) < 1e-6
        stride = 1 if self.lod >= .8 else 2 if self.lod >= .5 else 3
        if stride > 1 and len(path) > 4:
            keep = list(range(0, len(path), stride))
            if keep[-1] != len(path) - 1:
                keep.append(len(path) - 1)
            path, radii = [path[i] for i in keep], [radii[i] for i in keep]
        sides = self._sides(sides, keep=4) if sides > 4 else sides
        if self.lod < .5 and max(radii) < .12:      # a thin trim: three sides read the same from afar
            sides = 3
        rows, nrows, uvs, prev = [], [], [], None
        L = [0.0]
        for a, b in zip(path, path[1:]):
            L.append(L[-1] + math.dist(a, b))
        for i, p in enumerate(path):
            t = norm(sub(path[min(i + 1, len(path) - 1)], path[max(i - 1, 0)]))
            if prev is None:
                ref = up or ([0, 0, 1] if abs(t[2]) < .9 else [1, 0, 0])
                u = norm(cross(t, ref))
            else:
                u = norm(sub(prev, mul(t, dot(prev, t))))
            v = cross(t, u)
            prev = u
            row, nrow, urow = [], [], []
            for k in range(sides + 1):
                a = 2 * math.pi * k / sides
                d = add(mul(u, math.cos(a)), mul(v, math.sin(a) * squash))
                row.append(add(p, mul(d, radii[i])))
                nrow.append(norm(add(mul(u, math.cos(a) * squash), mul(v, math.sin(a)))))
                urow.append((k / sides, L[i] / (L[-1] or 1)))
            rows.append(row)
            nrows.append(nrow)
            uvs.append(urow)
        self.quad_strip(rows, nrows, tag, bone, uvs)
        if cap and not closed:
            self.flat(rows[0][:-1][::-1], tag, bone)
            self.flat(rows[-1][:-1], tag, bone)

    def tube(self, a, b, r, tag, bone, sides=10, r1=None):
        self.sweep([list(a), list(b)], [r, r if r1 is None else r1], tag, bone, sides=sides)

    def stud(self, centre, normal, r, tag, bone, h=None, sides=6):
        """A rivet or boss: a faceted cap on a surface (four sides at a low lod when small)."""
        nrm = norm(normal)
        h = h if h is not None else r * .6
        if self.lod < .6 and r < .09 or self.lod < .45 and r < .13:   # rivets nobody sees from the RTS camera
            return
        if self.lod < .8 and r < .15:
            sides = 4
        up = [0, 0, 1] if abs(nrm[2]) < .9 else [1, 0, 0]
        X = norm(cross(nrm, up))
        Y = cross(nrm, X)
        prof = [(r, r, 0), (r * .8, r * .8, h * .7), (r * .3, r * .3, h)] if self.lod >= .8 else [(r, r, 0), (r * .45, r * .45, h)]
        self.shell((list(centre), X, Y, nrm), prof, tag, bone, sides=sides, keep=sides)
        top = prof[-1][0]
        self.flat([add(centre, add(mul(nrm, h), add(mul(X, top * math.cos(2 * math.pi * i / sides)),
                                                       mul(Y, top * math.sin(2 * math.pi * i / sides)))))
                   for i in range(sides)], tag, bone)

    def ribbon(self, lower, upper, tag, bone, edge_r=None, edge_tag=None):
        """A thin standing plate between two polylines (a crest fin), seen from both sides."""
        uvs = [[(i / (len(lower) - 1), k) for i in range(len(lower))] for k in (0, 1)]
        self.grid([lower, upper], uvs, tag, bone, double=True)
        if edge_r:
            self.sweep(upper, [edge_r] * len(upper), edge_tag if edge_tag is not None else tag, bone, sides=6)

    def slab(self, outline, thick, normal, tag, bone, bevel=.06):
        """A plate from a convex outline, `thick` along `normal`, its front face bevelled."""
        nrm = norm(normal)
        newell = [0.0, 0.0, 0.0]
        for i, p in enumerate(outline):
            newell = add(newell, cross(p, outline[(i + 1) % len(outline)]))
        if dot(newell, nrm) < 0:
            outline = outline[::-1]
        if self.lod < .5 and thick <= .16:          # trimmed: a thin plate is one two-sided face
            n0, t0 = len(self.verts), len(self.tris)
            self.flat(outline, tag, bone)
            self.tris += [((a, c, b), s) for (a, b, c), s in self.tris[t0:]]
            return
        c = [sum(p[k] for p in outline) / len(outline) for k in range(3)]
        back = [add(p, mul(nrm, -thick / 2)) for p in outline]
        front = [add(add(p, mul(nrm, thick / 2)), mul(norm(sub(c, p)), bevel)) for p in outline]
        mid = [add(p, mul(nrm, thick / 2 - bevel * .5)) for p in outline]
        m = len(outline)
        for ring0, ring1 in (((back, mid), (mid, front)) if self.lod >= .8 else ((back, front),)):
            for i in range(m):
                j = (i + 1) % m
                self.flat([ring0[i], ring0[j], ring1[j], ring1[i]], tag, bone, [(0, 0), (1, 0), (1, 1), (0, 1)])
        lo = [min(p[k] for p in outline) for k in range(3)]
        hi = [max(p[k] for p in outline) for k in range(3)]
        span = [max(h - l, 1e-6) for l, h in zip(lo, hi)]
        ax = sorted(range(3), key=lambda k: -span[k])[:2]
        uv = lambda pts: [((p[ax[0]] - lo[ax[0]]) / span[ax[0]], (p[ax[1]] - lo[ax[1]]) / span[ax[1]]) for p in pts]
        self.flat(front, tag, bone, uv(front))
        self.flat(back[::-1], tag, bone, uv(back[::-1]))

    def loft(self, sections, tag, bone, uv=None, cap=True):
        """A closed body through rings `sections` (same point count each)."""
        n = len(sections[0])
        rows = [s + [s[0]] for s in sections]
        uvs = [[uv(k, i % n) if uv else (i / n, k / max(1, len(sections) - 1)) for i in range(n + 1)]
               for k in range(len(sections))]
        self.grid(rows, uvs, tag, bone, wrap=True)
        if cap:
            self.flat(sections[0][::-1], tag, bone)
            self.flat(sections[-1], tag, bone)

    def blade(self, origin, along, out, side, lo, hi, s_max, thick, tag, bone, steps=(10, 12), edge=.03, bulge=None):
        """A plate in the (along, out) plane: for s in 0..s_max it spans along in [lo(s), hi(s)],
        thick(s) across `side` (= along x out), keen at s_max; bulge(t) curves the edge. Planar UVs."""
        S, T = steps
        if self.lod < .8:
            S, T = max(6, S * 2 // 3), max(6, T * 2 // 3)
        tmin = min(min(lo(s_max * j / S) for j in range(S + 1)), 0)
        tmax = max(hi(s_max * j / S) for j in range(S + 1))
        P_ = lambda s, t, w: add(add(add(origin, mul(along, t)), mul(out, s + (bulge(t) * s / s_max if bulge else 0))),
                                 mul(side, w))
        uvf = lambda s, t: ((t - tmin) / (tmax - tmin), s / s_max)
        for w_sign in (1, -1):
            rows, uvs = [], []
            for j in range(S + 1):
                s = s_max * j / S
                w = max(thick(s) / 2, edge / 2) * w_sign
                ts = [lo(s) + (hi(s) - lo(s)) * i / T for i in range(T + 1)]
                ts = ts if w_sign > 0 else ts[::-1]
                rows.append([P_(s, t, w) for t in ts])
                uvs.append([uvf(s, t) for t in ts])
            self.grid(rows, uvs, tag, bone)
        outline = [(s_max * j / S, lo(s_max * j / S)) for j in range(S + 1)] + \
                  [(s_max * j / S, hi(s_max * j / S)) for j in range(S, -1, -1)]
        rows = [[P_(s, t, max(thick(s) / 2, edge / 2) * w) for s, t in outline] for w in (-1, 1)]
        self.grid(rows, [[uvf(s, t) for s, t in outline] for _ in (-1, 1)], tag, bone, double=True)
