"""Render the faction palantirs' 3D ornaments (assets/hud/factions/pieces.py) in Blender:
build/assets/_hud/factions/pieces/<faction>_<kind>.png at the painter's 4x, its shadows in the alpha.
A render is redone only when its spec or the Blender script changes (the spec's hash beside it)."""
import hashlib
import json
import os
import subprocess
import sys

from .. import paths
from . import root

PAGES = {"double": (512, 256), "single": (256, 256)}
SCRIPT = os.path.join(paths.REPO, "sagekit", "blender", "hudpieces.py")


def spec():
    sys.path.insert(0, paths.REPO)
    from assets.hud.factions import pieces
    return pieces


def folder():
    p = os.path.join(root(), "factions", "pieces")
    os.makedirs(p, exist_ok=True)
    return p


def jobs(names):
    sp = spec()
    out = []
    for n in names:
        for kind, (w, h) in PAGES.items():
            ps = [p for where, p in sp.PIECES.get(n, []) if where == "both" or where == kind]
            if not ps:
                continue
            used = sorted({p["mat"] for p in ps})
            r = dict(w=w, h=h, scale=4, pieces=ps, mats={m: sp.MATS[m] for m in used}, **sp.LIGHT.get(n, {}))
            key = hashlib.sha1((json.dumps(r, sort_keys=True) + open(SCRIPT).read()).encode()).hexdigest()[:16]
            r["out"] = os.path.join(folder(), "%s_%s.png" % (n, kind))
            r["hash"] = key
            out.append(r)
    return out


def render(names):
    """Render what changed; returns the number rendered."""
    from ..pipeline import blender_slot
    todo = []
    for r in jobs(names):
        stamp = r["out"] + ".key"
        if os.path.exists(r["out"]) and os.path.exists(stamp) and open(stamp).read() == r["hash"]:
            continue
        todo.append(r)
    if not todo:
        return 0
    path = os.path.join(folder(), "job.json")
    with open(path, "w") as fh:
        json.dump(dict(renders=todo, samples=64), fh, indent=1)
    with blender_slot():
        res = subprocess.run([paths.BLENDER, "-b", "--factory-startup", "--python", SCRIPT, "--", path],
                             capture_output=True, text=True)
    log = res.stdout + res.stderr
    open(os.path.join(folder(), "render.log"), "w").write(log)
    if "JOB OK" not in res.stdout or "Traceback" in log:
        raise SystemExit("ornament render failed - see %s\n%s" % (os.path.join(folder(), "render.log"), log[-2500:]))
    for r in todo:
        open(r["out"] + ".key", "w").write(r["hash"])
    return len(todo)
