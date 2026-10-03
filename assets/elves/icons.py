"""The Elven HUD icons (sagekit/icons, docs/ICONS.md): EA's portrait and button of each building,
shot from ours the way EA framed its own (EA's model through the same camera:
build/assets/elves/_icons/crops/<image>_ea.png)."""
from sagekit.icons import TOWER, Button, Portrait
from sagekit.icons.walls import beside, run

TOP = ((0, 1), (0, 1), (0.45, 1))
FLAT = dict(elev=35, ground=True, fill=1.0)      # a low building's button: from above, on its ground
WALL = dict(focus=((0, 1), (0, 1), (0.2, 1)), at=(0.5, 0.6), fill=1.0)     # a wall button: its face, sky above
F = "elves"

ICONS = {
    "BPEBarracks": Portrait("barracks", azim=20, elev=15, fill=0.86),
    "BPEBattleTower": Portrait("battle_tower", azim=-60, **TOWER),
    "BPEEntMoot": Portrait("ent_moot", azim=-60, elev=25, fill=0.86),
    "BPEEregionForge": Portrait("forge", azim=0, elev=15, fill=0.86),
    "BPEFortress": Portrait("fortress", azim=-60, elev=15, fill=0.86),
    "BPEFortress_BattleTower": Portrait("watchtower", azim=-60, **TOWER),
    "BPEFortress_FloodGate": Portrait("floodgate", azim=-60, elev=20, fill=0.86,
                                      extra=(("floodgate_doors", (0, 0, 0), 0),)),
    "BPEFortress_WallHub": Portrait("fortress_wall_hub", azim=-60, elev=40, fill=0.78),
    "BPEGreenPasture": Portrait("green_pasture_fence", azim=-60, elev=30, fill=0.86),
    "BPEHeroicStatue": Portrait("statue", azim=-60, elev=5, fill=1.0, focus=((0, 1), (0, 1), (0.3, 1))),
    "BPEMallornTree": Portrait("mallorn_tree", azim=-60, elev=12, fill=0.86),
    "BPEMirrorGaladriel": Portrait("mirror_of_galadriel", azim=-60, elev=25, fill=0.48, at=(0.47, 0.38),
                                   frame=("EBGALMIRR2", "EBGALMIRR3")),      # the basin, as EA's: the stairs run out
    "BPEWall": Portrait("wall_segment", azim=-35, elev=35, fill=0.7, extra=run(F)),
    "BPEWall_MainGate": Portrait("wall_gate", azim=-20, elev=20, fill=0.85, extra=beside(F, "wall_gate")),
    "BPEWall_WallHub": Portrait("wall_hub", azim=-30, elev=35, fill=0.6, extra=beside(F, "wall_hub")),
    "BEBattleTower": Button("battle_tower", azim=-60, focus=TOP),
    "BEElvenBarracks": Button("barracks", azim=20, elev=5, frame=("NBELVNBARXA",), focus=((0, 1), (0, 1), (0.1, 0.9))),
    "BEEntMoot": Button("ent_moot", azim=-60, **FLAT),
    "BEEregionForge": Button("forge", azim=0, focus=TOP),
    "BEFortress": Button("fortress", azim=-60, focus=TOP),
    "BEGreenPasture": Button("green_pasture_fence", azim=-60, **FLAT),
    "BEHeroicStatue": Button("statue", azim=-60, elev=0, focus=((0, 1), (0, 1), (0.4, 1)), sky=False),
    "BEMallornTree": Button("mallorn_tree", azim=-60, focus=TOP),
    "BEMirrorGaladriel": Button("mirror_of_galadriel", azim=-60, elev=15, focus=TOP),
    "BEWall_BuildWall": Button("wall_segment", azim=-20, elev=0, **WALL, extra=run(F)),
    "BEWall_MainGate": Button("wall_gate", azim=-20, frame=("EBWALLGATEN",), **WALL, extra=beside(F, "wall_gate")),
    "BEWall_WallHub": Button("wall_hub", azim=-20, elev=10, focus=TOP, extra=beside(F, "wall_hub")),
}

KEEP = {
    "BEEntMoot_Ents": "the Ents (unit art)",
    "BGWorkshop_Trebuchet": "the Men's trebuchet (unit art)",
    "BuildingNoArt": "EA's shared stand-in for a building without art",
}
