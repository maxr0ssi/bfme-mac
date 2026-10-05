#!/usr/bin/env python3
"""Create-a-Hero parts as models of our own on the hero's bones: EA's heroes are left alone
(docs/CAH.md, "Known issue / redesign").

Why: EA hides its parts at spawn with a Lua list (data\\scripts\\scripts.lua,
CreateAHeroHideEverything, run by the CreateAHeroFunctions events OnCreated and OnGenericEvent).
No CaH mesh carries the W3D hidden flag, so a part missing from that list is drawn from spawn
on. Our copies of EA's skins carried 12-24 such parts on every hero: "permanent stuff".

Now each part is a rigid mesh in a small model of ours, one model per (EA model, bone),
e.g. SKDWTMU_HEAD. A Draw module per model (`AttachToBoneInAnotherModule`, EA's own
HeroOfTheWestShield pattern) draws it only in the subclass's CREATE_A_HERO states. Every part
mesh has the W3D hidden flag, so it starts hidden without EA's list. The part's upgrade shows it
through the same SubObjectsUpgrade / RemoveUpgradeUpgrade modules as before. createaheromodels.inc
and EA's skins are not touched. A hero who picks none of our parts draws exactly EA's models.

A class opts in with ATTACH = [part sub-objects] (the pilot: the Dwarf's Erebor helm and axe)
and ATTACH_STEM (the model-name stem, e.g. "SKDW").

    python3 -m assets.cah.kit.attach <class> [--review]   build/assets/cah/<class>/attach/
"""
import json
import math
import re
import struct
import sys
import types
from pathlib import Path

from sagekit.formats import w3dmesh as WM
from sagekit.formats import w3dpose as P
from sagekit.formats.w3d import HLOD, HIERARCHY, MESH_HEADER3, VERTEX_INFLUENCES, W3DFile, chunk_bytes, chunks, rename_textures

from . import ini
from .models import LODS, folder, make_part, parts_of, placements, skeleton, sources, template

HIDDEN = 0x1000                                         # W3D_MESH_FLAG_HIDDEN
SKIN_TYPE = 0x00FF0000
FLT_MAX = 3.4028234663852886e+38
NAME_MAX = ini.NAME_MAX


def attach_dir(spec):
    return folder(spec)[0] / "attach"


def parts(spec):
    """The class's parts that ride bones (spec.ATTACH), in APPEND order."""
    want = list(spec.ATTACH)
    out = [p for p in spec.PARTS if p[0] in want]
    if [p[0] for p in out] != [p for p in want if p in {q[0] for q in out}] or len(out) != len(want):
        raise SystemExit("%s: ATTACH names parts not in PARTS: %s" % (spec.NAME, set(want) - {p[0] for p in out}))
    return out


def view(spec):
    """The spec as the INI kit sees it: only the attached parts, no model copies."""
    v = types.SimpleNamespace(**{k: getattr(spec, k) for k in dir(spec) if not k.startswith("__")})
    v.PARTS, v.MODELS = parts(spec), {}
    return v


def ea_models(spec):
    """EA's models of the class's subclasses (in game, creation screen, mounted), in order."""
    return list(dict.fromkeys(m.lower() for s in spec.SUBCLASSES for m in s["models"]))


def stem(bone):
    return re.sub(r"[^A-Z0-9]", "", bone.upper().replace("B_", "", 1))


def model_name(spec, ea_model, bone):
    """Ours for EA's model and bone: CHDW_TM_U_SKN + B_HEAD -> SKDWTMU_HEAD."""
    name = "%s%s_%s" % (spec.ATTACH_STEM, "".join(ea_model.upper().split("_")[1:3]), stem(bone))
    if len(name) > NAME_MAX:
        raise SystemExit("%s: model name longer than %d characters" % (name, NAME_MAX))
    return name


def _set_container(mesh_chunk, container):
    c = bytearray(mesh_chunk)
    for t, o, _, _ in chunks(c, 8, len(c)):
        if t == MESH_HEADER3:
            c[o + 32:o + 48] = container.upper().encode("latin-1").ljust(16, b"\0")
            return bytes(c)
    raise ValueError("no mesh header")


def _set_attrs(mesh_chunk, add=0, clear=0):
    c = bytearray(mesh_chunk)
    for t, o, _, _ in chunks(c, 8, len(c)):
        if t == MESH_HEADER3:
            a = struct.unpack_from("<I", c, o + 12)[0]
            struct.pack_into("<I", c, o + 12, (a & ~clear) | add)
            return bytes(c)
    raise ValueError("no mesh header")


def rigid_part(spec, entry, model, container="X"):
    """(bone name, rigid hidden MESH chunk named after the part, its vertices in the bone's space,
    stats): the kit's design, trimmed to the budget, every vertex on one bone (an attached model
    is rigid at that bone)."""
    name, group = entry[0], entry[1]
    if len(name) > NAME_MAX:
        raise SystemExit("%s: a W3D sub-object name holds %d characters" % (name, NAME_MAX))
    src = folder(spec)[1]
    w = W3DFile((src / (model + ".w3d")).read_bytes())
    sk = skeleton(spec, spec.SKELETONS[model])
    body, weapon = placements(spec, model)
    tmpl = template(spec, model, w)
    cap = spec.budget(name, group, spec.KIND[model])
    for lod in LODS:
        g = make_part(spec, entry, tmpl, sk, model, body, weapon, lod)
        if len(g.verts) <= cap:
            break
    bones = {v[3] for v in g.verts}
    if len(bones) != 1:
        raise SystemExit("%s in %s rides %s: an attached part rides one bone (split it)" %
                         (name, model, sorted(sk.names[b] for b in bones)))
    bone = sk.names[bones.pop()]
    raw = WM.build_mesh(g.original.bytes, {0: WM.Source(g.original.bytes)}, name, container, g.verts, g.tris, False)
    raw = rename_textures(raw, [(None, k, v.ljust(len(k), "\0")) for k, v in g.names.items()], name)
    raw = _set_attrs(raw, add=HIDDEN, clear=SKIN_TYPE)
    stats = dict(verts=len(g.verts), tris=len(g.tris), lod=lod, budget=cap, over=len(g.verts) > cap, bone=bone)
    return bone, raw, W3DFile(raw).meshes[name.upper()].verts, stats


def _model(name, meshes):
    """A rigid model: ROOTTRANSFORM plus one pivot per mesh at the root (EA's attached weapons'
    layout), the meshes, and an HLOD with each mesh on its pivot."""
    nm = name.upper().encode("latin-1").ljust(16, b"\0")
    pivots = struct.pack("<16si3f3f4f", b"ROOTTRANSFORM".ljust(16, b"\0"), -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    for mesh, _ in meshes:
        pivots += struct.pack("<16si3f3f4f", mesh.upper().encode("latin-1").ljust(16, b"\0"), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
    hier = chunk_bytes(HIERARCHY, chunk_bytes(0x101, struct.pack("<I16sI3f", 0x40001, nm, 1 + len(meshes), 0, 0, 0), False) +
                       chunk_bytes(0x102, pivots, False), True)
    arr = chunk_bytes(0x703, struct.pack("<If", len(meshes), FLT_MAX), False)
    for k, (mesh, _) in enumerate(meshes):
        arr += chunk_bytes(0x704, struct.pack("<I32s", k + 1, ("%s.%s" % (name.upper(), mesh.upper())).encode("latin-1")), False)
    hlod = chunk_bytes(HLOD, chunk_bytes(0x701, struct.pack("<II16s16s", 0x10000, 1, nm, nm), False) + chunk_bytes(0x702, arr, True), True)
    return hier + b"".join(c for _, c in meshes) + hlod


def build_models(spec):
    """{model name: (EA model, bone, bytes)} and per-part stats: for each of EA's models, one model
    of ours per bone its attached parts ride, drawn in that model's states only (each EA model has
    its own fit of the design, so the creation-screen Taskmaster and Sage differ slightly)."""
    groups, stats = {}, {}
    want = {p[0] for p in parts(spec)}
    for m in ea_models(spec):
        for entry in [p for p in parts_of(spec, m) if p[0] in want]:
            bone, raw, _, st = rigid_part(spec, entry, m)
            name = model_name(spec, m, bone)
            groups.setdefault(name, (m, bone, []))[2].append((entry[0], _set_container(raw, name)))
            stats["%s/%s" % (name, entry[0])] = st
    return {n: (m, b, _model(n, meshes)) for n, (m, b, meshes) in groups.items()}, stats


def states(ea_models_text, models):
    """The ModelConditionState lines whose Model is one of `models` (EA's createaheromodels.inc)."""
    out = []
    text = ini.strip(ea_models_text)
    for m in re.finditer(r"^\s*ModelConditionState\s*=\s*([^\n]*?)\s*\n\s*Model\s*=\s*(\S+)", text, re.M | re.I):
        if m.group(2).lower() in models and m.group(1) not in out:
            out.append(m.group(1))
    if not out:
        raise SystemExit("createaheromodels.inc has no state drawing %s" % models)
    return out


def draw_modules(spec, ea, built):
    NL = ini.NL
    text = ""
    for name, (ea_model, bone, _) in sorted(built.items()):
        text += ("Draw = W3DScriptedModelDraw SKH_Att_%s\t; sagekit cah: %s parts on %s, hidden until picked" % (name, spec.NAME, bone) + NL +
                 "\tOkToChangeModelColor = Yes" + NL + "\tDefaultModelConditionState" + NL + "\t\tModel = None" + NL + "\tEnd" + NL)
        for st in states(ea["models"], [ea_model]):
            text += "\tModelConditionState = %s" % st + NL + "\t\tModel = %s" % name + NL + "\tEnd" + NL
        text += "\tAttachToBoneInAnotherModule = %s" % bone + NL + "End" + NL
    return text


def fragment(spec, ea, built):
    frag = ini.fragment(view(spec), ea)
    frag["models"] = {}
    frag["append"]["obj_createaherodrawmodules"] = draw_modules(spec, ea, built)
    frag["attach"] = {n: sorted(W3DFile(b).meshes) for n, (_, _, b) in built.items()}
    return frag


def lint(spec, ea, ours, built):
    """The redesign's promises, each a check; broken copies must each fail (check())."""
    errs = []
    if ours["models"] != ea["models"]:
        errs.append("createaheromodels.inc changed: every hero would draw something else than EA's model")
    for k in ea:
        if not k.startswith("class_") and not ours[k].startswith(ea[k].rstrip()):
            errs.append("%s: EA's text is not kept byte for byte before ours" % k)
    meshes = {}
    for name, (ea_model, bone, data) in built.items():
        if len(name) > NAME_MAX:
            errs.append("model %s: longer than %d characters" % (name, NAME_MAX))
        if bone not in skeleton(spec, spec.SKELETONS[ea_model]).names:
            errs.append("%s rides %s, which %s's skeleton lacks" % (name, bone, ea_model))
        if not re.search(r"Draw = W3DScriptedModelDraw SKH_Att_%s\b[^\n]*\n(?:(?!^End).*\n)*?\s*AttachToBoneInAnotherModule = %s\s"
                         % (name, re.escape(bone)), ours["obj_createaherodrawmodules"], re.M):
            errs.append("%s: no Draw module attaches it to %s" % (name, bone))
        for mesh_name, m in W3DFile(data).meshes.items():
            meshes[mesh_name] = name
            attrs = [struct.unpack_from("<I", m.bytes, o + 12)[0] for t, o, _, _ in chunks(m.bytes, 8, len(m.bytes)) if t == MESH_HEADER3][0]
            if not attrs & HIDDEN:
                errs.append("%s.%s: not hidden by default (it would show on every hero)" % (name, mesh_name))
            if attrs & SKIN_TYPE or any(t == VERTEX_INFLUENCES for t, _, _, _ in chunks(m.bytes, 8, len(m.bytes))):
                errs.append("%s.%s: skinned; an attached part is rigid on its bone" % (name, mesh_name))
            if len(mesh_name) > NAME_MAX:
                errs.append("%s.%s: longer than %d characters" % (name, mesh_name, NAME_MAX))
    for p in parts(spec):
        if p[0].upper() not in meshes:
            errs.append("%s: in no part model" % p[0])
    return errs


def check(spec, ea, ours, built):
    errs = lint(spec, ea, ours, built)
    broken = {}
    b = dict(ours)
    b["models"] = ours["models"].replace("CHDW_TM_U_SKN", "SKDW_TM_U_SKN", 1) + " "
    broken["models_redirected"] = lint(spec, ea, b, built)
    b = dict(ours)
    b["obj_createaherodrawmodules"] = re.sub(r"AttachToBoneInAnotherModule = \S+", "AttachToBoneInAnotherModule = NOBONE",
                                            ours["obj_createaherodrawmodules"])
    broken["no_attach"] = lint(spec, ea, b, built)
    n0 = next(iter(built))
    k, bone, data = built[n0]
    first = next(iter(W3DFile(data).meshes.values()))
    shown = data.replace(first.bytes, _set_attrs(first.bytes, clear=HIDDEN))
    broken["shown_by_default"] = lint(spec, ea, ours, {**built, n0: (k, bone, shown)})
    b = dict(ours)
    b["remove"] = "X" + ours["remove"]
    broken["ea_text_changed"] = lint(spec, ea, b, built)
    if errs or not all(broken.values()):
        raise SystemExit("attach lint failed: %s" % (errs or {k: v for k, v in broken.items() if not v}))
    return {"errors": errs, "broken": {k: v[:1] for k, v in broken.items()}}


def pose_check(spec, built):
    """Every part vertex stays finite at its bone through EA's check animation."""
    worst = 0
    for name, (model, bone, data) in built.items():
        sk = skeleton(spec, spec.SKELETONS[model])
        anim = P.Animation((folder(spec)[1] / (spec.CHECK_ANIM[spec.SKELETONS[model]] + ".w3d")).read_bytes())
        b = sk.names.index(bone)
        for f in range(0, anim.frames, max(1, anim.frames // 8)):
            pose = sk.pose(anim, f)
            for mesh in W3DFile(data).meshes.values():
                for v in mesh.verts[::7]:
                    p = P.point(pose[0][b], v)
                    assert all(math.isfinite(x) for x in p), (name, f)
                    worst = max(worst, abs(math.dist(p, pose[0][b][3::4][:3]) - math.dist(v, (0, 0, 0))))
    assert worst < 1e-3, worst
    return worst


def load(spec):
    """The built part models {model name: (EA model, bone, bytes)} and the fragment (build() first)."""
    out = attach_dir(spec)
    if not (out / "report.json").exists():
        raise SystemExit("%s: build the attached parts first (python3 -m assets.cah.kit.attach %s)" % (spec.NAME, spec.NAME))
    report = json.loads((out / "report.json").read_text())
    built = {n: (m["ea_model"], m["bone"], (out / (n.lower() + ".w3d")).read_bytes()) for n, m in report["models"].items()}
    return built, json.loads((out / "fragment.json").read_text()), report


def sheets(built):
    """The sheets the part models draw (lower case .tga names)."""
    return sorted({t.lower() for _, _, d in built.values() for m in W3DFile(d).meshes.values() for t in m.textures})


def build(spec):
    """Part models, the INI fragment and every check into build/assets/cah/<class>/attach/."""
    sources(spec)
    out = attach_dir(spec)
    out.mkdir(parents=True, exist_ok=True)
    built, stats = build_models(spec)
    for name, (_, _, data) in built.items():
        (out / (name.lower() + ".w3d")).write_bytes(data)
    ea = ini.read_all()
    frag = fragment(spec, ea, built)
    (out / "fragment.json").write_text(json.dumps(frag, indent=1) + "\n")
    ours = ini.compose(ea, [frag])
    meshes = {n.lower(): set(W3DFile(b).meshes) for n, (_, _, b) in built.items()}
    report = {"models": {n: dict(ea_model=k, bone=b, bytes=len(d)) for n, (k, b, d) in built.items()}, "parts": stats,
              "ini": ini.check(ea, ours, meshes, [], [frag]), "attach": check(spec, ea, ours, built),
              "max_bone_drift": pose_check(spec, built)}
    written, changed = ini.write(ours, ea, out / "ini", [frag])
    report["ini"].update(members=written, changed_lines=changed)
    report["over_budget"] = [(k, s["verts"], s["budget"]) for k, s in stats.items() if s["over"]]
    (out / "report.json").write_text(json.dumps(report, indent=1) + "\n")
    for n, (k, b, d) in sorted(built.items()):
        print("PASS %s (%s, on %s): %s, %d bytes, every part hidden by default" % (n, k, b, ", ".join(sorted(W3DFile(d).meshes)), len(d)))
    print("INI: EA's files kept before ours, createaheromodels.inc untouched; members %s" % sorted(written.values()))
    print("Built into %s; nothing installed." % out)
    return report


if __name__ == "__main__":
    import importlib
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    spec = importlib.import_module("assets.cah.%s.design" % args[0])
    build(spec)
    if "--review" in sys.argv:
        from .attach_review import review
        review(spec)
