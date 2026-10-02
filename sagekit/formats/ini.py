"""SAGE INI, as far as art is concerned: which model, textures and animations an object draws in
which state.

A full SAGE INI grammar is per-field (the engine knows which keys open blocks). Art needs only the
Draw modules, whose grammar is small and regular:

    Object <Name>                                   (or ChildObject / ObjectReskin <Name> <Parent>)
      Draw = <DrawType> <Tag>
        WeatherTexture = SNOWY <snow.tga>             (the model's sheet in that weather)
        DefaultModelConditionState | ModelConditionState = FLAG FLAG ...
          Model = <name> | Texture = <old.tga> <new.tga> | ...
        End
        AnimationState | IdleAnimationState | TransitionState = ...
          Animation = <Name>
            AnimationName = <SKELETON>.<ANIMATION>
          End
          BeginScript ... EndScript
        End
      End

Comments start with ';' or '//'. `#define NAME value` macros are substituted in values.
"""
import re

OBJECT_RE = re.compile(r"^(Object|ChildObject|ObjectReskin)\s+(\S+)", re.I)
DRAW_RE = re.compile(r"^Draw\s*=\s*(\S+)\s+(\S+)", re.I)
DEFINE_RE = re.compile(r"^#define\s+(\S+)\s+(.*)$", re.I)
STATE_OPENERS = ("defaultmodelconditionstate", "modelconditionstate", "animationstate",
                 "idleanimationstate", "transitionstate")
ANIM_OPENER = "animation"


def strip(line):
    line = line.split(";", 1)[0]
    line = line.split("//", 1)[0]
    return line.strip()


class State:
    """One condition or animation state of a Draw module."""

    def __init__(self, kind, flags, line):
        self.kind = kind                    # 'model' (ModelConditionState) or 'animation'
        self.flags = frozenset(flags)
        self.line = line
        self.model = None
        self.textures = []                  # [(old, new)] texture swaps
        self.animations = []                # 'SKELETON.ANIMATION'
        self.modes = []                     # their AnimationMode (ONCE, MANUAL, LOOP...), in order

    def __repr__(self):
        return "<%s %s model=%s tex=%s anim=%s>" % (self.kind, " ".join(sorted(self.flags)) or "DEFAULT",
                                                    self.model, self.textures, self.animations)


class Draw:
    def __init__(self, obj, dtype, tag, line):
        self.object, self.type, self.tag, self.line = obj, dtype, tag, line
        self.states = []
        self.fields = {}                    # module-level keys (e.g. StaticModelLODMode)
        self.weather = []                   # [(WEATHER, texture)]: `WeatherTexture = SNOWY X_snow.tga`, the
                                            # model's sheet in that weather (W3DFloorDraw bibs, streaks)

    def models(self):
        return sorted({s.model for s in self.states if s.model and s.model.lower() != "none"}, key=str.lower)


PARENT_RE = re.compile(r"^(Object|ChildObject|ObjectReskin)[ \t]+(\S+)(?:[ \t]+([^\s;/]+))?", re.I | re.M)
VARIATION = "BUILD_VARIATION_"      # BUILD_VARIATION_ONE / _TWO: the body a fortress pad gives an expansion


def parse_objects(text):
    """{object: parent or None} for the objects a file defines (a ChildObject or ObjectReskin
    inherits its parent's modules, Draw modules included)."""
    return {m.group(2): (m.group(3) if m.group(1).lower() != "object" else None) for m in PARENT_RE.finditer(text)}


def variation_states(draw, source, flag=None):
    """The states of a Draw module that belong to the build variation showing `source`. A Draw that
    shows two bodies under BUILD_VARIATION_ONE / _TWO (EA's GBFDOTOWA / GBFDOTOWB) is two families:
    a state naming another variation's flag is theirs, and so is a state without one (the default)
    showing a model their states show. flag: the variation (default: the flags of the states
    showing `source`). A Draw without variations, or one not showing `source`: every state."""
    flags = {f for s in draw.states for f in s.flags if f.startswith(VARIATION)}
    if not flags:
        return list(draw.states)
    mine = {flag} if flag else {f for s in draw.states if s.model and s.model.lower() == source.lower()
                                for f in s.flags if f.startswith(VARIATION)}
    others = flags - mine
    if not mine or not others:
        return list(draw.states)
    theirs = {s.model.lower() for s in draw.states if s.model and s.flags & others}
    return [s for s in draw.states if not s.flags & others and not (s.model and s.model.lower() in theirs)]


def parse_draws(text, defines=None):
    """[Draw] in file order, with their states."""
    defines = dict(defines or {})
    draws, obj = [], None
    lines = text.splitlines()
    i = 0

    def value(v):
        return " ".join(defines.get(tok, tok) for tok in v.split())

    while i < len(lines):
        raw = lines[i]
        line = strip(raw)
        i += 1
        m = DEFINE_RE.match(raw.strip())
        if m:
            defines[m.group(1)] = m.group(2).split(";")[0].strip()
            continue
        m = OBJECT_RE.match(line)
        if m and not raw[:1].isspace():
            obj = m.group(2)
            continue
        m = DRAW_RE.match(line)
        if not m:
            continue
        draw = Draw(obj, m.group(1), m.group(2), i)
        depth, state, in_anim, in_script = 1, None, False, False
        while i < len(lines) and depth > 0:
            line = strip(lines[i])
            i += 1
            if not line:
                continue
            low = line.lower()
            if in_script:
                in_script = not low.startswith("endscript")
                continue
            if low.startswith("beginscript"):
                in_script = True
                continue
            key, _, val = (x.strip() for x in line.partition("="))
            k = key.lower()
            if low == "end":
                depth -= 1
                if in_anim:
                    in_anim = False
                elif depth == 1:
                    state = None
                continue
            if depth == 1 and k in STATE_OPENERS:
                kind = "animation" if "animation" in k or k == "transitionstate" else "model"
                state = State(kind, value(val).upper().split(), i)
                draw.states.append(state)
                depth += 1
            elif depth == 2 and k == ANIM_OPENER:
                in_anim = True
                depth += 1
            elif state is not None and k == "model":
                state.model = value(val)
            elif state is not None and k == "texture":
                parts = value(val).split()
                if len(parts) == 2:
                    state.textures.append((parts[0], parts[1]))
            elif state is not None and k == "animationname":
                state.animations.append(value(val))
            elif state is not None and k == "animationmode":
                state.modes.append(value(val).upper())
            elif depth == 1:
                draw.fields[key] = value(val)
                parts = value(line).replace("=", " ").split()      # EA writes it with or without '='
                if len(parts) == 3 and parts[0].lower() == "weathertexture":
                    draw.weather.append((parts[1].upper(), parts[2]))
        draws.append(draw)
    return draws


# ------------------------------------------------------------------------------------ edits
TEXTURE_RE = re.compile(r"^(\s*)Texture(\s*)=(\s*)(\S+)(\s+)(\S+)(.*)$", re.I)


def add_texture_swaps(text, base, swaps):
    """After every `Texture = <base> <variant>` line, add the same swap for a building's own
    textures: swaps {EA variant: (own base, own variant)}. The EA line stays (other meshes still
    use the shared sheet). Idempotent."""
    out, lines = [], text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        out.append(line)
        m = TEXTURE_RE.match(line.rstrip("\r\n"))
        if not m or m.group(4).lower() != base.lower():
            continue
        own = swaps.get(m.group(6)) or next((v for k, v in swaps.items() if k.lower() == m.group(6).lower()), None)
        if not own:
            continue
        new = "%sTexture%s=%s%s%s%s%s" % (m.group(1), m.group(2), m.group(3), own[0], m.group(5), own[1],
                                            line[len(line.rstrip("\r\n")):])
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if nxt.strip().lower() != new.strip().lower():
            out.append(new)
    return "".join(out)


def lod_off(text, obj, tag):
    """StaticModelLODMode = No in one Draw module (so low settings do not swap in EA's <model>L)."""
    return set_field(text, obj, tag, "StaticModelLODMode", "No")


def set_field(text, obj, tag, key, value):
    """`key = value` in one Draw module of one object (the field must exist; EA's value replaced)."""
    lines = text.splitlines(keepends=True)
    cur_obj, in_draw = None, False
    for i, raw in enumerate(lines):
        line = strip(raw)
        m = OBJECT_RE.match(line)
        if m and not raw[:1].isspace():
            cur_obj, in_draw = m.group(2), False
            continue
        m = DRAW_RE.match(line)
        if m:
            in_draw = cur_obj == obj and m.group(2) == tag
            continue
        if in_draw and re.match(r"^%s\s*=" % re.escape(key), line, re.I):
            lines[i] = re.sub(r"(=\s*)\w+", lambda m: m.group(1) + value, raw, count=1)
            in_draw = False
    return "".join(lines)


def add_draw(text, obj, tag, model):
    """A W3DScriptedModelDraw `tag` showing `model` with model colour allowed (the game tints its HC_
    meshes in the player's colour), inserted before object `obj`'s first Draw. Idempotent."""
    lines = text.splitlines(keepends=True)
    cur = None
    for i, raw in enumerate(lines):
        line = strip(raw)
        m = OBJECT_RE.match(line)
        if m and not raw[:1].isspace():
            cur = m.group(2)
            continue
        if cur != obj:
            continue
        m = DRAW_RE.match(line)
        if m and m.group(2) == tag:
            return text
        if m:
            pad = raw[:len(raw) - len(raw.lstrip())]
            nl = "\r\n" if raw.endswith("\r\n") else "\n"
            block = [pad + "Draw = W3DScriptedModelDraw " + tag, pad + "\tOkToChangeModelColor = Yes",
                     pad + "\tDefaultModelConditionState", pad + "\t\tModel = " + model, pad + "\tEnd", pad + "End", ""]
            lines[i:i] = [x + nl for x in block]
            return "".join(lines)
    raise ValueError("no Draw module in object %s" % obj)


def add_state(text, obj, tag, flags, model):
    """A `ModelConditionState = <flags>` showing `model` ("None": nothing) at the end of one Draw
    module of one object, unless the module already has a state with exactly those flags."""
    lines = text.splitlines(keepends=True)
    cur, depth, at, have = None, 0, None, False
    for i, raw in enumerate(lines):
        line = strip(raw)
        m = OBJECT_RE.match(line)
        if m and not raw[:1].isspace():
            cur = m.group(2)
            continue
        m = DRAW_RE.match(line)
        if m and cur == obj and m.group(2) == tag:
            depth, at = 1, i
            continue
        if not depth:
            continue
        low = line.lower()
        key, _, val = (x.strip() for x in line.partition("="))
        if low.startswith("beginscript"):
            depth += 1
        elif low.startswith("endscript"):
            depth -= 1
        elif key.lower() in STATE_OPENERS or key.lower() == ANIM_OPENER and depth == 2:
            depth += 1
            if key.lower() == "modelconditionstate" and set(val.upper().split()) == set(flags):
                have = True
        elif low == "end":
            depth -= 1
            if depth == 0:
                if have:
                    return text
                pad = lines[at][:len(lines[at]) - len(lines[at].lstrip())]
                nl = "\r\n" if raw.endswith("\r\n") else "\n"
                block = [pad + "\tModelConditionState = " + " ".join(flags), pad + "\t\tModel = " + model, pad + "\tEnd"]
                lines[i:i] = [x + nl for x in block]
                return "".join(lines)
    raise ValueError("no Draw module %s in object %s" % (tag, obj))


def set_model(text, obj, tag, old, new):
    """`Model = old` -> `Model = new` in the condition states of one Draw module of one object (a
    model of our own shown in place of a model other factions share; sagekit/owncopy.py). Only
    that module's states: the object's other modules and every other object keep EA's model.
    Comments and spacing stay; idempotent."""
    lines = text.splitlines(keepends=True)
    cur, depth = None, 0
    for i, raw in enumerate(lines):
        line = strip(raw)
        m = OBJECT_RE.match(line)
        if m and not raw[:1].isspace():
            cur, depth = m.group(2), 0
            continue
        m = DRAW_RE.match(line)
        if m:
            depth = 1 if cur == obj and m.group(2) == tag else 0
            continue
        if not depth or not line:
            continue
        low = line.lower()
        key, _, val = (x.strip() for x in line.partition("="))
        if low.startswith("beginscript"):
            depth += 1
        elif low.startswith("endscript"):
            depth -= 1
        elif key.lower() in STATE_OPENERS or key.lower() == ANIM_OPENER and depth == 2:
            depth += 1
        elif low == "end":
            depth -= 1
        elif depth >= 2 and key.lower() == "model" and val.lower() == old.lower():
            lines[i] = re.sub(r"(=\s*)" + re.escape(val), lambda mm: mm.group(1) + new, raw, count=1)
    return "".join(lines)


def add_draw_after(text, obj, after, tag, block):
    """Draw module `tag` - block: its lines from `Draw = ...` to its `End`, unindented - inserted
    after the End of object `obj`'s Draw module `after`, indented like it (sagekit/fire.py).
    Idempotent: an object that has a module `tag` already is left as it is."""
    lines = text.splitlines(keepends=True)
    cur, depth, at = None, 0, None
    for i, raw in enumerate(lines):
        line = strip(raw)
        m = OBJECT_RE.match(line)
        if m and not raw[:1].isspace():
            cur, depth = m.group(2), 0
            continue
        if cur != obj or not line:
            continue
        m = DRAW_RE.match(line)
        if m and not depth:
            if m.group(2) == tag:
                return text
            if m.group(2) == after:
                depth, at = 1, i
            continue
        if not depth:
            continue
        low = line.lower()
        key = line.partition("=")[0].strip().lower()
        if low.startswith("beginscript"):
            depth += 1
        elif low.startswith("endscript"):
            depth -= 1
        elif key in STATE_OPENERS or key == ANIM_OPENER and depth == 2:
            depth += 1
        elif low == "end":
            depth -= 1
            if depth == 0:
                pad = lines[at][:len(lines[at]) - len(lines[at].lstrip())]
                nl = "\r\n" if raw.endswith("\r\n") else "\n"
                rest = "".join(lines[i + 1:])
                if any(DRAW_RE.match(strip(x)) and DRAW_RE.match(strip(x)).group(2) == tag
                       for x in _object_lines(rest)):
                    return text
                lines[i + 1:i + 1] = [nl] + [pad + x + nl for x in block]
                return "".join(lines)
    raise ValueError("no Draw module %s in object %s" % (after, obj))


def add_behavior(text, obj, tag, block):
    """Module `tag` - block: its lines from `Behavior = ...` to its `End`, unindented - inserted
    before the End that closes object `obj` (its last unindented `End`), indented one tab
    (sagekit/capture.py). Idempotent: an object with a module `tag` already is left as it is."""
    lines = text.splitlines(keepends=True)
    start = next((i for i, raw in enumerate(lines) if not raw[:1].isspace() and OBJECT_RE.match(strip(raw))
                  and OBJECT_RE.match(strip(raw)).group(2) == obj), None)
    if start is None:
        raise ValueError("no object %s" % obj)
    stop = next((i for i in range(start + 1, len(lines)) if not lines[i][:1].isspace()
                 and OBJECT_RE.match(strip(lines[i]))), len(lines))
    if any(re.match(r"^Behavior\s*=\s*\S+\s+%s\s*$" % re.escape(tag), strip(x), re.I) for x in lines[start:stop]):
        return text
    end = next((i for i in range(stop - 1, start, -1) if not lines[i][:1].isspace() and strip(lines[i]).lower() == "end"), None)
    if end is None:
        raise ValueError("no End closing object %s" % obj)
    nl = "\r\n" if lines[end].endswith("\r\n") else "\n"
    lines[end:end] = [nl] + ["\t" + x + nl for x in block]
    return "".join(lines)


def _object_lines(text):
    """The lines up to the next top-level Object / ChildObject / ObjectReskin."""
    for raw in text.splitlines():
        if OBJECT_RE.match(strip(raw)) and not raw[:1].isspace():
            return
        yield raw


def apply_ops(text, ops):
    """Apply [('swaps', base, {ea: (own, own variant)}) | ('lod_off', object, tag) |
    ('field', object, tag, key, value) | ('draw', object, tag, model) |
    ('state', object, tag, [flags], model) | ('model', object, tag, old, new) |
    ('fire_draw', object, after tag, tag, lines) | ('fx_systems', ((name, after, lines), ...)) |
    ('behavior', object, tag, lines)] in order."""
    for op in ops:
        if op[0] == "fx_systems":                   # particle systems of our own (sagekit/fire_systems.py)
            from ..fire_systems import add_systems
            text = add_systems(text, op[1])
        elif op[0] == "draw":
            text = add_draw(text, *op[1:])
        elif op[0] == "fire_draw":
            text = add_draw_after(text, *op[1:])
        elif op[0] == "behavior":                   # an object's module of our own (sagekit/capture.py)
            text = add_behavior(text, *op[1:])
        elif op[0] == "model":
            text = set_model(text, *op[1:])
        elif op[0] == "state":
            text = add_state(text, *op[1:])
        elif op[0] == "swaps":
            text = add_texture_swaps(text, op[1], op[2])
        elif op[0] == "lod_off":
            text = lod_off(text, op[1], op[2])
        else:
            text = set_field(text, *op[1:])
    return text
