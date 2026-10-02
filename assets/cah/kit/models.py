"""Build a CaH class's models: EA's sources (hash-checked), and for each of its models (_U in game,
_C creation screen, _M mounted) a copy under its own name with the class's parts appended as new
hidden skinned sub-objects.

Every EA chunk stays byte for byte (bodies, EA's parts and their two-bone skin weights); our MESH
chunks follow EA's last mesh and are listed in the HLOD on bone 0 like EA's skins. Pieces are
designed once in the class's design model (spec.DESIGN) and placed in each model: a model on the
design model's skeleton takes them as drawn; any other is mapped by the exact affine fit of EA's
parts that both carry with identical vertices (spec.FIT_REFS), the weapons by spec.WEAPON_REF's.
Each part is trimmed (geom lod) to its budget in that model (spec.budget).

Checks: EA's chunks unchanged; new meshes skinned, single-bone, on their group's bones, one of our
sheets; through an EA animation every vertex is finite and keeps its distance to its bone; budgets.
"""
import hashlib
import json
import math
import struct
from pathlib import Path

from sagekit import paths
from sagekit.formats import w3dpose as P
from sagekit.formats.w3d import HLOD, MESH, MESH_HEADER3, W3DFile, chunk_bytes, chunks, rename_model
from sagekit.game import Install

from .geom import Gear, affine, affine_fit

LODS = (1.0, .85, .7, .55, .45, .35)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def folder(spec):
    d = Path(paths.BUILD) / "cah" / spec.NAME
    return d, d / "src", d / "work"


def sources(spec):
    """EA's files into src/, refusing anything but EA's bytes."""
    d, src, _ = folder(spec)
    src.mkdir(parents=True, exist_ok=True)
    g = Install()
    for name, want in spec.EXPECTED.items():
        data = g.read("art\\w3d\\%s\\%s.w3d" % (name[:2], name))
        if sha(data) != want:
            raise SystemExit("%s is not EA's (sha256 %s)" % (name, sha(data)))
        (src / (name + ".w3d")).write_bytes(data)
    (d / "sources.json").write_text(json.dumps(spec.EXPECTED, indent=1) + "\n")


def skeleton(spec, name):
    return P.Skeleton((folder(spec)[1] / (name + ".w3d")).read_bytes())


def rest_points(w, sk, name):
    me = w.meshes[name]
    return [P.point(sk.rest[b], v) for v, b in zip(me.verts, P.influences(me.bytes))]


def placements(spec, model):
    """(body place, weapon place): design space -> `model`'s rest space."""
    ident = lambda p: tuple(p)
    if spec.SKELETONS[model] == spec.SKELETONS[spec.DESIGN] or model in getattr(spec, "OWN_SPACE", ()):
        # one rest pose (EA's parts sit identically), or a class whose designs measure each model
        return ident, ident
    if hasattr(spec, "place"):           # no exact shared fit (the archers): spec.place(model, group) per group
        return None, None
    src = folder(spec)[1]
    dw, dsk = W3DFile(str(src / (spec.DESIGN + ".w3d"))), skeleton(spec, spec.SKELETONS[spec.DESIGN])
    w, sk = W3DFile(str(src / (model + ".w3d"))), skeleton(spec, spec.SKELETONS[model])
    fits = []
    for ref in spec.FIT_REFS:
        if ref in dw.meshes and ref in w.meshes:
            a, b = rest_points(dw, dsk, ref), rest_points(w, sk, ref)
            if len(a) == len(b):
                X, e = affine_fit(a, b)
                if e < 1e-3:
                    fits.append(X)
    if not fits or any(abs(a - b) > 1e-3 for X in fits for ra, rb in zip(fits[0], X) for a, b in zip(ra, rb)):
        raise SystemExit("%s: EA's parts give no single exact map from the design model" % model)
    weapon = None
    if getattr(spec, "WEAPON_REF", None) and spec.WEAPON_REF in w.meshes:
        Xw, ew = affine_fit(rest_points(dw, dsk, spec.WEAPON_REF), rest_points(w, sk, spec.WEAPON_REF))
        if ew > 1e-3:
            raise SystemExit("%s: EA's %s is no affine copy of the design model's (%g)" % (model, spec.WEAPON_REF, ew))
        weapon = lambda p: affine(Xw, p)
    return (lambda p: affine(fits[0], p)), weapon or (lambda p: affine(fits[0], p))


def rename_mesh(chunk, name):
    d = bytearray(chunk)
    for t, o, s, _ in chunks(d, 8, len(d)):
        if t == MESH_HEADER3:
            d[o + 16:o + 32] = name.encode().ljust(16, b"\0")
            return bytes(d)
    raise ValueError("no mesh header")


def add_meshes(model, new, container):
    """Model bytes with MESH chunks `new` [(name, chunk)] after EA's last mesh and an HLOD
    sub-object (bone 0) for each; every other chunk byte for byte."""
    top = list(chunks(model, 0, len(model)))
    last = max(k for k, (t, _, _, _) in enumerate(top) if t == MESH)
    out = bytearray()
    for k, (t, o, s, _) in enumerate(top):
        if t == HLOD:
            body = bytearray()
            for t2, o2, s2, h2 in chunks(model, o + 8, o + 8 + s):
                if not h2:
                    body += model[o2:o2 + 8 + s2]
                    continue
                arr = bytearray()
                for t3, o3, s3, _ in chunks(model, o2 + 8, o2 + 8 + s2):
                    c = bytearray(model[o3:o3 + 8 + s3])
                    if t3 == 0x703:                       # the array's sub-object count
                        struct.pack_into("<I", c, 8, struct.unpack_from("<I", c, 8)[0] + len(new))
                    arr += c
                for name, _ in new:
                    arr += chunk_bytes(0x704, struct.pack("<I", 0) + ("%s.%s" % (container, name)).encode().ljust(32, b"\0"), False)
                body += chunk_bytes(t2, bytes(arr), True)
            out += chunk_bytes(HLOD, bytes(body), True)
        else:
            out += model[o:o + 8 + s]
        if k == last:
            for _, c in new:
                out += c
    return bytes(out)


def parts_of(spec, model):
    """The class's parts that go into `model` (those of the subclasses that draw it)."""
    subs = {s["index"] for s in spec.SUBCLASSES if model.upper() in [m.upper() for m in s["models"]]}
    return [p for p in spec.PARTS if set(p[8] if len(p) > 8 else [s["index"] for s in spec.SUBCLASSES]) & subs]


def template(spec, model, w):
    """(EA mesh, its texture) whose material our meshes copy: spec.TEMPLATE / TEMPLATE_TEX, or per
    model {model: (mesh, texture)}. Our sheet names replace the texture in place: never longer."""
    t = spec.TEMPLATE[model] if isinstance(spec.TEMPLATE, dict) else (spec.TEMPLATE, spec.TEMPLATE_TEX)
    mesh = w.meshes[t[0]]
    if t[1].lower() not in [x.lower() for x in mesh.textures]:
        raise SystemExit("%s: template %s draws %s, not %s" % (model, t[0], mesh.textures, t[1]))
    long = [s for s in spec.SHEETS.values() if len(s) > len(t[1])]
    if long:
        raise SystemExit("%s: sheet names %s are longer than the template's %s" % (model, long, t[1]))
    return mesh, next(x for x in mesh.textures if x.lower() == t[1].lower())


def make_part(spec, entry, tmpl, sk, model, body, weapon, lod):
    name, group, fn, _, _, sheet, remap = entry[:7]
    place = weapon if group == "CreateAHero_Weapon" else body
    if place is None:
        place = spec.place(model, group)
    seat = getattr(spec, "SEAT", {}).get(group)
    if seat:
        place = (lambda f, s: lambda p: f(s(p)))(place, seat)
    mesh, tex = tmpl
    m = Gear(mesh, sk, {tex: spec.SHEETS[sheet]}, place=place,
             bone_map=dict(getattr(spec, "BONE_MAP", {}).get(model, {}), **{spec.DESIGN_HAND: spec.HAND[spec.SKELETONS[model]]}),
             remap=remap, lod=lod)
    fn(m)
    return m


def build_model(spec, model):
    _, src, work = folder(spec)
    data = (src / (model + ".w3d")).read_bytes()
    w, sk = W3DFile(data), skeleton(spec, spec.SKELETONS[model])
    body, weapon = placements(spec, model)
    tmpl = template(spec, model, w)
    new, stats = [], {}
    parts = parts_of(spec, model)
    kind = spec.KIND[model]
    for entry in parts:
        name, group = entry[0], entry[1]
        cap = spec.budget(name, group, kind)
        for lod in LODS:
            m = make_part(spec, entry, tmpl, sk, model, body, weapon, lod)
            if len(m.verts) <= cap:
                break
        new.append((name, rename_mesh(m.chunk(), name)))
        stats[name] = dict(verts=len(m.verts), tris=len(m.tris), lod=lod, budget=cap, over=len(m.verts) > cap)
    ours = spec.MODELS[model.upper()]
    built = rename_model(add_meshes(data, new, tmpl[0].container), model.upper(), ours)
    (work / (ours.lower() + ".w3d")).write_bytes(built)
    return check(spec, model, data, rename_model(built, ours, model.upper()), sk, stats, parts)


def check(spec, model, ea_bytes, built, sk, stats, parts):
    ea, ours = W3DFile(ea_bytes), W3DFile(built)
    names = [p[0] for p in parts]
    assert list(ours.meshes) == list(ea.meshes) + names, list(ours.meshes)
    for n in ea.meshes:                                   # bodies and EA's parts, weights included
        assert ea.meshes[n].bytes == ours.meshes[n].bytes, n
    new_chunks = {ours.meshes[n].bytes for n in names}
    keep = [c for t, c in ea.top() if t != HLOD]
    have = [c for t, c in ours.top() if t != HLOD and not (t == MESH and c in new_chunks)]
    assert keep == have, "an EA chunk changed"
    _, hier, bones = P.hlod(built)
    assert hier.upper() == spec.SKELETONS[model].upper(), hier
    anim = P.Animation((folder(spec)[1] / (spec.CHECK_ANIM[spec.SKELETONS[model]] + ".w3d")).read_bytes())
    rest, worst = sk.pose(None, 0), 0.0
    sheets = {s.lower() for s in spec.SHEETS.values()}
    for entry in parts:
        n, group = entry[0], entry[1]
        g = ours.meshes[n]
        infl = P.influences(g.bytes)
        assert bones.get(n) == 0 and g.skinned and len(infl) == len(g.verts), n
        used = {sk.names[b] for b in infl}
        assert used <= spec.BONES[group], (n, used)
        assert len({t.lower() for t in g.textures}) == 1 and {t.lower() for t in g.textures} <= sheets, (n, g.textures)
        assert all(math.isfinite(x) for v in g.verts for x in v) and all(max(t) < len(g.verts) for t in g.tris), n
        for f in range(0, anim.frames, max(1, anim.frames // 8)):
            pose = sk.pose(anim, f)
            for v, b in zip(g.verts[::11], infl[::11]):
                p, r = P.point(pose[0][b], v), P.point(rest[0][b], v)
                assert all(math.isfinite(x) for x in p)
                d1 = math.dist(p, [pose[0][b][3], pose[0][b][7], pose[0][b][11]])
                d0 = math.dist(r, [rest[0][b][3], rest[0][b][7], rest[0][b][11]])
                worst = max(worst, abs(d1 - d0))
        stats[n]["bones"] = sorted(used)
    assert worst < 1e-3, worst
    return dict(model=model, shipped=spec.MODELS[model.upper()], ea_bytes=len(ea_bytes), ours_bytes=len(built),
                max_bone_drift=worst, parts=stats)


def build_class(spec, paint=None, skip_paint=False):
    """Sources, sheets (paint(work)), models and the INI fragment of one class into build/cah/<NAME>/;
    the class's INI composed alone onto EA's and linted. Returns the report (also report.json)."""
    from . import ini
    d, _, work = folder(spec)
    work.mkdir(parents=True, exist_ok=True)
    sources(spec)
    if paint and not (skip_paint and all((work / (s.lower()[:-4] + ".dds")).exists() for s in spec.SHEETS.values())):
        paint(work)
    report = {"models": [build_model(spec, m.lower()) for m in spec.MODELS]}
    ea = ini.read_all()
    frag = ini.fragment(spec, ea)
    (work / "fragment.json").write_text(json.dumps(frag, indent=1) + "\n")
    ours = ini.compose(ea, [frag])
    models = {r["shipped"].lower(): set(W3DFile(str(work / (r["shipped"].lower() + ".w3d"))).meshes) for r in report["models"]}
    report["ini"] = ini.check(ea, ours, models, list(spec.MODELS.values()), [frag])
    written, changed = ini.write(ours, ea, work / "ini", [frag])
    report["ini"].update(members=written, changed_lines=changed,
                         lists={sub: {g[len("CreateAHero_"):]: len(v) for g, v in r.items()}
                                for sub, r in ini.lists(ours["class_" + spec.CLASS_FILE], ini.upgrades(ours["upgrades"])).items()})
    report["over_budget"] = [(r["shipped"], n, s["verts"], s["budget"]) for r in report["models"] for n, s in r["parts"].items()
                             if s["over"]]
    (d / "report.json").write_text(json.dumps(report, indent=1) + "\n")
    for r in report["models"]:
        print("PASS %s (%s): %d -> %d bytes, drift %.1e" % (r["shipped"], r["model"], r["ea_bytes"], r["ours_bytes"],
                                                           r["max_bone_drift"]))
    over = report["over_budget"]
    print("budgets: %s" % ("all parts within" if not over else "OVER: %s" % over))
    print("INI: lint clean, %d broken copies caught; lists %s" % (len(report["ini"]["broken"]), report["ini"]["lists"]))
    print("Built into %s; nothing installed." % d)
    return report
