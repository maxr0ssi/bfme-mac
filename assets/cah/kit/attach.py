#!/usr/bin/env python3
"""Create-a-Hero parts as models of our own on the hero's bones: EA's heroes are left alone
(docs/CAH.md, "Known issue / redesign").

Why: EA hides its parts at spawn with a Lua list (data\\scripts\\scripts.lua,
CreateAHeroHideEverything, run by the CreateAHeroFunctions events OnCreated and OnGenericEvent).
No CaH mesh carries the W3D hidden flag, so a part missing from that list is drawn from spawn
on. Our copies of EA's skins carried 12-24 such parts on every hero: "permanent stuff".

Now each part is split by bone into rigid meshes (every vertex of a part already rides one bone;
a pauldron pair rides both upper arms) in small models of ours, one model per (EA model, bone),
e.g. SKDWTMU_HD. All pieces of a part keep the part's sub-object name, so its one
SubObjectsUpgrade shows them all. A Draw module per (class, bone) (`AttachToBoneInAnotherModule`,
EA's own HeroOfTheWestShield pattern) lists every CREATE_A_HERO state of the class's EA models,
each with our model for that EA model and bone, or None; a mounted state therefore never falls
back to the unmounted model's parts. Every part mesh has the W3D hidden flag, so it starts hidden
without EA's list. createaheromodels.inc and EA's skins are not touched. A hero who picks none
of our parts draws exactly EA's models.

A class opts in with ATTACH = [part sub-objects] (every part) and ATTACH_STEM (the model-name
stem, at most 4 characters, e.g. "SKDW"). Checks: assets/cah/kit/attach_lint.py.

    python3 -m assets.cah.kit.attach <class> [--review]   build/assets/cah/<class>/attach/
"""
import json
import re
import struct
import sys
import types

from sagekit.formats import w3dmesh as WM
from sagekit.formats.w3d import HLOD, HIERARCHY, MESH_HEADER3, W3DFile, chunk_bytes, chunks, rename_textures

from . import ini
from .models import LODS, folder, make_part, parts_of, placements, skeleton, sources, template

HIDDEN = 0x1000                                         # W3D_MESH_FLAG_HIDDEN
SKIN_TYPE = 0x00FF0000
FLT_MAX = 3.4028234663852886e+38
NAME_MAX = ini.NAME_MAX
# short bone codes for model names (15 characters at most): every rig's names for a body place
BONE_CODES = [(r"HEAD", "HD"), (r"(HAND_?R|R HAND)$", "HR"), (r"(HAND_?L|L HAND)$", "HL"),
              (r"(UARML|L ?UPPERARM)$", "UL"), (r"(UARMR|R ?UPPERARM)$", "UR"),
              (r"(FARML|L ?FOREARM)$", "FL"), (r"(FARMR|R ?FOREARM)$", "FR"),
              (r"SPINE2$", "S2"), (r"SPINE1?$", "S1"), (r"RIBS$", "RB"), (r"PELVIS$", "PV"), (r"WAIST$", "WA")]


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


def bone_code(bone):
    """B_HEAD, BAT_HEAD, TROLL HEAD, BIP HEAD -> HD; B_HAND_R -> HR; BAT_UARML -> UL; others: the
    bone's letters and digits without its rig prefix, at most 6."""
    b = bone.upper()
    for pat, code in BONE_CODES:
        if re.search(pat, b):
            return code
    return re.sub(r"[^A-Z0-9]", "", re.sub(r"^(B_|BAT_|BIP |TROLL)", "", b))[:6]


def model_name(spec, ea_model, bone):
    """Ours for EA's model and bone: CHDW_TM_U_SKN + B_HEAD -> SKDWTMU_HD."""
    name = "%s%s_%s" % (spec.ATTACH_STEM, "".join(ea_model.upper().split("_")[1:3]), bone_code(bone))
    if len(name) > NAME_MAX:
        raise SystemExit("%s: model name longer than %d characters" % (name, NAME_MAX))
    return name


def ini_bone(bone):
    """A bone name as an INI value: quoted when it holds a space (TROLL HEAD, BIP HEAD); EA's INI
    reader takes a quoted string as one value (game.dat 0x42e787)."""
    return '"%s"' % bone if " " in bone else bone


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


def attrs(mesh_chunk):
    return [struct.unpack_from("<I", mesh_chunk, o + 12)[0] for t, o, _, _ in chunks(mesh_chunk, 8, len(mesh_chunk))
            if t == MESH_HEADER3][0]


def rigid_pieces(spec, entry, model, container="X"):
    """([(bone name, rigid hidden MESH chunk named after the part)], stats): the kit's design,
    trimmed to the part's budget as a whole, split by the bone each vertex rides (an attached
    model is rigid at its bone; a part is rigid on its bones already, so nothing moves)."""
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
    by_bone = {}
    for t in g.tris:
        bones = {g.verts[i][3] for i in t[0]}
        if len(bones) != 1:
            raise SystemExit("%s in %s: a triangle spans bones %s" % (name, model, sorted(sk.names[b] for b in bones)))
        by_bone.setdefault(bones.pop(), []).append(t)
    pieces = []
    for b, tris in sorted(by_bone.items()):
        raw = WM.build_mesh(g.original.bytes, {0: WM.Source(g.original.bytes)}, name, container, g.verts, tris, False)
        raw = rename_textures(raw, [(None, k, v.ljust(len(k), "\0")) for k, v in g.names.items()], name)
        pieces.append((sk.names[b], _set_attrs(raw, add=HIDDEN, clear=SKIN_TYPE)))
    stats = dict(verts=len(g.verts), tris=len(g.tris), lod=lod, budget=cap, over=len(g.verts) > cap,
                 bones=[b for b, _ in pieces])
    return pieces, stats


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
    of ours per bone its parts ride, drawn in that model's states only (each EA model has its own
    fit of the design, so the creation-screen and in-game models differ slightly)."""
    groups, stats = {}, {}
    want = {p[0] for p in parts(spec)}
    for m in ea_models(spec):
        codes = {}
        for entry in [p for p in parts_of(spec, m) if p[0] in want]:
            pieces, st = rigid_pieces(spec, entry, m)
            for bone, raw in pieces:
                name = model_name(spec, m, bone)
                if codes.setdefault(name, bone) != bone:
                    raise SystemExit("%s: bones %s and %s share the model name %s" % (m, codes[name], bone, name))
                groups.setdefault(name, (m, bone, []))[2].append((entry[0], _set_container(raw, name)))
            stats["%s/%s" % (m, entry[0])] = st
    return {n: (m, b, _model(n, meshes)) for n, (m, b, meshes) in groups.items()}, stats


def class_states(ea_models_text, models):
    """[(state, EA model)] of every ModelConditionState in EA's createaheromodels.inc whose Model is
    one of `models`, in file order (a mounted state and a stealth state included)."""
    out = []
    for m in re.finditer(r"^\s*ModelConditionState\s*=\s*([^\n]*?)\s*\n\s*Model\s*=\s*(\S+)", ini.strip(ea_models_text), re.M | re.I):
        st = " ".join(m.group(1).split())
        if m.group(2).lower() in models and st not in [s for s, _ in out]:
            out.append((st, m.group(2).lower()))
    if not out:
        raise SystemExit("createaheromodels.inc has no state drawing %s" % models)
    return out


def module_tag(spec, bone):
    """SKH_Att_SKDW_B_HAND_R: the class's stem and the bone's full name (B_HAND_R and B_HANDR share
    a model-name code, never a module)."""
    return "SKH_Att_%s_%s" % (spec.ATTACH_STEM, re.sub(r"[^A-Za-z0-9]", "_", bone.upper()))


def draw_modules(spec, ea, built):
    """One Draw module per bone our parts ride in this class: every state of the class's EA models,
    each drawing our model for that EA model and bone, or None."""
    NL = ini.NL
    text = ""
    states = class_states(ea["models"], ea_models(spec))
    by = {(m, b): n for n, (m, b, _) in built.items()}
    for bone in sorted({b for _, b, _ in built.values()}):
        text += ("Draw = W3DScriptedModelDraw %s\t; sagekit cah: %s parts on %s, hidden until picked" % (module_tag(spec, bone), spec.NAME, bone) + NL +
                 "\tOkToChangeModelColor = Yes" + NL + "\tDefaultModelConditionState" + NL + "\t\tModel = None" + NL + "\tEnd" + NL)
        for st, m in states:
            text += "\tModelConditionState = %s" % st + NL + "\t\tModel = %s" % by.get((m, bone), "None") + NL + "\tEnd" + NL
        text += "\tAttachToBoneInAnotherModule = %s" % ini_bone(bone) + NL + "End" + NL
    return text


def fragment(spec, ea, built):
    frag = ini.fragment(view(spec), ea)
    frag["models"] = {}
    frag["append"]["obj_createaherodrawmodules"] = draw_modules(spec, ea, built)
    frag["attach"] = {n: sorted(W3DFile(b).meshes) for n, (_, _, b) in built.items()}
    return frag


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
    from .attach_lint import check, pose_check
    sources(spec)
    out = attach_dir(spec)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.w3d"):
        old.unlink()
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
    report["split"] = {k: s["bones"] for k, s in stats.items() if len(s["bones"]) > 1}
    (out / "report.json").write_text(json.dumps(report, indent=1) + "\n")
    print("PASS %s: %d parts, %d part models on %d bones, %d Draw modules; every part hidden by default; %d parts split by bone"
          % (spec.NAME, len(parts(spec)), len(built), len({b for _, b, _ in built.values()}),
             len(re.findall(r"^Draw = ", frag["append"]["obj_createaherodrawmodules"], re.M)), len(report["split"])))
    print("budgets: %s" % ("all parts within" if not report["over_budget"] else "OVER: %s" % report["over_budget"]))
    print("INI: EA's files kept before ours, createaheromodels.inc untouched; members %s" % sorted(written.values()))
    print("Built into %s; nothing installed." % out)
    return report


if __name__ == "__main__":
    import importlib
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    spec = importlib.import_module("assets.cah.%s.design" % args[0])
    if "--review-only" not in sys.argv:
        build(spec)
    if "--review" in sys.argv or "--review-only" in sys.argv:
        from .attach_review import review
        review(spec)
