"""The engine's upgrade limit: every Upgrade the game defines takes one bit of a fixed mask.

RotWK 2.02 keeps an object's upgrades in a mask of 0x24 dwords, 1152 bits (exe 0x444db3 copies it
as 0x90 bytes). Each Upgrade definition takes the next bit when the INI loads (0x66fcb7, no limit
check). Object::removeUpgrade (0x691438) builds a mask on its stack, so a bit past 1151 overwrites
its saved frame pointer and return address: the game crashes the first time such an upgrade is
removed (the cah pack's crash, docs/CAH.md). EA's 2.02 defines 1027 upgrades.

    tally(ours)     EA's names plus {source: names} of ours: (total, problems, report line)
    validate()      python3 -m sagekit validate: EA + every installed archive of ours + the staged cah pack
"""
import os
import re

from . import paths
from .formats.big import Archive

LIMIT = 1152
_RX = re.compile(r"^[ \t]*Upgrade[ \t]+([^\s=;/]+)[ \t]*(?:(?:;|//)[^\n]*)?\r?$", re.M)


def names(text):
    """The (lower-case) names of the Upgrade blocks an INI text defines."""
    return {n.lower() for n in _RX.findall(text)}


def _ini_names(read, members):
    out = set()
    for m in members:
        if m.startswith("data\\ini\\") and m.endswith((".ini", ".inc")):
            out |= names(read(m).decode("latin-1"))
    return out


def ea_names():
    """Every Upgrade EA's game files define (every INI under data\\ini, our archives left out)."""
    from .game import Install
    g = Install()
    return _ini_names(g.read, g.members("data\\ini\\"))


def archive_names(path):
    a = Archive(str(path))
    return _ini_names(a.read, a.index())


def installed_ours(skip=()):
    """{archive file name: Upgrade names} of every archive of ours in the game folder, but `skip`."""
    d = paths.GAMEDIRS["rotwk"]
    return {f: archive_names(os.path.join(d, f)) for f in sorted(os.listdir(d))
            if f.lower().endswith(".big") and paths.is_ours(f) and f not in skip}


def tally(ours, ea=None):
    """(total, problems, line): EA's upgrades plus every {source: names} of ours, against LIMIT."""
    ea = ea_names() if ea is None else ea
    allnames = set(ea).union(*ours.values()) if ours else set(ea)
    adds = ", ".join("%s %d" % (k, len(v - ea)) for k, v in ours.items() if v - ea) or "nothing"
    line = "upgrades: EA %d + ours %d (%s) = %d of the engine's %d; headroom %d" % (
        len(ea), len(allnames) - len(ea), adds, len(allnames), LIMIT, LIMIT - len(allnames))
    problems = [] if len(allnames) <= LIMIT else [line + ": over the limit, the game would crash (sagekit/upgrades.py)"]
    return len(allnames), problems, line


def validate():
    """Count EA + every installed archive of ours + the staged cah pack; 1 when over the limit."""
    from .units import Folder, load
    try:
        ea = ea_names()
        ours = installed_ours()
    except OSError as e:
        print("note: game files not readable (%s): the upgrade limit not checked" % e)
        return 0
    u = load("cah/pack")
    staged = Folder(u).stage / u.archive
    if staged.exists():
        ours["staged " + u.archive] = archive_names(staged)
    _, problems, line = tally(ours, ea)
    print("FAIL " + problems[0] if problems else "ok   " + line)
    return 1 if problems else 0
