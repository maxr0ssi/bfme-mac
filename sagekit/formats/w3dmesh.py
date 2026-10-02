"""New W3D meshes assembled from the vertices and triangles of existing ones (pure Python).

The lifecycle step (sagekit/lifecycle.py) splits our body into EA's pieces and moves EA's own break
faces between meshes. Every new mesh is a template mesh chunk (its materials, shader and texture
names, pass structure) filled with vertices taken from source meshes with compatible layouts:

    vertex = (source key, [(source vertex, weight)], 3x4 matrix, bone, {chunk id: value})

A vertex blends its sources' per-vertex data (a new vertex on an edge or inside a triangle keeps
the texture mapping exact), then the matrix takes its position, normal and tangent frame into the
new mesh's space (its bone's rest space). Overrides replace a blended value before the matrix.
Rigid meshes get a collision tree (BFME2 does not draw a mesh without one); skins get the header's
skin flag and bone channel, like EA's, and a VERTEX_INFLUENCES row per vertex: (bone, second bone,
weight, second weight), weights in percent. A vertex that is a source skin's vertex unchanged (one
source vertex, same bone and space, position and normal not overridden) keeps that row and its
second-bone position and normal (VERTICES_2 / NORMALS_2: EA stores a two-bone vertex in each bone's
space and blends the two) byte for byte; any other vertex is bound 100 % to its one bone. The
second-bone chunks are written, where EA has them, when some vertex has a second weight.
Source colour chunks absent from the template are unused; every required template slot must exist.
"""
import math
import struct

from .w3d import (AABTREE, BITANGENTS, MATERIAL_PASS, MESH, MESH_HEADER3, NORMALS, STAGE_TEXCOORDS, TANGENTS,
                  TRIANGLES, VERTEX_INFLUENCES, VERTICES, _cstr, build_aabtree, chunk_bytes, chunks)
from .w3dpose import IDENTITY, direction, point

VERTEX_SHADE_INDICES, USER_TEXT, DCG, DIG, SCG = 0x22, 0x0C, 0x3B, 0x3C, 0x3E
# per-vertex chunks: (bytes per vertex, struct format)
PER_VERTEX = {VERTICES: (12, "3f"), NORMALS: (12, "3f"), TANGENTS: (12, "3f"), BITANGENTS: (12, "3f"),
              VERTEX_INFLUENCES: (8, "4H"), VERTEX_SHADE_INDICES: (4, "I"), STAGE_TEXCOORDS: (8, "2f"),
              DCG: (4, "4B"), DIG: (4, "4B"), SCG: (4, "4B")}
FRAME = (NORMALS, TANGENTS, BITANGENTS)
PER_FACE_IDS = (0x39, 0x3A, 0x3F, 0x49)             # vertex material / shader / shader material / texture ids
SKIN_FLAG, BONEID_CHANNEL, GEOMETRY_TYPE = 0x00020000, 0x10, 0x00FF0000
DROPPED = (AABTREE, USER_TEXT, VERTEX_INFLUENCES)       # rebuilt, or not ours to carry
VERTICES_2, NORMALS_2 = 0xC00, 0xC01                    # a two-bone skin's vertices / normals in the second bone's space
SECONDARY = {VERTICES: VERTICES_2, NORMALS: NORMALS_2}


class Source:
    """A mesh chunk's per-vertex data, in depth-first chunk order, and its triangles."""

    def __init__(self, mesh_bytes):
        self.bytes = mesh_bytes
        self.layout = []                                # [(chunk id, [row tuple per vertex])]
        self.tris, self.surface = [], []
        self.skin, self.secondary = None, {}            # VERTEX_INFLUENCES rows; {VERTICES_2 / NORMALS_2: rows}
        self._walk(8, len(mesh_bytes))

    def _walk(self, a, b):
        d = self.bytes
        for t, o, s, h in chunks(d, a, b):
            if t == TRIANGLES:
                for i in range(s // 32):
                    row = struct.unpack_from("<4I", d, o + 8 + 32 * i)
                    self.tris.append(row[:3])
                    self.surface.append(row[3])
            elif t == VERTEX_INFLUENCES:
                self.skin = [struct.unpack_from("<4H", d, o + 8 + 8 * i) for i in range(s // 8)]
            elif t in (VERTICES_2, NORMALS_2):
                self.secondary[t] = [struct.unpack_from("<3f", d, o + 8 + 12 * i) for i in range(s // 12)]
            elif t in PER_VERTEX and t not in DROPPED:
                size, fmt = PER_VERTEX[t]
                self.layout.append((t, [struct.unpack_from("<" + fmt, d, o + 8 + size * i) for i in range(s // size)]))
            elif h and t != AABTREE and t < 0xC00:
                self._walk(o + 8, o + 8 + s)

    def signature(self):
        return [t for t, _ in self.layout]

    def influence(self, combo, matrix, bone, over):
        """(row, second-bone position, second-bone normal) of this skin's vertex when the new vertex is
        that vertex unchanged: one source vertex, the same bone and space, position and normal not
        overridden; else None. The second-bone values are None where the source has no such chunk."""
        if not self.skin or len(combo) != 1 or combo[0][1] != 1 or VERTICES in over or NORMALS in over:
            return None
        if [float(x) for x in matrix] != IDENTITY:
            return None
        i = combo[0][0]
        row = self.skin[i]
        if row[0] != bone or row[3] and len(self.secondary) < 2:
            return None
        return (row,) + tuple(self.secondary[t][i] if t in self.secondary else None for t in (VERTICES_2, NORMALS_2))

    def value(self, k, combo):
        """The k-th per-vertex chunk's value blended over [(vertex, weight)]."""
        t, rows = self.layout[k]
        if len(combo) == 1:
            return rows[combo[0][0]]
        vals = [sum(rows[v][c] * w for v, w in combo) for c in range(len(rows[combo[0][0]]))]
        return tuple(int(round(x)) for x in vals) if PER_VERTEX[t][1].endswith("B") else tuple(vals)


def build_mesh(template, sources, name, container, verts, tris, skinned, rest=None):
    """A MESH chunk: `template`'s materials with the given vertices and triangles.

    sources: {key: Source}, carrying every template slot; unused extra colour chunks are allowed.
    verts: [(key, [(vertex, weight)], matrix, bone, {chunk id: value})]
    tris: [((i, j, k), surface type)]
    rest: a skin's bones' rest matrices: its header box and sphere are measured in the model's
    space, where the skin stands at rest (EA's are), not in its vertices' bone spaces."""
    used = sorted({i for ids, _ in tris for i in ids})       # vertices no triangle uses are dropped
    if len(used) != len(verts):
        remap = {v: k for k, v in enumerate(used)}
        verts = [verts[v] for v in used]
        tris = [([remap[i] for i in ids], surface) for ids, surface in tris]
    tpl = Source(template)
    sig = tpl.signature()
    slots = {}
    for key, src in sources.items():
        kept = _slots(sig, src.signature())
        if kept is None:
            raise ValueError("%s: per-vertex layout %s differs from the template's %s" % (key, src.signature(), sig))
        slots[key] = kept
    values = []                                         # per new vertex: [value per layout slot]
    for key, combo, m, _, over in verts:
        row = []
        for k, (t, _) in enumerate(tpl.layout):
            v = over.get(t) if t in over else sources[key].value(slots[key][k], combo)
            if t == VERTICES:
                v = point(m, v)
            elif t in FRAME:
                v = direction(m, v)
                n = math.sqrt(sum(x * x for x in v)) or 1.0
                v = tuple(x / n for x in v)
            elif t == VERTEX_SHADE_INDICES:
                v = (len(values),)
            row.append(v)
        values.append(row)
    pos_slot = sig.index(VERTICES)
    pos = [row[pos_slot] for row in values]
    slot = iter(range(len(sig)))
    rows, second = _skin(sources, verts, values, sig) if skinned else ([], {})

    def secondary(t):
        return chunk_bytes(t, b"".join(struct.pack("<3f", *v) for v in second[t]), False)

    def per_vertex(t, h):
        k = next(slot)
        fmt = "<" + PER_VERTEX[t][1]
        return chunk_bytes(t, b"".join(struct.pack(fmt, *row[k]) for row in values), h)

    def walk(a, b):
        out = b""
        for t, o, s, h in chunks(template, a, b):
            if t in (VERTICES_2, NORMALS_2) and second:
                out += secondary(t)
            if t in DROPPED or t >= 0xC00:
                continue
            if t == MESH_HEADER3:
                box = [point(rest[v[3]], p) for v, p in zip(verts, pos)] if skinned and rest else pos
                out += _header(template[o:o + 8 + s], name, container, box, len(tris), skinned)
            elif t == TRIANGLES:
                out += chunk_bytes(t, b"".join(_triangle(pos, ids, surface) for ids, surface in tris), h)
                if skinned:
                    out += chunk_bytes(VERTEX_INFLUENCES, b"".join(struct.pack("<4H", *r) for r in rows), False)
            elif t in PER_VERTEX:
                out += per_vertex(t, h)
                if second and t in SECONDARY and SECONDARY[t] not in tpl.secondary:
                    out += secondary(SECONDARY[t])          # (EA's order: after the primary chunk)
            elif h and t == MATERIAL_PASS or h and _inside_pass(template, a):
                out += chunk_bytes(t, walk(o + 8, o + 8 + s), True)
            elif t in PER_FACE_IDS and s > 4:
                raise ValueError("%s: per-triangle material ids (0x%x) are not carried over" % (name, t))
            else:
                out += template[o:o + 8 + s]
        return out
    body = walk(8, len(template))
    if not skinned:
        body += build_aabtree(pos, [ids for ids, _ in tris])
    return chunk_bytes(MESH, body, True)


def _skin(sources, verts, values, sig):
    """([influence row per vertex], {VERTICES_2 / NORMALS_2: [value per vertex]}): a source skin's
    vertex carried unchanged keeps its row and second-bone values (Source.influence), any other is
    bound 100 % to its bone, its second-bone values its own; the second-bone chunks only when some
    vertex has a second weight."""
    rows, extra = [], []
    for (key, combo, m, bone, over), row in zip(verts, values):
        ea = sources[key].influence(combo, m, bone, over)
        rows.append(ea[0] if ea else (bone, 0, 100, 0))
        extra.append(ea[1:] if ea else (None, None))
    if not any(r[3] for r in rows):
        return rows, {}
    if NORMALS not in sig:
        raise ValueError("a two-bone skin without normals")
    own = [sig.index(VERTICES), sig.index(NORMALS)]
    second = {t: [e[k] if e[k] is not None else row[own[k]] for e, row in zip(extra, values)]
              for k, t in enumerate((VERTICES_2, NORMALS_2))}
    return rows, second


def _slots(sig, source_sig):
    """The source's per-vertex chunks filling the template's slots in order (extra colour chunks
    skipped), or None when a required slot is missing or out of order."""
    kept = [i for i, t in enumerate(source_sig) if t in sig or t not in (DCG, DIG, SCG)]
    return kept if [source_sig[i] for i in kept] == sig else None


def fits(template, source):
    """Whether build_mesh can fill mesh chunk `template` with vertices of mesh chunk `source`."""
    return _slots(Source(template).signature(), Source(source).signature()) is not None


def _inside_pass(template, a):
    """Whether offset a is inside a material pass (texture stages nest their texcoords)."""
    for t, o, s, _ in chunks(template, 8, len(template)):
        if t == MATERIAL_PASS and o + 8 <= a < o + 8 + s:
            return True
    return False


def _triangle(pos, ids, surface):
    p0, p1, p2 = (pos[i] for i in ids)
    e1, e2 = [p1[x] - p0[x] for x in range(3)], [p2[x] - p0[x] for x in range(3)]
    n = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]]
    ln = math.sqrt(sum(x * x for x in n)) or 1.0
    n = [x / ln for x in n]
    return struct.pack("<4I4f", *ids, surface, *n, sum(a * b for a, b in zip(n, p0)))


def _header(raw, name, container, verts, ntris, skinned):
    h = bytearray(raw)
    p = 8
    attrs, vch = struct.unpack_from("<I", h, p + 4)[0], struct.unpack_from("<I", h, p + 68)[0]
    attrs = (attrs & ~GEOMETRY_TYPE) | (SKIN_FLAG if skinned else 0)
    vch = vch | BONEID_CHANNEL if skinned else vch & ~BONEID_CHANNEL
    struct.pack_into("<I", h, p + 4, attrs)
    h[p + 8:p + 24] = name.upper().encode("latin-1")[:15].ljust(16, b"\0")
    h[p + 24:p + 40] = container.encode("latin-1")[:15].ljust(16, b"\0")
    struct.pack_into("<II", h, p + 40, ntris, len(verts))
    struct.pack_into("<I", h, p + 68, vch)
    lo = [min(v[i] for v in verts) for i in range(3)] if verts else [0.0] * 3
    hi = [max(v[i] for v in verts) for i in range(3)] if verts else [0.0] * 3
    c = [(a + b) / 2 for a, b in zip(lo, hi)]
    r = max((math.dist(c, v) for v in verts), default=0.0)
    struct.pack_into("<10f", h, p + 76, *lo, *hi, *c, r)
    return bytes(h)


def mesh_name(mesh_chunk):
    for t, o, _, _ in chunks(mesh_chunk, 8, len(mesh_chunk)):
        if t == MESH_HEADER3:
            return _cstr(mesh_chunk[o + 16:o + 32]).upper()
    return None


def renamed(mesh_chunk, name):
    """A mesh chunk under another mesh name (same size)."""
    c = bytearray(mesh_chunk)
    for t, o, _, _ in chunks(c, 8, len(c)):
        if t == MESH_HEADER3:
            c[o + 16:o + 32] = name.upper().encode("latin-1")[:15].ljust(16, b"\0")
    return bytes(c)


def replace_meshes(model, new):
    """model bytes with each mesh named in `new` ({MESH NAME: mesh chunk}) replaced; every other
    chunk byte-identical."""
    out = bytearray()
    for t, o, s, _ in chunks(model, 0, len(model)):
        name = mesh_name(model[o:o + 8 + s]) if t == MESH else None
        out += new[name] if name in new else model[o:o + 8 + s]
    return bytes(out)


def check_layouts():
    """Standalone regression: optional colour slots cannot shift UVs or hide required data."""
    def mesh(colour=False, normal=True, second_uv=True):
        body = chunk_bytes(MESH_HEADER3, bytes(116), False)
        body += chunk_bytes(VERTICES, struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0), False)
        if normal:
            body += chunk_bytes(NORMALS, struct.pack("<9f", *(0, 0, 1) * 3), False)
        body += chunk_bytes(TRIANGLES, _triangle([(0, 0, 0), (1, 0, 0), (0, 1, 0)], (0, 1, 2), 0), False)
        material = chunk_bytes(STAGE_TEXCOORDS, struct.pack("<6f", 0, 0, 1, 0, 0, 1), False)
        if colour:
            material += chunk_bytes(DCG, bytes((20, 40, 60, 255)) * 3, False)
        if second_uv:
            material += chunk_bytes(STAGE_TEXCOORDS, struct.pack("<6f", 2, 2, 3, 2, 2, 3), False)
        return chunk_bytes(MESH, body + chunk_bytes(MATERIAL_PASS, material, True), True)

    template = mesh()
    verts = [("source", [(i, 1.0)], IDENTITY, 0, {}) for i in range(3)]

    def build(tpl, source):
        return build_mesh(tpl, {"source": Source(source)}, "TEST", "TEST", verts, [((0, 1, 2), 0)], True)

    baseline = build(template, template)
    assert Source(baseline).layout == Source(template).layout
    assert build(template, mesh(colour=True)) == baseline
    coloured = mesh(colour=True)
    assert Source(build(coloured, coloured)).layout == Source(coloured).layout
    for tpl, source in ((coloured, template), (template, mesh(normal=False)),
                        (template, mesh(second_uv=False))):
        try:
            build(tpl, source)
        except ValueError as error:
            assert "per-vertex layout" in str(error)
        else:
            raise AssertionError("missing required vertex data was accepted")
    print("W3D layouts: matching output unchanged; extra colour skipped; required colour, normals and UVs guarded")


def check_skin():
    """Regression (sagekit validate): a skin's vertices carried unchanged keep their influence rows
    and second-bone chunks byte for byte; new or moved vertices are bound 100 % to their bone; a
    one-bone skin gets no second-bone chunks. -> [failure]."""
    tri = _triangle([(0, 0, 0), (1, 0, 0), (0, 1, 0)], (0, 1, 2), 0)
    rows = [(0, 0, 100, 0), (0, 1, 50, 50), (1, 0, 0, 100), (2, 3, 100, 0)]
    pos, pos2 = (0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0), (0, 0, 0, 2, 0, 0, 0, 3, 0, 4, 4, 0)

    def mesh(influences, second):
        body = chunk_bytes(MESH_HEADER3, bytes(116), False) + chunk_bytes(VERTICES, struct.pack("<12f", *pos), False)
        if second:
            body += chunk_bytes(VERTICES_2, struct.pack("<12f", *pos2), False)
        body += chunk_bytes(NORMALS, struct.pack("<12f", *(0, 0, 1) * 4), False)
        if second:
            body += chunk_bytes(NORMALS_2, struct.pack("<12f", *(0, 1, 0) * 4), False)
        body += chunk_bytes(TRIANGLES, tri * 2, False)
        body += chunk_bytes(VERTEX_INFLUENCES, b"".join(struct.pack("<4H", *r) for r in influences), False)
        uv = chunk_bytes(STAGE_TEXCOORDS, struct.pack("<8f", *(0, 0) * 4), False)
        return chunk_bytes(MESH, body + chunk_bytes(MATERIAL_PASS, uv, True), True)

    def raw(chunk, t):
        return next((chunk[o + 8:o + 8 + s] for u, o, s, _ in chunks(chunk, 8, len(chunk)) if u == t), None)
    fails = []
    ea = mesh(rows, True)
    moved = [1.0, 0, 0, 1, 0, 1.0, 0, 0, 0, 0, 1.0, 0]
    verts = [("ea", [(i, 1.0)], IDENTITY, rows[i][0], {}) for i in range(4)]
    verts += [("ea", [(1, 1.0)], moved, 0, {}), ("ea", [(0, 1.0)], IDENTITY, 2, {VERTICES: (5, 5, 5)})]
    tris = [((0, 1, 2), 0), ((3, 4, 5), 0)]
    new = build_mesh(ea, {"ea": Source(ea)}, "TEST", "TEST", verts, tris, True)
    for t, size in ((VERTEX_INFLUENCES, 8), (VERTICES_2, 12), (NORMALS_2, 12)):
        if (raw(new, t) or b"")[:4 * size] != raw(ea, t):
            fails.append("chunk 0x%x of EA's vertices not carried byte for byte" % t)
    got = Source(new)
    if got.skin[4:] != [(0, 0, 100, 0), (2, 0, 100, 0)]:
        fails.append("moved / new vertices not bound 100 %% to their bone: %s" % got.skin[4:])
    if got.secondary.get(VERTICES_2, [])[4:] != [(2.0, 0.0, 0.0), (5.0, 5.0, 5.0)]:
        fails.append("a one-bone vertex's second-bone position is not its own")
    one = mesh([(r[0], 0, 100, 0) for r in rows], False)
    single = build_mesh(one, {"ea": Source(one)}, "TEST", "TEST", verts[:4], [((0, 1, 2), 0), ((1, 2, 3), 0)], True)
    if raw(single, VERTEX_INFLUENCES) != raw(one, VERTEX_INFLUENCES) or Source(single).secondary:
        fails.append("a one-bone skin changed: %s" % Source(single).skin)
    return fails


if __name__ == "__main__":
    check_layouts()
    print("\n".join(check_skin()) or "W3D skins: EA's influences and second-bone chunks carried byte for byte")
