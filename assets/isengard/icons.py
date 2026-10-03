"""The Isengard HUD icons (sagekit/icons, docs/ICONS.md): EA's portrait and button of each building,
shot from ours the way EA framed its own (EA's model through the same camera:
build/assets/isengard/_icons/crops/<image>_ea.png)."""
from sagekit.icons import TOWER, Button, Portrait
from sagekit.icons.walls import beside, run

TOP = ((0, 1), (0, 1), (0.45, 1))
FLAT = dict(elev=35, ground=True, fill=1.0)      # a low building's button: from above, on its ground
WALL = dict(focus=((0, 1), (0, 1), (0.2, 1)), at=(0.5, 0.6), fill=1.0)     # a wall button: its face, sky above
F = "isengard"

ICONS = {
    "BPIArmory": Portrait("armory", azim=-60, elev=20, fill=0.86),
    "BPIBattleTwr": Portrait("battle_tower", azim=-60, **TOWER),
    "BPIFortress": Portrait("fortress", azim=-60, elev=15, fill=0.86),
    "BPIFortress_BattleTower": Portrait("tower", azim=-60, **TOWER),
    "BPIFortress_WallHub": Portrait("fortress_wall_hub", azim=-60, elev=40, fill=0.9),
    "BPISiegeWorks": Portrait("siege_works", azim=-60, elev=20, fill=0.86),
    "BPIUrukPit": Portrait("uruk_pit", azim=-60, elev=25, fill=0.86),
    "BPIWargPit": Portrait("warg_pit", azim=-60, elev=25, fill=0.86),
    "BPIWargSentry": Portrait("warg_sentry", azim=-60, elev=25, fill=0.95),
    "BPIWall": Portrait("wall_segment", azim=-35, elev=35, fill=0.7, extra=run(F)),
    "BPIWall_MainGate": Portrait("wall_gate", azim=-5, elev=15, fill=0.9, extra=beside(F, "wall_gate")),
    "BPIWall_WallHub": Portrait("wall_hub", azim=-30, elev=35, fill=0.6, extra=beside(F, "wall_hub")),
    "BCFurnace": Button("furnace", azim=-60, focus=TOP),
    "BIArmory": Button("armory", azim=-60, focus=TOP),
    "BIFortress": Button("fortress", azim=-60, focus=TOP),
    "BIFortress_ArrowTower": Button("tower", azim=-60, focus=((0, 1), (0, 1), (0.55, 1))),
    "BIFortress_MineLauncher": Button("mine_launcher", azim=-60, elev=10, focus=TOP),
    "BISiegeWorks": Button("siege_works", azim=-60, focus=TOP),
    "BIUrukPit": Button("uruk_pit", azim=-60, elev=10, focus=TOP),
    "BIWargSentry": Button("warg_sentry", azim=-60, **FLAT),
    "BIWatchTower": Button("battle_tower", azim=-60, focus=((0, 1), (0, 1), (0.55, 1))),
    "BIWall_BuildWall": Button("wall_segment", azim=-20, elev=0, **WALL, extra=run(F)),
    "BIWall_Wall": Button("wall_segment", azim=-20, elev=0, **WALL, extra=run(F)),
    "BIWall_MainGate": Button("wall_gate", azim=-20, focus=((0, 1), (0, 1), (0.5, 1)), extra=beside(F, "wall_gate")),
    "BIWall_WallHub": Button("wall_hub", azim=-20, elev=10, focus=TOP, extra=beside(F, "wall_hub")),
}

KEEP = {
    "BIWargPit": "a warg (unit art)",
    "BCLumberMill": "drawn for the Goblin, Isengard and Mordor mills, each redesigned its own way",
    "BISiegeWorks_SeigeBallista": "the siege ballista (unit art)",
    "BuildingNoArt": "EA's shared stand-in for a building without art",
}
