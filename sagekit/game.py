"""The installed game, as the engine sees it: archives in load order, first provider wins."""
import os

from . import paths
from .formats.big import Archive, norm
from .formats.ini import parse_draws


class Install:
    """pristine=True (the default) ignores the archives this repo installs, so every source is
    EA's original even while a modified version is in the game."""

    def __init__(self, game="rotwk", pristine=True):
        self.game = game
        self.pristine = pristine
        self._archives = None
        self._owner = None
        self._caches = None

    def archives(self):
        """Every .big the game loads, in the order it searches them."""
        if self._archives is None:
            self._archives = []
            for g in paths.SEARCH_ORDER[self.game]:
                d = paths.GAMEDIRS[g]
                for name in sorted((f for f in os.listdir(d) if f.lower().endswith(".big")), key=str.lower):
                    if self.pristine and paths.is_ours(name):
                        continue
                    self._archives.append(Archive(os.path.join(d, name)))
        return self._archives

    def owner(self, member):
        """The archive the game takes `member` from, or None."""
        if self._owner is None:
            self._owner = {}
            for a in reversed(self.archives()):            # earlier archives overwrite later ones
                for key in a.index():
                    self._owner[key] = a
        return self._owner.get(norm(member))

    def read(self, member):
        a = self.owner(member)
        if a is None:
            raise FileNotFoundError("no archive provides %s" % member)
        return a.read(member)

    def extract(self, member, dest_root):
        a = self.owner(member)
        if a is None:
            raise FileNotFoundError("no archive provides %s" % member)
        return a.extract(member, dest_root)

    def members(self, prefix=""):
        """Every member path (normalised) the game can load, optionally under a directory."""
        self.owner("")
        p = norm(prefix)
        return sorted(k for k in self._owner if k.startswith(p))

    def asset_caches(self):
        """{live asset.dat path: AssetCache of its pristine copy}, in search order."""
        if self._caches is None:
            from .formats.assetcache import AssetCache
            self._caches = {}
            for g in paths.SEARCH_ORDER[self.game]:
                live = os.path.join(paths.GAMEDIRS[g], "asset.dat")
                self._caches[live] = AssetCache(live + ".orig" if os.path.exists(live + ".orig") else live)
        return self._caches

    def asset_cache(self, model):
        """Path of the asset.dat that files `model` (BFME2's for base-game art, RotWK's for its own)."""
        for live, cache in self.asset_caches().items():
            if cache.has_model(model):
                return live
        raise FileNotFoundError("no asset.dat files %s" % model)

    def route_cache_ops(self, ops):
        """{live asset.dat: [op]} (op as Building.cache_ops). A texture is registered in the cache
        that files the texture it copies - RotWK files some models in its own cache and their sheets
        in BFME2's - and its dependency switched only where that cache has the object; a model is
        patched where it is filed, and skipped when no cache files it (the game parses it)."""
        out = {}
        for op in ops:
            if op[0] == "texture":
                _, new, like, model, obj = op
                live = next((p for p, c in self.asset_caches().items() if c.has_texture(like)), None)
                if live is None:
                    raise FileNotFoundError("no asset.dat files texture %s" % like)
                if model and self.asset_caches()[live].dependencies(model, obj) is None:
                    op = ("texture", new, like, None, None)
            else:
                live = next((p for p, c in self.asset_caches().items() if c.has_model(op[1])), None)
                if live is None:
                    continue
            out.setdefault(live, []).append(op)
        return out

    # ------------------------------------------------------------------ art lookups
    @staticmethod
    def model_path(model):
        """Archive path of a model name: DBFortress -> art\\w3d\\db\\dbfortress.w3d"""
        m = model.lower()
        return "art\\w3d\\%s\\%s.w3d" % (m[:2], m)

    def has_model(self, model):
        return self.owner(self.model_path(model)) is not None

    def draws(self, ini_dir):
        """[Draw] from every INI under ini_dir, each tagged with its file."""
        out = []
        for member in self.members(ini_dir):
            if member.endswith(".ini"):
                for d in parse_draws(self.read(member).decode("latin-1")):
                    d.file = member
                    out.append(d)
        return out
