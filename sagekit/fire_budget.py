"""The fire budget: at most BUDGET live particles of our fire per building, in its worst state
(docs/ART.md "Fire budget", docs/PERFORMANCE.md §15).

Our fire burns the same points with the same systems in every state it burns in (healthy, damaged,
snow; sagekit/fire.py), so a building's worst state is its fire: the sum over its fire points of
each system's live particles at steady state (sagekit/drawcost.py Rates: BurstCount / BurstDelay x
Lifetime, means), read from EA's particle INIs with our own systems added as the packs ship them.
EA's own effects on the same object (its damage fire, a furnace's own flames, spells) are EA's
and not counted against it. Night lights are meshes, no particles.

Eight late-game bases at the budget's worst stay under the engine's 4,000-particle cap with EA's
own effects beside them; `python3 -m sagekit.drawcost_report --scene` has the estimate.

    sagekit validate        every recipe (the game's INIs needed) and every staged object
    the check suite         the building's own (sagekit/fire_checks.py)
    python3 -m sagekit.fire_budget [<faction/building> ...]     the table
"""
import sys

BUDGET = 60


def rates(install):
    """drawcost.Rates over the two particle INIs the game loads, ours added to fxparticlesystem.ini."""
    from . import fire_systems
    from .drawcost import Rates
    from .formats.ini import apply_ops
    texts = []
    for m in fire_systems.LOADED:
        if install.owner(m):
            text = install.read(m).decode("latin-1")
            texts.append(apply_ops(text, [fire_systems.ops(install)]) if m == fire_systems.MEMBER else text)
    return Rates(texts)


def per_point(b, r):
    """[(bone, kind, live particles)] of b's fire points."""
    from .fire import KINDS, points
    return [(bone, kind, sum(r.live(s) for s in KINDS[kind])) for bone, _, kind in points(b)]


def live(b, r):
    return sum(n for _, _, n in per_point(b, r))


def problem(b, r):
    """Why b's fire breaks the budget, or None."""
    n = live(b, r)
    if n <= BUDGET:
        return None
    pts = per_point(b, r)
    return "fire %.0f live particles over the budget of %d (%d points: %s)" % (
        n, BUDGET, len(pts), ", ".join("%s %s %.1f" % p for p in pts))


def main(argv):
    from . import registry
    from .game import Install
    r = rates(Install())
    ids = argv or registry.building_ids()
    rows = []
    for bid in ids:
        b = registry.load(bid)
        pts = per_point(b, r)
        if pts:
            rows.append((sum(n for _, _, n in pts), bid, len(pts)))
    for n, bid, k in sorted(rows, reverse=True):
        print("%-4s %6.1f  %-46s %2d points" % ("OVER" if n > BUDGET else "ok", n, bid, k))
    print("%d buildings with fire, %d over %d; all fire points together %.0f live particles" % (
        len(rows), sum(1 for n, _, _ in rows if n > BUDGET), BUDGET, sum(n for n, _, _ in rows)))
    return 1 if any(n > BUDGET for n, _, _ in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
