"""The standard check suite every building passes (helpers in checks.py)."""
import os

import numpy as np

from ..formats.assetcache import AssetCache
from ..formats.textures import dds_info, dxt1_size, full_chain, tga24_size, tga_header
from ..formats.w3d import W3DFile
from ..paint import imageio
from .checks import new_triangle_normals, snapshot, tangent_convention, uv_overlap


def run(b, ws, r):
    target = b.target
    shipped = ws.shipped_model
    O, N = snapshot(ws.source_model), snapshot(shipped)
    WO, WN = W3DFile(ws.source_model), W3DFile(shipped)
    meshes = sorted(O["meshes"])
    others = [n for n in meshes if n != target]

    r.section("structure")
    r.check("one armature", N["n_arm"] == 1, "%d" % N["n_arm"])
    r.check("same %d bone names" % len(O["bones"]), sorted(N["bones"]) == sorted(O["bones"]), "%d bones" % len(N["bones"]))
    moved = [k for k in O["bones"] if k in N["bones"] and any(
        abs(a - c) > 1e-3 for x, y in zip(O["bones"][k][:2], N["bones"][k][:2]) for a, c in zip(x, y))]
    moved += [k for k in O["bones"] if k in N["bones"] and O["bones"][k][2] != N["bones"][k][2]]
    r.check("bones not moved / re-parented", not moved, str(moved) if moved else "")
    r.check("exactly the original meshes", sorted(N["meshes"]) == meshes, str(sorted(N["meshes"])))
    for n in meshes:
        a, m = O["meshes"][n], N["meshes"].get(n)
        if m is None:
            continue
        r.check("%s parented to bone %s" % (n, a["parent_bone"]),
                (m["parent_type"], m["parent_bone"]) == ("BONE", a["parent_bone"]), "%s/%s" % (m["parent_type"], m["parent_bone"]))
        r.check("%s keeps its one material" % n, m["mats"] == a["mats"] and m["mat_idx"] == {0}, str(m["mats"]))
        r.check("%s zero-area faces / loose verts" % n, m["zero_area"] == 0 and m["loose"] == 0, "%d / %d" % (m["zero_area"], m["loose"]))
        r.check("%s UV layers as the original, inside [0,1]" % n, m["uv_layers"] == a["uv_layers"] and m["uv_out"] == 0,
                "%d layers, %d out" % (m["uv_layers"], m["uv_out"]))
    for n in others:
        same = sorted(O["meshes"][n]["tri_keys"]) == sorted(N["meshes"][n]["tri_keys"])
        r.check("%s geometry untouched" % n, same, "%d tris" % N["meshes"][n]["tris"])
    a, m = O["meshes"][target], N["meshes"][target]
    r.check("%s triangles <= %d" % (target, b.tri_budget), m["tris"] <= b.tri_budget, "%d -> %d" % (a["tris"], m["tris"]))
    for i, ax in enumerate("XY"):
        r.check("%s %s footprint inside the original [%.2f, %.2f]" % (target, ax, a["bbmin"][i], a["bbmax"][i]),
                m["bbmin"][i] >= a["bbmin"][i] - 1e-3 and m["bbmax"][i] <= a["bbmax"][i] + 1e-3,
                "new [%.2f, %.2f]" % (m["bbmin"][i], m["bbmax"][i]))
    h0, h1 = a["bbmax"][2] - a["bbmin"][2], m["bbmax"][2] - m["bbmin"][2]
    r.check("%s height growth <= %d%%" % (target, 100 * b.max_z_growth),
            h1 <= h0 * (1 + b.max_z_growth) + 1e-3 and m["bbmin"][2] >= a["bbmin"][2] - 1e-3,
            "%.2f -> %.2f (%+.1f%%)" % (h0, h1, 100 * (h1 / h0 - 1)))
    cnt, disagree, visible, back_seen = new_triangle_normals(m, a)
    r.check("new triangles: winding matches vertex normals", disagree == 0, "%d of %d disagree" % (disagree, cnt))
    r.check("new triangles: no back face visible from the sky", back_seen == 0,
            "%d of %d visible show their back (%d buried)" % (back_seen, visible, cnt - visible))
    r.check("hierarchy / container / HLOD names as the original", WN.object_names() == WO.object_names(), str(WN.object_names()))

    r.section("textures named in the file bytes")
    own = b.texture_names()
    want = sorted(own.values())
    r.check("%s -> %s" % (target, " / ".join(want)), WN.meshes[target].textures == want, str(WN.meshes[target].textures))
    for n in others:
        r.check("%s texture references unchanged" % n, WN.meshes[n].textures == WO.meshes[n].textures, str(WN.meshes[n].textures))
    r.check("every mesh header version as the original", all(WN.meshes[n].version == WO.meshes[n].version for n in meshes),
            str({n: hex(WN.meshes[n].version) for n in meshes}))

    r.section("texture files")
    atlas = b.style.atlas
    dds = ws.shipped_texture(own[atlas.texture], ".dds")
    for path, size in ((dds, b.tier.diffuse), (ws.tex(own[atlas.texture][:-4].lower() + "_%d.dds" % (b.tier.diffuse // 2)), b.tier.diffuse // 2)):
        i = dds_info(path)
        exp = dxt1_size(size, size, full_chain(size))
        r.check("%s: %d, DXT1, full mip chain" % (os.path.basename(path), size),
                (i["width"], i["height"], i["fourcc"], i["mips"], i["bytes"]) == (size, size, "DXT1", full_chain(size), exp),
                "%dx%d %s, %d mips, %d bytes" % (i["width"], i["height"], i["fourcc"], i["mips"], i["bytes"]))
    tga = ws.shipped_texture(own[atlas.normal], ".tga")
    ref, nt = imageio.read_tga24(ws.atlas_normal), imageio.read_tga24(tga)
    same = all(nt[k] == ref[k] for k in ("type", "bpp", "desc", "cmap", "idlen")) and nt["footer"] == ref["footer"]
    r.check("%s: the original normal map's TGA format" % os.path.basename(tga), same,
            "type %d, %d bpp, descriptor 0x%02x" % (nt["type"], nt["bpp"], nt["desc"]))
    r.check("%s: %d x %d, uncompressed" % (os.path.basename(tga), b.tier.normal, b.tier.normal),
            (tga_header(tga)["width"], tga_header(tga)["height"]) == (b.tier.normal, b.tier.normal)
            and os.path.getsize(tga) == tga24_size(b.tier.normal, b.tier.normal, len(ref["footer"])), "%d bytes" % os.path.getsize(tga))
    v = nt["pixels"] * 2 - 1
    ln = np.linalg.norm(v, axis=-1)
    r.check("normal map decodes to unit normals facing out", abs(float(np.median(ln)) - 1) < 0.03 and float(np.percentile(v[..., 2], 1)) > 0.2,
            "median |n| %.3f, 1st percentile z %.2f" % (float(np.median(ln)), float(np.percentile(v[..., 2], 1))))

    r.section("%s layout and tangent frame (file bytes)" % target)
    mm = WN.meshes[target]
    uv, tr = np.array(mm.uv), np.array(mm.tris)
    r.check("UVs inside [0,1]", bool(((uv >= 0) & (uv <= 1)).all()),
            "u [%.4f, %.4f] v [%.4f, %.4f]" % (uv[:, 0].min(), uv[:, 0].max(), uv[:, 1].min(), uv[:, 1].max()))
    cov, over = uv_overlap(uv, tr)
    r.check("UVs non-overlapping (2048 raster)", over / max(cov, 1) < 1e-4,
            "overlap %.5f%%; layout fills %.1f%% of the square" % (100 * over / max(cov, 1), 100 * cov / 2048 ** 2))
    passes = mm.material_passes()
    r.check("one material pass (as the original)", len(passes) == len(WO.meshes[target].material_passes()) == 1, "%d" % len(passes))
    t_n, b_n = tangent_convention(mm)
    r.check("tangent frame stored like the original (T=-dP/dv, B=+dP/du)", t_n > 0.95 and b_n > 0.95, "median dots %.3f / %.3f" % (t_n, b_n))
    P = np.array(mm.verts)
    a3 = np.linalg.norm(np.cross(P[tr[:, 1]] - P[tr[:, 0]], P[tr[:, 2]] - P[tr[:, 0]]), axis=1) / 2
    d1, d2 = uv[tr[:, 1]] - uv[tr[:, 0]], uv[tr[:, 2]] - uv[tr[:, 0]]
    dens = np.sqrt(np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / 2 * b.tier.diffuse ** 2 / np.maximum(a3, 1e-9))
    o = np.argsort(dens)
    cw = np.cumsum(a3[o])
    r.info("texel density (area-weighted px per unit)", "median %.1f, p10 %.1f, p90 %.1f" % tuple(
        dens[o][np.searchsorted(cw, cw[-1] * q)] for q in (0.5, 0.1, 0.9)))

    r.section("untouched parts, byte for byte (vs the original through the same export + fix-up)")
    WR = W3DFile(ws.reference_fixed)
    for n in others:
        r.check("%s mesh chunk identical" % n, WN.meshes[n].bytes == WR.meshes[n].bytes, "%d bytes" % len(WN.meshes[n].bytes))
    cn, cr = WN.top(), WR.top()
    for tag, name in ((0x100, "hierarchy"), (0x700, "HLOD")):
        x, y = [c for t, c in cn if t == tag], [c for t, c in cr if t == tag]
        r.check("%s chunk identical" % name, x == y and len(x) == 1, "%d bytes" % (len(x[0]) if x else 0))
    r.check("top-level chunk order unchanged", [t for t, _ in cn] == [t for t, _ in cr], str([hex(t) for t, _ in cn]))

    r.section("asset cache (the build's copy)")
    cache = AssetCache(ws.cache)
    stale = cache.stale_entries(shipped, b.model_file)
    r.check("record matches the file", not stale, "%d stale" % len(stale))
    names = cache.texture_names()
    r.check("own textures registered", all(t.lower().encode() in names for t in own.values()), "%d asset records" % len(names))
    dep = cache.dependencies(b.model_file, "%s.%s" % (ws.container, target))
    r.check("%s depends on %s" % (target, own[atlas.texture].lower()), dep is not None and own[atlas.texture].lower() in [d.lower() for d in dep], str(dep))
    return r.summary()
