"""SAGE INI, as far as art is concerned: which model, textures and animations an object draws in
which state.

A full SAGE INI grammar is per-field (the engine knows which keys open blocks). Art needs only the
Draw modules, whose grammar is small and regular:

    Object <Name>                                   (or ChildObject / ObjectReskin <Name> <Parent>)
      Draw = <DrawType> <Tag>
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

    def __repr__(self):
        return "<%s %s model=%s tex=%s anim=%s>" % (self.kind, " ".join(sorted(self.flags)) or "DEFAULT",
                                                    self.model, self.textures, self.animations)


class Draw:
    def __init__(self, obj, dtype, tag, line):
        self.object, self.type, self.tag, self.line = obj, dtype, tag, line
        self.states = []
        self.fields = {}                    # module-level keys (e.g. StaticModelLODMode)

    def models(self):
        return sorted({s.model for s in self.states if s.model and s.model.lower() != "none"}, key=str.lower)


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
            elif depth == 1:
                draw.fields[key] = value(val)
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
        if in_draw and re.match(r"^StaticModelLODMode\s*=", line, re.I):
            lines[i] = re.sub(r"(=\s*)\w+", r"\1No", raw, count=1)
            in_draw = False
    return "".join(lines)


def apply_ops(text, ops):
    """Apply [('swaps', base, {ea: (own, own variant)}) | ('lod_off', object, tag)] in order."""
    for op in ops:
        text = add_texture_swaps(text, op[1], op[2]) if op[0] == "swaps" else lod_off(text, op[1], op[2])
    return text
