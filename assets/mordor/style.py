"""Mordor: Barad-dur's black land. Volcanic and cruel: black basalt, lava in the cracks, heavy
blades and spikes, hard steel on the blades only. Never Isengard's machined black stone with
silver on every edge, never the Goblins' crimson horn, tarnished silver and bone.

The palette is F2 "Fire, shadow and steel" (Max's pick, 2026-09-30: "F2 is super cool!"). He
first took F for its contrast and asked for "a touch of like hard silver which the og has a little
of": F2 is F plus a "steel" ramp on the blades only (atlas "blade" rects: where EA's sheet has its
pale steel), never on every edge as Isengard's silver is, and its window green a third of the way
from F's lime toward F3's ghost-green.

Pass 7 of the citadel (Max, 2026-09-30: "we should drastically reduce the green"): F2's windows
("slit": every window and slot of EA's sheet and the kit's lancets) are unlit now, a dim ember deep
in them (EMBER_WINDOW); the Morgul green (MORGUL_WINDOW) stays only on the few slits a recipe tags
"witch" (the "witch" ramp, painted by the style's TagRamp) and in the crowns' green witch-fire (the
game's particles, sagekit/fire_systems.py). The other options stay in PALETTES for the record; the
boards are build/assets/mordor/_palettes/ (`sagekit palettes mordor --only F2`): palette_options.jpg
(EA and F2), round one (A to D) in palette_options_v1.jpg, round two (E, F, G, A) in
palette_options_v2.jpg, round three (F, F2, F3, F4) in palette_options_v3.jpg.

Each is a recolour of EA's own sheet through its material ramps (assets/mordor/paint.py): stone
(the smooth slabs), rock (crags and ground), iron (plate, blades, spikes), trim (the lit metal
edges), fire (the lava vein and the pyres), from E on slit (the windows and slots, lit) and, from
F2 on, steel (the blades' bright faces).

The green is Minas Morgul's, not Barad-dur's. EA's green is the Morgul sorcery upgrade's
witch-light (MorgulSorceryFX, a pale jade on MBFSorcery) and the Witch-king's poison and blade
(WitchKingPoison, MorgulBladeHit: yellow-green); MBFortress has no green. Ours is a sickly
yellow-green, never the Elves' teal.

Cloth follows the player's colour (house_template, as for every faction); the "cloth" ramp colours
only the previews of new cloth faces."""
from sagekit.style import Palette, Style

from .atlas import MordorAtlas

LEAF = [(0, (.03, .03, .02)), (.5, (.14, .14, .10)), (1, (.36, .35, .28))]         # dead scrub
GREY_CLOTH = [(0, (.02, .02, .02)), (.5, (.13, .13, .14)), (1, (.34, .34, .36))]      # preview only


def _palette(name, stone, rock, iron, trim, fire, wood, accents, slit=None, steel=None, witch=None):
    ramps = dict(stone=stone, rock=rock, iron=iron, trim=trim, fire=fire, wood=wood, cloth=GREY_CLOTH,
                 soot=iron, bronze=trim, gold=trim, silver=trim, inlay=trim, mark=trim, ground=rock, enamel=rock,
                 tiles=rock, leaf=LEAF, bone=stone, hide=wood, water=iron, witch=witch or slit or fire)
    if slit:
        ramps["slit"] = slit
    if steel:
        ramps["steel"] = steel
    base = dict(occl=(.05, .045, .045), edge=(.70, .62, .52), grime=(.05, .03, .02), moss=(.07, .065, .06),
                dirt=(.11, .09, .07), groove=(.02, .015, .015), glow=(1.0, .40, .06))
    return Palette(name, ramps, dict(base, **accents), tints=dict(stone_alt=(1.0, 1.0, 1.0),
                                                                  stone_alt2=(1.0, 1.0, 1.0)))


CHAR = [(0, (.012, .01, .008)), (.5, (.07, .058, .048)), (1, (.24, .20, .17))]      # charred timber
ASH = [(0, (.03, .03, .03)), (.25, (.16, .16, .155)), (.5, (.34, .34, .33)), (.75, (.52, .52, .51)),
       (1, (.68, .68, .66))]                                                          # ash-grey walks and ground
LAVA = [(0, (.05, .01, 0)), (.35, (.46, .09, 0)), (.7, (1.0, .45, .04)), (1, (1.0, .86, .46))]      # orange fire
MORGUL = [(0, (.02, .05, .01)), (.35, (.14, .38, .05)), (.7, (.52, .90, .22)), (1, (.88, 1.0, .68))]  # witch-fire
WITCH = [(0, (.02, .05, .01)), (.35, (.12, .34, .04)), (.7, (.40, .82, .14)), (1, (.70, 1.0, .40))]  # lit windows
# F2's first windows (since pass 7 only its few witch-lit slits): WITCH a third of the way toward GHOST
MORGUL_WINDOW = [(0, (.02, .047, .017)), (.35, (.127, .327, .087)), (.7, (.44, .827, .287)), (1, (.76, 1.0, .567))]
# F2's windows since the citadel's pass 7 (Max: "drastically reduce the green"): unlit, a dim ember deep in them
EMBER_WINDOW = [(0, (.01, .007, .005)), (.35, (.035, .012, .004)), (.7, (.09, .028, .006)), (1, (.19, .06, .012))]
GHOST = [(0, (.02, .04, .03)), (.35, (.14, .30, .18)), (.7, (.52, .84, .58)), (1, (.88, 1.0, .90))]  # Minas Morgul's
# sharpened steel: cold and hard, only on the blades' brightest metal (paint.py "steel"), never on every edge
STEEL = [(0, (.05, .055, .065)), (.3, (.22, .24, .27)), (.6, (.55, .58, .63)), (.85, (.80, .83, .88)),
         (1, (.95, .97, 1.0))]
# the same steel with the fire's orange on its flanks: a white-hot core on each blade, heat below it
HOT_STEEL = [(0, (.10, .05, .02)), (.3, (.52, .24, .07)), (.62, (.80, .44, .15)), (.78, (.70, .70, .72)),
             (.9, (.86, .88, .92)), (1, (.96, .98, 1.0))]
FIRE_AND_SHADOW = dict(
    stone=[(0, (.018, .017, .016)), (.3, (.105, .10, .096)), (.6, (.24, .23, .22)), (.85, (.38, .37, .355)),
           (1, (.53, .52, .50))],
    rock=ASH,
    iron=[(0, (.014, .012, .012)), (.3, (.07, .064, .06)), (.6, (.16, .148, .135)), (.85, (.27, .25, .225)),
          (1, (.38, .35, .31))],
    trim=[(0, (.08, .04, .02)), (.3, (.26, .12, .04)), (.6, (.52, .24, .07)), (.85, (.74, .38, .12)),
          (1, (.92, .58, .28))],
    fire=LAVA, slit=WITCH, wood=CHAR, accents=dict(glow=(1.0, .45, .05)))

PALETTES = {
    "A": _palette(
        "A Ash and lava",
        stone=[(0, (.02, .02, .022)), (.3, (.12, .12, .125)), (.6, (.29, .29, .30)), (.85, (.45, .45, .46)),
               (1, (.60, .60, .61))],
        rock=[(0, (.03, .03, .03)), (.25, (.17, .168, .165)), (.5, (.36, .355, .35)), (.75, (.55, .545, .54)),
              (1, (.72, .71, .70))],
        iron=[(0, (.02, .016, .014)), (.3, (.09, .07, .06)), (.6, (.20, .15, .12)), (.85, (.33, .25, .19)),
              (1, (.46, .36, .28))],
        trim=[(0, (.12, .05, .02)), (.3, (.40, .16, .04)), (.6, (.72, .32, .08)), (.85, (.90, .50, .16)),
              (1, (1.0, .72, .38))],
        fire=[(0, (.05, .01, 0)), (.35, (.46, .09, 0)), (.7, (1.0, .45, .04)), (1, (1.0, .86, .46))],
        wood=CHAR, accents=dict(glow=(1.0, .45, .05))),
    "B": _palette(
        "B The Red Eye",
        stone=[(0, (.008, .006, .006)), (.3, (.05, .04, .038)), (.6, (.13, .105, .098)), (.85, (.26, .215, .20)),
               (1, (.40, .34, .31))],
        rock=[(0, (.015, .012, .01)), (.25, (.095, .08, .07)), (.5, (.21, .18, .155)), (.75, (.36, .31, .27)),
              (1, (.50, .44, .38))],
        iron=[(0, (.01, .01, .01)), (.3, (.05, .045, .042)), (.6, (.12, .105, .09)), (.85, (.22, .19, .16)),
              (1, (.33, .29, .24))],
        trim=[(0, (.09, .06, .02)), (.3, (.34, .23, .08)), (.6, (.62, .45, .17)), (.85, (.80, .63, .28)),
              (1, (.92, .80, .48))],
        fire=[(0, (.04, 0, 0)), (.35, (.42, .025, 0)), (.7, (.96, .20, .02)), (1, (1.0, .58, .26))],
        wood=CHAR, accents=dict(edge=(.78, .62, .34), glow=(1.0, .25, .04))),
    "C": _palette(
        "C Scorched bone",
        stone=[(0, (.10, .095, .09)), (.3, (.36, .345, .33)), (.6, (.60, .58, .555)), (.85, (.76, .74, .71)),
               (1, (.88, .86, .83))],
        rock=[(0, (.02, .02, .02)), (.25, (.10, .095, .09)), (.5, (.24, .23, .22)), (.75, (.40, .385, .37)),
              (1, (.56, .54, .52))],
        iron=[(0, (.006, .006, .007)), (.3, (.03, .03, .033)), (.6, (.08, .08, .085)), (.85, (.16, .16, .17)),
              (1, (.26, .26, .27))],
        trim=[(0, (.06, .01, .005)), (.3, (.26, .04, .02)), (.6, (.50, .08, .035)), (.85, (.66, .14, .06)),
              (1, (.82, .28, .15))],
        fire=[(0, (.03, 0, 0)), (.35, (.38, .02, 0)), (.7, (.92, .10, .03)), (1, (1.0, .50, .34))],
        wood=CHAR, accents=dict(edge=(.80, .30, .18), glow=(.95, .12, .04))),
    "D": _palette(
        "D Gorgoroth rust",
        stone=[(0, (.014, .013, .012)), (.3, (.075, .07, .066)), (.6, (.17, .16, .15)), (.85, (.29, .275, .26)),
               (1, (.42, .40, .38))],
        rock=[(0, (.02, .016, .01)), (.25, (.11, .09, .06)), (.5, (.24, .20, .13)), (.75, (.40, .34, .22)),
              (1, (.55, .48, .32))],
        iron=[(0, (.03, .006, .004)), (.3, (.15, .03, .018)), (.6, (.34, .07, .035)), (.85, (.50, .12, .06)),
              (1, (.64, .22, .12))],
        trim=[(0, (.10, .025, .012)), (.3, (.34, .08, .035)), (.6, (.56, .15, .07)), (.85, (.72, .28, .14)),
              (1, (.86, .46, .28))],
        fire=[(0, (.04, .03, 0)), (.35, (.40, .30, 0)), (.7, (.95, .85, .10)), (1, (1.0, 1.0, .60))],
        wood=CHAR, accents=dict(edge=(.85, .55, .30), glow=(.95, .85, .15))),
    "E": _palette(
        "E Morgul",
        stone=[(0, (.018, .019, .019)), (.3, (.11, .115, .112)), (.6, (.25, .26, .255)), (.85, (.40, .41, .40)),
               (1, (.55, .56, .55))],
        rock=ASH,
        iron=[(0, (.012, .014, .014)), (.3, (.065, .07, .07)), (.6, (.15, .16, .16)), (.85, (.26, .27, .27)),
              (1, (.36, .37, .37))],
        trim=[(0, (.04, .05, .03)), (.3, (.15, .20, .09)), (.6, (.34, .47, .18)), (.85, (.54, .70, .30)),
              (1, (.76, .90, .56))],
        fire=MORGUL, slit=WITCH, wood=CHAR, accents=dict(edge=(.62, .74, .48), glow=(.55, .95, .25))),
    "F": _palette("F Fire and shadow", **FIRE_AND_SHADOW),
    "F2": _palette("F2 Fire, shadow and steel", **dict(FIRE_AND_SHADOW, steel=STEEL, slit=EMBER_WINDOW,
                                                         witch=MORGUL_WINDOW)),
    "F3": _palette("F3 Fire, steel and ghost-light", **dict(FIRE_AND_SHADOW, steel=STEEL, slit=GHOST)),
    "F4": _palette("F4 Hot steel and ghost-light", **dict(FIRE_AND_SHADOW, steel=HOT_STEEL, slit=GHOST)),
    "G": _palette(
        "G Barad-dur",
        stone=[(0, (.016, .016, .018)), (.3, (.095, .095, .10)), (.6, (.22, .22, .23)), (.85, (.36, .36, .37)),
               (1, (.50, .50, .51))],
        rock=[(0, (.03, .028, .025)), (.25, (.15, .14, .125)), (.5, (.31, .29, .26)), (.75, (.48, .45, .41)),
              (1, (.63, .60, .55))],
        iron=[(0, (.01, .01, .011)), (.3, (.055, .055, .06)), (.6, (.13, .13, .14)), (.85, (.22, .22, .23)),
              (1, (.32, .32, .33))],
        trim=[(0, (.05, .04, .035)), (.3, (.17, .14, .12)), (.6, (.33, .27, .22)), (.85, (.46, .37, .29)),
              (1, (.60, .48, .36))],
        fire=[(0, (.05, .005, 0)), (.35, (.50, .06, 0)), (.7, (1.0, .34, .03)), (1, (1.0, .78, .40))],
        slit=[(0, (.06, .01, 0)), (.35, (.55, .12, 0)), (.7, (1.0, .50, .06)), (1, (1.0, .88, .52))],
        wood=CHAR, accents=dict(edge=(.62, .52, .42), glow=(1.0, .40, .04))),
}
NOTES = {
    "A": "Grey basalt, ash-grey rock, dark rusted iron with hot orange edges, molten orange glow",
    "B": "Black stone and blackened iron, tarnished bronze and brass trims, deep red-orange glow",
    "C": "Pale ash-white weathered stone, black iron, red trims and glow",
    "D": "Charcoal stone, rust-red iron, scorched ochre ground, sulphur-yellow glow",
    "E": "Black stone, ash-grey walks, dark iron; sickly green witch-light in windows, trims and pyres",
    "F": "Black basalt and ash, orange fire and lava on the pyres and edges, Morgul green in the windows",
    "F2": "F with hard cold steel on the blades only; windows a dim ember, Morgul green on a few slits only",
    "F3": "F2 with a pale green-white witch-light in the windows (Minas Morgul), less lime",
    "F4": "F3 with the blades' steel only on their bright core, orange heat on the flanks",
    "G": "The films' Barad-dur: black iron-stone, ash ground, dull iron edges, windows and pyres fire-lit",
}
PALETTE = PALETTES["F2"]
# new faces of these atlas regions painted as a material: (ramp, gain, lift)
TAGRAMPS = {"iron": ("iron", 0.9, 0.0), "trim": ("trim", 0.9, 0.25), "cloth": ("cloth", 0.85, 0.2),
            "ember": ("fire", 0.6, 0.55), "flame": ("fire", 0.25, 0.74), "chain": ("iron", 0.8, 0.0),
            "soot": ("soot", 0.5, 0.0), "witch": ("witch", -2.4, 1.0)}     # witch: lit like a slit (paint.py)


class MordorStyle(Style):
    faction = 'mordor'
    name = PALETTE.name
    palette = PALETTE
    atlas = MordorAtlas()
    # the Haradrim palace and the mumakil pen are Mordor's but live in BFME1's evilmen folder
    ini_dir = ['data\\ini\\object\\evilfaction\\structures\\mordor\\',
               'data\\ini\\object\\evilfaction\\structures\\evilmen\\haradrimpalace.ini',
               'data\\ini\\object\\evilfaction\\structures\\evilmen\\mumakilpen.ini']
    sheet_dir = 'art\\compiledtextures\\mb\\'
    master_variants = {'damaged': 'MBFortress_D.tga', 'snow': 'MBFortress_snow.tga'}
    house_template = 'MBHCSentry'   # copied for buildings EA gave no house-colour model (the expansions): check
    # the palette options tool (sagekit/palettes.py): the choices, their notes, where they are shown
    palettes = PALETTES
    palette_notes = NOTES
    palette_ea_note = "Warm brown-grey plate and slab, rust flecks, a red lava vein"
    palette_building = 'fortress'
    palette_views = ('board', 'tower')
    swatches = (("stone", "stone", 0.55), ("rock / ground", "rock", 0.5), ("iron", "iron", 0.6),
                ("trim", "trim", 0.75), ("lava / glow", "fire", 0.75), ("windows", "slit", 0.8),
                ("witch-light", "witch", 0.8), ("steel", "steel", 0.85))

    def shapes(self):
        """The Mordor kit (assets/mordor/shapes.py; Blender side, needs mathutils)."""
        from .shapes import MordorShapes
        return MordorShapes()

    def recolour(self):
        from .paint import mordor_layers
        return mordor_layers()["MordorRecolour"]()

    def sheet_layers(self):
        return [self.recolour()]

    def layers(self, building):
        from sagekit.paint import layers as L

        return [self.recolour(),
                *[L.TagRamp(tag, r, gain=g, lift=k) for tag, (r, g, k) in TAGRAMPS.items()],
                L.BuildingDecals(building),
                L.WoodGrain(depth=0.22),
                L.Occlusion(),
                L.EdgeWear(base=0.3, metal=0.5),
                L.Streaks(),
                L.GroundDirt()]
