#!/usr/bin/env python3
"""Read and patch the SAGE asset cache (asset.dat) records for W3D models.

    tools/asset_dat.py show  <asset.dat> <model.w3d name>        e.g. dbfortress.w3d
    tools/asset_dat.py check <asset.dat> <file.w3d> [--name N]   does the record match this file?
    tools/asset_dat.py patch <asset.dat> <file.w3d> [--name N]   rewrite the record's offsets/sizes
    tools/asset_dat.py texture <asset.dat> <new.tga> --like <old.tga> [--model m.w3d --object OBJ]
                       register a new texture (and make OBJ of m.w3d depend on it instead of old)

Why: BFME2/RotWK do not parse a model file when they load it; asset.dat caches, per model, where
each top-level chunk is and the engine reads those ranges directly. A re-exported model with any
change in layout is read at stale offsets and silently fails to render. A texture the cache has no
record for is drawn magenta. The format: sagekit/formats/assetcache.py (this is its command line).
Only records whose entry names and count match the file are patched (the record's size never
changes); the first write keeps <asset.dat>.orig.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sagekit.formats.assetcache import AssetCache, CacheError  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["show", "check", "patch", "texture"])
    ap.add_argument("asset_dat")
    ap.add_argument("target", help="model name (show), .w3d file (check/patch) or new texture name (texture)")
    ap.add_argument("--name", help="record name, default: the file's basename, lower-case")
    ap.add_argument("--like", help="texture: existing texture whose record is copied")
    ap.add_argument("--model", help="texture: model file whose object should use the new texture")
    ap.add_argument("--object", help="texture: that object, e.g. DBFORTRESS.DBFORTRESS")
    a = ap.parse_args()
    cache = AssetCache(a.asset_dat)
    before = cache.data
    try:
        if a.cmd == "texture":
            if not a.like or bool(a.model) != bool(a.object):
                raise SystemExit("texture needs --like, and --model with --object")
            lines = cache.add_texture(a.target, a.like, a.model, a.object)
        elif a.cmd == "show":
            for name, tag, off, size, _ in cache.model_record(a.name or a.target):
                print("%-28s %s  offset %8d  size %8d" % (name, tag[::-1].decode(), off, size))
            return 0
        elif a.cmd == "check":
            stale = cache.stale_entries(a.target, a.name)
            for r, h in stale:
                print("STALE %-26s cached offset %d size %d, file offset %d size %d" % (r[0], r[2], r[3], h[2], h[3]))
            print("record matches the file" if not stale else "%d stale entr%s" % (len(stale), "y" if len(stale) == 1 else "ies"))
            return 1 if stale else 0
        else:
            lines = cache.patch_model(a.target, a.name)
    except CacheError as e:
        raise SystemExit(str(e))
    if cache.data != before:
        if not os.path.exists(a.asset_dat + ".orig"):
            print("backup: %s" % (a.asset_dat + ".orig"))
        cache.save()
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
