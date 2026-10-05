"""The cah pack: Create-a-Hero choices (assets/cah, docs/CAH.md), staged, installed and reverted
like a unit. Every class folder under assets/cah is built on its own; the pack merges them all into
ONE archive, composing their INI fragments onto EA's files in class-name order.

    python3 -m assets.cah.<class>.build                # each class: build and check
    python3 -m sagekit.units.cah --stage               # compose, lint, the archive into _install/
    python3 -m sagekit.units.cah --install [--dry-run]
    ... --stage | --install --classes dwarf,men_cg     # only those classes (test one class at a time)
    python3 -m sagekit.units.cah --revert  [--dry-run]

    RotWK/!!!!!!!!!!!sagekit-cah.big      every class's part models (rigid, hidden until picked, on the
                                          hero's bones: assets/cah/kit/attach.py), the sheets they draw
                                          and their masks, and EA's 2.02 Create-a-Hero INI files that
                                          change, EA's text first and ours appended
    RotWK/!!!!!!!!!!!!!sagekit-units.big  the shared housecolor.ini (sagekit/units/install.py): EA's
                                          plus every installed unit's lines, ours the two masks
    asset.dat                             our models filed under their own names, our textures
                                          registered; EA's records untouched

A class still on the old design (copies of EA's skins under SK* names, drawn by every hero through
createaheromodels.inc) is refused: Max's rule is that EA's heroes stay EA's (docs/CAH.md).

Revert removes the archive, takes our records out of asset.dat (records.py; every other record
byte for byte) and rebuilds the shared house-colour archive without our lines. EA's models, INI and
records are never edited, so a revert leaves the game as EA's plus whatever else is installed.
Every player in a LAN game needs the same pack (the INI is in the multiplayer check).
"""
import argparse
import json
from pathlib import Path

from .. import paths
from ..formats.assetcache import AssetCache
from ..formats.big import Archive, pack
from ..formats.textures import compiled_path
from ..game import Install
from ..install import apply, read, stage_ops
from ..pipeline import game_running
from . import Folder, load, records
from .install import SHARED, installed, live_dir, shared_receipt, shared_update
from .build import sha

UID = "cah/pack"
TEXTURE_LIKE = {"sheet": "chdw_dw_of3d_hlmt_06.tga", "mask": "hc_chdw_tm_03.tga"}   # asset.dat records to copy


def recipe(classes=None):
    """The pack, its build folder and its class specs: every class, or only the names in `classes`."""
    from assets.cah.pack import design
    u = load(UID)
    specs = design.classes()
    if classes:
        unknown = set(classes) - {s.NAME for s in specs}
        if unknown:
            raise SystemExit("cah: no class %s (classes: %s)" % (", ".join(sorted(unknown)), ", ".join(s.NAME for s in specs)))
        specs = [s for s in specs if s.NAME in classes]
    return u, Folder(u), specs


def class_dir(spec):
    return Path(paths.BUILD) / "cah" / spec.NAME


def attached(spec):
    """(built part models, fragment) of a class on the parts-on-bones design."""
    from assets.cah.kit import attach
    built, frag, _ = attach.load(spec)
    return built, frag


def check_design(specs):
    old = [s.NAME for s in specs if not getattr(s, "ATTACH", None)]
    if old:
        raise SystemExit("cah: %s still copy EA's hero models (every hero would draw ours); convert them to parts on "
                         "bones (ATTACH, assets/cah/kit/attach.py) or leave them out with --classes" % ", ".join(old))


def shipped_models(spec):
    """{our model name: its bytes} of a class."""
    return {n: d for n, (_, _, d) in attached(spec)[0].items()}


def shipped_sheets(spec):
    """{sheet: mask} of the sheets the class's part models draw."""
    from assets.cah.kit import attach
    used = set(attach.sheets(attached(spec)[0]))
    return {s: m for s, m in spec.MASKS.items() if s.lower() in used}


def compose_ini(specs, b):
    """Every class's fragment composed onto EA's files, linted, written into the pack's work/ini."""
    from assets.cah.kit import ini
    from ..formats.w3d import W3DFile
    from assets.cah.kit.attach_lint import check
    ea = ini.read_all()
    frags = [attached(s)[1] for s in specs]
    ours = ini.compose(ea, frags)
    models = {n.lower(): set(W3DFile(d).meshes) for s in specs for n, d in shipped_models(s).items()}
    report = ini.check(ea, ours, models, [], frags)
    for s in specs:
        report["attach_" + s.NAME] = check(s, ea, ours, attached(s)[0])
    written, changed = ini.write(ours, ea, b.work / "ini", frags)
    return written, report


def members(specs, b):
    """{archive member: bytes}: every class's models, sheets and masks, and the composed INI."""
    if not specs:
        raise SystemExit("cah: no class folder under assets/cah")
    files = {}
    from assets.cah.kit import attach
    for spec in specs:
        report = attach.load(spec)[2]
        if report.get("over_budget"):
            raise SystemExit("cah: %s parts over their vertex budget: %s" % (spec.NAME, report["over_budget"]))
        work = class_dir(spec) / "work"
        for ours, data in shipped_models(spec).items():
            files["art\\w3d\\%s\\%s.w3d" % (ours.lower()[:2], ours.lower())] = data
        for sheet, mask in shipped_sheets(spec).items():
            files[compiled_path(sheet, ".dds")] = (work / (sheet.lower()[:-4] + ".dds")).read_bytes()
            files[compiled_path(mask, ".tga")] = (work / mask.lower()).read_bytes()
    written, _ = compose_ini(specs, b)
    for member in written.values():
        if member in files:
            raise SystemExit("cah: %s twice" % member)
        files[member] = (b.work / "ini" / member.replace("\\", "/")).read_bytes()
    from ..texbake import bake          # house-colour masks ship with their mips built (sagekit/texbake.py)
    from ..texslim import slim          # opaque DXT5 ships as the identical DXT1 (sagekit/texslim.py)
    return slim(bake(files, log=lambda s: None), log=lambda s: None)


def cache_ops(specs):
    """asset.dat ops: each part model filed like the class's design model (its timestamp and cache),
    each sheet and mask registered like an EA CaH sheet and mask."""
    ops = [("model", ours.lower() + ".w3d", s.DESIGN + ".w3d", "own") for s in specs for ours in shipped_models(s)]
    for s in specs:
        for sheet, mask in shipped_sheets(s).items():
            ops += [("texture", sheet.lower(), TEXTURE_LIKE["sheet"], None, None),
                    ("texture", mask.lower(), TEXTURE_LIKE["mask"], None, None)]
    return ops


def owned(u, b):
    dest = live_dir() / u.archive
    if not dest.exists():
        return False
    receipt = b.stage / "unit.json"
    if receipt.exists() and json.loads(receipt.read_text())["sha256"] == sha(dest.read_bytes()):
        return True
    raise SystemExit("%s is in the game folder but no receipt of this pack installed it" % dest)


def model_source(specs):
    from assets.cah.kit import attach
    by_name = {ours.lower() + ".w3d": str(attach.attach_dir(s) / (ours.lower() + ".w3d")) for s in specs for ours in shipped_models(s)}
    return lambda name: by_name[name.lower()]


def stage(u, b, specs):
    """Check the build, pack the archive into _install/, and prove the asset.dat records come
    back as they were on a copy of each cache. Nothing in the game changes."""
    check_design(specs)
    names = [m.lower() for s in specs for m in shipped_models(s)]
    texts = [t.lower() for s in specs for kv in shipped_sheets(s).items() for t in kv]
    for kind, seen in (("model", names), ("texture", texts)):
        dup = {x for x in seen if seen.count(x) > 1}
        if dup:
            raise SystemExit("cah: two classes ship the %s %s" % (kind, sorted(dup)))
    files = members(specs, b)
    g, active, mine = Install(), Install(pristine=False), owned(u, b)
    for member in files:
        owner = active.owner(member)
        if owner and Path(owner.path).name != u.archive and Path(owner.path).name.lower() < u.archive.lower():
            raise SystemExit("cah: %s comes from %s, which the game reads before ours" % (member, owner.path))
        if not mine and member.startswith("art\\") and g.owner(member):
            raise SystemExit("cah: EA ships %s already" % member)
    if not mine:
        for name in [n + ".w3d" for n in names] + texts:
            if any((c.has_model(name) if name.endswith(".w3d") else c.has_texture(name)) for c in g.asset_caches().values()):
                raise SystemExit("cah: asset.dat files %s already (another install?)" % name)
    routed = g.route_cache_ops(cache_ops(specs))
    where = model_source(specs)
    for live, ops in routed.items():                    # stage and revert on copies: exact round trip
        cache, pristine = AssetCache(live), AssetCache(live + ".orig")
        if mine:
            continue
        staged = records.staged(cache, ops, where)
        if records.unstage(staged, pristine, ops, where) != cache.data:
            raise SystemExit("cah: reverting %s would not give back today's records" % live)
    b.stage.mkdir(parents=True, exist_ok=True)
    archive = b.stage / u.archive
    pack(sorted(files.items()), str(archive))
    staged_archive = Archive(str(archive))
    assert all(staged_archive.read(n) == d for n, d in files.items())
    (b.stage / "staged.json").write_text(json.dumps(dict(sha256=sha(archive.read_bytes()), members=sorted(files),
                                                         caches={k: v for k, v in routed.items()}), indent=1) + "\n")
    print("Staged %s (%s): %s (%d members, %d bytes); INI composed and linted; asset.dat round trip checked; "
          "nothing installed." % (UID, ", ".join(s.NAME for s in specs), archive, len(files), archive.stat().st_size))
    return archive, files, routed


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


def install(dry=False, classes=None):
    if game_running():
        raise SystemExit("Close the game before installing.")
    u, b, specs = recipe(classes)
    archive, files, routed = stage(u, b, specs)
    dest, data = live_dir() / u.archive, archive.read_bytes()
    updates, expected = {}, {dest: read(dest), live_dir() / SHARED: read(live_dir() / SHARED)}
    if owned(u, b):
        if dest.read_bytes() != data:
            raise SystemExit("cah: another build of the pack is installed; --revert it first")
        print("cah is installed already; composing the shared house-colour INI.")
    else:
        updates[dest] = data
        for live, ops in routed.items():
            cache = AssetCache(live)
            expected[Path(live)] = cache.data
            stage_ops(cache, [(op, model_source(specs)) for op in ops])
            updates[Path(live)] = cache.data
    units = installed(include=[UID])
    shared, ini = shared_update(units)
    updates.update(shared)
    if dry:
        print("Dry run: would write %s" % ", ".join(str(p) for p in updates))
        return
    _commit(b, updates, expected, units)
    (b.stage / "unit.json").write_text(json.dumps(dict(sha256=sha(data), caches=routed), indent=1) + "\n")
    if Install(pristine=False).read("data\\ini\\housecolor.ini") != ini:
        raise SystemExit("Installed, but another archive's housecolor.ini shadows the shared one")
    print("Installed the cah pack (%d members); the house-colour INI carries %s." % (len(files), ", ".join(units)))


def revert(dry=False):
    if game_running():
        raise SystemExit("Close the game before reverting.")
    u, b, specs = recipe()
    dest = live_dir() / u.archive
    if not owned(u, b):
        raise SystemExit("The cah pack is not installed.")
    shipped = Archive(str(dest))
    by_name = {}
    for name in shipped.index():
        if name.startswith("art\\w3d\\") and name.endswith(".w3d"):
            by_name[name.split("\\")[-1]] = shipped.read(name)
    receipt = json.loads((b.stage / "unit.json").read_text())
    if receipt.get("caches"):                       # the ops the install applied, per cache
        routed = {live: [tuple(op) for op in ops] for live, ops in receipt["caches"].items()}
    else:                                           # an install from before the receipt kept them: the copies design
        texs = [n.split("\\")[-1][:-4] + ".tga" for n in shipped.index() if n.startswith("art\\compiledtextures\\")]
        ops = [("model", n, "ch" + n[2:]) for n in sorted(by_name)] + \
              [("texture", t, TEXTURE_LIKE["mask" if t.startswith("hc_") else "sheet"], None, None) for t in sorted(texs)]
        routed = Install().route_cache_ops(ops)
    updates, expected = {dest: None}, {dest: read(dest), live_dir() / SHARED: read(live_dir() / SHARED)}
    for live, ops in routed.items():
        cache, pristine = AssetCache(live), AssetCache(live + ".orig")
        expected[Path(live)] = cache.data
        updates[Path(live)] = records.unstage(cache, pristine, ops, lambda m: by_name[m.lower()])
    shared, _ = shared_update(installed(exclude=[UID]))
    updates.update(shared)
    if dry:
        print("Dry run: would write %s" % ", ".join("%s (%s)" % (p, "remove" if d is None else "%d bytes" % len(d))
                                                     for p, d in updates.items()))
        return
    _commit(b, updates, expected, installed(exclude=[UID]))
    (b.stage / "unit.json").unlink(missing_ok=True)
    print("Removed the cah pack; its asset.dat records are gone, every other record untouched.")


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m sagekit.units.cah", description=__doc__.split("\n")[0])
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", action="store_true")
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--revert", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--classes", type=lambda v: [c for c in v.split(",") if c], metavar="A,B",
                   help="--stage / --install only these class folders (default: all)")
    a = p.parse_args(argv)
    if a.classes and a.revert:
        p.error("--revert takes the installed archive's records; it has no --classes")
    if a.stage:
        stage(*recipe(a.classes))
    elif a.install:
        install(a.dry_run, a.classes)
    else:
        revert(a.dry_run)


if __name__ == "__main__":
    main()
