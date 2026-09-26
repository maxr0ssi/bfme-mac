"""Install a faction: one archive with everything built for it, and the asset caches to match.

    RotWK/!!!!!!!!!!!sagekit-<faction>.big     (eleven '!': sorts before the group pack and the HD
                                                Edition, so our files win)
      - the recoloured sheets (build/assets/<faction>/_sheets/out)
      - every building whose checks passed (build/assets/<faction>/<building>/out)
      - the faction INIs with every building's edits applied to EA's text, in order
    asset.dat (each one that files a building's models): rebuilt from the pristine <asset.dat>.orig
    plus every building's cache ops, then verified - so installing twice gives the same bytes.

The archives an earlier experiment installed (hand-made tests) are moved to build/assets/_removed.
`revert` removes the faction archive and restores each asset.dat from its .orig.
"""
import os
import shutil

from . import house, paths, registry
from .formats.assetcache import AssetCache
from .formats.big import pack
from .formats.ini import apply_ops
from .game import Install
from .pipeline import apply_cache_ops
from .workspace import Workspace

SUPERSEDED = ("!!!!!!!!!!!fortress-test.big", "!!!!!!!!!!!hires-dwarf.big")


def archive_name(faction):
    return "!!!!!!!!!!!sagekit-%s.big" % faction


def built(faction):
    """(Building, Workspace) for every building of the faction whose last build passed its checks."""
    out = []
    for bid in registry.building_ids():
        if bid.split("/")[0] != faction:
            continue
        b = registry.load(bid)
        ws = Workspace(b)
        if os.path.exists(ws.path("work", "checks.ok")):
            out.append((b, ws))
    return out


def collect(faction, install):
    """{archive path: bytes} of everything the faction archive holds, and {asset.dat: [(op, ws)]}."""
    files, ini_ops, cache_ops = {}, {}, {}
    sheets = os.path.join(paths.BUILD, faction, "_sheets", "out")
    for root, _, names in os.walk(sheets):
        for n in names:
            p = os.path.join(root, n)
            files[os.path.relpath(p, sheets).replace("/", "\\")] = open(p, "rb").read()
    buildings = built(faction)
    superseded = {b.base for b, _ in buildings if b.base}   # their model ships from the dependent's build
    for b, ws in buildings:
        out = ws.path("out")
        mine = install.model_path(b.source).lower()
        for root, _, names in os.walk(out):
            for n in names:
                rel = os.path.relpath(os.path.join(root, n), out).replace("/", "\\")
                if rel.lower().endswith(".ini") or b.id in superseded and rel.lower() == mine:
                    continue
                files[rel] = open(os.path.join(root, n), "rb").read()
        for member, ops in b.ini_ops(install, ws.variants).items():
            ini_ops.setdefault(member, []).extend(ops)
        ops = b.cache_ops(ws.variants, ws.derived)
        if b.id in superseded:
            ops = [op for op in ops if op != ("patch", b.model_file)]
        for live, ops in install.route_cache_ops(ops).items():
            cache_ops.setdefault(live, []).extend((op, ws) for op in ops)
    record, house_out = house.shipped(faction)          # house-colour models (sagekit/house.py)
    if record:
        where = HouseOut(house_out)
        for member in record["models"]:
            files[member] = open(where.out(member), "rb").read()
            model = member.split("\\")[-1]
            for live, ops in install.route_cache_ops([("patch", model)]).items():
                cache_ops.setdefault(live, []).extend((op, where) for op in ops)
        for member, ops in record["ini"].items():
            ini_ops.setdefault(member, []).extend(tuple(op) for op in ops)
    for member, ops in ini_ops.items():
        files[member] = apply_ops(install.read(member).decode("latin-1"), ops).encode("latin-1")
    return files, cache_ops


class HouseOut:
    """Where the house-colour step's files are, with the Workspace.out interface install uses."""

    def __init__(self, out_dir):
        self.dir = out_dir

    def out(self, archive_path):
        return os.path.join(self.dir, *archive_path.split("\\"))


def install_faction(faction, log=print):
    g = Install()
    files, cache_ops = collect(faction, g)
    if not files:
        raise SystemExit("nothing built for %s yet" % faction)
    rotwk = paths.GAMEDIRS["rotwk"]
    removed = os.path.join(paths.BUILD, "_removed")
    for name in SUPERSEDED:
        if os.path.exists(os.path.join(rotwk, name)):
            os.makedirs(removed, exist_ok=True)
            shutil.move(os.path.join(rotwk, name), os.path.join(removed, name))
            log("moved aside %s -> build/assets/_removed/" % name)
    dest = os.path.join(rotwk, archive_name(faction))
    pack(sorted(files.items()), dest)
    log("packed %d files, %.1f MB -> %s" % (len(files), os.path.getsize(dest) / 1e6, os.path.relpath(dest, paths.REPO)))
    for live, ops in cache_ops.items():
        orig = live + ".orig"
        if not os.path.exists(orig):
            shutil.copy2(live, orig)
        cache = AssetCache(orig)
        cache.path = live
        for op, ws in ops:
            apply_cache_ops(cache, [op], lambda model, ws=ws: ws.out(g.model_path(model[:-4])))
        for op, ws in ops:
            if op[0] == "patch" and cache.stale_entries(ws.out(g.model_path(op[1][:-4])), op[1]):
                raise SystemExit("cache record of %s does not match after install" % op[1])
        cache.save(backup=False)
        log("asset cache %s: pristine + %d ops, records verified" % (os.path.relpath(live, paths.REPO), len(ops)))


def revert_faction(faction, log=print):
    dest = os.path.join(paths.GAMEDIRS["rotwk"], archive_name(faction))
    if os.path.exists(dest):
        os.remove(dest)
        log("removed %s" % os.path.basename(dest))
    for g in paths.GAMEDIRS.values():
        live = os.path.join(g, "asset.dat")
        if os.path.exists(live + ".orig"):
            shutil.copy2(live + ".orig", live)
            log("restored %s from .orig" % os.path.relpath(live, paths.REPO))
