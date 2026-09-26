"""New W3D meshes assembled from the vertices and triangles of existing ones (pure Python).

The lifecycle step (sagekit/lifecycle.py) splits our body into EA's pieces and moves EA's own break
faces between meshes. Every new mesh is a template mesh chunk (its materials, shader and texture
names, pass structure) filled with vertices taken from source meshes of the same layout:

    vertex = (source key, [(source vertex, weight)], 3x4 matrix, bone, {chunk id: value})

A vertex blends its sources' per-vertex data (a new vertex on an edge or inside a triangle keeps
the texture mapping exact), then the matrix takes its position, normal and tangent frame into the
new mesh's space (its bone's rest space). Overrides replace a blended value before the matrix.
Rigid meshes get a collision tree (BFME2 does not draw a mesh without one); skins get one bone per
vertex (VERTEX_INFLUENCES, weight 100) and the header's skin flag and bone channel, like EA's.
"""
import math
import struct

from .w3d import (AABTREE, BITANGENTS, MATERIAL_PASS, MESH, MESH_HEADER3, NORMALS, STAGE_TEXCOORDS, TANGENTS,
                  TRIANGLES, VERTEX_INFLUENCES, VERTICES, _cstr, build_aabtree, chunk_bytes, chunks)
from .w3dpose import direction, point

VERTEX_SHADE_INDICES, USER_TEXT, DCG, DIG, SCG = 0x22, 0x0C, 0x3B, 0x3C, 0x3E
# per-vertex chunks: (bytes per vertex, struct format)
PER_VERTEX = {VERTICES: (12, "3f"), NORMALS: (12, "3f"), TANGENTS: (12, "3f"), BITANGENTS: (12, "3f"),
              VERTEX_INFLUENCES: (8, "4H"), VERTEX_SHADE_INDICES: (4, "I"), STAGE_TEXCOORDS: (8, "2f"),
              DCG: (4, "4B"), DIG: (4, "4B"), SCG: (4, "4B")}
FRAME = (NORMALS, TANGENTS, BITANGENTS)
PER_FACE_IDS = (0x39, 0x3A, 0x3F, 0x49)             # vertex material / shader / shader material / texture ids
SKIN_FLAG, BONEID_CHANNEL, GEOMETRY_TYPE = 0x00020000, 0x10, 0x00FF0000
DROPPED = (AABTREE, USER_TEXT, VERTEX_INFLUENCES)       # rebuilt, or not ours to carry


class Source:
    """A mesh chunk's per-vertex data, in depth-first chunk order, and its triangles."""

    def __init__(self, mesh_bytes):
        self.bytes = mesh_bytes
        self.layout = []                                # [(chunk id, [row tuple per vertex])]
        self.tris, self.surface = [], []
        self._walk(8, len(mesh_bytes))

    def _walk(self, a, b):
        d = self.bytes
        for t, o, s, h in chunks(d, a, b):
            if t == TRIANGLES:
                for i in range(s // 32):
                    row = struct.unpack_from("<4I", d, o + 8 + 32 * i)
                    self.tris.append(row[:3])
                    self.surface.append(row[3])
            elif t in PER_VERTEX and t not in DROPPED:
                size, fmt = PER_VERTEX[t]
                self.layout.append((t, [struct.unpack_from("<" + fmt, d, o + 8 + size * i) for i in range(s // size)]))
            elif h and t != AABTREE and t < 0xC00:
                self._walk(o + 8, o + 8 + s)

    def signature(self):
        return [t for t, _ in self.layout]

    def value(self, k, combo):
        """The k-th per-vertex chunk's value blended over [(vertex, weight)]."""
        t, rows = self.layout[k]
        if len(combo) == 1:
            return rows[combo[0][0]]
        vals = [sum(rows[v][c] * w for v, w in combo) for c in range(len(rows[combo[0][0]]))]
        return tuple(int(round(x)) for x in vals) if PER_VERTEX[t][1].endswith("B") else tuple(vals)


def build_mesh(template, sources, name, container, verts, tris, skinned, rest=None):
    """A MESH chunk: `template`'s materials with the given vertices and triangles.

    sources: {key: Source}, all with the template's per-vertex layout.
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
    for key, src in sources.items():
        if src.signature() != sig:
            raise ValueError("%s: per-vertex layout %s differs from the template's %s" % (key, src.signature(), sig))
    values = []                                         # per new vertex: [value per layout slot]
    for key, combo, m, _, over in verts:
        row = []
        for k, (t, _) in enumerate(tpl.layout):
            v = over.get(t) if t in over else sources[key].value(k, combo)
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

    def per_vertex(t, h):
        k = next(slot)
        fmt = "<" + PER_VERTEX[t][1]
        return chunk_bytes(t, b"".join(struct.pack(fmt, *row[k]) for row in values), h)

    def walk(a, b):
        out = b""
        for t, o, s, h in chunks(template, a, b):
            if t in DROPPED or t >= 0xC00:
                continue
            if t == MESH_HEADER3:
                box = [point(rest[v[3]], p) for v, p in zip(verts, pos)] if skinned and rest else pos
                out += _header(template[o:o + 8 + s], name, container, box, len(tris), skinned)
            elif t == TRIANGLES:
                out += chunk_bytes(t, b"".join(_triangle(pos, ids, surface) for ids, surface in tris), h)
                if skinned:
                    out += chunk_bytes(VERTEX_INFLUENCES, b"".join(struct.pack("<4H", v[3], 0, 100, 0)
                                                                     for v in verts), False)
            elif t in PER_VERTEX:
                out += per_vertex(t, h)
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
