"""A game snapshot: the part of EA's archives a faction's builds read, for a machine without the
game (the A100 offload, docs/OFFLOAD.md).

`sagekit offload pack` writes one on the Mac; with SAGEKIT_GAME_SNAPSHOT=<its folder> set,
`game.Install` reads it instead of the game's .big files, in every process of a build (the host
steps and the Blender jobs inherit the variable). The snapshot keeps the full member index (every
path the game can load, in which archive, so `owner`/`has_model`/`members` answer as on the Mac)
and the bytes of the members a faction's builds read:

  - every INI under data\\ini (the faction's objects, their parents, the ownership scan);
  - every model the faction's Draw modules show, with their animation files and skeletons, and
    each recipe's source and the style's house template;
  - every texture those models' meshes name and every sheet the INIs swap in (.dds and .tga);
  - the style's declared shared sheets and their state variants;
  - the pristine asset.dat files, and the ownership fingerprint of the real archives.

A member outside the subset raises FileNotFoundError naming it: add it to `collect` and pack again.

    game/index.json          {"fingerprint", "archives": [path], "members": {key: [archive, size]}}
    game/members/<path>      the bytes, at the member's normalised path ('\\' -> '/')
    game/caches/<dir>/asset.dat   the pristine caches, <dir> as in the game (RotWK, BFME2)
"""
import json
import os

from .formats.big import norm

ENV = "SAGEKIT_GAME_SNAPSHOT"


def active():
    """The snapshot folder in use, or None (the real game)."""
    d = os.environ.get(ENV)
    return d if d else None


def _index(root):
    cache = _index.__dict__.setdefault("loaded", {})
    if root not in cache:
        with open(os.path.join(root, "index.json")) as fh:
            cache[root] = json.load(fh)
    return cache[root]


class SnapshotArchive:
    """One of the game's archives as the snapshot remembers it: its path (as on the Mac), its
    members, and the bytes of those the snapshot carries."""

    def __init__(self, root, path, members):
        self.root, self.path, self._index = root, path, members

    def index(self):
        return self._index

    def __contains__(self, member):
        return norm(member) in self._index

    def read(self, member):
        p = os.path.join(self.root, "members", *norm(member).split("\\"))
        if not os.path.exists(p):
            raise FileNotFoundError("%s is not in the offload snapshot (%s): add it to sagekit/snapshot.py "
                                    "collect() and pack again" % (member, self.root))
        with open(p, "rb") as fh:
            return fh.read()

    def extract(self, member, dest_root):
        out = os.path.join(dest_root, *norm(member).split("\\"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as fh:
            fh.write(self.read(member))
        return out


def archives(root):
    """The snapshot's archives in the game's search order (game.Install.archives)."""
    idx = _index(root)
    per = [{} for _ in idx["archives"]]
    for key, (i, size) in idx["members"].items():
        per[i][key] = size
    return [SnapshotArchive(root, p, m) for p, m in zip(idx["archives"], per)]


def cache_path(root, live):
    """The snapshot's copy of the live asset.dat `live` (a path under paths.GAMEDIRS)."""
    return os.path.join(root, "caches", os.path.basename(os.path.dirname(live)), "asset.dat")


def fingerprint(root):
    """The real archives' ownership fingerprint (sagekit/ownership.py), recorded at pack time."""
    return _index(root)["fingerprint"]


# ------------------------------------------------------------------------------------ packing
def collect(install, faction, buildings):
    """Archive members (normalised) the builds of `buildings` (Building objects of `faction`) read."""
    from .formats.textures import compiled_path
    from .formats.w3d import W3DFile
    style = buildings[0].style
    out = set(install.members("data\\ini"))
    models = {b.source.lower() for b in buildings}
    if getattr(style, "house_template", None):
        models.add(style.house_template.lower())
    textures = set()
    for ds in install.object_draws(style.ini_dirs()).values():     # (inherited modules included)
        for d in ds:
            for st in d.states:
                if st.model and st.model.lower() != "none":
                    models.add(st.model.lower())
                models.update(a.split(".")[-1].lower() for a in st.animations)
                textures.update(new for _, new in st.textures)
    seen = set()
    while models:
        m = models.pop()
        member = install.model_path(m)
        if m in seen or not install.owner(member):
            continue
        seen.add(m)
        out.add(norm(member))
        w = W3DFile(install.read(member))
        skl = w.skeleton()
        if skl:
            models.add(skl[:-4].lower())
        for mesh in w.meshes.values():
            textures.update(mesh.textures)
    stems = [k[:-4].lower() for k in (getattr(style, "shared_sheets", None) or {})]
    for t in textures:
        for ext in (".dds", ".tga"):
            member = norm(compiled_path(t, ext))
            if install.owner(member):
                out.add(member)
    for member in install.members("art\\compiledtextures"):
        name = member.split("\\")[-1]
        if any(name == s + ext or name.startswith(s + "_") for s in stems for ext in (".dds", ".tga")):
            out.add(member)
    return sorted(out)


def write(install, members, root, log=print):
    """The snapshot of `members` under root (game/); returns its size in bytes."""
    from .ownership import fingerprint as fp
    archives = install.archives()
    pos = {id(a): i for i, a in enumerate(archives)}
    install.owner("")
    idx = {"fingerprint": fp(install), "archives": [a.path for a in archives],
           "members": {k: [pos[id(a)], a.index()[k].size] for k, a in install._owner.items()}}
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, "index.json"), "w") as fh:
        json.dump(idx, fh)
    total = 0
    for m in members:
        data = install.read(m)
        p = os.path.join(root, "members", *m.split("\\"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(data)
        total += len(data)
    for live, cache in install.asset_caches().items():
        dest = cache_path(root, live)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(cache.path, "rb") as src, open(dest, "wb") as fh:
            data = src.read()
            fh.write(data)
        total += len(data)
    log("  game snapshot: %d of %d members, %.1f MB" % (len(members), len(idx["members"]), total / 1e6))
    return total

