"""Where a W3D model puts each mesh: the bone it hangs on (the HLOD's sub-objects) and that bone's
transform in model space (the HIERARCHY's pivots, parents first; a skinned model's hierarchy is its
separate skeleton file).

EA re-rigs some lifecycle models: the archery range's damaged body (DBArchRnge_D1.ARCHERY) is the
healthy ARCHERYRANGE triangle for triangle, but hangs on a bone turned 180 degrees about z, so its
mesh-local coordinates are the healthy ones mirrored through the axis. Bodies are therefore
compared in model space, and our body is moved into the lifecycle mesh's bone frame before it is
spliced there. A frame is (R, T): R a 3x3 rotation (rows), T a translation; x_model = R x + T.
Animated poses (a lifecycle model's pieces at a frame) are sagekit/formats/w3dpose.py's.
"""
import struct

from .w3d import (BITANGENTS, HIERARCHY, HLOD, HLOD_SUB_OBJECT, MESH, MESH_HEADER3, NORMALS, PIVOTS, TANGENTS,
                  VERTICES, W3DFile, _cstr, _mesh_name, chunks, chunk_bytes)

IDENTITY = (((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), (0.0, 0.0, 0.0))


def _quat(x, y, z, w):
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def rotate(R, v):
    return tuple(sum(R[i][k] * v[k] for k in range(3)) for i in range(3))


def apply(f, v):
    R, T = f
    return tuple(a + b for a, b in zip(rotate(R, v), T))


def compose(a, b):
    """The frame doing b, then a."""
    (Ra, Ta), (Rb, Tb) = a, b
    R = tuple(tuple(sum(Ra[i][k] * Rb[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    return R, apply(a, Tb)


def inverse(f):
    R, T = f
    Rt = tuple(tuple(R[j][i] for j in range(3)) for i in range(3))
    return Rt, tuple(-c for c in rotate(Rt, T))


def is_identity(f, eps=1e-5):
    (R, T), I = f, IDENTITY[0]
    return all(abs(R[i][j] - I[i][j]) <= eps for i in range(3) for j in range(3)) and all(abs(c) <= eps for c in T)


def bone_frames(data):
    """[model-space frame] per pivot of the file's hierarchy, or None if it has none."""
    for t, o, s, _ in chunks(data or b"", 0, len(data or b"")):
        if t != HIERARCHY:
            continue
        for t2, o2, s2, _ in chunks(data, o + 8, o + 8 + s):
            if t2 != PIVOTS:
                continue
            out = []
            for i in range(s2 // 60):           # name[16], parent, translation, euler, quaternion
                b = o2 + 8 + 60 * i
                parent = struct.unpack_from("<i", data, b + 16)[0]
                local = (_quat(*struct.unpack_from("<4f", data, b + 44)), struct.unpack_from("<3f", data, b + 20))
                out.append(compose(out[parent], local) if 0 <= parent < len(out) else local)
            return out
    return None


def mesh_bones(data):
    """{MESH NAME: bone index} from the HLOD's sub-objects (the first LOD that names the mesh)."""
    out = {}
    for t, o, s, _ in chunks(data, 0, len(data)):
        if t != HLOD:
            continue
        for _, o2, s2, has_sub in chunks(data, o + 8, o + 8 + s):
            if has_sub:
                for t3, o3, _, _ in chunks(data, o2 + 8, o2 + 8 + s2):
                    if t3 == HLOD_SUB_OBJECT:
                        name = _cstr(data[o3 + 12:o3 + 44]).split(".")[-1].upper()
                        out.setdefault(name, struct.unpack_from("<I", data, o3 + 8)[0])
    return out


def mesh_frames(data, read_skeleton=None):
    """{MESH NAME: model-space frame}. read_skeleton(file name) -> bytes, for a skinned model whose
    hierarchy is a separate file; a mesh with no bone (a lone mesh, no hierarchy) is at the origin."""
    f = W3DFile(data)
    skl = f.skeleton()
    bones = bone_frames((read_skeleton(skl) if read_skeleton else None) if skl else data) or []
    where = mesh_bones(data)
    return {n: bones[where[n]] if where.get(n, len(bones)) < len(bones) else IDENTITY for n in f.meshes}


def model_box(mesh, frame):
    """[min x, y, z, max x, y, z] of a mesh in model space."""
    ps = [apply(frame, v) for v in mesh.verts]
    return [f(p[i] for p in ps) for f in (min, max) for i in range(3)]


def moved(data, mesh, name, frame):
    """The file with mesh `mesh` renamed `name` (the header's 16-byte name) and its vertices,
    normals, tangents and bitangents taken through `frame`, the header's box and sphere to match;
    every other chunk unchanged. For splicing a body into a model that names or rigs it otherwise."""
    if len(name) > 15:
        raise ValueError("mesh name %s longer than 15 characters" % name)
    out = bytearray()
    ident = is_identity(frame)
    for t, o, s, _ in chunks(data, 0, len(data)):
        raw = data[o:o + 8 + s]
        if t == MESH and _mesh_name(data, o, s) == mesh.upper():
            raw = chunk_bytes(MESH, b"".join(_moved_sub(data, t2, o2, s2, name, frame, ident)
                                             for t2, o2, s2, _ in chunks(data, o + 8, o + 8 + s)), True)
        out += raw
    return bytes(out)


def _moved_sub(data, t, o, s, name, frame, ident):
    raw = bytearray(data[o:o + 8 + s])
    if t == MESH_HEADER3:
        raw[16:32] = name.upper().encode("latin-1").ljust(16, b"\0")
        if not ident:                         # box min/max, sphere centre (radius unchanged)
            lo, hi = struct.unpack_from("<3f", raw, 8 + 76), struct.unpack_from("<3f", raw, 8 + 88)
            corners = [apply(frame, (x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
            struct.pack_into("<3f", raw, 8 + 76, *[min(c[i] for c in corners) for i in range(3)])
            struct.pack_into("<3f", raw, 8 + 88, *[max(c[i] for c in corners) for i in range(3)])
            struct.pack_into("<3f", raw, 8 + 100, *apply(frame, struct.unpack_from("<3f", raw, 8 + 100)))
    elif not ident and t in (VERTICES, NORMALS, TANGENTS, BITANGENTS):
        move = (lambda v: apply(frame, v)) if t == VERTICES else (lambda v: rotate(frame[0], v))
        for i in range(s // 12):
            struct.pack_into("<3f", raw, 8 + 12 * i, *move(struct.unpack_from("<3f", raw, 8 + 12 * i)))
    return bytes(raw)
