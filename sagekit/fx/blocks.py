"""The INI blocks the FX work reads and writes, by line: particle systems, FX lists, object modules.

Three grammars, each regular enough to walk by line (comments start with ';' or '//'):

    FXParticleSystem <Name>             every line directly inside opens a module (`System`,
      System ... End                    `Color = DefaultColor`, `Update = DefaultUpdate`, ...);
      Color = DefaultColor              a module holds only `key = value` fields
        Color1 = R:0 G:0 B:0 0
      End
    End

    FXList <Name>                       a nugget opens on a line without '=' (`ParticleSystem`,
      ParticleSystem                    `Sound`, `DynamicDecal`, `FXListAtBonePos`, ...) and holds
        Name = <system>                 only fields
      End
    End

    Object | ChildObject <Name> ...     a module opens on `Behavior | Draw | ClientBehavior ... = <Type> <Tag>`;
      Behavior = <Type> <Tag>           the spell books' modules hold only fields, so their End is the
        TriggerFX = <FXList>            first one after the header (`module` checks that)
      End
    End

Every function takes and returns text with the file's own line endings untouched.
"""
import re

from ..formats.ini import strip

PS_HEAD = re.compile(r"^FXParticleSystem[ \t]+(\S+)", re.I)
FXLIST_HEAD = re.compile(r"^FXList[ \t]+(\S+)", re.I)
OBJ_HEAD = re.compile(r"^(Object|ChildObject|ObjectReskin)[ \t]+(\S+)(?:[ \t]+([^\s;/]+))?", re.I)
MODULE_HEAD = re.compile(r"^[ \t]*(Behavior|Draw|ClientBehavior|ClientUpdate|Body)[ \t]*=[ \t]*(\S+)[ \t]+([^\s;/]+)", re.I)
SYSTEM_REFS = ("SlaveSystem", "PerParticleAttachedSystem")   # a system's fields naming another system


def lines(text):
    return text.splitlines(keepends=True)


def _span(rows, i, nested):
    """Index of the End closing the block whose header is rows[i]. nested(depth, stripped line)
    says whether a non-End line opens a block."""
    depth = 1
    for j in range(i + 1, len(rows)):
        s = strip(rows[j])
        if not s:
            continue
        if s.lower() == "end":
            depth -= 1
            if depth == 0:
                return j
        elif nested(depth, s):
            depth += 1
    raise ValueError("block at line %d has no End" % (i + 1))


def _ps_nested(depth, s):
    return depth == 1


def _fx_nested(depth, s):
    return "=" not in s


def index(text, head, nested):
    """{name.lower(): (name, first row, End row)} of the top-level blocks `head` matches."""
    rows, out, i = lines(text), {}, 0
    while i < len(rows):
        m = head.match(rows[i]) if not rows[i][:1].isspace() else None
        if m and strip(rows[i]):
            z = _span(rows, i, nested)
            out.setdefault(m.group(1).lower(), (m.group(1), i, z))
            i = z + 1
            continue
        i += 1
    return out


def systems(text):
    return index(text, PS_HEAD, _ps_nested)


def fxlists(text):
    return index(text, FXLIST_HEAD, _fx_nested)


def body(text, span):
    """The rows of a block (header to End) as a list of strings with their line endings."""
    _, a, z = span
    return lines(text)[a:z + 1]


def modules_of(rows):
    """[(module name, [(key, value, row index)])] of a particle system's rows (header to End)."""
    out, cur = [], None
    for i, raw in enumerate(rows[1:-1], 1):
        s = strip(raw)
        if not s:
            continue
        if s.lower() == "end":
            cur = None
            continue
        key, _, val = (x.strip() for x in s.partition("="))
        if cur is None:
            cur = (s, [])
            out.append(cur)
        else:
            cur[1].append((key, val, i))
    return out


def field(rows, module, key):
    """The value of `key` in the particle system module whose opener starts with `module`, or None."""
    for name, fields in modules_of(rows):
        if name.split("=")[0].strip().lower() == module.lower():
            for k, v, _ in fields:
                if k.lower() == key.lower():
                    return v
    return None


def refs(rows):
    """Systems a particle system names (its slave and per-particle systems)."""
    out = []
    for name, fields in modules_of(rows):
        for k, v, _ in fields:
            if k in SYSTEM_REFS and v.split()[0].lower() != "none":
                out.append(v.split()[0])
    return out


def nuggets(rows):
    """[(nugget, {key: value}, first row, End row)] of an FX list's rows (header to End)."""
    out, cur = [], None
    for i, raw in enumerate(rows[1:-1], 1):
        s = strip(raw)
        if not s:
            continue
        if s.lower() == "end":
            if cur:
                cur[3] = i
                out.append(tuple(cur))
            cur = None
        elif cur is None:
            cur = [s.split()[0], {}, i, None]
        else:
            k, _, v = (x.strip() for x in s.partition("="))
            cur[1].setdefault(k, v)
    return out


def rename(rows, old, new):
    """rows with the header's name `old` replaced by `new` (the first row only)."""
    head = rows[0]
    i = head.index(old)
    return [head[:i] + new + head[i + len(old):]] + rows[1:]


def set_value(raw, value):
    """A `key = value` row with its value replaced, its indentation, comment and ending kept."""
    m = re.match(r"^([ \t]*[^=;/]*?=[ \t]*)(.*?)([ \t]*(?:;.*|//.*)?)(\r?\n?)$", raw)
    if not m:
        raise ValueError("not a field row: %r" % raw)
    return m.group(1) + value + m.group(4)


def drop_comment(raw):
    """A row without its trailing comment (EA's `;,; old value` notes would misdescribe our values)."""
    end = "\r\n" if raw.endswith("\r\n") else "\n" if raw.endswith("\n") else ""
    body_ = raw[:len(raw) - len(end)]
    cut = min([i for i in (body_.find(";"), body_.find("//")) if i >= 0], default=len(body_))
    return body_[:cut].rstrip() + end


# ------------------------------------------------------------------------------------ objects
def objects(text):
    """{name.lower(): (name, parent or None, header row, End row)} of the top-level objects. An
    object's End is the first top-level `End` (column 0, or the first End at depth 0 by modules)."""
    rows, out = lines(text), {}
    heads = [i for i, r in enumerate(rows) if not r[:1].isspace() and OBJ_HEAD.match(strip(r) or "-")]
    for n, i in enumerate(heads):
        m = OBJ_HEAD.match(strip(rows[i]))
        stop = heads[n + 1] if n + 1 < len(heads) else len(rows)
        z = next((j for j in range(stop - 1, i, -1) if strip(rows[j]).lower() == "end" and not rows[j][:1].isspace()), None)
        if z is None:
            raise ValueError("object %s has no End in column 0" % m.group(2))
        out.setdefault(m.group(2).lower(), (m.group(2), m.group(3) if m.group(1).lower() != "object" else None, i, z))
    return out


def module(text, obj, tag):
    """(header row, End row) of object `obj`'s module `tag` (a flat module: fields only)."""
    o = objects(text).get(obj.lower())
    if o is None:
        raise ValueError("no object %s" % obj)
    rows = lines(text)
    for i in range(o[2] + 1, o[3]):
        m = MODULE_HEAD.match(rows[i].split(";")[0])
        if m and m.group(3) == tag:
            for j in range(i + 1, o[3]):
                s = strip(rows[j])
                if s.lower() == "end":
                    return i, j
                if s and "=" not in s:
                    raise ValueError("%s %s: nested block %r (not a flat module)" % (obj, tag, s))
            break
    raise ValueError("%s has no module %s" % (obj, tag))


def module_fields(text, obj, tag):
    """[(key, value)] of a flat module, in order."""
    a, z = module(text, obj, tag)
    out = []
    for raw in lines(text)[a + 1:z]:
        s = strip(raw)
        if s:
            k, _, v = (x.strip() for x in s.partition("="))
            out.append((k, v))
    return out
