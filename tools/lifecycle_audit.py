#!/usr/bin/env python3
"""Audit a faction's lifecycle states from its last builds (no Blender, no game): for every model a
building's Draw modules show besides the healthy one (construction, damaged, really damaged, rubble,
collapse, snow), whether the game will draw OUR body there or EA's old model, and why; and whether
our fire burns only where our body stands.

    python3 tools/lifecycle_audit.py <faction>[/<building>] ... [--only-problems]

Per model (from build/assets/<faction>/<b>/work/lifecycle.json and lifecycle_plan.json):
  OURS      rebuilt by the lifecycle step, shipped in out/
  DERIVED   EA's healthy body in that state: our body spliced in whole (the derive step), shipped
  SKIP      the recipe's `lifecycle = {model: {"skip": why}}`
  EA-SHEET  EA's pieces there are painted from a sheet (or normal map) we have no variant of, so the
            step never saw them as our body (framework: Building.variants / normal_variants)
  EA-GATE   rebuilt, but below the per-frame checks (depth, spread, open backs); shipped EA's
  EA-FIT    no piece of EA's state lies on EA's healthy body (a remodel or an offset model)
  EA-ERROR  the build raised (e.g. a per-vertex layout the mesh writer refuses)
Also flagged: a state drawing a model of ours whose EA texture swap (snow, ice, damage, stonework)
has no swap of ours beside it (SWAP), a render in renders/lifecycle/ for a model not rebuilt (stale: it shows an older try),
a built model missing from out/, FAIL lines in checks.log, and the fire Draw modules of the shipped
INIs (sagekit/fire.py): a fire rig or ParticleSysBone in a construction, really damaged, rubble or
placement state, or in a state whose body is not our intact one (EA's model, or a broken model of ours:
fire.py burns only over the healthy body and derived models, EA's damage fire takes over elsewhere).
"""
import glob
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
BUILD = os.path.join(REPO, "build", "assets")

NO_FIRE = {"AWAITING_CONSTRUCTION", "PARTIALLY_CONSTRUCTED", "ACTIVELY_BEING_CONSTRUCTED", "RUBBLE",
           "POST_RUBBLE", "POST_COLLAPSE", "PHANTOM_STRUCTURE", "BUILD_PLACEMENT_CURSOR"}   # sagekit/fire.py NO_FIRE
DRAW_RE = re.compile(r"^\s*Draw\s*=\s*\S+\s+(\S+)", re.I)
STATE_RE = re.compile(r"^\s*(?:Default)?ModelConditionState\b\s*=?\s*(.*)$", re.I)


def classify(m):
    """(code, detail) for one entry of work/lifecycle.json."""
    s = m.get("summary", "")
    if m.get("built"):
        return "OURS", s.split(",")[0]
    if m.get("derived"):
        return "DERIVED", ""
    if s.startswith("skipped") or "skip" in s.lower() and "left to EA" not in s:
        return "SKIP", s
    if s.startswith("no body pieces"):
        tex = sorted({t for w in m.get("warnings", []) if "has no variant" in w
                      for t in re.findall(r"'([^']+)'", w.split("texture", 1)[1].split("has no")[0])})
        return "EA-SHEET", ("blocked by " + ", ".join(tex)) if tex else "painted from no sheet of ours"
    if "below the checks' standard" in s:
        first = next((w for w in m.get("warnings", []) if "@" in w), s)
        return "EA-GATE", first.split(": ", 1)[-1][:110]
    if "lies on EA's healthy body" in s:
        return "EA-FIT", "no piece on EA's healthy body"
    return "EA-ERROR", s.replace("left to EA: ", "")[:110]


def textures_of(ws_src, model):
    """Diffuse sheets the state's meshes are painted from (for EA-SHEET: which sheet blocked them)."""
    p = os.path.join(ws_src, model.lower() + ".w3d")
    if not os.path.exists(p):
        return []
    from sagekit.formats.w3d import W3DFile
    out = {}
    for mesh in W3DFile(open(p, "rb").read()).meshes.values():
        for t in mesh.textures:
            if "_nrm" not in t.lower():
                out[t] = out.get(t, 0) + len(mesh.tris)
    return sorted(out, key=lambda t: -out[t])


def shipped_models(root):
    return {os.path.splitext(f)[0].lower() for _, _, fs in os.walk(os.path.join(root, "out", "art", "w3d"))
            for f in fs if f.lower().endswith(".w3d")}


def fire_draws(root):
    """[(ini, draw tag, [(flags, model, particle lines)])] for every sagekit fire Draw shipped."""
    out = []
    for ini in glob.glob(os.path.join(root, "out", "data", "ini", "**", "*.ini"), recursive=True):
        lines = open(ini, encoding="latin-1").read().splitlines()
        i = 0
        while i < len(lines):
            m = DRAW_RE.match(lines[i].split(";")[0])
            i += 1
            if not m or not m.group(1).startswith("SagekitFire_"):
                continue
            states, depth, cur = [], 1, None
            while i < len(lines) and depth:
                line = lines[i].split(";")[0].strip()
                i += 1
                sm = STATE_RE.match(line)
                if sm and depth == 1:
                    cur = [frozenset(sm.group(1).upper().split()), None, 0]
                    states.append(cur)
                    depth += 1
                elif line.lower() == "end":
                    depth -= 1
                elif cur and line.lower().startswith("model"):
                    cur[1] = line.split("=", 1)[1].strip()
                elif cur and line.lower().startswith("particlesysbone"):
                    cur[2] += 1
            out.append((os.path.relpath(ini, root), m.group(1), states))
    return out


def swap_gaps(root, b, ours):
    """[(object, flags, model, EA's variant)]: shipped states drawing a model of ours whose EA swap of
    the sheet (snow, ice, damage, stonework) has no swap of ours beside it (our faces would stay healthy)."""
    from sagekit.formats.ini import parse_draws
    p = os.path.join(root, "work", "variants.json")
    variants = {k.lower(): v for k, v in json.load(open(p)).items()} if os.path.exists(p) else {}
    atlas, own = b.sheet_atlas.texture.lower(), b.own_diffuse.lower()
    out = []
    for ini in glob.glob(os.path.join(root, "out", "data", "ini", "**", "*.ini"), recursive=True):
        for d in parse_draws(open(ini, encoding="latin-1").read()):
            for st in d.states:
                if st.kind != "model" or (st.model or "").lower() not in ours:
                    continue
                have = {(a.lower(), c.lower()) for a, c in st.textures}
                for a, c in st.textures:
                    mine = variants.get(c.lower())
                    if a.lower() == atlas and mine and (own, mine.lower()) not in have:
                        out.append((d.object, " ".join(sorted(st.flags)), st.model, c))
    return out


def audit(bid, only_problems=False):
    root = os.path.join(BUILD, bid)
    rep = os.path.join(root, "work", "lifecycle.json")
    lines, problems = [], 0
    if not os.path.exists(rep):
        return ["%s: not built (no work/lifecycle.json)" % bid], 0
    try:
        from sagekit import registry
        b = registry.load(bid)
        shipped_name = b.shipped_name
    except Exception:                                   # a build folder whose recipe is gone
        b, shipped_name = None, (lambda m: m)
    models = json.load(open(rep))["models"]
    plan = {e["model"]: e for e in json.load(open(os.path.join(root, "work", "lifecycle_plan.json")))} \
        if os.path.exists(os.path.join(root, "work", "lifecycle_plan.json")) else {}
    ships = shipped_models(root)
    renders = os.path.join(root, "renders", "lifecycle")
    t_rep = os.path.getmtime(rep)
    no_fire = []                                        # flag sets whose body is not our intact one
    for m in models:
        code, detail = classify(m)
        name = m["model"]
        flags = sorted({" ".join(f) or "DEFAULT" for _, _, f in m.get("states", [])})
        notes = []
        if code in ("OURS", "DERIVED") and shipped_name(name).lower() not in ships:
            notes.append("NOT SHIPPED")
        png = os.path.join(renders, name.lower() + ".png")
        if code not in ("OURS", "DERIVED") and os.path.exists(png):
            notes.append("stale render" if os.path.getmtime(png) < t_rep else "render")
        if code == "EA-SHEET":
            tex = textures_of(os.path.join(root, "src"), name)
            detail += "; sheets " + ", ".join(tex[:3])
        if code != "DERIVED":
            no_fire += [(frozenset(f), code) for _, _, f in m.get("states", [])]
        bad = code.startswith("EA") or notes and notes != ["render"]
        problems += bool(bad)
        if bad or not only_problems:
            kind = (plan.get(name) or m).get("kind", "?")
            lines.append("  %-9s %-18s %-14s %s%s  [%s]" % (code, name, kind, detail,
                                                            "  (" + ", ".join(notes) + ")" if notes else "",
                                                            "; ".join(flags)[:80]))
    for ini, tag, states in fire_draws(root):
        for flags, model, n in states:
            lit = bool(model and model.lower() != "none") or n
            if lit and flags & NO_FIRE:
                problems += 1
                lines.append("  FIRE      %s: fire in %s (%s)" % (tag, " ".join(sorted(flags)), ini))
            elif lit and any(flags == f for f, _ in no_fire):
                problems += 1
                code = next(c for f, c in no_fire if flags == f)
                lines.append("  FIRE      %s: fire in %s over a %s body" % (tag, " ".join(sorted(flags)), code))
    if b is not None:                                   # snow / damage swaps on our models
        ours = {shipped_name(b.source).lower()} | {shipped_name(m["model"]).lower() for m in models
                                                   if classify(m)[0] in ("OURS", "DERIVED")}
        for obj, flags, model, ea in swap_gaps(root, b, ours):
            problems += 1
            lines.append("  SWAP      %s [%s] draws %s: EA swaps to %s, no swap of ours" % (obj, flags, model, ea))
    log = os.path.join(root, "work", "logs", "checks.log")
    if os.path.exists(log):
        fails = [x.strip() for x in open(log, errors="replace") if x.startswith("FAIL")]
        problems += len(fails)
        lines += ["  CHECK     " + f[:150] for f in fails]
    head = "%s: %d lifecycle models, %d problem(s)" % (bid, len(models), problems)
    return [head] + lines, problems


def main(argv):
    only = "--only-problems" in argv
    ids = []
    for a in [x for x in argv if not x.startswith("--")]:
        if "/" in a:
            ids.append(a)
        else:
            ids += sorted("%s/%s" % (a, d) for d in os.listdir(os.path.join(BUILD, a))
                          if not d.startswith("_") and os.path.isdir(os.path.join(BUILD, a, d)))
    if not ids:
        print(__doc__)
        return 2
    total = 0
    for bid in ids:
        out, n = audit(bid, only)
        total += n
        if n or not only:
            print("\n".join(out))
    print("\n%d building(s), %d problem(s)" % (len(ids), total))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
