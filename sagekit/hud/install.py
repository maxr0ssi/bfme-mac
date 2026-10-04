"""The HUD archive: stage, install, revert (never while the game runs).

    RotWK/!!!!!!!!!!!!!!sagekit-hud.big   our palantir textures (and, for 2x, the movies' doubled
                                          geometry); fourteen '!' sort it before EA's apt/*.big and
                                          __patch202.big, so its members are the ones the game reads

`--install` ships 2x (twice the texels, geometry doubled to match); `--install --1x` ships EA's sizes
only, no geometry: the fallback if 2x ever draws wrong. `--factions --install` ships the 2x pack plus
one palantir frame per faction (sagekit/hud/factions.py) in the same archive, replacing it;
`--factions --revert` puts the Good/Evil 2x pack back. build/assets/_hud/installed.json records
what is in the game; revert refuses an archive it did not write.
"""
import json
import os
from pathlib import Path

from .. import paths
from ..formats.big import Archive, pack
from ..install import apply, digest, read
from ..pipeline import game_running
from . import ARCHIVE, root
from .apt import Apt
from .build import check, files


def live():
    return Path(paths.GAMEDIRS["rotwk"]) / ARCHIVE


def receipt():
    return Path(root()) / "installed.json"


def stage(res):
    """build/assets/_hud/_install/<res>/!!!...sagekit-hud.big from the checked build; its path.
    res: "1x", "2x" or "factions" (the 2x pack and the faction frames)."""
    apt = Apt()
    new = set()
    if res == "factions":
        from . import factions
        lines, bad = factions.check(apt)
        members = {m: open(p, "rb").read() for m, p in factions.files().items()}
        new = factions.new_members()
        where = factions.froot("checks.txt")
    else:
        lines, bad = check(apt)
        members = {m: open(p, "rb").read() for m, p in files(res).items()}
        where = os.path.join(root(), "checks.txt")
    if bad:
        raise SystemExit("the HUD build's checks fail (%s):\n%s" % (
            where, "\n".join(x for x in lines if x.startswith("FAIL"))))
    if not members:
        raise SystemExit("nothing built: python3 -m sagekit hud")
    for m in members:
        if apt.owner(m) is None and m.lower() not in new:
            raise SystemExit("%s: EA has no such member; refusing to add new files" % m)
    out = Path(root()) / "_install" / res / ARCHIVE
    pack(sorted(members.items()), str(out))
    staged = Archive(str(out))
    assert all(staged.read(n) == b for n, b in members.items())
    print("Staged %s (%s): %d textures, %d geometry files" % (
        out, res, sum(m.endswith(".tga") for m in members), sum(m.endswith(".ru") for m in members)))
    return out


def main(action, res="2x", dry=False):
    if action != "stage" and game_running():
        raise SystemExit("Close the game first (it reads its archives at startup).")
    dest = live()
    rec = json.loads(receipt().read_text()) if receipt().exists() else None
    if dest.exists() and (rec is None or digest(dest.read_bytes()) != rec["sha256"]):
        raise SystemExit("%s changed since sagekit wrote it; refusing to touch it" % dest)
    if action == "revert" and res == "factions":
        if not dest.exists() or (rec or {}).get("res") != "factions":
            raise SystemExit("the faction palantir is not installed (installed: %s)" % (
                (rec or {}).get("res") if dest.exists() else "nothing"))
        print("Reverting the faction palantir to the Good/Evil 2x pack.")
        action, res = "install", "2x"
    if action == "revert":
        if not dest.exists():
            raise SystemExit("the HUD is not installed")
        if dry:
            print("Dry run: would remove %s" % dest)
            return 0
        apply({dest: None}, Path(root()) / "apply-receipt.json", {dest: read(dest)})
        receipt().unlink(missing_ok=True)
        print("Reverted: %s removed; the game draws EA's palantir." % dest.name)
        return 0
    staged = stage(res)
    if action == "stage":
        print("Nothing installed.")
        return 0
    data = staged.read_bytes()
    if dry:
        print("Dry run: would write %s (%s, %d bytes)" % (dest, res, len(data)))
        return 0
    apply({dest: data}, Path(root()) / "apply-receipt.json", {dest: read(dest)})
    receipt().write_text(json.dumps(dict(sha256=digest(data), res=res), indent=1) + "\n")
    print("Installed the HUD (%s): %s" % (res, dest))
    return 0
