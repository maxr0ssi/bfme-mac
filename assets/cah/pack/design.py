"""The cah pack's recipe for the shared house-colour archive (sagekit/units/install.py): one Unit
whose archive is the pack's and whose house lines are every class's masks. The pack itself is
built per class (assets/cah/<class>/build.py) and staged, installed and reverted by
python3 -m sagekit.units.cah, never by `sagekit unit`."""
import importlib
from pathlib import Path

from sagekit.units import Unit

ARCHIVE = "!!!!!!!!!!!sagekit-cah.big"
NOT_CLASSES = ("kit", "pack")


def classes():
    """Every class folder under assets/cah (one with a design.py), in name order: the order the
    pack composes their INI in."""
    root = Path(__file__).resolve().parents[1]
    names = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name not in NOT_CLASSES and (p / "design.py").exists())
    return [importlib.import_module("assets.cah.%s.design" % n) for n in names]


def _masks():
    out = {}
    for spec in classes():
        out.update(spec.MASKS)
    return out


class CaHPack(Unit):
    """The cah pack's archive and house-colour lines (python3 -m sagekit.units.cah)."""
    model, skeleton = "CHDW_TM_U_SKN", "CHDW_DW_U_SKL"
    house = _masks()
    textures = {t: t for t in house}
    archive = ARCHIVE

    def design(self, w, sk):
        raise SystemExit("cah/pack is the cah pack: build each class (python3 -m assets.cah.<class>.build), then "
                         "python3 -m sagekit.units.cah --stage | --install | --revert")
