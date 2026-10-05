"""The faction palantirs' materials cut from each citadel's sheets (assets/hud/factions/swatches.py):
build/assets/_hud/factions/swatch/<faction>/<name>.png, re-cut when the sheet is newer."""
import os
import subprocess
import sys

from .. import paths
from ..icons.pixels import MAGICK
from . import root


def spec():
    sys.path.insert(0, paths.REPO)
    from assets.hud.factions import swatches
    return swatches


def folder(name):
    return os.path.join(root(), "factions", "swatch", name)


def cut(names):
    """Crop every faction's swatches; a missing sheet is an error (build the faction first)."""
    sw = spec()
    n = 0
    for name in names:
        out = folder(name)
        os.makedirs(out, exist_ok=True)
        for key, (src, rect, rot) in sw.SWATCHES.get(name, {}).items():
            path = os.path.join(paths.BUILD, sw.SOURCES[name][src])
            if not os.path.exists(path):
                raise SystemExit("%s: no %s (%s); build the faction's sheets first" % (name, src, path))
            dst = os.path.join(out, key + ".png")
            if os.path.exists(dst) and os.path.getmtime(dst) > max(os.path.getmtime(path),
                                                                  os.path.getmtime(sw.__file__)):
                continue
            x0, y0, x1, y1 = rect
            cmd = [MAGICK, path + "[0]", "-crop", "%dx%d+%d+%d" % (x1 - x0, y1 - y0, x0, y0), "+repage",
                   "-alpha", "off"]
            if rot:
                cmd += ["-rotate", str(rot)]
            subprocess.check_call(cmd + ["-depth", "8", dst])
            n += 1
    return n
