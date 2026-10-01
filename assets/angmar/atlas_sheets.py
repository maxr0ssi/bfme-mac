"""Angmar's other sheets: where the materials are on each one.

KBFortress (atlas.py) paints the citadel; the other two master sheets paint the rest of the
fortress family, each with its own table here, in that sheet's own pixels (x right, y down; the
size is the healthy sheet's), read by eye on the flat sheets (2026-10-01):

    KBFortressB   the walls (hub, segment, gate, postern, tower, trebuchet, the cliff cap), the
                  wall-hub and battle-tower expansions, the catapult, the sanctum
    KBFortressX   the House of Lamentation, the fortress spikes, the kennel

Each table lists its materials in priority order: the first one whose rect a texel falls in wins;
slits lie over the rest (AngmarRecolour, paint.py). The materials are the citadel's (atlas.py):

    slit    the dark insides of arrow slits and barred windows: lit through the palette's "slit"
            ramp, darkest texel brightest; lighter texels (the frames) fall through
    iron    plates, panels, studded bands, brackets: rust on them found by colour
    planks  warm boards and beams: wood stays wood in every palette
    roof    the scale shingles
    timber  the dark frost-grained wood: its frost lines are the ramp's rime
    rock    the mossy ground patch
    stone   blocks, rubble, slabs and stairs: everything else

    earth   ground, gravel and straw (the bibs, the den's mound, the temple's gravel): a cold dark
            earth of its own, EA's straw and grass kept faintly (chroma)
    bone    the horns (barracks, den, mill, forge): pale ivory at EA's values
    glow    the forge's coals: fire by colour (the palette's cold fire), the rest falls through
    ice     the Ice Walls crust (_ice sheets): pale texels in these rects take a pale blue-white ice

KBHall (barracks), KBDen, KBTemple (Hall of Twilight), KBBtlTwr (sentry tower), KBForge and KBMill
(no recipe yet: skinned bodies) and every bib have tables here too. Every table paints with the
production extras (PRODUCTION): EA's rust keeps its warmth (a warm rust ramp and part of EA's own
rust colour, where the citadel's A2 freezes it) and the earth ramp. KBFortress and its own states
(_d1, _snow, _ice) stay on the faction atlas (atlas.py): the citadel's paint is unchanged.

State sheets (_d, _d1, _snow) share their healthy sheet's layout (key), checked on the flat sheets
(2026-10-01) except: KBFortressX_D1 is KBFortressB's damaged sheet (B's layout; the walls' damaged
models draw it), KBBtlTwr_D1 and KBWalls_D1 are other layouts no model draws (stone). The _snow and
_ice sheets are `frost` tables: their pale, unsaturated texels (snow, ice) take the tables' pale ice
ramp, so snow stays white on planks and roof; the _ice sheets also map their crust (ice rects).
Checked on recolour renders of EA's own buildings (build/assets/angmar/_review/sheets_v1.jpg)."""
from sagekit.atlas import Atlas

from .style import RIME


def _curve(k, gamma, hues):
    """A ramp whose colour at x has luminance k * x**gamma: hues [(x, (r, g, b) proportions)]."""
    out = []
    for x, (r, g, b) in hues:
        f = k * max(x, 0.012) ** gamma / (0.3 * r + 0.59 * g + 0.11 * b)
        out.append((x, tuple(round(min(1.0, c * f), 3) for c in (r, g, b))))
    return out


# every table's extras (sheet_atlas): EA's rust stays warm rust (darker than EA's, part of its own colour
# kept); ice and snow a pale blue-white at EA's values (the palette's ice is too cyan on a whole crust); the
# ground a cold dark earth that keeps some of EA's straw and grass and goes frost-white under EA's snow; the
# horns pale bone; stone and shingles a touch lighter than the citadel's (its gamma crushed the darker
# production sheets: barracks p50 0.21 -> 0.11 on sheets_v1), the shingles keeping some of EA's moss.
# Earth never rusts (EA's straw is orange)
PRODUCTION = {
    "ramps": {
        "rust": _curve(0.72, 1.0, [(0, (1.0, .56, .36)), (.5, (1.0, .60, .42)), (1, (1.0, .72, .56))]),
        "ice": _curve(1.0, 1.05, [(0, (.70, .80, 1.0)), (.5, (.84, .91, 1.0)), (1, RIME)]),
        "bone": _curve(0.95, 1.1, [(0, (1.0, .93, .84)), (.5, (1.0, .95, .88)), (1, (.97, .97, 1.0))]),
        "earth": _curve(0.92, 1.05, [(0, (1.0, .92, .84)), (.35, (1.0, .95, .90)), (.6, (.96, .97, 1.0)),
                                     (.85, (.92, .96, 1.0)), (1, RIME)]),
    },
    "tones": {"rust": (1.15, 0.0), "stone": (1.12, 0.0), "roof": (1.15, 0.0), "bone": (1.0, 0.0)},
    "chroma": {"rust": 0.3, "earth": 0.6, "roof": 0.35, "bone": 0.3},
}
_SLITS = [(48, 652, 88, 748), (176, 652, 212, 748), (302, 652, 338, 748),            # the small slits
          (388, 666, 437, 788), (468, 666, 514, 788), (543, 666, 592, 788), (623, 666, 670, 788),
          (703, 666, 752, 788), (806, 768, 832, 842),                                 # the tall ones
          (512, 490, 672, 582)]                                                       # the barred windows
_TIMBER = [(512, 0, 822, 135), (512, 345, 822, 450), (855, 570, 1024, 1024)]
_ROCK = [(512, 245, 612, 345)]
_B = {
    "slit": _SLITS,
    "iron": [(0, 320, 385, 528),                        # the riveted plate panels
             (345, 165, 512, 600),                      # the carved spire and its pieces
             (822, 515, 1024, 570)],                    # small bits and brackets
    "planks": [(345, 0, 410, 165), (822, 135, 1024, 515)],
    "roof": [(410, 0, 512, 135), (822, 0, 1024, 135)],
    "timber": _TIMBER,
    "rock": _ROCK,
    "stone": [(0, 0, 1024, 1024)],
}
_X = {
    "slit": _SLITS,
    "iron": [(390, 566, 512, 597), (410, 626, 855, 658), (410, 770, 855, 800),       # the studded bands
             (705, 452, 822, 532),                      # the stair's studded edges
             (822, 515, 1024, 570)],
    "planks": [(60, 362, 512, 534),                     # the ochre beam
               (822, 148, 1024, 515)],
    "roof": [(822, 0, 1024, 148)],
    "timber": _TIMBER,
    "rock": _ROCK,
    "stone": [(0, 0, 1024, 1024)],                      # blocks, the rune-diamond rubble, slabs
}
# the Ice Walls crust: the wall's feet, the waterfall down the pole, the slab of ice over the dark board
_ICE = [(0, 750, 860, 1024), (855, 570, 1024, 1024), (512, 345, 705, 452)]
_STONE = {"stone": [(0, 0, 512, 512)]}
_BIB = {"earth": [(0, 0, 512, 512)]}                    # ground: earth, straw, gravel, the den's bones
SHEETS = {
    "kbfortressb.tga": (1024, _B),
    "kbfortressb_ice.tga": (1024, dict(_B, ice=_ICE + [(0, 80, 348, 330)]), {"frost": True}),
    "kbfortressx.tga": (1024, _X),
    "kbfortressx_ice.tga": (1024, dict(_X, ice=_ICE + [(512, 0, 680, 136)]), {"frost": True}),
    "kbhall.tga": (512, {                               # the barracks
        "slit": [(370, 5, 410, 35), (450, 5, 490, 35), (328, 72, 348, 112)],          # the shutters' holes
        "iron": [(135, 52, 165, 220)],                  # the spiked iron strip
        "planks": [(0, 6, 104, 42), (205, 0, 345, 52), (355, 0, 415, 50), (440, 0, 500, 50),   # boards, shutters
                   (285, 50, 357, 128), (165, 220, 285, 253),                          # the door, the eaves
                   (60, 160, 75, 335), (92, 195, 108, 255), (5, 243, 60, 253),                         # beams
                   (314, 340, 374, 357), (367, 343, 390, 368), (380, 355, 405, 385), (396, 375, 415, 412)],
        "roof": [(165, 50, 285, 220)],                  # the square shingles
        "bone": [(0, 335, 110, 512), (448, 52, 512, 272)],                           # the horns
        "stone": [(0, 0, 512, 512)],                    # blocks, pillars, the sooted arch
    }),
    "kbden.tga": (512, {                                # the wolf den
        "slit": [(187, 232, 206, 313)],                 # the door's slot
        "planks": [(52, 0, 143, 333), (0, 215, 52, 333), (160, 222, 236, 318)],       # the logs, the door
        "roof": [(145, 65, 215, 208)],                  # the green slates
        "bone": [(0, 0, 52, 215)],                      # the horns
        "timber": [(143, 207, 250, 333)],               # the door frame
        "earth": [(143, 0, 512, 65), (215, 65, 512, 333), (375, 333, 512, 512)],     # the mound and its boulders
        "stone": [(0, 0, 512, 512)],
    }),
    "kbtemple.tga": (512, {                             # the Hall of Twilight
        "planks": [(302, 282, 410, 345)],               # the bowl
        "timber": [(385, 200, 512, 512)],               # the cracked pillars
        "earth": [(242, 0, 512, 155), (242, 155, 442, 200)],                        # the gravel
        "stone": [(0, 0, 512, 512)],                    # blocks, cobbles, the rune shield
    }),
    "kbbtltwr.tga": (512, {                             # the sentry tower
        "slit": [(0, 55, 6, 115), (35, 55, 48, 115), (80, 55, 93, 115), (124, 55, 136, 115), (166, 55, 179, 115),
                 (209, 55, 221, 115), (252, 55, 262, 115), (35, 210, 48, 250), (124, 210, 136, 250),
                 (209, 210, 221, 250)],
        "iron": [(0, 160, 262, 180), (0, 275, 262, 295), (80, 115, 95, 450), (164, 115, 180, 450)],   # the bars
        "planks": [(410, 360, 512, 512)],
        "timber": [(262, 0, 512, 215), (385, 215, 512, 360)],                        # frost-grained boards
        "stone": [(0, 0, 512, 512)],
    }),
    "kbforge.tga": (512, {                              # the forge works
        "glow": [(122, 0, 320, 82)],                    # the coals: cold fire, the citadel's torches' blue
        "iron": [(122, 0, 320, 82), (0, 215, 120, 330), (320, 0, 362, 312), (320, 312, 512, 332),
                 (120, 80, 320, 330)],                  # the pale riveted plates: lit metal
        "planks": [(55, 0, 120, 165), (362, 0, 512, 245), (0, 332, 142, 512)],
        "bone": [(0, 0, 55, 215)],                      # the horns
        "stone": [(0, 0, 512, 512)],
    }),
    "kbmill.tga": (512, {                               # the mill
        "slit": [(367, 55, 405, 98), (162, 277, 208, 328)],                         # the barred window, the panes
        "iron": [(145, 225, 255, 250), (280, 195, 415, 330), (415, 170, 512, 332)],  # rings, grate, bars
        "planks": [(270, 0, 512, 175), (155, 268, 215, 332), (215, 258, 285, 332)],
        "roof": [(0, 215, 140, 332)],
        "bone": [(0, 0, 55, 215)],                      # the horns
        "stone": [(0, 0, 512, 512)],                    # the millstone, the blocks
    }),
    "kbwalls.tga": (512, {"planks": [(0, 0, 145, 190)], "timber": [(145, 95, 512, 190)], "stone": [(0, 0, 512, 512)]}),
    "kbwallscon_2.tga": (256, {"planks": [(0, 0, 256, 62)], "timber": [(180, 100, 256, 256)],
                               "stone": [(0, 0, 256, 256)]}),         # Carn Dum's map scaffolding (civilian)
    "kbstonea.tga": (512, _STONE),
    "kbangwallgate.tga": (1024, {"stone": [(0, 0, 1024, 1024)]}),
    "kbbtltwr_d1.tga": (512, _STONE),                   # another layout, drawn by no model
    "kbwalls_d1.tga": (512, _STONE),
}
for _b in ("kbangwallgate_bib", "kbangwallgate_bibd1", "kbarwtow_bib", "kbarwtow_bibd", "kbbtltwr_bib",
           "kbbtltwr_bibd", "kbden_bib", "kbden_bibd", "kbforge_bib", "kbforge_bibd", "kbfortress_bib",
           "kbfortress_bibd", "kbhall_bib", "kbhall_bibd", "kbhtow_bib", "kbhtow_bibd", "kbkennel_bib",
           "kbkennel_bibd", "kbkennel_bibd1", "kbmill_bib", "kbposterngate_bib", "kbposterngate_bibd1",
           "kbsanct_bib", "kbsanct_bibd", "kbtemple_bib", "kbtemple_bibd", "kbtroltow_bib", "kbtroslitow_bip",
           "kbwall_bib", "kbwall_bibd", "kbwallhub_bib", "kbwallhubn_bibd1", "kbwalln_bib", "kbwalln_bibd",
           "kbwalln_bibd1", "kbwalltwrn_bib", "kbwalltwrn_bibd"):
    SHEETS[_b + ".tga"] = (512, _BIB)                   # rects in 512 px: a 256 bib reads the same (all earth)
# EA's sheets named off the pattern: KBFortressX_D1 is KBFortressB's damaged sheet (B's layout)
ALIASES = {"kbfortressx_d1.tga": "kbfortressb.tga", "kbkennel_bib_snw.tga": "kbkennel_bib_snow.tga",
           "kbwallhubn_bib_snow.tga": "kbwallhub_bib_snow.tga",
           "kbangwallgated1.tga": "kbangwallgate.tga"}
STATES = ("_d1", "_d", "_snow")
FROST = ("_snow", "_ice")                               # their pale texels: the tables' pale ice


def key(name):
    """The table a sheet reads: its own, or its healthy sheet's for a state sheet, or None (KBFortress
    and its own states: the faction atlas)."""
    k = name.lower().replace("\\", "/").split("/")[-1].replace(".dds", ".tga").replace(".png", ".tga")
    k = ALIASES.get(k, k)
    while k not in SHEETS:
        state = next((s for s in STATES if k.endswith(s + ".tga")), None)
        if state is None:
            return None
        k = ALIASES.get(k[:-len(state + ".tga")] + ".tga", k[:-len(state + ".tga")] + ".tga")
    return k


def sheet_atlas(name, ground_sat=(.6, .8)):
    """The Atlas of one of the tabled sheets (materials in its own pixels, `own_sheet` set, the
    production extras and `frost` on a snow or ice sheet), or None (KBFortress and its states: the
    faction atlas)."""
    k = key(name)
    if k is None:
        return None
    size, materials, extra = (SHEETS[k] + ({},))[:3]
    a = Atlas()
    a.texture, a.size, a.materials, a.own_sheet = name, size, materials, True
    a.ramps, a.tones, a.chroma = PRODUCTION["ramps"], PRODUCTION["tones"], PRODUCTION["chroma"]
    stem = name.lower().replace("\\", "/").split("/")[-1].rsplit(".", 1)[0]
    a.frost = extra.get("frost", False) or stem.endswith(FROST) or stem.endswith("_snw")
    a.ground_sat = ground_sat
    return a
