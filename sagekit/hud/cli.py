"""python3 -m sagekit hud [options] (docs/HUD.md)

    (no option)          extract EA's palantir textures, upscale, paint, write 1x and 2x, double the
                         2x geometry, check, and render the review sheets
    --sheet              the review sheets only (from the last build)
    --stage | --install | --revert [--1x] [--dry-run]   the !!!!!!!!!!!!!!sagekit-hud.big archive
                         (2x unless --1x: EA's sizes, no geometry)
"""
import argparse


def main(argv):
    ap = argparse.ArgumentParser(prog="python3 -m sagekit hud", description=__doc__.split("\n")[0])
    for x in ("stage", "install", "revert", "sheet"):
        ap.add_argument("--" + x, action="store_true")
    ap.add_argument("--1x", dest="one", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.stage or a.install or a.revert:
        from .install import main as install
        return install("stage" if a.stage else "install" if a.install else "revert", "1x" if a.one else "2x",
                       a.dry_run)
    from .sheet import review
    if a.sheet:
        print("\n".join(review()))
        return 0
    from .build import run
    bad = run()
    print("\n".join(review()))
    return 1 if bad else 0
