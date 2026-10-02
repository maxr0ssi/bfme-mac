"""The Dwarven HUD icons (sagekit/icons, docs/ICONS.md): EA's portrait and button of each building,
shot from our building the way EA framed its own (each camera checked by rendering EA's model
through it beside EA's icon: build/assets/dwarves/_icons/calibrate.jpg)."""
from sagekit.icons import Button, Portrait

# walls run along y: a segment is 38 long, a hub 45, the gate 122.4 (their shipped models' boxes)
RUN = (("wall_segment", (0, 38, 0), 0), ("wall_segment", (0, 76, 0), 0), ("wall_segment", (0, -38, 0), 0),
       ("wall_segment", (0, -76, 0), 0))


def run_beside(half):
    """Wall segments either side of a piece `half` long from its centre to each end."""
    return tuple(("wall_segment", (0, s * (half + 19 + 38 * k), 0), 0) for s in (1, -1) for k in (0, 1))


TOP = ((0, 1), (0, 1), (0.45, 1))           # a button's usual focus: the top half
STATUE = ("THORIN", "THORINKINGGEAR", "RAVENBLADE", "SHIELD")

ICONS = {
    # portraits: 192 x 192, sepia, the whole building on its ground
    "BPDArcheryRange": Portrait("archery_obelisks", azim=-60, elev=30, fill=0.95),
    "BPDCitadel": Portrait("citadel", azim=-65, elev=10, fill=0.86),
    "BPDForgeWorks": Portrait("siege_works", azim=-60, elev=25, fill=0.86),
    "BPDFortress_WallHub": Portrait("fortress_wall_hub", azim=-60, elev=45, fill=1.0, at=(0.55, 0.55)),
    "BPDFortress_Bunker": Portrait("hall", azim=-60, elev=18, fill=0.8),
    "BPDFortress_AxeTower": Portrait("erebor_tower", azim=-60, elev=8, fill=0.86),
    "BPDFortress": Portrait("fortress", azim=-60, elev=12, fill=0.82, at=(0.5, 0.48)),
    "BPDHallofWarriors": Portrait("barracks", azim=-60, elev=15, fill=0.86),
    "BPDHearth": Portrait("hearth", azim=-15, elev=25, fill=0.95),
    "BPDHeroicStatue": Portrait("statue", azim=-20, elev=5, fill=0.95, frame=STATUE, focus=((0, 1), (0, 1), (0.25, 1))),
    "BPDMineShaft": Portrait("mine", azim=-25, elev=15, fill=0.9),
    "BPDSentryTower": Portrait("sentry_tower", azim=-60, elev=12, fill=0.8),
    "BPDUndermine": Portrait("mine_underground", azim=-30, elev=10, fill=0.9),
    "BPDWall_WallHub": Portrait("wall_hub", azim=-30, elev=35, fill=0.6, extra=run_beside(22.5)),
    "BPDWall": Portrait("wall_segment", azim=-35, elev=35, fill=0.7, extra=RUN),
    "BPDWall_Gate": Portrait("wall_gate", azim=-10, elev=20, fill=0.85, extra=run_beside(61.2)),
    "BPDWall_AxeTower": Portrait("wall_tower", azim=-15, elev=15, fill=0.85, extra=run_beside(19)),
    "BPDWall_PosternGate": Portrait("wall_postern", azim=-30, elev=35, fill=0.55, extra=run_beside(19)),
    # buttons: 64 x 64 (the wall page's 59 x 59), round, a low close-up against the sky
    "BDArcheryRange": Button("archery_obelisks", azim=-60, frame=("V2",), focus=((0, 1), (0, 1), (0.4, 1))),
    "BDForgeWorks": Button("siege_works", azim=-45, frame=("V2",), focus=((0, 1), (0, 1), (0.3, 1)), fill=1.05),
    "BDFortress": Button("fortress", azim=-60, focus=TOP),
    "BDFortress_AxeTower": Button("erebor_tower", azim=-60, focus=((0, 1), (0, 1), (0.6, 1))),
    "BDFortress_Bunker": Button("hall", azim=-60, focus=TOP),
    "BDHallWarriors": Button("barracks", azim=-60, frame=("V1",)),
    "BDHearth": Button("hearth", azim=0, elev=10, fill=1.1, focus=((0, 1), (0, 1), (0.15, 1)), sky=False),
    "BDHeroicStatue": Button("statue", azim=-15, elev=0, frame=STATUE, focus=((0, 1), (0, 1), (0.4, 1)), fill=1.05,
                             sky=False),
    "BDMineShaft": Button("mine", azim=4, elev=8, frame=("DBMINE02",), fill=1.1, sky=False),
    "BDSentryTower": Button("sentry_tower", azim=-60, focus=((0, 1), (0, 1), (0.6, 1))),
    "BDWall_PosternGate": Button("wall_postern", azim=0, elev=0, fill=1.15, extra=run_beside(19)),
    "BDWall_WallHub": Button("wall_hub", azim=-20, elev=10, focus=TOP, extra=run_beside(22.5)),
    "BDWall_AxeTower": Button("wall_tower", azim=-20, frame=("DBWALLTWRN",), focus=((0, 1), (0, 1), (0.6, 1)),
                              extra=run_beside(19)),
    "BDWall_BuildWall": Button("wall_segment", azim=-20, elev=0, focus=TOP, fill=1.2, extra=RUN),
    "BDWall_Gate": Button("wall_gate", azim=-10, focus=((0, 1), (0, 1), (0.5, 1)), extra=run_beside(61.2)),
}

# building art on the Dwarven pages that stays EA's
KEEP = {
    "BPDFortress_BuildPlot": "the expansion pad: no recipe redesigns it",
    "BDDwarvenBattleTower": "no button or object shows it",
    "BDFortress_Catapult": "the catapult on the tower: unit art (the catapult tower's model has no catapult)",
    "BDWall_Catapult": "the same catapult (unit art)",
    "BuildingNoArt": "EA's shared stand-in for a building without art",
}
