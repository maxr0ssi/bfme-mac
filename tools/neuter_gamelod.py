#!/usr/bin/env python3
"""neuter_gamelod.py — the one-shot fix for the SAGE GameLOD pre-menu crash.

On Apple Silicon under Rosetta, the SAGE engine's raw-assembly ``RDTSC``/``CPUID``
CPU benchmark mis-reads the fast translated CPU and matches the **"UltraHigh"**
hardware profile in ``gamelodpresets.ini``. Applying that top detail tier writes
out of bounds and the game crashes every launch, before the main menu, with a
deterministic ``0xC0000005`` access violation inside ``game.dat`` (see
``parse_minidump.py``).

You can't stop the hardcoded benchmark, but you can delete the presets it is
allowed to pick. With **no ``LODPreset`` rows present**, the engine falls back to
its built-in ``VeryLow`` default — and the crash is gone.

This script does the whole edit in place:

    1. find ``data\\ini\\gamelodpresets.ini`` inside ``ini.big``
    2. strip every ``LODPreset = ...`` row (the ``P4 .../K7 ...`` CPU profiles)
    3. back up ``ini.big`` -> ``ini.big.preLODfix.bak`` and repack

Usage:
    neuter_gamelod.py "/path/to/.../ini.big"
    neuter_gamelod.py "/path/to/.../ini.big" --dry-run

Pair it with single-core pinning (``WINE_CPU_TOPOLOGY=1:0``) at launch. Fully
reversible — restore the ``.preLODfix.bak`` to undo.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bigtool import build_big, read_index, read_member  # noqa: E402

MEMBER = "data\\ini\\gamelodpresets.ini"
BACKUP_SUFFIX = ".preLODfix.bak"


def strip_presets(text: str) -> tuple[str, int]:
    out_lines = []
    removed = 0
    for line in text.splitlines(keepends=True):
        if line.lstrip().lower().startswith("lodpreset"):
            removed += 1
            continue
        out_lines.append(line)
    return "".join(out_lines), removed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ini_big", help="path to the game's ini.big")
    ap.add_argument("--dry-run", action="store_true", help="report, don't write")
    args = ap.parse_args(argv)

    entries, _ = read_index(args.ini_big)
    target = None
    for e in entries:
        if e.name.replace("/", "\\").lower() == MEMBER:
            target = e
            break
    if target is None:
        print(f"error: {MEMBER} not found in {args.ini_big}", file=sys.stderr)
        return 1

    original = read_member(args.ini_big, target).decode("latin-1")
    edited, removed = strip_presets(original)
    print(f"gamelodpresets.ini: {removed} LODPreset row(s) -> removed "
          f"(engine will fall back to VeryLow)")

    if removed == 0:
        print("nothing to do — already neutered?")
        return 0
    if args.dry_run:
        print("(dry run — no files written)")
        return 0

    bak = args.ini_big + BACKUP_SUFFIX
    if not os.path.exists(bak):
        with open(bak, "wb") as b, open(args.ini_big, "rb") as src:
            b.write(src.read())
        print(f"backup -> {bak}")

    members = []
    for e in entries:
        if e is target:
            members.append((e.name, edited.encode("latin-1")))
        else:
            members.append((e.name, read_member(args.ini_big, e)))

    with open(args.ini_big, "wb") as out:
        out.write(build_big(members))
    print(f"repacked {args.ini_big} ({os.path.getsize(args.ini_big):,} bytes)")
    print("done. Launch with WINE_CPU_TOPOLOGY=1:0 and the wined3d backend.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
