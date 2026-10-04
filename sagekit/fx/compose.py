"""Every faction's FX recipe composed onto the game's INIs: the members of the shared FX archive.

The base of each member is EA's file as the game reads it without the FX archive (`base_texts`);
fxparticlesystem.ini's base is EA's file with sagekit's fire systems added (sagekit/fire_systems.py),
so the one copy in the game defines every system the faction packs' fire Draws burn. Our blocks then
go in:

    fxparticlesystem.ini    each system of ours right after the EA system it copies
    fxlist.ini              each FX list of ours right after the EA list it copies
    object\\system\\system.ini   each faction's spell book (a ChildObject of EA's shared book) gains a
                            ReplaceModule per power: EA's module, word for word, but for its FX fields

Those three, and only those, are the FX archive's: no faction pack ships them (the packs leave
fxparticlesystem.ini to it). The faction's structure INIs are its own pack's: `structure_ops` gives
sagekit/install.py the op that moves `ParticleSysBone <bone> <EA system>` to our system in EA's Draw
modules only (sagekit's own fire Draws, SagekitFire_*, keep theirs).
"""
import re

from .. import fire_systems
from ..formats.ini import apply_ops, strip
from . import blocks, plan
from .textures import TextureTints
from .tint import tinted

BONE = re.compile(r"^([ \t]*ParticleSysBone[ \t]*=?[ \t]*\S+[ \t]+)(\S+)(.*)$", re.I | re.S)
OUR_FIRE_DRAW = "SagekitFire_"


def ps_base(g):
    """EA's fxparticlesystem.ini with sagekit's fire systems, as the faction packs ship it."""
    return apply_ops(g.read(plan.PS_MEMBER).decode("latin-1"), [fire_systems.ops(g)])


def base_texts(g, active, members):
    """{member: text}: fxparticlesystem.ini from ps_base, the rest as `active` (the game without the
    FX archive) reads them."""
    out = {plan.PS_MEMBER: ps_base(g)}
    for m in members:
        if m != plan.PS_MEMBER:
            out[m] = active.read(m).decode("latin-1")
    return out


def add_systems(text, p, tints):
    nl = "\r\n" if "\r\n" in text else "\n"
    items = []
    for ea, (ours, cls, why) in sorted(p.systems.items()):
        rows = p.ps_rows(ea)
        refs = {s: p.systems[s][0] for s in blocks.refs(rows) if s in p.systems}
        tex = tints(((blocks.field(rows, "System", "ParticleName") or "").split() or [None])[0])
        out = tinted(rows, ours, p.r.ramps[cls], refs, "EA's %s in the %s %s colours (%s)" % (ea, p.r.tag, cls, why), tex)
        items.append((ours, ea, tuple(x.rstrip("\r\n") for x in out)))
    return fire_systems.add_systems(text if text.endswith(nl) else text + nl, items)


def add_fxlists(text, p):
    nl = "\r\n" if "\r\n" in text else "\n"
    for ea in sorted(p.fxlists):
        ours = p.fxlists[ea]
        if blocks.fxlists(text).get(ours.lower()):
            continue
        z = blocks.fxlists(text)[ea.lower()][2]
        rows = blocks.lines(text)
        rows[z + 1:z + 1] = [nl] + [x.rstrip("\r\n") + nl for x in p.fx_rows(ea)]
        text = "".join(rows)
    return text


def replace_block(text, parent, tag, moved, r):
    """The ReplaceModule block (rows, no line endings) for EA's module `tag` of `parent`."""
    a, z = blocks.module(text, parent, tag)
    rows = blocks.lines(text)[a:z + 1]
    head = blocks.MODULE_HEAD.match(rows[0].split(";")[0])
    out = ["; sagekit (sagekit/fx): %s's %s with the %s FX (%s); every other field EA's" %
           (parent, tag, r.tag, ", ".join("%s %s" % kv for kv in sorted(moved.items()))),
           "ReplaceModule %s" % tag,
           "\t%s = %s %s" % (head.group(1), head.group(2), r.our_tag(tag))]
    for raw in rows[1:-1]:
        s = strip(raw)
        key = s.partition("=")[0].strip()
        if s and key in moved:
            raw = blocks.set_value(blocks.drop_comment(raw), moved[key])
        body = raw.rstrip("\r\n").strip()
        out.append("\t\t" + body if body else "")
    return out + ["\tEnd", "End"]


def add_modules(text, p):
    nl = "\r\n" if "\r\n" in text else "\n"
    by_book = {}
    for book, parent, tag, moved, power in p.modules:
        by_book.setdefault(book, []).append(replace_block(text, parent, tag, moved, p.r))
    for book, blocks_ in by_book.items():
        _, _, _, z = blocks.objects(text)[book.lower()]
        rows = blocks.lines(text)
        add = []
        for b in blocks_:
            add += [nl] + ["\t" + x + nl if x else nl for x in b]
        rows[z:z] = add
        text = "".join(rows)
    return text


def repoint_bones(text, moves):
    """text with every ParticleSysBone of EA's Draw modules naming a key of `moves` {EA: ours}
    (case-insensitive) naming ours; (text, count)."""
    low = {k.lower(): v for k, v in moves.items()}
    rows, draw, n = blocks.lines(text), None, 0
    for i, raw in enumerate(rows):
        if not raw[:1].isspace() and blocks.OBJ_HEAD.match(strip(raw) or "-"):
            draw = None
        m = blocks.MODULE_HEAD.match(raw.split(";")[0])
        if m:
            draw = m.group(3) if m.group(1).lower() == "draw" else None
        b = BONE.match(raw)
        if b and draw and not draw.startswith(OUR_FIRE_DRAW) and b.group(2).lower() in low:
            rows[i] = b.group(1) + low[b.group(2).lower()] + b.group(3)
            n += 1
    return "".join(rows), n


def compose(g, active, recipes):
    """({member: text} the FX archive ships, {member: base text}, [Plan]): the three shared files.
    `active` is the game without the FX archive (install.Without); the faction structure INIs are
    the faction packs' (`structure_ops`)."""
    members = (plan.PS_MEMBER, plan.FX_MEMBER, plan.BOOK_MEMBER)
    base = base_texts(g, active, members)
    texts = dict(base)
    plans = []
    tints = TextureTints(g)
    for f, r in sorted(recipes.items()):
        p = plan.Plan(r, base, tints)
        plans.append(p)
        texts[plan.PS_MEMBER] = add_systems(texts[plan.PS_MEMBER], p, tints)
        texts[plan.FX_MEMBER] = add_fxlists(texts[plan.FX_MEMBER], p)
        texts[plan.BOOK_MEMBER] = add_modules(texts[plan.BOOK_MEMBER], p)
    tints.save()
    return texts, base, plans


def faction_moves(faction, g):
    """{EA system: ours} the faction's structures burn instead (its fx.py; {} without one): the plan
    resolved against EA's shared files, as the FX archive composes them."""
    r = plan.recipes().get(faction)
    if r is None or not r.structures:
        return {}
    texts = {plan.PS_MEMBER: ps_base(g), plan.FX_MEMBER: g.read(plan.FX_MEMBER).decode("latin-1"),
             plan.BOOK_MEMBER: g.read(plan.BOOK_MEMBER).decode("latin-1")}
    tints = TextureTints(g)
    moves = plan.Plan(r, texts, tints).building_systems()
    tints.save()
    return moves


def structure_ops(faction, style, g):
    """{structure INI: [("fx_bones", ((EA, ours), ...))]} for the faction pack (sagekit/install.py
    collect): its EA Draws' building fire and smoke moved to our systems (formats/ini.py apply_ops)."""
    moves = faction_moves(faction, g)
    out = {}
    if not moves:
        return out
    op = ("fx_bones", tuple(sorted(moves.items())))
    for d in style.ini_dirs():
        members = [d.lower()] if d.lower().endswith(".ini") else [m for m in g.members(d) if m.endswith(".ini")]
        for m in members:
            if repoint_bones(g.read(m).decode("latin-1"), moves)[1]:
                out[m] = [op]
    return out


def localised_bones(files, faction, style, g):
    """files with the fire of the Draw modules sagekit/inherit.py wrote into the faction's own
    objects (a parent's, from a file other factions inherit too) moved like the rest."""
    moves = faction_moves(faction, g)
    if not moves:
        return files
    dirs = [d.lower() for d in style.ini_dirs()]
    out = dict(files)
    for m, data in files.items():
        if m.lower().endswith(".ini") and any(m.lower().startswith(d) or m.lower() == d for d in dirs):
            text, n = repoint_bones(data.decode("latin-1"), moves)
            if n:
                out[m] = text.encode("latin-1")
    return out
