"""The fire budget: our fire per building in live particles, in its worst state (docs/ART.md "Fire
budget", docs/PERFORMANCE.md §15). Since the fire reduction (Max, 2026-10-05: "I think fires we should
reduce on most buildings") a building whose fire is what it is (IDENTITY: forges, furnaces, smithies,
lava, the Mordor and Isengard citadel crowns, Angmar's cold fire on its key buildings) burns at most
IDENTITY_BUDGET; every other building at most BUDGET: one small brazier (flame and smoke, 6.0) or a
pair of torches (3.0 each) where a light matters at night, mostly none.

    IDENTITY_BUDGET 20  about two of EA's single fires (a lean furnace 9.7 + a crucible 5.5, a chimney 13.1
                        + two coal glows): one bold point and a second, small and tight. Eight bases at
                        both caps on every building stay well under the engine's 4,000-particle cap.
    BUDGET 6            exactly one lean brazier, or two torches, or one forge glow.

Our fire burns the same points with the same systems in every state it burns in (healthy, damaged,
snow; sagekit/fire.py), so a building's worst state is its fire: the sum over its fire points of
each system's live particles at steady state (sagekit/drawcost.py Rates: BurstCount / BurstDelay x
Lifetime, means), read from EA's particle INIs with our own systems added as the packs ship them.
EA's own effects on the same object (its damage fire, a furnace's own flames, spells) are EA's and
not counted against it. Night lights are meshes, no particles.

    sagekit validate        every recipe (the game's INIs needed) and every staged object's fire rig
    the check suite         the building's own (sagekit/fire_checks.py)
    python3 -m sagekit.fire_budget [<faction/building> ...]     the table
"""
import sys

BUDGET = 6                  # every other building (the fire budget was 60 for all, 2026-10-04)
IDENTITY_BUDGET = 20
# the buildings whose fire is their identity: id -> what burns
IDENTITY = {
    "elves/forge": "the forge's embers out of its chimney",
    "isengard/fortress": "the point crown's fire-pot and the two forge walks' furnaces",
    "isengard/furnace": "the smelter stack's fire, the furnace mouth and the forge hearth",
    "isengard/siege_works": "the two forge furnaces",
    "isengard/armory": "the smithy's furnace and crucible",
    "isengard/fortress_burning_forges_destructibles": "the Burning Forges: their chimney and crucible",
    "mordor/fortress": "the four green crowns",
    "mordor/siege_works": "the furnace and a forge",
    "mordor/fortress_lava_moat": "the lava moat's embers and smoke",
    "mordor/fortress_magma_cauldrons": "the magma cauldrons",
    "angmar/fortress": "the cold fire in the crown's craters and the front braziers",
    "angmar/fortress_sanctum": "the cold fire in the sanctum's ice blooms",
    "angmar/hallof_twilight": "the cold fire on the sorcerers' altar",
}


def budget(bid):
    return IDENTITY_BUDGET if bid in IDENTITY else BUDGET


def rig_budgets():
    """{fire rig name (lower case): its building's budget} over every recipe with fire points."""
    from . import registry
    from .fire import points, rig_name
    out = {}
    for bid in registry.building_ids():
        b = registry.load(bid)
        if points(b):
            out[rig_name(b).lower()] = budget(bid)
    return out


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
    n, cap = live(b, r), budget(b.id)
    if n <= cap + 1e-6:
        return None
    pts = per_point(b, r)
    return "fire %.1f live particles over the budget of %d (%d points: %s)" % (
        n, cap, len(pts), ", ".join("%s %s %.1f" % p for p in pts))


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
    over = [bid for n, bid, _ in rows if n > budget(bid) + 1e-6]
    for n, bid, k in sorted(rows, reverse=True):
        print("%-4s %6.1f / %2d  %-46s %2d points  %s" % ("OVER" if bid in over else "ok", n, budget(bid), bid, k,
                                                           IDENTITY.get(bid, "")))
    print("%d buildings with fire (%d identity, budget %d; the rest %d), %d over; all fire points together %.0f "
          "live particles" % (len(rows), sum(1 for _, bid, _ in rows if bid in IDENTITY), IDENTITY_BUDGET, BUDGET,
                              len(over), sum(n for n, _, _ in rows)))
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
