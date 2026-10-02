"""Blender side of the lifecycle step (the design is in sagekit/lifecycle.py): per planned model,
EA's body pieces found at the pose the state is whole in, our body anchored on EA's healthy
surface, cut where EA broke and split into EA's pieces, the model written to out/, and
work/lifecycle.json saying what went where and whether our banners may stay up."""
import json
import os

import numpy as np

from ..formats import w3dmesh as WM
from ..formats import w3dpose as P
from ..formats.w3d import W3DFile, fix
from ..game import Install
from ..lifecycle import view_frames
from ..owncopy import prepare
from ..workspace import Workspace
from .lifecycle_cut import CUT, Cutter, face_frame, nearest, tree

IDENTITY = P.IDENTITY


class Model:
    """A W3D model with its skeleton and (optional) animation, posed on demand."""

    def __init__(self, path, skel_path=None, anim_path=None):
        self.data = path if isinstance(path, bytes) else open(path, "rb").read()
        self.w3d = W3DFile(self.data)
        _, self.hier, self.bones = P.hlod(self.data)
        skel = skel_path if isinstance(skel_path, bytes) or skel_path is None else open(skel_path, "rb").read()
        self.skel = P.Skeleton(skel or self.data)
        self.anim = P.Animation(open(anim_path, "rb").read()) if anim_path else None
        self.frames = self.anim.frames if self.anim else 1

    def pose(self, frame):
        """(world matrices, visibility) per pivot; frame None is the rest pose."""
        return self.skel.pose(self.anim if frame is not None else None, frame or 0)

    def vertex_bones(self, name):
        m = self.w3d.meshes[name]
        return (P.influences(m.bytes) if m.skinned else None) or [self.bones.get(name, 0)] * len(m.verts)

    def world(self, name, pose, verts=None):
        """(N, 3) world positions of a mesh's vertices (or of `verts` in its space) under a pose."""
        m = self.w3d.meshes[name]
        mats = np.array([pose[0][b] for b in self.vertex_bones(name)]).reshape(-1, 3, 4)
        V = np.array(m.verts if verts is None else verts, float)
        return np.einsum("nij,nj->ni", mats[:, :, :3], V) + mats[:, :, 3]


class Link:
    """One recipe's body in the model: a chained recipe (`base`) redesigns another mesh of the same
    model, so a lifecycle model carries every link's body, each on its own texture."""

    def __init__(self, b, healthy, offset=(0, 0, 0)):
        self.b, self.ws = b, Workspace(b)
        self.names = dict(self.ws.own_names)        # diffuse, normal, state variants, state normals (as derive)
        Vh = healthy.world(b.target, healthy.pose(None)) + offset
        Th = np.array(healthy.w3d.meshes[b.target].tris)
        self.ea_tree, (_, self.ea_normals, _) = tree(Vh, Th), face_frame(Vh, Th)
        chunk = W3DFile(self.ws.export_model).meshes[b.target].bytes
        m = W3DFile(chunk).meshes[b.target]
        W = list(healthy.pose(None)[0][healthy.bones.get(b.target, 0)])
        for axis in range(3):
            W[axis * 4 + 3] += offset[axis]
        self.ours = {"chunk": chunk, "V": np.array([P.point(W, v) for v in m.verts]), "T": np.array(m.tris), "W": W}
        cloth = self.ws.house_cloth
        self.cloth = json.load(open(cloth)) if self.ws.house and os.path.exists(cloth) else []


class Build(Cutter):
    """One lifecycle model rebuilt around our body (every link's)."""

    def __init__(self, b, ws, entry, healthy, links):
        self.b, self.ws, self.e, self.s = b, ws, entry, dict(entry["settings"])
        if self.s["bend"] is None:
            self.s["bend"] = entry["kind"] != "construction"
        self.fill = bool(self.s.get("fill"))         # sagekit/lifecycle.py
        src = ws.path("src")
        a = entry["animation"]
        self.S = Model(os.path.join(src, entry["model"].lower() + ".w3d"),
                       os.path.join(src, entry["skeleton"]) if entry["skeleton"] else None,
                       os.path.join(src, a["file"]) if a else None)
        offset = np.asarray(self.s.get("match_offset", (0, 0, 0)), float)
        if offset.shape != (3,) or not np.isfinite(offset).all():
            raise ValueError("match_offset must contain three finite coordinates")
        if np.any(offset):
            links = [Link(L.b, healthy, offset) for L in links]
        self.H, self.links = healthy, links
        self.warnings = []
        self.names = {k: v for L in links for k, v in L.names.items()}         # EA's names, any link's
        Vh = [healthy.world(L.b.target, healthy.pose(None)) + offset for L in links]
        Th = [np.array(healthy.w3d.meshes[L.b.target].tris) for L in links]
        off = np.cumsum([0] + [len(v) for v in Vh])[:-1]
        self.ea_tree = self.all_tree = tree(np.concatenate(Vh), np.concatenate([t + o for t, o in zip(Th, off)]))

    def use(self, link, pieces):
        """Work on one link: its body, its healthy surface, the state pieces it owns."""
        self.link, self.ours, self.ea_tree = link, link.ours, link.ea_tree
        self.info = {n: self.all_info[n] for n in pieces}
        verts, tris, owner = [], [], []
        off = 0
        for n, i in self.info.items():
            keep = np.nonzero(i["surf"])[0]
            verts.append(i["V"])
            tris.append(i["T"][keep] + off)
            owner += [(n, f) for f in keep]
            off += len(i["V"])
        self.surf_tree, self.owner = (tree(np.concatenate(verts), np.concatenate(tris)), owner) if owner else (None, [])

    # ------------------------------------------------------------------ EA's side
    def body(self):
        """EA's body pieces: painted from the building's sheet (ours to replace), not one of EA's
        other healthy meshes, and mostly lying on EA's healthy body at some pose."""
        S, s = self.S.w3d.meshes, self.s
        if s["body"]:
            return [n.upper() for n in s["body"] if n.upper() in S]
        keep = {n.upper() for n in s["keep"]}
        others = set(self.H.w3d.meshes) - {L.b.target for L in self.links}
        out = []
        for n, m in S.items():
            tex = [t for t in m.textures if "_nrm" not in t.lower()]
            if n in keep or n in others or not tex or not m.tris:
                continue
            if all(t.lower() in self.names for t in m.textures):
                out.append(n)
            elif any(t.lower() in self.names for t in tex):
                self.warnings.append("%s: texture %s has no variant of ours; left to EA" % (
                    n, [t for t in m.textures if t.lower() not in self.names]))
        return out

    def fit(self, pieces, frame, surface=None):
        """Area share of the pieces lying on EA's healthy body at a frame."""
        pose = self.S.pose(frame)
        near = total = 0.0
        for n in pieces:
            V = self.S.world(n, pose)
            c, _, area = face_frame(V, np.array(self.S.w3d.meshes[n].tris))
            _, _, d = nearest(self.ea_tree, c)
            near += area[d <= (surface or self.s["surface"])].sum()
            total += area.sum()
        return near / max(total, 1e-9)

    def match(self, pieces):
        m = self.s["match"]
        last = self.S.frames - 1
        if m != "auto":
            return {"rest": None, "first": 0, "last": last}.get(m, m), None
        best, score = None, -1.0
        for f in dict.fromkeys([None, 0, last]):
            if f is not None and not self.S.anim:
                continue
            x = self.fit(pieces, f)
            if x > score + 0.02:
                best, score = f, x
        return best, score

    def surface(self, pieces):
        """Per piece: its link (of the links whose sheets paint it, the one whose healthy body most of
        it lies on: a chain's second body may stand beside the first, as a fence round a stable),
        world vertices at the match pose, triangles, vertex bones, and which faces lie on that
        link's healthy surface."""
        self.all_info, self.link_of = {}, {}
        loose = max(2.0, self.s["surface"])                            # EA's rubble chunks are dented
        for n in pieces:
            m = self.S.w3d.meshes[n]
            V, T = self.S.world(n, self.pose), np.array(m.tris)
            c, fn, area = face_frame(V, T)
            best = None
            tex = [t.lower() for t in m.textures if "_nrm" not in t.lower()]
            painted = [L for L in self.links if tex and all(t in L.names for t in tex)]
            for L in painted or self.links:         # a piece is its sheet's link's, never another's
                _, idx, d = nearest(L.ea_tree, c)
                share = area[d <= loose].sum() / max(area.sum(), 1e-9)
                if best is None or share > best[0]:
                    best = (share, L, idx, d)
            share, L, idx, d = best
            if share < 0.25 and not self.s["body"]:
                continue                                # not on any healthy body: debris, left to EA
            dot = (fn * L.ea_normals[np.maximum(idx, 0)]).sum(1)
            self.link_of[n] = L
            self.all_info[n] = dict(V=V, T=T, area=area, bones=self.S.vertex_bones(n), skinned=m.skinned,
                                    bone=self.S.bones.get(n, 0), surf=(d <= self.s["surface"]) & (dot >= 0.5))
        if not self.all_info:
            raise ValueError("no piece of %s lies on EA's healthy body" % self.e["model"])

    def classify(self, pts):
        """Per point: CUT, or (piece, bone) - the piece whose surface holds its anchor on EA's
        healthy body, on the bone of that surface's nearest vertex."""
        if self.surf_tree is None:
            return [CUT] * len(pts)
        anchors, _, _ = nearest(self.ea_tree, pts)
        loc, idx, d = nearest(self.surf_tree, anchors)
        out = []
        for i in range(len(pts)):
            if idx[i] < 0 or d[i] > self.s["tolerance"] and not self.fill:     # fill: nothing is cut
                out.append(CUT)
                continue
            n, f = self.owner[idx[i]]
            inf = self.info[n]
            tri = inf["T"][f]
            k = int(np.argmin(np.linalg.norm(inf["V"][tri] - loc[i], axis=1)))
            out.append((n, inf["bones"][tri[k]] if inf["skinned"] else inf["bone"]))
        return out

    # ------------------------------------------------------------------ assembly
    def run(self):
        e = self.e
        rep = {"model": e["model"], "kind": e["kind"], "states": e["states"], "built": False, "warnings": self.warnings}
        pieces = self.body()
        if not pieces:
            rep["summary"] = "no body pieces of ours: left to EA"
            return rep
        self.ea_tree = self.all_tree
        self.frame, fit = self.match(pieces)
        self.pose = self.S.pose(self.frame)
        self.surface(pieces)
        pieces = list(self.all_info)
        self.surf0 = {n: i["surf"].copy() for n, i in self.all_info.items()}
        solids = self.s["solid"] if isinstance(self.s["solid"], (list, tuple)) else [self.s["solid"]]
        tried = [self.variant(pieces, x) for x in solids]
        best = min(tried, key=lambda v: (bool(v["failed"]), v["worst"]))
        if best is not tried[-1]:                       # its state (EA's surface flags) for banner()
            best = self.variant(pieces, best["solid"])
        out, bones, plan, failed = best["out"], best["bones"], best["plan"], best["failed"]
        kept, faces = best["kept"], best["faces"]
        rep.update(match=self.frame, fit=fit, faces=faces, kept=kept, split=self.stats, pieces=plan, gate=failed,
                   solid=best["solid"], tried={str(v["solid"]): round(100 * v["worst"], 2) for v in tried})
        if failed and not self.s["force"]:
            rep["summary"] = "left to EA (below the checks' standard; `force` ships it): %s" % "; ".join(failed)
            self.warnings.extend(failed)
            return rep
        out = prepare(self.b, e["model"], out)            # an own copy ships under its own name
        from ..sharedsheets import renamed              # shared EA sheets as the faction's copies
        out = renamed(self.ws, out)
        from ..nightlights import carry                 # our night lights (sagekit/nightlights.py)
        out = carry(self.b, e["model"], out, keep=e["kind"] != "construction", pose=self.pose)
        dest = self.ws.out(Install.model_path(self.b.shipped_name(e["model"])))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(out)
        rep.update(built=True, pieces=plan, hosts={k: v for k, v in bones.items()},
                   banner=self.banner(), summary="match %s (fit %.2f), %s, %d of %d faces kept, %s" % (
                       "rest" if self.frame is None else "frame %d" % self.frame, fit or 0,
                       "solids whole" if best["solid"] is None else "solids over %s split" % best["solid"], kept, faces,
                       ", ".join("%s %s" % (n, p["mode"]) for n, p in plan.items())))
        return rep

    def variant(self, pieces, solid):
        """The model built with one `solid` setting (None: every added solid goes whole), held to
        the checks: {out, bones, plan, failed, worst (open backs past EA's), faces, kept}. Big
        solids split along EA's pieces follow the collapse closely but open seams; whole ones stay
        closed but ride one piece: the lifecycle step builds each way the recipe allows and ships
        the one the checks like best."""
        e = self.e
        for n, s0 in self.surf0.items():
            self.all_info[n]["surf"] = s0.copy()
        self.s = dict(self.s, solid=solid)
        own, faces, kept, stats = {n: [] for n in pieces}, 0, 0, {}
        for L in self.links:
            mine = [n for n in pieces if self.link_of[n] is L]
            if not mine:
                if not any("no piece of its own" in w for w in self.warnings):
                    self.warnings.append("%s's body has no piece of its own here: left out" % L.b.id)
                continue
            self.use(L, mine)
            done = self.bury(self.split())
            for x in done:
                if x[2] != CUT:
                    own[x[2][0]].append(x)
            faces += len(done)
            kept += sum(x[2] != CUT for x in done)
            stats[L.b.target] = self.stats
        self.info, self.stats = self.all_info, stats
        chunks, bones, plan = self.assemble(pieces, own)
        out = WM.replace_meshes(self.S.data, chunks)
        out = P.set_hlod_bones(out, bones)
        if W3DFile(out).object_names() != self.S.w3d.object_names():
            raise ValueError("%s: object names changed" % e["model"])
        from .checks_lifecycle import gate, reference   # held to the checks' standard before it ships
        a, src = e["animation"], self.ws.path("src")
        failed, worst = gate(self.b, e["model"], e["kind"], self.frame, view_frames(e, self.S.frames), self.S.data,
                             out, os.path.join(src, e["skeleton"]) if e["skeleton"] else None,
                             os.path.join(src, a["file"]) if a else None, list(plan),
                             [n for n, p in plan.items() if p["mode"].startswith("ours")],
                             own=reference(self.links))
        return dict(solid=solid, out=out, bones=bones, plan=plan, failed=failed, worst=worst, faces=faces, kept=kept)

    def assemble(self, pieces, own):
        """{mesh: new chunk}, {mesh turned into a skin: 0}, per-piece plan. Per link: a piece without
        break faces takes its share of our faces in place; the rest of that link's share goes to
        one host piece (a skin); EA's break faces stay in their pieces, a host's move to another."""
        info = self.info
        brk = {n: np.nonzero(~info[n]["surf"])[0] for n in pieces}

        def area(n):
            L = self.link_of[n]
            V, T = L.ours["V"], L.ours["T"]
            return sum(float(np.linalg.norm(np.cross(*(bc[1:] - bc[0]) @ V[T[f]]))) / 2 for f, bc, *_ in own[n] if f >= 0)
        ours_in = {}
        ea_in = {n: [(n, f) for f in brk[n]] for n in pieces if len(brk[n])}
        skins, moved = set(), []
        for L in self.links:
            mine = [n for n in pieces if self.link_of[n] is L]
            clean = [n for n in mine if not len(brk[n])]
            broken = [n for n in mine if len(brk[n])]
            ours_in.update({n: list(own[n]) for n in clean})
            if not any(own[n] for n in broken):
                continue
            if clean:
                host = max(clean, key=area)
            else:
                host = min(broken, key=lambda n: len(brk[n]))
                moved += ea_in.pop(host)
                ours_in[host] = []
            ours_in[host] += [x for n in broken for x in own[n]]
            skins.add(host)
        donated = {}
        groups = {}                                 # a chain's hosts may be painted from different sheets
        for p, g in moved:                          # (the Men's level meshes on GBVet beside the body)
            groups.setdefault(tuple(sorted(t.lower() for t in self.S.w3d.meshes[p].textures)), []).append((p, g))
        for tex, faces in groups.items():
            srcs = list(dict.fromkeys(p for p, _ in faces))
            back = [n for n in ea_in if sorted(t.lower() for t in self.S.w3d.meshes[n].textures) == list(tex)
                    and all(WM.fits(self.S.w3d.meshes[n].bytes, self.S.w3d.meshes[p].bytes) for p in srcs)]
            if back:
                back = max(back, key=lambda n: len(ea_in[n]))
                ea_in[back] += faces
                skins.add(back)
            else:                                   # no piece of EA's texture left to hold them: they
                for p, g in faces:                  # join our host, on our sheet (donor_uv)
                    host = next(n for n in skins if self.link_of[n] is self.link_of[p])
                    donated.setdefault(host, []).append((p, g))
                self.stats["donated"] = self.stats.get("donated", 0) + len(faces)
        vis = self.S.anim.vis if self.S.anim else {}
        for n in pieces:
            if n not in ours_in and own[n] and any(b in vis for b in set(info[n]["bones"]) | {info[n]["bone"]}):
                self.warnings.append("%s: its bone's visibility is animated, but our faces for it ride a skin" % n)
        chunks, plan = {}, {}
        for n in pieces:
            skin = info[n]["skinned"] or n in skins
            host = " (host)" if n in skins else ""
            if ours_in.get(n):
                chunks[n] = self.ours_mesh(n, ours_in[n], skin, self.link_of[n], donated.get(n, ()))
                plan[n] = {"mode": "ours" + host, "faces": len(ours_in[n]), "skin": skin, "link": self.link_of[n].b.id}
            elif ea_in.get(n):
                chunks[n] = self.ea_mesh(n, ea_in[n], skin)
                plan[n] = {"mode": "EA break faces" + host, "faces": len(ea_in[n]), "skin": skin}
            else:
                plan[n] = {"mode": "left to EA (none of ours reached it)", "faces": 0, "skin": info[n]["skinned"]}
                self.warnings.append("%s: no face of ours reached it; EA's piece kept" % n)
        bones = {n: 0 for n in skins if not info[n]["skinned"]}
        return chunks, bones, plan

    def ours_mesh(self, n, faces, skin, link, donated=()):
        """Our faces as mesh n: the link's body with n's material (EA's, pointed at its textures),
        and EA's break faces [(piece, face)] that had nowhere else to go, painted from our sheet
        (donor_uv)."""
        ea = self.S.w3d.meshes[n]
        renames = [(n, t, link.names[t.lower()]) for t in ea.textures if t.lower() in link.names]
        tpl, _ = fix(self.S.data, WM.renamed(link.ours["chunk"], n), renames)
        src = WM.Source(tpl)
        To, W = link.ours["T"], link.ours["W"]
        verts, tris, key, seen = [], [], {}, set()
        inv = P.invert(W)
        Vo = link.ours["V"]
        caps = [(p, bone) for f, _, (_, bone), p in faces if f < 0]
        faces = [x for x in faces if x[0] >= 0]
        for f, bc, (piece, bone), at in faces:
            m = P.mul(P.invert(self.pose[0][bone]), W)
            n0, n1 = np.cross(*(Vo[To[f]][1:] - Vo[To[f]][0])), np.cross(*(at[1:] - at[0]))
            bent = n0 @ n1 < 0.996 * np.linalg.norm(n0) * np.linalg.norm(n1)       # EA tilted it
            over = {WM.NORMALS: P.direction(inv, n1 / max(np.linalg.norm(n1), 1e-12))} if bent else {}
            ids = []
            for corner, p in zip(bc, at):           # at: where EA's state puts the corner (world)
                combo = tuple((int(To[f][k]), float(corner[k])) for k in range(3) if corner[k] > 1e-9)
                k = (tuple((v, round(w, 6)) for v, w in combo), bone, tuple(np.round(p, 4)), bent)
                if k not in key:
                    key[k] = len(verts)
                    verts.append(("ours", list(combo), m, bone, {**over, WM.VERTICES: P.point(inv, p)}))
                ids.append(key[k])
            if len(set(ids)) == 3 and tuple(sorted(ids)) not in seen:     # no slivers, no doubles
                seen.add(tuple(sorted(ids)))
                tris.append((ids, src.surface[f]))
        for at, bone in caps:                       # rims of our solids, painted from their nearest face
            ids = []
            for combo, pos, normal in self.donor_points(link, at):
                ids.append(len(verts))
                verts.append(("ours", combo, P.mul(P.invert(self.pose[0][bone]), W), bone,
                              {WM.VERTICES: pos, WM.NORMALS: normal}))
            tris.append((ids, src.surface[0]))
        for p, g, corners in self.donor_uv(link, donated):
            ids = []
            for combo, pos, normal, bone in corners:
                ids.append(len(verts))
                verts.append(("ours", combo, P.mul(P.invert(self.pose[0][bone]), W), bone,
                              {WM.VERTICES: pos, WM.NORMALS: normal}))
            tris.append((ids, src.surface[0]))
        return WM.build_mesh(tpl, {"ours": src}, n, ea.container, verts, tris, skin, self.S.skel.rest)

    def donor_points(self, link, G):
        """A triangle's corners (world, 3x3) as points of our body's texture: the nearest face of
        ours, each corner clamped into it. -> [(combo, position, normal)] in our body's space."""
        V, T, W = link.ours["V"], link.ours["T"], link.ours["W"]
        if not hasattr(link, "bvh"):
            link.bvh = tree(V, T)
        inv = P.invert(W)
        n = np.cross(G[1] - G[0], G[2] - G[0])
        n = n / max(np.linalg.norm(n), 1e-12)
        _, idx, _ = nearest(link.bvh, [G.mean(0)])
        A, B, C = V[T[idx[0]]]
        out = []
        for p in G:
            w = clamped_barycentric(p, A, B, C)
            out.append(([(int(T[idx[0]][j]), float(w[j])) for j in range(3) if w[j] > 1e-9], P.point(inv, p), P.direction(inv, n)))
        return out

    def donor_uv(self, link, faces):
        """EA's break faces as faces of our body: each corner takes the texture of the nearest point
        of our body (clamped into that face of ours, so it samples its island only) - the stone of
        the wall it broke out of. -> [(piece, face, [(combo, position, normal, bone)])] in our
        body's own space."""
        if not faces:
            return []
        V, T, W = link.ours["V"], link.ours["T"], link.ours["W"]
        bvh, inv = tree(V, T), P.invert(W)
        out = []
        for p, g in faces:
            inf = self.info[p]
            G = inf["V"][inf["T"][g]]
            n = np.cross(G[1] - G[0], G[2] - G[0])
            n = n / max(np.linalg.norm(n), 1e-12)
            _, idx, _ = nearest(bvh, [G.mean(0)])
            A, B, C = V[T[idx[0]]]
            corners = []
            for k, v in enumerate(inf["T"][g]):
                w = clamped_barycentric(G[k], A, B, C)
                combo = [(int(T[idx[0]][j]), float(w[j])) for j in range(3) if w[j] > 1e-9]
                bone = inf["bones"][v] if inf["skinned"] else inf["bone"]
                corners.append((combo, P.point(inv, G[k]), P.direction(inv, n), bone))
            out.append((p, g, corners))
        return out

    def ea_mesh(self, n, faces, skin):
        """EA's own faces [(source piece, face)] as mesh n (n's material)."""
        srcs, tpl = {}, self.S.w3d.meshes[n]
        for p, _ in faces:
            if p not in srcs:
                m = self.S.w3d.meshes[p]
                if sorted(t.lower() for t in m.textures) != sorted(t.lower() for t in tpl.textures):
                    raise ValueError("%s and %s are painted differently: cannot share a mesh" % (p, n))
                srcs[p] = WM.Source(m.bytes)
        verts, tris, key = [], [], {}
        for p, f in faces:
            ids = []
            for v in srcs[p].tris[f]:
                bone = self.info[p]["bones"][v]
                k = (p, v, bone)
                if k not in key:
                    key[k] = len(verts)
                    verts.append((p, [(v, 1.0)], IDENTITY, bone, {}))
                ids.append(key[k])
            tris.append((ids, srcs[p].surface[f]))
        return WM.build_mesh(tpl.bytes, srcs, n, tpl.container, verts, tris, skin, self.S.skel.rest)

    # ------------------------------------------------------------------ the banner
    def banner(self):
        """Whether our banners (the house-colour model, drawn static with the building) may stay:
        not while it is built, nor where the faces they hang on are cut or move."""
        if not any(L.cloth for L in self.links):
            return {"supported": True, "why": "no banners of ours"}
        if self.e["kind"] == "construction":
            return {"supported": False, "why": "under construction"}
        bones = set()
        for L in self.links:
            if not L.cloth:
                continue
            self.use(L, [n for n in self.info if self.link_of[n] is L])
            cls = self.classify(np.array([p for poly in L.cloth for p in poly]))
            cut = sum(c == CUT for c in cls)
            if cut:
                return {"supported": False, "why": "%d of %d banner corners on faces cut away" % (cut, len(cls))}
            bones |= {c[1] for c in cls}
        return self.static(bones)

    def static(self, bones):
        frames = list(range(0, self.S.frames, 5)) + [self.S.frames - 1] if self.S.anim else [None]
        return static(self.S, self.pose, bones, frames)


def static(model, match_pose, bones, frames):
    """Whether bones stay where the match pose has them at every frame (0.05 units / radians)."""
    for f in frames:
        w = model.pose(f)[0]
        for b in bones:
            if max(abs(x - y) for x, y in zip(w[b], match_pose[0][b])) > 0.05:
                return {"supported": False, "why": "bone %s moves by frame %s" % (model.skel.names[b], f)}
    return {"supported": True, "why": "the faces they hang on stay"}


def derived_banner(b, ws, entry, healthy):
    """A derived model (our body as it is, on the target's bone): banners stay unless the target's
    bone moves or it is a construction model."""
    if entry["kind"] == "construction":
        return {"supported": False, "why": "under construction"}
    a = entry["animation"]
    if not a:
        return {"supported": True, "why": "no animation"}
    src = ws.path("src")
    own = os.path.join(src, entry["model"].lower() + ".w3d")
    S = Model(own if os.path.exists(own) else Install().read(Install.model_path(entry["model"])),
              os.path.join(src, entry["skeleton"]) if entry["skeleton"] else None, os.path.join(src, a["file"]))
    bone = S.bones.get(b.target, 0)
    return static(S, S.pose(None), {bone}, list(range(0, S.frames, 5)) + [S.frames - 1])


def derived_views(ws, entry):
    """The frames a derived model is shown at (renders): as a built one's."""
    a = entry["animation"]
    frames = P.Animation(open(ws.path("src", a["file"]), "rb").read()).frames if a else 1
    return view_frames(entry, frames)


def chain(b):
    """The recipes whose bodies a model of b's carries: b and every base it builds on, root first."""
    out = [b]
    while out[0].base:
        out.insert(0, out[0].base_building())
    return out


def run(b, ws):
    entries = json.load(open(ws.path("work", "lifecycle_plan.json")))
    g = Install()
    data = g.read(g.model_path(b.source))                  # EA's healthy model, whatever the chain did
    skl = W3DFile(data).skeleton()
    healthy = Model(data, g.read(g.model_path(skl[:-4])) if skl else None)
    for x in chain(b):
        if not os.path.exists(Workspace(x).export_model):
            raise SystemExit("build %s first: %s's lifecycle models carry its body" % (x.id, b.id))
    links = [Link(x, healthy) for x in chain(b)]
    report = []
    for e in entries:
        if e["settings"]["skip"]:
            report.append({"model": e["model"], "kind": e["kind"], "states": e["states"], "built": False,
                           "summary": "left to EA by the recipe (skip): %s" % e["settings"]["skip"],
                           "banner": {"supported": False, "why": "EA's model is drawn: our banners would float"}})
            continue
        if e["derived"]:
            report.append({"model": e["model"], "kind": e["kind"], "states": e["states"], "built": False,
                           "derived": True, "views": derived_views(ws, e),
                           "summary": "derived (our body as it is): EA's body here is the healthy one, whole on "
                                      "one bone, so the derive step splices ours in and EA's animation moves it",
                           "banner": derived_banner(b, ws, e, healthy)})
            continue
        try:
            bld = Build(b, ws, e, healthy, links)
            r = bld.run()
            r["views"] = view_frames(e, bld.S.frames)
        except (ValueError, NotImplementedError) as x:          # a model the tool cannot read or place:
            r = {"model": e["model"], "kind": e["kind"], "states": e["states"], "built": False,   # EA's stays
                 "summary": "left to EA: %s" % x, "warnings": [str(x)]}
        if not r["built"]:                                  # EA's model stays: our banners' faces
            r["banner"] = {"supported": False, "why": "EA's model is drawn: our banners would float"}
        report.append(r)
        print("LIFECYCLE", r["model"], r["summary"], flush=True)
    with open(ws.path("work", "lifecycle.json"), "w") as fh:
        json.dump({"models": report}, fh, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))


def clamped_barycentric(p, a, b, c):
    """Barycentric weights of p's projection onto triangle abc, clamped into the triangle."""
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-12:
        return np.array([1.0, 0.0, 0.0])
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    bc = np.clip(np.array([1 - v - w, v, w]), 0, None)
    return bc / bc.sum()


def check_match_offset():
    """Standalone Blender check using the player's built floodgate doors; never launches the game."""
    from ..registry import load
    b = load("elves/floodgate_doors")
    ws = Workspace(b)
    e = next(e for e in json.load(open(ws.path("work", "lifecycle_plan.json"))) if e["model"] == "EBFFGate_DRA")
    healthy = Model(ws.path("src", b.source.lower() + ".w3d"))
    link = Link(b, healthy)
    default = Build(b, ws, dict(e, settings=dict(e["settings"], match_offset=(0, 0, 0))), healthy, [link])
    shifted = Build(b, ws, e, healthy, [link])
    assert default.links[0] is link  # zero preserves the existing path and reference data
    assert shifted.links[0] is not link
    np.testing.assert_allclose(shifted.links[0].ours["V"], link.ours["V"] + e["settings"]["match_offset"])
    assert shifted.fit(shifted.body(), shifted.S.frames - 1) > 0.999
    assert default.fit(default.body(), default.S.frames - 1) < 0.5
    print("match_offset: default unchanged; EA construction doors align with healthy geometry")
