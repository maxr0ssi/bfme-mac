"""IBFortress (1024): Isengard's master sheet, and where its materials are.

EA painted Isengard almost entirely as teal-grey metal: ribbed and fluted wall plates, spiked
cornices, riveted frames, great blade-shaped buttresses. Among it: smooth dark wall panels (the
keep's and the curtain's big faces), rough rock and trodden earth (the ground pieces, top left),
speckled granite and cobbles, timber planks and posts (top right), crates, a White Hand banner
(72..135, 197..282) and two patches of glowing coals. Colour alone cannot tell the smooth panels
from the plates (both teal-grey, low saturation), so the materials are declared here:

    materials   {material: [(x0, y0, x1, y1)]} in the sheet's pixels (y down): stone (the smooth
                panels: Orthanc stone), rock, wood, mark (the White Hand banner). Everything else
                is iron; embers are found by colour (assets/isengard/paint.py IsengardRecolour).
    mask_hints  one "stone" hint over the whole upscale: the stock masks stay out of the way.

Regions for new faces (the kit, shapes.py): the smooth panels (stoneA, stoneB: faceted Orthanc
stone), rock, a plain beaten plate (iron), a ribbed plate (ribs), a timber post, and the painted
materials, each repainted by a TagRamp of the style (style.py): trim (silver-white edges, rims and
rivet bands), cloth (the player's colour), ember
(glowing coals and furnace throats), mark (the White Hand's white), chain (dark oiled iron),
soot, water (the dammed Isen in the sluices) and flame (flame tongues, painted near-white
orange so they read as fire by day). The rects were read by eye on the flat sheet; confirm them on the citadel's first bake."""
from sagekit.atlas import Atlas, Region

PANEL = (15, 620, 120, 1000)               # the long smooth panel (left column)
PLATE = (615, 625, 705, 690)               # a plain beaten plate


class IsengardAtlas(Atlas):
    texture = 'IBFortress.tga'
    normal = 'IBFortress_NRM.tga'
    size = 1024
    density = 6.0                          # 1024 px over the same building sizes as the 512 sheets' 3.0
    ground_sat = (.6, .8)                  # no enamel band ground: the teal-grey is the plates themselves
    regions = {                                                   # order matters: face tags index it
        'stoneA': Region(PANEL),
        'stoneB': Region((935, 520, 1010, 1020)),                  # the right-hand panel
        'rock': Region((150, 20, 440, 220)),                       # rough rock and earth
        'iron': Region(PLATE),
        'ribs': Region((820, 90, 1020, 440)),                      # fluted wall plates
        'timber': Region((745, 130, 770, 380), Region.STRETCH),    # one post
        'cloth': Region(PLATE),
        'ember': Region(PLATE),
        'mark': Region(PLATE),
        'chain': Region(PLATE),
        'soot': Region((150, 20, 440, 220)),
        'trim': Region(PLATE),
        'water': Region(PLATE),
        'flame': Region(PLATE),
    }
    painted = ('cloth', 'ember', 'mark', 'chain', 'soot', 'trim', 'water', 'flame')
    materials = {
        'stone': [PANEL, (935, 520, 1010, 1020)],
        'rock': [(0, 0, 445, 232), (140, 230, 380, 395), (85, 236, 250, 400), (170, 390, 230, 512),
                 (445, 0, 535, 195), (250, 0, 385, 65), (400, 255, 475, 370), (597, 390, 662, 500),
                 (512, 512, 587, 632), (327, 932, 400, 1024)],
        'wood': [(602, 0, 930, 70), (712, 65, 905, 390), (215, 862, 400, 927)],
        'mark': [(72, 197, 135, 282)],
    }
    mask_hints = {
        'stone': [(0, 0, 4 * 1024, 4 * 1024)],
    }


# ------------------------------------------------------------------ the buildings' own sheets
# Nine buildings paint EA's faces from sheets of their own, not IBFortress: each gets its material
# rects here, in that sheet's own pixels (x right, y down; 256 or 512). Read by eye on the flat
# sheets (build/assets/isengard/<b>/src/*.png); confirm against the first bakes. Materials, in
# priority order (the first rect a texel falls in wins; IsengardSheetRecolour, paint.py):
#     iron   plates and bars, whatever their colour (rust never glows)
#     mark   the White Hand banners and bone: pale texels white, the rest Orthanc stone
#     stone  smooth dark panels (Orthanc stone)
#     rock   rough rock, earth, flagstones
#     wood   planks, posts, bark, cut ends, and hide and fur (the palette's hide is its wood)
# Fire is found by colour only outside every rect (the furnace's molten metal); the rest is iron,
# silver-white where it is brightest, as on IBFortress. The damaged and snow states share the layout.
# An optional third item overrides IsengardRecolour's tones {material: (gain, lift)} for that sheet.
SHEETS = {
    "ibarmory.tga": (256, {
        "wood": [(0, 0, 15, 150), (15, 0, 50, 54), (65, 0, 97, 110), (97, 0, 172, 80), (172, 0, 256, 95),
                 (216, 95, 256, 125), (36, 120, 66, 256), (70, 236, 122, 256)],
        "rock": [(140, 125, 256, 256)],                 # the cracked flagstones
    }),
    "ibbtltwr.tga": (256, {                             # battle tower (the add-ons group's design)
        "wood": [(0, 0, 150, 68), (0, 68, 85, 256), (85, 72, 140, 256), (150, 0, 256, 125)],   # fur, planks, lashed poles
        "rock": [(140, 125, 256, 256)],
    }),
    "mbfurnace.tga": (256, {                            # the molten sheet (92..181, 32..128) glows by colour
        "wood": [(199, 0, 256, 107)],                   # the timber poles
        "rock": [(0, 0, 92, 128), (92, 0, 155, 32), (0, 128, 181, 256)],
    }),
    "mblumbermill.tga": (256, {
        "iron": [(92, 0, 155, 72), (180, 225, 256, 256)],   # the rusted plate (no glow), the saw blade
        "wood": [(155, 0, 256, 225), (0, 128, 97, 185), (97, 128, 180, 256)],   # bark, planks, chips, cut ends
        "rock": [(0, 0, 92, 128), (97, 72, 155, 128), (0, 185, 97, 256)],
    }),
    "ibseigework.tga": (256, {
        "iron": [(36, 55, 58, 76)],                     # the gear on the gable
        "mark": [(117, 27, 218, 120)],                  # the White Hand banner
        "wood": [(0, 0, 220, 27), (218, 0, 256, 256), (0, 27, 117, 120)],
        "rock": [(0, 120, 240, 256)],                   # trodden earth
    }),
    "ibwildbuilding.tga": (512, {                       # tavern: logs, bark, a cut end, a pelt
        "rock": [(336, 122, 512, 250)],                 # the pelt (the V1 hide walls): dark weathered hide, not tan
        "wood": [(0, 0, 512, 512)],
    }, {"rock": (0.4, 0.0)}),                           # the only rock here: the pelt at about 0.4 of its EA brightness
    "iburukpit.tga": (512, {
        "mark": [(384, 112, 456, 242)],                 # the White Hand banner
        "wood": [(288, 0, 512, 25), (372, 22, 456, 112), (456, 22, 512, 290), (0, 220, 45, 512)],
        "rock": [(0, 0, 512, 512)],                     # the mound and its pits
    }),
    "ibwargpit.tga": (256, {                            # also the warg pit's door (warg_pit_02)
        "mark": [(90, 72, 147, 138)],                   # the bones and the skull
        "wood": [(0, 0, 90, 256), (90, 0, 128, 72), (90, 138, 140, 256)],
        "rock": [(128, 0, 256, 93)],                    # the earth; the carved lattice stays iron
    }),
    "ibwargsent.tga": (256, {                           # warg sentry (the add-ons group's design)
        "mark": [(0, 0, 256, 52), (95, 52, 240, 230)],  # the curved tusks round the ring (horn grain), the bones
        "wood": [(0, 52, 90, 185)],                     # the fur
        "rock": [(0, 0, 256, 256)],
    }, {"wood": (0.75, 0.08)}),
}


def sheet_atlas(name):
    """The Atlas of one of the buildings' own sheets (materials in its own pixels, `own_sheet`
    set), or None for a sheet without a table (IBFortress and the rest keep their own paths)."""
    key = name.lower().replace(".dds", ".tga")
    for state in ("_d", "_d1", "_d2", "_snow"):
        if key not in SHEETS and key.endswith(state + ".tga"):
            key = key[:-len(state + ".tga")] + ".tga"
    entry = SHEETS.get(key)
    if entry is None:
        return None
    size, materials, tones = (entry + (None,))[:3]
    a = Atlas()
    a.texture, a.size, a.materials, a.tones, a.own_sheet = name, size, materials, tones, True
    a.ground_sat = IsengardAtlas.ground_sat
    return a
