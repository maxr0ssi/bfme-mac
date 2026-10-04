#!/usr/bin/env python3
"""Review renders of the heroes pack: EA's hero beside ours, close up and at the RTS camera, posed
in EA's animations (one Blender process: sagekit/blender/cah_pose.py, the shared slot), and the
review sheet build/assets/_review_finish/heroes/*.jpg.

    python3 -m assets.heroes.render [captain|aragorn|gamling|roster ...]
"""
import json
import subprocess
import sys
from pathlib import Path

from sagekit import paths

SCRIPT = Path(paths.REPO) / "sagekit" / "blender" / "cah_pose.py"
REVIEW = Path(paths.REPO) / "build" / "assets" / "_review_finish" / "heroes"
ERE_BLUE, RED = (44, 80, 168), (178, 34, 30)


def job(name, label, model, skeleton, anim, show, textures, out_dir, masks=None, colours=None, frame=0, **view):
    return dict(name=name, label=label, model=str(model), skeleton=str(skeleton), anim=str(anim), frame=frame, show=list(show),
                textures=textures, masks=masks or {}, colours=colours, out=str(Path(out_dir) / (name + ".png")),
                samples=view.pop("samples", 24), size=view.pop("size", (420, 520)), **view)


def close(part=("HELMET", "HEAD"), dist=17.0, **kw):
    """A head-and-shoulders shot at a fixed distance on the given meshes (EA's and ours alike)."""
    return dict(dict(focus="part", part=list(part), dist=dist, size=(420, 460), elevation=8, azimuth=24), **kw)


def full(**kw):
    return dict(dict(size=(420, 560), elevation=12, azimuth=28, scale=2.0), **kw)


def rts(**kw):
    return dict(dict(size=(300, 300), elevation=48, azimuth=-36, scale=3.4), **kw)


def run(jobs, out_dir):
    from sagekit.pipeline import blender_slot, game_running
    if game_running():
        raise SystemExit("The game is running; close it before rendering.")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = out_dir / "jobs.json"
    spec.write_text(json.dumps(jobs, indent=1))
    with blender_slot(), (out_dir / "blender.log").open("w") as log:
        subprocess.run([paths.BLENDER, "-b", "--python-exit-code", "1", "--python", str(SCRIPT), "--", str(spec)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    for j in jobs:
        subprocess.run(["magick", j["out"], "-gravity", "NorthWest", "-font", paths.FONT, "-pointsize", "17", "-fill", "white",
                        "-undercolor", "#171b21cc", "-annotate", "+8+8", " %s " % j["label"], j["out"]], check=True)
    return [j["out"] for j in jobs]


def sheet(rows, out, title):
    """Rows of labelled images (same zoom per row) under a title, as one JPEG."""
    made = []
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    for k, row in enumerate(rows):
        p = Path(out).with_name("_row%d.png" % k)
        subprocess.run(["magick", *row, "-background", "#171b21", "-gravity", "North", "+append", str(p)], check=True)
        made.append(str(p))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["magick", "-background", "#171b21", "-fill", "white", "-font", paths.FONT, "-pointsize", "26",
                    "label: %s " % title, *made, "-gravity", "West", "-append", "-quality", "88", str(out)], check=True)
    for p in made:
        Path(p).unlink()
    return out


def main(argv):
    which = argv or ["captain", "aragorn", "unlocked", "roster"]
    for w in which:
        mod = __import__("assets.heroes.%s.review" % w if w in ("captain", "aragorn") else "assets.heroes.review_%s" % w,
                         fromlist=["review"])
        print(mod.review())


if __name__ == "__main__":
    main(sys.argv[1:])
