"""Find and load the buildings under assets/, enforcing the taxonomy."""
import importlib
import inspect
import os

from . import paths
from .building import Building
from .taxonomy import check_id


def building_ids():
    out = []
    for faction in sorted(os.listdir(paths.ASSETS)):
        fdir = os.path.join(paths.ASSETS, faction)
        if not os.path.isdir(fdir) or faction.startswith(("_", ".")):
            continue
        for b in sorted(os.listdir(fdir)):
            if os.path.isfile(os.path.join(fdir, b, "building.py")):
                out.append("%s/%s" % (faction, b))
    return out


def load(building_id):
    """The Building instance for 'faction/building'."""
    faction, name = building_id.split("/")
    check_id("faction", faction)
    check_id("building", name)
    mod = importlib.import_module("assets.%s.%s.building" % (faction, name))
    classes = [c for _, c in inspect.getmembers(mod, inspect.isclass)
               if issubclass(c, Building) and c is not Building and c.__module__ == mod.__name__]
    if len(classes) != 1:
        raise ValueError("%s/building.py must define exactly one Building subclass (found %d)" % (building_id, len(classes)))
    b = classes[0]()
    b.id = building_id
    if b.style is None or b.style.faction != faction:
        raise ValueError("%s: style must be the %s faction's Style" % (building_id, faction))
    for attr in ("source", "target"):
        if not getattr(b, attr):
            raise ValueError("%s: %s is required" % (building_id, attr))
    return b
