"""Unit recipes: a skinned unit (a faction's builder) redesigned on EA's body, skeleton and animations.

A recipe is assets/<faction>/<unit>/design.py with one `Unit` subclass. It names EA's model, the
private texture names its rebuilt meshes draw, the house-colour mask and the archive it installs in;
`design(w, sk)` returns {MESH NAME: Mesh} (EA's meshes with rigid pieces bound to EA's bones,
sagekit/units/mesh.py) and `paint(b)` writes the private atlas. Everything else is shared:

    build.py    sources and their hashes, the model, the mask, the checks
    paint.py    atlas helpers (palette ramps, ImageMagick, the tiled house mask)
    render.py   EA's builder and ours posed in EA's animations (sagekit/blender/unit_pose.py)
    install.py  the unit's own archive, its asset.dat records, the shared house-colour INI, revert
    cli.py      python3 -m sagekit unit <faction>/<unit> [--render|--check|--stage|--install|--revert]

How a recipe works: docs/UNITS.md.
"""
import importlib
import inspect
import os
from pathlib import Path

from .. import paths
from .mesh import Mesh  # noqa: F401  (recipes import it from here)


def View(anim, frame, target=(8, 0, 9), distance=77, elevation=48, size=(1100, 900), fit=False,
         fit_min=90, fit_scale=2.2, azimuth=-38, lens=52):
    """One preview pose: EA's animation `anim` at `frame`, the camera on `target` (or, fit=True,
    on the bounds of EA's model in that pose, at max(fit_min, its diagonal x fit_scale))."""
    return dict(anim=anim, frame=frame, target=list(target), distance=distance, elevation=elevation,
                size=list(size), fit=fit, fit_min=fit_min, fit_scale=fit_scale, azimuth=azimuth, lens=lens)


DEFAULT_VIEWS = {"portrait": View("idla", 0, distance=70, elevation=22, size=(1200, 1050), fit=True, fit_min=70, fit_scale=1.8),
                 "rts": View("idla", 0, fit=True), "run": View("runa", 8, fit=True),
                 "walk": View("wlka", 8, fit=True), "work": View("wrkb", 23, fit=True),
                 "water": View("fira", 38, fit=True), "death": View("diea", 45, fit=True)}


class Unit:
    id = None                   # "dwarves/porter" (set by load)
    model = None                # EA's model the INI draws: "DUPorter_SKN"
    skeleton = None             # its skeleton; the animation files are <skeleton family>_<anim>.w3d
    own_model = None            # ship under this name (EA's model is shared with other factions)
    objects = {}                # own_model: {object: (INI member, Draw tag)} whose Model is repointed
    anims = ()                  # animations extracted for the previews ("idla", "runa", ...)
    expected = {}               # {"duporter_skn": sha256, ...}: refuse any other source
    textures = {}               # {EA texture: private texture} renamed in the rebuilt meshes
    house = {}                  # {private texture: private mask}: house-colour INI lines, in order
    mask = None                 # (EA's mask, ours): EA's tiled across the atlas' left half
    sources = ()                # further EA sheets paint() reads ("DBFortress1.tga")
    archive = None              # "!!!!!!!!!!!!sagekit-dwarf-builder.big"
    bone = "CART"               # Mesh primitives' default bone
    smooth = ()                 # meshes the preview shades smooth
    opaque = False              # the preview ignores texture alpha (EA's opaque legacy meshes)
    views = DEFAULT_VIEWS       # {state: View(...)}
    labels = ("EA'S BUILDER", "OURS - DESIGN PREVIEW")
    label_colour = "#171b21cc"
    same_bones = ()             # rebuilt meshes whose bone set must stay EA's

    # ------------------------------------------------------------------ the recipe's part
    def design(self, w, sk):
        """{MESH NAME: Mesh} replacing EA's meshes; {} ships EA's model unchanged (a stub)."""
        return {}

    def paint(self, b):
        """Write the private atlas; return its image path (encoded as every private name's DDS)."""
        return None

    def check(self, b, original, new, sk):
        """Recipe checks beyond the shared ones (build.check); raise AssertionError."""

    # ------------------------------------------------------------------ derived
    def mesh(self, w, sk, name, keep=False, skin=None):
        """Mesh for EA's mesh `name` with this recipe's texture names and default bone."""
        from ..formats.w3dpose import hlod
        return Mesh(w.meshes[name], sk, keep=keep, names=self.textures, bone=self.bone,
                    rigid_bone=hlod(w.data)[2].get(name.upper(), 0), skin=skin)

    @property
    def family(self):
        return self.skeleton.lower()[:-4] if self.skeleton.lower().endswith("_skl") else self.skeleton.lower()

    @property
    def shipped(self):
        """The model name the archive ships: own_model, else EA's."""
        return self.own_model or self.model

    def privates(self):
        """Private texture names, each once, in first-use order."""
        return list(dict.fromkeys(self.textures.values()))


class Folder:
    """build/assets/<faction>/<unit> (or `root`): src/ EA's files, work/ ours, renders/, _install/."""

    def __init__(self, unit, root=None):
        self.unit = unit
        self.dir = Path(root) if root else Path(paths.BUILD) / unit.id
        self.src, self.work, self.renders = self.dir / "src", self.dir / "work", self.dir / "renders"
        self.stage = self.dir / "_install"

    def ea_model(self):
        return self.src / (self.unit.model.lower() + ".w3d")

    def source_model(self):
        """EA's model as our build starts from it (renamed to own_model when there is one)."""
        return self.src / (self.unit.shipped.lower() + ".w3d")

    def model(self):
        return self.work / (self.unit.shipped.lower() + ".w3d")

    def anim(self, a):
        return self.src / ("%s_%s.w3d" % (self.unit.family, a.lower()))


def ids(faction=None):
    """Every unit recipe: assets/<faction>/<unit>/design.py defining a Unit subclass."""
    out = []
    for f in sorted(os.listdir(paths.ASSETS)):
        fdir = os.path.join(paths.ASSETS, f)
        if not os.path.isdir(fdir) or f.startswith(("_", ".")) or faction and f != faction:
            continue
        for u in sorted(os.listdir(fdir)):
            design = os.path.join(fdir, u, "design.py")
            if os.path.isfile(design) and "Unit)" in open(design).read():
                out.append("%s/%s" % (f, u))
    return out


def load(unit_id):
    faction, name = unit_id.strip("/").split("/")
    mod = importlib.import_module("assets.%s.%s.design" % (faction, name))
    found = [c for _, c in inspect.getmembers(mod, inspect.isclass)
             if issubclass(c, Unit) and c is not Unit and c.__module__ == mod.__name__]
    if len(found) != 1:
        raise ValueError("%s/design.py must define exactly one Unit subclass (found %d)" % (unit_id, len(found)))
    u = found[0]()
    u.id = "%s/%s" % (faction, name)
    for attr in ("model", "skeleton"):
        if not getattr(u, attr):
            raise ValueError("%s: %s is required" % (u.id, attr))
    if u.own_model and len(u.own_model) > 15:
        raise ValueError("%s: own model name %s is longer than 15 characters" % (u.id, u.own_model))
    for old, new in u.textures.items():
        if len(new) > len(old):
            raise ValueError("%s: private %s is longer than EA's %s (names are renamed in place)" % (u.id, new, old))
    if {t.lower() for t in u.house} - {t.lower() for t in u.privates()}:
        raise ValueError("%s: house maps a texture the recipe does not ship" % u.id)
    return u
