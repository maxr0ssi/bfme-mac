"""HUD icons: EA's building portraits and buttons repainted from our buildings (docs/ICONS.md).

A faction's table, `assets/<faction>/icons.py`, names every MappedImage of EA's that shows one
of its buildings and how to shoot it:

    ICONS = {"BPDFortress": Portrait("fortress", azim=-60, elev=14, fill=0.78, at=(0.5, 0.55)),
             "BDFortress": Button("fortress", focus=((0, 1), (0, 1), (0.55, 1)), elev=8, ...)}
    KEEP = {"BDFortress_Porter": "the builder's face (unit art)"}

`Portrait` is EA's 192 x 192 sepia painting of the whole building on its ground under a
vignette; `Button` its 64 x 64 round close-up against the sky (`sky=False`: against the
building's own wall, as EA's hearth, statue and mine buttons are). Every other image on the
faction's pages stays EA's pixel for pixel.

Shot fields: azim, elev (degrees, as sagekit/blender/render.py's cameras: the camera stands at
(cos e cos a, cos e sin a, sin e) from what it looks at); focus, the part of the framed meshes'
box ((x0, x1), (y0, y1), (z0, z1), fractions) the camera frames; fill, how much of the frame
the focus's projection fills (its larger side); at, where the focus's centre sits (fractions from
the top-left); lens (mm); frame, the meshes framed (default every mesh the model shows); hide,
meshes left out; ground, whether EA's terrain is under it (buttons: no, the sky goes all the way
down); extra, neighbours drawn beside it ((building, (x, y, z), turn about z): the wall
segments EA's wall portraits show either side of a hub); grade, overrides of the grade
(sagekit/icons/grade.py DEFAULTS).
"""
import importlib
import os
from dataclasses import dataclass, field

from .. import paths

SCALE = 4                       # renders at 4x the page's pixels: 2x pages later need no new renders


@dataclass(frozen=True)
class Shot:
    building: str
    kind: str = "portrait"
    azim: float = -50.0
    elev: float = 20.0
    focus: tuple = ((0, 1), (0, 1), (0, 1))
    fill: float = 0.8
    at: tuple = (0.5, 0.5)
    lens: float = 50.0
    frame: tuple = ()
    hide: tuple = ()
    extra: tuple = ()
    sky: bool = True
    ground: bool = True
    grade: dict = field(default_factory=dict)

    def __hash__(self):
        return hash((self.building, self.kind, self.azim, self.elev, self.focus))


# a tall thin tower's portrait: low, so it stands up against the sky; blender/icon.py frames its
# silhouette as EA's towers stand (BODY tall, foot at FOOT, a thin spire into the burnt edge)
TOWER = dict(elev=10, fill=0.84)


def Portrait(building, **kw):
    return Shot(building, "portrait", **kw)


def Button(building, **kw):
    kw.setdefault("elev", -6.0)
    kw.setdefault("ground", False)
    kw.setdefault("lens", 70.0)
    kw.setdefault("fill", 1.1)
    return Shot(building, "button", **kw)


def table(faction):
    """(ICONS, KEEP) of the faction (assets/<faction>/icons.py), or ({}, {})."""
    try:
        mod = importlib.import_module("assets.%s.icons" % faction)
    except ModuleNotFoundError:
        return {}, {}
    return dict(mod.ICONS), dict(getattr(mod, "KEEP", {}))


def root(faction):
    """build/assets/<faction>/_icons: renders, graded crops, pages, the review sheet's parts."""
    return os.path.join(paths.BUILD, faction, "_icons")


def shared_root():
    return os.path.join(paths.BUILD, "_icons")
