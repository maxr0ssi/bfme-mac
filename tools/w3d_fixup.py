#!/usr/bin/env python3
"""Restore what the OpenSAGE Blender add-on (io_mesh_w3d 0.7.x) drops when it re-exports a game model.

    tools/w3d_fixup.py <original.w3d> <exported.w3d> [-o fixed.w3d] [--rename [MESH:]OLD.tga=NEW.tga ...]

What it restores and why: sagekit/formats/w3d.py (this is its command line).

--rename points restored materials at a model's own texture: DBFortress1.tga=DBFortressH.tga for
every mesh, DBFORTRESS:DBFortress1.tga=DBFortressH.tga for one. Names must keep their length, so
every chunk size stays put; register the new texture in the asset cache too (tools/asset_dat.py
texture), or the game draws it as its missing-texture pink.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sagekit.formats.w3d import fix  # noqa: E402


def parse_rename(r):
    pair, only = (r.split(":", 1)[1], r.split(":", 1)[0]) if ":" in r.split("=", 1)[0] else (r, None)
    old, new = pair.split("=", 1)
    return only, old, new


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("original")
    ap.add_argument("exported")
    ap.add_argument("-o", "--output", help="default: overwrite the exported file")
    ap.add_argument("--rename", action="append", default=[], metavar="[MESH:]OLD=NEW",
                    help="texture name to swap in restored materials, same length (repeatable)")
    a = ap.parse_args()
    renames = [parse_rename(r) for r in a.rename]
    with open(a.original, "rb") as fh:
        orig = fh.read()
    with open(a.exported, "rb") as fh:
        new = fh.read()
    try:
        fixed, report = fix(orig, new, renames)
    except ValueError as e:
        raise SystemExit("--rename: %s" % e)
    with open(a.output or a.exported, "wb") as fh:
        fh.write(fixed)
    for line in report:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
