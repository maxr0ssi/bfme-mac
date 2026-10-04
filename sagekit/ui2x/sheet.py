"""Review sheets: EA's 1x beside our 2x at the same physical size on a 3024x1964 screen
(build/assets/_review_finish/ui2x/*.jpg).

Each image is drawn as the game draws it: EA's page magnified by the measured scale (portraits
1.8x, buttons 1.4x; docs/UI2X.md), ours at half that, both bilinear, over the HUD's dark bronze.
A third column is a 2x detail of each, side by side.
"""
import os
import subprocess
import tempfile

from .. import paths
from ..game import Install
from ..icons import pixels
from ..icons.mapped import images
from . import root

MAGICK = pixels.MAGICK
BG = "#1d1812"
SCALE = {"portrait": 1.8, "button": 1.4}

SHEETS = {
    "portraits": ["UPDwarvenZerkerPortrait", "UPBlackOrcPortrait", "HPAragorn", "UPNoldorWarriorPortrait",
                  "UPRohanSpearmanPortrait", "UPWargPackPortrait"],
    "buttons": ["UCEnt_Stomp", "HSAragornElendil", "HSBalrogWings", "HIAragorn", "SBGood_Heal",
                "UCBuildingLvl2", "UC_GothmogRage", "HSElrondFarSight", "HILegolas", "SBGood_Earthquake"],
}


def out_dir():
    d = os.path.join(paths.BUILD, "_review_finish", "ui2x")
    os.makedirs(d, exist_ok=True)
    return d


def decoded(dds):
    """Our shipped page (its top level) as a PNG, decoded once."""
    png = dds[:-4] + ".dds.png"
    if not os.path.exists(png) or os.path.getmtime(png) < os.path.getmtime(dds):
        pixels.write(png, *pixels.read(dds))
    return png


def pair(ea_png, ours_png, rect, scale, tmp, tag):
    """[EA at physical size, ours at physical size, the 2x detail of both] as files."""
    l, t, r, b = rect
    w, h = r - l, b - t
    pw, ph = round(w * scale), round(h * scale)
    a = os.path.join(tmp, tag + "_a.png")
    o = os.path.join(tmp, tag + "_o.png")
    for src, crop, dst in ((ea_png, "%dx%d+%d+%d" % (w, h, l, t), a),
                           (ours_png, "%dx%d+%d+%d" % (2 * w, 2 * h, 2 * l, 2 * t), o)):
        subprocess.check_call([MAGICK, src, "-crop", crop, "+repage", "-filter", "Triangle", "-resize",
                               "%dx%d!" % (pw, ph), "-background", BG, "-flatten", "-gravity", "center",
                               "-extent", "%dx%d" % (max(pw, 230), ph), dst])
    d = os.path.join(tmp, tag + "_d.png")
    cw, ch = min(pw, 180), min(ph, 180)
    cx, cy = (max(pw, 230) - cw) // 2, (ph - ch) // 3
    subprocess.check_call([MAGICK, "(", a, "-crop", "%dx%d+%d+%d" % (cw, ch, cx, cy), "+repage", "-scale", "200%", ")",
                           "(", o, "-crop", "%dx%d+%d+%d" % (cw, ch, cx, cy), "+repage", "-scale", "200%", ")",
                           "-background", BG, "-splice", "6x0", "+append", d])
    return [a, o, d]


def sheet(name, entries, title, before="EA 1x"):
    """entries: [(label, ea_png, ours_png, rect, kind)] -> build/assets/_review_finish/ui2x/<name>.jpg"""
    with tempfile.TemporaryDirectory() as tmp:
        rows = []
        for k, (label, ea_png, ours_png, rect, kind) in enumerate(entries):
            files = pair(ea_png, ours_png, rect, SCALE[kind], tmp, "r%d" % k)
            row = os.path.join(tmp, "row%d.png" % k)
            labels = ["%s: %s" % (label, before), "ours 2x (same size)", "2x detail: %s | 2x" % before]
            subprocess.check_call([MAGICK, "montage", "-background", BG, "-fill", "#e8d8b0", "-font", paths.FONT, "-pointsize", "16",
                                   "-geometry", "+10+6", "-tile", "3x1"]
                                  + sum([["-label", lab, f] for lab, f in zip(labels, files)], []) + [row])
            rows.append(row)
        out = os.path.join(out_dir(), name + ".jpg")
        subprocess.check_call([MAGICK, "-background", BG, "-fill", "#f0c060", "-font", paths.FONT, "-pointsize", "26",
                               "label:" + title] + rows + ["-gravity", "west", "-append", "-quality", "88", out])
    return out


def entries_for(names, pages_dds):
    g = Install()
    imgs = images(g)
    out = []
    for n in names:
        i = imgs.get(n.lower())
        if i is None or i.page not in pages_dds:
            continue
        ea_png = os.path.join(root("src"), i.page + ".png")
        kind = "portrait" if min(i.width, i.height) >= 100 else "button"
        out.append((i.name, ea_png, decoded(pages_dds[i.page]), i.rect, kind))
    return out


def review(pages_dds, icon_entries=()):
    """The sheets from {page: our dds}, and item 1's [(image, our 1x page png, our 2x png, rect, kind)]."""
    made = []
    for name, names in SHEETS.items():
        e = entries_for(names, pages_dds)
        if e:
            made.append(sheet(name, e, "%s at 3024x1964: EA's 1x and ours at 2x, the same size on screen" % name))
    for k in range(0, len(icon_entries), 8):
        made.append(sheet("icons_%d" % (k // 8 + 1), icon_entries[k:k + 8],
                          "our building icons at 3024x1964: the 1x installed today and the 2x, the same size",
                          before="ours 1x"))
    return made


def tooltip_sheet():
    """The help box assembled from its pieces (top, sides, bottom; the glow set beside), EA's 1x and
    ours 2x at the size a 3024x1964 screen draws them (2.4x of EA's pixels)."""
    src, ours = root("tips", "src"), root("tips", "2x")
    with tempfile.TemporaryDirectory() as tmp:
        cols = []
        for label, d, k in (("EA 1x", src, 1), ("ours 2x", ours, 2)):
            for glow, ids in (("frame", (2, 6, 5, 10)), ("glow", (1, 8, 7, 9))):
                top, left, right, bottom = (os.path.join(d, "%d.png" % i) for i in ids)
                box = os.path.join(tmp, "%s_%s.png" % (k, glow))
                w, h = 405 * k, (35 + 78 + 27) * k
                subprocess.check_call([MAGICK, "-size", "%dx%d" % (w, h), "xc:#000000a0",
                                       "(", top, "-crop", "%dx%d+0+0" % (405 * k, 35 * k), ")", "-geometry", "+0+0",
                                       "-composite", "(", left, "-crop", "%dx%d+0+0" % (30 * k, 78 * k), ")",
                                       "-geometry", "+0+%d" % (35 * k), "-composite",
                                       "(", right, "-crop", "%dx%d+0+0" % (34 * k, 78 * k), ")",
                                       "-geometry", "+%d+%d" % ((405 - 34) * k, 35 * k), "-composite",
                                       "(", bottom, "-crop", "%dx%d+0+0" % (405 * k, 27 * k), ")",
                                       "-geometry", "+0+%d" % (113 * k), "-composite",
                                       "-filter", "Triangle", "-resize", "%dx%d!" % (round(405 * 2.4), round(140 * 2.4)),
                                       "-background", "#3a3026", "-flatten", box])
                cols.append(("%s %s" % (label, glow), box))
            for glow, tid in (("frame", 2), ("glow", 1)):
                det = os.path.join(tmp, "%s_%s_det.png" % (k, glow))
                subprocess.check_call([MAGICK, os.path.join(d, "%d.png" % tid), "-crop",
                                       "%dx%d+%d+0" % (120 * k, 35 * k, 140 * k), "+repage", "-filter", "Triangle",
                                       "-resize", "%dx%d!" % (round(120 * 4.8), round(35 * 4.8)),
                                       "-background", "#3a3026", "-flatten", det])
                cols.append(("%s %s, detail 2x" % (label, glow), det))
        cols = cols[0:1] + cols[2:3] + cols[1:2] + cols[3:4] + cols[4:5] + cols[6:7] + cols[5:6] + cols[7:8]
        out = os.path.join(out_dir(), "tooltip.jpg")
        subprocess.check_call([MAGICK, "montage", "-background", BG, "-fill", "#e8d8b0", "-font", paths.FONT,
                               "-pointsize", "18", "-geometry", "+10+8", "-tile", "2x"]
                              + sum([["-label", lab, f] for lab, f in cols], []) + [out])
    return out
