"""python3 -m sagekit <command>

    list                               every building under assets/
    validate                           load every building; taxonomy, names and budget rules
    inventory <faction/building>       its lifecycle as the game defines it, and what exists
    budget [faction]                   memory the own textures take, per faction
    build <faction/building> [--from STEP] [--to STEP]
    sheets <faction> [--only NAME]     recolour every texture sheet of the faction to its palette
    install <faction> | revert <faction>   put everything built into the game / take it out
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
    for bid in registry.building_ids():
        try:
            b = registry.load(bid)
            for old, new in b.texture_names().items():
                if len(old) != len(new):
                    raise ValueError("%s -> %s: own texture names must keep the original's length" % (old, new))
                if new.lower() in names:
                    raise ValueError("%s is also %s's texture" % (new, names[new.lower()]))
                names[new.lower()] = bid
            print("ok   %s" % bid)
        except (ValueError, ImportError, AttributeError) as e:
            bad += 1
            print("FAIL %s: %s" % (bid, e))
    bad += cmd_budget(a)
    return 1 if bad else 0


def cmd_budget(a):
    per, over = {}, 0
    for bid in registry.building_ids():
        b = registry.load(bid)
        per.setdefault(b.faction, [b.style.budget_mb, 0])[1] += b.tier.bytes()
    for f, (limit, used) in sorted(per.items()):
        if a.__dict__.get("faction") and f != a.faction:
            continue
        flag = "OVER" if used > limit * MB else "ok"
        over += flag == "OVER"
        print("%-4s %-10s %6.1f MB of %d MB" % (flag, f, used / MB, limit))
    return over


def cmd_inventory(a):
    """Every part of the building (each Draw module of its objects) with every condition the game
    draws it in: [x] this recipe builds it, [ ] still to do, MISSING the model is not in any archive."""
    b = registry.load(a.building)
    g = Install()
    print("%s: model family %s*, INIs under %s" % (b.id, b.source, b.style.ini_dir))
    for obj, draws in b.objects(g).items():
        print("\n%s" % obj)
        for d in draws:
            models = [m for m in d.models()]
            if not models:
                continue
            role = "body" if b.is_body(d) else "add-on"
            print("  %s  %-6s %s" % ("[x]" if b.covers(d) else "[ ]", role, d.tag))
            for st in d.states:
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
                    for m in models:
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


def cmd_sheets(a):
    """Recolour the faction's sheets (sagekit/paint/sheets.py) into build/assets/<faction>/_sheets/out,
    four at a time on Blender's Python."""
    import os
    import subprocess
    from concurrent.futures import ThreadPoolExecutor
    from . import paths
    from .formats.textures import dds_info
    from .pipeline import REALESRGAN, game_running
    if game_running() and not a.force:
        print("the game is running - recolouring would take its CPU and GPU. Close it, or pass --force")
        return 1
    style = _style(a.faction)
    g = Install()
    root = os.path.join(paths.BUILD, a.faction, "_sheets")
    todo = [m for m in style.sheets(g) if not a.only or a.only.lower() in m]

    def one(member):
        name = member.split("\\")[-1]
        src = os.path.join(root, "src", name)
        os.makedirs(os.path.dirname(src), exist_ok=True)
        with open(src, "wb") as fh:
            fh.write(g.read(member))
        out = os.path.join(root, "out", *member.split("\\"))
        r = subprocess.run([paths.blender_python(), "-m", "sagekit.paint.sheets", a.faction, src, out,
                            str(style.sheet_size(name)), REALESRGAN], capture_output=True, text=True,
                           cwd=paths.REPO, env=dict(os.environ, PYTHONPATH=paths.REPO))
        if r.returncode:
            return "FAIL %s\n%s" % (name, r.stderr[-1500:])
        i = dds_info(out)
        return "ok   %-28s %4dx%-4d %s" % (name, i["width"], i["height"], i["fourcc"])
    with ThreadPoolExecutor(4) as ex:
        results = list(ex.map(one, todo))
    print("\n".join(results))
    return 1 if any(r.startswith("FAIL") for r in results) else 0


def cmd_install(a):
    from .install import install_faction
    from .pipeline import game_running
    if game_running():
        print("the game is running - close it first (it reads its archives at startup)")
        return 1
    install_faction(a.faction)


def cmd_revert(a):
    from .install import revert_faction
    revert_faction(a.faction)


def _style(faction):
    import importlib
    mod = importlib.import_module("assets.%s.style" % faction)
    return next(v() for v in vars(mod).values() if isinstance(v, type) and getattr(v, "faction", None) == faction)


def main(argv=None):
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
    p = sub.add_parser("sheets")
    p.add_argument("faction")
    p.add_argument("--only")
    p.add_argument("--force", action="store_true")
    for name in ("install", "revert"):
        sub.add_parser(name).add_argument("faction")
    a = ap.parse_args(argv)
    return globals()["cmd_" + a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
