"""Item 1: the pages our building icons sit on, at 2x, for the icon archive (sagekit/icons/install.py
`members(factions, 2)`). Our rects come from the graded 4x crops the icon run leaves
(build/assets/<faction>/_icons/crops/<image>_new@4x.png), box-filtered to 2x; every other image on
the page is EA's, upscaled as items 2 and 3 are."""
from ..formats.textures import compiled_path
from ..game import Install
from .build import build
from .select import doublable, rects


def spec(g, big):
    out = {}
    for page, ours in sorted(big.items()):
        inf, why = doublable(g, page)
        if why:
            raise SystemExit("%s cannot ship at 2x: %s" % (page, why))
        mine = {tuple(r) for r, _, _ in ours}
        rs = [dict(rect=list(r), kind="portrait" if min(r[2] - r[0], r[3] - r[1]) >= 100 else "button")
              for r in rects(g, page) if tuple(r) not in mine]
        rs += [dict(rect=list(r), kind=kind, own=path) for r, path, kind in ours]
        out[page] = dict(mips=inf["mips"] + 1, rects=rs)
    return out


def pages2x(big):
    """{archive member: bytes} of the 2x pages, checked (refuses on any problem)."""
    g = Install()
    s = spec(g, big)
    out, probs = build(s)
    if probs:
        raise SystemExit("icon pages at 2x:\n  " + "\n  ".join(probs))
    return {compiled_path(page, ".dds"): open(out[page], "rb").read() for page in s}
