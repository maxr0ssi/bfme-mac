"""The shared icon archive: one archive for every faction's icons, rebuilt on each install and revert.

    RotWK/!!!!!!!!!!!!!!sagekit-icons.big   the pages: EA's, with every installed faction's icons
                                            in their rects (fourteen '!': before every archive of
                                            ours and EA's, so its pages are the ones the game reads)

Pages serve several factions (87 of EA's 332 building pages do), so no faction ships a page of its
own: each faction's run leaves its crops and their rects (build/assets/<faction>/_icons/icons.json),
and this archive composes each page from EA's and every installed faction's crops, refusing a rect
two factions claim. The pages keep EA's names (at 2x, twice EA's size: sagekit/ui2x), so asset.dat
files them already: a texture's record holds no size or format (sagekit/texrecords.py). Every write
checks the live caches file every page it ships.
build/assets/_icons/shared.json records the archive's digest and its factions; revert takes one
faction out (the archive goes when none is left), refusing an archive it did not write.
"""
import json
import os
from pathlib import Path

from .. import paths, texrecords
from ..formats.big import Archive, pack
from ..formats.textures import compiled_path
from ..game import Install
from ..install import apply, digest, read
from ..pipeline import game_running
from . import root, shared_root

SHARED = "!!!!!!!!!!!!!!sagekit-icons.big"


def live():
    return Path(paths.GAMEDIRS["rotwk"]) / SHARED


def receipt():
    return Path(shared_root()) / "shared.json"


def installed():
    """The factions the archive in the game folder carries (refuses one this module did not write)."""
    dest = live()
    if not dest.exists():
        return []
    rec = json.loads(receipt().read_text()) if receipt().exists() else {}
    if digest(dest.read_bytes()) != rec.get("sha256"):
        raise SystemExit("%s changed since sagekit wrote it; refusing to replace it" % dest)
    return rec["factions"]


def reviewed(faction):
    """The faction's manifest, if its last run's page checks passed."""
    r = root(faction)
    checks = os.path.join(r, "checks.txt")
    if not os.path.exists(checks) or not os.path.exists(os.path.join(r, "icons.json")):
        raise SystemExit("%s: no icon run: python3 -m sagekit icons %s" % (faction, faction))
    if any(line.startswith("FAIL") for line in open(checks)):
        raise SystemExit("%s: its page checks failed (%s)" % (faction, checks))
    return json.load(open(os.path.join(r, "icons.json")))


def members(factions, scale=1):
    """{archive member: bytes}: every page any of the factions draws on, composed and checked; at
    scale 2 twice EA's size (sagekit/ui2x: our crops from the 4x renders, EA's images upscaled)."""
    from .cli import compose
    g = Install()
    by_page, owner, big = {}, {}, {}
    for f in sorted(factions):
        for name, m in reviewed(f).items():
            rect = tuple(m["rect"])
            for other, (orect, oname) in owner.get(m["page"], {}).items():
                if rect[0] < orect[2] and orect[0] < rect[2] and rect[1] < orect[3] and orect[1] < rect[3]:
                    raise SystemExit("%s %s and %s %s claim the same pixels of %s" % (f, name, other, oname, m["page"]))
            owner.setdefault(m["page"], {})[f + ":" + name] = (rect, name)
            by_page.setdefault(m["page"], []).append((rect, os.path.join(root(f), "crops", "%s_new.png" % name)))
            big.setdefault(m["page"], []).append((rect, os.path.join(root(f), "crops", "%s_new@4x.png" % name), m["kind"]))
    files = {}
    if scale == 2:
        from ..ui2x.icons import pages2x
        files = pages2x(big)
    for page, crops in sorted(by_page.items()) if scale == 1 else ():
        _, dds, probs = compose(g, page, crops, os.path.join(shared_root(), "pages"))
        if probs:
            raise SystemExit("%s: %s" % (page, "; ".join(probs)))
        files[compiled_path(page, ".dds")] = open(dds, "rb").read()
    active = Install(pristine=False)
    for member in files:
        owner_archive = active.owner(member)
        name = Path(owner_archive.path).name if owner_archive else ""
        if name and name != SHARED and name.lower() < SHARED.lower():
            raise SystemExit("%s comes from %s, which the game reads before ours" % (member, name))
    return files


def build(factions, scale=1, out=None):
    """The archive for `factions` staged under build/assets/_icons/ (or `out`); its path, or None."""
    if not factions:
        return None
    files = members(factions, scale)
    ok, line = texrecords.check(list(files), SHARED)
    if not ok:
        raise SystemExit(line)
    out = Path(out or Path(shared_root()) / "_install" / SHARED)
    pack(sorted(files.items()), str(out))
    staged = Archive(str(out))
    assert all(staged.read(n) == d for n, d in files.items())
    print("Staged %s: %d pages at %dx for %s" % (out, len(files), scale, ", ".join(sorted(factions))))
    return out


def scale_now():
    """The scale of the installed archive (1 unless sagekit ui2x installed it at 2)."""
    return json.loads(receipt().read_text()).get("scale", 1) if receipt().exists() else 1


def put(staged, want, scale, dry, verb):
    """Write (or, staged None, remove) the live archive and its receipt."""
    dest = live()
    data = staged.read_bytes() if staged else None
    if dry:
        print("Dry run: would %s %s (%s, %dx)" % ("write" if data else "remove", dest, ", ".join(want) or "no faction",
                                                 scale))
        return 0
    apply({dest: data}, Path(shared_root()) / "apply-receipt.json", {dest: read(dest)})
    if data is None:
        receipt().unlink(missing_ok=True)
    else:
        receipt().write_text(json.dumps(dict(sha256=digest(data), factions=want, scale=scale), indent=1) + "\n")
    print("%s; the icon archive carries %s at %dx." % (verb, ", ".join(want) or "nothing (removed)", scale))
    if data is not None:
        print(texrecords.verify(list(Archive(str(dest)).index()), texrecords.live_caches(), SHARED))
    return 0


def rescale(scale, action="install", dry=False, out=None):
    """The installed factions' archive again at `scale` (sagekit ui2x --install 2, --revert 1);
    stage: only build it (at `out`). Returns the staged path (None: no faction installed)."""
    want = installed()
    staged = build(want, scale, out)
    if action != "stage" and want:
        put(staged, want, scale, dry, "Icons rebuilt")
    return staged


def main(faction, action, dry=False):
    if action != "stage" and game_running():
        raise SystemExit("Close the game first (it reads its archives at startup).")
    now = installed()
    want = sorted(set(now) - {faction}) if action == "revert" else sorted(set(now) | {faction})
    if faction == "all":                    # stage only: every faction with an icon run
        if action != "stage":
            raise SystemExit("'all' only stages; install and revert name a faction")
        want = sorted(f for f in os.listdir(paths.BUILD) if os.path.exists(os.path.join(root(f), "icons.json")))
    if action == "revert" and faction not in now:
        raise SystemExit("%s: its icons are not installed" % faction)
    scale = scale_now()
    staged = build(want, scale)
    if action == "stage":
        print("Nothing installed.")
        return 0
    return put(staged, want, scale, dry, "%s %s" % ("Reverted" if action == "revert" else "Installed", faction))


def pack_archive(faction):
    return "!!!!!!!!!!!!!!sagekit-icons-%s.big" % faction


def release(faction):
    """For sagekit/packbuild.py: (archive, {}, {}, {member: set()}) of the faction's own icon pages,
    or None when it has no icon run. A release pack carries one faction, so its pages go in an
    archive of its own; that is only sound while no page holds two factions' icons, which this
    refuses (the shared archive above merges them for a local install)."""
    if not os.path.exists(os.path.join(root(faction), "icons.json")):
        return None
    mine = {m["page"] for m in reviewed(faction).values()}
    for other in sorted(os.listdir(paths.BUILD)):
        if other != faction and os.path.exists(os.path.join(root(other), "icons.json")):
            both = mine & {m["page"] for m in json.load(open(os.path.join(root(other), "icons.json"))).values()}
            if both:
                raise SystemExit("%s and %s both draw on %s: a pack per faction cannot carry those pages" % (
                    faction, other, ", ".join(sorted(both))))
    files = members([faction])
    out = Path(root(faction)) / "_install" / pack_archive(faction)
    pack(sorted(files.items()), str(out))
    return out, {}, {}, {m: set() for m in files}
