"""The Goblins of the Misty Mountains: Goblin-town under the mountain, crude and rotten, near Angmar
in spirit. Rough rock, crude timber, horn and bone, rusted iron, sickly torchlight. Never Mordor's
black steel and lava red, never Isengard's cold teal-grey steel: stone and bone, not forged metal.

The palette, "Blood, iron and bone", recolours EA's own sheet through six material ramps
(assets/goblins/paint.py): dried-blood crimson hide and horn, gritty tarnished silver on plates and
spikes, near-black rock and charcoal timber, no brown; cool bleached white on the tusks, spike
tips, skulls and bone trim, as accents only. It stays clear of Mordor (blue-black steel,
orange-red lava glow on MBFortress): its red is a cool crimson (hue ~350, never orange) on horn and
hide, its metal silver, not black steel.

Cloth follows the player's colour (house_template, like the Men's); the "cloth" ramp colours only
the previews of new cloth faces."""
from sagekit.style import Palette, Style

from .atlas import GoblinAtlas

LEAF = [(0, (.04, .05, .02)), (.5, (.22, .26, .12)), (1, (.55, .55, .30))]


def _palette(name, stone, rock, bone, hide, wood, iron, cloth, fire, accents):
    ramps = dict(stone=stone, rock=rock, bone=bone, hide=hide, wood=wood, iron=iron, cloth=cloth, fire=fire,
                 bronze=iron, gold=bone, inlay=bone, trim=iron, ground=rock, enamel=rock, tiles=rock, leaf=LEAF)
    return Palette(name, ramps, accents, tints=dict(stone_alt=(1.0, 1.0, 1.0), stone_alt2=(1.0, 1.0, 1.0)))


PALETTE = _palette(
    "Blood, iron and bone",
    stone=[(0, (.012, .012, .014)), (.3, (.05, .05, .055)), (.6, (.12, .12, .13)), (.85, (.21, .21, .23)),
           (1, (.31, .31, .33))],
    rock=[(0, (.006, .006, .008)), (.35, (.03, .03, .035)), (.7, (.085, .085, .095)), (1, (.20, .20, .22))],
    bone=[(0, (.10, .10, .11)), (.25, (.50, .51, .53)), (.5, (.80, .81, .83)), (.75, (.91, .92, .93)),
          (1, (.97, .98, .99))],
    hide=[(0, (.03, .004, .008)), (.15, (.16, .012, .025)), (.35, (.40, .035, .06)), (.55, (.58, .07, .09)),
          (.75, (.72, .14, .15)), (1, (.86, .36, .34))],
    wood=[(0, (.008, .007, .007)), (.5, (.045, .04, .04)), (.85, (.11, .10, .10)), (1, (.18, .17, .17))],
    iron=[(0, (.02, .022, .026)), (.25, (.12, .13, .145)), (.5, (.33, .35, .38)), (.75, (.60, .62, .66)),
          (.9, (.80, .82, .85)), (1, (.95, .96, .98))],
    cloth=[(0, (.02, .02, .02)), (.5, (.13, .13, .14)), (1, (.34, .34, .36))],      # preview only: player colour
    fire=[(0, (0, 0, 0)), (.4, (.34, .02, .03)), (.75, (.86, .16, .12)), (1, (1.0, .72, .62))],
    accents=dict(occl=(.07, .07, .08), edge=(.90, .92, .96), grime=(.09, .01, .015), moss=(.08, .08, .085),
                 dirt=(.10, .09, .09), groove=(.02, .02, .025), glow=(.95, .22, .15)))
# new faces of these atlas regions painted as a material: (ramp, gain, lift). Bone is bleached white
# whatever the horn texel it samples; rope is dark leather thong, gore dried blood, paint the white war
# paint, socket the black of skulls' eyes and mouths, ember a brazier's coals
TAGRAMPS = {"iron": ("iron", 1.4, 0.1), "cloth": ("cloth", 0.85, 0.2), "bone": ("bone", 0.9, 0.2),
            "rope": ("hide", 0.55, 0.02), "gore": ("hide", 0.35, 0.02), "paint": ("bone", 0.35, 0.62),
            "socket": ("rock", 0.4, 0.0), "ember": ("fire", 0.6, 0.45)}
EDGE = (0.3, 0.45)                          # edge wear: bright scratched silver edges ("gritty")
# only truly grey texels are rock (EA's dark reddish spire scales are horn: crimson)
ROCK_RULE = dict(rock=((0.24, 0.40), (0.10, 0.17)))


class GoblinStyle(Style):
    faction = 'goblins'
    name = PALETTE.name
    palette = PALETTE
    atlas = GoblinAtlas()
    ini_dir = 'data\\ini\\object\\evilfaction\\structures\\wild\\'
    sheet_dir = 'art\\compiledtextures\\wb\\'
    master_variants = {'damaged': 'WBFortress_D.tga', 'snow': 'WBFortress_snow.tga', 'stonework': 'WBFortress_U.tga'}
    house_template = 'WBHCTower'    # copied for buildings EA gave no house-colour model (the expansions)

    def shapes(self):
        """The Goblin kit (assets/goblins/shapes.py; Blender side, needs mathutils)."""
        from .shapes import GoblinShapes
        return GoblinShapes()

    def sheet_atlas(self, name):
        """The production sheets' own material rects (atlas.py SHEETS) for `sagekit sheets`; the
        rest as before (WBFortress: the faction atlas; others: a plain one)."""
        from .atlas import sheet_atlas
        return sheet_atlas(name) or super().sheet_atlas(name)

    def recolour(self, building=None):
        """The first paint layer: GoblinRecolour, or for a production building on its own sheet
        (atlas.py SHEETS) and for flat sheets GoblinSheetRecolour (identical where no table applies)."""
        from .atlas import sheet_atlas
        from .paint import goblin_layers, goblin_sheet_layers
        if building is None:
            return goblin_sheet_layers()["GoblinSheetRecolour"](**ROCK_RULE)
        own = sheet_atlas(building.sheet_atlas.texture) if building.two_sheets else None
        if own is None:
            return goblin_layers()["GoblinRecolour"](**ROCK_RULE)
        return goblin_sheet_layers()["GoblinSheetRecolour"](sheet_atlas=own, **ROCK_RULE)     # own.tones: in apply

    def sheet_layers(self):
        return [self.recolour()]

    def layers(self, building):
        from sagekit.paint import layers as L

        return [self.recolour(building),
                *[L.TagRamp(tag, r, gain=g, lift=k) for tag, (r, g, k) in TAGRAMPS.items()],
                L.BuildingDecals(building),
                L.WoodGrain(depth=0.22),
                L.Occlusion(),
                L.EdgeWear(base=EDGE[0], metal=EDGE[1]),
                L.Streaks(),
                L.GroundDirt()]
