"""Night-light meshes written from scratch (pure Python): EA's own night-window material.

EA's lit windows (DBArchRnge_SKN.N_WINDOW, the glow cards N_GLOW) are single-pass legacy meshes:
one vertex material that is all emissive (no ambient, no diffuse), one texture, and the shader
    DepthCompare LEQUAL, no depth write, SrcBlend ONE, DestBlend ONE, texture modulated
i.e. additive: black adds nothing, so a texture's black margin is invisible and the glow never
darkens the stone under it. `lit_mesh` writes that structure with our vertices, texture name and
emissive colour; the header (version 5.0, sort level: drawn after the opaque meshes) follows EA's
night mesh it replaces, and a collision tree is generated (BFME2 does not draw a mesh without one).
"""
import math
import struct

from .w3d import (MATERIAL_INFO, MATERIAL_PASS, MESH, MESH_HEADER3, NORMALS, SHADER_IDS, SHADER_MATERIALS, SHADERS,
                  STAGE_TEXCOORDS, TEXTURE_IDS, TEXTURE_STAGE, TEXTURES, TRIANGLES, VERTEX_MATERIAL_IDS,
                  VERTEX_MATERIALS, VERTICES, build_aabtree, chunk_bytes, chunks)

VERTEX_SHADE_INDICES, VERTEX_MATERIAL, VERTEX_MATERIAL_NAME, VERTEX_MATERIAL_INFO = 0x22, 0x2B, 0x2C, 0x2D
TEXTURE, TEXTURE_NAME = 0x31, 0x32
FX_MATERIAL, FX_PROPERTY = 0x51, 0x53          # SHADER_MATERIALS' one material and its properties
# EA's additive night shader (DBArchRnge_SKN.N_WINDOW), byte for byte
ADDITIVE = bytes([3, 0, 0, 1, 2, 1, 0, 1, 1, 0, 0, 2, 0, 0, 0, 2])


def header_of(mesh_chunk):
    """(version, sort level) of an EA mesh chunk's header."""
    for t, o, _, _ in chunks(mesh_chunk, 8, len(mesh_chunk)):
        if t == MESH_HEADER3:
            return struct.unpack_from("<I", mesh_chunk, o + 8)[0], struct.unpack_from("<i", mesh_chunk, o + 8 + 56)[0]
    return 0x50000, 1


def material(mesh_chunk):
    """{'additive', 'emissive' (0..1 rgb), 'legacy', 'alpha'} of a mesh chunk: how the renders draw
    it. alpha: None (the texture's alpha is ignored), 'test' (cut out: a legacy shader's AlphaTest,
    an FX material's AlphaTestEnable) or 'blend' (legacy SrcBlend SRC_ALPHA, DestBlend
    ONE_MINUS_SRC_ALPHA). EA's bodies on NormalMapped.fx mostly have AlphaTestEnable off: their
    sheets' holes do not show, so a render must not cut them either."""
    out = {"additive": False, "emissive": (0.0, 0.0, 0.0), "legacy": False, "alpha": None}

    def walk(a, b):
        for t, o, s, h in chunks(mesh_chunk, a, b):
            if t == SHADERS and s >= 16:
                sh = mesh_chunk[o + 8:o + 24]
                out["additive"] = sh[3] == 1 and sh[7] == 1          # DestBlend ONE, SrcBlend ONE
                out["legacy"] = True
                out["alpha"] = "test" if sh[12] else "blend" if (sh[3], sh[7]) == (5, 2) else None
            elif t == VERTEX_MATERIAL_INFO:
                out["emissive"] = tuple(c / 255 for c in mesh_chunk[o + 8 + 16:o + 8 + 19])
            elif t == FX_PROPERTY:
                kind, n = struct.unpack_from("<II", mesh_chunk, o + 8)
                name = mesh_chunk[o + 16:o + 16 + n].split(b"\0")[0]
                if kind == 7 and name == b"AlphaTestEnable" and mesh_chunk[o + 16 + n]:
                    out["alpha"] = "test"
            elif h and t in (VERTEX_MATERIALS, VERTEX_MATERIAL, SHADER_MATERIALS, FX_MATERIAL):
                walk(o + 8, o + 8 + s)
    walk(8, len(mesh_chunk))
    return out


def lit_mesh(name, container, verts, normals, uvs, tris, texture, emissive=(255, 255, 255), like=None):
    """A MESH chunk: vertices (model units, the mesh's bone space), normals, one UV per vertex (W3D
    convention: v down), triangles [(i, j, k)]; drawn additively as texture x emissive colour.
    like: EA's mesh chunk this one replaces (header version and sort level)."""
    version, sort = header_of(like) if like else (0x50000, 1)
    n = len(verts)
    lo = [min(v[i] for v in verts) for i in range(3)]
    hi = [max(v[i] for v in verts) for i in range(3)]
    c = [(a + b) / 2 for a, b in zip(lo, hi)]
    r = max(math.dist(c, v) for v in verts)
    head = struct.pack("<II16s16sIIIIiIIII", version, 0, name.upper().encode("latin-1")[:15],
                       container.encode("latin-1")[:15], len(tris), n, 1, 0, max(sort, 1), 0, 0, 3, 1)
    head += struct.pack("<10f", *lo, *hi, *c, r)
    tri = b"".join(_triangle(verts, t) for t in tris)
    vm_info = struct.pack("<I4s4s4s4sfff", 0, b"\0" * 4, b"\0" * 4, b"\0" * 4, bytes(list(emissive) + [0]), 0.0, 1.0, 0.0)
    vm = chunk_bytes(VERTEX_MATERIAL, chunk_bytes(VERTEX_MATERIAL_NAME, b"night\0", False)
                     + chunk_bytes(VERTEX_MATERIAL_INFO, vm_info, False), True)
    tex = chunk_bytes(TEXTURE, chunk_bytes(TEXTURE_NAME, texture.encode("latin-1") + b"\0", False), True)
    zero = struct.pack("<I", 0)
    stage = chunk_bytes(TEXTURE_IDS, zero, False) + chunk_bytes(
        STAGE_TEXCOORDS, b"".join(struct.pack("<2f", *uv) for uv in uvs), False)
    body = (chunk_bytes(MESH_HEADER3, head, False)
            + chunk_bytes(VERTICES, b"".join(struct.pack("<3f", *v) for v in verts), False)
            + chunk_bytes(NORMALS, b"".join(struct.pack("<3f", *v) for v in normals), False)
            + chunk_bytes(TRIANGLES, tri, False)
            + chunk_bytes(VERTEX_SHADE_INDICES, b"".join(struct.pack("<I", i) for i in range(n)), False)
            + chunk_bytes(MATERIAL_INFO, struct.pack("<4I", 1, 1, 1, 1), False)
            + chunk_bytes(VERTEX_MATERIALS, vm, True)
            + chunk_bytes(SHADERS, ADDITIVE, False)
            + chunk_bytes(TEXTURES, tex, True)
            + chunk_bytes(MATERIAL_PASS, chunk_bytes(VERTEX_MATERIAL_IDS, zero, False)
                          + chunk_bytes(SHADER_IDS, zero, False) + chunk_bytes(TEXTURE_STAGE, stage, True), True)
            + build_aabtree(verts, tris))
    return chunk_bytes(MESH, body, True)


def _triangle(pos, ids):
    p0, p1, p2 = (pos[i] for i in ids)
    e1, e2 = [p1[x] - p0[x] for x in range(3)], [p2[x] - p0[x] for x in range(3)]
    n = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]]
    ln = math.sqrt(sum(x * x for x in n)) or 1.0
    n = [x / ln for x in n]
    return struct.pack("<4I4f", *ids, 13, *n, sum(a * b for a, b in zip(n, p0)))
