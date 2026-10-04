"""Install a unit into the game, and take it out again, in any order with any other unit.

    RotWK/<unit.archive>                  the unit: its model, private atlas, mask, and
                                          housecolor.ini as EA's plus its own lines (the release
                                          pack's member, sagekit/pack.py)
    RotWK/!!!!!!!!!!!!!sagekit-units.big  housecolor.ini: EA's plus every installed unit's lines,
                                          in unit-id order; thirteen '!' sort it before every
                                          unit archive, so it is the one the game reads
    asset.dat                             the unit's own records (sagekit/units/records.py)

Each unit archive's own housecolor.ini shadows the others' (the first archive wins), so before
the shared archive a builder had to be installed after the others and keep their lines (the
Dwarven builder's held the Elven one's). The shared archive is rebuilt from the recipes on every
unit install and revert. Revert puts the unit's records back as EA's and removes its archive,
whatever was installed after it; a legacy install (receipt.json of apply()) reverts the same way.
"""
import json
from pathlib import Path

from .. import paths
from ..formats.assetcache import AssetCache
from ..formats.big import Archive, pack
from ..formats.ini import set_model
from ..formats.textures import compiled_path
from ..formats.w3d import W3DFile, rename_model
from ..game import Install
from ..install import apply, read, stage_ops
from ..pipeline import game_running
from . import Folder, build, ids, load, records

SHARED = "!!!!!!!!!!!!!sagekit-units.big"
INI = "data\\ini\\housecolor.ini"


def live_dir():
    return Path(paths.GAMEDIRS["rotwk"])


def shared_receipt():
    return Path(paths.BUILD) / "_units" / "shared.json"


def unit_archives():
    """{archive name (lower): unit id} of every unit recipe with an archive."""
    out = {}
    for uid in ids():
        u = load(uid)
        if u.archive:
            out[u.archive.lower()] = uid
    return out


def installed(exclude=(), include=()):
    """Unit ids whose archive is in the game folder (and `include`), without `exclude`, sorted."""
    present = {p.name.lower() for p in live_dir().glob("*.big")}
    have = {uid for name, uid in unit_archives().items() if name in present}
    return sorted((have | set(include)) - set(exclude))


def base(member):
    """`member` as the game reads it without any unit archive (EA's, or a faction pack's)."""
    ours = set(unit_archives()) | {SHARED.lower()}
    for a in Install(pristine=False).archives():
        if Path(a.path).name.lower() not in ours and member.lower() in a.index():
            return a.read(member)
    raise FileNotFoundError(member)


def mapping(u):
    return "".join("\r\nHouseColor\r\n\tBaseTexture = %s\r\n\tHouseTexture = %s\r\nEnd\r\n" % kv
                   for kv in u.house.items()).encode("latin-1")


def compose(ini, units):
    """ini plus each unit's lines; refuses a texture the INI maps already."""
    import re
    for u in units:
        for name in u.house:
            if re.search(rb"(?im)^\s*BaseTexture\s*=\s*" + re.escape(name.encode()) + rb"\s*$", ini):
                raise SystemExit("%s: housecolor.ini maps %s already" % (u.id, name))
        ini += mapping(u)
    return ini


def ea_source(u):
    """EA's model as the build starts from it (renamed to own_model)."""
    data = Install().read(Install.model_path(u.model))
    return rename_model(data, u.model, u.own_model) if u.own_model else data


def cache_ops(u, model):
    """The asset.dat ops for our model (bytes), in order: its record, the mask, each mesh's texture."""
    shipped = u.shipped.lower() + ".w3d"
    original, new = W3DFile(ea_source(u)), W3DFile(model)
    ops = [("model", shipped, u.model.lower() + ".w3d")] if u.own_model else [("patch", shipped)]
    if u.mask:
        ops.append(("texture", u.mask[1].lower(), u.mask[0].lower(), None, None))
    ops += [("texture", texture, old, shipped, m.container + "." + m.name) for n, m in new.meshes.items()
            for old, texture in zip(original.meshes[n].textures, m.textures) if old.lower() != texture.lower()]
    return ops


def members(u, b):
    """{archive member: bytes} the unit's archive holds."""
    g = Install()
    files = {g.model_path(u.shipped): b.model().read_bytes()}
    files.update({compiled_path(n, ".dds"): (b.work / (n.lower()[:-4] + ".dds")).read_bytes() for n in u.privates()})
    if u.mask:
        files[compiled_path(u.mask[1], ".tga")] = (b.work / u.mask[1].lower()).read_bytes()
    if u.house:
        files[INI] = compose(base(INI), [u])
    files.update(u.ini_files(base))
    for obj, (member, tag) in u.objects.items():
        text = files.get(member) or base(member)
        files[member] = set_model(text.decode("latin-1"), obj, tag, u.model, u.own_model).encode("latin-1")
        if files[member] == text:
            raise SystemExit("%s: %s draws no %s in %s %s" % (u.id, obj, u.model, member, tag))
    return files


def named(objects, files):
    """The objects of `objects` that an INI of `files` {member: bytes} names as its WorkerName."""
    import re
    out = set()
    for member, data in files.items():
        if member.lower().endswith(".ini"):
            for obj in objects:
                if re.search(rb"(?im)^\s*WorkerName\s*=\s*" + re.escape(obj.encode()) + rb"\b", data):
                    out.add(obj)
    return out


def workers_guard(faction, files):
    """sagekit/install.py, before a faction pack is installed: every worker object its INIs name
    (Style.workers) is defined by a unit installed already, or nothing is installed."""
    have = installed()
    for uid in ids(faction):
        u = load(uid)
        if u.defines and named(u.defines, files) and uid not in have:
            raise SystemExit("%s's buildings name %s, which %s defines: python3 -m sagekit unit %s --install "
                             "first; nothing installed" % (faction, ", ".join(sorted(named(u.defines, files))), uid, uid))


def pack_files():
    """{member: bytes} of every INI in the faction packs in the game folder (eleven '!')."""
    out = {}
    for p in sorted(live_dir().glob("!!!!!!!!!!!sagekit-*.big")):
        if p.name.startswith("!!!!!!!!!!!!"):
            continue                                    # twelve or more: a unit's or a shared archive
        a = Archive(str(p))
        out.update({m: a.read(m) for m in a.index() if m.endswith(".ini")})
    return out


def owned(u, b):
    """Whether the game folder holds this unit's archive as installed (refuses an unknown one)."""
    dest = live_dir() / u.archive
    if not dest.exists():
        return False
    digest = build.sha(dest.read_bytes())
    for receipt in (b.stage / "unit.json", b.stage / "receipt.json"):
        if receipt.exists():
            entries = json.loads(receipt.read_text())
            entries = entries if isinstance(entries, list) else [dict(path=u.archive, after=entries["sha256"])]
            if any(Path(e["path"]).name == u.archive and e["after"] == digest for e in entries):
                return True
    raise SystemExit("%s: %s is in the game folder but no receipt of this unit installed it" % (u.id, u.archive))


def stage(u, b):
    """Check the build, then pack the archive into _install/; nothing in the game changes."""
    if not u.archive or not build.check(u, b)["rebuilt"]:
        raise SystemExit("%s: nothing to install (no archive, or design() rebuilds no mesh)" % u.id)
    g, active, mine = Install(), Install(pristine=False), owned(u, b)
    files = members(u, b)
    for member in files:
        if member == INI or member in {m for m, _ in u.objects.values()}:
            continue
        owner = active.owner(member)
        if owner and Path(owner.path).name != u.archive and Path(owner.path).name.lower() < u.archive.lower():
            raise SystemExit("%s: %s comes from %s, which the game reads before ours" % (u.id, member, owner.path))
    shipped = g.model_path(u.shipped)
    if u.own_model and (g.owner(shipped) or not mine and any(
            c.has_model(u.shipped.lower() + ".w3d") for c in g.asset_caches().values())):
        raise SystemExit("%s: EA has a model named %s (an archive or asset.dat files it)" % (u.id, u.own_model))
    if not u.own_model and not mine and build.sha(active.read(shipped)) != u.expected.get(u.model.lower(), build.sha(g.read(shipped))):
        raise SystemExit("%s: the game's %s is not EA's" % (u.id, u.model))
    for name in u.privates() + ([u.mask[1]] if u.mask else []):
        for ext in (".dds", ".tga"):
            owner = active.owner(compiled_path(name, ext))
            if owner and (not mine or Path(owner.path).name != u.archive):
                raise SystemExit("%s: %s is another archive's texture" % (u.id, name))
        if not mine and any(c.has_texture(name) for c in g.asset_caches().values()):
            raise SystemExit("%s: asset.dat registers %s already" % (u.id, name))
    b.stage.mkdir(parents=True, exist_ok=True)
    archive = b.stage / u.archive
    pack(sorted(files.items()), str(archive))
    staged = Archive(str(archive))
    assert all(staged.read(n) == data for n, data in files.items())
    routed = g.route_cache_ops(cache_ops(u, files[shipped]))
    print("Staged %s: %s (%d members); nothing installed." % (u.id, archive, len(files)))
    return archive, files, routed


def shared_update(units):
    """{shared archive path: bytes or None}: EA's housecolor.ini plus the units' lines."""
    dest = live_dir() / SHARED
    receipt = shared_receipt()
    if dest.exists():
        want = json.loads(receipt.read_text())["sha256"] if receipt.exists() else None
        if build.sha(dest.read_bytes()) != want:
            raise SystemExit("%s changed since a unit wrote it; refusing to replace it" % dest)
    if not units:
        return {dest: None}, None
    ini = compose(base(INI), [load(uid) for uid in units])
    receipt.parent.mkdir(parents=True, exist_ok=True)
    tmp = receipt.with_name(SHARED)
    pack([(INI, ini)], str(tmp))
    return {dest: tmp.read_bytes()}, ini


def _commit(u, b, updates, expected, note):
    if game_running():
        raise SystemExit("The game is running; nothing changed.")
    apply(updates, b.stage / "apply-receipt.json", expected)
    shared = live_dir() / SHARED
    if shared in updates:
        if updates[shared] is None:
            shared_receipt().unlink(missing_ok=True)
        else:
            shared_receipt().write_text(json.dumps(dict(sha256=build.sha(updates[shared]), units=note)) + "\n")


def install(u, b, dry=False):
    if game_running():
        raise SystemExit("Close the game before installing.")
    archive, files, routed = stage(u, b)
    dest, data = live_dir() / u.archive, archive.read_bytes()
    updates, expected = {}, {dest: read(dest), live_dir() / SHARED: read(live_dir() / SHARED)}
    if owned(u, b):
        if dest.read_bytes() != data:
            raise SystemExit("%s: another build of this unit is installed; --revert it first" % u.id)
        print("%s is installed already; composing the shared house-colour INI." % u.id)
    else:
        updates[dest] = data
        for live, ops in routed.items():
            cache, pristine = AssetCache(live), AssetCache(live + ".orig")
            expected[Path(live)] = cache.data
            keys = records.written(ops)
            now, ea = records.index(cache), records.index(pristine)
            if any(now.get(k, []) != ea.get(k, []) for k in keys):
                raise SystemExit("%s: asset.dat %s holds records of another install for this unit" % (u.id, live))
            stage_ops(cache, [(op, lambda model: str(b.model())) for op in ops])
            updates[Path(live)] = cache.data
    units = installed(include=[u.id])
    shared, ini = shared_update(units)
    updates.update(shared)
    if dry:
        print("Dry run: would write %s" % ", ".join(str(p) for p in updates))
        return
    _commit(u, b, updates, expected, units)
    (b.stage / "unit.json").write_text(json.dumps(dict(sha256=build.sha(data), caches={
        live: ops for live, ops in routed.items()}), indent=1) + "\n")
    if Install(pristine=False).read(INI) != ini:
        raise SystemExit("Installed, but another archive's housecolor.ini shadows the shared one")
    print("Installed %s; the house-colour INI carries %s." % (u.id, ", ".join(units)))


def revert(u, b, dry=False):
    if game_running():
        raise SystemExit("Close the game before reverting.")
    dest = live_dir() / u.archive
    if not owned(u, b):
        raise SystemExit("%s is not installed." % u.id)
    if u.defines and named(u.defines, pack_files()):
        raise SystemExit("%s: an installed faction pack names %s (its WorkerName); revert or reinstall that "
                         "pack first, so no building calls a worker that no longer exists" % (u.id, ", ".join(u.defines)))
    model = Archive(str(dest)).read(Install.model_path(u.shipped))
    updates, expected = {dest: None}, {dest: read(dest), live_dir() / SHARED: read(live_dir() / SHARED)}
    for live, ops in Install().route_cache_ops(cache_ops(u, model)).items():
        cache, pristine = AssetCache(live), AssetCache(live + ".orig")
        expected[Path(live)] = cache.data
        updates[Path(live)] = records.unstage(cache, pristine, ops, lambda m: model)
    shared, _ = shared_update(installed(exclude=[u.id]))
    updates.update(shared)
    if dry:
        print("Dry run: would write %s" % ", ".join("%s (%s)" % (p, "remove" if d is None else "%d bytes" % len(d))
                                                     for p, d in updates.items()))
        return updates
    _commit(u, b, updates, expected, installed(exclude=[u.id]))
    (b.stage / "unit.json").unlink(missing_ok=True)
    if (b.stage / "receipt.json").exists():                     # a legacy install's: kept, renamed
        (b.stage / "receipt.json").rename(b.stage / "receipt.reverted.json")
    print("Removed %s; its asset.dat records are EA's again, every other record untouched." % u.id)


def release(u, b=None):
    """For sagekit/pack.py (staged with --stage): (archive, {game: [cache op]} as install applies
    them, {INI: our lines}, [folders of the EA files it was made from])."""
    b = b or Folder(u)
    archive = b.stage / u.archive
    if not archive.exists():
        raise SystemExit("%s: not staged: python3 -m sagekit unit %s --stage" % (u.id, u.id))
    staged = Archive(str(archive))
    if any(staged.read(m) != d for m, d in members(u, b).items() if m != INI):
        raise SystemExit("%s: the staged archive is not the reviewed build: stage it again (--stage)" % u.id)
    games = {str(Path(d).resolve()): k for k, d in paths.GAMEDIRS.items()}
    routed = Install().route_cache_ops(cache_ops(u, staged.read(Install.model_path(u.shipped))))
    return archive, {games[str(Path(live).parent.resolve())]: ops for live, ops in routed.items()}, \
        ({INI: mapping(u)} if u.house else {}), [b.src]
