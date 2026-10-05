"""EA's APT movies as the game loads them, and the one edit Retina needs: doubled texture matrices.

The game mounts every .big under its folder, the apt/ subfolder too, first provider wins: RotWK's
own archives (__patch202.big overrides palantir.apt and two of its .ru files), then apt/<Movie>.big,
then BFME2's. A movie is <movie>.apt/.const/.dat plus <movie>_geometry\\<character>.ru, and its
images are art\\textures\\apt_<movie>_<n>.tga.

How the game maps an image (game.dat, RotWK 2.01; docs/HUD.md has the addresses):
  .dat    each line `img->tex` (the image lives on texture apt_<movie>_<tex>.tga) or `img=x y w h`
          (texture apt_<movie>_<img>.tga): the loader reads only the ids, never the rect
  .ru     `s tc:r:g:b:a:img:a:b:c:d:tx:ty`: the six floats map the shape's coordinates to the
          texture's PIXELS; at first draw they are divided by the loaded texture's width (a, c, tx)
          and height (b, d, ty)
So a texture twice the size draws its top-left quarter, unless every matrix that samples it is
doubled too. Doubled together, the movie draws the same shape at the same place and size, with
twice the texels. Nothing else reads these textures' sizes.
"""
import os
import re

from .. import paths
from ..formats.big import Archive, norm
from ..game import Install

STYLE = re.compile(r"^(s t[a-z]:)(.*)$")


class Apt:
    """The game's APT members, pristine (archives this repo installs are skipped)."""

    def __init__(self, game="rotwk"):
        self.game = game
        self._archives = []
        for g in paths.SEARCH_ORDER[game]:
            d = paths.GAMEDIRS[g]
            roots = Install(g, pristine=True).archives()
            self._archives += [a for a in roots if os.path.dirname(a.path) == d]
            sub = os.path.join(d, "apt")
            if os.path.isdir(sub):
                self._archives += [Archive(os.path.join(sub, f)) for f in sorted(os.listdir(sub), key=str.lower)
                                   if f.lower().endswith(".big")]
        self._owner = None

    def owner(self, member):
        if self._owner is None:
            self._owner = {}
            for a in reversed(self._archives):
                for k in a.index():
                    self._owner[k] = a
        return self._owner.get(norm(member))

    def read(self, member):
        a = self.owner(member)
        if a is None:
            raise FileNotFoundError("no archive provides %s" % member)
        return a.read(member)

    def members(self, prefix):
        self.owner("")
        p = norm(prefix)
        return sorted(k for k in self._owner if k.startswith(p))


def images(apt, movie):
    """{image id: texture id} from the movie's .dat."""
    out = {}
    for line in apt.read("%s.dat" % movie.lower()).decode("latin-1").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        if "->" in line:
            img, tex = line.split("->")
            out[int(img)] = int(tex)
        else:
            img = int(re.match(r"\d+", line).group())
            out[img] = img
    return out


def geometry(apt, movie, own=False):
    """{member: bytes} of every .ru file of the movie, as the game reads them. own: only the game's
    own (RotWK's); BFME2's Palantir.big has .ru files for characters RotWK's movie does not have."""
    home = os.path.realpath(paths.GAMEDIRS[apt.game])
    return {m: apt.read(m) for m in apt.members("%s_geometry\\" % movie.lower()) if m.endswith(".ru")
            and (not own or os.path.realpath(apt.owner(m).path).startswith(home + os.sep))}


def scale(text, image_ids, factor):
    """The .ru text with the texture matrix of every style sampling one of image_ids multiplied by
    factor; (new text, lines changed). Line endings and every other byte are kept."""
    out, changed = [], 0
    for line in text.split("\n"):
        body = line[:-1] if line.endswith("\r") else line
        m = STYLE.match(body)
        if m:
            f = m.group(2).split(":")
            if len(f) != 11:
                raise ValueError("unexpected texture style: %r" % body)
            if int(f[4]) in image_ids:
                f[5:] = [_num(float(v) * factor) for v in f[5:]]
                body = m.group(1) + ":".join(f)
                changed += 1
        out.append(body + ("\r" if line.endswith("\r") else ""))
    return "\n".join(out), changed


def _num(v):
    s = "%.6f" % v
    return s.rstrip("0").rstrip(".") if "." in s else s


def matrices(text):
    """[(image id, (a, b, c, d, tx, ty))] of a .ru text's texture styles."""
    out = []
    for line in text.splitlines():
        m = STYLE.match(line.strip())
        if m:
            f = m.group(2).split(":")
            out.append((int(f[4]), tuple(float(v) for v in f[5:])))
    return out


def retina(apt, movie, textures, factor=2):
    """{member: bytes} of the movie's .ru files whose matrices sample one of `textures` (texture ids),
    doubled; and the count of styles changed."""
    imgs = images(apt, movie)
    ids = {i for i, t in imgs.items() if t in textures}
    out, total = {}, 0
    for member, data in geometry(apt, movie, own=True).items():
        text, n = scale(data.decode("latin-1"), ids, factor)
        if n:
            out[member] = text.encode("latin-1")
            total += n
    return out, total
