"""Draw modules a faction's objects inherit from a parent in a file other factions' objects inherit
from too, written into the faction's own objects, so no two packs ship that file.

EA's three evil lumber mills (WildLumberMill, IsengardLumberMill, MordorLumberMill) are ChildObjects
of the civilian LumberMill and draw its Draw modules (Install.object_draws); so do IsengardFurnace
(Furnace) and MordorSlaughterHouse (SlaughterHouse), all in civilianbuildings.ini. Each faction's
edits of those modules (its own copy of the model, its house copy, its fire Draw) went to the
parent, so the Goblin, Isengard and Mordor packs each shipped civilianbuildings.ini and the game read
the first in sort order, the Goblins': every evil mill drew the Goblin mill, and Isengard's furnace
and Mordor's slaughter house drew EA's. The copies cannot be merged: one Draw shows one model.

`localise` (sagekit/install.py collect) takes such a file out of the pack and writes every Draw module
of each edited parent, this faction's edits applied, into each of the faction's children under the
parent's tags; the parent stays EA's. EA's own ChildObjects redefine their parent's Draw modules
under the parent's tags (CastleFlagNW < CastleFlag, ModuleTag_01; 1184 children redefine every one
their parent has). Every Draw module is written, not only the edited ones, so the child draws the
same whether the engine replaces the module of that tag or every inherited Draw module. A file only
this faction's objects inherit from (the Men's FarmInterface) keeps its edits. `clashes` is the
lint: install refuses to stage a pack whose INI another faction pack in the game folder ships otherwise.
"""
import re

from .formats.ini import ANIM_OPENER, DRAW_RE, OBJECT_RE, STATE_OPENERS, parse_objects, strip

PACK = "!!!!!!!!!!!sagekit-"                    # a faction pack (sagekit/install.py archive_name)
OBSOLETE = "data\\ini\\object\\obsolete\\"   # EA's retired objects (RohanFarm < FarmInterface): nobody's
NOTE = "; sagekit (sagekit/inherit.py): %s's Draw modules, the %s redesign's edits applied"


def draw_spans(text, obj):
    """[(tag, first row, End row)] of object `obj`'s Draw modules, rows of text.splitlines(True)."""
    rows, cur, out, depth, at, tag = text.splitlines(keepends=True), None, [], 0, None, None
    for i, raw in enumerate(rows):
        line = strip(raw)
        if not line:
            continue
        m = OBJECT_RE.match(line)
        if m and not raw[:1].isspace():
            if depth:
                raise ValueError("Draw module %s of %s has no End" % (tag, cur))
            cur = m.group(2)
            continue
        if cur != obj:
            continue
        if not depth:
            m = DRAW_RE.match(line)
            if m:
                depth, at, tag = 1, i, m.group(2)
            continue
        low, key = line.lower(), line.partition("=")[0].strip().lower()
        if low.startswith("beginscript"):
            depth += 1
        elif low.startswith("endscript"):
            depth -= 1
        elif key in STATE_OPENERS or key == ANIM_OPENER and depth == 2:
            depth += 1
        elif low == "end":
            depth -= 1
            if not depth:
                out.append((tag, at, i))
    return out


def without_draws(text, objs):
    """text's rows with the Draw modules of `objs` left out (what an edit of them may not touch)."""
    rows, drop = text.splitlines(keepends=True), set()
    for obj in objs:
        for _, a, z in draw_spans(text, obj):
            drop.update(range(a, z + 1))
    return [r for i, r in enumerate(rows) if i not in drop and strip(r)]


def give(text, child, parent, blocks, faction):
    """text with `blocks` [(tag, rows)] written right after object `child`'s header, but for the tags
    the child defines itself (its own module already wins over the parent's)."""
    own = {t for t, _, _ in draw_spans(text, child)}
    rows = text.splitlines(keepends=True)
    for i, raw in enumerate(rows):
        m = OBJECT_RE.match(strip(raw))
        if m and not raw[:1].isspace() and m.group(2) == child:
            nl = "\r\n" if raw.endswith("\r\n") else "\n"
            add = ["\t" + NOTE % (parent, faction) + nl]
            for tag, block in blocks:
                if tag not in own:
                    add += [r.rstrip("\r\n") + nl for r in block] + [nl]
            rows[i + 1:i + 1] = add
            return "".join(rows)
    raise ValueError("no object %s" % child)


def localise(files, install, style, faction):
    """files ({archive member: bytes}, the pack) with each INI member that edits a parent other groups'
    objects inherit too taken out, its Draw modules written into this faction's children instead.
    Refuses an edit of such a member that is not in a shared parent's Draw modules."""
    mine = {m for d in style.ini_dirs() for m in install.members(d) if m.endswith(".ini")}
    parents = {}                                    # {object: parent} over the game's object INIs
    for m in install.members("data\\ini\\object"):
        if m.endswith(".ini"):
            for obj, p in install._parsed(m)[1].items():
                parents.setdefault(obj, p)
    where = install.object_index()
    out = dict(files)
    for member in sorted(m for m in files if m.endswith(".ini") and m.startswith("data\\ini\\object\\") and m not in mine):
        ea = install.read(member).decode("latin-1")
        defined = parse_objects(ea)
        heirs = {}                                  # {parent defined here: [(member, child) of ours]}
        foreign = set()                             # parents defined here other groups' objects inherit
        for child, p in parents.items():
            if p in defined and child not in defined:
                if where.get(child) in mine:
                    heirs.setdefault(p, []).append((where[child], child))
                elif not where.get(child, "").startswith(OBSOLETE):
                    foreign.add(p)
        if not foreign:
            continue                                # only our objects inherit from it: the edits stay there
        shared = sorted(heirs)                      # every parent here our objects inherit, edited or not
        new = files[member].decode("latin-1")
        if without_draws(new, shared) != without_draws(ea, shared):
            raise SystemExit("%s: %s edits more than the Draw modules of %s (other factions' objects inherit "
                             "from it too, so no pack may ship it)" % (faction, member, ", ".join(shared)))
        del out[member]
        for p in shared:
            rows = new.splitlines(keepends=True)
            if [rows[a:z + 1] for _, a, z in draw_spans(new, p)] == \
                    [ea.splitlines(keepends=True)[a:z + 1] for _, a, z in draw_spans(ea, p)]:
                continue                            # not edited: the child inherits EA's as before
            blocks = [(tag, rows[a:z + 1]) for tag, a, z in draw_spans(new, p)]
            for child_member, child in sorted(heirs[p]):
                text = (out.get(child_member) or install.read(child_member)).decode("latin-1")
                out[child_member] = give(text, child, p, blocks, faction).encode("latin-1")
    return out


def clashes(archive, files):
    """[(member, other archive)] of the INIs `files` (the pack named `archive`) ships that another
    faction pack in the game folder ships with other bytes: the one sorting first would hide the other's
    edits (sagekit/install.py refuses to stage such a pack)."""
    import os
    from . import paths
    from .formats.big import Archive, norm
    d, out = paths.GAMEDIRS["rotwk"], []
    inis = {norm(m): v for m, v in files.items() if m.lower().endswith(".ini")}
    for name in sorted(os.listdir(d), key=str.lower):
        if not name.lower().endswith(".big") or not name.startswith(PACK) or name.startswith(PACK + "!") \
                or name.lower() == archive.lower():
            continue
        other = Archive(os.path.join(d, name))
        out += [(m, name) for m in sorted(set(inis) & set(other.index())) if other.read(m) != inis[m]]
    return out


def self_check():
    """Game-free check on EA's shapes (run by `sagekit validate`): [] when it holds."""
    parent = ("Object LumberMill\n  Draw = W3DScriptedModelDraw ModuleTag_Draw\n    DefaultModelConditionState\n"
              "      Model = WBLumMill_SKN\n    End\n    IdleAnimationState\n      Animation = A\n"
              "        AnimationName = X.Y\n      End\n    End\n  End\n  Draw = W3DFloorDraw Bib\n"
              "    ModelName = MBLumMill_Bib\n  End\n  Body = StructureBody ModuleTag_05\n  End\nEnd\n")
    child = "ChildObject WildLumberMill LumberMill\r\n  Side = Wild\r\nEnd\r\n"
    fails = []
    spans = draw_spans(parent, "LumberMill")
    if [(t, a, z) for t, a, z in spans] != [("ModuleTag_Draw", 1, 10), ("Bib", 11, 13)]:
        fails.append("draw_spans: %s" % spans)
    rows = parent.splitlines(keepends=True)
    out = give(child, "WildLumberMill", "LumberMill", [(t, rows[a:z + 1]) for t, a, z in spans], "goblins")
    if [t for t, _, _ in draw_spans(out, "WildLumberMill")] != ["ModuleTag_Draw", "Bib"] or "\r\n" not in out \
            or re.search(r"[^\r]\n", out):
        fails.append("give: %r" % out)
    if without_draws(parent.replace("WBLumMill", "IBLumMill"), ["LumberMill"]) != without_draws(parent, ["LumberMill"]):
        fails.append("without_draws sees a Draw module's edit")
    return fails
