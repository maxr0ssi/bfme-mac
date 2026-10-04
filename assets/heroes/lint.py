"""The heroes pack's lint: the composed INI checked against itself and EA's, and broken copies that
must fail (a roster grown without a slot, a missing label, a power whose level is never granted).

  roster      every rostered hero exists; a revive slot per hero in every hero building; submenus
              cover their slots and nothing else; at most 33 slots a set (roster.lint)
  objects     every new or edited hero: its command set and each button exist, each button's power
              is defined and carried by the hero, its labels are in our string table, its images are
              mapped; module tags unique; its Draw models EA's or ours; its voice events EA's
  levels      each power's level gate (Upgrade_ObjectLevelN) is granted by the hero's levels
  upgrades    no Upgrade defined beyond EA's (the 1152 limit: sagekit/upgrades.py)
"""
import re

from sagekit import upgrades as U
from sagekit.formats.ini import parse_draws

from . import ea, levels, roster
from .compose import FILES, NEW_FILES

MEMBERS = dict(FILES, **NEW_FILES)
from .text import blocks, code

HEROES = {"DwarvenEreborCaptain": "captain", "RohanGamling": "gamling", "GondorEarnur": "earnur", "GondorDamrod": None}


def object_texts(f):
    """{object: (body, file key)} of the objects our composed files define, EA's for the rest."""
    out = {}
    for key in ("gamling", "earnur", "aragorn", "captain"):
        t = f[key]
        hs = list(re.finditer(r"^(Object|ChildObject)[ \t]+(\S+)", t, re.M))
        for k, h in enumerate(hs):
            out[h.group(2)] = (t[h.end(): hs[k + 1].start() if k + 1 < len(hs) else len(t)], key)
    return out


def expand(body, member):
    """`body` with its #include lines replaced by the files they name (relative to `member`)."""
    import posixpath

    def inc(m):
        rel = m.group(1).replace("\\", "/")
        path = posixpath.normpath(posixpath.join(posixpath.dirname(member.replace("\\", "/")), rel)).replace("/", "\\").lower()
        try:
            return "\n".join(code(l) for l in ea.text(path).splitlines())
        except FileNotFoundError:
            return ""
    return re.sub(r'^[ \t]*#include[ \t]+"([^"]+)"[^\n]*', inc, body, flags=re.M | re.I)


def fields(body, key):
    return [m.group(1).strip() for m in re.finditer(r"^[ \t]*%s[ \t]*=[ \t]*([^;\r\n]*)" % key, body, re.M)]


def check(ea_files, f, labels, images, models, objects):
    """Problems (empty: clean). labels: our string table's labels; images: mapped image names
    (lower) incl. ours; models: model names we ship (lower); objects: every object name."""
    errs = list(roster.lint(ea_files, f, objects))
    ours = object_texts(f)
    sets = blocks(f["commandset"], "CommandSet")
    buttons = blocks(f["commandbutton"], "CommandButton")
    powers = set(ea.all_blocks("SpecialPower")) | set(blocks(f["specialpower"], "SpecialPower"))
    g = ea.install()
    for hero in HEROES:
        if hero not in ours and hero not in ea.objects():
            errs.append("%s: no object" % hero)
            continue
        body = ours[hero][0] if hero in ours else ea.objects()[hero]["body"]
        member = MEMBERS[ours[hero][1]] if hero in ours else ea.objects()[hero]["member"]
        body = "\n".join(code(l) if not l.lstrip().startswith("#") else l.split(";")[0] for l in body.splitlines())
        body = expand(body, member)
        if hero in ours:
            tags = re.findall(r"^[ \t]*(?:Behavior|Body|ClientBehavior|Draw)[ \t]*=[ \t]*\w+[ \t]+(\w+)", body, re.M)
            dup = {t for t in tags if tags.count(t) > 1}
            if dup:
                errs.append("%s: module tags used twice: %s" % (hero, sorted(dup)))
        for k in ("DisplayName", "RecruitText", "ReviveText", "Hotkey"):
            for v in fields(body, k):
                if v.split()[0].lower() not in labels:
                    errs.append("%s: %s %s is no label" % (hero, k, v))
        for k in ("SelectPortrait", "ButtonImage"):
            for v in fields(body, k):
                if v.split()[0].lower() not in images:
                    errs.append("%s: %s %s is no mapped image" % (hero, k, v))
        for v in [x for k, x in re.findall(r"^[ \t]*(Voice(?!Priority)\w+|Sound)[ \t]*=[ \t]*([^;\r\n]*)", body, re.M)]:
            ev = v.split()[-1]
            if ev.lower() not in ea.audio_events():
                errs.append("%s: sound %s undefined" % (hero, ev))
        for d in parse_draws("Object %s\n%s" % (hero, body), ea.defines()):
            for m in d.models():
                if m.lower() not in models and not g.has_model(m):
                    errs.append("%s: draws %s, which nobody ships" % (hero, m))
        cs = fields(body, "CommandSet")
        if not cs or cs[0].split()[0] not in sets:
            errs.append("%s: command set %s undefined" % (hero, cs))
            continue
        carried = {v.split()[0].lower() for v in fields(body, "SpecialPowerTemplate") + fields(body, "SpecialAbility")}
        gates = {v.split()[0]: None for v in fields(body, "SpecialPowerTemplate")}
        for slot, name in roster.slots(sets[cs[0].split()[0]][2]).items():
            b = buttons.get(name)
            if b is None:
                errs.append("%s: button %s undefined" % (hero, name))
                continue
            bt = "\n".join(code(l) for l in b[2].splitlines())
            p = re.search(r"^\s*SpecialPower\s*=\s*(\S+)", bt, re.M)
            if p and p.group(1) not in powers:
                errs.append("%s: %s fires undefined %s" % (hero, name, p.group(1)))
            if p and p.group(1).lower() not in carried:
                errs.append("%s: %s fires %s, which %s does not carry" % (hero, name, p.group(1), hero))
            for k in ("TextLabel", "DescriptLabel"):
                lab = re.search(r"^\s*%s\s*=\s*(\S+)" % k, bt, re.M)
                if lab and lab.group(1).lower() not in labels:
                    errs.append("%s: %s's %s %s is no label" % (hero, name, k, lab.group(1)))
            img = re.search(r"^\s*ButtonImage\s*=\s*(\S+)", bt, re.M)
            if img and img.group(1).lower() not in images:
                errs.append("%s: %s's image %s is not mapped" % (hero, name, img.group(1)))
        # every level upgrade a module waits for is granted by the hero's levels
        waits = {int(n) for n in re.findall(r"TriggeredBy[ \t]*=[^;\r\n]*\bUpgrade_ObjectLevel(\d+)", body)}
        try:
            got = {int(u[len("Upgrade_ObjectLevel"):]) for ups in levels.granted(f["levels"], hero).values() for u in ups
                   if u.startswith("Upgrade_ObjectLevel")}
        except SystemExit as e:
            errs.append("%s: %s" % (hero, e))
            continue
        if waits - got:
            errs.append("%s: waits for levels %s, which its levels never grant" % (hero, sorted(waits - got)))
    ea_names = set().union(*(U.names(t) for t in ea_files.values()))
    for k, t in f.items():
        extra = U.names(t) - ea_names
        if extra and k in ea_files:
            errs.append("%s defines Upgrades %s" % (k, sorted(extra)))
        elif extra:
            errs.append("%s defines Upgrades %s" % (k, sorted(extra)))
    return errs


def broken_copies(ea_files, f, labels, images, models, objects):
    """Copies that must each fail the lint: [(what, problems)]."""
    out = []
    b = dict(ea_files)
    b["playertemplate"] = roster.append_roster(b["playertemplate"], "Men", "RohanGamling")
    out.append(("roster grown without a slot", roster.lint(ea_files, b, objects)))
    out.append(("a label missing", check(ea_files, f, labels - {"object:sageKitereborcaptain".lower()}, images, models, objects)))
    c = dict(f)
    c["levels"] = c["levels"].replace("Upgrade_ObjectLevel3\t; sagekit heroes", "Upgrade_ObjectLevel2\t; sagekit heroes", 1)
    out.append(("a level never granted", check(ea_files, c, labels, images, models, objects)))
    c = dict(f)
    c["captain"] = c["captain"].replace("CommandSet  = SagekitEreborCaptainCommandSet", "CommandSet  = NoSuchCommandSet", 1)
    out.append(("a command set missing", check(ea_files, c, labels, images, models, objects)))
    return out
