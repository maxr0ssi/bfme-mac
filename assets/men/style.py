"""Gondor: white limestone of Minas Tirith, charcoal slate, bright forged steel, a little old gold on
finials, stars and crests, and black heraldic fields for the White Tree. Contrast is the point:
the stone is brighter than EA's grey, the steel clearly silver against it, the fields near black,
so small details read from the RTS camera. Not the Elves' ivory, mithril and mallorn gold (warm
cream, soft silver, rich gold): cool white stone, hard steel, sparing gold."""
from sagekit.style import Palette, Style

from .atlas import MenAtlas

STONE = [(0, (.13, .13, .125)), (.25, (.40, .40, .385)), (.5, (.66, .66, .64)),
         (.75, (.84, .84, .82)), (1, (.965, .96, .94))]
STEEL = [(0, (.07, .08, .09)), (.3, (.30, .33, .36)), (.6, (.60, .64, .67)), (.85, (.83, .86, .88)), (1, (.97, .98, .99))]
IRON = [(0, (.03, .03, .035)), (.4, (.12, .13, .14)), (.8, (.30, .32, .34)), (1, (.52, .54, .56))]
GOLD = [(0, (.14, .11, .05)), (.4, (.46, .37, .17)), (.7, (.75, .63, .35)), (1, (.96, .89, .65))]
SLATE = [(0, (.03, .035, .045)), (.35, (.12, .135, .16)), (.7, (.25, .28, .32)), (1, (.46, .50, .55))]
SABLE = [(0, (.012, .014, .018)), (.5, (.045, .05, .06)), (1, (.16, .17, .19))]
NAVY = [(0, (.02, .03, .08)), (.4, (.06, .10, .25)), (.7, (.12, .19, .43)), (1, (.30, .38, .63))]   # preview only
WOOD = [(0, (.09, .065, .045)), (.5, (.36, .29, .21)), (1, (.70, .61, .47))]
ramps = dict(stone=STONE, bronze=GOLD, gold=GOLD, inlay=STEEL, trim=STEEL, iron=IRON, wood=WOOD,
             ground=SLATE, enamel=SABLE, cloth=NAVY, rock=STONE, tiles=SLATE,
             leaf=[(0, (.04, .06, .025)), (.5, (.24, .31, .13)), (1, (.67, .65, .34))])
PALETTE = Palette('Gondor: white stone, steel and sable', ramps,
                  dict(occl=(.24, .245, .26), edge=(1.0, 1.0, .98), grime=(.30, .29, .27),
                       moss=(.32, .36, .25), dirt=(.40, .37, .32), groove=(.20, .21, .23), glow=None),
                  tints=dict(stone_alt=(1.02, 1.0, .97), stone_alt2=(.97, .99, 1.02)))
# new faces of these atlas regions painted as a material: (ramp, gain, lift)
TAGRAMPS = {"trim": ("trim", 0.8, 0.22), "gilt": ("gold", 0.9, 0.12), "enamel": ("enamel", 0.9, 0.0),
            "iron": ("iron", 0.9, 0.05), "relief": ("stone", 0.5, 0.52), "cloth": ("cloth", 0.85, 0.2),
            "slate": ("tiles", 1.0, 0.0)}
RECOLOUR = dict(stone_pivot=.40, stone_gain=1.1, stone_mid=.56)


class MenStyle(Style):
    faction = 'men'
    name = PALETTE.name
    palette = PALETTE
    atlas = MenAtlas()
    ini_dir = 'data\\ini\\object\\goodfaction\\structures\\men\\'
    sheet_dir = 'art\\compiledtextures\\gb\\'
    master_variants = {'damaged': 'GBFortress1D.tga', 'snow': 'GBFortress1_Snow.tga',
                       'stonework': 'GBFortress1_U.tga'}
    house_template = 'GBHCBtlTwrM'   # copied for buildings EA gave no house-colour model (walls, expansions)

    def shapes(self):
        from .shapes import MenShapes
        return MenShapes()

    def sheet_layers(self):
        from sagekit.paint import layers as L

        from .paint import keep_layers, men_layers
        k = keep_layers()               # wood, thatch, dirt, fruit, coals and red cloth stay EA's; slate charcoal
        return [L.Recolour(**RECOLOUR), k["SheetSlate"](), men_layers()[0](), k["Materials"]()]

    def layers(self, building):
        from sagekit.paint import layers as L

        from .paint import men_layers
        Lawn, SteelJoint, _ = men_layers()
        return [L.Recolour(**RECOLOUR),
                *[L.TagRamp(tag, r, gain=g, lift=k) for tag, (r, g, k) in TAGRAMPS.items()],
                Lawn(),
                L.BuildingDecals(building),
                L.WoodGrain(depth=0.22),
                SteelJoint(),
                L.Occlusion(),
                L.EdgeWear(base=0.2, metal=0.4),
                L.Streaks(),
                L.GroundDirt()]
