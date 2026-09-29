"""Isengard: Saruman's war-works round Orthanc. Black, hard, faceted stone; heavy riveted iron;
furnaces, chains and gears; fire only where metal is worked. Industry, not rot: never the
Goblins' crimson horn and bleached bone, never gore. Mordor will take red and black steel, so
Isengard's black is stone and its accents are forge orange and the White Hand's white.

The palette, "Orthanc black and silver" (Max's pick, 2026-09-28: A "with some strong
silver-white contrast"), recolours EA's own sheet through its material ramps
(assets/isengard/paint.py): near-black faceted stone with a cool sheen, dark iron, soot-black
timber, ember orange in coals, vents and throats, and a bright silver-white on the polished
edges: EA's brightest metal texels (the plates' lit rims and ribs), new trims, rivet bands and
rims (the "trim" tag), and the White Hand. The retired options B "Soot and rust" and C "Cold
steel" are in git history and in build/assets/isengard/_palettes/palette_options_v1.jpg.

Cloth follows the player's colour (house_template, like the Men's and the Goblins'); the "cloth"
ramp colours only the previews of new cloth faces."""
from sagekit.style import Palette, Style

from .atlas import IsengardAtlas

LEAF = [(0, (.04, .05, .03)), (.5, (.20, .23, .14)), (1, (.48, .50, .34))]
EMBER = [(0, (0, 0, 0)), (.35, (.40, .07, .0)), (.7, (1.0, .42, .05)), (1, (1.0, .86, .52))]
GREY_CLOTH = [(0, (.02, .02, .02)), (.5, (.13, .13, .14)), (1, (.34, .34, .36))]      # preview only


WATER = [(0, (.01, .015, .02)), (.5, (.06, .085, .10)), (1, (.30, .36, .40))]      # the Isen: dark, cold


def _palette(name, stone, rock, iron, wood, mark, silver, soot=None, fire=EMBER, cloth=GREY_CLOTH, water=WATER,
             accents=None):
    ramps = dict(stone=stone, rock=rock, iron=iron, wood=wood, mark=mark, silver=silver, fire=fire, cloth=cloth,
                 water=water, soot=soot or rock,
                 bronze=iron, gold=silver, inlay=mark, trim=silver, ground=rock, enamel=rock, tiles=rock, leaf=LEAF,
                 bone=mark, hide=wood)
    base = dict(occl=(.05, .05, .06), edge=(.86, .88, .92), grime=(.04, .035, .03), moss=(.07, .07, .07),
                dirt=(.10, .09, .08), groove=(.02, .02, .02), glow=(1.0, .45, .08))
    return Palette(name, ramps, dict(base, **(accents or {})), tints=dict(stone_alt=(1.0, 1.0, 1.0),
                                                                          stone_alt2=(1.0, 1.0, 1.0)))


# Orthanc's stone is black and glassy-hard: near-black with a cool sheen on its facets, not rough
# rock. Dark iron, soot-black timber, ember orange, and silver-white where edges catch the light.
PALETTES = {
    "A": _palette(
        "A Orthanc black and silver",
        stone=[(0, (.005, .006, .008)), (.3, (.025, .028, .034)), (.6, (.075, .08, .095)), (.85, (.19, .20, .23)),
               (1, (.44, .46, .50))],
        # natural rock and earth (the mounds, the ground discs, IBFortress's rock and cobbles): a
        # dark warm slate about 0.75 of EA's own luminance (TONES["rock"] maps it 1:1), so the
        # black architecture stands out from its own ground; soot keeps the old near-black ramp
        rock=[(0, (.006, .006, .006)), (.1, (.075, .071, .066)), (.25, (.20, .19, .175)), (.5, (.40, .38, .355)),
              (.75, (.58, .56, .53)), (1, (.72, .70, .67))],
        soot=[(0, (.008, .008, .008)), (.4, (.045, .043, .042)), (.75, (.12, .115, .11)), (1, (.26, .25, .24))],
        iron=[(0, (.012, .012, .013)), (.3, (.07, .07, .072)), (.6, (.19, .19, .195)), (.85, (.34, .345, .355)),
              (1, (.50, .51, .53))],
        wood=[(0, (.03, .024, .018)), (.3, (.11, .088, .07)), (.5, (.19, .15, .12)), (1, (.44, .37, .30))],
        mark=[(0, (.30, .31, .33)), (.5, (.84, .85, .87)), (1, (.98, .98, .99))],
        silver=[(0, (.10, .105, .11)), (.3, (.42, .44, .47)), (.6, (.72, .74, .77)), (.85, (.88, .90, .93)),
                (1, (.97, .98, 1.0))]),
}
NOTES = {"A": "Near-black faceted stone, dark iron, ember orange; silver-white edges, trims and the Hand"}
PALETTE = PALETTES["A"]
# new faces of these atlas regions painted as a material: (ramp, gain, lift). "iron" too: its
# region samples a bright plate, which the recolour turns silver-white (the pass-6 chimneys read
# as white ladders); new iron is dark, silver only where EdgeWear catches an edge
TAGRAMPS = {"iron": ("iron", 0.9, 0.0), "trim": ("silver", 0.9, 0.25), "cloth": ("cloth", 0.85, 0.2),
            "ember": ("fire", 0.6, 0.55),
            "flame": ("fire", 0.25, 0.74),
            "mark": ("mark", 0.4, 0.6), "chain": ("iron", 0.8, 0.0), "soot": ("soot", 0.5, 0.0),
            "water": ("water", 0.8, 0.1)}


class IsengardStyle(Style):
    faction = 'isengard'
    name = PALETTE.name
    palette = PALETTE
    atlas = IsengardAtlas()
    ini_dir = 'data\\ini\\object\\evilfaction\\structures\\isengard\\'
    sheet_dir = 'art\\compiledtextures\\ib\\'
    master_variants = {'damaged': 'IBFortress_D.tga', 'snow': 'IBFortress_snow.tga', 'stonework': 'IBFortress_U.tga'}
    house_template = 'IBHCBtlTwr'   # copied for buildings EA gave no house-colour model (the expansions): check
    # the palette options tool (sagekit/palettes.py): the choices, their notes, where they are shown
    palettes = PALETTES
    palette_notes = NOTES
    palette_building = 'fortress'
    palette_views = ('close', 'keep')
    swatches = (("Orthanc stone", "stone", 0.55), ("rock", "rock", 0.6), ("iron", "iron", 0.6),
                ("silver edges", "silver", 0.8), ("timber", "wood", 0.6), ("White Hand", "mark", 0.8),
                ("forge fire", "fire", 0.75))

    def shapes(self):
        """The Isengard kit (assets/isengard/shapes.py; Blender side, needs mathutils)."""
        from .shapes import IsengardShapes
        return IsengardShapes()

    def sheet_atlas(self, name):
        """The buildings' own sheets' material rects (atlas.py SHEETS) for `sagekit sheets`; the
        rest as before (IBFortress: the faction atlas; others: a plain one)."""
        from .atlas import sheet_atlas
        return sheet_atlas(name) or super().sheet_atlas(name)

    def recolour(self, building=None):
        """The first paint layer: IsengardRecolour, or for a building on its own sheet (atlas.py
        SHEETS) and for flat sheets IsengardSheetRecolour (identical where no table applies)."""
        from .atlas import sheet_atlas
        from .paint import isengard_layers, isengard_sheet_layers
        if building is None:
            return isengard_sheet_layers()["IsengardSheetRecolour"]()
        own = sheet_atlas(building.sheet_atlas.texture) if building.two_sheets else None
        if own is None:
            return isengard_layers()["IsengardRecolour"]()
        return isengard_sheet_layers()["IsengardSheetRecolour"](sheet_atlas=own)

    def sheet_layers(self):
        return [self.recolour()]

    def layers(self, building):
        from sagekit.paint import layers as L

        from .paint import isengard_layers

        recolour = self.recolour(building)
        return [recolour,
                *[L.TagRamp(tag, r, gain=g, lift=k) for tag, (r, g, k) in TAGRAMPS.items()],
                L.BuildingDecals(building),
                L.WoodGrain(depth=0.22),
                isengard_layers()["IsengardOcclusion"](recolour),
                L.EdgeWear(base=0.3, metal=0.55),
                L.Streaks(),
                L.GroundDirt()]
