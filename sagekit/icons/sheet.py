"""The review sheet: per icon EA's against ours at 1x and at 2x (as Retina shows them), then each
page before and after (build/assets/<faction>/_review/icons_v<N>.jpg)."""
import os
import subprocess

from .. import paths
from . import root
from .pixels import MAGICK

BG = "#262626"


def label(text, w):
    return ["(", "-size", "%dx24" % w, "xc:" + BG, "-font", paths.FONT, "-pointsize", "13", "-fill", "#e8e0cc",
            "-gravity", "west", "-annotate", "+6+0", text, ")"]


def tile(png, scale, bg=BG):
    return ["(", png, "-background", bg, "-alpha", "remove", "-alpha", "off", "-filter", "point", "-resize",
            "%d%%" % (scale * 100), ")"]


def icon_row(name, ea, ours, w):
    """EA 1x, ours 1x, EA 2x, ours 2x, side by side under a label."""
    gap = ["(", "-size", "8x8", "xc:" + BG, ")"]
    row = ["("] + tile(ea, 1) + gap + tile(ours, 1) + gap + tile(ea, 2) + gap + tile(ours, 2) + \
        ["-gravity", "south", "-background", BG, "+append", ")"]
    return ["("] + label(name + "   EA | ours (1x) | EA | ours (2x)", w) + row + ["-background", BG, "-append", ")"]


def review(faction, g, man, version=None):
    r = root(faction)
    out_dir = os.path.join(paths.BUILD, faction, "_review")
    os.makedirs(out_dir, exist_ok=True)
    if version is None:
        version = 1
        while os.path.exists(os.path.join(out_dir, "icons_v%d.jpg" % (version + 1))):
            version += 1
    cols = []
    for kind, w in (("portrait", 1180), ("button", 420)):
        rows = [icon_row(n, os.path.join(r, "src", "ea_%s.png" % n), os.path.join(r, "crops", "%s_new.png" % n), w)
                for n, m in sorted(man.items()) if m["kind"] == kind]
        half = (len(rows) + 1) // 2
        for part in (rows[:half], rows[half:]):
            if not part:
                continue
            cols.append(["("] + [x for row in part for x in row + ["(", "-size", "8x10", "xc:" + BG, ")"]] +
                        ["-background", BG, "-append", ")"])
    top = ["("] + [x for c in cols for x in c + ["(", "-size", "24x8", "xc:" + BG, ")"]] + \
        ["-background", BG, "-gravity", "north", "+append", ")"]
    pages = []
    for page in sorted({m["page"] for m in man.values()}):
        pages.append(["("] + label(page + "   EA | ours (2x)", 1040) + ["("] +
                     tile(os.path.join(r, "src", page + ".png"), 2, "#555555") + ["(", "-size", "16x8", "xc:" + BG, ")"] +
                     tile(os.path.join(r, "pages", page + ".png"), 2, "#555555") +
                     ["-background", BG, "+append", ")", "-background", BG, "-append", ")"])
    grid = []
    for k in range(0, len(pages), 3):
        grid.append(["("] + [x for p in pages[k:k + 3] for x in p + ["(", "-size", "24x8", "xc:" + BG, ")"]] +
                    ["-background", BG, "-gravity", "north", "+append", ")"])
    out = os.path.join(out_dir, "icons_v%d.jpg" % version)
    subprocess.check_call([MAGICK] + top + ["(", "-size", "8x40", "xc:" + BG, ")"] +
                          [x for gr in grid for x in gr + ["(", "-size", "8x16", "xc:" + BG, ")"]] +
                          ["-background", BG, "-gravity", "northwest", "-append", "-quality", "92", out])
    return out
