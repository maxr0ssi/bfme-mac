"""Our body cut into EA's pieces (the lifecycle step's Blender side, sagekit/blender/lifecycle.py):
which of our faces go to which piece and bone, and which EA broke away. Our faces lying on EA's
healthy surface (EA's own faces, kept in our body) take EA's state pieces' exact shapes there; the
solids we added go whole to the piece most of them hangs on; anything else is cut straight."""
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from ..formats import w3dpose as P

CUT = ("cut",)


def tree(V, T):
    return BVHTree.FromPolygons([tuple(map(float, v)) for v in V], [tuple(map(int, t)) for t in T], all_triangles=True)


def nearest(bvh, pts):
    """(locations, face indices, distances) of the nearest surface points."""
    loc, idx, dist = np.zeros((len(pts), 3)), np.full(len(pts), -1), np.full(len(pts), np.inf)
    for i, p in enumerate(pts):
        r = bvh.find_nearest(Vector(p))
        if r[0] is not None:
            loc[i], idx[i], dist[i] = r[0], r[2], r[3]
    return loc, idx, dist


def face_frame(V, T):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.cross(b - a, c - a)
    area = np.linalg.norm(n, axis=1) / 2
    return (a + b + c) / 3, n / np.maximum(2 * area, 1e-12)[:, None], area


class Cutter:
    """The cutting half of lifecycle.Build (it provides S, info, ours, s, pose, classify...)."""

    def at(self, f, bary):
        """Where our face f is sampled for its class: a hair inside it (0.5% towards its centre),
        so a corner or edge lying on a boundary between EA's pieces is judged from its own face."""
        Vo, To = self.ours["V"], self.ours["T"]
        return (0.995 * np.asarray(bary) + 0.005 / 3) @ Vo[To[f]]

    def solids(self):
        """(our faces on EA's healthy surface, [(face, corners, class, placed corners)] for the rest).
        What we added to EA's body (a turret, a parapet) is a solid of its own: it goes whole, with
        the class most of its area has, so no sliver or half-open turret is left behind; a solid
        larger than `solid` units whose area is split more evenly goes face by face (whole faces).
        Each corner moves as EA's state moved the surface at its anchor (EA bends its rubble)."""
        Vo, To = self.ours["V"], self.ours["T"]
        c, _, area = face_frame(Vo, To)
        inset = np.array([self.at(f, np.eye(3)[k]) for f in range(len(To)) for k in range(3)])
        _, _, d = nearest(self.ea_tree, inset)
        on = d.reshape(-1, 3).max(1) <= 0.05
        key = {}
        weld = np.array([key.setdefault(tuple(np.round(v, 3)), len(key)) for v in Vo])
        parent = list(range(len(key)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for f in np.nonzero(~on)[0]:
            a, b, cc = (find(weld[v]) for v in To[f])
            parent[b] = a
            parent[find(cc)] = a
        extra = np.nonzero(~on)[0]
        cls = self.classify([c[f] for f in extra])
        groups = {}
        for f, k in zip(extra, cls):
            groups.setdefault(find(weld[To[f][0]]), []).append((f, k))
        used = sorted({int(v) for f in extra for v in To[f]})
        shift = dict(zip(used, self.displacement([Vo[v] for v in used])))      # each corner moves with
        at = {f: Vo[To[f]] + np.array([shift[int(v)] for v in To[f]]) for f in extra}    # its anchor
        out, whole = [], 0
        for faces in groups.values():
            votes = {}
            for f, k in faces:
                votes[k] = votes.get(k, 0.0) + area[f]
            kept = {k: v for k, v in votes.items() if k != CUT}
            if not kept or votes.get(CUT, 0.0) >= self.s["cut"] * sum(votes.values()):
                best = CUT                          # too much of it where EA's state has nothing
            else:
                best = max(kept, key=kept.get)
            pts = Vo[To[[f for f, _ in faces]].ravel()]
            small = self.s["solid"] is None or np.linalg.norm(pts.max(0) - pts.min(0)) <= self.s["solid"]
            if small or votes.get(best, 0.0) >= 0.6 * sum(votes.values()):
                out += [(f, np.eye(3), best, at[f]) for f, _ in faces]
                whole += 1
                if best != CUT:
                    caps = self.caps([f for f, _ in faces], weld, at)
                    out += [(-1, None, best, tri) for tri in caps]
                    self.capped = getattr(self, "capped", 0) + len(caps)
            else:                                   # face by face: each piece's part is closed
                out += [(f, np.eye(3), k, at[f]) for f, k in faces]     # where the others were
                parts = {}
                for f, k in faces:
                    parts.setdefault(k, []).append(f)
                for k, part in parts.items():
                    if k != CUT and self.s["seams"]:
                        caps = self.caps(part, weld, at, [f for f, j in faces if j != k])
                        out += [(-1, None, k, tri) for tri in caps]
                        self.capped = getattr(self, "capped", 0) + len(caps)
        self.stats = dict(surface=int(on.sum()), solids=len(groups), whole=whole, caps=getattr(self, "capped", 0),
                          rims=dict(getattr(self, "rimstat", {})))
        self.rimstat = {}
        self.capped = 0
        return [int(f) for f in np.nonzero(on)[0]], out

    def caps(self, faces, weld, at, rest=()):
        """Triangles closing a solid's open rims (the faces a design leaves out where the solid sits
        on the wall): hidden while it stands there, they keep its inside from showing once the
        pieces part. Each rim is triangulated in its plane (ear clipping) and kept only when it
        lies on EA's body (a doorway's does not), wound to face out of the solid. -> [3x3].
        rest: the solid's faces that went elsewhere (a solid split between pieces, or partly cut):
        a rim running along one of their edges is a seam the split opened; where a plane does not
        fit it (a seam winding round the solid), a fan from its centre. A seam's cap goes both ways
        (which way is out depends on how the seam winds). Every cap triangle must lie inside our
        body as it stands (inside(): a recess's or an arch's opening is not), so none shows then."""
        To = self.ours["T"]
        seam = {(int(weld[To[f][(k + 1) % 3]]), int(weld[To[f][k]])) for f in rest for k in range(3)}
        if not hasattr(self, "rimstat"):
            self.rimstat = {}
        where, home, edges = {}, {}, {}
        for f in faces:
            for k in range(3):
                a, b = int(weld[To[f][k]]), int(weld[To[f][(k + 1) % 3]])
                where[a], where[b] = at[f][k], at[f][(k + 1) % 3]
                home[a], home[b] = self.ours["V"][To[f][k]], self.ours["V"][To[f][(k + 1) % 3]]
                edges[(a, b)] = edges.get((a, b), 0) + 1
        rim = {}                                        # a vertex may start two rim edges (rims
        for (a, b) in edges:                            # touching at a corner): each edge once
            if (b, a) not in edges:
                rim.setdefault(a, []).append(b)
        out = []
        for loop in loops(rim):
            if len(loop) < 3:
                self.rimstat["open"] = self.rimstat.get("open", 0) + 1
                continue                                # an open strip, not a rim: leave it
            pts = np.array([where[v] for v in loop])
            n = sum(np.cross(p, q) for p, q in zip(pts, np.roll(pts, -1, 0)))      # Newell: the rim's
            if np.linalg.norm(n) < 1e-9:                                           # plane, facing
                continue                                                            # out of the solid
            n /= np.linalg.norm(n)
            e1 = np.cross(n, [1.0, 0.0, 0.0] if abs(n[0]) < 0.9 else [0.0, 1.0, 0.0])
            e1 /= np.linalg.norm(e1)
            flat = [np.array([p @ e1, p @ np.cross(n, e1)]) for p in pts]
            tris = ear_clip(flat)
            homes = np.array([home[v] for v in loop])
            if any((a, b) in seam for a, b in zip(loop, loop[1:] + loop[:1])):
                if not tris:
                    tris = fan(len(loop))
                    pts, homes = np.vstack([pts, pts.mean(0)]), np.vstack([homes, homes.mean(0)])
                keep = [t for t in tris if self.inside(homes[list(t)].mean(0))]
                self.rimstat["seam"] = self.rimstat.get("seam", 0) + 1
                self.rimstat["outside"] = self.rimstat.get("outside", 0) + len(tris) - len(keep)
                out += [pts[[a, c, b]] for a, b, c in keep]
                continue
            cen = [homes[list(t)].mean(0) for t in tris]
            if not tris or np.mean(nearest(self.ea_tree, cen)[2] <= 0.3) < 0.8 or \
                    not all(self.inside(c) for c in cen):
                why = "noear" if not tris else "air"
                self.rimstat[why] = self.rimstat.get(why, 0) + 1
                continue                                # an opening (a doorway, a recess)
            self.rimstat["capped"] = self.rimstat.get("capped", 0) + 1
            out += [pts[[a, c, b]] for a, b, c in tris]     # against the rim's own run: facing out
        return out

    def inside(self, p, dirs=np.vstack([np.eye(3), -np.eye(3)]), reach=60.0):
        """Whether a point is enclosed by the building as it stands: a ray each way along the axes
        meets our body or EA's healthy one within `reach` units (our body alone is open where it
        sits on EA's walls). A doorway's, an arch's or a recess's opening lets one out."""
        if not hasattr(self.link, "bvh"):
            self.link.bvh = tree(self.ours["V"], self.ours["T"])
        for d in dirs:
            if all(t.ray_cast(Vector(p), Vector(d), reach)[0] is None for t in (self.link.bvh, self.all_tree)):
                return False
        return True

    def displacement(self, pts):
        """How far EA's state moved its surface at each point's anchor (the nearest point of EA's
        healthy body): the state face lying over the anchor, projected along the healthy face's
        normal, gives the anchor's place in the state (EA bends and crumples its rubble); none
        there, no move."""
        anchors, idx, _ = nearest(self.ea_tree, pts)
        out = []
        for a in anchors:
            best = None
            if self.surf_tree is not None:
                r = self.ea_tree.find_nearest(Vector(a))
                n = np.array(r[1]) if r[0] is not None else np.array([0.0, 0.0, 1.0])
                e1 = np.cross(n, [1.0, 0.0, 0.0] if abs(n[0]) < 0.9 else [0.0, 1.0, 0.0])
                e1 /= np.linalg.norm(e1)
                e2 = np.cross(n, e1)
                for _, _, k, _ in self.surf_tree.find_nearest_range(Vector(a), self.s["tolerance"]):
                    piece, g = self.owner[k]
                    G = self.info[piece]["V"][self.info[piece]["T"][g]]
                    flat = [np.array([(p - a) @ e1, (p - a) @ e2]) for p in G]
                    w = barycentric(np.zeros(2), flat) if abs(polygon_area(flat)) > 1e-9 else None
                    if w is not None and (w >= -1e-6).all():
                        p = w @ G
                        if best is None or np.linalg.norm(p - a) < np.linalg.norm(best - a):
                            best = p
            out.append(np.zeros(3) if best is None else best - a)
        return out

    def split(self):
        """[(our face, barycentric corners 3x3, class)] for every part of ours that stays."""
        shell, done = self.solids()
        clipped = self.clip(shell)
        self.stats.update(faces=len(self.ours["T"]), shell_parts=len(clipped))
        return done + clipped

    def clip(self, shell):
        """Our faces on EA's healthy surface, cut to EA's state pieces there: each of EA's state
        surface faces near one of ours, projected into its plane and clipped to it, becomes a part
        of our face on that face's piece and bone (a skin's: its vertex nearest the part). What no
        state face covers, EA broke away."""
        Vo, To = self.ours["V"], self.ours["T"]
        tol = self.s["surface"]
        out = []
        covered = {n: np.zeros(len(i["T"])) for n, i in self.info.items()}
        for f in shell:
            A, B, C = Vo[To[f]]
            n = np.cross(B - A, C - A)
            if np.linalg.norm(n) < 1e-9:
                continue
            n /= np.linalg.norm(n)
            e1 = (B - A) / np.linalg.norm(B - A)
            e2 = np.cross(n, e1)
            flat = lambda p: np.array([(p - A) @ e1, (p - A) @ e2])        # noqa: E731
            tri = [flat(A), flat(B), flat(C)]
            cen = (A + B + C) / 3
            reach = max(np.linalg.norm(A - cen), np.linalg.norm(B - cen), np.linalg.norm(C - cen)) + tol
            for _, _, k, _ in self.surf_tree.find_nearest_range(Vector(cen), reach):
                piece, g = self.owner[k]
                inf = self.info[piece]
                G = inf["V"][inf["T"][g]]
                gn = np.cross(G[1] - G[0], G[2] - G[0])
                if np.linalg.norm(gn) < 1e-9 or (gn / np.linalg.norm(gn)) @ n < 0.7 or abs((G.mean(0) - A) @ n) > tol:
                    continue
                poly = convex_clip([flat(p) for p in G], tri)
                if len(poly) < 3 or polygon_area(poly) < 1e-4:
                    continue
                covered[piece][g] += polygon_area(poly)
                bc = [barycentric(q, tri) for q in poly]
                on_g = [barycentric(q, [flat(p) for p in G]) @ G for q in poly] if self.s["bend"] else \
                    [A + e1 * q[0] + e2 * q[1] for q in poly]      # EA's (bent) surface, or our own
                mid = A + e1 * np.mean([q[0] for q in poly]) + e2 * np.mean([q[1] for q in poly])
                vb = inf["T"][g][int(np.argmin(np.linalg.norm(G - mid, axis=1)))]
                cls = (piece, inf["bones"][vb] if inf["skinned"] else inf["bone"])
                out += [(f, np.array([bc[0], bc[i], bc[i + 1]]), cls, np.array([on_g[0], on_g[i], on_g[i + 1]]))
                        for i in range(1, len(bc) - 1)]
        for n, inf in self.info.items():            # EA's faces near its healthy surface that none of
            lone = inf["surf"] & (covered[n] < 0.5 * inf["area"])     # ours covers are break faces
            inf["surf"] &= ~lone                    # after all (a floor, a ledge): they stay EA's
            self.stats["uncovered"] = self.stats.get("uncovered", 0) + int(lone.sum())
        return out

    def bury(self, faces):
        """A collapse that plays once holds its last frame; EA sinks some pieces below the ground
        there to be rid of them. Our faces on those bones that would still stand above it (ours
        reach further than EA's piece) are cut, so no fragment of ours is left lying about."""
        a = self.e["animation"]
        if not a or a["mode"] != "ONCE":
            self.stats["buried"] = 0
            return faces
        last = self.S.pose(self.S.frames - 1)
        top = {}
        for n, inf in self.info.items():
            V = self.S.world(n, last)
            for v, b in enumerate(inf["bones"] if inf["skinned"] else [inf["bone"]] * len(V)):
                top[(n, b)] = max(top.get((n, b), -1e9), V[v, 2])
        sunk = {k for k, z in top.items() if z < 0}
        Vo, To, W = self.ours["V"], self.ours["T"], self.ours["W"]
        out, n = [], 0
        for f, bc, c, at in faces:
            if c != CUT and c in sunk:
                m = P.mul(last[0][c[1]], P.invert(self.pose[0][c[1]]))
                if max(P.point(m, p)[2] for p in at) > -0.05:
                    out.append((f, bc, CUT, at))
                    n += 1
                    continue
            out.append((f, bc, c, at))
        self.stats["buried"] = n
        return out



def polygon_area(poly):
    return 0.5 * sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1]))


def convex_clip(poly, clip):
    """Sutherland-Hodgman: a polygon clipped to a convex polygon; both counter-clockwise (the
    subject is turned if it is not), the result counter-clockwise."""
    if polygon_area(poly) < 0:
        poly = poly[::-1]
    if polygon_area(clip) < 0:
        clip = clip[::-1]
    out = list(poly)
    for a, b in zip(clip, clip[1:] + clip[:1]):
        if not out:
            break
        side = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])      # noqa: E731
        src, out = out, []
        for p, q in zip(src, src[1:] + src[:1]):
            sp, sq = side(p), side(q)
            if sp >= 0:
                out.append(p)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq)
                out.append(p + (q - p) * t)
    return out


def barycentric(p, tri):
    a, b, c = tri
    m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    u, v = np.linalg.solve(m, np.asarray(p) - a)
    return np.array([1 - u - v, u, v])


def ear_clip(poly):
    """Triangles [(i, j, k)] of a simple 2D polygon (either winding), by ear clipping."""
    idx = list(range(len(poly)))
    if polygon_area(poly) < 0:
        idx.reverse()
    out, guard = [], 0
    while len(idx) > 3 and guard < 4 * len(poly) * len(poly):
        guard += 1
        for k in range(len(idx)):
            a, b, c = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            A, B, C = poly[a], poly[b], poly[c]
            if (B[0] - A[0]) * (C[1] - A[1]) - (B[1] - A[1]) * (C[0] - A[0]) <= 1e-12:
                continue                                # reflex or flat corner
            if any(_inside(poly[p], A, B, C) for p in idx if p not in (a, b, c)):
                continue
            out.append((a, b, c))
            idx.pop(k)
            break
        else:
            return []                                   # not a simple polygon
    if len(idx) == 3:
        out.append(tuple(idx))
    return out


def loops(rim):
    """Closed loops [[vertex]] of directed rim edges {a: [b]}, each edge used once; a walk that
    does not come back to its start gives the part it walked as an open strip (fewer than 3)."""
    out = []
    for start in list(rim):
        while rim.get(start):
            loop, v = [start], rim[start].pop()
            while v != start and rim.get(v) and len(loop) < 4096:
                loop.append(v)
                v = rim[v].pop()
            out.append(loop if v == start else loop[:2])
    return out


def fan(n):
    """Triangles [(i, j, k)] of an n-gon's loop to its centre (index n): for a loop no plane fits."""
    return [(n, i, (i + 1) % n) for i in range(n)]


def _inside(p, a, b, c):
    def side(u, v, w):
        return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    return side(a, b, p) > 0 and side(b, c, p) > 0 and side(c, a, p) > 0
