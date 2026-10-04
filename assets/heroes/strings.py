"""The heroes pack's names and tooltips: 2.02's English string table with our labels added.

The game reads data\\lotr.str from lang\\English*.big before any root archive (exe 0xa14419: lang
first, then the root *.big; the first archive to file a member wins, 0xa18384). So the strings
ship in their own lang archive, named to load before English.big and englishpatch202.big
(STRINGS_ARCHIVE): a copy of 2.02's table (the live one: 2.02's own units are named only there)
plus our labels. Every other label keeps 2.02's text; the few EA labels we correct are listed.
"""
import re

from . import ea

STRINGS_ARCHIVE = "English!!!!!!!!!!!sagekit-heroes.big"      # lang\; sorts before English.big either way
MEMBER = "data\\lotr.str"


def compose(entries):
    """2.02's table with `entries` [(label, text)]: an existing label's text replaced in place,
    a new one appended. Returns (bytes, {"added": [...], "replaced": [...]})."""
    src = ea.strings_text()
    nl = "\r\n" if "\r\n" in src else "\n"
    added, replaced = [], []
    for label, text in entries:
        if '"' in text:
            raise SystemExit("heroes: a string may not hold a double quote: %s" % label)
        rx = re.compile(r"(^[ \t]*%s[ \t]*\r?\n(?:[ \t]*//[^\r\n]*\r?\n|[ \t]*\r?\n)*[ \t]*)\"[^\"\r\n]*\"" % re.escape(label),
                        re.M | re.I)
        hits = list(rx.finditer(src))
        if len(hits) > 1:
            raise SystemExit("heroes: %s is in 2.02's table %d times" % (label, len(hits)))
        if hits:
            m = hits[0]
            src = src[:m.start()] + m.group(1) + '"%s"' % text + src[m.end():]
            replaced.append(label)
        else:
            added.append(label)
    tail = "".join("%s%s%s\"%s\"%sEND%s" % (nl, label, nl, text, nl, nl) for label, text in entries if label in added)
    src = src.rstrip("\r\n") + nl + nl + "// sagekit heroes pack (assets/heroes): our labels" + nl + tail
    return src.encode("utf-8"), {"added": added, "replaced": replaced}


def labels_of(data):
    """{label lower-case: text} of a string table, as ea.labels() reads 2.02's."""
    out, label = {}, None
    for line in data.decode("utf-8", "replace").splitlines():
        s = line.strip()
        if not s or s.startswith("//"):
            continue
        if label is None:
            if re.match(r"^[A-Za-z0-9_]+:\S+$", s):
                label = s
        elif s.upper() == "END":
            out.setdefault(label.lower(), "")
            label = None
        elif s.startswith('"'):
            out.setdefault(label.lower(), s.strip('"'))
    return out


def check(data, entries):
    """Our table is 2.02's with exactly our labels added or changed."""
    ours, theirs = labels_of(data), ea.labels()
    want = {k.lower(): v for k, v in entries}
    diff = {k for k in set(ours) | set(theirs) if ours.get(k) != theirs.get(k)}
    if diff != set(want):
        raise SystemExit("heroes: the string table differs from 2.02's in %s" % sorted(diff ^ set(want))[:8])
    for k, v in want.items():
        if ours.get(k) != v:
            raise SystemExit("heroes: %s reads %r, not %r" % (k, ours.get(k), v))
    return len(diff)
