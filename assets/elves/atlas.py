"""EBFortress: the sheet the Elven fortress, its upgrades and expansions and the castle walls (segment,
cliff cap, hub, gate) are painted on - 15 model families. Regions measured on the 1024 original
(twice the Dwarven sheet, hence density 5.6: EA's walls sample it at 5.0..7.2 px per unit, median
5.6); mask hints on its 4x upscale (4096), written as original pixels through `up()`.

The sheet is DXT5 with cut-out alpha (`cutout`): the filigree lattice panel, the leaf emblem, the
teal arch's window lattice and the pool's faded edge are holes EA's alpha-tested faces show
through. New faces take the atlas's alpha where they sample it (sagekit/alpha.py; the `painted`
regions stay opaque), so a tag on a cut-out region cuts holes in new geometry: the kit maps none
(everything it samples is opaque); a recipe may use one on purpose, for real tracery.

Regions whose new faces are a material of their own (`painted`: repainted by a TagRamp, never
masonry or moss) take their grain from plain stone: gilt, enamel and crystal are plain stone
repainted mallorn gold, deep slate and blue-white glass, as the Dwarven trim is stone repainted
bronze; "trim" is the same stone repainted mithril silver (style.py TAGRAMPS): the fillet's bands
had broad silver faces (copings, ridges) read as mottled stone.

EA's Elven stone, slate and bark are themselves blue-grey (saturation 0.08..0.2 at teal-blue hues),
which the framework's colour rule read as enamel ground: teal blotches over the battle tower's
shaft, the boards and the mallorn bark. `ground_sat` asks for real colour (EA's teal arch frame,
lattice and pool are 0.3 and up); the building's own sheets inherit it (Building.sheet_atlas).
"""
from sagekit.atlas import Atlas, Region


def up(x0, y0, x1, y1):
    """An original-pixel rect on the 4x upscale the masks are computed on."""
    return (4 * x0, 4 * y0, 4 * x1, 4 * y1)


# the sheet's opaque plain stone, reused by the painted regions for an even grain
PLAIN_LIGHT = (210, 676, 300, 700)       # the flat white stone right of the coping moulding
PLAIN_MID = (936, 800, 1020, 1016)        # the plain wall stone down the sheet's right edge


class ElvenAtlas(Atlas):
    texture = "EBFortress.tga"
    normal = "EBFortress_NRM.tga"
    size = 1024
    density = 5.6
    regions = {                                                     # order matters: face tags index it
        "stoneA": Region((108, 740, 236, 824)),                     # dressed ashlar, the walls' own stone
        "stoneB": Region(PLAIN_MID),                                # plain pale stone, grime streaks
        "top": Region(PLAIN_LIGHT),                                 # walk tops, sills, caps (lightest)
        "course": Region((0, 642, 300, 670), Region.BAND, su=5.6),  # darker ledge / string course
        "coping": Region((0, 673, 200, 702), Region.BAND, su=5.6),  # white torus moulding (cornices)
        "trim": Region(PLAIN_LIGHT),                                # mithril silver (repainted: an even grain)
        "scallop": Region((400, 738, 526, 760), Region.BAND, period=21.0),  # little arcade frieze, 6 arches
        "knot": Region((970, 750, 1024, 782), Region.BAND),         # knotwork band: silver knot, verdigris ground
        "arcade": Region((749, 836, 797, 912), Region.BAND, period=48.0),   # one bay of the colonnette arcade
        "pilaster": Region((366, 742, 406, 1020), Region.STRETCH),  # rusticated pilaster strip
        "column": Region((700, 862, 735, 1000), Region.STRETCH),    # fluted column shaft
        "capital": Region((692, 836, 742, 862), Region.STRETCH),    # its capital
        "lancet": Region((722, 702, 828, 830), Region.STRETCH),     # gold leaf-lancet tracery on slate
        "vine": Region((532, 640, 598, 716), Region.STRETCH),       # gold vine spandrel on dark green
        "window": Region((418, 814, 508, 988), Region.STRETCH),     # arched lattice window (opaque glass)
        "roof": Region((828, 446, 934, 690)),                       # slate scale roof
        "wood": Region((590, 450, 724, 594)),                       # warm vertical boards
        "birch": Region((390, 600, 526, 708)),                      # silver-grey weathered boards
        "bark": Region((2, 4, 104, 460)),                           # mallorn bark (the dark knotted trunk)
        "spire": Region((958, 164, 1022, 696), Region.STRETCH),     # a spire's outline panel
        "cloth": Region((56, 474, 82, 596), Region.STRETCH),        # EA's leaf banner (repainted, house colour)
        "gilt": Region(PLAIN_LIGHT),                                # mallorn gold (repainted)
        "enamel": Region(PLAIN_MID),                                # deep slate enamel (repainted)
        "crystal": Region((960, 100, 988, 234), Region.STRETCH),    # the green crystal shaft (repainted blue-white)
    }
    painted = ("cloth", "gilt", "enamel", "crystal", "trim")
    ground_sat = (0.2, 0.32)                # blue-grey stone and bark are no enamel (module notes)
    # cut-out alpha (original px): holes, not paint. Kept out of every kit tag until export keeps alpha
    cutout = {
        "filigree": (164, 64, 243, 114),        # teal knotwork lattice panel
        "leaf": (253, 240, 335, 304),           # the gold leaf emblem on its white plinth
        "arch_lattice": (340, 186, 415, 597),   # the teal arch frame's window lattice
        "pool": (163, 310, 362, 642),           # the teal-tiled pool and grass bank: alpha fades to 0
    }
    # EA's eagle (EBFE, the eagle's nest's bird: wing, talons, head and body) keeps EA's own browns in
    # the flat sheet recolour (sagekit/paint/sheets.py keep_motifs): the masks take the feathers for
    # metal and the recolour turned the bird bright gold. The stone between the feathers still recolours
    keep = {"eagle": [(310, 55, 425, 245), (355, 15, 805, 218), (755, 0, 1015, 110), (880, 110, 1000, 165)]}
    # EA's motifs the style repaints by colour (style.py Repaint; original px): the tan and cream
    # gable frames, swooping beams, leaf emblem and tracery (gold); the slate behind the gatehouse
    # roof's leaf-lancet tracery (roof slate, not the grille's teal glass); the tree-houses' pale
    # scale roofs (taken down to mid slate); the lattice window's pale leading (silver)
    gilded = [(163, 112, 262, 295), (253, 240, 335, 304), (0, 468, 52, 640), (520, 596, 832, 850),
              (620, 322, 770, 448), (760, 188, 824, 352), (785, 412, 975, 450), (780, 448, 832, 600),
              (468, 455, 522, 600)]
    roof_slate = [(700, 596, 832, 836)]
    roof_scales = [(828, 440, 936, 700), (878, 210, 970, 416)]   # the tree-houses' scale roofs, louvres
    leading = [(418, 814, 508, 988)]
    mask_hints = {
        # knotwork: light strokes -> inlay (silver), the rest of the band -> ground (verdigris enamel)
        "rune": [up(970, 750, 1024, 782)],
        "tiles": [up(828, 440, 936, 700), up(878, 210, 970, 416)],          # slate roof, dark louvres
        # dark glass: the lattice window's (stepped to its arch: the stone corners are no glass), and
        # the slate behind the leaf-lancet tracery (glass; as stone it lifted to a blotchy grey)
        "grille": [up(446, 814, 482, 819), up(436, 819, 496, 825), up(428, 825, 502, 833), up(422, 833, 506, 845),
                   up(418, 845, 508, 988), up(713, 633, 825, 832)],
        # bark, earth and the boarded house front: never metal or wood (colour alone flecks the boards'
        # highlights gold); the grass keeps its green through the style's Foliage
        "rock": [up(0, 0, 160, 470), up(236, 0, 320, 60), up(163, 312, 362, 386), up(163, 480, 310, 642),
                 up(478, 440, 822, 600)],
        # plain stone whose warm grime is not metal
        "stone": [up(108, 712, 306, 826), up(930, 790, 1024, 1024), up(832, 700, 930, 780),
                  up(0, 642, 306, 720), up(956, 160, 1024, 700)],
    }
