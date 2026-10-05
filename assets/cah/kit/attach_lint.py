"""Checks of the parts-on-bones design (assets/cah/kit/attach.py), each with a broken copy that
must fail (check()):

- createaheromodels.inc is EA's (no hero draws a model of ours in EA's place);
- every shipped INI keeps EA's text byte for byte before ours;
- every part mesh is hidden by default, rigid (no skin), its name and its model's at most 15
  characters, and in a model of ours;
- every part model rides a bone its EA model's skeleton has, through a Draw module of its class
  attached to that bone that draws it in a state of its own EA model;
- no Draw module of ours draws a part model in a state of another EA model (a mounted rider
  never shows the unmounted model's parts, the Sage never the Taskmaster's fit);
- through EA's check animation every part vertex stays at its distance from its bone;
- colours (paint_lint, docs/CAH.md "Serious and fun"): no part reacts to the Hair (R) or Skin (G)
  picker; every serious part has at least MIN_PAINT of its surface on Paint (B) unless the class
  lists it in ALL_METAL; a serious part with a tile remap (a gold-plated or hot-pink variant) keeps
  its fixed colours and needs none; a fun part is tinted only if the class lists it in FUN_TINTED
  (then on B), else it stays fixed.
"""
import math
import re

from sagekit.formats import w3dpose as P
from sagekit.formats.w3d import VERTEX_INFLUENCES, W3DFile, chunks

from sagekit.housecheck import shares

from .attach import HIDDEN, NAME_MAX, SKIN_TYPE, _set_attrs, attrs, class_states, ea_models, module_tag, parts
from .models import folder, skeleton

MIN_PAINT = .03                 # a serious part's least share of surface on the Paint picker (B)
MASK_W, MASK_H = 512, 256       # the kit's masks (kit/paint.py)


def modules(text):
    """{module tag: (bone, [(state, model)])} of our attach Draw modules in a drawmodules file."""
    out = {}
    for m in re.finditer(r"^Draw = W3DScriptedModelDraw (SKH_Att_\S+)[^\n]*\n(.*?)^End\b", text, re.M | re.S):
        body = m.group(2)
        bone = re.search(r"^\s*AttachToBoneInAnotherModule = (\"[^\"]*\"|\S+)", body, re.M)
        states = re.findall(r"^\s*ModelConditionState = ([^\r\n]*?)\s*\r?\n\s*Model = (\S+)", body, re.M)
        out[m.group(1)] = (bone.group(1).strip('"') if bone else None, [(" ".join(s.split()), mo) for s, mo in states])
    return out


def lint(spec, ea, ours, built):
    """The redesign's promises for one class, as a list of problems."""
    errs = []
    if ours["models"] != ea["models"]:
        errs.append("createaheromodels.inc changed: every hero would draw something else than EA's model")
    for k in ea:
        if not k.startswith("class_") and not ours[k].startswith(ea[k].rstrip()):
            errs.append("%s: EA's text is not kept byte for byte before ours" % k)
    mods = modules(ours["obj_createaherodrawmodules"])
    of_state = dict(class_states(ea["models"], ea_models(spec)))
    meshes = {}
    for name, (ea_model, bone, data) in built.items():
        if len(name) > NAME_MAX:
            errs.append("model %s: longer than %d characters" % (name, NAME_MAX))
        if bone not in skeleton(spec, spec.SKELETONS[ea_model]).names:
            errs.append("%s rides %s, which %s's skeleton lacks" % (name, bone, ea_model))
        tag = module_tag(spec, bone)
        if tag not in mods or mods[tag][0] != bone:
            errs.append("%s: no Draw module %s attaches it to %s" % (name, tag, bone))
        elif not any(mo == name and of_state.get(st) == ea_model for st, mo in mods[tag][1]):
            errs.append("%s: %s draws it in no state of %s" % (name, tag, ea_model))
        for mesh_name, m in W3DFile(data).meshes.items():
            meshes.setdefault(mesh_name, []).append(name)
            if not attrs(m.bytes) & HIDDEN:
                errs.append("%s.%s: not hidden by default (it would show on every hero)" % (name, mesh_name))
            if attrs(m.bytes) & SKIN_TYPE or any(t == VERTEX_INFLUENCES for t, _, _, _ in chunks(m.bytes, 8, len(m.bytes))):
                errs.append("%s.%s: skinned; an attached part is rigid on its bone" % (name, mesh_name))
            if len(mesh_name) > NAME_MAX:
                errs.append("%s.%s: longer than %d characters" % (name, mesh_name, NAME_MAX))
    ours_by_name = {n: (m, b) for n, (m, b, _) in built.items()}
    prefix = "SKH_Att_%s_" % spec.ATTACH_STEM
    for tag, (bone, states) in mods.items():
        if not tag.startswith(prefix):
            continue
        for st, mo in states:
            if mo == "None":
                continue
            if mo not in ours_by_name:
                errs.append("%s: state %s draws %s, no model of ours" % (tag, st, mo))
            elif ours_by_name[mo] != (of_state.get(st), bone):
                errs.append("%s: state %s draws %s, made for %s on %s" % (tag, st, mo, *ours_by_name[mo]))
        missing = [st for st in of_state if st not in [s for s, _ in states]]
        if missing:
            errs.append("%s lists no state %s: the hero would fall back to another state's parts" % (tag, missing))
    for p in parts(spec):
        if p[0].upper() not in meshes:
            errs.append("%s: in no part model" % p[0])
    return errs


def masks(spec):
    """{sheet texture (lower case .tga): raw RGBA mask bytes} of the class (kit/paint.py writes
    <sheet>_mask.rgba next to the TGA)."""
    work = folder(spec)[2]
    return {s.lower(): (work / (s.lower()[:-4] + "_mask.rgba")).read_bytes() for s in spec.MASKS}


def coverage(spec, built, mk):
    """{part: [share on R, G, B]}: per EA model the part's pieces summed by area, the model with the
    least Paint share kept."""
    per = {}
    for name, (ea_model, _, data) in built.items():
        for part, m in W3DFile(data).meshes.items():
            px = mk.get(m.textures[0].lower()) if m.textures else None
            area, sh = shares(m, MASK_W, MASK_H, px, rgb=(0, 1, 2)) if px else (0.0, [0, 0, 0])
            a = per.setdefault(part, {}).setdefault(ea_model, [0.0, 0.0, 0.0, 0.0])
            a[0] += area
            for c in range(3):
                a[c + 1] += area * sh[c]
    out = {}
    for part, models in per.items():
        got = [[x / a[0] for x in a[1:]] if a[0] else [0, 0, 0] for a in models.values()]
        out[part] = [max(q[0] for q in got), max(q[1] for q in got), min(q[2] for q in got)]
    return out


def paint_lint(spec, cov):
    """The colour rules over coverage(), as a list of problems."""
    errs = []
    fun_tinted, metal = set(getattr(spec, "FUN_TINTED", ())), set(getattr(spec, "ALL_METAL", ()))
    names = {p[0] for p in parts(spec)}
    for n in sorted((fun_tinted | metal) - names):
        errs.append("%s: listed in FUN_TINTED/ALL_METAL but no part of the class" % n)
    for p in parts(spec):
        r, g, b = cov.get(p[0].upper(), [0, 0, 0])
        if r > 0 or g > 0:
            errs.append("%s: %.1f%% on Hair (R), %.1f%% on Skin (G); our parts follow Paint (B) only" % (p[0], 100 * r, 100 * g))
        if p[5] == "fun":
            if p[0] in fun_tinted and b <= 0:
                errs.append("%s: listed in FUN_TINTED but takes no Paint colour" % p[0])
            elif p[0] not in fun_tinted and b > 0:
                errs.append("%s: a fun part with %.1f%% on Paint; fun parts keep their fixed colours" % (p[0], 100 * b))
        elif p[6] is None and p[0] not in metal and b < MIN_PAINT:
            errs.append("%s: %.1f%% on Paint (B), under %.0f%% (tint its enamel, cloth or leather, or list it in "
                        "ALL_METAL)" % (p[0], 100 * b, 100 * MIN_PAINT))
        elif p[0] in metal and b > 0:
            errs.append("%s: listed in ALL_METAL but %.1f%% takes the Paint colour" % (p[0], 100 * b))
    return errs


def _moved(mk, f):
    """The masks with f(r, g, b, a) -> (r, g, b, a) applied to every texel."""
    out = {}
    for k, d in mk.items():
        b = bytearray(d)
        for o in range(0, len(b), 4):
            b[o:o + 4] = bytes(f(*b[o:o + 4]))
        out[k] = bytes(b)
    return out


def paint_check(spec, built):
    """paint_lint() clean, and its broken copies caught: Paint moved to Skin, no Paint at all, every
    texel tinted (the fun parts too)."""
    mk = masks(spec)
    cov = coverage(spec, built, mk)
    errs = paint_lint(spec, cov)
    broken = {"paint_on_skin": paint_lint(spec, coverage(spec, built, _moved(mk, lambda r, g, b, a: (r, b, 0, a)))),
              "no_paint": paint_lint(spec, coverage(spec, built, _moved(mk, lambda r, g, b, a: (r, g, 0, a)))),
              "all_tinted": paint_lint(spec, coverage(spec, built, _moved(mk, lambda r, g, b, a: (0, 0, 200, 255))))}
    return errs, broken, {k: [round(100 * x, 1) for x in v] for k, v in sorted(cov.items())}


def check(spec, ea, ours, built):
    """lint() and paint_lint() clean, and each broken copy caught."""
    errs = lint(spec, ea, ours, built)
    paint_errs, broken, cov = paint_check(spec, built)
    errs += paint_errs
    first_model = ea_models(spec)[0].upper()
    b = dict(ours)
    b["models"] = ours["models"].replace(first_model, "SK" + first_model[2:], 1) + " "
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
    # a module drawing another EA model's fit in a state (the unmounted parts on the rider), or
    # a module missing one of the class's states
    text = ours["obj_createaherodrawmodules"]
    m = re.search(r"^Draw = W3DScriptedModelDraw SKH_Att_%s_\S+[^\n]*\n.*?^End\b" % re.escape(spec.ATTACH_STEM), text, re.M | re.S)
    block = m.group(0)
    names = [n for n in dict.fromkeys(re.findall(r"Model = (\S+)", block)) if n != "None"]
    if len(names) > 1:
        bad = block.replace("Model = %s\r\n" % names[1], "Model = %s\r\n" % names[0], 1)
    else:
        bad = re.sub(r"ModelConditionState = [^\r\n]*", "ModelConditionState = PREORDER", block, count=1)
    text = text.replace(block, bad, 1)
    broken["wrong_state"] = lint(spec, ea, dict(ours, obj_createaherodrawmodules=text), built)
    if errs or not all(broken.values()):
        raise SystemExit("attach lint failed: %s" % (errs or {k: v for k, v in broken.items() if not v}))
    return {"errors": errs, "broken": {k: v[:1] for k, v in broken.items()}, "paint": cov}


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

