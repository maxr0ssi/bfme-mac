"""The colour a particle texture lends its keys: a key's colour reaches the screen multiplied by the
texture, and some of EA's textures are not grey (EXFireScroll3, the burning buildings' flames, is a
warm yellow: blue keys on it read green). `TextureTints(g)(name)` is the texture's mean colour,
weighted by brightness and alpha and scaled to luma 1, so a grey texture gives (1, 1, 1); tint.py
aims at the colour seen (key times this) and divides it back out of the key.

Read once from the game's file with ImageMagick (32 x 32) and kept in build/assets/_fx/textures.json.
"""
import json
import os
import subprocess
import tempfile

from .. import paths
from ..formats.textures import sheet_member

CACHE = os.path.join(paths.BUILD, "_fx", "textures.json")


class TextureTints:
    def __init__(self, g):
        self.g = g
        self.data = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
        self.dirty = False

    def __call__(self, name):
        if not name or name.lower().endswith(".w3d"):
            return (1.0, 1.0, 1.0)
        member = sheet_member(self.g, name)
        if member is None:
            return (1.0, 1.0, 1.0)
        key = "%s %d" % (member, self.g.owner(member).index()[member].size)
        if key not in self.data:
            self.data[key] = self._measure(member)
            self.dirty = True
        return tuple(self.data[key])

    def _measure(self, member):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, member.split("\\")[-1])
            with open(src, "wb") as fh:
                fh.write(self.g.read(member))
            raw = subprocess.check_output(["magick", src + "[0]", "-resize", "32x32!", "-depth", "8", "rgba:-"])
        acc, total = [0.0, 0.0, 0.0], 0.0
        for i in range(0, len(raw), 4):
            r, gr, b, a = raw[i:i + 4]
            w = a * (r + gr + b)
            acc = [acc[0] + r * w, acc[1] + gr * w, acc[2] + b * w]
            total += w
        if total <= 0:
            return [1.0, 1.0, 1.0]
        mean = [c / total for c in acc]
        lum = 0.30 * mean[0] + 0.59 * mean[1] + 0.11 * mean[2]
        return [round(c / lum, 4) for c in mean] if lum > 0 else [1.0, 1.0, 1.0]

    def save(self):
        if self.dirty:
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            with open(CACHE, "w") as fh:
                json.dump(self.data, fh, indent=0, sort_keys=True)
            self.dirty = False
