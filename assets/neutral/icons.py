"""The neutral HUD icons (sagekit/icons, docs/ICONS.md): the Inn's portrait, shot from ours the way
EA framed its own (EA's model through the same camera: build/assets/neutral/_icons/crops/
BPCInn_ea.png). The other capturable buildings and the lairs join as their recipes are reviewed."""
from sagekit.icons import Portrait

ICONS = {
    "BPCInn": Portrait("inn", azim=-75, elev=35, fill=0.92),
}

KEEP = {
    "BPCDrakeLair": "not reviewed yet", "BPCGoblinLair": "not reviewed yet", "BPCOutpost": "not reviewed yet",
    "BPCRuinedTower": "not reviewed yet", "BPCShipwright": "not reviewed yet", "BPCSignalFire": "not reviewed yet",
    "BPCSpiderLair": "not reviewed yet", "BPCTrollLair": "not reviewed yet", "BPCWargLair": "not reviewed yet",
}
