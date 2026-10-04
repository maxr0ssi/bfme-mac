"""Build a unit recipe into its folder: EA's sources (hash-checked), our model, atlas and mask, checks.

    src/    EA's model, skeleton, animations, sheets and mask, as the game has them
    work/   our model (<model>.w3d), the private atlas DDS (one per private name), hc_<...>.tga,
            textures.json (what the preview draws), checks.json
    sources.json / textures.json   every EA file read, by archive path and SHA-256; EA's sheets
"""
import hashlib
import json
import math

from ..formats import w3dmesh as WM
from ..formats import w3dpose as P
from ..formats.textures import compiled_path, write_dds
from ..formats.w3d import MESH, VERTEX_INFLUENCES, W3DFile, chunks, rename_model
from ..game import Install
from . import paint as PT


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare(u, b):
    """Extract EA's files into src/ and check their hashes; return (W3DFile, Skeleton) of the
    model our build starts from (EA's, renamed to own_model when there is one)."""
    b.src.mkdir(parents=True, exist_ok=True)
    g, hashes = Install(), {}

    def fetch(member, dest):
        data = g.read(member)
        dest.write_bytes(data)
        hashes[member] = sha(data)
        return data
    for name in [u.model, u.skeleton] + ["%s_%s" % (u.family, a) for a in u.anims]:
        data = fetch(g.model_path(name), b.src / (name.lower() + ".w3d"))
        want = u.expected.get(name.lower())
        if want and sha(data) != want:
            raise SystemExit("%s: EA's %s is not the one this recipe was designed on; inspect the "
                             "model and rig before using it" % (u.id, name))
    if u.own_model:
        b.source_model().write_bytes(rename_model(b.ea_model().read_bytes(), u.model, u.own_model))
    w = W3DFile(str(b.source_model()))
    textures = {}
    for name in sorted({t.lower() for m in W3DFile(str(b.ea_model())).meshes.values() for t in m.textures}):
        member = next((compiled_path(name, e) for e in (".dds", ".tga") if g.owner(compiled_path(name, e))), None)
        if member is None:
            raise SystemExit("%s: no archive has the sheet %s" % (u.id, name))
        dest = b.src / (name[:-4] + member[-4:])
        fetch(member, dest)
        textures[name] = str(dest)
    for name in u.sources:
        fetch(compiled_path(name, ".dds"), b.src / (name.lower()[:-4] + ".dds"))
    if u.mask:
        fetch(mask_member(u), b.src / u.mask[0].lower())
    (b.dir / "textures.json").write_text(json.dumps(textures, indent=2))
    (b.dir / "sources.json").write_text(json.dumps(hashes, indent=2))
    return w, P.Skeleton(b.src.joinpath(u.skeleton.lower() + ".w3d").read_bytes())


def mask_member(u):
    """EA's house mask as an archive holds it (the recipe's mask_source, else <mask>.tga)."""
    return u.mask_source or compiled_path(u.mask[0], ".tga")


def build(u, b):
    """sources -> design -> model -> paint -> mask; then check()."""
    b.work.mkdir(parents=True, exist_ok=True)
    w, sk = prepare(u, b)
    meshes = u.design(w, sk)
    model = WM.replace_meshes(w.data, {n: m.chunk() for n, m in meshes.items()})
    converted = {n: 0 for n, m in meshes.items() if getattr(m, "converted", False)}
    (b.work / "kept.json").write_text(json.dumps(sorted(n for n, m in meshes.items() if getattr(m, "kept", False))))
    b.model().write_bytes(P.set_hlod_bones(model, converted) if converted else model)
    textures = json.loads((b.dir / "textures.json").read_text())
    atlas = u.paint(b)
    if u.privates() and not atlas:
        raise SystemExit("%s: paint() must return the atlas image for %s" % (u.id, ", ".join(u.privates())))
    for name in u.privates():
        dest = b.work / (name.lower()[:-4] + ".dds")
        write_dds(str(atlas), str(dest))
        textures[name.lower()] = str(dest)
    (b.work / "textures.json").write_text(json.dumps(textures, indent=2))
    if u.mask:
        PT.house_mask(b.src / u.mask[0].lower(), b.work / u.mask[1].lower(), u.mask_scale)
    return check(u, b)


def check(u, b):
    """The shared checks of a built unit against EA's model; then the recipe's own."""
    g = Install()
    for name, digest in u.expected.items():
        assert sha(b.src.joinpath(name + ".w3d").read_bytes()) == digest, name
    original, new = W3DFile(str(b.source_model())), W3DFile(str(b.model()))
    sk = P.Skeleton(b.src.joinpath(u.skeleton.lower() + ".w3d").read_bytes())
    assert original.skeleton() == new.skeleton(), "hierarchy changed"
    assert new.meshes.keys() == original.meshes.keys(), "meshes added or dropped"
    # every chunk but the meshes is EA's; a rigid mesh made a skin hangs on bone 0 in the HLOD
    converted = {n: 0 for n, m in new.meshes.items() if m.skinned and not original.meshes[n].skinned}
    expect = W3DFile(P.set_hlod_bones(original.data, converted)) if converted else original
    assert [c for t, c in expect.top() if t != MESH] == [c for t, c in new.top() if t != MESH], \
        "a chunk other than the meshes changed"
    privates = {t.lower() for t in u.privates()}
    kept = json.loads((b.work / "kept.json").read_text()) if (b.work / "kept.json").exists() else []
    rebuilt = []
    for name, m in new.meshes.items():
        old = original.meshes[name]
        assert len(m.uv) == len(m.verts) == len(m.normals), name
        assert all(0 <= i < len(m.verts) for t in m.tris for i in t), name
        assert all(math.isfinite(x) for v in m.verts + m.uv for x in v), name
        if m.bytes == old.bytes:
            continue
        rebuilt.append(name)
        assert all(0 <= x <= 1 for uv in m.uv for x in uv), "%s: UVs outside the atlas" % name
        assert all(t.lower() in privates for t in m.textures), "%s draws %s" % (name, m.textures)
        if name in kept:                                # EA's body first: its vertices unmoved
            assert m.verts[:len(old.verts)] == old.verts, "%s: EA's vertices moved" % name
        if m.skinned:
            bones = P.influences(m.bytes)
            assert len(bones) == len(m.verts) and all(0 <= x < len(sk.pivots) for x in bones), name
            ea = P.influences(old.bytes) if old.skinned else [P.hlod(original.data)[2].get(name, 0)] * len(old.verts)
            rows = P.skin(m.bytes)[0]
            assert all(r[2] + r[3] == 100 and r[1] < len(sk.pivots) for r in rows), "%s: skin weights" % name
            if name in kept:
                assert bones[:len(ea)] == ea, "%s: EA's bone assignments changed" % name
                skin_kept(name, old, m)
            if name in u.same_bones:
                assert set(bones) == set(ea or ()), "%s: bone set differs from EA's" % name
    for a in u.anims:
        anim = P.Animation(b.anim(a).read_bytes())
        assert anim.hierarchy.upper() == sk.name.upper() and anim.frames > 0, a
    if u.mask:
        assert b.src.joinpath(u.mask[0].lower()).read_bytes() == g.read(mask_member(u))
        PT.check_mask(b.src / u.mask[0].lower(), b.work / u.mask[1].lower(), u.mask_scale)
    u.check(b, original, new, sk)
    report = {"rebuilt": rebuilt, "unchanged": [n for n in new.meshes if n not in rebuilt],
              "source_triangles": sum(len(m.tris) for m in original.meshes.values()),
              "new_triangles": sum(len(m.tris) for m in new.meshes.values()),
              "model_sha256": sha(new.data)}
    (b.work / "checks.json").write_text(json.dumps(report, indent=2))
    print("PASS %s: skeleton, HLOD and EA's unchanged meshes; kept bodies on EA's vertices, bones and skin weights; "
          "mesh, UV and bone indices; animation hierarchies%s. %d -> %d triangles." % (
              u.id, "; the house mask" if u.mask else "", report["source_triangles"], report["new_triangles"]))
    return report


def skin_kept(name, old, new):
    """A kept body's skin weights are EA's byte for byte: EA's VERTEX_INFLUENCES rows (bone, second
    bone, weights) lead ours, and so do its second-bone positions and normals where it blends."""
    def raw(mesh, t):
        return next((mesh.bytes[o + 8:o + 8 + s] for u, o, s, _ in chunks(mesh.bytes, 8, len(mesh.bytes)) if u == t), None)
    sk = P.skin(old.bytes)
    two = bool(sk) and any(r[3] for r in sk[0])
    for t in (VERTEX_INFLUENCES, WM.VERTICES_2, WM.NORMALS_2):
        want, got = raw(old, t), raw(new, t)
        if want is not None and (t == VERTEX_INFLUENCES or two or got is not None):
            assert (got or b"")[:len(want)] == want, "%s: EA's skin weights (chunk 0x%x) changed" % (name, t)
