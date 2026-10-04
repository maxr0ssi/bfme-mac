"""Who each faction can recruit: playertemplate.ini's BuildableHeroesMP, the fortress command sets'
revive slots and their hero submenus, and the skirmish AI's build order.

A faction's fortress (and monument fortress, custom keep, Throne of Erebor) lists one
Command_GenericReviveSlotN per named hero; the game fills them from the roster. A roster that
grows needs a slot per hero in every such set, and the set's hero submenu button
(PUSH_VISIBLE_COMMAND_RANGE) must count the new slots. A set holds at most 33 slots (the engine's
CommandSet field table names "1".."33"; exe 0xc4f5e8).
"""
import re

from .text import blocks, code

MAX_SLOTS = 33
FACTION_SETS = {"Men": ("Men", "Gondor", "Rohan", "HelmsDeep", "CommandSetCustomCastleBaseKeepMen"),
                "Dwarves": ("Dwarven", "ThroneofErebor", "CommandSetCustomCastleBaseKeepDwarven")}


def rosters(pt):
    out = {}
    for name, (_, _, body) in blocks(pt, "PlayerTemplate").items():
        for line in body.splitlines():
            m = re.match(r"\s*BuildableHeroesMP\s*=\s*(.*)", code(line))
            if m:
                out[name.replace("Faction", "", 1)] = m.group(1).split()
    return out


def slots(body):
    return {int(m.group(1)): m.group(2) for m in
            re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", "\n".join(code(l) for l in body.splitlines()), re.M)}


def submenu(cb, name):
    """(start, count) of a PUSH_VISIBLE_COMMAND_RANGE button, else None."""
    b = blocks(cb, "CommandButton").get(name)
    if not b or "PUSH_VISIBLE_COMMAND_RANGE" not in b[2]:
        return None
    body = "\n".join(code(l) for l in b[2].splitlines())
    return (int(re.search(r"CommandRangeStart\s*=\s*(\d+)", body).group(1)),
            int(re.search(r"CommandRangeCount\s*=\s*(\d+)", body).group(1)))


def hero_sets(cs, faction):
    """The faction's command sets that revive heroes (they carry the Create-a-Hero slot)."""
    return [n for n, (_, _, b) in blocks(cs, "CommandSet").items()
            if n.startswith(FACTION_SETS[faction]) and "Command_CreateAHeroReviveSlot" in slots(b).values()]


def _set_count(cb, name, key, value):
    s, e, body = blocks(cb, "CommandButton")[name]
    new = re.sub(r"(%s\s*=\s*)\d+" % key, lambda m: m.group(1) + str(value), body, count=1)
    return cb[:s] + cb[s:e].replace(body, new, 1) + cb[e:]


def add_revive_slot(cs, cb, setname, slot_no, bumped=None):
    """Command_GenericReviveSlot<slot_no> after the set's last generic slot; later slot numbers move
    up one; submenus starting past it start one later; the hero submenu counts one more. A submenu
    button two sets share (a fortress and its rebuilt state) moves once per slot (`bumped`)."""
    bumped = set() if bumped is None else bumped
    s, e, body = blocks(cs, "CommandSet")[setname]
    sl = slots(body)
    last = max(k for k, v in sl.items() if v.startswith("Command_GenericReviveSlot"))
    out = []
    for line in body.splitlines(True):
        m = re.match(r"(\s*)(\d+)(\s*=.*)", line, re.S)
        live = m and code(line)
        if live and int(m.group(2)) > last:
            line = "%s%d%s" % (m.group(1), int(m.group(2)) + 1, m.group(3))
        out.append(line)
        if live and int(m.group(2)) == last:
            nl = "\r\n" if line.endswith("\r\n") else "\n"
            out.append("\t%d\t= Command_GenericReviveSlot%d\t\t; sagekit heroes pack%s" % (last + 1, slot_no, nl))
    cs = cs[:s] + cs[s:e].replace(body, "".join(out), 1) + cs[e:]
    hero_menu, menus = None, 0
    for v in set(sl.values()):
        r = submenu(cb, v)
        if not r:
            continue
        menus += 1
        if r[0] >= last:                                  # 0-based start at or past the new slot
            if (v, "start", slot_no) not in bumped:
                cb = _set_count(cb, v, "CommandRangeStart", r[0] + 1)
                bumped.add((v, "start", slot_no))
        elif r[0] < last <= r[0] + r[1]:                  # the menu that shows the hero slots
            hero_menu = v
    if hero_menu is None:
        if menus:
            raise SystemExit("heroes: %s has submenus but none over its hero slots" % setname)
        return cs, cb, None                             # the slots stand on the set's own page
    if (hero_menu, "count", slot_no) not in bumped:
        cb = _set_count(cb, hero_menu, "CommandRangeCount", submenu(cb, hero_menu)[1] + 1)
        bumped.add((hero_menu, "count", slot_no))
    return cs, cb, hero_menu


def ensure_slots(cs, cb, pt, faction):
    """Every hero set of the faction gets a generic revive slot per named hero on its roster."""
    need = len([h for h in rosters(pt)[faction] if h != "CreateAHero"])
    done, bumped = [], set()
    for name in hero_sets(cs, faction):
        have = len([v for v in slots(blocks(cs, "CommandSet")[name][2]).values() if v.startswith("Command_GenericReviveSlot")])
        for k in range(have + 1, need + 1):
            cs, cb, menu = add_revive_slot(cs, cb, name, k, bumped)
            done.append((name, "Command_GenericReviveSlot%d" % k, menu))
    return cs, cb, done


def append_roster(pt, faction, hero):
    s, e, body = blocks(pt, "PlayerTemplate")["Faction" + faction]
    new = re.sub(r"^([ \t]*BuildableHeroesMP[ \t]*=[ \t]*)([^;\r\n]*?)([ \t]*(;[^\r\n]*)?)(\r?)$",
                 lambda m: m.group(1) + m.group(2).rstrip() + " " + hero + m.group(3) + m.group(5), body, count=1, flags=re.M)
    if new == body:
        raise SystemExit("heroes: Faction%s has no BuildableHeroesMP line" % faction)
    return pt[:s] + pt[s:e].replace(body, new, 1) + pt[e:]


def append_ai(ai, after, hero, phase3):
    """`hero` after `after` in the live HeroBuildOrder naming it, and an ArmyMemberDefinition after
    `after`'s (the AI recruits him in the late game like its other heroes)."""
    new, n = re.subn(r"^([ \t]*HeroBuildOrder[ \t]*=[^;\r\n]*\b%s\b)" % after, r"\g<1> %s" % hero, ai, count=1, flags=re.M)
    if n != 1:
        raise SystemExit("heroes: no live HeroBuildOrder names %s" % after)
    anchor = re.search(r"^[ \t]*ArmyMemberDefinition[ \t]+%s\b.*?^[ \t]*End[ \t]*\r?$" % after, new, re.M | re.S)
    nl = "\r\n" if "\r\n" in ai else "\n"
    block = (nl + nl + "\tArmyMemberDefinition %s\t; sagekit heroes pack" % hero + nl + "\t\tUnit\t\t\t= %s" % hero + nl +
             "\t\tPercentageOfArmyPhase1\t= 0.0" + nl + "\t\tPercentageOfArmyPhase2\t= 0.0" + nl +
             "\t\tPercentageOfArmyPhase3\t= %.1f" % phase3 + nl + "\tEnd")
    return new[:anchor.end()] + block + new[anchor.end():]


def lint(ea_files, files, objects):
    """Problems in the composed roster data (EA's own quirks, present in EA's files too, are not)."""
    def problems(f):
        out = set()
        pt, cs, cb, ai = f["playertemplate"], f["commandset"], f["commandbutton"], f["skirmishai"]
        sets, buttons = blocks(cs, "CommandSet"), blocks(cb, "CommandButton")
        for fac, heroes in rosters(pt).items():
            for h in heroes:
                if h not in objects:
                    out.add("%s: roster names %s, no such object" % (fac, h))
            if fac in FACTION_SETS:
                need = len([h for h in heroes if h != "CreateAHero"])
                for name in hero_sets(cs, fac):
                    gen = [v for v in slots(sets[name][2]).values() if v.startswith("Command_GenericReviveSlot")]
                    if len(gen) < need:
                        out.add("%s: %s has %d hero slots for %d heroes" % (fac, name, len(gen), need))
                    if len(set(gen)) != len(gen):
                        out.add("%s: %s repeats a generic revive slot" % (fac, name))
        for name, (_, _, body) in sets.items():
            sl = slots(body)
            if sl and max(sl) > MAX_SLOTS:
                out.add("%s: slot %d past the engine's %d" % (name, max(sl), MAX_SLOTS))
            ranges = []
            for v in set(sl.values()):
                if v not in buttons and v not in ("Command_RadialBack",):
                    out.add("%s uses undefined %s" % (name, v))
                r = submenu(cb, v)
                if r:
                    ranges.append((r[0] + 1, r[0] + r[1], v))
                    gaps = [k for k in range(r[0] + 1, r[0] + r[1] + 1) if k not in sl]
                    if gaps:
                        out.add("%s: submenu %s covers empty slots %s" % (name, v, gaps))
            ranges.sort()
            for (a0, a1, va), (b0, b1, vb) in zip(ranges, ranges[1:]):
                if b0 <= a1:
                    out.add("%s: submenus %s and %s overlap" % (name, va, vb))
            gen = [k for k, v in sl.items() if v.startswith("Command_GenericReviveSlot")]
            if gen and ranges and not any(a0 <= min(gen) and max(gen) <= a1 for a0, a1, _ in ranges):
                out.add("%s: no submenu shows all its hero slots %s" % (name, gen))
        for m in re.finditer(r"^[ \t]*HeroBuildOrder[ \t]*=[ \t]*([^;\r\n]*)", ai, re.M):
            for h in m.group(1).split():
                if h not in objects:
                    out.add("AI HeroBuildOrder names %s, no such object" % h)
        return out
    return sorted(problems(files) - problems(ea_files))
