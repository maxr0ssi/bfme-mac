#!/usr/bin/env python3
"""neuter_gamelod.py - remove the LODPreset rows that crash the game before the main menu.

Under Rosetta the engine's startup CPU benchmark (RDTSC/CPUID) matches the "UltraHigh" hardware
profile in gamelodpresets.ini; applying it writes out of bounds, and every launch ends before the
main menu in an access violation (0xC0000005) inside game.dat (parse_minidump.py reads the dump).
With no LODPreset rows the engine uses its built-in default instead. scripts/install.sh runs this
on the games' ini.big and __patch202.big.

    neuter_gamelod.py "/path/to/.../ini.big" [--dry-run]

It strips every ``LODPreset = ...`` row from ``data\\ini\\gamelodpresets.ini`` and repacks
the archive, keeping the original as ``ini.big.preLODfix.bak`` (copy it back to undo).
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
