"""Stage, install, revert and report the shared FX archive; what the faction installs ask of it.

    build/assets/_fx/_install/<ARCHIVE>     the staged archive
    build/assets/_fx/_install/staged.json   its digest, its members' digests, per faction its counts
    build/assets/_fx/_install/receipt.json  the last installation (sagekit/install.py apply)

The archive ships the three shared files and nothing else: fxparticlesystem.ini (EA's, sagekit's
fire systems, every faction's tints), fxlist.ini and object\\system\\system.ini. The faction packs
ship none of them; their own structure INIs carry their fire moves (compose.structure_ops). So a
faction pack whose fire burns a Sagekit system needs this archive in the game: `requires` refuses a
faction install without it, and `revert` refuses while an installed pack still needs it. Install the
FX archive first, then the faction packs. (Packs installed before 2026-10-04 carry their own copy
of fxparticlesystem.ini, EA's plus the fire systems; this archive sorts before them and wins.)
"""
import json
import re
from pathlib import Path

from .. import paths
from ..formats.big import Archive, pack
from ..game import Install
from ..install import apply, digest, read, revert_receipt
from ..pipeline import game_running
from . import ARCHIVE, blocks, checks, compose, plan

ROOT = Path(paths.BUILD) / "_fx"
STAGE = ROOT / "_install"


class Without(Install):
    """The game as it reads its archives without the FX archive (every other archive of ours in)."""

    def __init__(self):
        super().__init__(pristine=False)

    def archives(self):
        return [a for a in super().archives() if Path(a.path).name != ARCHIVE]


def live():
    return Path(paths.GAMEDIRS["rotwk"]) / ARCHIVE


BONE_SYS = re.compile(r"^[ \t]*ParticleSysBone[ \t]*=?[ \t]*\S+[ \t]+(Sagekit\w+)", re.I | re.M)


def named(files):
    """{lower-case Sagekit system names} the INIs among files {member: bytes} burn."""
    out = set()
    for m, data in files.items():
        if m.lower().endswith(".ini"):
            out |= {n.lower() for n in BONE_SYS.findall(data.decode("latin-1"))}
    return out


def staged_packs():
    """{faction: Archive} of the staged faction packs (build/assets/<faction>/_install)."""
    from ..install import archive_name
    out = {}
    for d in sorted(Path(paths.BUILD).iterdir()):
        a = d / "_install" / archive_name(d.name)
        if a.exists():
            out[d.name] = Archive(str(a))
    return out


def compose_all(recipes=None):
    g, active = Install(), Without()
    recipes = recipes or plan.recipes()
    shipped, base, plans = compose.compose(g, active, recipes)
    r = checks.run(shipped, base, plans, g)
    for member in shipped:
        for a in active.archives():
            name = Path(a.path).name
            if paths.is_ours(name) and member in a and not (member == plan.PS_MEMBER and name.startswith("!!!!!!!!!!!sagekit-")):
                r.check("%s: no other archive of ours ships it" % member, False, name)
    defined = set(blocks.systems(shipped[plan.PS_MEMBER]))
    counts = {}
    for f, a in staged_packs().items():
        files = {m: a.read(m) for m in a.index() if m.endswith(".ini")}
        if plan.PS_MEMBER in files:                 # staged before the shared archive took the file over
            r.info("staged %s pack predates the FX archive (ships fxparticlesystem.ini): restage it with "
                   "python3 -m sagekit install %s --check" % (f, f))
            continue
        r.check("staged %s pack ships none of the FX archive's files" % f, not (set(files) & set(shipped)),
                ", ".join(sorted(set(files) & set(shipped))))
        missing = sorted(named(files) - defined)
        r.check("every Sagekit system the staged %s pack burns is defined here" % f, not missing, ", ".join(missing))
        rec = recipes.get(f)
        if rec is not None and rec.structures:
            n = sum(len(re.findall(r"ParticleSysBone[ \t]*=?[ \t]*\S+[ \t]+Sagekit%s" % rec.tag, d.decode("latin-1"), re.I))
                    for d in files.values())
            counts[f] = n
            r.check("staged %s pack burns its fire in its colours (%d ParticleSysBone lines)" % (f, n), n > 0,
                    "restage it: python3 -m sagekit install %s --check" % f)
    return g, active, shipped, base, plans, counts, r


def stage(recipes=None, quiet=False):
    """Compose, check and pack the archive into build/assets/_fx/_install; nothing in the game changes."""
    g, active, shipped, base, plans, counts, r = compose_all(recipes)
    STAGE.mkdir(parents=True, exist_ok=True)
    (STAGE / "checks.txt").write_text(r.text() + "\n")
    if r.failed:
        print(r.text())
        raise SystemExit("fx: %d checks failed; nothing staged (build/assets/_fx/_install/checks.txt)" % r.failed)
    files = {m: t.encode("latin-1") for m, t in shipped.items()}
    archive = STAGE / ARCHIVE
    pack(sorted(files.items()), str(archive))
    staged = Archive(str(archive))
    assert all(staged.read(m) == d for m, d in files.items())
    record = dict(sha256=digest(archive.read_bytes()), members={m: digest(d) for m, d in files.items()},
                  systems=sorted(blocks.systems(shipped[plan.PS_MEMBER])),
                  factions={p.r.faction: dict(systems=len(p.systems), fxlists=len(p.fxlists), modules=len(p.modules),
                                              bones=counts.get(p.r.faction)) for p in plans})
    (STAGE / "staged.json").write_text(json.dumps(record, indent=1) + "\n")
    if not quiet:
        print(r.text())
        for p in plans:
            print("%-9s %3d systems, %2d FX lists, %2d spell book modules; building fire and smoke: %s" % (
                p.r.faction, len(p.systems), len(p.fxlists), len(p.modules),
                ("%d lines in its staged pack" % counts[p.r.faction]) if counts.get(p.r.faction) else
                "not staged" if p.r.structures else "EA's"))
        print("Staged %s (%d members, %d bytes); nothing installed." % (archive, len(files), archive.stat().st_size))
    return archive, record


def installed_record():
    """The staged record of the archive in the game folder, or None when none is there. Refuses an
    archive this module did not install."""
    dest = live()
    if not dest.exists():
        return None
    rec = STAGE / "installed.json"
    if rec.exists():
        data = json.loads(rec.read_text())
        if data["sha256"] == digest(dest.read_bytes()):
            return data
    raise SystemExit("%s is in the game folder but no receipt of sagekit.fx installed it" % dest)


def install(dry=False):
    if game_running():
        raise SystemExit("Close the game before installing.")
    archive, record = stage(quiet=True)
    dest = live()
    data = archive.read_bytes()
    current = installed_record()
    if current and current["sha256"] == record["sha256"]:
        print("The FX archive is installed already, as staged.")
        return
    if dry:
        print("Dry run: would write %s (%d bytes)" % (dest, len(data)))
        return
    apply({dest: data}, STAGE / "receipt.json", {dest: read(dest)})
    (STAGE / "installed.json").write_text(json.dumps(record, indent=1) + "\n")
    if Install(pristine=False).read(plan.PS_MEMBER) != Archive(str(dest)).read(plan.PS_MEMBER):
        raise SystemExit("Installed, but another archive's fxparticlesystem.ini shadows ours")
    print("Installed %s: %s." % (ARCHIVE, ", ".join("%s %d systems" % (f, v["systems"]) for f, v in record["factions"].items())))


def needing():
    """Installed faction packs whose fire burns a Sagekit system their own INIs do not define."""
    out = []
    for f in sorted(Path(paths.GAMEDIRS["rotwk"]).glob("!!!!!!!!!!!sagekit-*.big")):
        a = Archive(str(f))
        files = {m: a.read(m) for m in a.index() if m.endswith(".ini")}
        own = set(blocks.systems(files[plan.PS_MEMBER].decode("latin-1"))) if plan.PS_MEMBER in files else set()
        if named(files) - own:
            out.append(f.name)
    return out


def revert(dry=False):
    if game_running():
        raise SystemExit("Close the game before reverting.")
    if installed_record() is None:
        raise SystemExit("The FX archive is not installed.")
    need = needing()
    if need:
        raise SystemExit("These packs burn systems only the FX archive defines; revert them first: %s" % ", ".join(need))
    if dry:
        print("Dry run: would restore %s from the receipt" % live())
        return
    revert_receipt(STAGE / "receipt.json")
    (STAGE / "installed.json").unlink(missing_ok=True)
    print("Removed %s." % ARCHIVE)


def status():
    rec = installed_record()
    staged = json.loads((STAGE / "staged.json").read_text()) if (STAGE / "staged.json").exists() else None
    print("installed: %s" % ("yes, %s" % rec["sha256"][:12] if rec else "no"))
    print("staged:    %s" % ("%s%s" % (staged["sha256"][:12], " (installed)" if rec and rec["sha256"] == staged["sha256"] else "")
                             if staged else "no"))
    print("packs needing it: %s" % (", ".join(needing()) or "none"))


def requires(faction, files):
    """Refuse a faction install whose fire burns a Sagekit system the installed FX archive does not
    define (sagekit/install.py calls this before writing anything)."""
    names = named(files)
    if not names:
        return
    have = set()
    if live().exists():
        installed_record()
        have = set(blocks.systems(Archive(str(live())).read(plan.PS_MEMBER).decode("latin-1")))
    missing = sorted(names - have)
    if missing:
        raise SystemExit("%s burns %d particle systems the FX archive defines (%s...): install it first "
                         "(python3 -m sagekit.fx --install)" % (faction, len(missing), missing[0]))
