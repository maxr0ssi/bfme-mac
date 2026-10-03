"""The Goblin HUD icons (sagekit/icons, docs/ICONS.md): EA's portrait and button of each building,
shot from ours the way EA framed its own (EA's model through the same camera:
build/assets/goblins/_icons/crops/<image>_ea.png)."""
from sagekit.icons import TOWER, Button, Portrait

TOP = ((0, 1), (0, 1), (0.45, 1))
FLAT = dict(elev=35, ground=True, fill=1.0)      # a low building's button: from above, on its ground

ICONS = {
    "BPWAbandonedMineShaft": Portrait("mine_shaft", azim=-60, elev=25, fill=1.0, at=(0.5, 0.5)),
    "BPWCave": Portrait("cave", azim=-60, elev=20, fill=0.86),
    "BPWFissure": Portrait("fissure", azim=-60, elev=25, fill=0.86),
    "BPWFortress": Portrait("fortress", azim=-60, elev=15, fill=0.86),
    "BPWFortress_ArrowDen": Portrait("arrow_den", azim=-60, elev=20, fill=0.86),
    "BPWFortress_Burrows": Portrait("burrows", azim=-60, elev=25, fill=0.86),
    "BPWSentryTower": Portrait("sentry_tower", azim=-60, **TOWER),
    "BPWSpiderPit": Portrait("spider_pit", azim=-60, elev=25, fill=0.86),
    "BPWTreasureTrove": Portrait("treasure_trove", azim=-60, elev=20, fill=0.86),
    "BWAbandonedMineShaft": Button("mine_shaft", azim=-60, **FLAT),
    "BWCave": Button("cave", azim=-60, focus=TOP),
    "BWFissure": Button("fissure", azim=-60, **FLAT),
    "BWFissure_Giant": Button("giant_sentry", azim=-60, focus=TOP),
    "BWFortress": Button("fortress", azim=-60, focus=TOP),
    "BWFortress_ArrowDen": Button("arrow_den", azim=-60, focus=TOP),
    "BWFortress_Burrows": Button("burrows", azim=-60, **FLAT),
    "BWSentryTower": Button("sentry_tower", azim=-60, focus=((0, 1), (0, 1), (0.55, 1))),
    "BWSpiderPit": Button("spider_pit", azim=-60, **FLAT),
    "BWTreasureTrove": Button("treasure_trove", azim=-60, **FLAT),
}

KEEP = {
    "BCLumberMill": "drawn for the Goblin, Isengard and Mordor mills, each redesigned its own way",
    "BuildingNoArt": "EA's shared stand-in for a building without art",
}
