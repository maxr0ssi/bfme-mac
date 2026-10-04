"""Which pages double, and the checks that make doubling safe (stdlib only).

A page doubles only when every MappedImage on it (from any INI) declares the page's real size and
lies inside it: then Coords over the declared size give the same UVs on a page twice the size.
Pages our building icons sit on belong to the icon archive (sagekit/icons/install.py builds them at
2x), and a page any other archive of ours provides is left to that archive.
"""
import json
import os

from .. import paths
from ..game import Install
from ..icons import pages as ipages
from ..icons import root as icons_root
from ..icons.mapped import images, on_page, page_member
from . import INIS

INI_DIR = "data\\ini\\mappedimages\\aptimages\\"


def icon_pages():
    """{page} any faction's icon run draws on (build/assets/<faction>/_icons/icons.json)."""
    out = set()
    for f in sorted(os.listdir(paths.BUILD)):
        p = os.path.join(icons_root(f), "icons.json")
        if os.path.exists(p):
            out |= {m["page"] for m in json.load(open(p)).values()}
    return out


def rects(g, page):
    """The distinct rects of every MappedImage on the page, with the names that use each."""
    out = {}
    for i in on_page(g, page):
        out.setdefault(i.rect, []).append(i.name)
    return out


def doublable(g, page):
    """(page info, None) when the page can ship at 2x as it is, else (None, reason)."""
    try:
        member = page_member(g, page)
    except FileNotFoundError:
        return None, "no page in the archives"
    if not member.endswith(".dds"):
        return None, "a TGA page"
    inf = ipages.info(g.read(member))
    size = (inf["width"], inf["height"])
    for i in on_page(g, page):
        if i.size != size:
            return None, "%s declares %s, the page is %s" % (i.name, i.size, size)
        l, t, r, b = i.rect
        if not (0 <= l < r <= size[0] and 0 <= t < b <= size[1]):
            return None, "%s's rect %s is outside the page" % (i.name, i.rect)
    if inf["fourcc"] not in ("DXT3", "DXT5", ipages.RAW):
        return None, "format %r" % inf["fourcc"]
    return dict(inf, member=member), None


def select(g=None):
    """({page: {member, width, height, mips, fourcc, item, rects}}, {page: reason skipped})."""
    g = g or Install()
    active = Install(pristine=False)
    skip_icons = icon_pages()
    by_page = {}
    for i in images(g).values():
        ini = i.ini.lower()
        if ini.startswith(INI_DIR) and ini[len(INI_DIR):] in INIS:
            by_page.setdefault(i.page, INIS[ini[len(INI_DIR):]])
    out, skipped = {}, {}
    for page, item in sorted(by_page.items()):
        if page in skip_icons:
            skipped[page] = "the icon archive's (item 1)"
            continue
        inf, why = doublable(g, page)
        if why:
            skipped[page] = why
            continue
        owner = active.owner(inf["member"])
        if owner is not None and paths.is_ours(owner.path) and "sagekit-ui2x" not in owner.path \
                and "sagekit-icons" not in owner.path:
            skipped[page] = "provided by %s" % os.path.basename(owner.path)
            continue
        out[page] = dict(inf, item=item, rects=[list(r) for r in sorted(rects(g, page))])
    return out, skipped
