"""python3 -m sagekit ui2x [options] (docs/UI2X.md)

    --stage (or nothing) build items 2-4 and the icon pages at 2x, check them, stage
                         build/assets/_ui2x/_install/: !!!!!!!!!!!!!!sagekit-ui2x.big and the icon
                         archive at 2x, the duplicate scan over every staged *sagekit-*.big, the
                         review sheets (build/assets/_review_finish/ui2x/)
    --sheet              the review sheets only (from the last build)
    --install | --revert [--dry-run]   the ui2x archive in RotWK/, and the icon archive rebuilt at
                         2x (install) or 1x (revert)
"""
import argparse
import glob
import os


def sheets():
    """The review sheets: items 2-3 from EA's pages, item 1 from the icon archive's 1x pages (ours
    as installed today) against the 2x, item 4 from the tooltip pieces."""
    import json
    from .. import paths
    from ..icons import root as icons_root
    from ..icons.install import shared_root
    from . import root
    from .sheet import decoded, review, sheet, tooltip_sheet
    pages = {os.path.basename(p)[:-4]: p for p in glob.glob(os.path.join(root("pages"), "*.dds"))}
    entries = []
    for f in sorted(os.listdir(paths.BUILD)):
        man = os.path.join(icons_root(f), "icons.json")
        if not os.path.exists(man):
            continue
        items = json.load(open(man))
        for kind in ("portrait", "button"):
            name = next((n for n, m in sorted(items.items()) if m["kind"] == kind and m["page"] in pages), None)
            if name:
                m = items[name]
                before = os.path.join(shared_root(), "pages", m["page"] + ".png")
                if os.path.exists(before):
                    entries.append((name, before, decoded(pages[m["page"]]), tuple(m["rect"]), kind))
    icon_pages = {e[2] for e in entries}
    made = review({p: d for p, d in pages.items() if decoded(d) not in icon_pages}, entries)
    stray = []                  # the rects Real-ESRGAN strayed on (less of it used): the hard cases
    for f in sorted(glob.glob(os.path.join(root("report"), "*.json"))):
        for page, rows in json.load(open(f)).items():
            stray += [(page, tuple(r[0]), r[5]) for r in rows if len(r) > 5 and r[5] is not None and r[5] < 0.8]
    e = [("%s %s (%.1f ESRGAN)" % (page, list(rect), w), os.path.join(root("src"), page + ".png"),
          decoded(pages[page]), rect, "portrait" if rect[3] - rect[1] >= 100 else "button")
         for page, rect, w in sorted(stray, key=lambda x: x[2])[:10] if page in pages]
    if e:
        made.append(sheet("hardest", e, "the hardest: busy art where Real-ESRGAN invented detail, so less of it"))
    made.append(tooltip_sheet())
    return made


def main(argv):
    ap = argparse.ArgumentParser(prog="python3 -m sagekit ui2x", description=__doc__.split("\n")[0])
    for x in ("stage", "install", "revert", "sheet"):
        ap.add_argument("--" + x, action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.sheet:
        print("\n".join(sheets()))
        return 0
    from .install import main as install
    if a.install or a.revert:
        return install("install" if a.install else "revert", a.dry_run)
    rc = install("stage")
    print("\n".join(sheets()))
    return rc
