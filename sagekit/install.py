"""Install a faction: one archive with everything built for it, and the asset caches to match.

    RotWK/!!!!!!!!!!!sagekit-<faction>.big     (eleven '!': sorts before the group pack and the HD
                                                Edition, so our files win)
      - the recoloured sheets (build/assets/<faction>/_sheets/out)
      - every building whose checks passed (build/assets/<faction>/<building>/out)
      - the faction INIs with every building's edits applied to EA's text, in order
    asset.dat: patch the CURRENT cache, preserving other installed factions and units.

Every write is staged and backed up. Revert restores the last installation only when its
files still match the receipt, never overwriting a later installation's shared cache.
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path

from . import house, paths, registry
from .formats.assetcache import AssetCache
from .formats.big import pack
from .formats.ini import apply_ops
from .game import Install
from .pipeline import apply_cache_ops, game_running
from .workspace import Workspace

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
    # a chained recipe's base: its model and derived models ship from the dependent's build, which
    # carries the base's redesign too (Building.derived_models)
    superseded = {b.base for b, _ in buildings if b.base}
    for b, ws in buildings:
        out = ws.path("out")
        models = {b.model_file} | {b.shipped_name(m).lower() + ".w3d" for m in ws.derived + ws.lifecycle} \
            if b.id in superseded else set()
        mine = {install.model_path(m[:-4]).lower() for m in models}
        for root, _, names in os.walk(out):
            for n in names:
                rel = os.path.relpath(os.path.join(root, n), out).replace("/", "\\")
                if rel.lower().endswith(".ini") or rel.lower() in mine:
                    continue
                files[rel] = open(os.path.join(root, n), "rb").read()
        for member, ops in b.ini_ops(install, ws.variants).items():
            ini_ops.setdefault(member, []).extend(ops)
        ops = [op for op in b.cache_ops(ws.variants, ws.derived + ws.lifecycle) if not (op[0] == "patch" and op[1] in models)]
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


def cache_records(cache, assets=(), objects=()):
    """Unrelated records, including duplicates, byte-for-byte in their original order."""
    aa, _, oo = cache.sections()
    return ([cache.data[s:e] for n,s,e in aa if n.lower().decode() not in assets],
            [cache.data[s:e] for f,o,s,e in oo if (f.lower().decode(),o.lower().decode()) not in objects])


def prepare(faction):
    """Return the archive members and new cache bytes; never alter the installation."""
    g = Install()
    files, cache_ops = collect(faction, g)
    if not files:
        raise SystemExit("nothing built for %s yet" % faction)
    updates = {}
    for live, ops in cache_ops.items():
        cache = AssetCache(live)
        assets, objects = set(), set()
        for op,_ in ops:
            assets.add(op[1].lower())
            if op[0] == "texture" and op[3]:
                objects.add((op[3].lower(),op[4].lower()))
        untouched = cache_records(cache,assets,objects)
        for op, ws in ops:
            apply_cache_ops(cache, [op], lambda model, ws=ws: ws.out(g.model_path(model[:-4])))
        for op, ws in ops:
            if op[0] == "patch" and cache.stale_entries(ws.out(g.model_path(op[1][:-4])), op[1]):
                raise SystemExit("staged cache record of %s does not match" % op[1])
            if op[0] == "texture":
                if not cache.has_texture(op[1]):
                    raise SystemExit("staged texture is not registered: %s" % op[1])
                if op[3]:
                    deps = cache.dependencies(op[3],op[4])
                    if deps is None or op[1].lower() not in [d.lower() for d in deps]:
                        raise SystemExit("staged texture dependency does not match: %s %s" % (op[3],op[4]))
        if cache_records(cache,assets,objects) != untouched:
            raise SystemExit("refusing to change unrelated cache records: %s" % live)
        updates[Path(live)] = cache.data
    return files, updates


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def read(path):
    return path.read_bytes() if path.exists() else None


def atomic(path, data):
    if data is None:
        path.unlink(missing_ok=True)
        return
    fd, tmp = tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def apply(updates, receipt, expected=None):
    """Back up and replace a reviewed file set; roll back our writes if any step fails."""
    before = {p:read(p) for p in updates} if expected is None else {p:expected[p] for p in updates}
    if any(read(p) != b for p,b in before.items()):
        raise RuntimeError("installation files changed since preparation; stage again")
    updates = {p:b for p,b in updates.items() if b != before[p]}
    if not updates:
        return False
    receipt.parent.mkdir(parents=True,exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix="backup-",dir=receipt.parent))
    entries = []
    for i,(p,data) in enumerate(updates.items()):
        b = backup/(str(i)+".bak")
        if before[p] is not None:
            b.write_bytes(before[p])
        entries.append(dict(path=str(p),backup=str(b),before=digest(before[p]),after=digest(data)))
    written = []
    try:
        for p,data in updates.items():
            if read(p) != before[p]:
                raise RuntimeError("file changed during staging: %s" % p)
            atomic(p,data)
            written.append(p)
        for p,data in updates.items():
            if read(p) != data:
                raise RuntimeError("installed bytes do not match: %s" % p)
        atomic(receipt,(json.dumps(entries,indent=2)+"\n").encode())
    except BaseException:
        for p in reversed(written):
            if read(p) == updates[p]:
                atomic(p,before[p])
        raise
    return True


def install_faction(faction, log=print, check=False):
    if game_running():
        raise SystemExit("close the game before installing")
    dest = Path(paths.GAMEDIRS["rotwk"])/archive_name(faction)
    expected = {Path(g)/"asset.dat":read(Path(g)/"asset.dat") for g in paths.GAMEDIRS.values()}
    expected[dest] = read(dest)
    files, updates = prepare(faction)
    stage = Path(paths.BUILD)/faction/"_install"
    stage.mkdir(parents=True,exist_ok=True)
    archive = stage/archive_name(faction)
    pack(sorted(files.items()),str(archive))
    updates[Path(paths.GAMEDIRS["rotwk"])/archive.name] = archive.read_bytes()
    for p,data in updates.items():
        if p.name == "asset.dat":
            (stage/(p.parent.name+"-asset.dat")).write_bytes(data)
    if check:
        log("Staged and verified; unrelated cache records preserved. Nothing installed.")
        return
    if game_running():
        raise SystemExit("game started during staging; nothing installed")
    apply(updates,stage/"receipt.json",expected)
    log("Installed %s; scoped backups saved, unrelated records preserved." % faction)


def revert_faction(faction, log=print):
    if game_running():
        raise SystemExit("close the game before reverting")
    receipt = Path(paths.BUILD)/faction/"_install/receipt.json"
    if not receipt.exists():
        raise SystemExit("No scoped installation receipt; refusing to reset shared caches from .orig.")
    entries = json.loads(receipt.read_text())
    updates, expected = {}, {}
    for e in entries:
        p = Path(e["path"])
        expected[p] = read(p)
        if digest(expected[p]) != e["after"]:
            raise SystemExit("Later changes to %s; refusing to overwrite them." % p)
        before = Path(e["backup"]).read_bytes() if e["before"] is not None else None
        if digest(before) != e["before"]:
            raise SystemExit("Backup damaged: %s" % e["backup"])
        updates[p] = before
    apply(updates,receipt.with_name("revert-receipt.json"),expected)
    receipt.unlink()
    log("Restored files from the last %s installation only." % faction)


def selfcheck():
    """Synthetic cache, multi-pack preservation, stale-revert and interrupted-write checks."""
    import struct
    from types import SimpleNamespace
    from unittest.mock import patch

    def texture(name):
        n = name.encode()
        return bytes([len(n)])+n+b"\0"*8+struct.pack("<H",1)+bytes([len(n)])+n+b"XET\0"+b"\0"*8

    def string(name):
        return bytes([len(name)])+name.encode()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cache, dwarf, elf = root/"asset.dat",root/"dwarves.big",root/archive_name("elves")
        model = string("m.w3d")+b"\0"*8+struct.pack("<H",1)+string("M.BODY")+b"HSEM"+struct.pack("<II",8,64)
        obj = string("m.w3d")+string("M.BODY")+struct.pack("<H",1)+string("base.tga")
        original = b"ALAE"+struct.pack("<III",1,4,2)+texture("base.tga")+texture("ducrafts.tga")+model*2+obj*2
        cache.write_bytes(original)
        dwarf.write_bytes(b"existing dwarf art")
        ops = {str(cache):[(('texture','elf.tga','base.tga','m.w3d','M.BODY'),None)]}
        with patch(__name__+".collect",return_value=({},ops)):
            try:
                prepare("elves")
            except SystemExit:
                pass
            else:
                raise AssertionError("empty pack accepted")
        with patch(__name__+".collect",return_value=({'test':b'elf art'},ops)):
            _, updates = prepare("elves")
        assert cache.read_bytes() == original
        assert texture("ducrafts.tga") in updates[cache]
        assert texture("base.tga") in updates[cache]
        assert updates[cache].count(string("elf.tga")) == 4  # texture+TEX and both object dependencies
        probe = AssetCache(str(cache))
        with patch("sagekit.formats.assetcache.W3DFile",return_value=SimpleNamespace(
                cache_entries=lambda:[("M.BODY",b"HSEM",100,200)])):
            assert len(probe.stale_entries("mock.w3d","m.w3d")) == 2
            probe.patch_model("mock.w3d","m.w3d")
            assert not probe.stale_entries("mock.w3d","m.w3d")
        assert probe.data.count(string("M.BODY")+b"HSEM"+struct.pack("<II",100,200)) == 2
        receipt = root/"elves/_install/receipt.json"
        updates[elf] = b"elf pack"
        assert apply(updates,receipt)
        assert not apply(updates,receipt)
        assert dwarf.read_bytes() == b"existing dwarf art"
        with patch.object(paths,"BUILD",tmp),patch(__name__+".game_running",return_value=False):
            after = cache.read_bytes()
            cache.write_bytes(after+b"later edit")
            try:
                revert_faction("elves",log=lambda _:None)
            except SystemExit:
                assert cache.read_bytes() == after+b"later edit" and elf.exists()
            else:
                raise AssertionError("revert overwrote later edits")
            cache.write_bytes(after)
            revert_faction("elves",log=lambda _:None)
        assert cache.read_bytes() == original and not elf.exists()
        original_atomic = atomic
        def fail_second(p,data):
            if p == elf:
                raise OSError("injected write failure")
            return original_atomic(p,data)
        with patch(__name__+".atomic",side_effect=fail_second):
            try:
                apply(updates,receipt)
            except OSError:
                pass
            else:
                raise AssertionError("injected failure did not run")
        assert cache.read_bytes() == original and not elf.exists()
        try:
            apply(updates,receipt,{cache:b"outdated",elf:None})
        except RuntimeError:
            pass
        else:
            raise AssertionError("stale preparation accepted")
    print("PASS: scoped cache/pack changes, revert guards, idempotence, rollback, stale preparation")


if __name__ == "__main__":
    selfcheck()
