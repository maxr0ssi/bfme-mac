"""The fire reduction's review sheets (Max, 2026-10-05; docs/ART.md "Fire budget"): per faction, every
building with our fire before or after, before and after, at the in-game camera (a 1:1 crop of the build's
`ingame` render, healthy), the live particles of our fire on each tile.

    python3 -m sagekit.fire_grid [--before <snapshot.json>] [faction ...]
        build/assets/_review_finish/fire_reduce/<faction>.jpg; the snapshot is sagekit/fire_review.py's
        (`--snapshot`), taken before the change (default: fire_reduce/before.json)

The particles are drawn by sagekit/paint/fire_composite.py (an approximation of the game's sprites,
no wind); the in-game look is Max's check.
"""
import json
import os
import subprocess
import sys

from . import paths
from .fire_review import header_rows, raw_rgb, snapshot

OUT = os.path.join(paths.BUILD, "_review_finish", "fire_reduce")
WORK = os.path.join(OUT, "work")
FACTIONS = ("dwarves", "elves", "goblins", "isengard", "mordor", "angmar", "neutral")
CROP = (640, 460)                       # of the 1600x1100 in-game render: the building at the game's scale
PER_ROW = 3                             # buildings (before | after pairs) per row


def live(snap, bid):
    return sum(snap["live"][s] for _, k in snap["buildings"].get(bid, []) for s in snap["kinds"][k])


def tiles(bid, before, after, g, cache):
    from . import registry
    from .fire_checks import views as all_views
    from .fx.preview import params
    from .workspace import Workspace
    b = registry.load(bid)
    ws = Workspace(b)
    bg_png = os.path.join(ws.path("renders"), "new_ingame.png")
    if not os.path.exists(bg_png):
        return []
    work = os.path.join(WORK, bid.replace("/", "_"))
    os.makedirs(work, exist_ok=True)
    bg = os.path.join(work, "ingame.rgb")
    size = raw_rgb(bg_png, bg)
    view = list(all_views(b, ws, g)["ingame"])
    out = []
    for side, snap in (("before", before), ("after", after)):
        ems = [dict(pos=xyz, systems=[params(header_rows(snap["systems"][s]), g, cache) for s in snap["kinds"][kind]])
               for xyz, kind in snap["buildings"].get(bid, [])]
        out.append(dict(bg=bg, size=size, view=view, emitters=ems, seed=11, out=os.path.join(work, "%s.ppm" % side)))
    return out


def label(ppm, text, colour):
    png = ppm[:-4] + ".png"
    subprocess.check_call(["magick", ppm, "-gravity", "center", "-crop", "%dx%d+0+0" % CROP, "+repage",
                           "-font", paths.FONT, "-gravity", "NorthWest", "-fill", colour, "-undercolor", "#000b",
                           "-pointsize", "17", "-annotate", "+6+6", " %s " % text, png])
    return png


def faction_sheet(faction, ids, before, after):
    from .fire_budget import IDENTITY, budget
    cells = []
    for bid in ids:
        work = os.path.join(WORK, bid.replace("/", "_"))
        nb, na = live(before, bid), live(after, bid)
        kb, ka = len(before["buildings"].get(bid, [])), len(after["buildings"].get(bid, []))
        tag = "identity, budget %d" % budget(bid) if bid in IDENTITY else "budget %d" % budget(bid)
        left = label(os.path.join(work, "before.ppm"), "%s  before: %.1f live, %d points" % (bid, nb, kb), "#f2ead8")
        right = label(os.path.join(work, "after.ppm"), "after: %.1f live, %d points (%s)" % (na, ka, tag),
                      "#f0c870" if bid in IDENTITY else "#a8e0a0")
        cell = os.path.join(work, "cell.png")
        subprocess.check_call(["magick", left, "-size", "4x%d" % CROP[1], "xc:#141414", right, "+append", cell])
        cells.append(cell)
    gap = ["-size", "%dx%d" % (24, CROP[1]), "xc:#2a2a2a"]
    rows = []
    for i in range(0, len(cells), PER_ROW):
        row = os.path.join(WORK, "%s_row%d.png" % (faction, i // PER_ROW))
        parts = sum(([c] + gap for c in cells[i:i + PER_ROW]), [])[:-len(gap)]
        subprocess.check_call(["magick"] + parts + ["-background", "#141414", "+append", row])
        rows.append(row)
    tb = sum(live(before, b) for b in ids)
    ta = sum(live(after, b) for b in ids)
    width = PER_ROW * (2 * CROP[0] + 4) + (PER_ROW - 1) * 24
    head = os.path.join(WORK, "%s_head.png" % faction)
    subprocess.check_call(["magick", "-size", "%dx52" % width, "xc:#141414", "-font", paths.FONT, "-fill", "#f0c870",
                           "-pointsize", "26", "-gravity", "West", "-annotate", "+10+0",
                           "%s: our fire on %d buildings, %.0f -> %.0f live particles (each building once). Each pair: "
                           "before | after at the in-game camera (1:1 crop, healthy). Gold: identity (at most 20); "
                           "green: the rest (at most 6). Particles approximated, no wind." % (
                               faction, len(ids), tb, ta), head])
    dest = os.path.join(OUT, "%s.jpg" % faction)
    subprocess.check_call(["magick", head] + rows + ["-background", "#141414", "-gravity", "NorthWest", "-append", "-quality", "86", dest])
    print("  " + os.path.relpath(dest, paths.REPO))


def main(argv):
    from .game import Install
    before_path = argv[argv.index("--before") + 1] if "--before" in argv else os.path.join(OUT, "before.json")
    factions = [a for a in argv if a in FACTIONS] or list(FACTIONS)
    with open(before_path) as fh:
        before = json.load(fh)
    after = snapshot()
    g, cache = Install(), {}
    os.makedirs(WORK, exist_ok=True)
    for faction in factions:
        ids = sorted({b for b in list(before["buildings"]) + list(after["buildings"]) if b.split("/")[0] == faction},
                     key=lambda b: (-live(before, b), b))
        job = []
        for bid in ids:
            job += tiles(bid, before, after, g, cache)
        if not job:
            continue
        path = os.path.join(WORK, "%s_job.json" % faction)
        with open(path, "w") as fh:
            json.dump(dict(tiles=job), fh)
        subprocess.check_call([paths.blender_python(), "-m", "sagekit.paint.fire_composite", path], cwd=paths.REPO)
        faction_sheet(faction, [b for b in ids if os.path.exists(os.path.join(WORK, b.replace("/", "_"), "after.ppm"))],
                      before, after)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
