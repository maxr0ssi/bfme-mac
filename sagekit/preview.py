"""A shape preview in about a minute: `python3 -m sagekit preview <faction>/<building>`.

For iterating on silhouette and detail on the Mac; the full-quality builds (bake, paint,
lifecycle, render) are for the finished recipe (`build`, or the A100 offload: docs/OFFLOAD.md).

    extract    only when the building has never been extracted (or --extract)
    geometry   the pipeline's own geometry job (blender/jobs.py job_geometry), writing its scene and
               house cloth under preview/ instead of work/: a full build's intermediates stay as
               they were, and what the preview shows is exactly what `build` would make
    preview    EA's model and ours with EEVEE in flat atlas-tag colours (blender/preview.py);
               the checks that need no bake (triangle budget, footprint, height growth, winding,
               sky-facing backs, zero-area faces, UVs, closed solids)

Writes build/assets/<faction>/<building>/preview/compare_<view>.png. Blender runs share the
build slots (SAGEKIT_BLENDER_SLOTS) and wait while the game runs, as every build step does.
"""
import json
import os
import time

from . import paths, registry
from .pipeline import Extract, Geometry, Pipeline, StepFailed

LINES = ("TRIS after", "Z growth", "house colour", "CLEARED")


def needs_extract(ws, b):
    want = [ws.source_model, ws.reference_model, ws.path("work", "derived.json")]
    return not all(os.path.exists(p) for p in want)


def run(building_id, views=None, res="1200x825", extract=False, force=False):
    """0 when every check passed, 1 when one failed, 2 when a step failed."""
    t0 = time.time()
    b = registry.load(building_id)
    p = Pipeline(b, force)
    ws, step = p.ws, Geometry(p)
    out = ws.path("preview")
    os.makedirs(out, exist_ok=True)
    views = views or ",".join(b.views or ("rts", "close", "ingame"))
    stage, cloth = os.path.join(out, "stage_geometry.blend"), os.path.join(out, "house_cloth.json")
    try:
        if extract or needs_extract(ws, b):
            print("[%s] extract" % b.id, flush=True)
            Extract(p).run()
        t = time.time()
        print("[%s] geometry" % b.id, flush=True)
        log = step.blender("geometry", log_as="preview_geometry", stage=stage, cloth=cloth)
        print("\n".join("  " + x for x in log.splitlines() if x.startswith(LINES)))
        print("  (%.0fs)" % (time.time() - t), flush=True)
        t = time.time()
        print("[%s] preview" % b.id, flush=True)
        log = step.blender("preview", blend=stage, log_as="preview_render", prefix=out + os.sep, views=views,
                           res=res, cloth=cloth)
    except StepFailed as e:
        print("FAILED:", e)
        return 2
    report = [x for x in log.splitlines() if x.startswith(("PASS", "FAIL", "---", "PREVIEW TIMES")) or "checks passed" in x]
    print("\n".join("  " + x for x in report))
    with open(os.path.join(out, "checks.txt"), "w") as fh:
        fh.write("\n".join(report) + "\n")
    compose(b, out, views.split(","), res)
    print("  (%.0fs)" % (time.time() - t))
    print("preview of %s in %.0fs%s" % (b.id, time.time() - t0, "" if all_passed(report) else " - SOME CHECKS FAILED"))
    return 0 if all_passed(report) else 1


def all_passed(report):
    return any("checks passed" in x for x in report) and not any(x.startswith("FAIL") for x in report)


def hexcol(rgb):
    return "#%02x%02x%02x" % tuple(int(round(255 * max(0.0, min(1.0, c)))) for c in rgb)


def compose(b, out, views, res):
    """compare_<view>.png: EA's model | ours, labelled, over a legend of the new faces' tags."""
    step = Geometry.__new__(Geometry)           # only its tool(): no pipeline needed
    font = paths.FONT
    w, h = (int(x) for x in res.split("x"))
    legend = os.path.join(out, "_legend.png")
    items = json.load(open(os.path.join(out, "legend.json")))
    cmd = ["magick", "-size", "%dx%d" % (2 * w + 10, 20 + 34 * ((len(items) + 5) // 6)), "xc:#141414", "-font", font,
           "-pointsize", "20"]
    for i, (tag, n, rgb) in enumerate(items):
        x, y = 16 + (i % 6) * ((2 * w + 10) // 6), 12 + 34 * (i // 6)
        cmd += ["-fill", hexcol(rgb), "-draw", "rectangle %d,%d %d,%d" % (x, y, x + 24, y + 24),
                "-fill", "#e8e2d4", "-annotate", "+%d+%d" % (x + 34, y + 20), "%s (%d)" % (tag, n)]
    step.tool(cmd + [legend])
    for v in views:
        labelled = []
        for who, text in (("orig", "EA's original"), ("new", "%s - shape preview" % b.id)):
            src, dst = os.path.join(out, "%s_%s.png" % (who, v)), os.path.join(out, "_%s_%s.png" % (who, v))
            step.tool(["magick", src, "-font", font, "-gravity", "NorthWest", "-fill", "#f2ead8", "-undercolor", "#0008",
                       "-pointsize", "28", "-annotate", "+14+12", " %s " % text, dst])
            labelled.append(dst)
        dest = os.path.join(out, "compare_%s.png" % v)
        step.tool(["magick", "(", labelled[0], "-size", "10x%d" % h, "xc:#141414", labelled[1], "+append", ")",
                   legend, "-append", dest])
        for f in labelled:
            os.remove(f)
        print("  " + os.path.relpath(dest, paths.REPO))
    os.remove(legend)
