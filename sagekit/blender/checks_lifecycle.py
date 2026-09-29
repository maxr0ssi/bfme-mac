"""Checks for the lifecycle models (sagekit/lifecycle.py), against EA's own model of each state and at
the frames the player sees it: EA's skeleton, animations and HLOD kept (a host piece's bone aside),
valid one-bone skins, nothing of ours deeper in the ground or wider than EA's pieces go, and no
more of our faces showing their back to the sky than EA's model does (open holes where we cut)."""
import json
import os
import struct

import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from ..formats import w3dpose as P
from ..formats.assetcache import AssetCache
from ..formats.w3d import AABTREE, W3DFile, chunks
from ..game import Install
from ..owncopy import prepare
from .checks import sky_dirs
from ..workspace import Workspace
from .lifecycle import Model, chain

DEBUG = None               # a list to collect the back-seen triangles in (diagnostics)
GROUND_TOL = 0.5            # units our faces may go below EA's deepest vertex on the same bone
SPREAD_TOL = 1.0            # units our model may reach past EA's (plus the recipe's footprint margin)
BACK_TOL = {True: 0.02, False: 0.10}    # area share of our faces showing their back to the RTS camera
                                        # beyond EA's: standing / pieces moving or crumpled (rubble)


def run(b, ws, r):
    p = ws.path("work", "lifecycle.json")
    if not os.path.exists(p):
        return
    plan = {e["model"]: e for e in json.load(open(ws.path("work", "lifecycle_plan.json")))}
    report = json.load(open(p))["models"]
    r.section("lifecycle models (construction / really damaged / rubble)")
    for m in report:
        if not m["built"]:
            r.info(m["model"], m["summary"])
            continue
        check_model(b, ws, r, m, plan[m["model"]])


def check_model(b, ws, r, m, e):
    name = m["model"]
    src = ws.path("src")
    skel = os.path.join(src, e["skeleton"]) if e["skeleton"] else None
    anim = os.path.join(src, e["animation"]["file"]) if e["animation"] else None
    ea_path, new_path = os.path.join(src, name.lower() + ".w3d"), ws.out(Install.model_path(b.shipped_name(name)))
    r.check("%s: shipped" % name, os.path.exists(new_path), os.path.relpath(new_path, ws.root))
    if not os.path.exists(new_path):
        return
    EA, NEW = Model(ea_path, skel, anim), Model(new_path, skel, anim)
    EA.data = prepare(b, name, EA.data)                 # an own copy: EA's model under our name
    from ..sharedsheets import renamed                  # and shared EA sheets as the faction's copies
    EA.data = renamed(ws, EA.data)
    EA.w3d = type(EA.w3d)(EA.data)
    we, wn = EA.w3d, NEW.w3d
    pieces = m["pieces"]

    # bones and hierarchy intact
    r.check("%s: object names as EA's" % name, wn.object_names() == we.object_names(), "")
    top_e, top_n = we.top(), wn.top()
    r.check("%s: top-level chunk order as EA's" % name, [t for t, _ in top_e] == [t for t, _ in top_n], "")
    same = [hex(t) for (t, a), (_, c) in zip(top_e, top_n) if t in (0x100, 0x200, 0x280, 0x740) and a != c]
    r.check("%s: hierarchy, animations, boxes byte-identical" % name, not same, str(same))
    _, _, hb_e = P.hlod(EA.data)
    _, _, hb_n = P.hlod(NEW.data)
    moved = {k: (hb_e[k], v) for k, v in hb_n.items() if hb_e.get(k) != v}
    hosts = {k: (hb_e[k], 0) for k in m.get("hosts", {}) if hb_e.get(k)}
    r.check("%s: HLOD bones as EA's but the skin hosts' (on 0)" % name, moved == hosts, str(moved))
    from ..nightlights import names_of, night_meshes     # rebuilt by the night-lights standard
    night = night_meshes(names_of(ws), EA.data)
    others = [n for n in we.meshes if (n not in pieces or pieces[n]["mode"].startswith("left")) and n not in night]
    r.check("%s: EA's other meshes byte-identical" % name,
            all(wn.meshes[n].bytes == we.meshes[n].bytes for n in others), ", ".join(others))

    # vertex influences valid
    ea_bones = set()
    for n in pieces:
        ea_bones |= set(EA.vertex_bones(n))
    bad = []
    for n in pieces:
        mesh = wn.meshes[n]
        if len(mesh.verts) > 65535:
            bad.append("%s: %d vertices" % (n, len(mesh.verts)))
        if mesh.skinned:
            infl = _influences(mesh.bytes)
            if len(infl) != len(mesh.verts):
                bad.append("%s: %d influences for %d vertices" % (n, len(infl), len(mesh.verts)))
            wrong = {x[0] for x in infl if x[0] >= len(NEW.skel.pivots) or x[0] not in ea_bones or x[1:] != (0, 100, 0)}
            if wrong:
                bad.append("%s: bones %s" % (n, sorted(wrong)))
            rest = NEW.world(n, NEW.pose(None))                 # EA files a skin's box at rest
            box = struct.unpack_from("<6f", mesh.bytes, _header_at(mesh.bytes) + 76)
            if len(rest) and max(np.abs(np.array(box) - np.concatenate([rest.min(0), rest.max(0)]))) > 0.01:
                bad.append("%s: header box not the skin's rest box" % n)
        elif not any(t == AABTREE for t, _, _, _ in chunks(mesh.bytes, 8, len(mesh.bytes))):
            bad.append("%s: rigid without a collision tree" % n)
    r.check("%s: skins one bone per vertex on EA's body bones, boxed at rest; rigid meshes with collision trees" % name,
            not bad, "; ".join(bad) or "%d bones" % len(ea_bones))
    mine = {k.lower() for x in chain(b) for k in list(x.texture_names().values()) + list(Workspace(x).variants.values())}
    tex = [n for n, p in pieces.items() if p["mode"].startswith("ours") and
           not all(t.lower() in mine for t in wn.meshes[n].textures)]
    r.check("%s: our pieces painted from our sheets" % name, not tex, str({n: wn.meshes[n].textures for n in tex}))

    caches = [AssetCache(c) for c in ws.caches()]
    home = next((c for c in caches if c.has_model(b.shipped_name(name).lower() + ".w3d")), None)
    if home is None:                        # the engine draws no model its caches do not file
        r.check("%s filed in the asset caches" % b.shipped_name(name), False, "no record: the game would not draw it")
    else:
        st = home.stale_entries(new_path, b.shipped_name(name).lower() + ".w3d")
        r.check("%s: asset cache record matches the file" % name, not st, "%d stale" % len(st))

    ours = [n for n, p in pieces.items() if p["mode"].startswith("ours")]
    for f in m["views"]:
        frame_checks(b, r, name, f, EA, NEW, list(pieces), ours, m["match"], m["kind"])


class Collect:
    """A Report that only remembers the failures (the lifecycle step's own gate)."""

    def __init__(self):
        self.failed = []
        self.worst = 0.0                            # the largest open-back share past EA's, any frame

    def check(self, name, ok, detail=""):
        if not ok:
            self.failed.append("%s: %s" % (name, detail))

    def info(self, name, detail):
        pass


def gate(b, name, kind, match, views, ea_data, new_data, skel, anim, pieces, ours):
    """The per-frame checks run on a freshly built model: ([failure] (empty: it may ship), the
    largest share of our area showing its back to the sky past EA's, at any frame)."""
    EA, NEW = Model(ea_data, skel, anim), Model(new_data, skel, anim)
    r = Collect()
    for f in views:
        frame_checks(b, r, name, f, EA, NEW, pieces, ours, match, kind)
    return r.failed, r.worst


def _header_at(mesh_bytes):
    return next(o + 8 for t, o, _, _ in chunks(mesh_bytes, 8, len(mesh_bytes)) if t == 0x1F)


def _influences(mesh_bytes):
    for t, o, s, _ in chunks(mesh_bytes, 8, len(mesh_bytes)):
        if t == 0x0E:
            return [struct.unpack_from("<4H", mesh_bytes, o + 8 + 8 * i) for i in range(s // 8)]
    return []


def frame_checks(b, r, name, f, EA, NEW, pieces, ours, match, kind):
    """At one frame the player sees. What stands where it stood (every bone at its match pose) is
    held to the healthy building's limits; pieces in flight or lying about carry our bigger body
    with them, so their depth and spread are reported, and only their open backs are held to a
    looser limit. Bones EA sinks out of sight are not looked at."""
    at = "rest" if f is None else "frame %d" % f
    pe, pn, pm = EA.pose(f), NEW.pose(f), EA.pose(match)
    moving = {k for k in range(len(pe[0])) if max(abs(x - y) for x, y in zip(pe[0][k], pm[0][k])) > 0.05}
    standing = not moving & {bn for n in pieces for bn in EA.vertex_bones(n)}

    def by_bone(model, pose, names):
        lo, hi = {}, {}
        for n in names:
            V = model.world(n, pose)
            for v, bone in zip(V, model.vertex_bones(n)):
                lo[bone], hi[bone] = min(lo.get(bone, 1e9), v[2]), max(hi.get(bone, -1e9), v[2])
        return lo, hi
    (low_e, top_e), (low_n, _) = by_bone(EA, pe, pieces), by_bone(NEW, pn, ours)
    deep = {EA.skel.names[k]: round(z, 1) for k, z in low_n.items()
            if z < min(0.0, low_e.get(k, 0.0)) - GROUND_TOL and top_e.get(k, 1.0) > 0}
    fixed = {k: v for k, v in deep.items() if EA.skel.index(k) not in moving}
    r.check("%s @ %s: nothing of ours deeper in the ground than EA's (bones in place)" % (name, at), not fixed,
            str(fixed) if fixed else "lowest %.1f (EA %.1f)" % (min(low_n.values(), default=0), min(low_e.values(), default=0)))
    if len(deep) > len(fixed):
        r.info("%s @ %s: pieces in flight below EA's" % (name, at), str({k: v for k, v in deep.items() if k not in fixed}))
    box = lambda model, pose, names: np.concatenate([model.world(n, pose)[:, :2] for n in names])   # noqa: E731
    be, bn = box(EA, pe, list(EA.w3d.meshes)), box(NEW, pn, list(NEW.w3d.meshes))
    tol = SPREAD_TOL + b.footprint_margin
    over = max(np.maximum(be.min(0) - bn.min(0), 0).max(), np.maximum(bn.max(0) - be.max(0), 0).max())
    text = "x/y [%.1f %.1f]..[%.1f %.1f], EA [%.1f %.1f]..[%.1f %.1f]" % (*bn.min(0), *bn.max(0), *be.min(0), *be.max(0))
    if standing:
        r.check("%s @ %s: footprint within EA's (+%.1f)" % (name, at, tol), over <= tol, text)
    else:
        r.info("%s @ %s: spread past EA's by %.1f" % (name, at, over), text)
    se, sn = back_seen(EA, pe, pieces, pieces), back_seen(NEW, pn, list(NEW.w3d.meshes), ours)
    slack = BACK_TOL[standing and kind != "rubble"]
    if hasattr(r, "worst"):
        r.worst = max(r.worst, sn - se)
    r.check("%s @ %s: our faces' backs open to the sky at most %d%% more than EA's" % (name, at, 100 * slack),
            sn <= se + slack, "%.2f%% of our area (EA's body: %.2f%%)" % (100 * sn, 100 * se))


def covered(bvh, p, d):
    """Whether a face turned away from direction d at p lies on a surface facing d (a cap on the
    wall top it stands on): culled, it shows that surface, not a hole."""
    hit = bvh.ray_cast(p + d * 0.02, -d, 0.2)
    return hit[0] is not None and hit[1].dot(d) > 0.05


def back_seen(model, pose, scene, measured, dirs=[d for d in sky_dirs(64) if d.z >= 0.5]):
    """Area share of the `measured` meshes' triangles whose back is visible from some direction the
    RTS camera looks from (30 degrees above the horizon and up; the rest of `scene` may block the
    view), at a pose; hidden meshes and faces under the ground do not count."""
    verts, polys, which = [], [], []
    off = 0
    for n in scene:
        mesh = model.w3d.meshes[n]
        if not mesh.tris or not pose[1][model.vertex_bones(n)[0]]:
            continue
        V = model.world(n, pose)
        verts += [tuple(v) for v in V]
        polys += [tuple(off + i for i in t) for t in mesh.tris]
        which += [n in measured] * len(mesh.tris)
        off += len(V)
    if not polys:
        return 0.0
    bvh = BVHTree.FromPolygons(verts, polys, all_triangles=True)
    V = np.array(verts)
    seen = total = 0.0
    for t, mine in zip(polys, which):
        if not mine:
            continue
        a, b_, c = V[list(t)]
        n = np.cross(b_ - a, c - a)
        area = np.linalg.norm(n) / 2
        if area < 1e-6:
            continue
        n = Vector(n / (2 * area))
        cen = Vector((a + b_ + c) / 3)
        if cen.z < 0.0:
            continue                                # under the ground: nobody sees it
        total += area
        for d in dirs:
            if n.dot(d) < -0.05 and bvh.ray_cast(cen + d * 0.02, d, 5000.0)[0] is None and not covered(bvh, cen, d):
                seen += area
                if DEBUG is not None:
                    DEBUG.append((tuple(cen), area, tuple(n), tuple(d)))
                break
    return seen / max(total, 1e-9)
