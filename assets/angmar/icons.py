"""The Angmar HUD icons (sagekit/icons, docs/ICONS.md): RotWK's portraits and buttons of each
building (expansion1icons pages), shot from ours the way EA framed its own (EA's model through
the same camera: build/assets/angmar/_icons/crops/<image>_ea.png)."""
from sagekit.icons import Button, Portrait
from sagekit.icons.walls import beside, run

TOP = ((0, 1), (0, 1), (0.45, 1))
WALL = dict(focus=((0, 1), (0, 1), (0.2, 1)), at=(0.5, 0.6), fill=1.0)     # a wall button: its face, sky above
F = "angmar"

ICONS = {
    "KUFortressPortrait": Portrait("fortress", azim=-60, elev=15, fill=0.86),
    "KUArrowTwrFortPortrait": Portrait("battle_tower", azim=-60, elev=12, fill=0.92),
    "KUBattleTowerPortrait": Portrait("sentry_tower", azim=-60, elev=12, fill=0.8),
    "KUHallPortrait": Portrait("barracks", azim=-60, elev=20, fill=0.86),
    "KUHubFortPortrait": Portrait("fortress_wall_hub", azim=-60, elev=40, fill=0.9),
    "KUKennelPortrait": Portrait("kennel", azim=-60, elev=20, fill=0.86),
    "KUTemplePortrait": Portrait("hallof_twilight_v2", azim=-60, elev=15, fill=0.86),
    "KUTrollDenPortrait": Portrait("den", azim=-60, elev=20, fill=0.86),
    "KUTrollSlingTwrPortrait": Portrait("catapult", azim=-60, elev=15, fill=0.86),
    "KUTrollSlingWallPortrait": Portrait("wall_trebuchet", azim=-20, elev=15, fill=0.85,
                                         extra=beside(F, "wall_trebuchet")),
    "KUArrowTwrWallPortrait": Portrait("wall_tower", azim=-20, elev=15, fill=0.8, extra=beside(F, "wall_tower")),
    "KUPosternGatePortrait": Portrait("wall_postern", azim=-30, elev=35, fill=0.55, extra=beside(F, "wall_postern")),
    "KUWallGatePortrait": Portrait("wall_gate", azim=-20, elev=20, fill=0.85, extra=beside(F, "wall_gate")),
    "KUWallHubPortrait": Portrait("wall_hub", azim=-30, elev=35, fill=0.6, extra=beside(F, "wall_hub")),
    "KUWallSectionPortrait": Portrait("wall_segment", azim=-35, elev=35, fill=0.7, extra=run(F)),
    "KUFortressIcon": Button("fortress", azim=-60, focus=TOP),
    "KUBattleTowerIcon": Button("battle_tower", azim=-60, focus=((0, 1), (0, 1), (0.55, 1))),
    "KUHallOfKingsIcon": Button("barracks", azim=-60, focus=TOP),
    "KUKennelIcon": Button("kennel", azim=-60, elev=10, focus=TOP),
    "KUTempleOfTwilightIcon": Button("hallof_twilight_v2", azim=-60, focus=TOP),
    "KUTrollDenIcon": Button("den", azim=-60, focus=TOP),
    "KUHubBuildWallIcon": Button("wall_segment", azim=-20, elev=0, **WALL, extra=run(F)),
    "KUWallBuildArrowTowerIcon": Button("wall_tower", azim=-20, focus=((0, 1), (0, 1), (0.55, 1)),
                                        extra=beside(F, "wall_tower")),
    "KUWallBuildHubIcon": Button("wall_hub", azim=-20, elev=10, focus=TOP, extra=beside(F, "wall_hub")),
    "KUWallBuildMainGateIcon": Button("wall_gate", azim=-20, focus=((0, 1), (0, 1), (0.5, 1)),
                                      extra=beside(F, "wall_gate")),
    "KUWallBuildPosternGateIcon": Button("wall_postern", azim=0, elev=0, fill=1.15, extra=beside(F, "wall_postern")),
}

KEEP = {
    "BDFortress_Catapult": "the Dwarven catapult button (unit art)",
    "KUWallBuildTrollSlingIcon": "the troll on the sling (unit art)",
}
