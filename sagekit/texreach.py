"""The largest mip level of each model texture the RTS camera can ever sample, and a check that no
staged texture ships levels above it (docs/MEMORY-2GB.md, "Texture memory of our archives").

The bound, per triangle of every mesh that uses the texture: the texture's largest texel density on
that triangle (the larger singular value of its UV mapping, in texels per world unit) against the
smallest world size of a pixel there, which is at the closest camera, facing the triangle, at the
smallest possible distance (the camera's eye `EYE` units above flat ground minus the triangle's
highest point, at least 1). GPUs take the mip level from the larger of the two screen-axis
derivatives, at least the larger singular value / sqrt(2) when facing the triangle, so

    LOD >= log2(sigma * distance * 2 tan(HFOV / 2) / WIDTH / sqrt(2))

and a texture whose lowest bound over all its triangles is >= k + MARGIN never samples its top k
levels (trilinear filtering, no anisotropy: the game's samplers in d3d traces). EYE is
DefaultCameraMinHeight (data/ini/gamedata.ini), HFOV the 50 degrees game.dat passes to
Set_View_Plane (0x5346e4, 0x487567 scales it with the viewport), WIDTH Max's 3024 pixels. Measured
2026-10-04: every texture of every pack reaches its top level (tall towers come within a few units of
the closest camera; magnified UV islands exist on nearly every sheet), so nothing can be dropped; the
check keeps it so for new art.

    python3 -m sagekit.texreach [archive.big ...]   the bound per texture (default: staged faction packs)
"""
import math
import os
import struct
import sys

from .formats import w3dpose
from .formats.big import Archive
from .formats.textures import compiled_path
from .formats.w3d import W3DFile

EYE, HFOV, WIDTH, MARGIN = 120.0, math.radians(50.0), 3024, 0.5
PIXEL = 2 * math.tan(HFOV / 2) / WIDTH


def sigma(p, t, w, h):
    """Larger singular value of a triangle's UV mapping in texels per world unit, or None."""
    e1 = [p[1][i] - p[0][i] for i in range(3)]
    e2 = [p[2][i] - p[0][i] for i in range(3)]
    l1 = math.sqrt(sum(x * x for x in e1))
    if l1 < 1e-6:
        return None
    a = sum(e2[i] * e1[i] for i in range(3)) / l1
    b = math.sqrt(max(0.0, sum(x * x for x in e2) - a * a))
    if b < 1e-6:
        return None
    du1, dv1 = (t[1][0] - t[0][0]) * w, (t[1][1] - t[0][1]) * h
    du2, dv2 = (t[2][0] - t[0][0]) * w, (t[2][1] - t[0][1]) * h
    j11, j12 = du1 / l1, (du2 - du1 * a / l1) / b
    j21, j22 = dv1 / l1, (dv2 - dv1 * a / l1) / b
    f, det = j11 * j11 + j12 * j12 + j21 * j21 + j22 * j22, j11 * j22 - j12 * j21
    return math.sqrt((f + math.sqrt(max(0.0, f * f - 4 * det * det))) / 2)


def lowest_lods(archive, read_other=None):
    """{texture member: (lowest LOD bound, model, mesh)} for the archive's models' textures that the
    archive ships. read_other(member) supplies skeletons from other archives."""
    a = Archive(str(archive))
    idx = a.index()
    dims = {}
    for k in idx:
        if k.startswith("art\\compiledtextures\\") and k.endswith((".dds", ".tga")):
            d = a.read(k)[:128]
            dims[k] = struct.unpack_from("<II", d, 12)[::-1] if d[:4] == b"DDS " else struct.unpack_from("<HH", d, 12)
    out = {}
    for k in idx:
        if not k.endswith(".w3d"):
            continue
        data = a.read(k)
        f = W3DFile(data)
        if not f.meshes:
            continue
        skl, sdata = f.skeleton(), data
        if skl:
            p = "art\\w3d\\%s\\%s" % (skl[:2], skl)
            sdata = a.read(p) if p in idx else (read_other(p) if read_other else None) or data
        pose = w3dpose.Skeleton(sdata).pose(None, 0)
        bones = w3dpose.hlod(data)[2]
        for m in f.meshes.values():
            mine = [(t, dims[t]) for t in (next((compiled_path(n, e) for e in (".dds", ".tga")
                    if compiled_path(n, e) in dims), None) for n in m.textures) if t]
            if not (m.uv and m.tris and mine):
                continue
            try:
                pts = w3dpose.mesh_points(m, bones, pose)
            except (IndexError, KeyError):
                pts = m.verts
            for tri in m.tris:
                if max(tri) >= min(len(m.uv), len(pts)) or any(pts[i] is None for i in tri):
                    continue
                p, uv = [pts[i] for i in tri], [m.uv[i] for i in tri]
                dist = max(1.0, EYE - max(q[2] for q in p)) * PIXEL / math.sqrt(2)
                for t, (w, h) in mine:
                    s = sigma(p, uv, w, h)
                    if s:
                        lod = math.log2(max(1e-12, s * dist))
                        if t not in out or lod < out[t][0]:
                            out[t] = (lod, k.split("\\")[-1], m.name)
    return out


def cached(archive):
    """lowest_lods(archive), cached by the archive's size and time in build/texreach/."""
    import json
    from . import paths
    st = os.stat(archive)
    f = os.path.join(paths.REPO, "build", "texreach", "%s-%d-%d.json" % (os.path.basename(str(archive)).lstrip("!"),
                                                                       st.st_size, int(st.st_mtime)))
    if os.path.exists(f):
        return {k: tuple(v) for k, v in json.load(open(f)).items()}
    out = lowest_lods(archive)
    os.makedirs(os.path.dirname(f), exist_ok=True)
    json.dump(out, open(f, "w"))
    return out


def faction_packs():
    from .texbake import staged
    small = ("-builder", "-worker", "-heroes", "-units", "-hud", "-icons", "-ui2x", "-fx", "-scenery")
    return [p for p in staged() if not any(s in p.name for s in small)]


def validate():
    """sagekit validate: no staged texture ships a top level the closest RTS camera cannot sample."""
    bad = n = 0
    for p in faction_packs():
        for t, (lod, model, mesh) in sorted(cached(p).items()):
            n += 1
            if lod >= 1 + MARGIN:
                bad += 1
                if bad <= 5:
                    print("FAIL texture reach %s: %s never samples its top %d level(s) at the closest camera "
                          "(lowest LOD %.2f on %s %s); ship it %d level(s) smaller"
                          % (p.name, t, int(lod - MARGIN), lod, model, mesh, int(lod - MARGIN)))
    if not bad:
        print("ok   texture reach: %d model textures in %d staged packs, each sampled at its top level at the closest camera"
              % (n, len(faction_packs())))
    return 1 if bad else 0


if __name__ == "__main__":
    for p in sys.argv[1:] or faction_packs():
        rows = sorted(lowest_lods(p).items(), key=lambda r: -r[1][0])
        print("%s: %d textures, highest lowest-LOD %.2f (%s)" % (os.path.basename(str(p)), len(rows),
              rows[0][1][0] if rows else 0, rows[0][0] if rows else "-"))
