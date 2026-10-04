"""Hero powers recombined from EA's own modules: no new module kinds, no new upgrades.

A power is (1) EA's modules copied by tag from an EA hero or include file, under tags of our own
and with a few fields changed, (2) an UnpauseSpecialPowerUpgrade on one of EA's level upgrades
(Upgrade_ObjectLevelN, which every hero's ExperienceLevels grant), and (3) a copy of EA's command
button under our name with our tooltip (and, where the power is renamed, our label).

    Power(slot, level, button, ours, modules, tooltip, label=None, template=None, unpause=True)
"""
import re
from dataclasses import dataclass, field

from . import ea
from .text import code, module_text, retag


@dataclass
class Module:
    source: str                 # "obj:GondorBoromir" or an include member (data\ini\object\...)
    tag: str                    # EA's module tag
    edits: dict = field(default_factory=dict)   # {key: value, or None to drop the line}

    def text(self, new_tag):
        if self.source.startswith("obj:"):
            name = self.source[4:]
            o = ea.objects()[name]
            src = ea.text(o["member"])
            mod = module_text(src, self.tag, o["start"], o["start"] + len(o["body"]) + 200)
        else:
            mod = module_text(ea.text(self.source), self.tag)
        mod = retag(mod, new_tag)
        for key, value in self.edits.items():
            rx = re.compile(r"^([ \t]*%s[ \t]*=[ \t]*)[^\r\n]*(\r?\n)" % re.escape(key), re.M)
            hits = [m for m in rx.finditer(mod) if code(m.group(0))]
            if len(hits) != 1:
                raise SystemExit("heroes: %s %s: %d lines %s" % (self.source, self.tag, len(hits), key))
            m = hits[0]
            rep = "" if value is None else m.group(1) + value + "\t; sagekit heroes" + m.group(2)
            mod = mod[:m.start()] + rep + mod[m.end():]
        return mod


@dataclass
class Power:
    slot: int
    level: int                  # 0: no level gate (passive from the start)
    button: str                 # EA's command button copied
    ours: str                   # our copy's name
    modules: list               # [Module], copied in order
    tooltip: tuple              # (label, text) our DescriptLabel
    label: tuple = None         # (label, text) our TextLabel, None keeps EA's
    template: str = None        # the SpecialPower the button fires (default: the button's)
    unpause: bool = True        # add our UnpauseSpecialPowerUpgrade on Upgrade_ObjectLevel<level>
    ai: str = None              # SpecialPowerAIType for an AISpecialPowerUpdate on our button
    ai_radius: float = None
    template_copy: tuple = None  # (EA template, ours, {key: value or None}): a SpecialPower of our own

    def power(self):
        if self.template_copy:
            return self.template_copy[1]
        if self.template:
            return self.template
        b = ea.all_blocks("CommandButton")[self.button]
        return re.search(r"^\s*SpecialPower\s*=\s*(\S+)", "\n".join(code(l) for l in b.splitlines()), re.M).group(1)


def button_text(p):
    """Our copy of EA's button: its name, labels and (with a template of our own) its power swapped;
    the Create-a-Hero screen's fields dropped."""
    body = ea.all_blocks("CommandButton")[p.button]
    lines = []
    for line in body.splitlines(True):
        c = code(line)
        key = c.split("=")[0].strip().lower() if "=" in c else ""
        if key.startswith("createaheroui"):
            continue
        if key == "descriptlabel":
            line = re.sub(r"=\s*\S+", "= " + p.tooltip[0], line, count=1)
        if key == "textlabel" and p.label:
            line = re.sub(r"=\s*\S+", "= " + p.label[0], line, count=1)
        if key == "specialpower" and p.template_copy:
            line = re.sub(r"=\s*\S+", "= " + p.template_copy[1], line, count=1)
        lines.append(line)
    return "CommandButton %s\t; sagekit heroes: EA's %s\n%sEnd\n" % (p.ours, p.button, "".join(lines))


def template_text(p):
    """A SpecialPower of our own: EA's template copied with fields changed or dropped."""
    src, ours, edits = p.template_copy
    body = ea.all_blocks("SpecialPower")[src]
    for key, value in edits.items():
        rx = re.compile(r"^([ \t]*%s[ \t]*=[ \t]*)[^\r\n]*(\r?\n)" % re.escape(key), re.M)
        hits = [m for m in rx.finditer(body) if code(m.group(0))]
        if len(hits) != 1:
            raise SystemExit("heroes: SpecialPower %s: %d lines %s" % (src, len(hits), key))
        m = hits[0]
        body = body[:m.start()] + ("" if value is None else m.group(1) + value + m.group(2)) + body[m.end():]
    return "SpecialPower %s\t; sagekit heroes: EA's %s\n%sEnd\n" % (ours, src, body)


def modules_text(hero, powers):
    """Every power's modules for `hero`'s object: EA's copies, our level gates and AI hooks."""
    out = []
    for i, p in enumerate(powers):
        stem = "SKH_%s_P%d" % (hero, i + 1)
        if p.unpause and p.level:
            out.append("\tBehavior = UnpauseSpecialPowerUpgrade %s_Level\t; sagekit heroes\n"
                       "\t\tSpecialPowerTemplate\t= %s\n\t\tTriggeredBy\t\t\t= Upgrade_ObjectLevel%d\n\tEnd\n" % (stem, p.power(), p.level))
        for k, m in enumerate(p.modules):
            mod = m.text("%s_M%d" % (stem, k + 1))
            if p.template_copy:
                mod = re.sub(r"\b%s\b" % re.escape(p.template_copy[0]), p.template_copy[1], mod)
            out.append(mod if mod.endswith("\n") else mod + "\n")
        if p.ai:
            out.append("\tBehavior = AISpecialPowerUpdate %s_AI\t; sagekit heroes\n\t\tCommandButtonName = %s\n"
                       "\t\tSpecialPowerAIType = %s\n%s\tEnd\n" % (stem, p.ours, p.ai,
                                                                   "\t\tSpecialPowerRadius = %.1f\n" % p.ai_radius if p.ai_radius else ""))
    return "\n".join(out)


def command_set(name, powers, generic):
    """Our command set: the hero's powers at their slots plus EA's generic hero commands."""
    rows = [(p.slot, p.ours) for p in powers] + list(generic)
    rows.sort()
    if len({s for s, _ in rows}) != len(rows):
        raise SystemExit("heroes: %s uses a slot twice" % name)
    return "CommandSet %s\t; sagekit heroes\n%sEnd\n" % (name, "".join("\t%d\t= %s\n" % r for r in rows))


GENERIC_HERO_COMMANDS = [(1, "Command_ToggleStance"), (12, "Command_CaptureBuilding"), (13, "Command_AttackMove"),
                         (14, "Command_Stop"), (16, "Command_SetStanceBattle"), (17, "Command_SetStanceAggressive"),
                         (18, "Command_SetStanceHoldGround")]


def reload_seconds(p):
    t = p.template_copy[0] if p.template_copy else p.power()
    body = ea.all_blocks("SpecialPower")[t]
    ms = int(re.search(r"ReloadTime\s*=\s*(\d+)", body).group(1))
    if p.template_copy and "ReloadTime" in p.template_copy[2]:
        ms = int(p.template_copy[2]["ReloadTime"])
    return ms / 1000


def recharge(p):
    s = reload_seconds(p)
    return "%dm %02ds" % (s // 60, s % 60) if s >= 60 else "%ds" % s
