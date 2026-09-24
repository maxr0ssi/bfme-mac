"""The one entry point for work inside Blender:

    Blender -b [scene.blend] --python sagekit/blender/run.py -- <job> <faction/building> [key=value ...]

Jobs (sagekit/blender/jobs.py): geometry, bake, paint, export, reference, render, checks.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from sagekit import registry  # noqa: E402
from sagekit.blender import jobs  # noqa: E402


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    job, building_id = argv[0], argv[1]
    opts = dict(a.split("=", 1) for a in argv[2:])
    fn = getattr(jobs, "job_" + job, None)
    if fn is None:
        raise SystemExit("unknown job %s" % job)
    fn(registry.load(building_id), **opts)
    print("JOB OK", job, flush=True)


main()
