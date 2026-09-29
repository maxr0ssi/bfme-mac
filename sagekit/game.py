"""The installed game, as the engine sees it: archives in load order, first provider wins."""
import os

from . import paths, snapshot
from .formats.big import Archive, norm
from .formats.ini import parse_draws, parse_objects


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
        if self._archives is None and snapshot.active():     # no game here: the offload snapshot
            self._archives = snapshot.archives(snapshot.active())
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
                if snapshot.active():
                    self._caches[live] = AssetCache(snapshot.cache_path(snapshot.active(), live))
                    continue
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
        in BFME2's - and its dependency switched only where that cache has the object; a model of
        ours ('model') is filed where EA's model it copies is; a model is patched where it is filed."""
        out, filed = {}, {}
        for op in ops:
            if op[0] == "model":                # a model of ours: filed where EA's model it copies is
                live = next((p for p, c in self.asset_caches().items() if c.has_model(op[2])), None)
                if live is None:
                    raise FileNotFoundError("no asset.dat files %s to copy for %s" % (op[2], op[1]))
                filed[op[1].lower()] = (live, op[2])
            elif op[0] == "texture" and op[3] and op[3].lower() in filed and self._copies_object(filed[op[3].lower()], op):
                live = filed[op[3].lower()][0]  # its object is filed there by the op before
            elif op[0] == "texture":
                _, new, like, model, obj = op
                have = [p for p, c in self.asset_caches().items() if c.has_texture(like)]
                # the cache that also has the object, if another files the sheet first (RotWK re-files
                # EBForge.tga; the Dwarven DBFORGE.ANVIL that depends on it is in BFME2's)
                live = next((p for p in have if model and self.asset_caches()[p].dependencies(model, obj) is not None),
                            have[0] if have else None)
                if live is None:
                    raise FileNotFoundError("no asset.dat files texture %s" % like)
                if model and self.asset_caches()[live].dependencies(model, obj) is None:
                    op = ("texture", new, like, None, None)
            else:
                live = filed.get(op[1].lower(), (None,))[0] or next((p for p, c in self.asset_caches().items() if c.has_model(op[1])), None)
                if live is None:
                    continue
            out.setdefault(live, []).append(op)
        return out

    def _copies_object(self, filed, op):
        """Whether the cache a model of ours is filed in has the texture op[2] and EA's object
        that becomes op[4] (CONTAINER.MESH under our name) in the copy."""
        (live, like), c = filed, self.asset_caches()[filed[0]]
        return c.has_texture(op[2]) and c.dependencies(like, like[:-4].upper() + "." + op[4].split(".", 1)[-1]) is not None

    # ------------------------------------------------------------------ art lookups
    @staticmethod
    def model_path(model):
        """Archive path of a model name: DBFortress -> art\\w3d\\db\\dbfortress.w3d"""
        m = model.lower()
        return "art\\w3d\\%s\\%s.w3d" % (m[:2], m)

    def has_model(self, model):
        return self.owner(self.model_path(model)) is not None

    @staticmethod
    def _dirs(ini_dir):
        return [ini_dir] if isinstance(ini_dir, str) else list(ini_dir)

    def _inis(self, ini_dir):
        return sorted({m for d in self._dirs(ini_dir) for m in self.members(d) if m.endswith(".ini")})

    def _parsed(self, member):
        """(draws, {object: parent}) of one INI, parsed once per Install."""
        cache = self.__dict__.setdefault("_ini_cache", {})
        if member not in cache:
            text = self.read(member).decode("latin-1")
            draws = parse_draws(text)
            for d in draws:
                d.file = member
            cache[member] = (draws, parse_objects(text))
        return cache[member]

    def draws(self, ini_dir):
        """[Draw] from every INI under ini_dir (a folder or file, or a list of them), each tagged with
        its file."""
        return [d for member in self._inis(ini_dir) for d in self._parsed(member)[0]]

    def object_draws(self, ini_dir):
        """{object: [Draw]} for the objects the INIs under ini_dir define, with the Draw modules a
        ChildObject or ObjectReskin inherits from a parent defined elsewhere (GondorFarm, in men\\,
        draws FarmInterface's from goodfaction\\structures\\farminterface.ini). Inherited modules keep
        their parent's object and file, where an edit to them must go; a module the child defines
        under the same tag replaces its parent's."""
        members = self._inis(ini_dir)
        out, parents = {}, {}
        for member in members:
            draws, objects = self._parsed(member)
            parents.update(objects)
            for d in draws:
                out.setdefault(d.object, []).append(d)
        for child, parent in sorted(parents.items()):
            seen = {child}
            while parent and parent not in parents and parent not in seen:     # defined elsewhere
                seen.add(parent)
                member = self.object_index().get(parent)
                if member is None:
                    break
                draws, objects = self._parsed(member)
                own = {d.tag for d in out.get(child, [])}
                out[child] = [d for d in draws if d.object == parent and d.tag not in own] + out.get(child, [])
                parent = objects.get(parent)
        return out

    def object_index(self):
        """{object: the INI under data\\ini\\object that defines it}."""
        if "_object_index" not in self.__dict__:
            idx = {}
            for member in self._inis("data\\ini\\object"):
                for name in parse_objects(self.read(member).decode("latin-1")):
                    idx.setdefault(name, member)
            self._object_index = idx
        return self._object_index
