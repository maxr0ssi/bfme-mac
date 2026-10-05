"""The faction palantir's review sheets (build/assets/_review_finish/hud_faction/):

    hud_factions.jpg         per side: the fallback (the installed Good/Evil pack, what any other side
                             sees) and each faction's frame, over the in-game crop at 3024x1964 (the
                             mock-up: buttons, portrait and the bar's numbers are the screenshot's;
                             the button rims are one sheet for every side in EA's movie, so they stay)
                             and a detail of each 2x texture magnified 2x
    hud_factions_single.jpg  every faction's single frame (minimap alone), its 2x texture
    trace.txt                per side and state, the label and texture the frame draws (dry trace)

build/assets/_review_finish/hud_citadel/all.jpg: per faction, a crop of its citadel's close render,
the frame cut from it over the in-game crop at 3024x1964, and the frame before (sheet/prev/, the
mock-ups of the frames installed before the redesign, when kept).
"""
import os
import shutil
import subprocess

from .. import paths
from ..icons.pixels import MAGICK
from . import root
from .factions import factions, froot

OUT = os.path.join(paths.BUILD, "_review_finish", "hud_faction")
CIT = os.path.join(paths.BUILD, "_review_finish", "hud_citadel")
BG = "#1e1e1e"
TW = 600


def tile(src, text, out, crop=None, flat=None, tw=TW):
    cmd = [MAGICK, src, "+repage"]
    if flat:
        cmd += ["-background", flat, "-flatten"]
    if crop:
        cmd += ["-crop", crop, "+repage"]
    cmd += ["-resize", "%dx" % tw, "(", "-size", "%dx30" % tw, "xc:" + BG, "-font", paths.FONT, "-pointsize",
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


def citadels():
    """all.jpg: each faction's citadel beside its frame (and the frame before)."""
    from .swatch import spec
    os.makedirs(CIT, exist_ok=True)
    t = os.path.dirname(froot("sheet", "tiles", "x"))
    rows = []
    for n, f in factions().items():
        render, crop = spec().CITADEL[n]
        src = os.path.join(paths.BUILD, n, "fortress", "renders", render)
        mock = froot("sheet", "mock_%s.png" % n)
        if not (os.path.exists(src) and os.path.exists(mock)):
            continue
        cut = os.path.join(t, n + "_cit_src.png")
        subprocess.check_call([MAGICK, src, "-crop", crop, "+repage",
                               "-resize", "%dx%d" % (900, 660), "-background", "#7a6f5e",
                               "-gravity", "center", "-extent", "%dx%d" % (900, 660), cut])
        row = [tile(cut, "%s: the citadel" % n.capitalize(), os.path.join(t, n + "_cit.png"), tw=900),
               tile(mock, "New: %s (100%%, as at 3024x1964)" % f["what"], os.path.join(t, n + "_new.png"), tw=900)]
        prev = froot("sheet", "prev", "mock_%s.png" % n)
        if os.path.exists(prev):
            row.append(tile(prev, "Previous", os.path.join(t, n + "_prev.png"), tw=900))
        row.append(tile(mock, "New, zoomed 2x: the joint and the top", os.path.join(t, n + "_100.png"),
                        crop="450x310+120+0", tw=900))
        for k, (crop2, what) in enumerate((("380x262+300+0", "the joint"), ("380x262+0+0", "the top left"),
                                            ("380x262+0+250", "the bar's left end"))):
            row.append(tile(froot("paint", "%s_double_2.png" % n), "New: %s (2x texture, magnified 2.4x)" % what,
                            os.path.join(t, "%s_newd%d.png" % (n, k)), crop=crop2, flat="#4a4038", tw=900))
        rows.append(row)
    sock = froot("paint", "sockets_2.png")
    if os.path.exists(sock):
        rows.append([tile(os.path.join(root(), "paint", "libingameimagesmain_1_2.png"),
                          "Portrait button rings before (every side)", os.path.join(t, "sock_prev.png"),
                          crop="262x404+2+250", flat="#4a4038", tw=450),
                     tile(sock, "Now: neutral gunmetal (every side)", os.path.join(t, "sock_new.png"),
                          crop="262x404+2+250", flat="#4a4038", tw=450)])
    return sheet(rows, os.path.join(CIT, "all.jpg"))


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
    out.append(citadels())
    if os.path.exists(froot("trace.txt")):
        shutil.copy(froot("trace.txt"), os.path.join(OUT, "trace.txt"))
        out.append(os.path.join(OUT, "trace.txt"))
    return out
