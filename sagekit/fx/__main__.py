"""python3 -m sagekit.fx: the shared FX archive (sagekit/fx/__init__.py).

    --stage             compose every assets/<faction>/fx.py, check, pack into build/assets/_fx/_install
    --review [F,G]      the review sheets, build/assets/_review_finish/fx/<faction>.jpg
    --install           stage, then put the archive in the game folder (receipt, revertable)
    --revert            take it out again (refuses when the game folder changed since)
    --status            installed / staged, and whether the faction packs under it changed
"""
import argparse

from . import install


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m sagekit.fx", description=__doc__.split("\n")[0])
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", action="store_true")
    mode.add_argument("--review", nargs="?", const="", metavar="F,G")
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--revert", action="store_true")
    mode.add_argument("--status", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    if a.stage:
        install.stage()
    elif a.review is not None:
        from . import preview
        preview.review([f for f in a.review.split(",") if f] or None)
    elif a.install:
        install.install(a.dry_run)
    elif a.revert:
        install.revert(a.dry_run)
    else:
        install.status()


if __name__ == "__main__":
    main()
