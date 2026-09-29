"""The standard check suite every building passes (helpers in checks.py)."""
import os

import numpy as np

from ..formats.assetcache import AssetCache
from ..formats.textures import dds_info, dds_size, full_chain, tga24_size, tga_header
from ..formats.w3d import W3DFile
from ..paint import imageio
from .checks import new_triangle_normals, snapshot, tangent_convention, uv_overlap


def run(b, ws, r):
    target = b.target
    shipped = ws.shipped_model
    from . import checks as _checks
    _checks.WORLD = b.world_space
    O, N = snapshot(ws.source_model, ws.src), snapshot(shipped, ws.src)
    from ..sharedsheets import checks as shared_checks, renamed      # EA's, shared sheets as we ship them
    WO, WN = W3DFile(renamed(ws, open(ws.source_model, "rb").read())), W3DFile(shipped)
    from ..nightlights import names_of, night_meshes                 # rebuilt by the night-lights standard:
    night = night_meshes(names_of(ws), WO.data)                     # checked in blender/nightlights.py
    meshes = sorted(n for n in O["meshes"] if n not in night)
    others = [n for n in meshes if n != target]

    r.section("structure")
    r.check("one armature (none if EA's has none)", N["n_arm"] == min(1, O["n_arm"]), "%d" % N["n_arm"])
    r.check("same %d bone names" % len(O["bones"]), sorted(N["bones"]) == sorted(O["bones"]), "%d bones" % len(N["bones"]))
    moved = [k for k in O["bones"] if k in N["bones"] and any(
        abs(a - c) > 1e-3 for x, y in zip(O["bones"][k][:2], N["bones"][k][:2]) for a, c in zip(x, y))]
    moved += [k for k in O["bones"] if k in N["bones"] and O["bones"][k][2] != N["bones"][k][2]]
    r.check("bones not moved / re-parented", not moved, str(moved) if moved else "")
    r.check("exactly the original meshes", sorted(N["meshes"]) == sorted(O["meshes"]), str(sorted(N["meshes"])))
    for n in meshes:
        a, m = O["meshes"][n], N["meshes"].get(n)
        if m is None:
            continue
        r.check("%s parented as the original (%s/%s)" % (n, a["parent_type"], a["parent_bone"]),
                (m["parent_type"], m["parent_bone"]) == (a["parent_type"], a["parent_bone"]),
                "%s/%s" % (m["parent_type"], m["parent_bone"]))
        r.check("%s keeps its one material" % n, m["mats"] == a["mats"] and m["mat_idx"] == {0}, str(m["mats"]))
        # EA's own meshes may carry degenerate faces (the Elven gate's door leaves: 6 each); ours must not
        zero_ok = m["zero_area"] == 0 if n == target else m["zero_area"] <= a["zero_area"]
        r.check("%s zero-area faces / loose verts" % n, zero_ok and m["loose"] <= (0 if n == target else a["loose"]),
                "%d / %d" % (m["zero_area"], m["loose"]))
        # EA's own meshes may tile past [0,1] (props, effect cards); ours must not
        out_ok = m["uv_out"] == 0 if n == target else m["uv_out"] <= a["uv_out"]
        r.check("%s UV layers as the original, %s" % (n, "inside [0,1]" if n == target else "no more outside [0,1]"),
                m["uv_layers"] == a["uv_layers"] and out_ok, "%d layers, %d out (original %d)" % (m["uv_layers"], m["uv_out"], a["uv_out"]))
    for n in others:
        same = sorted(O["meshes"][n]["tri_keys"]) == sorted(N["meshes"][n]["tri_keys"])
        r.check("%s geometry untouched" % n, same, "%d tris" % N["meshes"][n]["tris"])
    a, m = O["meshes"][target], N["meshes"][target]
    from ..owncopy import checks as own_checks, extent        # an own copy's target takes over `replaces`
    lim = dict(zip(("bbmin", "bbmax"), extent(b, ws, a["bbmin"], a["bbmax"])))
    r.check("%s triangles <= %d" % (target, b.tri_budget), m["tris"] <= b.tri_budget, "%d -> %d" % (a["tris"], m["tris"]))
    for i, ax in enumerate("XY"):
        e = b.footprint_margin + 1e-3
        r.check("%s %s footprint inside the original [%.2f, %.2f]%s" % (target, ax, lim["bbmin"][i], lim["bbmax"][i],
                                                                      " + %.1f" % b.footprint_margin if b.footprint_margin else ""),
                m["bbmin"][i] >= lim["bbmin"][i] - e and m["bbmax"][i] <= lim["bbmax"][i] + e,
                "new [%.2f, %.2f]" % (m["bbmin"][i], m["bbmax"][i]))
    h0, h1 = lim["bbmax"][2] - lim["bbmin"][2], m["bbmax"][2] - m["bbmin"][2]
    r.check("%s height growth <= %d%%" % (target, 100 * b.max_z_growth),
            h1 <= h0 * (1 + b.max_z_growth) + 1e-3 and m["bbmin"][2] >= lim["bbmin"][2] - 1e-3,
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
    from ..alpha import dds_fourcc
    fmt = dds_fourcc(ws)                    # DXT5 when EA's sheet has cut-out alpha (sagekit/alpha.py)
    dds = ws.shipped_texture(b.own_diffuse, ".dds")
    for path, size in ((dds, b.tier.diffuse), (ws.tex(b.own_diffuse[:-4].lower() + "_%d.dds" % (b.tier.diffuse // 2)), b.tier.diffuse // 2)):
        i = dds_info(path)
        exp = dds_size(size, size, full_chain(size), fmt)
        r.check("%s: %d, %s, full mip chain" % (os.path.basename(path), size, fmt),
                (i["width"], i["height"], i["fourcc"], i["mips"], i["bytes"]) == (size, size, fmt, full_chain(size), exp),
                "%dx%d %s, %d mips, %d bytes" % (i["width"], i["height"], i["fourcc"], i["mips"], i["bytes"]))
    if b.own_normal:
        tga = ws.shipped_texture(b.own_normal, ".tga")
        ref, nt = imageio.read_tga24(ws.atlas_normal), imageio.read_tga24(tga)
        same = all(nt[k] == ref[k] for k in ("type", "bpp", "desc", "cmap", "idlen")) and nt["footer"] == ref["footer"]
        r.check("%s: the original normal map's TGA format" % os.path.basename(tga), same,
                "type %d, %d bpp, descriptor 0x%02x" % (nt["type"], nt["bpp"], nt["desc"]))
        r.check("%s: %d x %d, uncompressed" % (os.path.basename(tga), b.tier.normal, b.tier.normal),
                (tga_header(tga)["width"], tga_header(tga)["height"]) == (b.tier.normal, b.tier.normal)
                and os.path.getsize(tga) == tga24_size(b.tier.normal, b.tier.normal, len(ref["footer"]), ref["bpp"]), "%d bytes" % os.path.getsize(tga))
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
    if mm.tangents:
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

    r.section("untouched parts, byte for byte (vs EA's original file)")
    for n in others:
        r.check("%s mesh chunk identical" % n, WN.meshes[n].bytes == WO.meshes[n].bytes, "%d bytes" % len(WN.meshes[n].bytes))
    cn, co = WN.top(), WO.top()
    for tag, name in ((0x100, "hierarchy"), (0x700, "HLOD")):
        x, y = [c for t, c in cn if t == tag], [c for t, c in co if t == tag]
        r.check("%s chunk identical" % name, x == y and len(x) <= 1, "%d bytes" % (len(x[0]) if x else 0))
    r.check("top-level chunk order unchanged", [t for t, _ in cn] == [t for t, _ in co], str([hex(t) for t, _ in cn]))

    r.section("state variants (damaged / snow / stonework) and derived models")
    for ea, mine in sorted(ws.variants.items()):
        path = ws.shipped_texture(mine, ".dds")
        size = b.tier.diffuse // 2
        i = dds_info(path) if os.path.exists(path) else None
        r.check("%s (for EA's %s): %d, %s, full mips" % (mine, ea, size, fmt),
                i is not None and (i["width"], i["fourcc"], i["mips"]) == (size, fmt, full_chain(size)),
                "%s" % ("missing" if i is None else "%dx%d %s %d mips" % (i["width"], i["height"], i["fourcc"], i["mips"])))
    for ea, mine in sorted(ws.normal_variants.items()):     # our normal map under a state's name
        path, own_nrm = ws.shipped_texture(mine, ".tga"), ws.shipped_texture(b.own_normal, ".tga")
        r.check("%s (for EA's %s): a copy of %s" % (mine, ea, b.own_normal), os.path.exists(path) and
                os.path.exists(own_nrm) and open(path, "rb").read() == open(own_nrm, "rb").read(), "")
    for model, body in ws.derived_bodies.items():
        shipped_as = b.shipped_name(model).lower()
        member = "art\\w3d\\%s\\%s.w3d" % (shipped_as[:2], shipped_as)
        new, ea = W3DFile(ws.out(member)), W3DFile(os.path.join(ws.path("src"), model.lower() + ".w3d")) \
            if os.path.exists(os.path.join(ws.path("src"), model.lower() + ".w3d")) else None
        if body is None:                    # a chained recipe passes on its base's derived file
            r.check("%s: as %s derived it" % (model, b.base), ea is not None and new.data == ea.data, "")
            continue
        mesh = new.meshes[body]
        mine = ws.own_names                 # EA's files vary the case
        want = sorted({mine.get(t.lower(), t) for t in ea.meshes[body].textures}) if ea else None
        theirs = [t for t in mesh.textures if t.lower() not in {v.lower() for v in mine.values()}]
        r.check("%s: %s carries our body (%d tris)" % (model, body, len(mesh.tris)),
                len(mesh.tris) == len(WN.meshes[target].tris) and not mesh.skinned, "")
        box, where = placed(ws, new, body, WN, target)
        r.check("%s: %s where the healthy body is (%s)" % (model, body, where), box is not None,
                "box %s" % [round(x, 2) for x in box or ()])
        if ea:
            r.check("%s: %s textures %s, ours only" % (model, body, mesh.textures), mesh.textures == want and not theirs,
                    "want %s%s" % (want, "; EA's %s" % theirs if theirs else ""))
            others = [n for n in ea.meshes if n != body and n not in night_meshes(names_of(ws), ea.data)]
            r.check("%s: EA's other meshes byte-identical" % model,
                    all(new.meshes[n].bytes == W3DFile(renamed(ws, ea.data)).meshes[n].bytes for n in others), ", ".join(others))

    own_checks(b, ws, r)
    from .alpha import checks as alpha_checks
    alpha_checks(b, ws, r)              # EA's cut-outs carried over
    shared_checks(b, ws, r)
    r.section("asset caches (the build's copies)")
    caches = [AssetCache(p) for p in ws.caches()]
    r.check("at least one cache copy", bool(caches), ", ".join(ws.caches()))
    home = lambda f: next((c for c in caches if c.has_model(f)), None)  # noqa: E731
    for model, path in [(b.model_file, shipped)] + [
            (n + ".w3d", ws.out("art\\w3d\\%s\\%s.w3d" % (n[:2], n))) for n in (b.shipped_name(m).lower() for m in ws.derived)]:
        cache = home(model)
        if cache is None:                   # the engine draws no model its caches do not file
            r.check("%s filed in the asset caches" % model, False, "no record: the game would not draw it")
            continue
        st = cache.stale_entries(path, model)
        r.check("record of %s matches the file" % model, not st, "%d stale" % len(st))
    names = {n for c in caches for n in c.texture_names()}
    mine = list(own.values()) + list(ws.variants.values()) + list(ws.normal_variants.values())
    r.check("own textures registered (%d)" % len(mine), all(t.lower().encode() in names for t in mine), "%d asset records" % len(names))
    obj = "%s.%s" % (ws.container, target)
    dep = next((d for d in (c.dependencies(b.model_file, obj) for c in caches) if d is not None), None)
    if dep is None:
        r.info(obj, "no object record in the game's caches (none in EA's either): nothing to switch")
    else:
        r.check("%s depends on %s" % (target, b.own_diffuse.lower()), b.own_diffuse.lower() in [d.lower() for d in dep], str(dep))
    from .nightlights import checks as night_checks
    night_checks(b, ws, r)              # night lights on our surface, the faction's texture only
    from ..fire import checks as fire_checks
    fire_checks(b, ws, r)               # the fire rig, its Draw modules, EA's particle systems
    from .checks_lifecycle import run as lifecycle_checks
    lifecycle_checks(b, ws, r)          # construction / really damaged / rubble models
    return r.summary()


def placed(ws, new, body, healthy, target):
    """(model-space box, how) if the derived body sits where the healthy one does: as it stands (a
    construction model's bone animates from a bind pose of its own) or through the two models'
    bones (a re-rigged body); (None, "moved") if neither."""
    from ..formats.w3dframes import IDENTITY, mesh_frames, model_box

    def skl(name):
        p = os.path.join(ws.src, name)
        return open(p, "rb").read() if os.path.exists(p) else None
    a, h = new.meshes[body], healthy.meshes[target]
    for how, fa, fh in (("as it stands", IDENTITY, IDENTITY),
                        ("in model space", mesh_frames(new.data, skl).get(body), mesh_frames(healthy.data, skl).get(target))):
        if fa and fh and all(abs(x - y) < 0.01 for x, y in zip(model_box(a, fa), model_box(h, fh))):
            return model_box(a, fa), how
    return None, "moved"
