"""EA's unit and ours, posed in EA's animations, side by side: renders/compare_<state>.png.

One Blender process (sagekit/blender/unit_pose.py) renders every state for both sides with the
same camera and light; ImageMagick labels and joins them.
"""
import json
import subprocess
from pathlib import Path

from .. import paths

SCRIPT = Path(paths.REPO) / "sagekit" / "blender" / "unit_pose.py"


def jobs(u, b, states):
    out = []
    for state in states:
        v = u.views[state]
        if v["anim"] not in u.anims:
            print("skipping %s: the recipe extracts no %s animation" % (state, v["anim"]))
            continue
        for who in ("original", "new"):
            textures = json.loads(((b.dir if who == "original" else b.work) / "textures.json").read_text())
            out.append(dict(who=who, state=state, view=v, frame=v["frame"],
                            model=str(b.ea_model() if who == "original" else b.model()),
                            reference=str(b.ea_model()), skeleton=str(b.src / (u.skeleton.lower() + ".w3d")),
                            anim=str(b.anim(v["anim"])), textures=textures, smooth=list(u.smooth),
                            opaque=u.opaque, out=str(b.renders / ("%s_%s.png" % (who, state))),
                            motion=str(b.work / ("motion_%s.txt" % v["anim"]))))
    return out


def previews(u, b, states=None):
    from ..pipeline import blender_slot, game_running
    if game_running():
        raise SystemExit("The game is running; close it before rendering unit previews.")
    states = states or list(u.views)
    bad = [s for s in states if s not in u.views]
    if bad:
        raise SystemExit("%s: no view %s (the recipe's: %s)" % (u.id, ", ".join(bad), ", ".join(u.views)))
    b.renders.mkdir(parents=True, exist_ok=True)
    todo = jobs(u, b, states)
    spec = b.work / "render-jobs.json"
    spec.write_text(json.dumps(todo, indent=1))
    with blender_slot(), (b.work / "render.log").open("w") as log:
        subprocess.run([paths.BLENDER, "-b", "--python-exit-code", "1", "--python", str(SCRIPT), "--", str(spec)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    made = []
    for state in dict.fromkeys(j["state"] for j in todo):
        images = []
        for who, title in zip(("original", "new"), u.labels):
            path = b.renders / ("%s_%s.png" % (who, state))
            label = path.with_name("label_" + path.name)
            subprocess.run(["magick", str(path), "-gravity", "NorthWest", "-font", paths.FONT, "-pointsize", "23",
                            "-fill", "white", "-undercolor", u.label_colour, "-annotate", "+20+20", " " + title + " ",
                            str(label)], check=True)
            images.append(str(label))
        made.append(b.renders / ("compare_%s.png" % state))
        subprocess.run(["magick", *images, "+append", str(made[-1])], check=True)
    print("Rendered %s" % ", ".join(str(p) for p in made))
    return made
