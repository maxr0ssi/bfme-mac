"""Real fire: the game's own particle systems on bones, a faction standard like night lights.
A recipe declares `fire_points = [(x, y, z, kind)]` in the healthy model's space (the target's own
coordinates when it hangs on an identity bone, as most do); the game draws flames, smoke and embers
there that flicker, glow additively and read at night. Painted flame cones read as plastic.

The engine side (read from RotWK's game.dat and EA's INIs; docs/ART.md "Fire"):
  - `ParticleSysBone = <bone> <system> [FollowBone:Yes]` in a ModelConditionState starts the
    system at that bone of the state's own model; a bone the model lacks (or `NONE`, or a state
    whose Model is None) puts it at the object's origin. Pivot names hold 15 characters.
  - Every ModelConditionState starts as a copy of the Draw's DefaultModelConditionState, particle
    lines included (game.dat 0x4c8133 copies the default into each new state; EA's own comment:
    "Not DefaultConditionState, because that keyword copies anything in here to every other
    state"). A line in the healthy default would burn in the rubble, the building site and the
    POST_RUBBLE state, whose Model is None (at the origin).

So our fire never touches EA's Draw modules, models or animations. Per Draw module the recipe
covers, a Draw of our own, after EA's pattern for effects (the Dwarven hearth's and statue's
`TheHealEffect`): no default state, first `ModelConditionState = NONE`, then EA's condition states
in EA's order (so the engine picks the same state in both), each showing the fire rig with the
lines where the state draws our intact body (healthy, damaged, snow, stonework), Model None
elsewhere (really damaged, rubble, building site, placement ghost: EA's own damage fires take
over; nothing burns over rubble). The rig, `<model>_FX.w3d`, is a model without meshes like EA's
OBBFoundationX (hierarchy, one invisible collision-free box, HLOD): its root and one pivot per
fire point, FIRE01.., filed in asset.dat as a copy of OBBFoundationX's record.

Hooks: the pipeline's `fire` step writes the rig (after ship, before ini), Building.ini_ops adds
the Draw modules (`ini_ops`), Building.cache_ops files the rig (`cache_ops`), the check suite
runs `checks` (sagekit/fire_checks.py) and the render step `render` (markers over the render: the
particles themselves only show in game). A recipe without fire_points gets none of it. A kind
drawing a system of our own (Sagekit*, sagekit/fire_systems.py) adds every one of them to EA's
particle INI in the same ini step.
"""
import math
import os
import struct

from .formats.ini import ANIM_OPENER, DRAW_RE, OBJECT_RE, STATE_OPENERS, strip
from .formats.w3d import (BOX, HIERARCHY, HIERARCHY_HEADER, HLOD, HLOD_HEADER, HLOD_SUB_OBJECT, PIVOT_FIXUPS,
                          PIVOTS, chunk_bytes)
from .taxonomy import State, states_of

HLOD_LOD_ARRAY, HLOD_SUB_OBJECT_ARRAY_HEADER = 0x702, 0x703

# kind -> particle systems: EA's (in data\ini\fxparticlesystem.ini or particlesystem.ini, each drawn by one
# of EA's own buildings or props in its healthy state) or, named Sagekit*, our own copies of EA's (fire_systems.py)
KINDS = {
    # since the fire budget (2026-10-04) every kind but the unused pyre draws lean copies of EA's systems
    # (sagekit/fire_lean.py: fewer, slightly larger, longer-lived particles over the same volume, in the
    # same colours); the comment names EA's own building or prop that burns the EA system copied:
    "chimney": ("SagekitLeanSiegeWorkFire", "SagekitLeanSmokeChimney"),  # Isengard siege works; tavern chimney
    "furnace": ("SagekitLeanFurnaceFire", "SagekitLeanFurnaceSparks"),   # the civilian furnace; Isengard camp
    "forge": ("SagekitLeanForgeCoal", "SagekitLeanForgeEmbers"),         # the Men forge: coal glow, rising embers
    "hearth": ("SagekitLeanFurnaceFire", "SagekitLeanCampfireEmbers"),   # a broad low bed of fire; campfire embers
    "crucible": ("SagekitLeanForgeCoal", "SagekitLeanFurnaceSparks"),    # a molten glow and a few sparks
    "brazier": ("SagekitLeanFireTorch", "SagekitLeanTorchSmoke"),        # Isengard tavern's torches
    "grate": ("SagekitLeanForgeCoal", "SagekitLeanCampfireEmbers"),      # hot coals under a grating
    "embers": ("SagekitLeanCampfireEmbers",),
    "pyre": ("FireBuildingLarge", "SmokeBuildingLarge"),  # EA's burning structures' big fire and heavy plume:
                                                          # over the fire budget alone (103 live), used nowhere
    "smoke": ("SagekitLeanSmokeChimney",),              # a thin dark column only (Isengard and Mordor taverns)
    # green witch-fire and cold fire: our own colours of furnaceFire / SmokeChimney (sagekit/fire_systems.py)
    "witchfire": ("SagekitWitchFire", "SagekitWitchSmoke"),  # Morgul green, a modest dark plume
    "witchflame": ("SagekitWitchFire",),                # the green fire alone (a second flame in one bowl)
    "plume": ("SagekitLeanSmokePlume",),                # EA's heavy dark plume alone (over a forge's flue)
    "coldfire": ("SagekitColdFire", "SagekitColdSmoke"),  # ice-blue to white, a blue-black plume (Angmar)
    "coldflame": ("SagekitColdFire",),                  # the cold fire alone (more flames in one hearth)
    # appended with the fire budget: a part of a kind, for points that share a neighbour's smoke or sparks
    "torch": ("SagekitLeanFireTorch",),                 # the brazier's flame without its smoke
    "coals": ("SagekitLeanForgeCoal",),                 # the grate's glow without its embers
    "flame": ("SagekitLeanFurnaceFire",),               # the hearth's / furnace's fire alone
}
NO_FIRE = {State.CONSTRUCTION, State.PLACEMENT, State.EDITOR, State.RUBBLE}
LIKE = "obbfoundationx.w3d"             # EA's meshless model whose asset.dat record the rig copies
TAG = "SagekitFire_"                    # + the covered Draw's tag + the rig's name (two variations' recipes)
MAX_NAME = 15                           # W3D names: 16 bytes with the terminator


def points(b):
    """[(bone, (x, y, z), kind)] from the recipe's fire_points; ValueError on a malformed entry."""
    out = []
    for i, p in enumerate(getattr(b, "fire_points", None) or ()):
        ok = len(p) == 4 and p[3] in KINDS and all(isinstance(c, (int, float)) and math.isfinite(c) for c in p[:3])
        if not ok:
            raise ValueError("%s: fire_points[%d] = %r: want (x, y, z, kind), kind one of %s" % (b.id, i, p, ", ".join(KINDS)))
        out.append(("FIRE%02d" % (i + 1), tuple(float(c) for c in p[:3]), p[3]))
    if len(out) > 99:
        raise ValueError("%s: %d fire points (99 at most)" % (b.id, len(out)))
    return out


def rig_name(b):
    return b.shipped_name(b.source)[:MAX_NAME - 3] + "_FX"


def rig_file(b):
    return rig_name(b).lower() + ".w3d"


def rig_member(b):
    from .game import Install
    return Install.model_path(rig_name(b))


def members(b):
    """{archive path} of the files this standard ships for b (Derive keeps them)."""
    return {rig_member(b).lower()} if points(b) else set()


def systems(b):
    """Every particle system b's fire draws, in first use order."""
    return list(dict.fromkeys(s for _, _, kind in points(b) for s in KINDS[kind]))


# ------------------------------------------------------------------------------------ the rig
def _name(s, n):
    s = s.upper().encode("latin-1")
    if len(s) >= n:
        raise ValueError("W3D name %r longer than %d" % (s, n - 1))
    return s + b"\0" * (n - len(s))


def rig_bytes(name, pts):
    """A meshless W3D in OBBFoundationX's form: HIERARCHY (ROOTTRANSFORM and one pivot per point,
    parent the root, no rotation), a BOX `<NAME>.OB` (oriented, no collision type, 0.01 across)
    on the root, and an HLOD of one LOD holding the box."""
    piv = [("ROOTTRANSFORM", -1, (0.0, 0.0, 0.0))] + [(bone, 0, xyz) for bone, xyz, _ in pts]
    head = struct.pack("<I", 0x00040001) + _name(name, 16) + struct.pack("<I3f", len(piv), 0, 0, 0)
    body = b"".join(_name(n, 16) + struct.pack("<i3f3f4f", parent, *t, 0, 0, 0, 0, 0, 0, 1) for n, parent, t in piv)
    fix = struct.pack("<12f", 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0) * len(piv)
    hier = chunk_bytes(HIERARCHY, chunk_bytes(HIERARCHY_HEADER, head, False) + chunk_bytes(PIVOTS, body, False)
                       + chunk_bytes(PIVOT_FIXUPS, fix, False), True)
    box_name = name + ".OB"
    box = chunk_bytes(BOX, struct.pack("<II", 0x00010000, 1) + _name(box_name, 32) + bytes(4)
                      + struct.pack("<6f", 0, 0, 0, 0.005, 0.005, 0.005), False)
    lod = chunk_bytes(HLOD_SUB_OBJECT_ARRAY_HEADER, struct.pack("<If", 1, 3.4028234663852886e38), False) \
        + chunk_bytes(HLOD_SUB_OBJECT, struct.pack("<I", 0) + _name(box_name, 32), False)
    hlod = chunk_bytes(HLOD, chunk_bytes(HLOD_HEADER, struct.pack("<II", 0x00010000, 1) + _name(name, 16) + _name(name, 16), False)
                       + chunk_bytes(HLOD_LOD_ARRAY, lod, True), True)
    return hier + box + hlod


# ------------------------------------------------------------------------------------ the Draw modules
def mirror(text, obj, tag):
    """(IgnoreConditionStates value or None, [(flags, model)]) of one Draw module's model states in
    order: the default as flags (), a state without its own Model showing the default's."""
    cur, depth, script, st, states, ignore = None, 0, False, None, [], None
    for raw in text.splitlines():
        line = strip(raw)
        if not line:
            continue
        m = OBJECT_RE.match(line)
        if m and not raw[:1].isspace():
            if depth:
                break
            cur = m.group(2)
            continue
        if not depth:
            m = DRAW_RE.match(line)
            depth = 1 if m and cur == obj and m.group(2) == tag else 0
            continue
        low = line.lower()
        key, _, val = (x.strip() for x in line.partition("="))
        k = key.lower()
        if script:
            script = not low.startswith("endscript")
        elif low.startswith("beginscript"):
            script = True
        elif low == "end":
            depth -= 1
            st = None if depth <= 1 else st
            if depth == 0:
                break
        elif depth == 1 and k in STATE_OPENERS:
            depth += 1
            st = None
            if k in ("defaultmodelconditionstate", "modelconditionstate"):
                flags = () if k.startswith("default") else tuple(f for f in val.upper().split() if f != "NONE")
                st = [flags, None]
                states.append(st)
        elif depth == 2 and k == ANIM_OPENER:
            depth += 1
        elif depth == 1 and k == "aliasconditionstate":
            raise ValueError("%s %s: AliasConditionState is not mirrored yet" % (obj, tag))
        elif depth == 1 and k == "ignoreconditionstates":
            ignore = val
        elif st is not None and depth == 2 and k == "model":
            st[1] = val
    default = next((m for f, m in states if f == ()), None)
    return ignore, [(f, m if m is not None else default) for f, m in states]


def plan(b, install):
    """[{file, object, after, tag, ignore, states: [(flags, burns)]}] per Draw module b covers in
    which something burns: a state burns where it shows our intact body (b.source or a derived
    model) and is none of NO_FIRE's; a Draw of two build variations burns in b's own states only."""
    if not points(b):
        return []
    burning = {b.source.lower()} | {m.lower() for m in b.derived_bodies(install)}
    texts, out, seen = {}, [], set()
    for draws in b.objects(install).values():
        for d in draws:
            if not b.covers(d) or (d.file, d.object, d.tag) in seen:
                continue
            seen.add((d.file, d.object, d.tag))
            if d.file not in texts:
                texts[d.file] = install.read(d.file).decode("latin-1")
            ignore, states = mirror(texts[d.file], d.object, d.tag)
            own = {frozenset(f for f in s.flags if f != "NONE") for s in b.own_states(d) if s.kind == "model"}
            burns = [(f, frozenset(f) in own and (m or "").lower() in burning and not states_of(f) & NO_FIRE)
                     for f, m in states]
            if not states or states[0][0]:
                raise ValueError("%s %s: no default or NONE state first to mirror" % (d.object, d.tag))
            if any(x for _, x in burns):
                out.append({"file": d.file, "object": d.object, "after": d.tag, "tag": "%s%s_%s" % (TAG, d.tag, rig_name(b)),
                            "ignore": ignore, "states": burns})
    return out


def block(b, draw):
    """The lines of our Draw module (unindented; add_draw_after indents them like EA's)."""
    rig, pts = rig_name(b), points(b)
    out = ["Draw = W3DScriptedModelDraw %s" % draw["tag"],
           "\t; sagekit fire (sagekit/fire.py): %s's states mirrored, no default state (it would copy" % draw["after"],
           "\t; its fire into every state); the rig %s's bones, fire only where our body stands" % rig]
    if draw["ignore"]:
        out.append("\tIgnoreConditionStates = %s" % draw["ignore"])
    for flags, burns in draw["states"]:                 # the first is the default's: NONE
        out += ["\tModelConditionState = %s" % (" ".join(flags) or "NONE"), "\t\tModel = %s" % (rig if burns else "None")]
        if burns:
            out += ["\t\tParticleSysBone = %s %s" % (bone, s) for bone, _, kind in pts for s in KINDS[kind]]
        out.append("\tEnd")
    return out + ["End"]


def own_systems(b):
    """The systems of our own b's fire draws (sagekit/fire_systems.py)."""
    from .fire_systems import names
    return [s for s in systems(b) if s.lower() in names()]


def ini_ops(b, install):
    """{INI archive path: [("fire_draw", object, after tag, tag, lines)]} (sagekit/formats/ini.py),
    and when b draws a system of our own, every one of them added to EA's particle INI."""
    out = {}
    for d in plan(b, install):
        out.setdefault(d["file"], []).append(("fire_draw", d["object"], d["after"], d["tag"], tuple(block(b, d))))
    if out and own_systems(b):
        from . import fire_systems
        out.setdefault(fire_systems.MEMBER, []).append(fire_systems.ops(install))
    return out


def cache_ops(b):
    """Building.cache_ops entries: the rig filed as a copy of OBBFoundationX's record."""
    return [("model", rig_file(b), LIKE)] if points(b) else []


def game_systems(install):
    """{lower-case name} of every particle system the game's INIs define: the two particle INIs the
    game loads (fxparticlesystemcustom.ini is not loaded; sagekit/fire_systems.py LOADED)."""
    import re

    from .fire_systems import LOADED
    out = set()
    for m in install.members("data\\ini"):
        if m in LOADED:
            for x in re.finditer(r"^[ \t]*(?:FX)?ParticleSystem[ \t]+(\S+)", install.read(m).decode("latin-1"), re.I | re.M):
                out.add(x.group(1).lower())
    return out


# ------------------------------------------------------------------------------------ the step
def run(step):
    """The pipeline's fire step: the rig into out/ (a stale one out), the plan printed."""
    from .pipeline import StepFailed
    b, g, ws = step.b, step.p.install, step.ws
    dest = ws.out(rig_member(b))
    pts = points(b)
    if not pts:
        if os.path.exists(dest):
            os.remove(dest)
            print("  removed %s (no fire points)" % os.path.basename(dest))
        return
    if b.per_level:
        raise StepFailed("%s: a `base` recipe's mesh is shown per upgrade level; its fire would burn before the "
                         "upgrade - declare fire_points on the base's body" % b.id)
    name = rig_name(b)
    if g.has_model(name) or any(c.has_model(rig_file(b)) for c in g.asset_caches().values()):
        raise StepFailed("%s: the fire rig's name %s is one of EA's" % (b.id, name))
    missing = [s for s in systems(b) if s.lower() not in game_systems(g) and s not in own_systems(b)]
    if missing:
        raise StepFailed("%s: particle systems the game does not define: %s" % (b.id, ", ".join(missing)))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as fh:
        fh.write(rig_bytes(name, pts))
    print("  %s: %d fire points (%s)" % (os.path.relpath(dest, ws.root), len(pts), ", ".join(
        "%d %s" % (sum(1 for p in pts if p[2] == k), k) for k in KINDS if any(p[2] == k for p in pts))))
    draws = plan(b, g)
    for d in draws:
        on = [" ".join(f) or "(default)" for f, x in d["states"] if x]
        off = [" ".join(f) or "(default)" for f, x in d["states"] if not x]
        print("  %s %s: burns in %s; none in %s" % (d["object"], d["tag"], ", ".join(on), ", ".join(off) or "-"))
    if not draws:
        raise StepFailed("%s: fire_points, but no state of its Draw modules shows the healthy body" % b.id)


def render(step):
    from .fire_checks import render as markers
    markers(step)


def checks(b, ws, r):
    from .fire_checks import checks as run_checks
    run_checks(b, ws, r)
