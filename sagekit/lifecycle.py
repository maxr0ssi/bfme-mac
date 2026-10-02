"""Lifecycle models with our body: construction, really damaged and rubble follow EA's state.

EA draws a building under construction, really damaged or collapsing with models of their own
(DBTower_D2, DBFortress_A, ...). Their body is EA's healthy body cut into pieces: rigid meshes on
bones, or skins whose vertices name a bone each. The animation the INI pairs with the model moves
the pieces (the build rising out of the ground, the collapse), and EA's break faces (jagged cross
sections, the tops of half-built walls) close what the cut opened. The derive step already gives
models whose body is the healthy one (same triangles) our body; this step does the rest:

  1. EA's body pieces: the state's meshes painted from the building's sheet (not EA's other healthy
     meshes, e.g. the fortress's skegs), found again on EA's healthy body at the pose where the
     state is whole ("match": the rest pose, the first or the last frame, whichever fits best).
  2. Each EA piece face lies on EA's healthy surface or is a break face.
  3. Our body splits along EA's. Our faces on EA's healthy surface (EA's own faces, which every
     recipe keeps) take the exact shapes of EA's state faces there: each state surface face is
     projected into our face's plane and clipped to it, and the part goes to that face's piece and
     bone (a skin: its nearest vertex's); what no state face covers, EA broke away. What we added
     (a turret, a parapet) is a solid of its own, anchored on EA's healthy surface (the nearest point
     there): it goes whole to the piece holding most of its anchors, or is cut when EA's state has
     no surface within `tolerance` of them; its open rim is capped where it sat on EA's wall. A big
     solid whose anchors split evenly may instead go face by face, each part capped where the
     others were (it follows the collapse closer, but its seams can open): the step builds the
     model both ways and ships the one the checks like best (fewer of our faces' backs open to
     the sky). A collapse that ends with pieces sunk below the ground drops what of ours on them
     would still stick out.
  4. Our faces go into EA's pieces, in their pieces' bones' space: a piece without break faces
     takes its own share in place; a piece with break faces keeps them (EA's texture, recoloured
     by the faction sheets) and its share of ours goes to one host piece turned into a skin (one
     bone per vertex, vertices split at bone boundaries). Break faces with no EA piece left to hold
     them (a model that is one skin) join our host, painted from the nearest of our faces. Mesh
     names, the hierarchy, the HLOD (but for a host's bone, 0 like EA's skins), animations, FX and
     fire bones stay EA's, so the asset cache record is patched in place and every effect still
     attaches (and scripts that show or hide a piece by name still find it).
  A chained recipe (`base`) redesigns another mesh of the same model: its lifecycle models carry
  every link's body, each state piece going to the link whose healthy mesh it lies on.
  5. The house-colour model (our banners) is hidden in every state that moves or cuts the faces
     it hangs on (sagekit/house.py adds `ModelConditionState = <flags> / Model = None`).

Recipe settings, Building.lifecycle = {model name or "*": {setting: value}}:
    skip        the reason to leave this model to EA (recoloured); reported in lifecycle.json
    match       "auto", "rest", "first", "last" or a frame: the pose EA's body is whole in
    match_offset translation of the healthy reference into this state's model space (x, y, z)
    tolerance   units our faces may reach past EA's break before they are cut
    surface     units an EA face may lie from EA's healthy body and still be its surface
    body        EA's meshes that are the body (default: those painted from the building's sheet)
    keep        EA's meshes to leave alone although painted from the sheet
    solid       an added solid larger than this (units) whose anchors split evenly goes face by face;
                None: every solid goes whole; a list: each is built, the one the checks like best ships
    bend        our faces on EA's surface take its dents there (EA bends its rubble); default: all
                but construction, whose finished pose is the healthy body and gains only cracks from it
    seams       True: close each part of a solid split face by face where the other parts were
    cut         the share of an added solid's area over nothing of EA's state that cuts it whole
    force       ship the model even when the per-frame checks (depth, spread, open backs) fail it;
                by default such a model is left to EA and the report says why
    views       frames shown by the renders and checks: fractions of the animation, or "rest"
    backs       (share, reason): our faces' backs may open to the sky this much past EA's (0.04: 4%
                of our area), at every frame, instead of the checks' standard (2% standing, 10%
                moving); only where the renders show no hole the RTS camera sees. Nothing else is
                loosened, and the reason goes into every check line it touches (allowance())
    deep        (units, reason): how far our faces may go below EA's deepest on a bone (0.5)
    sheets      {EA texture: ours}: a state whose pieces (`body`) EA paints from another building's
                healthy sheet, laid out otherwise (the Angmar sanctum's build-up on the fortress's
                KBFortressX): no state copy of ours can carry its painting, but our faces keep our
                UVs, so that sheet's name in our pieces becomes our own diffuse's (same length)
    fill        EA's model is a remodel of its healthy body, not a cut of it (the Goblins' _A models:
                offset faces, trimmed underground, a narrower footprint), so the finished frame must
                still be our whole body. Nothing of ours is cut: a face of ours no state face covers
                whole, or a solid anchored where the state has no surface, rides its nearest state
                piece whole. Also for a damaged state whose pieces EA remodelled (Mordor's barricade
                D2 and fire-arrow tower D2: our shell would keep only scraps where EA's surface
                strays, and holes show): the pieces still move and fall as EA's do. (The checks of every construction model hold
                what stands where our healthy body stands to that body, the healthy checks'
                standard, not to EA's pieces: EA trims its build-ups at the ground, Angmar's
                citadel and Hall of Twilight among them, where the healthy body goes below it.)
"""
import json
import os
import re

from . import paths
from .formats.ini import VARIATION
from .formats.w3d import W3DFile
from .taxonomy import FLAG_STATES, State, states_of, upgrades_of

DEFAULTS = {"skip": False, "match": "auto", "match_offset": (0, 0, 0), "tolerance": 2.0, "surface": 1.5, "body": None, "keep": (),
            "solid": (15.0, None), "bend": None, "seams": True, "cut": 0.5, "views": None, "force": False,
            "fill": False}
LIFECYCLE_FLAGS = {f for f, s in FLAG_STATES.items() if s in (State.CONSTRUCTION, State.REALLY_DAMAGED, State.RUBBLE)} \
    | {"JUST_BUILT"}
BUILD_RE = re.compile(r"_A(SKN)?$", re.I)
KIND_ORDER = (State.CONSTRUCTION, State.REALLY_DAMAGED, State.RUBBLE, State.DAMAGED)


def settings(b, model):
    """DEFAULTS < the recipe's "*" < the recipe's entry for this model (any case)."""
    own = getattr(b, "lifecycle", {}) or {}
    out = dict(DEFAULTS)
    out.update(own.get("*", {}))
    out.update(next((v for k, v in own.items() if k.lower() == model.lower()), {}))
    return out


def allowance(s, key, standard):
    """(limit, " (the recipe's allowance: why)") of a `backs` / `deep` setting, else (standard, "")."""
    a = s.get(key)
    return (max(standard, float(a[0])), " (the recipe's allowance: %s)" % a[1]) if a else (standard, "")


def check_settings(b):
    """ValueError for a lifecycle allowance without a number and a reason, or a `sheets` entry that
    is not one of our own textures as long as EA's (sagekit validate)."""
    for model, s in (getattr(b, "lifecycle", {}) or {}).items():
        for ea, ours in (s.get("sheets") or {}).items():
            if ours not in b.texture_names().values() or len(ea) != len(ours):
                raise ValueError("lifecycle %s sheets: %s -> %s is none of our own textures as long" % (model, ea, ours))
        for key in ("backs", "deep"):
            a = s.get(key)
            if a is not None and not (isinstance(a, (tuple, list)) and len(a) == 2 and
                                      isinstance(a[0], (int, float)) and isinstance(a[1], str) and a[1].strip()):
                raise ValueError("lifecycle %s %s: (number, reason), not %r" % (model, key, a))


def plan(b, install, derived=()):
    """[entry] for every model of the body family the covered Draw modules show besides the healthy
    one: {model, kind, states [[ini, object, flags]], skeleton, animation {file, name, mode},
    derived (True: the derive step built it; only its banner is judged here), settings}. Only the
    recipe's own build variation's states (Building.own_states: B's models are B's recipe's), and
    no model without meshes (OBBFoundationX, a foundation's empty stand-in: nothing to rebuild).
    The object is the one the building's INI defines (a ChildObject for the modules it inherits)."""
    out, empty = {}, set()                          # (a chained recipe's models carry the whole chain)
    for obj, draws in b.objects(install).items():
        for d in draws:
            if not b.covers(d):
                continue
            own = b.own_states(d)
            anims = [s for s in own if s.kind == "animation" and s.animations]
            for st in own:
                m = st.model
                if st.kind != "model" or not m or m.lower() in ("none", b.source.lower()) or m.lower() in empty:
                    continue
                if not install.has_model(m):
                    continue
                if m.lower() not in out and not W3DFile(install.read(install.model_path(m))).meshes:
                    empty.add(m.lower())
                    continue
                e = out.setdefault(m.lower(), {"model": m, "states": [], "animations": []})
                e["states"].append([d.file, obj, sorted(st.flags)])
                a = _animation_for(st.flags, anims)
                if a and a not in e["animations"]:
                    e["animations"].append(a)
    entries = []
    for key, e in sorted(out.items()):
        kinds = set().union(*(states_of(f) for _, _, f in e["states"]))
        e["kind"] = next((k.value for k in KIND_ORDER if k in kinds), "other")
        if BUILD_RE.search(e["model"]):             # EA's name for a construction model (an upgrade's
            e["kind"] = State.CONSTRUCTION.value    # build shows under purchase flags, not construction's)
        e["derived"] = key in {x.lower() for x in derived}
        e["skeleton"] = W3DFile(install.read(install.model_path(e["model"]))).skeleton()
        e["animation"] = _pick(e.pop("animations"), install)
        e["settings"] = settings(b, e["model"])
        entries.append(e)                           # (a recipe's skip is reported, with its reason)
    return entries


def _animation_for(flags, anims):
    """The animation state an INI pairs with a model state: the same flags, else the one sharing
    most of them (no flags the model state lacks)."""
    best, score = None, -1
    for a in anims:
        if not a.flags <= flags:
            continue
        s = len(a.flags & flags)
        if s > score and (a.flags or not flags):
            best, score = a, s
    if best is None:
        return None
    mode = best.modes[0] if best.modes else "LOOP"
    return {"name": best.animations[0], "mode": mode}


def _pick(anims, install):
    """The animation that defines the state: a MANUAL one (construction follows build progress),
    else the first; with the file that holds it (the part after the skeleton's name)."""
    if not anims:
        return None
    a = next((x for x in anims if x["mode"] == "MANUAL"), anims[0])
    name = a["name"].split(".")[-1]
    if not install.has_model(name):
        return None
    names = W3DFile(install.read(install.model_path(name))).object_names()
    if not any(n.upper() == "A*" + a["name"].upper() for n in names):
        return None                             # EA names one its file lacks (DBCitadel_D2): it stands still
    return dict(a, file=name.lower() + ".w3d")


def view_frames(entry, frames):
    """The frames the player sees: a build rises (a MANUAL animation follows construction
    progress), a collapse plays once and holds its last frame; a model without one stands still."""
    views = entry["settings"]["views"]
    a = entry["animation"]
    if views is None:
        views = ["rest"] if not a else [0.35, 0.7, 1.0] if a["mode"] == "MANUAL" else [0.0, 0.4, 1.0]
    return [None if v == "rest" else int(round(v * (frames - 1))) if isinstance(v, float) else int(v) for v in views]


def unmapped(links, install, entry, names):
    """[EA texture] of an EA state model's body meshes (Building.state_body, every link's) that the
    build records map to none of ours (`names`: Workspace.own_names, every link's, lower case), so
    the step must leave those meshes to EA: [] once the extract step's Building.variants and
    normal_variants hold them all. A diffuse that is no state copy of the sheet (state_sheet) is
    meant to stay EA's and is not counted."""
    from .building import state_body, state_sheet
    meshes = W3DFile(install.read(install.model_path(entry["model"]))).meshes
    s = entry["settings"]
    out = []
    for b in links:
        healthy = set(W3DFile(install.read(install.model_path(b.source))).meshes) - {x.target for x in links}
        for t in state_body(meshes, b.target, healthy, names, s["body"], s["keep"]):
            if t.lower() in names or t in out:
                continue
            if "_nrm" in t.lower() or state_sheet(install, b.sheet_atlas.texture, t):
                out.append(t)
    return out


def self_check():
    """Game-free check of the framework's state-texture rules (run by `sagekit validate`), on the
    shapes of EA's state models the audit of 2026-10-01 found, and of the mesh writer carrying EA's
    two-bone skin weights: [] when they hold."""
    from types import SimpleNamespace as M
    from .building import state_body, state_sheet
    from .taxonomy import own_variant_name
    fails = []

    def mesh(*textures):
        return M(tris=[(0, 1, 2)], textures=list(textures))
    cases = [   # (meshes, target, EA's other healthy meshes, ours, expected)
        ({"ARROWTOWER": mesh("KBFortressXD1_NRM.tga", "KBFortressX_D1.tga")}, "ARROWTOWER", set(),
         {"kbfortressb.tga", "kbfortressb_nrm.tga"}, ["KBFortressXD1_NRM.tga", "KBFortressX_D1.tga"]),
        ({"DP9": mesh("KBFortressX_D1.tga", "KBFortressX_NRM.tga")}, "KBFKENNEL", set(),
         {"kbfortressx.tga", "kbfortressx_nrm.tga"}, ["KBFortressX_D1.tga", "KBFortressX_NRM.tga"]),
        ({"N_WINDOW": mesh("WBCave.tga", "WBCave_NRM.tga"),
          "V2": mesh("MBTrollPit_D.tga", "MBTrollPit_NRM.tga"),
          "SIEGEWORKS1": mesh("MBSeigeWork1D.tga", "MBSeigeWork1_NRM.tga"),
          "GBSTABLE_05": mesh("GBStable.tga", "GBStableHorses.tga", "RUFrmHors04.tga")}, "MBTROLLPIT", {"V2"},
         {"mbtrollpit.tga", "mbtrollpit_nrm.tga", "gbstable.tga"}, []),
    ]
    for meshes, target, others, mine, want in cases:
        got = state_body(meshes, target, others, mine)
        if got != want:
            fails.append("state_body(%s): %s, not %s" % (list(meshes), got, want))
    for s, want in (({}, (0.02, "")), ({"backs": (0.05, "why")}, (0.05, " (the recipe's allowance: why)")),
                    ({"backs": (0.01, "why")}, (0.02, " (the recipe's allowance: why)"))):
        if allowance(s, "backs", 0.02) != want:                 # an allowance only ever loosens
            fails.append("allowance(%s): %s, not %s" % (s, allowance(s, "backs", 0.02), want))
    archives = M(owner=lambda member: member)               # every sheet exists
    for sheet, t, want in (("KBFortressB.tga", "KBFortressX_D1.tga", True),
                           ("MBSeigeWork2.tga", "MBSeigeWork2D.tga", True),
                           ("KBFortressB.tga", "KBFortressX.tga", False)):
        if state_sheet(archives, sheet, t) != want:
            fails.append("state_sheet(%s, %s) is not %s" % (sheet, t, want))
    for sheet, own, t, want in (("KBHall.tga", "KBHalH.tga", "KBHall_NRM.tga", "KBHalH_NRM.tga"),
                                ("KBFortressB.tga", "KBFortressH.tga", "KBFortressX_D1.tga", "KBFortressH_D1.tga"),
                                ("MBSeigeWork2.tga", "MBSeigeWorkH.tga", "MBSeigeWork2D.tga", "MBSeigeWorkHD.tga"),
                                ("KBFortressB.tga", "KBFortressH.tga", "KBFortressXD1_NRM.tga",
                                 "KBFortressHDH_NRM.tga")):
        got = own_variant_name(sheet, own, t, same_length=True)
        if got != want or len(got) != len(t):
            fails.append("own_variant_name(%s, %s, %s): %s, not %s as long as EA's" % (sheet, own, t, got, want))
    from .formats.w3dmesh import check_skin         # EA's skin weights survive a rebuilt piece
    return fails + ["skin weights: " + f for f in check_skin()]


# ------------------------------------------------------------------------------------ the step
def run(step):
    """The pipeline's lifecycle step (host side): plan, extract EA's files, build in Blender."""
    b, ws, g = step.b, step.ws, step.p.install
    entries = plan(b, g, ws.derived)
    for e in entries:                               # (a derived model's file is the derive step's)
        own = e["model"].lower() + ".w3d"
        files = [f for f in [own, e["skeleton"], (e["animation"] or {}).get("file")]
                 if f and not (e["derived"] and f == own)]
        for f in files:
            dest = ws.path("src", f)
            with open(dest, "wb") as fh:
                fh.write(g.read(g.model_path(f[:-4])))
    with open(ws.path("work", "lifecycle_plan.json"), "w") as fh:
        json.dump(entries, fh, indent=1)
    report = ws.path("work", "lifecycle.json")
    if os.path.exists(report):
        os.remove(report)
    if not entries:
        print("  no lifecycle models")
        with open(report, "w") as fh:
            json.dump({"models": []}, fh)
        return
    step.blender("lifecycle")
    keep = {g.model_path(b.shipped_name(m)).lower() for m in [b.source] + list(ws.derived) + ws.lifecycle}
    root = ws.path("out", "art", "w3d")
    for d, _, names in os.walk(root):                  # models an earlier run built and this one did not
        for f in names:
            rel = os.path.relpath(os.path.join(d, f), ws.path("out")).replace(os.sep, "\\").lower()
            if rel not in keep:
                os.remove(os.path.join(d, f))
                print("  removed %s (no longer rebuilt)" % rel)
    for m in json.load(open(report))["models"]:
        print("  %-16s %-14s %s" % (m["model"], m["kind"], m["summary"]))
        for w in m.get("warnings", []):
            print("      ! " + w)


def hidden_states(ws):
    """[(ini, object, flags)]: the states whose model moves or cuts the faces our banners hang on,
    where the house-colour model must not be drawn. Only the flags that make the state count: the
    engine picks the state sharing most flags with the object's, so a hiding state that also named
    SNOW would win over the default in plain snow. Upgrades' states are left out (the house model
    is shared by the building and its add-ons), but for an add-on's own house model: its Draw
    mirrors the add-on's states (Building.addon_conditions), so these are the add-on's states as
    they stand ([FORTRESS_IMPROVEMENT_3 USER_1]: the anvil under construction), the mirrored state
    then drawing nothing (sagekit/house.py)."""
    p = ws.path("work", "lifecycle.json")
    if not os.path.exists(p):
        return []
    addon = bool((ws.house or {}).get("conditions"))
    out = []
    for m in json.load(open(p))["models"]:
        if m.get("banner", {}).get("supported", True):
            continue
        for ini, obj, flags in m["states"]:
            if addon:
                if (ini, obj, sorted(flags)) not in out:
                    out.append((ini, obj, sorted(flags)))
                continue
            own = sorted(f for f in flags if f in LIFECYCLE_FLAGS)
            # a build variation's state keeps its flag: [BUILD_VARIATION_TWO REALLYDAMAGED] must outscore
            # the house draw's [BUILD_VARIATION_TWO] (Building.house_conditions) in a really damaged B
            own = sorted(own + [f for f in flags if f.startswith(VARIATION)]) if own else own
            if own and not upgrades_of(flags) and (ini, obj, own) not in out:
                out.append((ini, obj, own))
    return out


def house_ops(ws, draws):
    """INI ops for the house-colour Draw modules [[ini, object, tag]] of one building: its model
    hidden in hidden_states(ws) - for sagekit/house.py's record. Matched by object (object names are
    unique): a ChildObject's lifecycle states live in its parent's file (GondorFarm's in
    farminterface.ini), its house draw in its own; the state goes where the house draw is."""
    out = {}
    for ini, obj, flags in hidden_states(ws):
        for dini, dobj, tag in draws:
            if dobj == obj:
                out.setdefault(dini, []).append(("state", obj, tag, list(flags), "None"))
    return out


def render(step, res="1100x760", spp="48"):
    """EA's state against ours at the frames the player sees (Blender): renders/lifecycle/<model>.png,
    a row per frame, EA's (as the installed faction draws it: recoloured sheets) left, ours right."""
    ws = step.ws
    r = ws.path("renders", "lifecycle")
    os.makedirs(r, exist_ok=True)
    p = ws.path("work", "lifecycle.json")
    report = json.load(open(p))["models"] if os.path.exists(p) else []
    for m in [x for x in report if x["built"] or x.get("derived") and x.get("views") != [None]]:   # a static
        # derived model is the render step's compare_<model>_*.png already
        model = m["model"]
        member = step.p.install.model_path(step.b.shipped_name(model))
        refs = {}
        for path in (ws.path("src", model.lower() + ".w3d"), ws.out(member)):
            refs.update(step.references(path, recoloured=True))
        for who in ("ea", "ours"):
            step.blender("lifecycle_render", log_as="render_%s_%s" % (model.lower(), who), model=model, who=who,
                         out=r, res=res, spp=spp, **refs)
        rows = []
        for f in m["views"]:
            tag = "rest" if f is None else str(f)
            pair = []
            for who, text in (("ea", "EA %s (recoloured, as installed)" % model), ("ours", "%s %s" % (step.b.id, model))):
                src = os.path.join(r, "%s_%s_%s.png" % (model.lower(), who, tag))
                dst = os.path.join(r, "_%s_%s_%s.png" % (model.lower(), who, tag))
                label = " %s - %s " % (text, "rest pose" if f is None else "frame %s" % f)
                step.tool(["magick", src, "-font", step.FONT, "-gravity", "NorthWest", "-fill", "#f2ead8",
                           "-undercolor", "#0008", "-pointsize", "26", "-annotate", "+14+10", label, dst])
                pair.append(dst)
            row = os.path.join(r, "_%s_row_%s.png" % (model.lower(), tag))
            step.tool(["magick", pair[0], "-size", "8x%s" % res.split("x")[1], "xc:#141414", pair[1], "+append", row])
            rows.append(row)
        out = os.path.join(r, model.lower() + ".png")
        step.tool(["magick"] + rows + ["-background", "#141414", "-splice", "0x8", "-append", out])
        print("  " + os.path.relpath(out, paths.REPO))
