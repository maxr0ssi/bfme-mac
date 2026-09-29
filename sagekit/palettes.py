"""Palette options for the owner's pick: `python3 -m sagekit palettes <faction> [--only A,B]`.

EA's citadel (the style's `palette_building`) rendered as it is and recoloured with each palette
of the style's `palettes`, side by side and labelled: build/assets/<faction>/_palettes/
palette_options.jpg. Rows are the style's `palette_views` (views of that recipe, e.g. the RTS
view and a close crop of the keep), columns EA's and one per palette, with swatches of each
palette's ramps (`swatches`) under its column.

Recolour only: EA's model and painted detail, no design. Each palette goes through the style's
own flat-sheet layers (`sheet_layers()`, the `sagekit sheets` path; the building paint's first
layer on EA's faces), on the sheet upscaled 4x when Real-ESRGAN is there, so what the options
show is the colour a build would give EA's faces before occlusion and edge wear.

The recolour runs on Blender's Python (numpy): sagekit/paint/palette.py.
"""
import os
import subprocess

from . import paths

RES = (1200, 825)                           # each render: the size the recipe's views are framed for (preview.py)

def ramp_at(stops, x):
    """A palette ramp's colour at x (plain Python: the host has no numpy)."""
    if x <= stops[0][0]:
        return stops[0][1]
    for (x0, c0), (x1, c1) in zip(stops, stops[1:]):
        if x <= x1:
            f = (x - x0) / (x1 - x0)
            return tuple(a + (b - a) * f for a, b in zip(c0, c1))
    return stops[-1][1]


def hexcol(rgb):
    return "#%02x%02x%02x" % tuple(int(round(255 * max(0.0, min(1.0, c)))) for c in rgb)


def swatches(style, key, dest, width):
    """A row of labelled colour chips for one palette (style.swatches: label, ramp, position)."""
    from .board import magick
    pal = style.palettes[key] if key else None
    items = style.swatches if pal else ()
    cmd = ["-size", "%dx84" % width, "xc:#1c1d21", "-font", paths.FONT, "-pointsize", "19"]
    if not items:
        cmd += ["-fill", "#a8a49c", "-annotate", "+10+30", "EA's own sheet, as it ships"]
    w = (width - 10) // max(len(items), 1)
    for i, (label, name, x) in enumerate(items):
        x0 = 5 + i * w
        cmd += ["-fill", hexcol(ramp_at(pal.ramps[name], x)), "-draw", "rectangle %d,4 %d,48" % (x0, x0 + w - 4),
                "-fill", "#d8d4cc", "-annotate", "+%d+74" % (x0 + 2), label]
    magick(cmd + [dest])


def run(faction, only=None):
    from . import registry
    from .__main__ import _style
    from .board import extract, hidden_meshes, magick, render, root
    from .game import Install
    from .pipeline import REALESRGAN
    style = _style(faction)
    if not style.palettes:
        print("%s's style declares no palettes (Style.palettes)" % faction)
        return 1
    keys = [k for k in style.palettes if not only or k in only.split(",")]
    b = registry.load("%s/%s" % (faction, style.palette_building))
    g = Install()
    out = root(faction, "_palettes")
    path, skl, texmap = extract(g, b.source, os.path.join(out, "ea"))
    hidden = hidden_meshes(open(path, "rb").read())
    views = {v: b.views[v] for v in style.palette_views}
    sheet = b.sheet.lower()
    shots = [{"model": path, "skeletons": skl, "texmap": texmap, "hidden": hidden, "views": views,
              "out": os.path.join(out, "ea", "shot_"), "expect": list(views)}]
    py = paths.blender_python()
    for d in ["ea"] + keys:                                 # views or sheets may have changed: shoot again
        for f in os.listdir(os.path.join(out, d)) if os.path.isdir(os.path.join(out, d)) else ():
            if f.startswith("shot_"):
                os.remove(os.path.join(out, d, f))
    for k in keys:
        os.makedirs(os.path.join(out, k), exist_ok=True)
        png = os.path.join(out, k, os.path.splitext(sheet)[0] + ".png")
        print("[%s] recolour %s" % (k, b.sheet), flush=True)
        r = subprocess.run([py, "-m", "sagekit.paint.palette", faction, k, texmap[sheet], png, REALESRGAN],
                           capture_output=True, text=True, cwd=paths.REPO, env=dict(os.environ, PYTHONPATH=paths.REPO))
        if r.returncode:
            raise SystemExit("recolour %s failed\n%s" % (k, r.stderr[-2000:]))
        shots.append(dict(shots[0], texmap=dict(texmap, **{sheet: png}), out=os.path.join(out, k, "shot_")))
    print("render %d x %d views" % (len(shots), len(views)), flush=True)
    render(shots, os.path.join(out, "shots.json"), res=RES, samples=48)
    cols = []
    for k, shot in zip([None] + keys, shots):
        head = os.path.join(out, "_head_%s.png" % (k or "ea"))
        title = "%s  %s" % (k, style.palettes[k].name.split(" ", 1)[1]) if k else "EA's %s as it is" % b.source
        note = style.palette_notes.get(k, "") if k else "Teal-grey metal throughout"
        magick(["-size", "%dx62" % RES[0], "xc:#1c1d21", "-font", paths.FONT, "-fill", "#f2ede2", "-pointsize", "28",
                "-annotate", "+8+30", title, "-fill", "#a8a49c", "-pointsize", "16", "-annotate", "+8+54", note, head])
        sw = os.path.join(out, "_sw_%s.png" % (k or "ea"))
        swatches(style, k, sw, RES[0])
        col = os.path.join(out, "_col_%s.png" % (k or "ea"))
        magick([head] + [shot["out"] + v + ".png" for v in views] + [sw, "-background", "#1c1d21", "-splice", "0x0",
                                                                     "-append", col])
        cols.append(col)
    dest = os.path.join(out, "palette_options.jpg")
    top = os.path.join(out, "_title.png")
    magick(["-size", "%dx86" % (RES[0] * len(cols) + 12 * (len(cols) - 1)), "xc:#1c1d21", "-font", paths.FONT,
            "-fill", "#f2ede2", "-pointsize", "34", "-annotate", "+8+42",
            "%s: palette options on EA's citadel (%s), recolour only" % (faction.capitalize(), b.source),
            "-fill", "#a8a49c", "-pointsize", "17", "-annotate", "+8+74",
            "Rows: %s. Same model and sheet; only the palette differs (assets/%s/style.py PALETTES). "
            "Cloth is the player's colour in game." % (", ".join(views), faction), top])
    row = os.path.join(out, "_row.png")
    magick(cols[:1] + sum((["(", "-size", "12x10", "xc:#1c1d21", ")", c] for c in cols[1:]), []) + ["+append", row])
    magick(["-background", "#1c1d21", top, row, "-append", "-bordercolor", "#1c1d21", "-border", "16",
            "-quality", "90", dest])
    for f in cols + [top, row] + [os.path.join(out, x) for x in os.listdir(out) if x.startswith(("_head_", "_sw_"))]:
        os.remove(f)
    print(os.path.relpath(dest, paths.REPO))
    return 0

