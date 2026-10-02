"""Render the shots of a faction's icon table in one Blender process (sagekit/blender/icon.py).

Each building's model is drawn twice: ours as it ships (out/, the faction's recoloured sheets on
its EA meshes, its cloth in the house colour, as the colour renders show it) and EA's (the
before), through the same cameras. EA's through our camera beside EA's own icon is how a
table's framing is checked (the calibration sheet).
"""
import json
import os
import subprocess
import time

from .. import paths, registry
from ..formats.w3d import W3DFile
from ..game import Install
from ..workspace import Workspace
from . import SCALE, root, table
from .mapped import images

RUN_PY = os.path.join(paths.REPO, "sagekit", "blender", "run.py")
GROUND = "art\\terrain\\tdirt_aus01.tga"       # EA's dirt with grass tufts, as on its portraits
TILE = 160.0


def wait_for_blender():
    """One Blender at a time on this machine (other builds share it): wait for any to finish."""
    said = False
    while subprocess.run(["pgrep", "-x", "Blender"], capture_output=True).returncode == 0:
        if not said:
            print("another Blender is running; waiting", flush=True)
            said = True
        time.sleep(10)


def ground(faction, g):
    path = os.path.join(root(faction), "src", "ground.tga")
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(g.read(GROUND))
    return path


def house(b, ws):
    """The cloth in the house colour, as job_render draws it for our model."""
    if not ws.house:
        return None
    from ..house import root as house_root
    from ..house import shipped
    _, out = shipped(b.style.faction)
    path = out and os.path.join(out, *Install.model_path(ws.house["model"]).split("\\"))
    own = ws.house_cloth if os.path.exists(ws.house_cloth) else None
    return [path, own, os.path.join(house_root(b.style.faction), "src")] if path and os.path.exists(path) else None


def out_path(faction, name, who):
    return os.path.join(root(faction), "render", "%s_%s.png" % (name, who))


def spec(faction, names=None, who=("new", "ea"), samples=None, sweep=None):
    """The Blender job's JSON: one entry per (building, who), its shots. sweep: (azimuths,
    elevation) renders EA's model of each named icon round the compass instead (calibration)."""
    from ..nightlights import day_hidden
    from ..pipeline import Pipeline, Render
    g = Install()
    icons, _ = table(faction)
    imgs = images(g)
    models = {}
    def drawn(b, w):
        ws = Workspace(b)
        model = ws.shipped_model if w == "new" else ws.reference_model
        texmap = ws.texture_map()
        texmap.update(Render(Pipeline(b)).references(model, recoloured=w == "new"))
        return dict(building=b.id, w3d=model, skeletons=ws.src, texmap=texmap,
                    house=house(b, ws) if w == "new" else None, hidden=list(day_hidden(b, W3DFile(model).data)))

    for name, shot in sorted(icons.items()):
        if names and name not in names:
            continue
        img = imgs[name.lower()]
        b = registry.load("%s/%s" % (faction, shot.building))
        for w in who:
            key = (b.id, w, shot.extra)
            if key not in models:
                extras = [dict(drawn(registry.load("%s/%s" % (faction, x)), w), offset=list(at), rotz=rot)
                          for x, at, rot in shot.extra]
                models[key] = dict(drawn(b, w), target=b.target, extras=extras, ground=ground(faction, g),
                                   tile=TILE, shots=[])
            base = dict(res=[img.width * SCALE, img.height * SCALE], focus=[list(f) for f in shot.focus],
                        fill=shot.fill, at=list(shot.at), lens=shot.lens, frame=list(shot.frame),
                        hide=list(shot.hide), azim=shot.azim, elev=shot.elev, ground=shot.ground,
                        samples=samples or (96 if shot.kind == "portrait" else 64))
            if sweep:
                for az in sweep[0]:
                    models[key]["shots"].append(dict(base, azim=az, elev=sweep[1], samples=samples or 16,
                                                     res=[img.width, img.height],
                                                     out=out_path(faction, "%s_%s_az%03d" % (name, w, az % 360), "sweep")))
            else:
                models[key]["shots"].append(dict(base, out=out_path(faction, name, w)))
    return dict(models=list(models.values()))


def run(faction, names=None, who=("new", "ea"), samples=None, sweep=None):
    job = spec(faction, names, who, samples, sweep)
    if not job["models"]:
        raise SystemExit("no icons to render (assets/%s/icons.py)" % faction)
    os.makedirs(os.path.join(root(faction), "render"), exist_ok=True)
    path = os.path.join(root(faction), "render", "spec.json")
    with open(path, "w") as fh:
        json.dump(job, fh, indent=1)
    wait_for_blender()
    from ..pipeline import blender_slot
    t = time.time()
    with blender_slot():
        r = subprocess.run([paths.BLENDER, "-b", "--python", RUN_PY, "--", "icons", "-", "spec=" + path],
                           capture_output=True, text=True)
    with open(os.path.join(root(faction), "render", "blender.log"), "w") as fh:
        fh.write(r.stdout + r.stderr)
    if "JOB OK" not in r.stdout or "Traceback" in r.stdout + r.stderr:
        raise SystemExit("icon renders failed - see %s/render/blender.log\n%s" % (root(faction), (r.stdout + r.stderr)[-3000:]))
    n = sum(len(m["shots"]) for m in job["models"])
    print("rendered %d shots of %d models in %.0fs" % (n, len(job["models"]), time.time() - t))
