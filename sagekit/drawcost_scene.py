"""An 8-player late game in draw costs, EA's art against ours (sagekit/drawcost.py, docs/PERFORMANCE.md §14).

Each player's base: the citadel with three expansions, about fifteen buildings, a few wall pieces,
two builders and four workers (counts below; the 8th player is a second Men base). Soldiers are
EA's art either way and add the same to both sides, so they are left out. What a frame pays:

  - in view (render objects, draws, materials): the base on screen; the shadow-map pass's light
    camera sees a little more, ignored here;
  - map-wide (the particle manager walks every system on the map): all eight bases.
"""
from .drawcost import US

BASES = {
    "dwarves": {"DwarvenFortressCitadel": 1, "DwarvenHallExpansion": 1, "DwarvenCatapultExpansion": 1,
                "DwarvenEreborTowerTowerExpansion": 1, "DwarfBarracks": 2, "DwarvenArcheryRange": 1,
                "DwarvenSiegeWorks": 1, "MineShaft_Interface": 5, "DwarvenHearth": 1, "DwarvenStatue": 1,
                "DwarvenSentryTower_Independent": 2, "DwarvenWallSegmentSmall": 4, "DwarvenWallHubSmall": 2,
                "DwarvenPorter": 2, "DwarvenWorkerNoSelect": 4},
    "elves": {"ElvenCitadel": 1, "ElvenWatchtowerExpansion": 1, "ElvenVigilantEntExpansion": 1,
              "ElvenFloodgateExpansion": 1, "ElvenBarracks": 2, "EregionForge": 1, "ElvenEntMoot": 1,
              "ElvenGreenPasture": 1, "ElvenMallornTree": 5, "ElvenStatue": 1, "ElvenMirrorOfGaladriel": 1,
              "ElvenBattleTower": 1, "ElvenCastleWallSegment": 4, "ElvenCastleWallHub": 2, "ElvenPorter": 2,
              "ElvenWorkerNoSelect": 4},
    "men": {"MenFortressCitadel": 1, "MenArrowTowerExpansion": 1, "MenGarrisonTowerExpansion": 1,
            "MenTrebuchetExpansion": 1, "GondorBarracks": 2, "GondorArcherRange": 1, "GondorStable": 1,
            "GondorWorkshop": 1, "FarmInterface": 5, "GondorForge": 1, "GondorWell": 1, "GondorSentryTower": 1,
            "MenWallSegmentSmall": 4, "MenWallHubSmall": 2, "MenPorter": 2, "GondorWorkerNoSelect": 4},
    "goblins": {"WildFortressCitadel": 1, "WildArrowDenExpansion": 1, "WildGiantSentryExpansion": 1,
                "WildSpiderHolesExpansion": 1, "GoblinCave": 2, "WildSpiderPit": 1, "GoblinFissure": 1,
                "WildTreasureTrove": 1, "WildMineShaft": 3, "WildLumberMill": 2, "WildSentryTower": 2,
                "WildFortressRazorSpines": 1, "WildPorter": 2, "WildLaborerNoSelect": 4},
    "isengard": {"IsengardFortressCitadel": 1, "IsengardTowerExpansion": 1, "IsengardBallistaExpansion": 1,
                 "IsengardMineLauncherExpansion": 1, "IsengardUrukPit": 2, "IsengardWargPit": 1,
                 "IsengardSiegeWorks": 1, "IsengardArmory": 1, "IsengardFurnace": 2, "IsengardLumberMill": 3,
                 "IsengardTavern": 1, "IsengardWargSentry": 1, "IsengardCastleWallSegment": 4,
                 "IsengardCastleWallHub": 2, "IsengardPorter": 2, "IsengardWorkerNoSelect": 4},
    "mordor": {"MordorFortressCitadel": 1, "MordorGateWatchersExpansion": 1, "MordorWallCatapultExpansion": 1,
               "MordorFortressLavaMoat": 1, "MordorOrcPit": 2, "MordorTrollCage": 1, "MordorSiegeWorks": 1,
               "MordorHaradrimPalace": 1, "MordorMumakilPen": 1, "MordorLumberMill": 2,
               "MordorSlaughterHouse": 3, "MordorTavern": 1, "MordorBattleTower": 1, "MordorPorter": 2,
               "MordorWorkerNoSelect": 4},
    "angmar": {"AngmarFortressCitadel": 1, "AngmarBattleTowerExpansion": 1, "AngmarCatapultExpansion": 1,
               "AngmarKennelExpansion": 1, "AngmarBarracks": 2, "AngmarDen": 1, "AngmarHallofTwilight": 1,
               "AngmarForgeWorks": 1, "AngmarMill": 5, "AngmarSentryTower_Independent": 2,
               "AngmarWallSegmentSmall": 4, "AngmarWallHubSmall": 2, "AngmarPorter": 2,
               "AngmarWorkerNoSelect": 4},
}
PLAYERS = ["dwarves", "elves", "men", "goblins", "isengard", "mordor", "angmar", "men"]
KEYS = ("objects", "main", "shadow", "tris", "systems", "particles")
CAP = 4000                      # MaxParticleCount at UltraHigh (gamelod.ini); the oldest go first above it


def base_cost(rows, faction, side):
    """Sums over one base for side 'ea' or 'ours'; materials once per base (copies share a batch)."""
    by = {}
    for r in rows:
        by.setdefault(r["object"], r)
    tot = {k: 0.0 for k in KEYS}
    tot.update(materials=set(), missing=[])
    for obj, n in BASES[faction].items():
        r = by.get(obj)
        c = r and r["healthy"][side]
        if not c:
            tot["missing"].append(obj)
            continue
        for k in KEYS:
            tot[k] += n * c[k]
        tot["materials"] |= c["materials"]
    view = 2 * US["object"] * tot["objects"] + US["fx_main"] * tot["main"] + US["fx_shadow"] * tot["shadow"] \
        + US["batch"] * len(tot["materials"])
    tot["view_ms"] = view / 1000.0
    tot["map_ms"] = (US["system"] * tot["systems"] + US["particle"] * tot["particles"]) / 1000.0
    tot["gl_draws"] = tot["main"] + tot["shadow"]
    return tot


def report(rows):
    print("\n8-player late game (one base: citadel + 3 expansions, ~15 buildings, 6 wall pieces, 2 builders, 4 workers)")
    print("%-9s %15s %15s %15s %19s %15s %17s %17s" % ("base", "objects EA/ours", "draws EA/ours", "materials",
                                                      "tris EA/ours", "systems", "particles", "view ms EA/ours"))
    tot = {"ea": {k: 0.0 for k in KEYS + ("map_ms",)}, "ours": {k: 0.0 for k in KEYS + ("map_ms",)}}
    views = {"ea": [], "ours": []}
    for f in sorted(BASES):
        e, o = base_cost(rows, f, "ea"), base_cost(rows, f, "ours")
        n = PLAYERS.count(f)
        for side, c in (("ea", e), ("ours", o)):
            for k in KEYS + ("map_ms",):
                tot[side][k] += n * c[k]
            views[side].append(c["view_ms"])
        print("%-9s %15s %15s %15s %19s %15s %17s %17s %s" % (
            f, "%d/%d" % (e["objects"], o["objects"]), "%d/%d" % (e["gl_draws"], o["gl_draws"]),
            "%d/%d" % (len(e["materials"]), len(o["materials"])), "%d/%d" % (e["tris"], o["tris"]),
            "%d/%d" % (e["systems"], o["systems"]), "%.0f/%.0f" % (e["particles"], o["particles"]),
            "%.2f/%.2f" % (e["view_ms"], o["view_ms"]), ("missing: " + ", ".join(o["missing"])) if o["missing"] else ""))
    for side in ("ea", "ours"):
        t = tot[side]
        t["map_ms"] = (US["system"] * t["systems"] + US["particle"] * min(t["particles"], CAP)) / 1000.0
        print("%-4s 8 bases: %d render objects, %d draws (main %d + shadow %d), %d tris, %d particle systems, "
              "%.0f live particles (cap 4,000 at UltraHigh); map-wide particle render %.2f ms, a base in view %.2f ms" % (
                  side.upper(), t["objects"], t["main"] + t["shadow"], t["main"], t["shadow"], t["tris"],
                  t["systems"], t["particles"], t["map_ms"], sum(views[side]) / len(views[side])))
    return tot
