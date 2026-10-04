"""Experience levels (experiencelevels.ini): a hero's powers wait for EA's level upgrades
(Upgrade_ObjectLevelN), which only the hero's own ExperienceLevel blocks grant. New heroes get
copies of a donor's ten blocks; a hero whose blocks grant too little gets Upgrades lines added.
"""
import re

from . import ea

MEMBER = ea.I + "experiencelevels.ini"


def hero_levels(hero, src=None):
    """[(name, start, end, body)] of the ExperienceLevel blocks targeting `hero`, by rank."""
    src = src if src is not None else ea.text(MEMBER)
    out = []
    for m in re.finditer(r"^ExperienceLevel[ \t]+(\S+)[^\n]*\n(.*?)^END\b[^\n]*\n", src, re.M | re.S | re.I):
        t = re.search(r"^[ \t]*TargetNames[ \t]*=[ \t]*([^;\r\n]*)", m.group(2), re.M)
        if t and hero.lower() in [x.lower() for x in t.group(1).split()]:
            rank = int(re.search(r"^[ \t]*Rank[ \t]*=[ \t]*(\d+)", m.group(2), re.M).group(1))
            out.append((rank, m.group(1), m.start(), m.end(), m.group(0)))
    out.sort()
    if [r for r, *_ in out] != list(range(1, 11)):
        raise SystemExit("heroes: %s has levels %s, not 1..10" % (hero, [r for r, *_ in out]))
    return [(n, s, e, b) for _, n, s, e, b in out]


def _grant(block, rank):
    """The block granting Upgrade_ObjectLevel<rank> (its own Upgrades line set, else one added)."""
    up = "Upgrade_ObjectLevel%d" % rank
    line = "\tUpgrades\t\t\t\t\t=\t%s\t; sagekit heroes" % up
    have = re.search(r"^[ \t]*Upgrades[ \t]*=[ \t]*([^;\r\n]*)[^\r\n]*", block, re.M)
    if have:
        if up in have.group(1).split():
            return block
        return block[:have.start()] + "\tUpgrades\t\t\t\t\t=\t%s %s\t; sagekit heroes" % (have.group(1).strip(), up) + block[have.end():]
    return re.sub(r"(^[ \t]*Rank[ \t]*=[^\r\n]*\r?\n)", lambda m: m.group(1) + line + ("\r\n" if "\r\n" in block else "\n"),
                  block, count=1, flags=re.M)


def copy_levels(donor, hero, grant_all=False):
    """Ten ExperienceLevel blocks for `hero`: the donor's, renamed and targeting only `hero`."""
    out = []
    for rank, (name, _, _, body) in enumerate(hero_levels(donor), 1):
        b = re.sub(r"^ExperienceLevel[ \t]+\S+", "ExperienceLevel %sLevel%d\t; sagekit heroes: EA's %s" % (hero, rank, name),
                   body, count=1, flags=re.M)
        b = re.sub(r"^([ \t]*TargetNames[ \t]*=[ \t]*)[^;\r\n]*", r"\g<1>%s " % hero, b, count=1, flags=re.M)
        if grant_all:
            b = _grant(b, rank)
        out.append(b)
    return "".join(out)


def add_grants(src, hero, ranks):
    """`src` with `hero`'s blocks at `ranks` granting their level upgrade (EA's blocks edited in place)."""
    for name, s, e, body in reversed(hero_levels(hero, src)):
        rank = int(re.search(r"^[ \t]*Rank[ \t]*=[ \t]*(\d+)", body, re.M).group(1))
        if rank in ranks and not re.search(r"^[ \t]*Upgrades[ \t]*=[ \t]*Upgrade_ObjectLevel%d\b" % rank, body, re.M):
            src = src[:s] + _grant(body, rank) + src[e:]
    return src


def granted(src, hero):
    """{rank: [upgrades]} the hero's levels grant."""
    out = {}
    for name, s, e, body in hero_levels(hero, src):
        rank = int(re.search(r"^[ \t]*Rank[ \t]*=[ \t]*(\d+)", body, re.M).group(1))
        up = re.search(r"^[ \t]*Upgrades[ \t]*=[ \t]*([^;\r\n]*)", body, re.M)
        out[rank] = up.group(1).split() if up else []
    return out
