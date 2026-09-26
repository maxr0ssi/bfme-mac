#!/usr/bin/env python3
"""Build the group pack: one add-on .big whose INI copies override the game's own.

Everyone who plays together installs the same pack, so settings that multiplayer checks stay
identical across machines (MULTIPLAYER.md). The pack is generated from each player's own install
- the repo carries only the edits below, never EA's files.

    tools/make_group_pack.py rotwk            build build/group-pack/rotwk/install/<PACK_NAME>
    scripts/install-mod.sh rotwk build/group-pack/rotwk/install      install it (--revert undoes)

How it overrides: SAGE loads every .big in the game folder in case-insensitive name order and the
first archive to provide a path wins (that is why the HD Edition starts with "!!!!!!!!" and patch
2.02 with "__"). PACK_NAME sorts before all of them. Each INI is copied from whichever archive the
game currently takes it from, so the pack starts from exactly what you play now.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIGTOOL = os.path.join(HERE, "bigtool.py")
PACK_NAME = "!!!!!!!!!!group-pack.big"   # ten "!" beat the HD Edition's eight
GAMEDIRS = {
    "rotwk": "prefixes/w10/drive_c/Program Files (x86)/Electronic Arts/RotWK",
    "bfme2": "prefixes/w10/drive_c/Program Files (x86)/Electronic Arts/BFME2",
}

# (member, block header regex or None for anywhere, key, new value). Each must hit at least once.
EDITS = [
    # Particles on screen at once: patch 2.02's own UltraHigh value (EA shipped 3000). 10000 was
    # tried and big battles dropped frames; the engine's particle skipping below 20 FPS (EA's
    # ParticleSkipMask in the Medium/Low DynamicGameLOD blocks) is left as EA set it.
    (r"data\ini\gamelod.ini", r"StaticGameLOD\s*=\s*UltraHigh", "MaxParticleCount", "4000"),
    # Heat shimmer over fires: it copies the whole screen every frame while any fire is on screen,
    # which is exactly when battles slow down, and it is barely visible. Off pending a measurement.
    (r"data\ini\gamelod.ini", r"StaticGameLOD\s*=\s*UltraHigh", "UseHeatEffects", "No"),
    # Zoom out further: EA 300, patch 2.02 540. The limit is draw calls, not pixels: the frame rate
    # is bound by Wine's render thread (every draw call crosses into 64-bit OpenGL), and zooming out
    # draws more units, trees and buildings - 1000 made big battles unplayable, 700 is measured fine.
    (r"data\ini\gamedata.ini", None, "DefaultCameraMaxHeight", "700.0"),
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("failed: %s\n%s" % (" ".join(cmd), r.stderr[:2000]))
    return r.stdout


def members(archive):
    return {line.split(None, 1)[1].lower() for line in run([sys.executable, BIGTOOL, "list", archive]).splitlines()
            if len(line.split(None, 1)) == 2}


def source_archive(gamedir, member):
    """The archive the game takes `member` from: first in case-insensitive name order."""
    for name in sorted((f for f in os.listdir(gamedir) if f.lower().endswith(".big")), key=str.lower):
        if name == PACK_NAME:
            continue
        path = os.path.join(gamedir, name)
        if member.lower() in members(path):
            return path
    raise SystemExit("no archive in %s provides %s" % (gamedir, member))


def apply_edit(text, block, key, value):
    """Set `key` to `value` (inside every block matching `block`, or anywhere). Keeps comments."""
    line_re = re.compile(r"^(\s*%s\s*=\s*)([^;\r\n]*?)(\s*(;.*)?)$" % re.escape(key), re.IGNORECASE)
    head_re = re.compile(r"^\s*%s\b" % block, re.IGNORECASE) if block else None
    out, inside, hits = [], block is None, 0
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        if head_re and head_re.match(body):
            inside = True
        elif head_re and inside and re.match(r"^\s*End\b", body, re.IGNORECASE):
            inside = False
        m = line_re.match(body) if inside else None
        if m:
            line = m.group(1) + value + m.group(3) + line[len(body):]
            hits += 1
        out.append(line)
    return "".join(out), hits


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("game", choices=sorted(GAMEDIRS))
    a = ap.parse_args()
    gamedir = os.path.join(ROOT, GAMEDIRS[a.game])
    work = os.path.join(ROOT, "build", "group-pack", a.game)
    tree, install = os.path.join(work, "tree"), os.path.join(work, "install")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(install)

    for member in sorted({e[0] for e in EDITS}):
        src = source_archive(gamedir, member)
        run([sys.executable, BIGTOOL, "extract", src, member, "-o", tree])
        path = os.path.join(tree, *member.split("\\"))
        with open(path, "r", encoding="latin-1", newline="") as fh:
            text = fh.read()
        for m, block, key, value in EDITS:
            if m != member:
                continue
            text, hits = apply_edit(text, block, key, value)
            if not hits:
                raise SystemExit("%s: %s not found in %s - the game data changed, check EDITS" % (member, key, os.path.basename(src)))
            print("%-24s %-24s = %-8s (%d place%s, from %s)" % (member.split("\\")[-1], key, value, hits,
                                                               "" if hits == 1 else "s", os.path.basename(src)))
        with open(path, "w", encoding="latin-1", newline="") as fh:
            fh.write(text)

    out = os.path.join(install, PACK_NAME)
    run([sys.executable, BIGTOOL, "pack", tree, out])
    print("\nbuilt %s (%d bytes)\ninstall: scripts/install-mod.sh %s %s" % (os.path.relpath(out, ROOT),
                                                                       os.path.getsize(out), a.game, os.path.relpath(install, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
