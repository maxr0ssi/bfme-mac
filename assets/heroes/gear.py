"""Hero models: EA's model under our own name with gear of ours, drawn with the Create-a-Hero kit
(assets/cah/kit/geom.py Gear) and bound to EA's bones.

Three edits, each leaving every other chunk EA's byte for byte:
  replace  an EA mesh drawn anew (Dain's helmet, shield and axe become the Erebor kit);
  retex    an EA mesh kept, its texture name swapped for a recoloured private copy (same length);
  add      new skinned sub-objects after EA's last mesh, on bone 0 in the HLOD (Aragorn's level-8
           armour, hidden until its SubObjectsUpgrade shows it).
Then the click box (sagekit/units/pick.py): EA's BOUNDINGBOX, or one borrowed from the model the
hero draws today when EA's has none (Gamling), made oriented and grown to hold what we draw.

Rig: the Create-a-Hero designs are drawn in another model's rest space (the CaH dwarf's for the
Captain). A piece is stored in its bone's space of THAT rest pose and bound to the hero's bone of
the same name, so it sits on the hero as it sat on the design model, relative to the bone.
"""
import hashlib
import math
import struct

from sagekit.formats import w3dmesh as WM
from sagekit.formats import w3dpose as P
from sagekit.formats.w3d import BOX, HLOD, MESH, MESH_HEADER3, W3DFile, chunks, rename_model, rename_textures
from sagekit.units import pick

from assets.cah.kit.geom import Gear, add, cross, dot, mul, norm, sub
from assets.cah.kit.models import add_meshes, rename_mesh


def sha(b):
    return hashlib.sha256(b).hexdigest()


class Rig:
    """The hero's skeleton whose rest frames for `bones` are the design model's (same names)."""

    def __init__(self, target, design=None, bones=()):
        self.target, self.names, self.name = target, target.names, target.name
        self.rest = list(target.rest)
        self.pivots = target.pivots
        for b in bones:
            self.rest[target.index(b)] = design.rest[design.index(b)]

    def index(self, name):
        return self.target.index(name)


# ------------------------------------------------------------------ measuring EA's meshes
def rest_points(w, sk, name):
    m = w.meshes[name]
    infl = P.influences(m.bytes) if m.skinned else [P.hlod(w.data)[2].get(name.upper(), 0)] * len(m.verts)
    return [P.point(sk.rest[b], v) for v, b in zip(m.verts, infl)]


def centroid(pts):
    return [sum(p[k] for p in pts) / len(pts) for k in range(3)]


def principal(pts):
    """Axes of a point cloud, largest spread first (power iteration on the covariance)."""
    c = centroid(pts)
    C = [[sum((p[i] - c[i]) * (p[j] - c[j]) for p in pts) / len(pts) for j in range(3)] for i in range(3)]
    axes = []
    for _ in range(3):
        v = [1.0, .7, .3]
        for a in axes:
            v = sub(v, mul(a, dot(v, a)))
        for _ in range(200):
            v = [sum(C[i][j] * v[j] for j in range(3)) for i in range(3)]
            for a in axes:
                v = sub(v, mul(a, dot(v, a)))
            v = norm(v)
        axes.append(v)
    return c, axes


def frame_map(src, dst, scale=1.0):
    """p -> dst: the point with src-frame coordinates (scaled) placed in dst's frame. A frame is
    (origin, X, Y, Z), orthonormal."""
    (o0, X0, Y0, Z0), (o1, X1, Y1, Z1) = src, dst

    def f(p):
        d = sub(p, o0)
        a, b, c = dot(d, X0) * scale, dot(d, Y0) * scale, dot(d, Z0) * scale
        return tuple(add(add(add(o1, mul(X1, a)), mul(Y1, b)), mul(Z1, c)))
    return f


def frame(origin, z, y_hint):
    """An orthonormal frame with Z along `z` and Y as close to `y_hint` as possible."""
    Z = norm(z)
    Y = norm(sub(y_hint, mul(Z, dot(y_hint, Z))))
    return list(origin), cross(Y, Z), Y, Z


# ------------------------------------------------------------------ drawing
LODS = (1.0, .85, .7, .55, .45, .35)


def draw(original, skeleton, fn, sheet_from, sheet_to, place=None, bone_map=None, budget=None, remap=None):
    """One Gear mesh: `fn(gear)` drawn on EA's mesh `original`'s material (its texture renamed),
    trimmed (the kit's lod: fewer sides and samples, rivets dropped) until it fits `budget` vertices."""
    for lod in LODS:
        g = Gear(original, skeleton, {sheet_from: sheet_to}, place=place or (lambda p: tuple(p)), bone_map=bone_map,
                 lod=lod, remap=remap)
        fn(g)
        if budget is None or len(g.verts) <= budget:
            break
    if budget is not None and len(g.verts) > budget:
        raise SystemExit("heroes: %s: %d vertices at the lowest lod, over its %d" % (fn.__name__, len(g.verts), budget))
    if isinstance(skeleton, Rig):               # the header's box is measured on the hero's own rest pose
        g.skeleton = skeleton.target
    return g


def merge(first, *others):
    """One mesh of several Gears drawn on the same material (their vertices and triangles joined)."""
    for g in others:
        off = len(first.verts)
        first.verts += g.verts
        first.tris += [((a + off, b + off, c + off), s) for (a, b, c), s in g.tris]
    return first


def chunk_of(gear, name):
    return rename_mesh(gear.chunk(), name)


def contained(chunk, container):
    """A mesh chunk with its container name set: a Gear drawn on another model's mesh (Gamling's
    gear on RUGamling_SKN's) carries that model's, which rename_model leaves, so the HLOD's
    'MODEL.MESH' would name nothing in the file and the game would drop the mesh."""
    d = bytearray(chunk)
    for t, o, s, _ in chunks(d, 8, len(d)):
        if t == MESH_HEADER3:
            d[o + 32:o + 48] = container.encode().ljust(16, b"\0")
            return bytes(d)
    raise ValueError("no mesh header")


def borrowed_box(donor, container):
    """(BOUNDINGBOX, chunk) of `donor` (a model's bytes) named for `container`."""
    at = pick.boxes(donor)[pick.pick_box(donor)[0]][0] - 8
    c = bytearray(donor[at:at + 8 + (struct.unpack_from("<I", donor, at + 4)[0] & 0x7FFFFFFF)])
    c[16:48] = (container + ".BOUNDINGBOX").encode().ljust(32, b"\0")
    return "BOUNDINGBOX", bytes(c)


def assemble(ea_bytes, ea_name, ours, container, sk, replace=None, retex=None, extra=None, box_from=None):
    """Our model's bytes: EA's with meshes replaced ({mesh: chunk}), retextured ({mesh: [(old, new)]}),
    new meshes added ([(name, chunk)]), `box_from`'s BOUNDINGBOX added when EA's model has none,
    renamed `ours`, the click box covering the rest pose on skeleton `sk`."""
    w = W3DFile(ea_bytes)
    new = {n: contained(c, container) for n, c in (replace or {}).items()}
    for mesh, pairs in (retex or {}).items():
        for old, newname in pairs:
            if len(old) != len(newname):
                raise SystemExit("heroes: %s -> %s: a texture renamed in place keeps its length" % (old, newname))
        new[mesh] = rename_textures(w.meshes[mesh].bytes, [(None, o, n) for o, n in pairs], mesh)
        if new[mesh] == w.meshes[mesh].bytes:
            raise SystemExit("heroes: %s draws none of %s" % (mesh, pairs))
    data = WM.replace_meshes(ea_bytes, new)
    extra = [(n, contained(c, container)) for n, c in extra or []]
    if box_from is not None:
        if pick.pick_box(ea_bytes):
            raise SystemExit("heroes: %s has a BOUNDINGBOX of its own; borrow none" % ea_name)
        extra.append(borrowed_box(box_from, container))
    if extra:
        data = add_meshes(data, extra, container)
    data = pick.cover(rename_model(data, ea_name, ours), sk)
    if pick.unresolved(data):
        raise SystemExit("heroes: %s: HLOD sub-objects the file does not define: %s" % (ours, pick.unresolved(data)))
    return data


def check(ea_bytes, built, ea_name, ours, sk, anim, replaced=(), retexed=(), added=(), sheets=(), wrapped=(), clicked=None):
    """EA's chunks unchanged but ours (the click box's volume aside); new and replaced meshes skinned
    on the rig, drawing only our sheets, finite, and each vertex keeping its distance to its bone
    through EA's animation; the click box (pick.check) against `clicked`, the EA model the hero
    is clicked on today (EA's own by default)."""
    ea, w = W3DFile(rename_model(ea_bytes, ea_name, ours)), W3DFile(built)     # EA's as renamed (name fields keep EA's tail bytes)
    picking = pick.check(built, clicked or ea_bytes, sk)
    assert list(w.meshes) == list(ea.meshes) + list(added), list(w.meshes)
    for n, m in ea.meshes.items():
        got = w.meshes[n].bytes
        if n in replaced:
            continue
        if n in retexed:
            assert len(got) == len(m.bytes) and sum(a != b for a, b in zip(got, m.bytes)) <= 64, n
            continue
        assert got == m.bytes, "EA's %s changed" % n
    ours_chunks = {w.meshes[n].bytes for n in list(replaced) + list(added) + list(retexed)}
    borrowed = None if pick.pick_box(ea_bytes) else (picking["box"] or "").encode()
    keep = [pick.without_volume(t, c) for t, c in ea.top()
            if t not in (HLOD,) and not (t == MESH and WM.mesh_name(c) in set(replaced) | set(retexed))]
    have = [pick.without_volume(t, c) for t, c in w.top() if t not in (HLOD,) and not (t == MESH and c in ours_chunks)
            and not (t == BOX and borrowed and c[16:48].rstrip(b"\0").upper() == borrowed)]
    assert keep == have, "an EA chunk changed"
    if not added and not borrowed:
        assert [c for t, c in ea.top() if t == HLOD] == [c for t, c in w.top() if t == HLOD], "HLOD changed"
    _, hier, bones = P.hlod(built)
    assert hier.upper() == sk.name.upper(), hier
    rest, worst, verts = sk.pose(None, 0), 0.0, 0
    lowsheets = {s.lower() for s in sheets}
    for n in list(replaced) + list(added):
        g = w.meshes[n]
        infl = P.influences(g.bytes)
        assert g.skinned and len(infl) == len(g.verts) and all(0 <= b < len(sk.names) for b in infl), n
        assert {t.lower() for t in g.textures} <= lowsheets, (n, g.textures)
        assert all(math.isfinite(x) for v in g.verts for x in v), n
        if n not in wrapped:                    # `wrapped`: EA's own tiling UVs on a copy of EA's sheet
            assert all(0 <= x <= 1 for uv in g.uv for x in uv), "%s: UVs outside the sheet" % n
        verts += len(g.verts)
        for f in range(0, anim.frames, max(1, anim.frames // 8)):
            pose = sk.pose(anim, f)
            for v, b in zip(g.verts[::7], infl[::7]):
                p, r = P.point(pose[0][b], v), P.point(rest[0][b], v)
                assert all(math.isfinite(x) for x in p)
                d1 = math.dist(p, [pose[0][b][3], pose[0][b][7], pose[0][b][11]])
                d0 = math.dist(r, [rest[0][b][3], rest[0][b][7], rest[0][b][11]])
                worst = max(worst, abs(d1 - d0))
    assert worst < 1e-3, worst
    return dict(ea_sha256=sha(ea_bytes), sha256=sha(built), ea_bytes=len(ea_bytes), bytes=len(built),
                new_vertices=verts, max_bone_drift=worst, meshes=list(w.meshes), picking=picking)


def mesh_flags(chunk):
    for t, o, s, _ in chunks(chunk, 8, len(chunk)):
        if t == MESH_HEADER3:
            return struct.unpack_from("<I", chunk, o + 12)[0]
    return None


# ------------------------------------------------------------------ plates on EA's own surface
def surface_plate(g, w, sk, mesh, keep, tag, offset, axes=None):
    """A plate that follows EA's surface: the triangles of EA's `mesh` that pass keep(centroid in
    the rest pose, the bone names of its vertices), copied into Gear `g` and lifted `offset` along EA's normals
    (coincident vertices share one averaged normal, so the plate does not crack at EA's UV seams),
    each vertex on EA's bone; planar UVs into tile `tag` over the plate's two widest axes (or `axes`),
    or with tag None EA's own UVs (the plate drawn with a copy of EA's sheet).
    Returns the plate's boundary loops [(rest-space point, bone name)], for rims (rim())."""
    from sagekit.formats.w3d import NORMALS, STAGE_TEXCOORDS, VERTICES
    m = w.meshes[mesh]
    infl = P.influences(m.bytes) if m.skinned else [P.hlod(w.data)[2].get(mesh.upper(), 0)] * len(m.verts)
    pts = [P.point(sk.rest[b], v) for v, b in zip(m.verts, infl)]
    nrm = [norm(P.direction(sk.rest[b], n)) for n, b in zip(m.normals, infl)]
    tris = [t for t in m.tris if keep(centroid([pts[i] for i in t]), {sk.names[infl[i]] for i in t})]
    if not tris:
        raise SystemExit("heroes: no triangle of %s passes the plate's test" % mesh)
    key = lambda i: tuple(round(x, 3) for x in pts[i])
    shared = {}
    for t in tris:
        for i in t:
            shared.setdefault(key(i), []).append(nrm[i])
    smooth = {k: norm([sum(n[c] for n in ns) for c in range(3)]) for k, ns in shared.items()}
    used = sorted({i for t in tris for i in t})
    c, ax = principal([pts[i] for i in used])
    ax = axes or ax
    span = [(min(dot(sub(pts[i], c), a) for i in used), max(dot(sub(pts[i], c), a) for i in used)) for a in ax[:2]]
    index, surf = {}, g.original.surface[0]
    for i in used:
        n = smooth[key(i)]
        q = add(pts[i], mul(n, offset))
        u, v = ((dot(sub(pts[i], c), a) - lo) / max(hi - lo, 1e-6) for a, (lo, hi) in zip(ax[:2], span))
        b = infl[i]
        index[i] = len(g.verts)
        uv = tuple(m.uv[i]) if tag is None else g.uv_for(tag, u, v)     # None: EA's own UVs on EA's sheet
        g.verts.append((0, [(0, 1)], P.invert(g.skeleton.rest[b]), b,
                        {VERTICES: tuple(q), NORMALS: tuple(n), STAGE_TEXCOORDS: uv}))
    g.tris += [((index[a], index[b_], index[c_]), surf) for a, b_, c_ in tris]
    # boundary loops, by position (EA's seams split vertices that stand together)
    count = {}
    for t in tris:
        for a, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            e = tuple(sorted((key(a), key(b_))))
            count[e] = count.get(e, 0) + 1
    where = {key(i): (add(pts[i], mul(smooth[key(i)], offset)), sk.names[infl[i]]) for i in used}
    edges = [e for e, k in count.items() if k == 1]
    nxt = {}
    for a, b_ in edges:
        nxt.setdefault(a, []).append(b_)
        nxt.setdefault(b_, []).append(a)
    loops, seen = [], set()
    for a, _ in edges:
        if a in seen:
            continue
        loop, cur, prev = [a], a, None
        seen.add(a)
        while True:
            opts = [x for x in nxt[cur] if x != prev and x not in seen]
            if not opts:
                break
            prev, cur = cur, opts[0]
            loop.append(cur)
            seen.add(cur)
        if len(loop) > 2:
            loops.append([where[k] for k in loop] + [where[loop[0]]])
    return loops


def rim(g, loop, r, tag, sides=5):
    """A rolled rim along a plate's boundary loop, each run of it on the bone its vertices ride
    (runs share their end points, so the rim has no gap where the bone changes)."""
    runs, cur = [], [loop[0]]
    for p in loop[1:]:
        if p[1] != cur[-1][1]:
            cur.append((p[0], cur[-1][1]))
            runs.append(cur)
            cur = [p]
        else:
            cur.append(p)
    runs.append(cur)
    for run in runs:
        if len(run) >= 2:
            g.sweep([list(p) for p, _ in run], [r] * len(run), tag, run[0][1], sides=sides, cap=False)
