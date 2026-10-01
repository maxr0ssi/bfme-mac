"""What the Hall of Twilight's level pieces (hallof_twilight_top, _v1, _v2) share: the review views
(the same cameras at every level, so the levels compare) and the meshes each level does not show
(left out of its bakes and renders). EA's SubObjectsUpgrades: level 1 shows TOP_1 and ROCKS_1;
level 2 V1 (hides TOP_1, ROCKS_1); level 3 V2 and RUNEGLOWV2 (hides V1). The rune glow and the night
window stay out of every bake (glow cards)."""

VIEWS = {
    "rts": ((-1.1, -5.7, 34.0), 430, 50, -38, 50),
    "close": ((0.0, -8.0, 76.0), 200, 24, -30, 45),
    "ingame": ((-1.1, -5.7, 34.0), 900, 53, -62, 50),
}
HIDDEN = {
    1: ("V1", "V2", "RUNEGLOWV2", "N_WINDOW"),
    2: ("TOP_1", "ROCKS_1", "V2", "RUNEGLOWV2", "N_WINDOW"),
    3: ("TOP_1", "ROCKS_1", "V1", "RUNEGLOWV2", "N_WINDOW"),
}
