"""The Men's HUD icons, Arnor's too (its buildings show Gondor's) (sagekit/icons, docs/ICONS.md):
EA's portrait and button of each building, shot from ours the way EA framed its own (EA's model
through the same camera: build/assets/men/_icons/crops/<image>_ea.png)."""
from sagekit.icons import TOWER, Button, Portrait
from sagekit.icons.walls import beside, run

TOP = ((0, 1), (0, 1), (0.45, 1))
FLAT = dict(elev=35, ground=True, fill=1.0)      # a low building's button: from above, on its ground
WALL = dict(focus=((0, 1), (0, 1), (0.2, 1)), at=(0.5, 0.6), fill=1.0)     # a wall button: its face, sky above
F = "men"

ICONS = {
    "BPFarm": Portrait("farm_level3", azim=-60, elev=30, fill=0.86),
    "BPGArcheryRange": Portrait("archer_range_level3", azim=-60, elev=25, fill=0.86),
    "BPGBarracks": Portrait("barracks_level3", azim=-60, elev=20, fill=0.86),
    "BPGBattleTower": Portrait("keep", azim=-60, **TOWER),
    "BPGBlackSmith": Portrait("forge_level3", azim=-60, elev=20, fill=0.86),
    "BPGFortress": Portrait("fortress", azim=-60, elev=15, fill=0.86),
    "BPGFortress_ArrowTower": Portrait("arrow_tower", azim=-60, elev=12, fill=0.8),
    "BPGFortress_Dormitory": Portrait("garrison_tower", azim=-60, elev=15, fill=0.8),
    "BPGFortress_WallHub": Portrait("fortress_wall_hub", azim=-60, elev=40, fill=0.9),
    "BPGHeroicStatue": Portrait("statue", azim=-60, elev=5, fill=1.0, focus=((0, 1), (0, 1), (0.3, 1))),
    "BPGMarketplace": Portrait("market_place", azim=-60, elev=25, fill=0.86),
    "BPGSentryTwr": Portrait("sentry_tower", azim=-60, elev=12, fill=0.8),
    "BPGStables": Portrait("stable_level3", azim=-60, elev=25, fill=0.86),
    "BPGWell": Portrait("well", azim=-60, elev=25, fill=0.86),
    "BPGWorkshop": Portrait("workshop_level3", azim=-60, elev=20, fill=0.86),
    "BPGWall_ArrowTower": Portrait("wall_tower", azim=-20, elev=15, fill=0.8, extra=beside(F, "wall_tower")),
    "BPGWall_MainGate": Portrait("wall_gate", azim=-20, elev=20, fill=0.85, extra=beside(F, "wall_gate")),
    "BPGWall_PosternGate": Portrait("wall_postern", azim=-30, elev=35, fill=0.55, extra=beside(F, "wall_postern")),
    "BPGWall_Wall": Portrait("wall_segment", azim=-35, elev=35, fill=0.7, extra=run(F)),
    "BPGWall_WallHub": Portrait("wall_hub", azim=-30, elev=35, fill=0.6, extra=beside(F, "wall_hub")),
    "BCFarm": Button("farm_level3", azim=-60, elev=15, focus=TOP),
    "BGBarracks": Button("barracks_level3", azim=-60, focus=TOP),
    "BGBattleTower": Button("keep", azim=-60, focus=((0, 1), (0, 1), (0.55, 1))),
    "BGBlacksmith": Button("forge_level3", azim=-60, focus=TOP),
    "BGFortress": Button("fortress", azim=-60, focus=TOP),
    "BGFortress_ArrowTower": Button("arrow_tower", azim=-60, focus=((0, 1), (0, 1), (0.55, 1))),
    "BGFortress_Dormitory": Button("garrison_tower", azim=-60, focus=TOP),
    "BGFortress_Trebuchet": Button("trebuchet", azim=-60, elev=15, focus=TOP),
    "BGFortress_WallHub": Button("fortress_wall_hub", azim=-60, elev=10, focus=TOP),
    "BGHeroicStatue": Button("statue", azim=-60, elev=0, focus=((0, 1), (0, 1), (0.4, 1)), sky=False),
    "BGMarketplace": Button("market_place", azim=-60, elev=10, focus=TOP),
    "BGSentryTwr": Button("sentry_tower", azim=-60, focus=((0, 1), (0, 1), (0.55, 1))),
    "BGStables": Button("stable_level3", azim=-60, focus=TOP),
    "BGWell": Button("well", azim=-60, **FLAT),
    "BGWorkshop": Button("workshop_level3", azim=-60, focus=TOP),
    "BGWall_ArrowTower": Button("wall_tower", azim=-20, focus=((0, 1), (0, 1), (0.55, 1)), extra=beside(F, "wall_tower")),
    "BGWall_MainGate": Button("wall_gate", azim=0, elev=0, fill=1.05, extra=beside(F, "wall_gate")),
    "BGWall_PosternGate": Button("wall_postern", azim=0, elev=0, fill=1.15, extra=beside(F, "wall_postern")),
    "BGWall_Trebuchet": Button("wall_trebuchet", azim=-20, elev=15, focus=TOP, extra=beside(F, "wall_trebuchet")),
    "BGWall_Wall": Button("wall_segment", azim=-20, elev=0, **WALL, extra=run(F)),
    "BGWall_WallHub": Button("wall_hub", azim=-20, elev=10, focus=TOP, extra=beside(F, "wall_hub")),
}

KEEP = {
    "BGArcheryRange": "an archery target close-up, not the building",
    "BGWall_PosternGateTemp": "a stand-in no button shows",
    "BuildingNoArt": "EA's shared stand-in for a building without art",
}
