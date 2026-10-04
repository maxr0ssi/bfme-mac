"""Edits on EA's INI text that keep every other byte: modules found by tag, fields set in place,
blocks appended, command-set slots inserted. Each edit fails loudly when EA's text is not the one
it was written for (a different patch level must be looked at, not guessed through).
"""
import re

NL = "\r\n"
MODULE_RE = re.compile(r"^[ \t]*(Behavior|Body|ClientBehavior|ClientUpdate|Draw)[ \t]*=[ \t]*(\w+)[ \t]+(\w+)", re.M)


def code(line):
    return re.split(r";|//", line, maxsplit=1)[0].strip()


def object_span(src, name):
    """(start, end) of `Object|ChildObject <name>` up to and including its closing End line."""
    m = re.search(r"^(?:Object|ChildObject)[ \t]+%s\b[^\n]*\n" % re.escape(name), src, re.M)
    if not m:
        raise SystemExit("heroes: no object %s here" % name)
    nxt = re.search(r"^(?:Object|ChildObject|ObjectReskin)[ \t]+\S+", src[m.end():], re.M)
    stop = m.end() + nxt.start() if nxt else len(src)
    ends = list(re.finditer(r"^End\b[^\n]*(\n|$)", src[m.start():stop], re.M))
    if not ends:
        raise SystemExit("heroes: object %s has no closing End" % name)
    return m.start(), m.start() + ends[-1].end()


def module_span(src, tag, start=0, end=None):
    """(start, end) of the module tagged `tag` (its `X = Kind Tag` line through its End line)."""
    end = len(src) if end is None else end
    hits = [m for m in MODULE_RE.finditer(src, start, end) if m.group(3) == tag]
    if len(hits) != 1:
        raise SystemExit("heroes: %d modules tagged %s (expected 1)" % (len(hits), tag))
    m = hits[0]
    line_start = src.rfind("\n", 0, m.start()) + 1
    pos, depth = src.index("\n", m.end()) + 1, 1
    while pos < end:
        nl = src.find("\n", pos)
        nl = end if nl < 0 else nl + 1
        c = code(src[pos:nl])
        if c.lower() == "end":
            depth -= 1
            if depth == 0:
                return line_start, nl
        elif c and "=" not in c and re.fullmatch(r"[A-Za-z_]\w*", c) and c.lower() not in ("beginscript", "endscript"):
            depth += 1                  # a nested block (ReplaceObject, LodOptions ...)
        pos = nl
    raise SystemExit("heroes: module %s never ends" % tag)


def module_text(src, tag, start=0, end=None):
    s, e = module_span(src, tag, start, end)
    return src[s:e]


def remove_modules(src, tags, start, end):
    """src with the modules `tags` (inside [start, end)) removed; returns (src, removed bytes)."""
    removed = 0
    for tag in tags:
        s, e = module_span(src, tag, start, end - removed)
        src = src[:s] + src[e:]
        removed += e - s
    return src, removed


def set_field(block, key, value, count=1, comment=None):
    """Every `key = ...` line of `block` (exactly `count` of them) set to `value`, EA's indentation kept."""
    rx = re.compile(r"^([ \t]*%s[ \t]*=[ \t]*)([^\r\n]*)" % re.escape(key), re.M)
    hits = [m for m in rx.finditer(block) if not code(m.group(0)) == ""]
    hits = [m for m in hits if code(m.group(0)).lower().startswith(key.lower())]
    if len(hits) != count:
        raise SystemExit("heroes: %d lines %s (expected %d)" % (len(hits), key, count))
    tail = "\t; sagekit heroes%s" % (": " + comment if comment else "")
    for m in reversed(hits):
        block = block[:m.start()] + m.group(1) + value + tail + block[m.end():]
    return block


def replace_once(text, old, new, what):
    if text.count(old) != 1:
        raise SystemExit("heroes: %s: expected one %r, found %d" % (what, old, text.count(old)))
    return text.replace(old, new)


def retag(module, new_tag):
    """A module copied under its own tag (tags must be unique within an object)."""
    m = MODULE_RE.search(module)
    return module[:m.start(3)] + new_tag + module[m.end(3):]


def blocks(src, kind):
    """{name: (start, end, body)} of top-level `kind Name ... End` blocks."""
    out = {}
    for m in re.finditer(r"^%s[ \t]+(\S+)[^\n]*\n(.*?)^End\b[^\n]*(\n|$)" % kind, src, re.M | re.S | re.I):
        out.setdefault(m.group(1), (m.start(), m.end(), m.group(2)))
    return out


def append(src, text, banner):
    """`text` appended after EA's last line, under a banner comment."""
    nl = NL if NL in src else "\n"
    body = text.replace("\r\n", "\n").replace("\n", nl)
    return src.rstrip("\r\n") + nl * 2 + "; ---- sagekit heroes pack: %s (assets/heroes)" % banner + nl + body.rstrip("\r\n") + nl


def lf_to(src, text):
    """`text` with the line ends `src` uses."""
    return text.replace("\r\n", "\n").replace("\n", NL if NL in src else "\n")
