"""W3D models: read what the game reads, and repair what Blender's exporter drops.

Reading - `W3DFile(path)`: top-level chunks, per-mesh geometry / UVs / tangent frame / texture
names straight from the bytes, the object names the asset cache files them under, and the
cache entries (name, tag, offset, size) for asset.dat.

Repairing - `fix(original, exported, renames)`. Measured on the Dwarven fortress, the OpenSAGE
Blender add-on (io_mesh_w3d 0.7.x) keeps meshes, counts, bones and flags, but:
  - drops `BumpScale` from NormalMapped.fx shader materials, sets SpecularColor alpha to 1.0
    -> the original SHADER_MATERIALS chunk is copied back per mesh when its material count holds;
  - renames legacy-material textures to the file it loaded (.tga -> .dds) and adds TEXTURE_INFO
    -> TEXTURES, SHADERS and VERTEX_MATERIALS copied back per mesh when the counts match;
  - writes HIERARCHY without the sub-chunk bit and without PIVOT_FIXUPS -> both restored;
  - writes mesh headers as version 4.2 (Generals; BFME2's are 5.0 and 4.2 does not render) and
    tags every triangle surface type 13 -> version and surface types copied back;
  - drops AABTREE chunks, which BFME2 needs (Generals rebuilt them; BFME2 does not render a mesh
    without one) -> generated like WW3D2's AABTreeBuilderClass.
Anything it cannot match is reported, not guessed. `renames` points restored materials at a
building's own texture: (mesh or None, old, new), names of equal length so no chunk size moves.
"""
import struct

SUB = 0x80000000

# chunk ids (w3d_file.h)
MESH, VERTICES, NORMALS, MESH_HEADER3, TRIANGLES = 0x00, 0x02, 0x03, 0x1F, 0x20
VERTEX_INFLUENCES = 0x0E
SHADERS, VERTEX_MATERIALS, TEXTURES, MATERIAL_PASS = 0x29, 0x2A, 0x30, 0x38
TEXTURE_STAGE, STAGE_TEXCOORDS, SHADER_MATERIALS = 0x48, 0x4A, 0x50
MATERIAL_INFO, VERTEX_MATERIAL_IDS, SHADER_IDS, TEXTURE_IDS = 0x28, 0x39, 0x3A, 0x49
TANGENTS, BITANGENTS, AABTREE = 0x60, 0x61, 0x90
AABTREE_HEADER, AABTREE_POLYINDICES, AABTREE_NODES = 0x91, 0x92, 0x93
HIERARCHY, HIERARCHY_HEADER, PIVOTS, PIVOT_FIXUPS = 0x100, 0x101, 0x102, 0x103
HLOD, HLOD_HEADER, HLOD_SUB_OBJECT = 0x700, 0x701, 0x704
ANIMATION, ANIMATION_HEADER, COMPRESSED_ANIMATION, COMPRESSED_ANIMATION_HEADER = 0x200, 0x201, 0x280, 0x281
BOX = 0x740

LEGACY = {SHADERS: "shaders", VERTEX_MATERIALS: "vertex materials", TEXTURES: "textures"}
# asset.dat tags per top-level chunk (stored byte-reversed in the file)
CACHE_TAGS = {HIERARCHY: b"HIER", MESH: b"MESH", HLOD: b"HLOD", ANIMATION: b"ANIM",
              COMPRESSED_ANIMATION: b"ANIM", BOX: b"\0BOX"}


def chunks(d, off, end):
    """(type, offset, payload size, has sub-chunks) for each chunk in d[off:end]."""
    while off + 8 <= end:
        t, s = struct.unpack_from("<II", d, off)
        yield t, off, s & 0x7FFFFFFF, bool(s & SUB)
        off += 8 + (s & 0x7FFFFFFF)


def sub(d, o, s, want):
    """[(offset, size)] of the `want` sub-chunks of the chunk at o."""
    return [(o2, s2) for t, o2, s2, _ in chunks(d, o + 8, o + 8 + s) if t == want]


def chunk_bytes(t, payload, has_sub):
    return struct.pack("<II", t, len(payload) | (SUB if has_sub else 0)) + payload


def _cstr(b):
    return b.split(b"\0")[0].decode("latin-1")


def _vectors(d, o, s, n):
    return [struct.unpack_from("<%df" % n, d, o + 8 + 4 * n * i) for i in range(s // (4 * n))]


class Mesh:
    """One MESH chunk as the game sees it."""

    def __init__(self, data, offset, size):
        self.bytes = data[offset:offset + 8 + size]
        self.offset = offset
        self.uv = None
        self.verts = self.normals = self.tangents = self.bitangents = self.tris = self.surface = []
        d = data
        for t, o, s, _ in chunks(d, offset + 8, offset + 8 + size):
            if t == MESH_HEADER3:
                self.version = struct.unpack_from("<I", d, o + 8)[0]
                self.name = _cstr(d[o + 16:o + 32]).upper()
                self.container = _cstr(d[o + 32:o + 48])
            elif t == VERTICES:
                self.verts = _vectors(d, o, s, 3)
            elif t == NORMALS:
                self.normals = _vectors(d, o, s, 3)
            elif t == TANGENTS:
                self.tangents = _vectors(d, o, s, 3)
            elif t == BITANGENTS:
                self.bitangents = _vectors(d, o, s, 3)
            elif t == TRIANGLES:
                self.tris = [struct.unpack_from("<3I", d, o + 8 + 32 * i) for i in range(s // 32)]
                self.surface = [struct.unpack_from("<I", d, o + 8 + 32 * i + 12)[0] for i in range(s // 32)]
            elif t == MATERIAL_PASS and self.uv is None:
                self.uv = self._first_texcoords(d, o, s)
        self.textures = sorted(set(texture_names(self.bytes)))
        self.skinned = any(t == VERTEX_INFLUENCES for t, _, _, _ in chunks(d, offset + 8, offset + 8 + size))

    @staticmethod
    def _first_texcoords(d, o, s):
        for t, o2, s2, _ in chunks(d, o + 8, o + 8 + s):
            if t == STAGE_TEXCOORDS:
                return _vectors(d, o2, s2, 2)
            if t == TEXTURE_STAGE:
                for t3, o3, s3, _ in chunks(d, o2 + 8, o2 + 8 + s2):
                    if t3 == STAGE_TEXCOORDS:
                        return _vectors(d, o3, s3, 2)
        return None

    def material_passes(self):
        return [c for c in chunks(self.bytes, 8, len(self.bytes)) if c[0] == MATERIAL_PASS]


def texture_names(b):
    import re
    return [x.decode("latin-1") for x in re.findall(rb"[A-Za-z0-9_]+\.(?:tga|dds)", b, re.I)]


class W3DFile:
    def __init__(self, path_or_bytes):
        if isinstance(path_or_bytes, (bytes, bytearray)):
            self.data = bytes(path_or_bytes)
        else:
            with open(path_or_bytes, "rb") as fh:
                self.data = fh.read()
        self._meshes = None

    def top(self):
        """[(type, chunk bytes)] of the top-level chunks, in file order."""
        return [(t, self.data[o:o + 8 + s]) for t, o, s, _ in chunks(self.data, 0, len(self.data))]

    @property
    def meshes(self):
        """{MESH NAME: Mesh}"""
        if self._meshes is None:
            self._meshes = {}
            for t, o, s, _ in chunks(self.data, 0, len(self.data)):
                if t == MESH:
                    m = Mesh(self.data, o, s)
                    self._meshes[m.name] = m
        return self._meshes

    def cache_entries(self):
        """[(entry name, tag, offset, size)] as asset.dat files this model: hierarchy 'H*name',
        meshes 'CONTAINER.MESH', the HLOD by name, animations 'A*HIERARCHY.NAME', collision boxes
        by name; tags byte-reversed like the cache stores them."""
        d, out = self.data, []
        for t, o, s, _ in chunks(d, 0, len(d)):
            if t not in CACHE_TAGS:
                continue
            name = None
            if t == BOX:                                        # no sub-chunks: version, flags, name[32]
                out.append((_cstr(d[o + 16:o + 48]), CACHE_TAGS[t][::-1], o, 8 + s))
                continue
            for t2, o2, s2, _ in chunks(d, o + 8, o + 8 + s):   # the first sub-chunk is the header
                if t == HIERARCHY and t2 == HIERARCHY_HEADER:
                    name = "H*" + _cstr(d[o2 + 12:o2 + 28])
                elif t == MESH and t2 == MESH_HEADER3:
                    box, mesh = _cstr(d[o2 + 32:o2 + 48]), _cstr(d[o2 + 16:o2 + 32])
                    name = "%s.%s" % (box, mesh) if box else mesh     # a lone mesh: GBFITOWER, as the cache has it
                elif t == HLOD and t2 == HLOD_HEADER:
                    name = _cstr(d[o2 + 16:o2 + 32])
                elif (t, t2) in ((ANIMATION, ANIMATION_HEADER), (COMPRESSED_ANIMATION, COMPRESSED_ANIMATION_HEADER)):
                    name = "A*%s.%s" % (_cstr(d[o2 + 28:o2 + 44]), _cstr(d[o2 + 12:o2 + 28]))
                if name:
                    break
            out.append((name, CACHE_TAGS[t][::-1], o, 8 + s))
        return out

    def skeleton(self):
        """The separate skeleton file ('dbarchrnge_skl.w3d') a skinned model's HLOD names, or None
        when the model carries its own hierarchy."""
        d = self.data
        top = list(chunks(d, 0, len(d)))
        if any(t == HIERARCHY for t, _, _, _ in top):
            return None
        for t, o, s, _ in top:
            if t == HLOD:
                for t2, o2, _, _ in chunks(d, o + 8, o + 8 + s):
                    if t2 == HLOD_HEADER:
                        model, hier = _cstr(d[o2 + 16:o2 + 32]), _cstr(d[o2 + 32:o2 + 48])
                        return hier.lower() + ".w3d" if hier and hier.lower() != model.lower() else None
        return None

    def object_names(self):
        """Hierarchy, container.mesh and HLOD names in file order ('H:x', 'C.M', 'L:x')."""
        out = []
        for name, tag, _, _ in self.cache_entries():
            out.append({b"REIH": "H:" + name[2:], b"HSEM": name, b"DOLH": "L:" + (name or ""),
                        b"MINA": name, b"XOB\0": "B:" + (name or "")}[tag])
        return out


# ------------------------------------------------------------------------------------ fix-up
def _surface_types(d, o, s):
    tri = sub(d, o, s, TRIANGLES)
    if not tri:
        return []
    to, ts = tri[0]
    return [struct.unpack_from("<I", d, to + 8 + 32 * i + 12)[0] for i in range(ts // 32)]


def _count(d, o, s):
    return len(list(chunks(d, o + 8, o + 8 + s)))


def _mesh_name(d, o, s):
    for t, o2, _, _ in chunks(d, o + 8, o + 8 + s):
        if t == MESH_HEADER3:
            return _cstr(d[o2 + 16:o2 + 32]).upper()
    return None


def build_aabtree(verts, tris, leaf_max=4):
    """An AABTREE chunk laid out like WW3D2's AABTreeBuilderClass::Export: leaves hold at most
    MIN_POLYS_PER_NODE (4) polys, nodes are numbered root-first depth-first, a leaf's FrontOrPoly0
    is (first poly-index slot | 0x80000000) and BackOrPolyCount its count."""
    boxes = []
    for a, b, c in tris:
        pts = (verts[a], verts[b], verts[c])
        boxes.append(([min(p[k] for p in pts) for k in range(3)], [max(p[k] for p in pts) for k in range(3)]))
    nodes, poly_out = [], []

    def build(polys):
        idx = len(nodes)
        nodes.append(None)
        lo = [min(boxes[p][0][k] for p in polys) for k in range(3)]
        hi = [max(boxes[p][1][k] for p in polys) for k in range(3)]
        if len(polys) <= leaf_max:
            nodes[idx] = (lo, hi, len(poly_out) | 0x80000000, len(polys))
            poly_out.extend(polys)
            return idx
        # split on the longest axis of the centroid spread, at the median
        cen = {p: [(boxes[p][0][k] + boxes[p][1][k]) / 2 for k in range(3)] for p in polys}
        spread = [max(cen[p][k] for p in polys) - min(cen[p][k] for p in polys) for k in range(3)]
        axis = spread.index(max(spread))
        polys = sorted(polys, key=lambda p: cen[p][axis])
        mid = len(polys) // 2
        front = build(polys[:mid])
        back = build(polys[mid:])
        nodes[idx] = (lo, hi, front, back)
        return idx

    build(list(range(len(tris))))
    header = struct.pack("<II6I", len(nodes), len(poly_out), 0, 0, 0, 0, 0, 0)
    indices = struct.pack("<%dI" % len(poly_out), *poly_out)
    body = b"".join(struct.pack("<3f3fII", *lo, *hi, a, b) for lo, hi, a, b in nodes)
    payload = (chunk_bytes(AABTREE_HEADER, header, False) + chunk_bytes(AABTREE_POLYINDICES, indices, False)
               + chunk_bytes(AABTREE_NODES, body, False))
    return chunk_bytes(AABTREE, payload, True)


def rename_textures(raw, renames, mesh):
    """raw with the texture names in renames swapped for this mesh (case-insensitive, same length)."""
    for only, old, new in renames:
        if only and only.upper() != mesh:
            continue
        low, key = raw.lower(), old.lower().encode("latin-1")
        at = low.find(key)
        while at >= 0:
            raw = raw[:at] + new.encode("latin-1") + raw[at + len(key):]
            at = low.find(key, at + len(key))
    return raw



def _as_legacy(new, t2, o2, s2, raw, legacy, info, vch, renames, name):
    """One sub-chunk of an exported shader-material mesh, rewritten for the original's single-pass
    material: tangents dropped, the original's material info / vertex material / shader / textures
    (renamed) in place of the shader material, a full pass (ids + our UVs). None drops the chunk."""
    if t2 in (TANGENTS, BITANGENTS):
        return None
    if t2 == MESH_HEADER3 and vch:
        return raw[:8 + 68] + vch + raw[8 + 72:]
    if t2 == MATERIAL_INFO and info:
        return info
    if t2 == SHADER_MATERIALS:
        textures = legacy[TEXTURES]
        if renames:
            textures = rename_textures(textures, renames, name)
        return legacy.get(VERTEX_MATERIALS, b"") + legacy.get(SHADERS, b"") + textures
    if t2 == MATERIAL_PASS:
        uv = b"".join(new[p:p + 8 + q] for p, q in sub(new, o2, s2, STAGE_TEXCOORDS))
        zero = struct.pack("<I", 0)
        stage = chunk_bytes(TEXTURE_IDS, zero, False) + uv
        return chunk_bytes(MATERIAL_PASS, chunk_bytes(VERTEX_MATERIAL_IDS, zero, False) + chunk_bytes(SHADER_IDS, zero, False)
                           + chunk_bytes(TEXTURE_STAGE, stage, True), True)
    return raw

def fix(orig, new, renames=()):
    """(fixed bytes, report lines) for an exported model, using the original as the reference."""
    for _, old, new_name in renames:
        if len(old) != len(new_name):
            raise ValueError("rename %s=%s: names must have the same length" % (old, new_name))
    report = []
    o_mats, o_fix, o_pivots, o_ver, o_surf, o_legacy = {}, None, None, {}, {}, {}
    o_info, o_vch = {}, {}
    for t, o, s, _ in chunks(orig, 0, len(orig)):
        if t == MESH:
            name = _mesh_name(orig, o, s)
            sm = sub(orig, o, s, SHADER_MATERIALS)
            if sm:
                o_mats[name] = orig[sm[0][0]:sm[0][0] + 8 + sm[0][1]]
            hd = sub(orig, o, s, MESH_HEADER3)
            if hd:
                o_ver[name] = orig[hd[0][0] + 8:hd[0][0] + 12]
                o_vch[name] = orig[hd[0][0] + 8 + 68:hd[0][0] + 8 + 72]
            mi = sub(orig, o, s, MATERIAL_INFO)
            if mi:
                o_info[name] = orig[mi[0][0]:mi[0][0] + 8 + mi[0][1]]
            o_surf[name] = _surface_types(orig, o, s)
            o_legacy[name] = {k: orig[p:p + 8 + q] for k in LEGACY for p, q in sub(orig, o, s, k)[:1]}
        elif t == HIERARCHY:
            fx = sub(orig, o, s, PIVOT_FIXUPS)
            pv = sub(orig, o, s, PIVOTS)
            o_fix = orig[fx[0][0]:fx[0][0] + 8 + fx[0][1]] if fx else None
            o_pivots = pv[0][1] if pv else None

    out = bytearray()
    for t, o, s, has_sub in chunks(new, 0, len(new)):
        if t == MESH:
            name = _mesh_name(new, o, s)
            parts = bytearray()
            # the original draws this mesh with the older single-pass material (no shader material)
            # while the export carries a shader material: rebuild it in the original's format
            to_legacy = name not in o_mats and TEXTURES in o_legacy.get(name, {}) and bool(sub(new, o, s, SHADER_MATERIALS))
            if to_legacy:
                report.append("%s: shader material converted to the original's single-pass material" % name)
            for t2, o2, s2, h2 in chunks(new, o + 8, o + 8 + s):
                raw = new[o2:o2 + 8 + s2]
                if to_legacy:
                    raw = _as_legacy(new, t2, o2, s2, raw, o_legacy[name], o_info.get(name), o_vch.get(name),
                                     renames, name)
                    if raw is None:
                        continue
                if t2 == MESH_HEADER3 and name in o_ver and raw[8:12] != o_ver[name]:
                    raw = raw[:8] + o_ver[name] + raw[12:]
                    report.append("%s: mesh header version restored (%s)" % (name, o_ver[name][::-1].hex()))
                elif t2 == TRIANGLES and o_surf.get(name):
                    tris = bytearray(raw)
                    n = s2 // 32
                    same = len(o_surf[name]) == n
                    common = max(set(o_surf[name]), key=o_surf[name].count)
                    for i in range(n):
                        struct.pack_into("<I", tris, 8 + 32 * i + 12, o_surf[name][i] if same else common)
                    raw = bytes(tris)
                    report.append("%s: triangle surface types restored (%s)" % (name, "per triangle" if same else "as %d" % common))
                if t2 in LEGACY and name in o_legacy and t2 in o_legacy[name]:
                    old = o_legacy[name][t2]
                    same_count = (len(old) == len(raw)) if t2 == SHADERS else \
                        _count(new, o2, s2) == _count(old, 0, len(old) - 8)
                    if same_count and old != raw:
                        raw = old
                        report.append("%s: %s restored from original" % (name, LEGACY[t2]))
                    if t2 == TEXTURES and renames:
                        raw = rename_textures(raw, renames, name)
                if t2 == SHADER_MATERIALS and name in o_mats and \
                        _count(new, o2, s2) == _count(o_mats[name], 0, len(o_mats[name]) - 8):
                    raw = rename_textures(o_mats[name], renames, name)
                    report.append("%s: shader materials restored from original%s" % (name, " (renamed)" if raw != o_mats[name] else ""))
                elif t2 == SHADER_MATERIALS and not to_legacy:
                    report.append("%s: shader materials NOT restored (no matching mesh/material count)" % name)
                parts += raw
            if not sub(new, o, s, AABTREE):
                m = Mesh(new, o, s)
                parts += build_aabtree(m.verts, m.tris)
                report.append("%s: collision tree generated (%d triangles)" % (name, len(m.tris)))
            out += chunk_bytes(t, bytes(parts), True)
        elif t == HIERARCHY:
            kids = list(chunks(new, o + 8, o + 8 + s))
            parts = b"".join(new[o2:o2 + 8 + s2] for _, o2, s2, _ in kids)
            pv = [s2 for t2, _, s2, _ in kids if t2 == PIVOTS]
            if o_fix and not any(t2 == PIVOT_FIXUPS for t2, _, _, _ in kids) and pv and pv[0] == o_pivots:
                parts += o_fix
                report.append("hierarchy: pivot fixups restored")
            out += chunk_bytes(t, parts, True)
            report.append("hierarchy: sub-chunk flag set")
        else:
            out += new[o:o + 8 + s]
    return bytes(out), report


def splice_mesh(model, mesh_name, mesh_chunk, container):
    """model bytes with its mesh `mesh_name` replaced by mesh_chunk (another file's), the chunk's
    container name set to `container` - every other chunk byte-identical."""
    out = bytearray()
    done = False
    for t, o, s, _ in chunks(model, 0, len(model)):
        if t == MESH and _mesh_name(model, o, s) == mesh_name.upper():
            c = bytearray(mesh_chunk)
            for t2, o2, s2, _ in chunks(c, 8, len(c)):
                if t2 == MESH_HEADER3:
                    c[o2 + 32:o2 + 48] = container.encode("latin-1")[:15].ljust(16, b"\0")
                    break
            out += c
            done = True
        else:
            out += model[o:o + 8 + s]
    if not done:
        raise ValueError("no mesh %s to replace" % mesh_name)
    return bytes(out)


def rename_model(data, old, new):
    """The model's own name changed in every fixed-width field that carries it: the hierarchy, each
    mesh's container, the HLOD's model and hierarchy names and its sub-objects ('OLD.MESH'), and an
    embedded animation's name and hierarchy. For a copy of a model under another file name (the
    file name is the model's name)."""
    if len(new) > 15:
        raise ValueError("model name %s longer than 15 characters" % new)
    d = bytearray(data)
    old_u, new_u = old.upper().encode("latin-1"), new.upper().encode("latin-1")

    def put(o, width, value):
        d[o:o + width] = value.ljust(width, b"\0")[:width]

    def swap(o, width):
        v = bytes(d[o:o + width]).split(b"\0")[0]
        if v.upper() == old_u:
            put(o, width, new_u)
        elif v.upper().startswith(old_u + b"."):
            put(o, width, new_u + v[len(old_u):])
    for t, o, s, _ in chunks(d, 0, len(d)):
        for t2, o2, s2, sub in chunks(d, o + 8, o + 8 + s):
            if t == HIERARCHY and t2 == HIERARCHY_HEADER:
                swap(o2 + 12, 16)
            elif t == MESH and t2 == MESH_HEADER3:
                swap(o2 + 32, 16)
            elif t == HLOD and t2 == HLOD_HEADER:
                swap(o2 + 16, 16)
                swap(o2 + 32, 16)
            elif (t, t2) in ((ANIMATION, ANIMATION_HEADER), (COMPRESSED_ANIMATION, COMPRESSED_ANIMATION_HEADER)):
                swap(o2 + 12, 16)                       # an embedded animation: its name and hierarchy
                swap(o2 + 28, 16)
            elif t == HLOD and sub:                    # LOD arrays: sub-objects are bone + name[32]
                for t3, o3, _, _ in chunks(d, o2 + 8, o2 + 8 + s2):
                    if t3 == HLOD_SUB_OBJECT:
                        swap(o3 + 12, 32)
    return bytes(d)
