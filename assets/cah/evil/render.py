#!/usr/bin/env python3
"""An Evil class's overview: EA's parts beside ours at the same zoom (head shots per model), kits
full length, and the in-game models at the RTS camera, for every subclass (the kit's render.py
draws one model per row; these classes span several skeletons). One Blender process (the shared
slot), lean samples; the kit's cah_pose.py does the Blender side.

    python3 -m assets.cah.evil.render <class> [--samples N] [--only heads,kits,game]
        -> build/assets/cah/<class>/renders/overview.png

design.RENDER: "body" {model: body mesh}, "colours", "anims" {skeleton: animation}, and the rows
"heads" [(model, label, [meshes], ea?)], "kits" [(model, label, [meshes], ea?)], "game" likewise.
"""
import importlib
import json
import subprocess
import sys

from sagekit import paths

from ..kit.models import folder
from ..kit.render import SCRIPT, textures


def jobs(spec, samples, only):
    R = spec.RENDER
    d, src, work = folder(spec)
    shipped = {ea.lower(): work / (ours.lower() + ".w3d") for ea, ours in spec.MODELS.items()}
    tex, masks = textures(spec, list(shipped.values()) + [src / (m + ".w3d") for m in shipped])
    out = d / "renders"
    out.mkdir(parents=True, exist_ok=True)
    from .anatomy import REGISTRY, of

    def job(name, model, ea, show, label, **kw):
        skel = spec.SKELETONS[model]
        return dict(name=name, label=label, model=str(src / (model + ".w3d") if ea else shipped[model]),
                    skeleton=str(src / (skel + ".w3d")), anim=str(src / (R["anims"][skel] + ".w3d")), frame=0,
                    show=[R["body"][model]] + show, textures=tex, masks=masks, colours=R["colours"],
                    out=str(out / (name + ".png")), samples=samples, size=kw.pop("size", (420, 500)), **kw)

    class _M:                                    # anatomy by skeleton, as the design functions see it
        def __init__(self, model):
            self.skeleton = type("S", (), {"name": spec.SKELETONS[model].upper()})()
    assert REGISTRY
    rows = {}
    for row in ("heads", "kits", "close", "game"):
        if only and row not in only:
            continue
        rows[row] = []
        for i, (model, label, parts, ea, *_) in enumerate(R.get(row, [])):
            A = of(_M(model))
            if row == "heads":
                kw = dict(focus="head", head_bone=A.head_bone, size=(300, 330))
            elif row == "close":                 # (model, label, shown, ea, [focus meshes], distance in heights)
                focus, dist = R["close"][i][4], R["close"][i][5]
                kw = dict(focus="part", part=focus, dist=dist * A.height, size=(340, 340), azimuth=R["close"][i][6]
                          if len(R["close"][i]) > 6 else 28)
            elif row == "kits":
                kw = dict(size=(380, 480))
            else:
                kw = dict(elevation=48, scale=3.0, size=(300, 300))
            rows[row].append(job("%s%02d" % (row[0], i), model, ea, parts, label, **kw))
    return rows, out


def run(spec, samples=16, only=None):
    from sagekit.pipeline import blender_slot
    rows, out = jobs(spec, samples, only)
    todo = [j for r in rows.values() for j in r]
    specfile = out / "jobs.json"
    specfile.write_text(json.dumps(todo, indent=1))
    with blender_slot(), (out / "blender.log").open("w") as log:
        subprocess.run([paths.BLENDER, "-b", "--python-exit-code", "1", "--python", str(SCRIPT), "--", str(specfile)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    made = []
    for k, r in rows.items():
        lab = []
        for j in r:
            p = out / ("l_" + j["name"] + ".png")
            subprocess.run(["magick", j["out"], "-gravity", "NorthWest", "-font", paths.FONT, "-pointsize", "15", "-fill", "white",
                            "-undercolor", "#171b21cc", "-annotate", "+6+6", " %s " % j["label"], str(p)], check=True)
            lab.append(str(p))
        per = 8 if k == "heads" else 6
        for n in range(0, len(lab), per):
            row = out / ("row_%s_%d.png" % (k, n // per))
            subprocess.run(["magick", *lab[n:n + per], "+append", str(row)], check=True)
            made.append(str(row))
    name = "overview.png" if not only else "overview_%s.png" % "_".join(sorted(only))
    subprocess.run(["magick", *made, "-background", "#171b21", "-gravity", "West", "-append", str(out / name)], check=True)
    print(out / name)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    samples = int(sys.argv[sys.argv.index("--samples") + 1]) if "--samples" in sys.argv else 16
    only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
    run(importlib.import_module("assets.cah.%s.design" % args[0]), samples, only)
