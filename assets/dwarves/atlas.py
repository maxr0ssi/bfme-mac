"""DBFortress1: the sheet every Dwarven building is painted on (fortress, walls, towers, barracks,
forge, mine...). Regions measured on the 512 original; mask hints on its 2048 upscale."""
from sagekit.atlas import Atlas, Region

HEX_W = 399 - 193


class DwarvenAtlas(Atlas):
    texture = "DBFortress1.tga"
    normal = "DBFortress1_NRM.tga"
    regions = {                                   # order matters: face tags are indices into it
        "stoneA": Region((72, 398, 404, 508)),    # big plain wall stone under the rune band
        "stoneB": Region((416, 346, 494, 508)),   # plain stone, right column
        "top": Region((58, 3, 188, 44)),          # walkway-top stone (lighter)
        "trim": Region((68, 350, 232, 357), Region.BAND, su=3.0),       # light coping strip
        "rune": Region((30, 360, 262, 388), Region.BAND, su=5.0),       # rune frieze
        "tri": Region((276, 359, 396, 388), Region.BAND, period=40.0),  # triangle frieze
        "hex": Region((193, 56, 399, 78), Region.BAND, period=HEX_W / 3.0),  # hexagon chain
        "pilaster": Region((43, 256, 50, 345), Region.STRETCH),         # vertical pilaster strip
        "statue": Region((196, 240, 222, 345), Region.STRETCH),         # dwarf statue in its niche
    }
    mask_hints = {
        "rune": [(96, 1424, 1048, 1556)],
        "tri": [(1030, 1424, 1652, 1560), (700, 1024, 768, 1386), (1262, 1322, 1626, 1386)],
        "hex": [(770, 188, 1600, 332)],
        "grille": [(562, 742, 772, 902)],
        "rock": [(515, 350, 1600, 640), (1318, 620, 1428, 842), (1400, 640, 1600, 700)],
        "tiles": [(1060, 648, 1346, 846)],
        "strap": [(247, 525, 256, 676), (318, 525, 327, 676), (1724, 108, 1940, 117), (1724, 268, 1940, 277)],
        "stone": [(90, 1560, 1652, 2048), (1652, 1180, 2048, 2048)],
        "plate": [(860, 0, 1236, 188)],     # the round bronze disc (the catapult tower's platform floor)
    }
