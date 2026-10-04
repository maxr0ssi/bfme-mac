"""The Retina archive: stage, install, revert (never while the game runs); the duplicate scan.

    RotWK/!!!!!!!!!!!!!!sagekit-ui2x.big    items 2-4: EA's portrait and button pages at 2x, the
                                            tooltip textures at 2x with their movies' geometry
    RotWK/!!!!!!!!!!!!!!sagekit-icons.big   item 1: rebuilt at 2x for the factions it carries
                                            (sagekit/icons/install.py `rescale`); --revert
                                            rebuilds it at 1x

build/assets/_ui2x/installed.json records what is in the game; revert refuses an archive it did not
write. Every page lives in exactly one archive of ours: `dupes()` scans every staged and installed
*sagekit-*.big and the stage refuses a member ours shares with another.
"""
import glob
import json
import os
from pathlib import Path

from .. import paths
from ..formats.big import Archive, norm, pack
from ..formats.textures import compiled_path
from ..game import Install
from ..icons import install as icons
from ..install import apply, digest, read
from ..pipeline import game_running
from . import ARCHIVE, root
from .build import build
from .select import select
from .tooltip import build as tooltip


def live():
    return Path(paths.GAMEDIRS["rotwk"]) / ARCHIVE


def receipt():
    return Path(root()) / "installed.json"


def pow2(n):
    return n & (n - 1) == 0


def members():
    """{member: bytes} of items 2-4, built and checked, and the memory lines."""
    sel, skipped = select()
    for page in [p for p, s in sel.items() if not (pow2(s["width"]) and pow2(s["height"]))]:
        skipped[page] = "not a power of two (%dx%d)" % (sel[page]["width"], sel[page]["height"])
        del sel[page]
    spec = {p: dict(mips=s["mips"] + 1, rects=[dict(rect=r, kind="portrait" if min(r[2] - r[0], r[3] - r[1]) >= 100
                                                    else "button") for r in s["rects"]])
            for p, s in sel.items()}
    out, probs = build(spec)
    if probs:
        raise SystemExit("the 2x pages' checks fail (%s):\n  %s" % (root("checks.txt"), "\n  ".join(probs)))
    g = Install()
    files = {compiled_path(p, ".dds"): open(out[p], "rb").read() for p in sorted(out)}
    ea_bytes = {m: len(g.read(m)) for m in files}
    tips, line = tooltip()
    files.update(tips)
    with open(root("skipped.txt"), "w") as fh:
        fh.write("".join("%s: %s\n" % kv for kv in sorted(skipped.items())))
    added = sum(len(files[m]) - ea_bytes[m] for m in ea_bytes)
    tex = [m for m in tips if m.endswith(".tga")]
    from ..hud.apt import Apt
    apt = Apt()
    added_t = sum(len(tips[m]) - len(apt.read(m)) for m in tex)
    lines = ["items 2-3: %d pages at 2x, +%.1f MB (EA's %.1f MB)" % (len(ea_bytes), added / 1e6,
                                                                     sum(ea_bytes.values()) / 1e6),
             "item 4: %s, +%.2f MB" % (line, added_t / 1e6), "skipped: %d pages (%s)" % (len(skipped),
                                                                                     root("skipped.txt"))]
    return files, lines


def staged_archives():
    """{archive name: path}: what would be live after every staged pack installs: the game folder's
    *sagekit-*.big, each replaced by the newest staged copy of its name (a HUD 1x fallback and a
    per-faction release pack of the icons are alternatives, never installed beside the rest)."""
    out = {f: os.path.join(paths.GAMEDIRS["rotwk"], f) for f in os.listdir(paths.GAMEDIRS["rotwk"])
           if "sagekit-" in f and f.lower().endswith(".big")}
    staged = {}
    for p in glob.glob(os.path.join(paths.BUILD, "**", "_install", "**", "*sagekit-*.big"), recursive=True):
        name = os.path.basename(p)
        if os.sep + "1x" + os.sep in p or "sagekit-icons-" in name or not name.startswith("!"):
            continue
        if name not in staged or os.path.getmtime(p) > os.path.getmtime(staged[name]):
            staged[name] = p
    out.update(staged)
    return out


def dupes(archives):
    """{member: [archive names]} of every member more than one of the archives carries."""
    seen = {}
    for name, p in sorted(archives.items()):
        for m in Archive(p).index():
            seen.setdefault(norm(m), []).append(name)
    return {m: names for m, names in seen.items() if len(names) > 1}


def stage():
    files, lines = members()
    out = Path(root("_install", ARCHIVE))
    pack(sorted(files.items()), str(out))
    staged = Archive(str(out))
    assert all(staged.read(n) == d for n, d in files.items())
    icons_out = icons.rescale(2, "stage", out=root("_install", icons.SHARED))
    if icons_out:
        n = Archive(str(icons_out)).index()
        old = sum(len(Install().read(m)) for m in n)
        lines.append("item 1: %d icon pages at 2x, +%.1f MB" % (len(n), (os.path.getsize(icons_out) - old) / 1e6))
    arcs = staged_archives()
    arcs[ARCHIVE] = str(out)
    if icons_out:
        arcs[icons.SHARED] = str(icons_out)
    dup = dupes(arcs)
    ours = {m: v for m, v in dup.items() if ARCHIVE in v or icons.SHARED in v}
    lines.append("duplicate scan: %d archives, %d members in two or more (%d involve ui2x or icons)" % (
        len(arcs), len(dup), len(ours)))
    lines += ["  %s: %s" % (m, ", ".join(v)) for m, v in sorted(dup.items())[:40]]
    with open(root("summary.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    if ours:
        raise SystemExit("pages in two of our archives (above): refusing")
    print("Staged %s (%d members)%s" % (out, len(files), " and %s" % icons_out if icons_out else ""))
    return out, icons_out


def main(action, dry=False):
    if action != "stage" and game_running():
        raise SystemExit("Close the game first (it reads its archives at startup).")
    dest = live()
    rec = json.loads(receipt().read_text()) if receipt().exists() else None
    if dest.exists() and (rec is None or digest(dest.read_bytes()) != rec["sha256"]):
        raise SystemExit("%s changed since sagekit wrote it; refusing to touch it" % dest)
    if action == "revert":
        if dry:
            print("Dry run: would remove %s and rebuild the icon archive at 1x" % dest)
            return 0
        if dest.exists():
            apply({dest: None}, Path(root()) / "apply-receipt.json", {dest: read(dest)})
            receipt().unlink(missing_ok=True)
        if icons.scale_now() == 2:
            icons.rescale(1)
        print("Reverted: %s removed, the icon pages back at 1x; the game draws EA's sizes." % dest.name)
        return 0
    staged, _ = stage()
    if action == "stage":
        print("Nothing installed.")
        return 0
    data = staged.read_bytes()
    if dry:
        print("Dry run: would write %s (%d bytes) and rebuild the icon archive at 2x" % (dest, len(data)))
        return 0
    apply({dest: data}, Path(root()) / "apply-receipt.json", {dest: read(dest)})
    receipt().write_text(json.dumps(dict(sha256=digest(data)), indent=1) + "\n")
    icons.rescale(2)
    print("Installed: %s, and the icon pages at 2x." % dest)
    return 0
