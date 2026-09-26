"""A copy of a W3D model with some of its meshes left out (sagekit/owncopy.py).

EA's placeholder models carry stand-in meshes (a box or cylinder painted with a text label) next to
the mesh a recipe rebuilds. In a model of our own - a copy nobody else draws - those meshes can go
altogether rather than be hidden: the MESH chunks are dropped and so are their HLOD sub-objects,
with every enclosing chunk size and each LOD array's sub-object count corrected. Bones stay (they
cost nothing and scripts or INI may name them). A model filed in the asset cache must not be cut
like this - its record lists every chunk - so this is only for copies the game parses itself.
"""
import struct

from .w3d import HLOD, HLOD_SUB_OBJECT, MESH, SUB, _cstr, _mesh_name, chunk_bytes, chunks

HLOD_SUB_OBJECT_ARRAY_HEADER = 0x703


def drop_meshes(data, names):
    """Model bytes without the meshes `names` (MESH NAMES) and their HLOD sub-objects."""
    names = {n.upper() for n in names}
    out = bytearray()
    for t, o, s, has_sub in chunks(data, 0, len(data)):
        if t == MESH and _mesh_name(data, o, s) in names:
            continue
        out += _hlod_without(data, o, s, names) if t == HLOD else data[o:o + 8 + s]
    return bytes(out)


def _hlod_without(d, o, s, names):
    body = bytearray()
    for t2, o2, s2, has_sub in chunks(d, o + 8, o + 8 + s):
        if not has_sub:
            body += d[o2:o2 + 8 + s2]
            continue
        kept, head = [], None
        for t3, o3, s3, _ in chunks(d, o2 + 8, o2 + 8 + s2):
            if t3 == HLOD_SUB_OBJECT_ARRAY_HEADER:
                head = bytearray(d[o3:o3 + 8 + s3])
            elif t3 == HLOD_SUB_OBJECT and _cstr(d[o3 + 12:o3 + 44]).split(".")[-1].upper() in names:
                continue
            else:
                kept.append(d[o3:o3 + 8 + s3])
        if head is not None:
            n = sum(1 for c in kept if struct.unpack_from("<I", c, 0)[0] == HLOD_SUB_OBJECT)
            struct.pack_into("<I", head, 8, n)
            kept.insert(0, bytes(head))
        body += chunk_bytes(t2, b"".join(kept), True)
    return chunk_bytes(HLOD, bytes(body), bool(struct.unpack_from("<I", d, o + 4)[0] & SUB))
