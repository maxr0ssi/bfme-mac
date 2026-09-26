"""EA's body, measured: the numbers a recipe used to type by hand.

The Dwarven recipes hold 5,708 hand-typed measurements against 89 kit calls (docs/FACTIONS-PLAN.md):
most recipe code was reading EA's model. `python3 -m sagekit measure <faction/building>` reads the
target mesh from EA's file (sagekit/blender/measure.py, on Blender's Python) and writes
build/assets/<faction>/<building>/work/measure.json; design() reads it back:

    from sagekit.measure import measured
    m = measured(self)
    m.bbox                  [[x, y, z] min, [x, y, z] max]
    m.footprint.hull        convex outline [[x, y]...], m.footprint.area
    m.planes                dominant face planes, largest first: .kind (wall / floor / slope /
                            overhang / underside), .normal, .offset (n.p), .area, .u / .v extents
                            along .u_axis / .v_axis (walls: u horizontal, v = z)
    m.levels                up-facing area by height [{z, area}]: ledges, walkways, roofs
    m.bands                 .ground, .plinth_top, .walkways, .roof, .top
    m.setbacks              heights where the outline steps in or out: {z, below, above}
                            (extents [xmin, xmax, ymin, ymax] under and over the step)
    m.openings              doors, arches, niches in the big walls: .kind (hole | recess), .u
                            along the wall, .z, .width, .height, .depth, .top (flat | pointed or
                            round), .top_z {middle, jambs}, .at_ground
    m.heads                 tower and column heads: .centre, .z, .top_box [x0, x1, y0, y1]
    m.symmetry              mirror axes and the quarter turn: .axis, .c, .match

All in the frame design() builds in: the target mesh's own coordinates, or model space for
world_space recipes. Walls are found to the grid (0.5 units) for openings and heads, exactly for
planes, levels and setbacks (they come from the vertices).
"""
import json
import os
import subprocess
from types import SimpleNamespace

from . import paths


def _ns(x):
    if isinstance(x, dict):
        return SimpleNamespace(**{k: _ns(v) for k, v in x.items()})
    if isinstance(x, list):
        return [_ns(v) for v in x]
    return x


def path(b):
    """work/measure.json of a Building (or of a building id)."""
    return os.path.join(paths.work_dir(b if isinstance(b, str) else b.id), "work", "measure.json")


def run(building_id):
    """Measure one building now (Blender's Python: numpy); True when it worked."""
    r = subprocess.run([paths.blender_python(), "-m", "sagekit.blender.measure", building_id], cwd=paths.REPO,
                       env=dict(os.environ, PYTHONPATH=paths.REPO), capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("measuring %s failed:\n%s" % (building_id, r.stderr[-2000:]))
    return r.stdout


def measured(b, raw=False):
    """The measurements of building `b`'s EA body (measured on first use), as attributes (or the
    JSON dict with raw=True)."""
    p = path(b)
    if not os.path.exists(p):
        try:                                    # inside Blender: numpy is here, measure in-process
            from .blender.measure import run as measure_now
            measure_now(b.id)
        except ImportError:
            run(b.id)
    with open(p) as fh:
        data = json.load(fh)
    return data if raw else _ns(data)
