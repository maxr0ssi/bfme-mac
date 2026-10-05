"""The heroes pack (assets/heroes, docs/HEROES.md): EA's hidden heroes unlocked, the Captain of
Erebor, Aragorn's level-8 armour; staged, installed and reverted like the cah pack.

    python3 -m assets.heroes.build                    # models, portraits, INI, strings, every check
    python3 -m sagekit.units.heroes --stage           # the archives into build/.../_install/, asset.dat round trip
    python3 -m sagekit.units.heroes --install [--dry-run]
    python3 -m sagekit.units.heroes --revert  [--dry-run]

    RotWK/!!!!!!!!!!!sagekit-heroes.big           our models, sheets, masks, portraits and icons; EA's
                                                  2.02 INI files with our heroes composed in (12 members)
    RotWK/lang/English!!!!!!!!!!!sagekit-heroes.big   2.02's English string table plus our labels (the
                                                  game reads data\\lotr.str from lang\\English*.big first)
    RotWK/!!!!!!!!!!!!!sagekit-units.big          the shared housecolor.ini (sagekit/units/install.py)
    asset.dat                                     our three models filed under their own names, our
                                                  textures registered; EA's records untouched

Revert removes both archives, takes our records out of asset.dat (records.py) and rebuilds the
shared house-colour archive without our lines. Every player in a LAN game needs the same pack.
"""
import argparse
import json
from pathlib import Path

from .. import paths
from ..formats.assetcache import AssetCache
from ..formats.big import Archive, pack
from ..game import Install
from ..install import apply, read, stage_ops
from ..pipeline import game_running
from . import Folder, load, pick, records
from .build import sha
from .install import SHARED, installed, live_dir, shared_receipt, shared_update

UID = "heroes/pack"
MODELS = {"skereborcpt_skn.w3d": "dudain_skn.w3d", "skaragorn_skn.w3d": "guaragorn_skn.w3d",
          "skgamling_skn.w3d": "rugamlingch_skn.w3d"}
TEXTURE_LIKE = {"sheet": "chdw_dw_of3d_hlmt_06.tga", "mask": "hc_chdw_tm_03.tga"}


def recipe():
    u = load(UID)
    return u, Folder(u)


def lang_path():
    from assets.heroes.strings import STRINGS_ARCHIVE
    return live_dir() / "lang" / STRINGS_ARCHIVE


def built():
    """{member: bytes} of the root archive, and the string table's bytes (from assets.heroes.build)."""
    out = Path(paths.BUILD) / "heroes" / "pack"
    rep = json.loads((out / "report.json").read_text())
    files = {m: Path(p).read_bytes() for m, p in rep["art"].items()}
    for m, p in rep["ini"].items():
        if m in files:
            raise SystemExit("heroes: %s twice" % m)
        files[m] = Path(p).read_bytes()
    from ..texbake import bake          # house-colour masks ship with their mips built (sagekit/texbake.py)
    return bake(files, log=lambda s: None), (out / "lotr.str").read_bytes()


def cache_ops(files):
    """asset.dat: our models filed as copies of EA's records, our textures registered."""
    from assets.heroes import portraits
    ops = [("model", ours, ea) for ours, ea in MODELS.items()]
    like = dict(portraits.textures())
    for member in sorted(files):
        if not member.startswith("art\\compiledtextures\\"):
            continue
        name = member.split("\\")[-1][:-4] + ".tga"
        src = like.get(name) or TEXTURE_LIKE["mask" if name.startswith("hc_") else "sheet"]
        ops.append(("texture", name, src, None, None))
    return ops


def model_source(files):
    by_name = {m.split("\\")[-1]: d for m, d in files.items() if m.endswith(".w3d")}
    return lambda name: by_name[name.lower()]


def owned(u, b):
    dest, lang = live_dir() / u.archive, lang_path()
    if not dest.exists() and not lang.exists():
        return False
    receipt = b.stage / "unit.json"
    if receipt.exists():
        r = json.loads(receipt.read_text())
        if dest.exists() and r["sha256"] == sha(dest.read_bytes()) and lang.exists() and r["lang_sha256"] == sha(lang.read_bytes()):
            return True
    raise SystemExit("%s or %s is in the game folder but no receipt of this pack installed it" % (dest, lang))


def stage(u, b):
    """Check the build (each model's HLOD resolves and has an oriented click box), pack both
    archives into _install/, prove the asset.dat records come back as they were on a copy of each
    cache. Nothing in the game changes."""
    files, table = built()
    for member, data in files.items():                  # the click box (pick.py): built by assets/heroes/gear.py
        if member.endswith(".w3d") and (pick.unresolved(data) or not (pick.pick_box(data) or [0, 0, 0])[2] & pick.ORIENTED):
            raise SystemExit("heroes: %s: HLOD sub-objects the file does not define %s, or no oriented BOUNDINGBOX; "
                             "rebuild (python3 -m assets.heroes.build)" % (member, pick.unresolved(data)))
    g, active, mine = Install(), Install(pristine=False), owned(u, b)
    for member in files:
        owner = active.owner(member)
        if owner and Path(owner.path).name != u.archive and Path(owner.path).name.lower() < u.archive.lower():
            raise SystemExit("heroes: %s comes from %s, which the game reads before ours" % (member, owner.path))
        if owner and Path(owner.path).name != u.archive and paths.is_ours(Path(owner.path).name):
            raise SystemExit("heroes: %s is %s's edit; ours, built on EA's, would drop it" % (member, owner.path))
        if not mine and member.startswith("art\\") and g.owner(member):
            raise SystemExit("heroes: EA ships %s already" % member)
    ops = cache_ops(files)
    if not mine:
        for op in ops:
            name = op[1]
            if any((c.has_model(name) if op[0] == "model" else c.has_texture(name)) for c in g.asset_caches().values()):
                raise SystemExit("heroes: asset.dat files %s already (another install?)" % name)
    routed = g.route_cache_ops(ops)
    where = model_source(files)
    for live, cops in routed.items():
        if mine:
            continue
        cache, pristine = AssetCache(live), AssetCache(live + ".orig")
        st = records.staged(cache, cops, where)
        if records.unstage(st, pristine, cops, where) != cache.data:
            raise SystemExit("heroes: reverting %s would not give back today's records" % live)
    b.stage.mkdir(parents=True, exist_ok=True)
    archive, lang = b.stage / u.archive, b.stage / lang_path().name
    pack(sorted(files.items()), str(archive))
    pack([("data\\lotr.str", table)], str(lang))
    a = Archive(str(archive))
    assert all(a.read(n) == d for n, d in files.items()) and Archive(str(lang)).read("data\\lotr.str") == table
    (b.stage / "staged.json").write_text(json.dumps(dict(sha256=sha(archive.read_bytes()), lang_sha256=sha(lang.read_bytes()),
                                                         members=sorted(files), caches=routed), indent=1) + "\n")
    print("Staged %s: %s (%d members, %d bytes) and %s; asset.dat round trip checked; nothing installed." % (
        UID, archive, len(files), archive.stat().st_size, lang))
    return archive, lang, files, routed


def _commit(b, updates, expected, units):
    if game_running():
        raise SystemExit("The game is running; nothing changed.")
    apply(updates, b.stage / "apply-receipt.json", expected)
    shared = live_dir() / SHARED
    if shared in updates:
        if updates[shared] is None:
            shared_receipt().unlink(missing_ok=True)
        else:
            shared_receipt().write_text(json.dumps(dict(sha256=sha(updates[shared]), units=units)) + "\n")


def install(dry=False):
    if game_running():
        raise SystemExit("Close the game before installing.")
    u, b = recipe()
    archive, lang, files, routed = stage(u, b)
    dest, data, lang_dest, lang_data = live_dir() / u.archive, archive.read_bytes(), lang_path(), lang.read_bytes()
    updates = {}
    expected = {dest: read(dest), lang_dest: read(lang_dest), live_dir() / SHARED: read(live_dir() / SHARED)}
    if owned(u, b):
        if dest.read_bytes() != data or lang_dest.read_bytes() != lang_data:
            raise SystemExit("heroes: another build of the pack is installed; --revert it first")
        print("The heroes pack is installed already; composing the shared house-colour INI.")
    else:
        updates[dest], updates[lang_dest] = data, lang_data
        for live, ops in routed.items():
            cache = AssetCache(live)
            expected[Path(live)] = cache.data
            stage_ops(cache, [(op, model_source(files)) for op in ops])
            updates[Path(live)] = cache.data
    units = installed(include=[UID])
    shared, ini = shared_update(units)
    updates.update(shared)
    if dry:
        print("Dry run: would write %s" % ", ".join(str(p) for p in updates))
        return
    _commit(b, updates, expected, units)
    (b.stage / "unit.json").write_text(json.dumps(dict(sha256=sha(data), lang_sha256=sha(lang_data), caches=routed), indent=1) + "\n")
    if Install(pristine=False).read("data\\ini\\housecolor.ini") != ini:
        raise SystemExit("Installed, but another archive's housecolor.ini shadows the shared one")
    print("Installed the heroes pack (%d members and the string table); the house-colour INI carries %s." % (
        len(files), ", ".join(units)))


def revert(dry=False):
    if game_running():
        raise SystemExit("Close the game before reverting.")
    u, b = recipe()
    dest, lang_dest = live_dir() / u.archive, lang_path()
    if not owned(u, b):
        raise SystemExit("The heroes pack is not installed.")
    shipped = Archive(str(dest))
    files = {n: shipped.read(n) for n in shipped.index()}
    ops = cache_ops(files)
    updates = {dest: None, lang_dest: None}
    expected = {dest: read(dest), lang_dest: read(lang_dest), live_dir() / SHARED: read(live_dir() / SHARED)}
    for live, cops in Install().route_cache_ops(ops).items():
        cache, pristine = AssetCache(live), AssetCache(live + ".orig")
        expected[Path(live)] = cache.data
        updates[Path(live)] = records.unstage(cache, pristine, cops, model_source(files))
    shared, _ = shared_update(installed(exclude=[UID]))
    updates.update(shared)
    if dry:
        print("Dry run: would write %s" % ", ".join("%s (%s)" % (p, "remove" if d is None else "%d bytes" % len(d))
                                                     for p, d in updates.items()))
        return
    _commit(b, updates, expected, installed(exclude=[UID]))
    (b.stage / "unit.json").unlink(missing_ok=True)
    print("Removed the heroes pack and its string table; its asset.dat records are gone, every other record untouched.")


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m sagekit.units.heroes", description=__doc__.split("\n")[0])
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", action="store_true")
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--revert", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    if a.stage:
        stage(*recipe())
    elif a.install:
        install(a.dry_run)
    else:
        revert(a.dry_run)


if __name__ == "__main__":
    main()
