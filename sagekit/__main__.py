"""python3 -m sagekit <command>

    list                               every building under assets/
    validate                           load every building; taxonomy, names, budget rules, the upgrade limit
    inventory <faction/building>       its lifecycle as the game defines it, and what exists
    budget [faction]                   memory the own textures take, per faction
    build <faction/building> [--from STEP] [--to STEP]
    preview <faction/building> [--views rts,close]   geometry + flat-colour renders + bake-free checks (~1 min)
    sheets <faction> [--only NAME]     recolour every texture sheet of the faction to its palette
    house <faction>                    add the buildings' cloth to the house-colour models (player colour)
    names <faction> [--write]          every model and texture name the faction ships (assets/<faction>/NAMES.md)
    owners <faction> [--refresh]       what the faction draws that other factions draw too (sagekit/ownership.py)
    new <faction> [--write] [--only N] one stub recipe per design unit of EA's (sagekit/scaffold.py)
    board <faction>                    EA's buildings as they are, one labelled grid (sagekit/board.py)
    palettes <faction> [--only A,B]    EA's citadel recoloured with each palette option (sagekit/palettes.py)
    measure <faction/building>         EA's body measured into work/measure.json (sagekit/measure.py)
    capture <faction/building> [--version v1] [--no-render]   the capture dress review sheet (sagekit/capture.py)
    install <faction> | revert <faction>   put everything built into the game / take it out
    unit <faction>/<unit> [--render|--check|--stage|--install|--revert]   a unit (builder) recipe
                                       (sagekit/units/, docs/UNITS.md); unit list | unit selfcheck
    icons <faction> [--map|--render|--stage|--install|--revert]   HUD portraits and buttons of our
                                       buildings (sagekit/icons/, docs/ICONS.md)
    hud [--sheet|--stage|--install|--revert] [--1x]   the in-game palantir's frames, glass and
                                       buttons in our metal, 1x and Retina 2x (sagekit/hud/, docs/HUD.md)
    ui2x [--stage|--install|--revert|--sheet]   Retina 2x pages for portraits, buttons, our icons and
                                       the tooltip frame (sagekit/ui2x/, docs/UI2X.md)
    offload pack <faction> [--only b1,b2] | run [--builds N] | results | unpack <zip> [--print-only]
                                       full-quality builds on another machine (sagekit/offload.py)
"""
import argparse
import sys

from . import registry
from .game import Install
from .taxonomy import MB, State, states_of, upgrades_of


def cmd_list(a):
    for bid in registry.building_ids():
        b = registry.load(bid)
        print("%-24s %-12s %-6s %s" % (bid, b.source, b.tier.name, ", ".join(s.value for s in b.built_states)))


def cmd_validate(a):
    names, bad = {}, 0
    from .ownership import self_check
    for f in self_check():                      # the ownership scan's rules, no game needed
        bad += 1
        print("FAIL ownership: %s" % f)
    from .inherit import self_check as inherit_check
    for f in inherit_check():                   # inherited Draw modules made a faction's own, no game needed
        bad += 1
        print("FAIL inherit: %s" % f)
    from .lifecycle import self_check as lifecycle_check
    for f in lifecycle_check():                 # the state-texture rules (Building.state_textures), no game needed
        bad += 1
        print("FAIL lifecycle: %s" % f)
    game = _game_checks()
    for bid in registry.building_ids():
        try:
            b = registry.load(bid)
            if game:                            # EA's names and other factions' art (ownership.py)
                game[0](b)
            from .fire import points as fire_points
            fire_points(b)                      # (x, y, z, kind) with a kind sagekit/fire.py knows
            from .lifecycle import check_settings
            check_settings(b)                   # lifecycle allowances carry a number and a reason
            for old, new in b.texture_names().items():
                if len(old) != len(new):
                    raise ValueError("%s -> %s: own texture names must keep the original's length" % (old, new))
                if new.lower() in names:
                    raise ValueError("%s is also %s's texture" % (new, names[new.lower()]))
                names[new.lower()] = bid
            from .workspace import Workspace    # state variants (build records): no other recipe's
            ws = Workspace(b)
            for old, new in list(ws.variants.items()) + list(ws.normal_variants.items()):
                if names.setdefault(new.lower(), bid) != bid:
                    raise ValueError("%s (for %s) is also %s's texture" % (new, old, names[new.lower()]))
            print("ok   %s" % bid)
        except (ValueError, ImportError, AttributeError) as e:
            bad += 1
            print("FAIL %s: %s" % (bid, e))
    from . import units                         # unit recipes (sagekit/units/): load and name rules
    for uid in units.ids():
        try:
            units.load(uid)
            print("ok   %s (unit)" % uid)
        except (ValueError, ImportError, AttributeError) as e:
            bad += 1
            print("FAIL %s: %s" % (uid, e))
    from .upgrades import validate as upgrade_limit
    bad += upgrade_limit()                      # EA's upgrades + ours within the engine's 1152
    from .texbake import validate as texture_formats
    bad += texture_formats()                    # staged archives: no TGA left to build mips in game
    from .drawcost_report import validate as draw_cost
    bad += draw_cost()                          # staged archives: no object draws more than EA's + margin
    from .texslim import validate as texture_memory
    bad += texture_memory()                     # staged archives: texture memory within the per-archive cap
    from .texreach import validate as texture_reach
    bad += texture_reach()                      # staged packs: no texture level the closest camera never samples
    bad += cmd_budget(a)
    return 1 if bad else 0


def _game_checks():
    """(check(b),) raising ValueError for an own texture name EA's files use or art another faction
    draws; () when the game is not installed (validate then checks the recipes alone)."""
    from . import names, ownership
    try:
        g = Install()
        stems, own = names.ea_texture_stems(g), ownership.load(g)
    except OSError as e:
        print("note: game files not readable (%s): names and ownership not checked" % e)
        return ()

    def check(b):
        names.check_free(b, stems)
        probs = ownership.recipe_problems(b, own, g)
        if probs:
            raise ValueError("; ".join(probs))
    return (check,)


def cmd_budget(a):
    per, over = {}, 0
    for bid in registry.building_ids():
        b = registry.load(bid)
        from .alpha import extra_bytes         # DXT5 where EA's sheet has cut-outs (once extracted)
        per.setdefault(b.faction, [b.style.budget_mb, 0])[1] += b.tier.bytes() + extra_bytes(b)
    for f, (limit, used) in sorted(per.items()):
        if a.__dict__.get("faction") and f != a.faction:
            continue
        flag = "OVER" if used > limit * MB else "ok"
        over += flag == "OVER"
        print("%-4s %-10s %6.1f MB of %d MB" % (flag, f, used / MB, limit))
    return over


def cmd_inventory(a):
    """Every part of the building (each Draw module of its objects) with every condition the game
    draws it in: [x] this recipe builds it, [ ] still to do, MISSING the model is not in any archive.
    A Draw showing two build variations lists this recipe's variation only."""
    b = registry.load(a.building)
    g = Install()
    print("%s: model family %s*, INIs under %s" % (b.id, b.source, ", ".join(b.style.ini_dirs())))
    for obj, draws in b.objects(g).items():
        print("\n%s" % obj)
        for d in draws:
            models = [m for m in d.models()]
            if not models:
                continue
            role = "body" if b.is_body(d) else "add-on"
            print("  %s  %-6s %s%s" % ("[x]" if b.covers(d) else "[ ]", role, d.tag,
                                       "" if d.object == obj else " (inherited from %s)" % d.object))
            own = b.own_states(d)
            for st in d.states:
                if st not in own:               # another build variation's (its own recipe's)
                    continue
                what = st.model if st.model and st.model.lower() != "none" else ""
                if st.textures:
                    what += (" " if what else "") + ", ".join("%s->%s" % t for t in st.textures)
                if st.animations:
                    what += (" " if what else "") + "anim " + ", ".join(st.animations)
                if not what:
                    continue
                cond = "+".join(sorted(s.value for s in states_of(st.flags)))
                ups = upgrades_of(st.flags)
                cond += (" [" + ", ".join(u.lower() for u in ups) + "]") if ups else ""
                built = b.covers(d) and all(s in b.built_states for s in states_of(st.flags)) and not ups
                missing = st.model and st.model.lower() != "none" and not g.has_model(st.model)
                print("       %s %-44s %s%s" % ("x" if built else "-", cond, what, "  MISSING" if missing else ""))
            if d.fields.get("StaticModelLODMode", "").lower() == "yes":
                for suffix, state in (("M", State.LOD_MEDIUM), ("L", State.LOD_LOW)):
                    for m in b.own_models(d):
                        if g.has_model(m + suffix):
                            print("       %s %-44s %s" % ("x" if state in b.built_states else "-", state.value, m + suffix))


def cmd_build(a):
    from .pipeline import Pipeline, StepFailed
    try:
        Pipeline(registry.load(a.building), a.force).run(a.first, a.last)
    except StepFailed as e:
        print("FAILED:", e)
        return 1
    return 0


def cmd_preview(a):
    from .preview import run
    return run(a.building, a.views, a.res, a.extract, a.force)


def cmd_sheets(a):
    """Recolour the faction's sheets (sagekit/paint/sheets.py) into build/assets/<faction>/_sheets/out,
    four at a time on Blender's Python."""
    import os
    import subprocess
    from concurrent.futures import ThreadPoolExecutor
    from . import paths
    from .formats.textures import dds_info, tga_header
    from .pipeline import REALESRGAN, game_running
    if game_running() and not a.force:
        print("the game is running - recolouring would take its CPU and GPU. Close it, or pass --force")
        return 1
    style = _style(a.faction)
    g = Install()
    root = os.path.join(paths.BUILD, a.faction, "_sheets")
    from .ownership import faction_sheets
    keep, skipped = faction_sheets(style, g)            # never another faction's sheet (ownership.py)
    for m, others, copy in skipped:
        print("skip %-28s drawn by %s too%s" % (m.split("\\")[-1], ", ".join(sorted(others)),
                                               " (copied per build as %s)" % copy if copy else ""))
        stale = os.path.join(root, "out", *m.split("\\"))
        if os.path.exists(stale):                       # a recolour from before the ownership rule:
            os.remove(stale)                            # install packs everything in out/
            print("     removed its earlier recolour")
    todo = [m for m in keep if not a.only or a.only.lower() in m]

    def one(member):
        name = member.split("\\")[-1]
        src = os.path.join(root, "src", name)
        os.makedirs(os.path.dirname(src), exist_ok=True)
        with open(src, "wb") as fh:
            fh.write(g.read(member))
        out = os.path.join(root, "out", *member.split("\\"))
        tga = name.endswith(".tga")                     # EA's TGA-only sheet: a TGA again, EA's size
        size = tga_header(src)["width"] if tga else style.sheet_size(name)
        r = subprocess.run([paths.blender_python(), "-m", "sagekit.paint.sheets", a.faction, src, out,
                            str(size), REALESRGAN], capture_output=True, text=True,
                           cwd=paths.REPO, env=dict(os.environ, PYTHONPATH=paths.REPO))
        if r.returncode:
            return "FAIL %s\n%s" % (name, r.stderr[-1500:])
        i = dict(tga_header(out), fourcc="TGA%d" % tga_header(out)["bpp"]) if tga else dds_info(out)
        return "ok   %-28s %4dx%-4d %s" % (name, i["width"], i["height"], i["fourcc"])
    with ThreadPoolExecutor(4) as ex:
        results = list(ex.map(one, todo))
    print("\n".join(results))
    return 1 if any(r.startswith("FAIL") for r in results) else 0


def cmd_house(a):
    """Add every building's cloth to the faction's house-colour models (sagekit/house.py)."""
    from .house import build
    build(a.faction, force=a.force)


def cmd_names(a):
    from . import names
    if a.write:
        print("wrote", names.write(a.faction))
    else:
        print(names.markdown(a.faction), end="")


def cmd_owners(a):
    from .ownership import load, report
    if a.refresh:
        load(refresh=True)
    print("\n".join(report(a.faction)))


def cmd_new(a):
    from .scaffold import run
    return run(a.faction, a.write, a.only)


def cmd_board(a):
    from .board import run
    return run(a.faction)


def cmd_palettes(a):
    from .palettes import run
    return run(a.faction, a.only)


def cmd_measure(a):
    """EA's body measured (sagekit/measure.py), on Blender's Python (numpy)."""
    import os
    import subprocess
    from . import paths
    r = subprocess.run([paths.blender_python(), "-m", "sagekit.blender.measure", a.building], cwd=paths.REPO,
                       env=dict(os.environ, PYTHONPATH=paths.REPO))
    return r.returncode


def cmd_capture(a):
    from .capture import review
    review(registry.load(a.building), a.version, render=not a.no_render)


def cmd_install(a):
    from .install import install_faction
    from .pipeline import game_running
    if game_running():
        print("the game is running - close it first (it reads its archives at startup)")
        return 1
    if a.revert:
        from .install import revert_faction
        revert_faction(a.faction, dry=a.dry_run)
    else:
        install_faction(a.faction, check=a.check)


def cmd_revert(a):
    from .install import revert_faction
    revert_faction(a.faction, dry=a.dry_run)


def cmd_unit(a):
    from .units.cli import main as unit
    return unit(a.args)


def cmd_offload(a):
    from .offload import main as offload
    return offload(a)


def _style(faction):
    import importlib
    mod = importlib.import_module("assets.%s.style" % faction)
    return next(v() for v in vars(mod).values() if isinstance(v, type) and getattr(v, "faction", None) == faction)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["unit"]:                    # its own options (sagekit/units/cli.py)
        from .units.cli import main as unit
        return unit(argv[1:]) or 0
    if argv[:1] == ["scenery"]:                 # its own options (sagekit/scenery.py)
        from .scenery import main as scenery
        return scenery(argv[1:]) or 0
    if argv[:1] == ["icons"]:                   # its own options (sagekit/icons/cli.py)
        from .icons.cli import main as icons
        return icons(argv[1:]) or 0
    if argv[:1] == ["ui2x"]:                    # its own options (sagekit/ui2x/cli.py)
        from .ui2x.cli import main as ui2x
        return ui2x(argv[1:]) or 0
    if argv[:1] == ["hud"]:                     # its own options (sagekit/hud/cli.py)
        from .hud.cli import main as hud
        return hud(argv[1:]) or 0
    ap = argparse.ArgumentParser(prog="python3 -m sagekit", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("validate")
    p = sub.add_parser("budget")
    p.add_argument("faction", nargs="?")
    p = sub.add_parser("inventory")
    p.add_argument("building")
    p = sub.add_parser("build")
    p.add_argument("building")
    p.add_argument("--from", dest="first")
    p.add_argument("--to", dest="last")
    p.add_argument("--force", action="store_true", help="build even while the game is running")
    p = sub.add_parser("preview", help="a fast shape preview (sagekit/preview.py)")
    p.add_argument("building")
    p.add_argument("--views", help="comma-separated views (default: the recipe's, else rts,close,ingame)")
    p.add_argument("--res", default="1200x825")
    p.add_argument("--extract", action="store_true", help="extract again first")
    p.add_argument("--force", action="store_true", help="run even while the game is running")
    p = sub.add_parser("sheets")
    p.add_argument("faction")
    p.add_argument("--only")
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("house")
    p.add_argument("faction")
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("names")
    p.add_argument("faction")
    p.add_argument("--write", action="store_true")
    p = sub.add_parser("owners")
    p.add_argument("faction")
    p.add_argument("--refresh", action="store_true", help="rescan the game even if the cache is current")
    p = sub.add_parser("new")
    p.add_argument("faction")
    p.add_argument("--write", action="store_true", help="write the stubs (never over an existing recipe)")
    p.add_argument("--only", help="comma-separated stub names to write (default: every one)")
    sub.add_parser("measure").add_argument("building")
    sub.add_parser("board", help="EA's buildings as they are (sagekit/board.py)").add_argument("faction")
    p = sub.add_parser("palettes", help="the palette options on EA's citadel (sagekit/palettes.py)")
    p.add_argument("faction")
    p.add_argument("--only", help="comma-separated palette keys (default: every one in the style)")
    p = sub.add_parser("capture", help="the capture dress review sheet (sagekit/capture.py)")
    p.add_argument("building")
    p.add_argument("--version", default="v1")
    p.add_argument("--no-render", action="store_true", help="the sheet again from the last renders")
    for name in ("install", "revert"):
        p = sub.add_parser(name)
        p.add_argument("faction")
        p.add_argument("--dry-run", action="store_true", help="with a revert: say what it would write")
        if name == "install":
            modes = p.add_mutually_exclusive_group()
            modes.add_argument("--check",action="store_true",help="stage and verify without installing")
            modes.add_argument("--revert",action="store_true",help="restore the last scoped installation")
    p = sub.add_parser("unit", help="a unit recipe: build, render, stage, install, revert (sagekit/units/cli.py)",
                       add_help=False)
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("offload", help="builds on another machine (docs/OFFLOAD.md)")
    p.add_argument("action", choices=["pack", "run", "results", "unpack"])
    p.add_argument("target", nargs="?", help="pack: the faction; unpack: the results zip")
    p.add_argument("--only", help="comma-separated building names (pack, run)")
    p.add_argument("--no-extract", action="store_true", help="pack: use the sources extracted before")
    p.add_argument("--builds", type=int, default=4, help="run: buildings at once")
    p.add_argument("--with-bakes", action="store_true", help="results: keep work/bake (large)")
    p.add_argument("--print-only", action="store_true", help="unpack: print the Mac's commands, run nothing")
    a = ap.parse_args(argv)
    return globals()["cmd_" + a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
