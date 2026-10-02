"""Wall neighbours for a table's `extra`: segments either side of a wall piece, laid along the
segment's long axis from the shipped models' boxes (EA's wall portraits show a hub or a gate in
its wall, not alone)."""
import os

from .. import registry
from ..formats.w3d import W3DFile
from ..formats.w3dframes import IDENTITY, mesh_frames, model_box
from ..workspace import Workspace


def box(building_id):
    """(lo, hi) over the shipped model's meshes (x, y, z), or None before a build."""
    ws = Workspace(registry.load(building_id))
    if not os.path.exists(ws.shipped_model):
        return None
    w = W3DFile(ws.shipped_model)
    try:
        frames = mesh_frames(w.data)
    except (KeyError, ValueError, IndexError):
        frames = {}
    boxes = [model_box(m, frames.get(n, IDENTITY)) for n, m in w.meshes.items() if m.verts and not n.upper().startswith("HC_")]
    if not boxes:
        return None
    return [min(b[i] for b in boxes) for i in range(3)], [max(b[i + 3] for b in boxes) for i in range(3)]


def beside(faction, piece, segment="wall_segment", each=2, gap=0.0):
    """Extras: `each` segments on both sides of `piece` along the segment's long axis."""
    seg, mine = box("%s/%s" % (faction, segment)), box("%s/%s" % (faction, piece))
    if not seg or not mine:
        return ()
    axis = 0 if seg[1][0] - seg[0][0] > seg[1][1] - seg[0][1] else 1
    length = seg[1][axis] - seg[0][axis]
    centre = [(a + b) / 2 for a, b in zip(*mine)]
    seg_c = [(a + b) / 2 for a, b in zip(*seg)]
    half = (mine[1][axis] - mine[0][axis]) / 2
    out = []
    for s in (1, -1):
        for k in range(each):
            at = [centre[0] - seg_c[0], centre[1] - seg_c[1], 0.0]
            at[axis] = centre[axis] - seg_c[axis] + s * (half + gap + length / 2 + length * k)
            out.append((segment, tuple(round(x, 2) for x in at), 0))
    return tuple(out)


def run(faction, segment="wall_segment", each=2):
    """Extras: a straight run of segments either side of a segment."""
    return beside(faction, segment, segment, each)
