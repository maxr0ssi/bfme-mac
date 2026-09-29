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
soot and water (the dammed Isen in the sluices). The rects were read by eye on the flat sheet; confirm them on the citadel's first bake."""
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
    }
    painted = ('cloth', 'ember', 'mark', 'chain', 'soot', 'trim', 'water')
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
