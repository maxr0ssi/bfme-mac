"""The faction palantir's review sheets (build/assets/_review_finish/hud_faction/):

    hud_factions.jpg         per side: the fallback (the installed Good/Evil pack, what any other side
                             sees) and each faction's frame, over the in-game crop at 3024x1964 (the
                             mock-up: buttons, portrait and the bar's numbers are the screenshot's;
                             the button rims are one sheet for every side in EA's movie, so they stay)
                             and a detail of each 2x texture magnified 2x
    hud_factions_single.jpg  every faction's single frame (minimap alone), its 2x texture
    trace.txt                per side and state, the label and texture the frame draws (dry trace)
"""
import os
import shutil
import subprocess

from .. import paths
from ..icons.pixels import MAGICK
from . import root
from .factions import factions, froot

OUT = os.path.join(paths.BUILD, "_review_finish", "hud_faction")
BG = "#1e1e1e"
TW = 600


def tile(src, text, out, crop=None, flat=None):
    cmd = [MAGICK, src]
    if flat:
        cmd += ["-background", flat, "-flatten"]
    if crop:
        cmd += ["-crop", crop, "+repage"]
    cmd += ["-resize", "%dx" % TW, "(", "-size", "%dx30" % TW, "xc:" + BG, "-font", paths.FONT, "-pointsize",
            "17", "-fill", "#eadfc8", "-gravity", "west", "-annotate", "+6+0", text, ")", "+swap",
            "-background", BG, "-append", "-bordercolor", BG, "-border", "5", out]
    subprocess.check_call(cmd)
    return out


def sheet(rows, out):
    args = [MAGICK]
    for r in rows:
        args += ["("] + r + ["-background", BG, "+append", ")"]
    subprocess.check_call(args + ["-background", BG, "-gravity", "northwest", "-append", "-quality", "90", out])
    return out


def review():
    os.makedirs(OUT, exist_ok=True)
    t = os.path.dirname(froot("sheet", "tiles", "x"))
    os.makedirs(t, exist_ok=True)
    looks = factions()
    rows, singles = [], []
    for side, page in (("good", "palantirexport_17"), ("evil", "palantirexport_11")):
        fb = os.path.join(root(), "sheet", "mock_%s_3024_ours.png" % side)
        if not os.path.exists(fb):
            continue
        names = [n for n, f in looks.items() if f["side"] == side]
        ts = [tile(fb, "Fallback: the installed %s pack (any other side)" % side.capitalize(),
                   os.path.join(t, "fb_%s.png" % side))]
        ds = [tile(os.path.join(root(), "paint", page + "_2.png"), "Fallback: detail (2x texture, magnified 2x)",
                   os.path.join(t, "fbd_%s.png" % side), crop="300x180+400+10", flat="#4a4038")]
        for n in names:
            f = looks[n]
            mock = froot("sheet", "mock_%s.png" % n)
            sides = "/".join(f["sides"]).replace("Wild", "Wild (Goblins)")
            ts.append(tile(mock, "%s: %s" % (sides, f["what"]), os.path.join(t, n + ".png")))
            ds.append(tile(froot("paint", "%s_double_2.png" % n), "%s: detail (2x texture, magnified 2x)" % sides,
                           os.path.join(t, n + "_d.png"), crop="300x180+400+10", flat="#4a4038"))
            singles.append(tile(froot("paint", "%s_single_2.png" % n), "%s: single (minimap alone), 2x" % sides,
                                os.path.join(t, n + "_s.png"), flat="#4a4038"))
        rows += [ts, ds]
    out = [sheet(rows, os.path.join(OUT, "hud_factions.jpg"))]
    out.append(sheet([singles[:4], singles[4:]], os.path.join(OUT, "hud_factions_single.jpg")))
    if os.path.exists(froot("trace.txt")):
        shutil.copy(froot("trace.txt"), os.path.join(OUT, "trace.txt"))
        out.append(os.path.join(OUT, "trace.txt"))
    return out
