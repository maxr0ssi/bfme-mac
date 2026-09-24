#!/usr/bin/env python3
"""Pre-bake a game's uncompressed TGA textures into DDS with mipmaps.

Roughly 60% of BFME2/RotWK texture bytes ship as uncompressed TGA. TGA carries no
mipmap chain, so the engine converts the pixels and builds every mip level on the CPU
at load time, on one thread (docs/LOAD-TIME.md). This moves that work offline: the
same art, stored the way the engine can hand straight to the GPU.

".tga" and ".dds" are the same length, so every reference inside .w3d models and the
text assets is patched in place with no change to any offset or chunk size.

    tools/prebake_textures.py <gamedir> [--format auto|dxt1|dxt5|raw] [--dry-run]
    tools/prebake_textures.py <gamedir> --revert

Every archive it rewrites is backed up as <name>.prebake.bak first; --revert puts
them all back. Needs build/tga2dds (cc -O2 -o build/tga2dds tools/tga2dds.c).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIGTOOL = os.path.join(HERE, "bigtool.py")
TGA2DDS = os.path.join(ROOT, "build", "tga2dds")
# Text-ish assets that can name a texture; .w3d is binary but holds plain strings.
PATCHABLE = (".w3d", ".ini", ".txt", ".xml", ".inc", ".lua")
# Over half these texture names contain spaces ("cin amon sul - castle pan.tga"), so the
# name class has to allow them. The lookbehind stops a match starting mid-identifier, and
# a hit only counts when the captured text names a texture we actually converted, which
# keeps the wide class from matching lookalike bytes in binary members.
REF = re.compile(rb"(?<![A-Za-z0-9_])([A-Za-z0-9_\-# ]+)\.tga", re.IGNORECASE)


def _swap(m, stems):
    """NAME.tga -> NAME.dds when NAME was converted; byte-identical otherwise."""
    name = m.group(1)
    if name.strip().decode("latin-1").lower() in stems:
        return name + b".dds"
    return m.group(0)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("failed: %s\n%s" % (" ".join(cmd), r.stderr[:2000]))
    return r.stdout


def list_members(archive):
    out = run([sys.executable, BIGTOOL, "list", archive])
    names = []
    for line in out.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            names.append(parts[1])
    return names


def archives(gamedir):
    return sorted(
        os.path.join(gamedir, f) for f in os.listdir(gamedir) if f.lower().endswith(".big")
    )


def revert(gamedir):
    n = 0
    for dirpath, dirs, files in os.walk(gamedir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if not f.endswith(".prebake.bak"):
                continue
            bak = os.path.join(dirpath, f)
            shutil.move(bak, bak[: -len(".prebake.bak")])
            n += 1
            print("restored", os.path.relpath(bak[: -len(".prebake.bak")], gamedir))
    print("reverted %d file(s)" % n)
    return 0


def convert_tree(workdir, fmt, dry_run):
    """Convert every .tga under workdir to .dds; return the set of converted stems."""
    todo = []
    for dirpath, _, files in os.walk(workdir):
        for f in files:
            if f.lower().endswith(".tga"):
                todo.append(os.path.join(dirpath, f))
    stems = set()
    failed = []

    def one(src):
        dst = src[:-4] + ".dds"
        cmd = [TGA2DDS, src, dst]
        if fmt != "auto":
            cmd += ["--format", fmt]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(dst):
            return src, r.stderr.strip()
        os.remove(src)
        return None

    if dry_run:
        print("  would convert %d TGA(s)" % len(todo))
        return {os.path.basename(p)[:-4].lower() for p in todo}, []

    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        for res in pool.map(one, todo):
            if res:
                failed.append(res)
    for src in todo:
        if not os.path.exists(src):
            stems.add(os.path.basename(src)[:-4].lower())
    return stems, failed


def patch_refs(workdir, stems):
    """Rewrite NAME.tga -> NAME.dds in place for every converted NAME. Same length."""
    changed = 0

    def sub(m):
        return _swap(m, stems)

    for dirpath, _, files in os.walk(workdir):
        for f in files:
            if not f.lower().endswith(PATCHABLE):
                continue
            p = os.path.join(dirpath, f)
            with open(p, "rb") as fh:
                data = fh.read()
            new = REF.sub(sub, data)
            if new != data:
                assert len(new) == len(data), p
                with open(p, "wb") as fh:
                    fh.write(new)
                changed += 1
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("gamedir")
    ap.add_argument("--format", default="auto", choices=["auto", "dxt1", "dxt5", "raw"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()

    if not os.path.isdir(a.gamedir):
        raise SystemExit("no such game directory: %s" % a.gamedir)
    if a.revert:
        return revert(a.gamedir)
    if not os.path.exists(TGA2DDS):
        raise SystemExit("build/tga2dds missing - cc -O2 -o build/tga2dds tools/tga2dds.c")

    allarch = archives(a.gamedir)
    if not allarch:
        raise SystemExit("no .big archives in %s" % a.gamedir)

    # Pass 1: which archives hold TGAs, and every TGA stem across all of them. The
    # reference patch has to use the full set, because a model in W3D.big names a
    # texture that lives in Textures2.big.
    holds_tga, all_stems = [], set()
    for path in allarch:
        stems = {
            os.path.basename(m)[:-4].lower().replace("\\", "/").split("/")[-1]
            for m in list_members(path)
            if m.lower().endswith(".tga")
        }
        if stems:
            holds_tga.append(path)
            all_stems |= stems
    print("%d archive(s) hold %d distinct TGA name(s)" % (len(holds_tga), len(all_stems)))
    if a.dry_run:
        for p in holds_tga:
            print("  would rewrite", os.path.basename(p))
        return 0

    # Phase 1: extract and convert everything first. A texture that fails to convert
    # stays .tga, so its references must stay .tga too - and an archive packed early
    # cannot know about a failure in an archive processed later. So nothing is packed
    # until the whole converted set is known.
    total_failed = []
    jobs = []  # (archive path, work dir, converted-something)
    for path in allarch:
        members = list_members(path)
        has_tga = any(m.lower().endswith(".tga") for m in members)
        has_ref = any(m.lower().endswith(PATCHABLE) for m in members)
        if not (has_tga or has_ref):
            continue
        name = os.path.basename(path)
        work = tempfile.mkdtemp(prefix="prebake-", dir=os.path.join(ROOT, "build"))
        print("== extract %s" % name)
        run([sys.executable, BIGTOOL, "extract", path, "-o", work])
        stems = set()
        if has_tga:
            stems, failed = convert_tree(work, a.format, False)
            print("   converted %d TGA(s)%s" % (len(stems), ", %d FAILED" % len(failed) if failed else ""))
            total_failed += failed
        jobs.append((path, work, bool(stems)))

    # Anything that failed keeps its .tga name, so drop it from the rename set.
    unconverted = {os.path.basename(src)[:-4].lower() for src, _ in total_failed}
    all_stems -= unconverted
    if unconverted:
        print("\n%d texture(s) stay TGA; their references are left alone" % len(unconverted))

    # Phase 2: patch every reference against the final set, then pack.
    for path, work, converted in jobs:
        name = os.path.basename(path)
        try:
            n = patch_refs(work, all_stems)
            if n:
                print("== %s: patched references in %d file(s)" % (name, n))
            if not converted and not n:
                continue
            bak = path + ".prebake.bak"
            if not os.path.exists(bak):
                shutil.copy2(path, bak)
            tmp = path + ".prebake.new"
            run([sys.executable, BIGTOOL, "pack", work, tmp])
            # bigtool's pack writes BIGF; most BFME2/RotWK archives are the BIG4
            # variant (identical layout, different magic). Keep whatever this one had.
            with open(bak, "rb") as fh:
                magic = fh.read(4)
            with open(tmp, "r+b") as fh:
                if fh.read(4) != magic:
                    fh.seek(0)
                    fh.write(magic)
            os.replace(tmp, path)
            print("   rewrote %s (%.1f MB)" % (name, os.path.getsize(path) / 1048576))
        finally:
            shutil.rmtree(work, ignore_errors=True)

    # asset.dat is the prebuilt catalogue the engine reads at startup; it names every
    # texture with its extension, so it needs the same in-place patch as the archives.
    # Loose .w3d/.ini in the game directory (mods, -preferLocalFiles overrides) too.
    loose = 0
    for dirpath, dirs, files in os.walk(a.gamedir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            low = f.lower()
            if low != "asset.dat" and not low.endswith(PATCHABLE):
                continue
            p = os.path.join(dirpath, f)
            with open(p, "rb") as fh:
                data = fh.read()
            new = REF.sub(lambda m: _swap(m, all_stems), data)
            if new == data:
                continue
            assert len(new) == len(data), p
            bak = p + ".prebake.bak"
            if not os.path.exists(bak):
                shutil.copy2(p, bak)
            with open(p, "wb") as fh:
                fh.write(new)
            loose += 1
            print("   patched loose %s" % os.path.relpath(p, a.gamedir))
    if loose:
        print("patched %d loose file(s)" % loose)

    if total_failed:
        print("\n%d texture(s) could not be converted and were left as TGA:" % len(total_failed))
        for src, err in total_failed[:10]:
            print("  %s: %s" % (os.path.basename(src), err))
    print("\ndone. --revert restores every .prebake.bak")
    return 0


if __name__ == "__main__":
    sys.exit(main())
