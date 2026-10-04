"""The HUD review sheets (build/assets/_review_finish/hud/):

    hud_frames.jpg    each palantir frame, EA's page beside ours (both at 2x), and a detail at 4x
    hud_atlases.jpg   the glass/buttons sheet and the portrait-ring sheet, EA's beside ours, and details
    hud_mockup.jpg    the bottom-left of the screen at 3024x1964 (Retina on) and 1512x982 (Retina off,
                      shown at the same physical size), EA's frame and ours, Good and Evil

The mock-ups draw the frame over a screenshot of the game (build/assets/_hud/backdrop.png: the
bottom-left 900x620 of a 3024x1964 match, kept out of git, EA's art): where the screenshot shows
something drawn above the frame (the buttons, the portrait) it is kept; only the frame changes.
"""
import json
import os
import subprocess

from .. import paths
from ..icons.pixels import MAGICK
from . import root
from .build import specs

OUT = os.path.join(paths.BUILD, "_review_finish", "hud")
BG = "#262626"
BACKDROP = "backdrop.png"
# where the game draws the double frame on the backdrop (3024x1964 screen, the crop's pixels): texel
# (u, v) at (OX + u * SX, OY + v * SY); measured by matching EA's frame on the screenshot
# (correlation 0.65 on the metal; SX/SY = 0.87: the 2.02 patch squeezes the HUD on a 16:10 screen)
PLACE = (2.24, 2.565, 0.0, -34.5)
# what the game draws over the frame on that screenshot, kept from it: the minimap's three buttons,
# the six round buttons round the portrait (x, y, r), and the resource bar's numbers (l, t, r, b)
ABOVE = dict(circles=[(188, 85, 41), (287, 70, 52), (380, 85, 41), (638, 133, 41), (742, 180, 43),
                      (800, 290, 42), (795, 410, 45), (725, 510, 45), (622, 540, 45)],
             rects=[(88, 505, 482, 552)])
ZOOM = {"palantirexport_17": (130, 10, 340, 140), "palantirexport_11": (130, 10, 340, 140),
        "palantirexport_20": (20, 0, 230, 130), "palantirexport_14": (20, 0, 230, 130),
        "palantir_1": (496, 0, 776, 140), "libingameimagesmain_1": (0, 120, 140, 330)}


def p(*parts):
    path = os.path.join(root(), "sheet", *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def label(text, w):
    return ["(", "-size", "%dx26" % w, "xc:" + BG, "-font", paths.FONT, "-pointsize", "15", "-fill", "#e8e0cc",
            "-gravity", "west", "-annotate", "+6+0", text, ")"]


def gap(w, h):
    return ["(", "-size", "%dx%d" % (w, h), "xc:" + BG, ")"]


def pair(a, b, title, w, scale=None):
    """[a | b] under a title; scale: resize both (percent) for the sheet."""
    rs = ["-resize", "%d%%" % scale] if scale else []
    row = ["(", "(", a] + rs + [")"] + gap(12, 8) + ["(", b] + rs + [")", "-background", BG, "+append", ")"]
    return ["("] + label(title, w) + row + ["-background", BG, "-append", ")"]


def render(job):
    path = p("job.json")
    with open(path, "w") as fh:
        json.dump(job, fh, indent=1)
    res = subprocess.run([paths.blender_python(), "-m", "sagekit.paint.hudsheet", path], cwd=paths.REPO,
                         env=dict(os.environ, PYTHONPATH=paths.REPO), capture_output=True, text=True)
    if res.returncode:
        raise SystemExit("review panels failed:\n" + res.stderr[-3000:])


def mockups():
    back = os.path.join(root(), BACKDROP)
    if not os.path.exists(back):
        return []
    tex = {k: (os.path.join(root(), "src", k + ".png"), os.path.join(root(), "paint", k + "_2.png"))
           for k in ("palantirexport_17", "palantirexport_11")}
    out = []
    for key, side in (("palantirexport_17", "good"), ("palantirexport_11", "evil")):
        for res, k in (("3024", 1.0), ("1512", 0.5)):
            if side == "evil" and res == "1512":
                continue
            for who, f in (("ea", 1), ("ours", 2)):
                out.append(dict(backdrop=back, scale=k, out=p("mock_%s_%s_%s.png" % (side, res, who)),
                                above=ABOVE,
                                layers=[dict(texture=tex[key][0 if who == "ea" else 1], texels=f,
                                             transform=list(PLACE))]))
    return out


def review():
    os.makedirs(OUT, exist_ok=True)
    pages = []
    for mv, tid, spec, key, member in specs():
        pages.append(dict(name=key, ea=os.path.join(root(), "src", key + ".png"),
                          ours=os.path.join(root(), "paint", key + "_2.png"), zoom=ZOOM[key],
                          out_ea=p(key + "_ea2.png"), out_ours=p(key + "_ours2.png"),
                          zoom_ea=p(key + "_zea.png"), zoom_ours=p(key + "_zours.png")))
    mocks = mockups()
    render(dict(pages=pages, mockups=mocks))
    sheets = []
    frames = [x for x in pages if x["name"].startswith("palantirexport")]
    atlases = [x for x in pages if not x["name"].startswith("palantirexport")]
    what = {key: spec["what"] for _, _, spec, key, _ in specs()}
    for name, group, scale in (("hud_frames.jpg", frames, 100), ("hud_atlases.jpg", atlases, 50)):
        rows = []
        for x in group:
            rows += pair(x["out_ea"], x["out_ours"], "%s - %s   EA | ours (2x)" % (x["name"], what[x["name"]]),
                         2200, scale) + gap(8, 6)
            rows += pair(x["zoom_ea"], x["zoom_ours"], "detail at 4x EA's pixels: EA's 1x magnified | our 2x",
                         2200) + gap(8, 22)
        out = os.path.join(OUT, name)
        subprocess.check_call([MAGICK] + rows + ["-background", BG, "-gravity", "northwest", "-append",
                                                 "-quality", "92", out])
        sheets.append(out)
    if mocks:
        rows = []
        for side, title in (("good", "Good"), ("evil", "Evil")):
            rows += pair(p("mock_%s_3024_ea.png" % side), p("mock_%s_3024_ours.png" % side),
                         "%s, 3024x1964 (Retina on): EA | ours (mock-up over a screenshot; buttons and portrait "
                         "are the screenshot's)" % title, 1900) + gap(8, 18)
            if side == "good":
                rows += ["("] + label("Good, 1512x982 (Retina off), shown at the same physical size: EA | ours",
                                      1900) + ["(", "(", p("mock_good_1512_ea.png"), "-filter", "point", "-resize",
                                               "200%", ")"] + gap(12, 8) + \
                    ["(", p("mock_good_1512_ours.png"), "-filter", "point", "-resize", "200%", ")",
                     "-background", BG, "+append", ")", "-background", BG, "-append", ")"] + gap(8, 18)
        out = os.path.join(OUT, "hud_mockup.jpg")
        subprocess.check_call([MAGICK] + rows + ["-background", BG, "-gravity", "northwest", "-append",
                                                 "-quality", "92", out])
        sheets.append(out)
    return sheets
