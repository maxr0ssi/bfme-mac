"""python3 -m sagekit <command>

    list                               every building under assets/
    validate                           load every building; taxonomy, names and budget rules
    inventory <faction/building>       its lifecycle as the game defines it, and what exists
    budget [faction]                   memory the own textures take, per faction
    build <faction/building> [--from STEP] [--to STEP]
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
    a = ap.parse_args(argv)
    return globals()["cmd_" + a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
