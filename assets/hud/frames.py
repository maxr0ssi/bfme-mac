"""The palantir textures we repaint (stdlib only: sagekit/hud reads this table).

Each texture is an APT movie's image: art\\textures\\apt_<movie>_<id>.tga, which the movie's .dat
maps image ids onto and its geometry (.ru) draws with pixel-space texture matrices
(docs/HUD.md). Kinds:

  frame  a palantir frame: recoloured whole by its side's look, its rings drawn again
         (ring: name, a centre guess and the radii its metal lies between, 1x pixels)
  atlas  a sheet of parts: upscaled whole; only `parts` (rect, side) are recoloured, and in them only
         the metal (bronze, gold, iron), never a button's coloured emblem or a glow

Everything listed ships at 1x (EA's size) and at 2x with its geometry's texture matrices doubled.
"""

FRAMES = {
    # RotWK's Good palantir: minimap and unit portrait, and minimap alone
    ("PalantirExport", 17): dict(kind="frame", side="good", what="Good palantir, minimap and portrait",
                                 rings=[("minimap", (127.5, 128.5), (95, 135)), ("portrait", (286.5, 148.5), (66, 110))]),
    ("PalantirExport", 20): dict(kind="frame", side="good", what="Good palantir, minimap alone",
                                 rings=[("minimap", (127.5, 128.5), (95, 135))]),
    # the Evil side's: blackened iron
    ("PalantirExport", 11): dict(kind="frame", side="evil", what="Evil palantir, minimap and portrait",
                                 rings=[("minimap", (127.5, 128.5), (95, 135)), ("portrait", (286.5, 148.5), (66, 110))]),
    ("PalantirExport", 14): dict(kind="frame", side="evil", what="Evil palantir, minimap alone",
                                 rings=[("minimap", (127.5, 128.5), (95, 135))]),
    # the glass, the glows and the round buttons over the minimap: both sides draw these. Only
    # sharpened: recoloured, the sockets' silver-gold rims came out duller than EA's (review v1)
    ("Palantir", 1): dict(kind="atlas", what="minimap glass, glows, round buttons and their sockets",
                          parts=[]),
    # the portrait's chain of button rings, the side bar's brackets and scrolls (both sides)
    ("libInGameImagesMain", 1): dict(kind="atlas", what="portrait button rings, brackets, medallion bezels",
                                     parts=[((1, 125, 131, 327), "good"), ((412, 125, 536, 241), "good"),
                                            ((413, 224, 489, 295), "good"), ((934, 186, 1016, 334), "good"),
                                            ((337, 268, 393, 339), "good"), ((620, 262, 674, 326), "good"),
                                            ((752, 256, 795, 323), "good"), ((0, 296, 1024, 460), "good")]),
}


def key(movie, tid):
    return "%s_%d" % (movie.lower(), tid)


def texture_member(movie, tid):
    return "art\\textures\\apt_%s_%d.tga" % (movie.lower(), tid)
