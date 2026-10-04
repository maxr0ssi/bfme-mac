"""python -m sagekit.paint.palantir <job.json> (Blender's Python; sagekit/hud/factions.py writes the job).

job: hud (the Good/Evil pack's build dir), out (where <faction>_<kind>_4/_2.png go), factions (names
in assets/hud/factions), backdrop/place/keep (the mock-up; backdrop may be missing), mock_out.
"""
import json
import os
import sys
import time

from assets.hud.factions import look
from .frame import mockup, paint


def main(path):
    job = json.load(open(path))
    os.makedirs(job["out"], exist_ok=True)
    for name in job["factions"]:
        t = time.time()
        F = look(name)
        for kind in ("double", "single"):
            col4, a4, ea = paint(F, job["hud"], kind, os.path.join(job["out"], "%s_%s" % (name, kind)))
            if kind == "double" and os.path.exists(job.get("backdrop", "")):
                import numpy as np
                mockup(np.concatenate([col4, a4[..., None]], -1), ea, job["backdrop"], job["place"],
                       job["keep"], os.path.join(job["mock_out"], "mock_%s.png" % name))
        print("%s painted (%.0fs)" % (name, time.time() - t))


if __name__ == "__main__":
    main(sys.argv[1])
