"""python3 -m sagekit unit <faction>/<unit> [--render [STATE ...]] [--check] [--stage] [--install] [--revert]

    (no option)        build: EA's sources, our model, atlas and mask into build/assets/<unit>/; the checks
    --render [STATES]  build, then EA's unit and ours in each state's pose: renders/compare_<state>.png
    --check            the checks of the last build only
    --stage            the checks, then the archive into _install/ (what --install would ship; and the
                       release pack's input, sagekit/pack.py); nothing in the game changes
    --install          stage, then install: the unit's archive, its asset.dat records, the shared
                       house-colour INI (sagekit/units/install.py)
    --revert           take the unit out: its archive gone, its records EA's again (any order)
    --dry-run          with --install/--revert: everything but the writes
    --out DIR          build somewhere else than build/assets/<unit> (a comparison build)

python3 -m sagekit unit list      every unit recipe, its model and whether it is installed
python3 -m sagekit unit selfcheck the composition and record-level revert on synthetic files
"""
import argparse

from . import Folder, ids, load


def selfcheck():
    from . import install as I
    from .records import selfcheck as records_check

    class Fake:
        id, house = "x/porter", {"xcrafts.tga": "hc_xcrafts.tga"}
    ea = b"HouseColor\r\n BaseTexture = eucrafts.tga\r\n HouseTexture = hc_eucrafts.tga\r\nEnd\r\n"
    one = I.compose(ea, [Fake()])
    assert one.startswith(ea) and one.endswith(I.mapping(Fake()))
    try:
        I.compose(one, [Fake()])
    except SystemExit:
        pass
    else:
        raise AssertionError("a texture mapped twice was accepted")
    records_check()
    print("PASS: house-colour lines appended once, conflicts refused")


def main(argv):
    p = argparse.ArgumentParser(prog="python3 -m sagekit unit", description=__doc__.split("\n")[0])
    p.add_argument("unit", help="<faction>/<unit>, list or selfcheck")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--render", nargs="*", metavar="STATE")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--stage", action="store_true")
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--revert", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--out")
    a = p.parse_args(argv)
    if a.unit == "selfcheck":
        return selfcheck()
    if a.unit == "list":
        from .install import installed
        have = installed()
        for uid in ids():
            u = load(uid)
            print("%-18s %-14s %-14s %s" % (uid, u.model, u.own_model or "", "installed" if uid in have else
                                            "stub" if not u.privates() else ""))
        return
    u = load(a.unit)
    b = Folder(u, a.out)
    from . import build, install
    if a.check:
        build.check(u, b)
    elif a.stage:
        install.stage(u, b)
    elif a.install:
        install.install(u, b, a.dry_run)
    elif a.revert:
        install.revert(u, b, a.dry_run)
    else:
        build.build(u, b)
        if a.render is not None:
            from .render import previews
            previews(u, b, a.render)
