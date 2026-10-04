"""What the FX archive's members must hold before they ship (`run`): EA's text plus exactly our
blocks; our copies EA's systems but for their colours; every
spell book module EA's but for its FX fields; every name we write defined once and never EA's."""
import re

from .. import fire_systems
from ..formats.ini import strip
from . import blocks, plan
from .tint import same_but_colour

OURS_NOTE = "; sagekit (sagekit/fx):"


class Report:
    def __init__(self):
        self.rows, self.failed = [], 0

    def check(self, what, ok, detail=""):
        self.rows.append(("ok" if ok else "FAIL", what, detail))
        self.failed += not ok

    def info(self, what, detail=""):
        self.rows.append(("info", what, detail))

    def text(self):
        return "\n".join("%-4s  %s%s" % (s, w, ("  [%s]" % d) if d else "") for s, w, d in self.rows)


def without_ours(text, index):
    """text with every block of ours (its note line, the block, the blank line before) taken out."""
    rows = blocks.lines(text)
    cut = set()
    for name, a, z in index.values():
        if a > 0 and rows[a - 1].startswith(OURS_NOTE):
            lo = a - 1
            if lo > 0 and not strip(rows[lo - 1]) and not rows[lo - 1].lstrip().startswith(";"):
                lo -= 1
            cut.update(range(lo, z + 1))
    return "".join(r for i, r in enumerate(rows) if i not in cut)


def ours_in(index, prefix):
    return {k: v for k, v in index.items() if v[0].lower().startswith(prefix.lower())}


def check_systems(r, shipped, base, plans, ea_names):
    text = shipped[plan.PS_MEMBER]
    idx = blocks.systems(text)
    mine = ours_in(idx, "Sagekit")
    fire = {n.lower() for n in fire_systems.OWN}
    tints = {k: v for k, v in mine.items() if k not in fire}
    r.check("fxparticlesystem.ini: EA's with sagekit's fire systems (as the faction packs ship it) plus %d "
            "systems of ours, nothing else changed" % len(tints),
            without_ours(text, tints) == base[plan.PS_MEMBER])
    counts = {}
    for name in tints:
        counts[name] = len(re.findall(fire_systems.HEAD_RE % re.escape(idx[name][0]), text, re.I | re.M))
    r.check("each system of ours defined once", all(c == 1 for c in counts.values()),
            ", ".join(k for k, c in counts.items() if c != 1))
    r.check("no system of ours named like one of EA's", not (set(tints) & ea_names),
            ", ".join(sorted(set(tints) & ea_names)))
    bad = []
    for p in plans:
        for ea, (ours, cls, why) in p.systems.items():
            rows = p.ps_rows(ea)
            refs = {s: p.systems[s][0] for s in blocks.refs(rows) if s in p.systems}
            if not same_but_colour(rows, blocks.body(text, idx[ours.lower()]), refs):
                bad.append(ours)
    r.check("every copy is EA's system but for its colour keys and renamed slaves: lifetimes, sizes, "
            "rates, counts, emission, priority, shader, texture unchanged", not bad, ", ".join(bad))
    missing = [x for p in plans for ea, (ours, _, _) in p.systems.items()
               for ref in blocks.refs(blocks.body(text, idx[ours.lower()])) if ref.lower() not in idx]
    r.check("every slave system a copy names is defined", not missing, ", ".join(missing))


def check_fxlists(r, shipped, base, plans):
    text = shipped[plan.FX_MEMBER]
    idx = blocks.fxlists(text)
    mine = ours_in(idx, "FX_Sagekit")
    r.check("fxlist.ini: EA's plus %d FX lists of ours, nothing else changed" % len(mine),
            without_ours(text, mine) == base[plan.FX_MEMBER])
    ps = blocks.systems(shipped[plan.PS_MEMBER])
    bad, dangling = [], []
    for p in plans:
        back = {v.lower(): k for k, v in list(p.fxlists.items()) + [(k, v[0]) for k, v in p.systems.items()]}
        for ea, ours in p.fxlists.items():
            a = [strip(x) for x in blocks.body(base[plan.FX_MEMBER], p.fx_index[ea.lower()])][1:]
            b = [strip(x) for x in blocks.body(text, idx[ours.lower()])][1:]
            undo = [re.sub(r"=\s*(\S+)", lambda m: "= " + back.get(m.group(1).lower(), m.group(1)), x) for x in b]
            if [re.sub(r"\s*=\s*", "=", x) for x in undo] != [re.sub(r"\s*=\s*", "=", x) for x in a]:
                bad.append(ours)
            for kind, fields, _, _ in blocks.nuggets(blocks.body(text, idx[ours.lower()])):
                n = fields.get("Name") if kind.lower() == "particlesystem" else None
                if n and n.split()[0].lower().startswith("sagekit") and n.split()[0].lower() not in ps:
                    dangling.append("%s -> %s" % (ours, n))
    r.check("every FX list of ours is EA's but for the systems and lists it names", not bad, ", ".join(bad))
    r.check("every system our FX lists name is defined", not dangling, ", ".join(dangling))


def check_modules(r, shipped, base, plans):
    text, old = shipped[plan.BOOK_MEMBER], base[plan.BOOK_MEMBER]
    fx = blocks.fxlists(shipped[plan.FX_MEMBER])
    bad, n = [], 0
    for p in plans:
        for book, parent, tag, moved, power in p.modules:
            n += 1
            ea = blocks.module_fields(old, parent, tag)
            new = _replaced_fields(text, book, tag)
            if new is None:
                bad.append("%s %s: no ReplaceModule" % (book, tag))
                continue
            want = [(k, moved.get(k, v)) for k, v in ea]
            if [(k, re.sub(r"\s+", " ", v)) for k, v in new] != [(k, re.sub(r"\s+", " ", v)) for k, v in want]:
                bad.append("%s %s" % (book, tag))
            bad += ["%s %s: %s undefined" % (book, tag, v) for v in moved.values() if v.lower() not in fx]
    rest = _without_replaces(text)
    r.check("system.ini: EA's plus %d ReplaceModule blocks in the factions' spell books, nothing else changed" % n,
            rest == old)
    r.check("every replaced module is EA's word for word but for its FX fields (gameplay unchanged)", not bad,
            "; ".join(bad))


def _replaced_fields(text, book, tag):
    o = blocks.objects(text)[book.lower()]
    rows = blocks.lines(text)
    for i in range(o[2], o[3]):
        if strip(rows[i]) == "ReplaceModule %s" % tag:
            out = []
            for raw in rows[i + 2:o[3]]:
                s = strip(raw)
                if s.lower() == "end":
                    return out
                if s:
                    k, _, v = (x.strip() for x in s.partition("="))
                    out.append((k, v))
    return None


def _without_replaces(text):
    rows, out, skip = blocks.lines(text), [], 0
    i = 0
    while i < len(rows):
        if rows[i].lstrip().startswith(OURS_NOTE) and i + 1 < len(rows) and strip(rows[i + 1]).startswith("ReplaceModule"):
            if out and not strip(out[-1]) and not out[-1].lstrip().startswith(";"):
                out.pop()
            depth, i = 0, i + 1
            while i < len(rows):
                s = strip(rows[i])
                if s.startswith("ReplaceModule") or blocks.MODULE_HEAD.match(rows[i].split(";")[0]):
                    depth += 1
                elif s.lower() == "end":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            i += 1
            continue
        out.append(rows[i])
        i += 1
    return "".join(out)


def run(shipped, base, plans, g):
    r = Report()
    ea_names = set()
    for m in fire_systems.LOADED:
        ea_names |= set(blocks.systems(g.read(m).decode("latin-1"))) if m == plan.PS_MEMBER else \
            {x.lower() for x in re.findall(r"^ParticleSystem[ \t]+(\S+)", g.read(m).decode("latin-1"), re.M | re.I)}
    check_systems(r, shipped, base, plans, ea_names)
    check_fxlists(r, shipped, base, plans)
    check_modules(r, shipped, base, plans)
    r.check("the archive ships exactly fxparticlesystem.ini, fxlist.ini and system.ini",
            set(shipped) == {plan.PS_MEMBER, plan.FX_MEMBER, plan.BOOK_MEMBER}, ", ".join(sorted(shipped)))
    return r
