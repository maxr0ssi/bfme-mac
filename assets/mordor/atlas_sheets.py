"""Mordor's production sheets: where the materials are on each building's own sheet.

MBFortress (atlas.py) paints the citadel and its add-ons; every other Mordor building paints EA's
faces from a sheet of its own. Each gets its material rects here, in that sheet's own pixels (x
right, y down; the size is the healthy sheet's), read by eye on the flat sheets and checked on
recolour renders of EA's own buildings (build/assets/mordor/_review/sheets_v2.jpg). Each table
lists its materials in priority order: the first one whose rect a texel falls in wins (slits lie
over the rest; MordorSheetRecolour, paint.py). The materials:

    slit    the dark insides of windows, doors and slots: lit through the palette's "slit" ramp
            (F2: a dim ember, no green), darkest texel brightest; lighter texels fall through
    glow    lit windows, lamps, glowing bars: fire by colour (yellow to red, bright), the rest iron
    lava    ground bibs' lava cracks, the lumber mill's ember pit: fire by colour, the rest rock
    blade   sharpened metal and chains: steel on the bright texels, iron and trim below
    bone    tusks, skulls and bones: ivory, the buildings' highlights
    flesh   raw meat: dark blood red, never fire
    hide    leather, pelts and fur: warm leather, pale fur stays pale
    accent  the Harad trims' painted bands: red texels war-paint, yellow ones gold, the rest cloth
    brass   a painted inscription band (the pen): gold and brass
    cloth   canvas and sails: deep red (Mordor), sand and ochre (Harad)
    wood    planks, poles, bark, reed mats and lashings: scorched warm brown
    trim    metal that is all edge
    iron    plates, bars, locks and rusted scrap (rust never glows): F2's black iron
    mud     the orc pit's spawning pool: sickly green sludge (Max kept EA's green), the focal point
    rock    ground, earth, gravel, boulders: F2's ash (sand on the Harad sheets)
    stone   dressed stone, slabs and roof slates: F2's basalt

Texels outside every rect are metal (iron, trim on the bright ones) with fire only where strongly
saturated and bright, as on MBFortress. Fire elsewhere comes only from glow and lava rects, so
EA's rust and meat never burn.

F2 on the production sheets (Max, 2026-09-30, on sheets_v1: "some of these feel like a step
back"): F2's black is for stone and iron only. Timber stays scorched brown, bone ivory, cloth
deep red, ground ash. Each material keeps EA's values: its ramp's colour at x has luminance k*x
(`_valued`), read at EA's own luminance, so EA's lights stay light and its darks dark, k a little
under 1 (darker, not duller). Orange ember where EA has fire, lit windows or metal glow; no green
anywhere (Max: "we don't need much green on the other buildings"). The Harad sheets (MBHrdPlc,
MBMumkPen, their bibs) are allies from the south, not Barad-dur: sand and ochre canvas and ground,
gold and brass, war-paint red, ivory, warmer than Mordor and only a little darker than EA.

An entry is (size, {material: rects}) or (size, {material: rects}, extra) where extra holds
"tones" {material: (gain, lift)} over TONES and "ramps" {material: stops} over SHEET_RAMPS.
State sheets (_d, _d1, _snow, _s, EA's 1d/2d) share their healthy sheet's layout (sheet_atlas).
The tavern's sheets have DDS copies (no TGA-only sheet in Mordor's folder, checked 2026-09-30);
MBTavern, MBTavernWD and MBLumberMill are drawn by Isengard (and the Goblins) too, so `sagekit
sheets` leaves them and their tables serve the recipes' own copies (MBTaverH, MBLumberMilB).
"""
from sagekit.atlas import Atlas


def _valued(k, stops):
    """A ramp whose colour at x has luminance k*x: stops [(x, hue as (r, g, b) proportions)] scaled
    to that luminance (clipped at white)."""
    out = []
    for x, (r, g, b) in stops:
        f = k * max(x, 0.012) / (0.3 * r + 0.59 * g + 0.11 * b)
        out.append((x, tuple(round(min(1.0, c * f), 3) for c in (r, g, b))))
    return out


# (gain, lift) from EA's luminance to each ramp's position: 1:1 where the ramp keeps EA's values
# (_valued); F2's own ramps (stone, iron, rock) are darker than their position, so a gain spreads them
TONES = {"stone": (1.9, 0.0), "rock": (1.35, 0.0), "iron": (2.0, 0.0), "trim": (2.2, -0.7),
         "steel": (1.3, -0.17), "fire": (1.8, 0.2), "slit": (-2.4, 1.0), "mud": (1.4, 0.0),
         "wood": (1.0, 0.0), "hide": (1.0, 0.0), "cloth": (1.0, 0.02), "bone": (1.0, 0.03),
         "flesh": (1.0, 0.04), "paint": (1.0, 0.04), "brass": (1.0, 0.02)}
RAMP_OF = {}                                            # material -> palette ramp, where the names differ
SHEET_RAMPS = {
    "wood": _valued(0.88, [(0, (1, .7, .5)), (.15, (1, .68, .46)), (.35, (1, .64, .38)), (.6, (1, .7, .46)),
                          (1, (1, .84, .66))]),         # scorched brown: char in the grain, weathered tan lit
    "hide": _valued(0.85, [(0, (1, .72, .5)), (.3, (1, .7, .46)), (.6, (1, .8, .6)), (1, (1, .95, .86))]),
    "bone": _valued(0.95, [(0, (1, .8, .55)), (.4, (1, .84, .6)), (1, (1, .93, .78))]),      # warm ivory
    "cloth": _valued(0.8, [(0, (1, .2, .14)), (.4, (1, .16, .1)), (.8, (1, .22, .14)), (1, (1, .4, .3))]),
    "flesh": _valued(0.5, [(0, (1, .2, .14)), (.5, (1, .14, .09)), (1, (1, .26, .18))]),
    # the orc pit's pool (EA's green goo; Max: "i like it for sludge"): crusted black-green in the swirl's
    # grooves, sickly Morgul green on its crests (the citadel's witch-light hue, style.MORGUL_WINDOW)
    "mud": [(0, (.015, .03, .01)), (.3, (.07, .17, .04)), (.55, (.22, .47, .12)), (.8, (.46, .80, .26)),
            (1, (.72, .98, .50))],
}
# the Harad pair's own: sand and ochre, gold and brass, war-paint red, sand ground
HARAD = {"ramps": {
    "cloth": _valued(0.78, [(0, (1, .66, .4)), (.4, (1, .64, .36)), (.8, (1, .7, .42)), (1, (1, .84, .6))]),
    "paint": _valued(0.85, [(0, (1, .14, .08)), (.5, (1, .12, .07)), (1, (1, .3, .18))]),
    "brass": _valued(0.92, [(0, (1, .64, .26)), (.5, (1, .68, .26)), (1, (1, .84, .5))]),
    "rock": _valued(0.8, [(0, (1, .86, .66)), (.5, (1, .86, .66)), (1, (1, .92, .78))]),
}, "tones": {"rock": (1.0, 0.0)}}

_BIB = {"lava": [(0, 0, 256, 256)]}                     # ground bibs: earth, lava cracks on the level-ups by colour
_PEN = {                                                # the mumakil pen
    "accent": [(96, 64, 256, 98)],                      # the red pennants with gold edges
    "brass": [(96, 162, 256, 204)],                     # the painted inscription band
    "rock": [(96, 0, 131, 22)],                         # the pebbles
    "bone": [(0, 0, 37, 256)],                          # the tusks
    "wood": [(37, 0, 96, 256)],                         # the dark lattice
    "cloth": [(96, 0, 256, 256)],                       # the canvas
}
_PENV = dict(_PEN, rock=[(96, 0, 131, 22), (0, 224, 96, 256)], bone=[(0, 0, 37, 224)])     # V1, V2: a ground patch
SHEETS = {
    "mbhrdplc.tga": (256, {                             # the Haradrim palace
        "bone": [(40, 220, 162, 256)],                  # the great tusks
        "accent": [(0, 0, 46, 24), (165, 98, 192, 186), (192, 172, 256, 190)],   # the painted borders
        "wood": [(52, 0, 77, 64), (80, 0, 250, 90),     # the lattice panels and their lashings
                 (6, 182, 162, 222), (164, 188, 256, 256), (0, 222, 44, 256)],   # reed mat, frame, rope
        "cloth": [(0, 0, 256, 256)],                    # the tent canvas
    }, HARAD),
    "mbmumkpen.tga": (256, _PEN, HARAD),
    "mbmumkpen_v1.tga": (256, _PENV, HARAD),
    "mbmumkpen_v2.tga": (256, _PENV, HARAD),
    "mbbstone.tga": (512, {"rock": [(0, 0, 512, 512)]}),          # the orc pit's rock
    "mborcpit01.tga": (256, {
        "mud": [(155, 0, 256, 96)],                     # the pool
        "wood": [(0, 78, 155, 96)],                     # the beam
        "rock": [(0, 0, 256, 256)],                     # earth, gravel, the posts' ends
    }),
    "mborcpit01a.tga": (512, {"rock": [(0, 0, 512, 512)]}),       # the pit's walls and steps
    "mborcpit_mud.tga": (128, {"mud": [(0, 0, 128, 128)]}),
    "mborcpit_mud_v3.tga": (128, {"mud": [(0, 0, 128, 128)]}),    # EA's green slime: the same green sludge
    "mbseigework1.tga": (256, {
        "slit": [(196, 88, 236, 150)],                  # the barred hatch: ember behind,
        "glow": [(196, 88, 236, 150)],                  # its bars hot
        "iron": [(4, 4, 36, 32)],                       # the iron box
        "wood": [(0, 0, 256, 38), (155, 38, 256, 160), (235, 38, 256, 256)],
        "stone": [(0, 38, 155, 256)],                   # the rubble wall
        "rock": [(155, 160, 235, 256)],
    }),
    "mbseigework2.tga": (256, {
        "wood": [(0, 0, 256, 120)],
        "rock": [(0, 120, 256, 256)],                   # earth and the scorched pit
    }),
    "mbsltrhs.tga": (256, {                             # the slaughter house
        "flesh": [(155, 205, 256, 256)],                # the carcass
        "wood": [(0, 0, 165, 30), (65, 30, 165, 133)],  # the plank, the logs
        "stone": [(0, 30, 65, 120)],                    # the roof slates
        "hide": [(165, 0, 256, 205), (0, 135, 165, 256)],   # the roof's stitched leather; the pale pelt
        "rock": [(0, 120, 65, 135)],
    }),
    "mbsltrhsbib.tga": (256, {"rock": [(0, 0, 256, 256)]}),
    "mbtavern.tga": (512, {                             # the tavern (MAINHOUSE: our copy MBTaverH)
        "glow": [(392, 196, 446, 500), (470, 110, 500, 480)],     # the lit windows and the round lamps
        "slit": [(56, 102, 101, 157)],                  # the dark window
        "stone": [(0, 0, 496, 82), (159, 82, 345, 148), (366, 150, 456, 512),   # the cobbled walls
                  (47, 132, 272, 270)],                 # the slate gable
        "iron": [(496, 0, 512, 82)],
        "wood": [(0, 82, 512, 512)],                    # boards, panels, the plank floor
    }),
    "mbtavernwd.tga": (512, {                           # the tavern's props (Isengard draws it too)
        "glow": [(386, 32, 444, 112)],
        "hide": [(100, 110, 385, 270), (330, 255, 440, 370), (100, 270, 245, 512)],   # the hides and the shield
        "wood": [(0, 0, 512, 512)],
    }),
    "mbtrollpit.tga": (256, {                           # the troll cage
        "blade": [(215, 15, 240, 120)],                 # the chains, shackle and lock: steel
        "rock": [(0, 115, 152, 256)],                   # the pit's floor
        "wood": [(0, 0, 256, 256)],
    }),
    "mblumbermill.tga": (256, {                         # our copy MBLumberMilB (Isengard and the Goblins draw it)
        "blade": [(180, 225, 256, 256)],                # the saw
        "lava": [(0, 128, 97, 185)],                    # the red chips in the stone ring: an ember pit
        "iron": [(92, 0, 155, 72)],                     # the rusted plate
        "wood": [(155, 0, 256, 225), (97, 128, 180, 256)],
        "rock": [(0, 0, 92, 128), (97, 72, 155, 128), (0, 185, 97, 256)],
    }),
    "mbbarcade.tga": (512, {                            # the barricade: carved grey stone
        "slit": [(382, 0, 512, 255), (0, 222, 60, 312)],    # the dark arches: a dim ember
        "stone": [(0, 0, 512, 512)],
    }),
    "dolgolgate.tga": (512, {                           # the battle tower (our copy DolGolGatH)
        "slit": [(408, 22, 446, 54)],
        "trim": [(75, 0, 125, 512)],                    # the zig-zag strip
        "iron": [(0, 0, 512, 512)],
    }, {"tones": {"iron": (2.3, 0.0)}}),                # EA's rust is dark: spread F2's iron over it
}
for _b in ("mbmumkpen_bib", "mbmumkpen_bibv1", "mbhrdplcbib", "mbhrdplcbib_v1"):
    SHEETS[_b + ".tga"] = (256, _BIB, HARAD)            # the Harad pair's ground: sand
for _b in ("mborcpitbib", "mborcpitbibv1", "mborcpit_biblava", "mbseigework_bib", "mbseigework_bibv1", "mbsltrhs_bib",
           "mbsltrhs_bibv1", "mbtavern_bib", "mbtrollpit_bib", "mbtrollpit_bibv1", "mbbarcade_bib", "mblumbermill_bib",
           "mblumbermill_bibv1", "mbsentry_bib"):
    SHEETS[_b + ".tga"] = (256, _BIB)
# EA's state sheets named off the pattern
ALIASES = {"mbseigework1d.tga": "mbseigework1.tga", "mbseigework2d.tga": "mbseigework2.tga",
           "mborcpit_d.tga": "mborcpit01.tga"}
STATES = ("_d", "_d1", "_d2", "_snow", "_s")


def key(name):
    """The table a sheet reads: its own, or its healthy sheet's for a state sheet, or None."""
    k = name.lower().replace("\\", "/").split("/")[-1].replace(".dds", ".tga")
    k = ALIASES.get(k, k)
    while k not in SHEETS:
        state = next((s for s in STATES if k.endswith(s + ".tga")), None)
        if state is None:
            return None
        k = ALIASES.get(k[:-len(state + ".tga")] + ".tga", k[:-len(state + ".tga")] + ".tga")
    return k


def sheet_atlas(name, ground_sat=(.6, .8)):
    """The Atlas of one of the production sheets (materials in its own pixels, `own_sheet` set), or
    None for a sheet without a table (MBFortress and the rest keep MordorRecolour's paths)."""
    k = key(name)
    if k is None:
        return None
    size, materials, extra = (SHEETS[k] + ({},))[:3]
    a = Atlas()
    a.texture, a.size, a.materials, a.own_sheet = name, size, materials, True
    a.tones = dict(TONES, **extra.get("tones", {}))
    a.ramps = dict(SHEET_RAMPS, **extra.get("ramps", {}))
    a.ground_sat = ground_sat
    return a
