"""python -m sagekit.paint.palantir <job.json> (Blender's Python; sagekit/hud/factions.py writes the job).

job: hud (the Good/Evil pack's build dir), out (where <faction>_<kind>_4/_2.png go), factions (names
in assets/hud/factions), swatch (the looks' citadel swatches, <swatch>/<faction>/<name>.png),
pieces (the 3D ornaments' renders, <pieces>/<faction>_<kind>.png),
backdrop/place/keep (the mock-up; backdrop may be missing), mock_out.
"""
import json
import os
import sys
import time

from assets.hud.factions import look
from .frame import mockup, paint
from .tex import load_all
from ..icons import load


def main(path):
    job = json.load(open(path))
    os.makedirs(job["out"], exist_ok=True)
    for name in job["factions"]:
        t = time.time()
        F = look(name)
        F.tex = load_all(os.path.join(job.get("swatch", ""), name))
        F.keep, F.place = job.get("keep"), job.get("place")     # what the ornaments must stay clear of
        F.pieces = {k: load(os.path.join(job["pieces"], "%s_%s.png" % (name, k))) for k in ("double", "single")
                    if job.get("pieces") and os.path.exists(os.path.join(job["pieces"], "%s_%s.png" % (name, k)))}
        for kind in ("double", "single"):
            col4, a4, ea = paint(F, job["hud"], kind, os.path.join(job["out"], "%s_%s" % (name, kind)))
            if kind == "double" and os.path.exists(job.get("backdrop", "")):
                import numpy as np
                mockup(np.concatenate([col4, a4[..., None]], -1), ea, job["backdrop"], job["place"],
                       job["keep"], os.path.join(job["mock_out"], "mock_%s.png" % name))
        print("%s painted (%.0fs)" % (name, time.time() - t))
    if job.get("sockets"):
        sockets(job["hud"], job["out"])


SOCKETS = (1, 125, 131, 327)          # the portrait's chain of button rings on libInGameImagesMain_1 (1x px)


def sockets(hud, out):
    """The portrait's button rings, shared by every side, toned from the Good pack's bronze to a dark
    neutral gunmetal that sits with every faction (sockets_2.png; the glass inside stays)."""
    import numpy as np
    from .core import ramp
    from ..icons import save
    img = load(os.path.join(hud, "paint", "libingameimagesmain_1_2.png"))
    x0, y0, x1, y1 = (2 * v for v in SOCKETS)
    reg = img[y0:y1, x0:x1]
    rgb = reg[..., :3]
    lum = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    warm = np.clip((rgb[..., 0] - rgb[..., 2]) * 4.0, 0, 1) * (reg[..., 3] > 0.02)
    metal = ramp([(0, (0.02, 0.02, 0.022)), (0.3, (0.16, 0.16, 0.17)), (0.65, (0.52, 0.52, 0.54)),
                  (1, (0.92, 0.92, 0.95))], np.clip(lum * 1.1, 0, 1))
    reg[..., :3] = rgb * (1 - warm[..., None]) + metal * warm[..., None]
    img[y0:y1, x0:x1] = reg
    save(os.path.join(out, "sockets_2.png"), img)


if __name__ == "__main__":
    main(sys.argv[1])
