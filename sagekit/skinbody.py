"""A skinned target: a building body the game animates (the Angmar mill's capstan and gear, the
forge works' bellows), redesigned like a rigid one while EA's bones, animations and skin weights stay
EA's byte for byte.

The pipeline's steps see the body as they see any other (pure Python, no numpy):
  - geometry: Blender's importer stands every skin vertex at rest in model space; the design is in
    those coordinates. New pieces stand still on the root unless the recipe makes them ride one of
    EA's bones (`Building.ride(solids, bone)`): each new vertex is bound 100 % to that one bone, so
    the piece moves rigidly with it (sagekit/blender/skintarget.py gives them vertex groups);
  - export: the body twice, as a skin (its vertex groups: which bone each new vertex rides) into
    work/export_skin/, and as a rigid mesh at rest into work/export/, which every later step reads
    (derive, lifecycle, night, checks, renders) as it reads a rigid body;
  - fixup: the shipped body is rebuilt from EA's mesh and the skin export (`rebuild`), with the units'
    mesh writer (sagekit/formats/w3dmesh.py): every one of EA's vertices our body keeps is EA's
    vertex unchanged (its position and normal in its bone's space, its VERTEX_INFLUENCES row and its
    second-bone position and normal) in EA's order, ahead of the rest, with our UVs and tangent
    frame; the new vertices follow, each on its one bone; triangles and materials as exported.
The checks (`checks`) hold the result to that, with sagekit/units/build.py's skin_kept.
"""
import math
import os

from .formats import w3dmesh as WM
from .formats import w3dpose as P
from .formats.w3d import BITANGENTS, STAGE_TEXCOORDS, TANGENTS, W3DFile, rename_textures

TOL = 2e-3                      # how far the exporter's float round trip moves one of EA's vertices


def export_skin(ws):
    """The skin export's path (the exporter names the container after the file)."""
    return ws.path("work", "export_skin", ws.container + ".w3d")


def skeleton(ws, data=None):
    """The source model's Skeleton (its separate skeleton file in src/), or None for a rigid model."""
    skl = W3DFile(data or open(ws.source_model, "rb").read()).skeleton()
    return P.Skeleton(open(os.path.join(ws.src, skl), "rb").read()) if skl else None


def skinned(ws):
    """Whether the building's target mesh in its source model is a skin."""
    if not os.path.exists(ws.source_model):
        return False
    m = W3DFile(ws.source_model).meshes.get(ws.b.target)
    return bool(m and m.skinned)


def _rest(mesh, sk, rows):
    """[(model-space position, model-space normal)] per vertex at rest, on each vertex's first bone."""
    out = []
    for v, n, r in zip(mesh.verts, mesh.normals, rows):
        m = sk.rest[r[0]]
        out.append((P.point(m, v), P.direction(m, n)))
    return out


class Rest:
    """A skinned mesh stood at rest in model space (verts, tris): what the rigid paths compare boxes
    with (Building.bodies_in, the derived-body checks)."""

    def __init__(self, mesh, sk):
        self.name, self.tris, self.skinned = mesh.name, mesh.tris, False
        self.verts = [p for p, _ in _rest(mesh, sk, P.skin(mesh.bytes)[0])]


def at_rest(mesh, sk):
    return Rest(mesh, sk) if mesh.skinned and sk else mesh


def _match(ea, ea_rest, k_rest, k_rows, order=None):
    """{K vertex: EA vertex} for the skin export's vertices that are EA's: at the same rest position;
    among EA's coincident vertices (its UV seams) the one of the same index (the exporter keeps the
    importer's order and appends what it splits), then on the same bone, then the nearest normal (the
    exporter's split normals differ from EA's by a few degrees), then one not yet taken. order:
    {"ea": EA's vertices in the mesh, "verts": all} at export: ours (between the two) are never EA's,
    a split one (past both) only on the same bone."""
    n_ea, n_all = (order or {}).get("ea", len(k_rest)), (order or {}).get("verts", len(k_rest))
    cell = {}
    for i, (p, _) in enumerate(ea_rest):
        cell.setdefault(tuple(int(math.floor(c / TOL)) for c in p), []).append(i)
    taken, out = set(), {}
    rows = P.skin(ea.bytes)[0]
    for j, (q, nq) in enumerate(k_rest):
        if n_ea <= j < n_all:
            continue
        base = [int(math.floor(c / TOL)) for c in q]
        cands = [i for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)
                 for i in cell.get((base[0] + dx, base[1] + dy, base[2] + dz), ())
                 if math.dist(ea_rest[i][0], q) <= TOL and (j < n_ea or rows[i][0] == k_rows[j][0])]
        if cands:
            cands.sort(key=lambda i: (i != j, rows[i][0] != k_rows[j][0],
                                      -sum(a * b for a, b in zip(ea_rest[i][1], nq)), i in taken, i))
            out[j] = cands[0]
            taken.add(cands[0])
    return out


def rebuild(orig, skin_fixed, target, sk, renames=(), order=None):
    """(the target's MESH chunk for the shipped model, report lines): EA's mesh `target` of model
    bytes `orig` rebuilt with the vertices and triangles of the fixed skin export `skin_fixed`."""
    ea, k = W3DFile(orig).meshes[target], W3DFile(skin_fixed).meshes[target]
    if not ea.skinned or not k.skinned:
        raise ValueError("%s: EA's body and its skin export must both be skins" % target)
    ea_rows, k_rows = P.skin(ea.bytes)[0], P.skin(k.bytes)[0]
    match = _match(ea, _rest(ea, sk, ea_rows), _rest(k, sk, k_rows), k_rows, order)
    tpl, src_k = WM.Source(ea.bytes), WM.Source(k.bytes)
    sig = tpl.signature()
    has_frame = TANGENTS in sig
    # EA's vertices first, in EA's order (each once: its first export copy), then the rest
    first = {}
    for j in sorted(match):
        first.setdefault(match[j], j)
    seq = [first[i] for i in sorted(first)] + [j for j in range(len(k.verts)) if first.get(match.get(j)) != j]
    where = {j: n for n, j in enumerate(seq)}
    kslots = {t: n for n, (t, _) in enumerate(src_k.layout)}
    verts, new_bones = [], set()
    for j in seq:
        if j in match:
            i = match[j]
            b = ea_rows[i][0]
            over = {STAGE_TEXCOORDS: k.uv[j]}
            if has_frame and TANGENTS in kslots:      # our UVs' tangent frame, in EA's bone's space
                to = P.mul(P.invert(sk.rest[b]), sk.rest[k_rows[j][0]])
                for t in (TANGENTS, BITANGENTS):
                    over[t] = P.direction(to, src_k.layout[kslots[t]][1][j])
            verts.append(("ea", [(i, 1)], P.IDENTITY, b, over))
        else:
            r = k_rows[j]
            if r[3] or r[2] != 100:
                raise ValueError("%s: new vertex %d is not on one bone at 100 %% (%s)" % (target, j, r))
            new_bones.add(r[0])
            verts.append(("k", [(j, 1)], P.IDENTITY, r[0], {}))
    tris = [(tuple(where[x] for x in t), s) for t, s in zip(k.tris, src_k.surface)]
    chunk = WM.build_mesh(ea.bytes, {"ea": tpl, "k": src_k}, target, ea.container, verts, tris, True, sk.rest, exact=True)
    chunk = rename_textures(chunk, [(None, a, b) for _, a, b in renames], target)
    kept, ours = len(first), sum(1 for j in seq if j not in match)
    report = ["%s: skin rebuilt: %d of EA's %d vertices kept as EA's (rows, second-bone data), %d copies of them "
              "(UV seams), %d of ours on %s" % (target, kept, len(ea.verts), len(seq) - kept - ours, ours,
                                                ", ".join(sk.names[b] for b in sorted(new_bones)) or "no bone")]
    return chunk, report


def checks(orig_mesh, new_mesh, sk, moving=()):
    """[(label, ok, detail)]: EA's vertices lead ours with EA's skin data byte for byte (units'
    skin_kept), every vertex of EA's on a moving bone is still there, every other vertex is on one
    bone at 100 %, bone indices in the skeleton. moving: bone indices an animation moves."""
    from .units.build import skin_kept
    (ea_rows, ea_two), (rows, two) = P.skin(orig_mesh.bytes), P.skin(new_mesh.bytes)
    kept, p = [], 0                         # EA's vertices our body keeps: in EA's order, at the front
    for i in range(len(orig_mesh.verts)):
        if p < len(rows) and _same(orig_mesh, new_mesh, i, p) and rows[p] == ea_rows[i] and \
                (not ea_rows[i][3] or ea_two is None or two is not None and two[p] == ea_two[i]):
            kept.append(i)
            p += 1
    detail = "%d of %d" % (p, len(orig_mesh.verts))
    ok = p > 0
    if ok and p == len(orig_mesh.verts):
        try:
            skin_kept(new_mesh.name, orig_mesh, new_mesh)      # the chunks' bytes themselves
            detail += ", chunks byte for byte"
        except AssertionError as e:
            ok, detail = False, str(e)
    out = [("%s: EA's vertices lead ours with EA's positions, normals, skin rows and second-bone data" % new_mesh.name,
            ok, detail)]
    keep = set(kept)
    lost = [i for i in range(len(orig_mesh.verts)) if i not in keep and
            (ea_rows[i][0] in moving or ea_rows[i][3] and ea_rows[i][1] in moving)]
    used = {r[k] for r in ea_rows for k in (0, 1) if r[k + 2]} & set(moving)
    out.append(("%s: every vertex of EA's on a moving bone kept (%s)" % (new_mesh.name, ", ".join(
        sk.names[b] for b in sorted(used)) or "none"), not lost, "%d missing" % len(lost)))
    ea_keys = {(orig_mesh.verts[i], orig_mesh.normals[i], ea_rows[i]) for i in range(len(orig_mesh.verts))}
    copies = [j for j in range(p, len(rows)) if (new_mesh.verts[j], new_mesh.normals[j], rows[j]) in ea_keys]
    extra = [rows[j] for j in range(p, len(rows)) if j not in set(copies)]
    out.append(("%s: the rest EA's vertices again (UV seams) or ours, each on one bone at 100 %%" % new_mesh.name,
                all(r[3] == 0 and r[2] == 100 for r in extra), "%d copies, %d of ours" % (len(copies), len(extra))))
    out.append(("%s: bone indices in the skeleton" % new_mesh.name,
                all(r[0] < len(sk.pivots) and r[1] < len(sk.pivots) for r in rows), "%d bones" % len(sk.pivots)))
    return out


def _same(a, b, i, j):
    return a.verts[i] == b.verts[j] and a.normals[i] == b.normals[j]


def moving_bones(anim, sk):
    """Bone indices an animation moves (any channel), with the bones below them."""
    keyed = {p for p, _ in anim.keys}
    out = set()
    for i, (_, parent, _, _) in enumerate(sk.pivots):
        if i in keyed or parent in out:
            out.add(i)
    return out


def skin_checks(b, ws, r, original, new):
    """The check suite's section for a skinned body (nothing for a rigid one): EA's vertices and skin
    data kept (`checks`) against the bones EA's animations move, and those animations' hierarchy."""
    if not skinned(ws):
        return
    from .game import Install
    from .skinanim import animations
    g = Install()
    sk = skeleton(ws, original.data)
    r.section("skinned body: EA's bones, animations and skin weights")
    moving = set()
    for name in animations(b, g):
        anim = P.Animation(g.read(g.model_path(name)))
        r.check("%s plays on %s" % (name, sk.name), anim.hierarchy.upper() == sk.name.upper() and anim.frames > 0,
                "%d frames" % anim.frames)
        moving |= moving_bones(anim, sk)
    for label, ok, detail in checks(original.meshes[b.target], new.meshes[b.target], sk, moving):
        r.check(label, ok, detail)
