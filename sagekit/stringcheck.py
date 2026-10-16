"""String labels: every label our archives' INI blocks add must be in the string table the game reads.

The game reads data\\lotr.str from the LAST of RotWK's lang\\English*.big in case-insensitive name
order (the lang folder loads with overwrite on; assets/heroes/strings.py has the addresses). One
table wins whole, so the table that wins must be ours whenever any of ours is installed, and it must
hold every label our INI blocks reference. An EA block we ship unchanged keeps EA's own missing
labels (EA's bugs, counted, not failed); a block we add or change fails on a label the table lacks
that EA's block of the same name did not already reference.

    winner(names)          the lang archive the game takes lotr.str from
    labels(data)           {label lower-case: text} of a string table
    problems()             (failures, notes) over the installed and staged state
    validate()             python3 -m sagekit validate: prints, returns the failure count
"""
import os
import re

from . import paths
from .formats.big import Archive

MEMBER = "data\\lotr.str"
# INI fields whose values are string labels (DisplayName, TextLabel, DescriptLabel, RecruitText,
# Hotkey, LacksPrerequisiteLabel, DescriptionStrategic, ...: every field EA fills with a label)
FIELD = re.compile(r"^[ \t]*(\w*(?:Label|Name|Tag|Text|Help|Title|Tooltip|Description|Notice|Message|Hotkey|"
                   r"Objectives|Fiction|GameType|Territory|Strategic|BonusLegendary|BonusArmy|BonusResource))"
                   r"[ \t]*=[ \t]*([^;\r\n]*)", re.M | re.I)
TOKEN = re.compile(r"\b([A-Za-z]+):([A-Za-z0-9_\-.]+)")
HEAD = re.compile(r"^([A-Za-z]\w*)[ \t]+([^\s;/]+)", re.M)


def lang_dir():
    return os.path.join(paths.GAMEDIRS["rotwk"], "lang")


def order_key(name):
    """The game's order: _memicmp over the common length, then the shorter first (0x405324)."""
    return name.lower().encode("latin-1")


def winner(names):
    """The lang\\English*.big that provides data\\lotr.str: the last in the game's order that has one."""
    cands = [n for n in names if n.lower().startswith("english") and n.lower().endswith(".big")]
    return max(cands, key=order_key) if cands else None


def labels(data):
    """{label lower-case: text} (comment lines between a label and its text skipped, as the game does)."""
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


def blocks(text):
    """{(keyword, name) lower-case: block text} of the top-level blocks of an INI text."""
    hs = [h for h in HEAD.finditer(text) if h.group(1).lower() not in ("end", "#include", "#define")]
    return {(h.group(1).lower(), h.group(2).lower()): text[h.start(): hs[k + 1].start() if k + 1 < len(hs) else len(text)]
            for k, h in enumerate(hs)}


def refs(text, cats):
    """{label lower-case: label} a block's label fields reference (categories the table knows)."""
    out = {}
    for _, val in FIELD.findall(re.sub(r"//[^\r\n]*", "", text)):
        for c, n in TOKEN.findall(val):
            if c.lower() in cats:
                out.setdefault(("%s:%s" % (c, n)).lower(), "%s:%s" % (c, n))
    return out


def _ini(read, members):
    return {m: read(m).decode("latin-1") for m in members if m.startswith("data\\ini\\") and m.endswith((".ini", ".inc"))}


def ea_blocks():
    from .game import Install
    g = Install()
    out = {}
    for text in _ini(g.read, g.members("data\\ini\\")).values():
        for k, body in blocks(text).items():
            out.setdefault(k, body)
    return out


def ours():
    """{source: Archive} of every archive of ours in the game folder, and the staged cah and heroes packs."""
    d = paths.GAMEDIRS["rotwk"]
    out = {f: Archive(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.lower().endswith(".big") and paths.is_ours(f)}
    from .units import Folder, load
    for uid in ("cah/pack", "heroes/pack"):
        u = load(uid)
        staged = Folder(u).stage / u.archive
        if staged.exists():
            out["staged " + u.archive] = Archive(str(staged))
    return out


def tables():
    """[(state, lang archive the game takes lotr.str from, its path, ours?)] for the installed lang
    folder and, when the heroes pack is staged, the folder with the staged string table in place."""
    from assets.heroes.strings import LEGACY_ARCHIVES, STRINGS_ARCHIVE
    from .units import Folder, load
    have = {n: os.path.join(lang_dir(), n) for n in os.listdir(lang_dir())}
    ourn = {STRINGS_ARCHIVE.lower()} | {n.lower() for n in LEGACY_ARCHIVES}
    out = []
    w = winner(have)
    out.append(("installed", w, have[w], any(n.lower() in ourn for n in have)))
    u = load("heroes/pack")
    staged = Folder(u).stage / STRINGS_ARCHIVE
    if staged.exists():
        st = {n: p for n, p in have.items() if n.lower() not in ourn}
        st[STRINGS_ARCHIVE] = str(staged)
        w = winner(st)
        out.append(("staged", w, st[w], True))
    return out


def problems():
    from assets.heroes.strings import LEGACY_ARCHIVES, STRINGS_ARCHIVE
    fails, notes = [], []
    ourn = {STRINGS_ARCHIVE.lower()} | {n.lower() for n in LEGACY_ARCHIVES}
    if winner([STRINGS_ARCHIVE, "englishpatch202.big", "English.big", "EnglishAudio.big"]) != STRINGS_ARCHIVE:
        fails.append("strings: %s does not sort after englishpatch202.big; the game would read EA's table" % STRINGS_ARCHIVE)
    ea = ea_blocks()
    archives = ours()
    for state, name, path, mine in tables():
        if mine and name.lower() not in ourn:
            fails.append("strings (%s): the game reads lotr.str from lang\\%s, not ours: every label of ours "
                         "shows as MISSING (assets/heroes/strings.py)" % (state, name))
        tab = labels(Archive(path).read(MEMBER))
        cats = {k.split(":", 1)[0] for k in tab}
        missing, inherited = {}, 0
        for src, a in archives.items():
            if state == "staged" and src == "!!!!!!!!!!!sagekit-heroes.big" and "staged !!!!!!!!!!!sagekit-heroes.big" in archives:
                continue
            if state == "installed" and src.startswith("staged "):
                continue
            for m, text in _ini(a.read, a.index()).items():
                for k, body in blocks(text).items():
                    theirs = ea.get(k)
                    if theirs is not None and theirs.split() == body.split():
                        continue
                    old = refs(theirs, cats) if theirs is not None else {}
                    for low, lab in refs(body, cats).items():
                        if low in tab:
                            continue
                        if low in old:
                            inherited += 1
                        else:
                            missing.setdefault(lab, "%s %s (%s %s)" % (src, m, k[0], k[1]))
        for lab, where in sorted(missing.items()):
            fails.append("strings (%s, lang\\%s): %s is not in the table; %s" % (state, name, lab, where))
        notes.append("strings (%s): lotr.str from lang\\%s (%d labels)%s; %d references EA's own blocks already "
                     "lacked" % (state, name, len(tab), ", ours" if name.lower() in ourn else "", inherited))
    return fails, notes


def validate():
    try:
        fails, notes = problems()
    except OSError as e:
        print("note: game files not readable (%s): string labels not checked" % e)
        return 0
    for n in notes:
        print("ok   " + n if not fails else "note " + n)
    for f in fails:
        print("FAIL " + f)
    return len(fails)
