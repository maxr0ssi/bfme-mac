"""The Mordor HUD icons (sagekit/icons, docs/ICONS.md): EA's portrait and button of each building,
shot from ours the way EA framed its own (EA's model through the same camera:
build/assets/mordor/_icons/crops/<image>_ea.png)."""
from sagekit.icons import TOWER, Button, Portrait

TOP = ((0, 1), (0, 1), (0.45, 1))
FLAT = dict(elev=35, ground=True, fill=1.0)      # a low building's button: from above, on its ground

ICONS = {
    "BPMBattleTower": Portrait("battle_tower", azim=-60, **TOWER),
    "BPMFortress": Portrait("fortress", azim=-60, elev=15, fill=0.86),
    "BPMFortress_Barricade": Portrait("fortress_barricade", azim=-60, elev=25, fill=0.86),
    "BPMFortress_GateWatcher": Portrait("gate_watchers", azim=-60, elev=12, fill=0.86),
    "BPMGreatSiegeWorks": Portrait("siege_works", azim=-60, elev=20, fill=0.86),
    "BPMHaradrimPalace": Portrait("haradrim_palace", azim=-60, elev=20, fill=0.86),
    "BPMMumakilPen": Portrait("mumakil_pen", azim=-60, elev=25, fill=0.86),
    "BPMOrcPit": Portrait("orc_pit", azim=-60, elev=25, fill=0.86),
    "BPMTavern": Portrait("tavern", azim=-60, elev=20, fill=0.86),
    "BPMTrollCages": Portrait("troll_cage", azim=-60, elev=25, fill=0.86),
    "BCSlaughterHouse": Button("slaughter_house", azim=-60, focus=TOP),
    "BMBattleTower": Button("battle_tower", azim=-60, focus=((0, 1), (0, 1), (0.55, 1))),
    "BMFortress": Button("fortress", azim=-60, focus=TOP),
    "BMFortress_GateWatchers": Button("gate_watchers", azim=-60, focus=TOP),
    "BMGreatSiegeWorks": Button("siege_works", azim=-60, focus=TOP),
    "BMHaradrimPalace": Button("haradrim_palace", azim=-60, focus=TOP),
    "BMMumakilPen": Button("mumakil_pen", azim=-60, elev=10, focus=TOP),
    "BMOrcPit": Button("orc_pit", azim=-60, **FLAT),
    "BMTavern": Button("tavern", azim=-60, focus=TOP),
    "BMTrollCages": Button("troll_cage", azim=-60, **FLAT),
}

KEEP = {
    "BMFortress_Catapult": "a catapult firing (unit art)",
    "BCLumberMill": "drawn for the Goblin, Isengard and Mordor mills, each redesigned its own way",
    "BuildingNoArt": "EA's shared stand-in for a building without art",
}
