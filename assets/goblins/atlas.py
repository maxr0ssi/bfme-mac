"""WBFortress (512): the Goblin master sheet, and where its materials are.

EA painted the Goblin fortress almost entirely in one warm red-brown: carved horn and hide plates
(the dragon head, the scaled buttresses), pale bone and tusks, reddish block masonry, dark grey
rock curtains (the wavy drapes between the horn pillars), a few timber planks with square rivets
and one beaten plate. Colour alone cannot tell the planks and blocks from the horn (the stock
material masks call the whole sheet bronze), so the materials are declared here:

    materials   {material: [(x0, y0, x1, y1)]} in the sheet's pixels (y down): timber, brick, iron.
                Everything else is told apart by colour in GoblinRecolour (assets/goblins/paint.py):
                dark grey texels are rock, pale unsaturated ones bone, the rest hide and horn.
    mask_hints  one "stone" hint over the whole upscale: the stock masks' bronze and wood (the
                warm texels) are off, so EdgeWear and WoodGrain do not treat the horn as metal.

Regions for new faces (the kit, shapes.py): plain rock and blocks, bleached bone (the long pale
horn, stretched over each face so a tusk never tiles), crimson hide (the dragon's scaled plates),
a timber plank, and the painted materials, each repainted by a TagRamp of the style (style.py):
iron (silver), cloth (the player's colour), rope (dark leather thongs), gore (dried blood), paint
(the white war-paint markings), socket (the black of eye sockets and mouths) and ember (coals)."""
from sagekit.atlas import Atlas, Region

PLAIN = (248, 424, 326, 506)              # plain reddish blocks (the lower brick panel)


class GoblinAtlas(Atlas):
    texture = 'WBFortress.tga'
    normal = 'WBFortress_NRM.tga'
    size = 512
    density = 3.0
    ground_sat = (.6, .8)                 # no teal "band ground" on this sheet: the drapes' blue-grey is rock
    regions = {                                                   # order matters: face tags index it
        'stoneA': Region(PLAIN),
        'stoneB': Region((130, 44, 190, 196)),                     # the upper block wall
        'rock': Region((60, 410, 88, 500)),                       # a dark rock curtain
        'bone': Region((436, 56, 447, 124), Region.STRETCH),      # the long pale horn (tusks, bones, skulls)
        'hide': Region((280, 150, 370, 250)),                     # the dragon's scaled plates
        'timber': Region((102, 24, 123, 196), Region.STRETCH),    # a riveted plank
        'iron': Region(PLAIN),
        'cloth': Region(PLAIN),
        'rope': Region((102, 24, 123, 196), Region.STRETCH),      # the painted materials below take their
        'gore': Region((280, 150, 370, 250)),                     # grain from these (the hide's for gore,
        'paint': Region((436, 56, 447, 124), Region.STRETCH),     # the bone's for the white paint)
        'socket': Region((60, 410, 88, 500)),
        'ember': Region((60, 410, 88, 500)),
    }
    painted = ('iron', 'cloth', 'rope', 'gore', 'paint', 'socket', 'ember')
    materials = {
        'timber': [(40, 0, 64, 206), (100, 20, 125, 200), (366, 268, 384, 392)],
        # (x 64..100, y 20..190 and the panels at x 0..180, y 206..322 look like blocks but are the
        # spires' and buttresses' horn scales: hide, not masonry; measured from the citadel's bake)
        'brick': [(125, 40, 192, 200), (240, 392, 332, 512)],
        'iron': [(180, 206, 240, 322), (268, 282, 366, 300)],
    }
    mask_hints = {
        'stone': [(0, 0, 4 * 512, 4 * 512)],
    }


# ------------------------------------------------------------------ the production group's own sheets
# EA's faces of the production buildings paint from sheets of their own, not WBFortress: each gets
# its material rects here, in that sheet's own pixels (x right, y down; MBLumberMill is 256, the
# rest 512), read on EA's faces only (new faces keep GoblinAtlas.materials). "rock" wins over every
# colour rule inside its rects (GoblinSheetRecolour, paint.py), so pale rock never reads as bone.
# Checked by eye on the flat sheets (build/assets/goblins/<b>/src/*.png) and the flat recolour test;
# confirm against the first bakes. An optional third item overrides GoblinRecolour's tones (gain, lift)
# for that sheet's EA faces ("all": True: for the building's new faces too; "ramps": palette ramps
# replaced for that sheet).
SHEETS = {
    "wbcave.tga": (512, {                               # cave: the claw plank and the red interior stay
        "iron": [(365, 175, 432, 312)],                 # hide by colour, the skull pile bone
        "rock": [(0, 0, 60, 128), (0, 130, 365, 175), (432, 195, 512, 320), (0, 320, 330, 512)],
    }),
    "wbstone.tga": (512, {"rock": [(0, 0, 512, 512)]}),            # fissure (and the cave's rock, EA's mesh)
    "wbbstone.tga": (512, {"rock": [(0, 0, 512, 512)]}),           # spider pit
    "wbpit2.tga": (512, {                               # mine shaft: the collar silver iron (Max)
        "iron": [(0, 0, 512, 245), (256, 245, 512, 512)],
        "brick": [(0, 245, 256, 470)],                  # the white rubble: stone, not bone
        "rock": [(0, 470, 256, 512)],
    }, {"iron": (1.05, -0.05)}),                        # EA's bright rust: a darker silver than WBFortress's plates
    "wbtreatrov.tga": (512, {"iron": [(185, 118, 256, 240)]}),     # trove: scales and horn plates by colour
    "mblumbermill.tga": (256, {                         # lumber mill: the red wood-chips timber (Max);
        "timber": [(155, 0, 190, 150), (190, 0, 256, 176), (0, 125, 95, 185), (95, 125, 150, 256),
                   (176, 176, 256, 224)],               # the stumps' and logs' cut ends (160..176,
        "iron": [(90, 0, 155, 72), (180, 225, 256, 256)],     # 196..256) by colour: pale bone, warm hide
        "rock": [(0, 0, 90, 65), (0, 72, 150, 125), (0, 185, 95, 256)],
    }, {"wood": (1.9, 0.08), "all": True,               # a step lighter, new timber too (Max: a dark smudge):
        "ramps": {"wood": [(0, (.02, .019, .019)), (.5, (.11, .10, .097)), (.85, (.25, .235, .225)),
                           (1, (.37, .35, .335))]}}),    # weathered grey timber, still no brown
}
# EA's spider pit plates (the SPI PIT mesh on WBSpiPit, not the building's body): recoloured by
# `sagekit sheets goblins`, the riveted plates silver iron like the mine's collar, the grey rock
# rock, the red glow crimson by colour. The damaged and snow states share the layout.
_SPIPIT = (512, {
    "iron": [(0, 348, 145, 512)],
    "rock": [(0, 190, 145, 348), (145, 145, 512, 240), (145, 240, 225, 512), (475, 240, 512, 512)],
}, {"iron": (0.95, -0.12)})                             # EA's bright copper: gritty silver, not white
SHEETS.update({"wbspipit.tga": _SPIPIT, "wbspipit_d1.tga": _SPIPIT, "wbspipit_snow.tga": _SPIPIT})


def sheet_atlas(name):
    """The Atlas of one of the production sheets (materials in its own pixels), or None for a
    sheet without a table (WBFortress and the rest keep their own paths)."""
    entry = SHEETS.get(name.lower().replace(".dds", ".tga"))
    if entry is None:
        return None
    size, materials, tones = (entry + (None,))[:3]
    a = Atlas()
    a.texture, a.size, a.materials, a.tones = name, size, materials, tones
    a.ground_sat = GoblinAtlas.ground_sat
    return a
