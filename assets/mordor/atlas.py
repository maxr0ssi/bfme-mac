"""MBFortress (1024): Mordor's master sheet, and where its materials are.

EA painted Mordor as warm brown-grey plate and slab, rust-flecked: smooth cracked slabs with
rivets and slot windows (the keep's and the towers' big faces), rows of blades and spikes over
fluted plate (the lower half), blue-grey ribbed plate, blade finials, an eagle-headed statue,
cratered and craggy rock, and a rock strip with a red lava vein (top left) plus small lava crumbs.
Colour alone cannot tell the slabs from the plate (both brown-grey, low saturation), so:

    materials   {material: [(x0, y0, x1, y1)]} in the sheet's pixels (y down): stone (the
                citadel's walls and tower shafts, the fluted plate under the spike rows, the
                smooth slabs: basalt), rock (natural rock, crags, the walks), lava (the lava strip
                and crumbs: fire by colour inside, rock around it), wood (the roof pyres' sticks:
                fire by colour inside, charred timber around it), slit (the dark insides of the
                windows and slots: a palette with a "slit" ramp lights them), blade (where EA's
                pale steel is: the spike rows, the blade finials and hooked blade, the crest and
                the crown blades; a palette with a "steel" ramp paints their brightest metal with
                it). Everything else is metal, split by EA's luminance into iron and trim (the lit
                edges); fire outside the lava rects only where a texel is strongly saturated and
                bright (assets/mordor/paint.py).
    mask_hints  one "stone" hint over the whole upscale: the stock masks stay out of the way.

Regions for new faces (the kit, later): a slab (stoneA, stoneB), rock, a plain plate (iron),
ribbed plate (ribs), a spike row, and the painted materials, each repainted by a TagRamp of the
style (style.py): trim, cloth (the player's colour), ember, chain, soot, flame, witch (the few
Morgul-lit slits). The rects were
read by eye on the flat sheet; confirm them on the citadel's first bake."""
from sagekit.atlas import Atlas, Region

SLAB = (772, 702, 858, 845)                 # the keep's cracked slab face, above its two barred windows
                                            # (851..992): new faces tiled over them lit green (slit)
PLATE = (512, 645, 615, 720)                # a plain riveted plate
LAVA = (0, 95, 245, 200)                    # the lava vein through the rock strip


class MordorAtlas(Atlas):
    texture = 'MBFortress.tga'
    normal = 'MBFortress_NRM.tga'
    size = 1024
    density = 6.0                           # 1024 px over the same building sizes as the 512 sheets' 3.0
    ground_sat = (.6, .8)                   # no enamel band ground: the brown-grey is the plate itself
    regions = {                                                   # order matters: face tags index it
        'stoneA': Region(SLAB),
        'stoneB': Region((642, 230, 720, 500)),                    # the tall slab left of the window
        'rock': Region((55, 295, 178, 415)),                       # cratered volcanic rock
        'iron': Region(PLATE),
        'ribs': Region((560, 200, 620, 440)),                      # blue-grey fluted plate
        'spikes': Region((130, 760, 440, 1010)),                   # the blade row over fluted plate
        'cloth': Region(PLATE),
        'ember': Region(PLATE),
        'chain': Region(PLATE),
        'soot': Region((55, 295, 178, 415)),
        'trim': Region(PLATE),
        'flame': Region(PLATE),
        # the kit's (assets/mordor/shapes.py): charred timber, witch-lit slits and cold steel blade
        # edges, each on a rect of its material (painted by MordorRecolour like EA's own faces)
        'wood': Region((848, 70, 872, 250)),                       # the pyres' sticks
        'slit': Region((856, 326, 876, 366)),                      # a tower crown's window
        'steel': Region((330, 380, 445, 600)),                     # the hooked blade
        # the few slits kept in the Morgul witch-light (pass 7): a crown window's rect, painted green by
        # the style's TagRamp (its own material), while every "slit" is a dim ember
        'witch': Region((856, 326, 876, 366)),
    }
    painted = ('cloth', 'ember', 'chain', 'soot', 'trim', 'flame', 'witch')
    materials = {
        'stone': [(838, 290, 948, 640), (485, 180, 722, 520), (445, 640, 620, 1024), (245, 830, 445, 1024),
                  (592, 0, 722, 225), (722, 105, 837, 512), (592, 512, 722, 620), (620, 645, 737, 1024),
                  (770, 655, 992, 1024), (690, 580, 800, 830)],
        'rock': [(0, 0, 245, 290), (50, 290, 180, 420), (180, 360, 320, 420), (220, 420, 320, 575),
                 (772, 105, 837, 165)],
        'lava': [LAVA, (725, 0, 775, 35), (585, 90, 625, 140)],
        'wood': [(848, 70, 872, 250)],                          # the pyres' sticks (MBFDPYRES), glowing tips
        'slit': [(856, 326, 876, 366), (905, 326, 925, 366),    # the tower crowns' two windows
                 (450, 505, 500, 606),                          # the keep's slot panel
                 (594, 16, 610, 50), (614, 16, 630, 56), (637, 16, 654, 70), (660, 16, 677, 96),
                 (684, 16, 700, 156),                           # the arch's five slots
                 (779, 851, 806, 992), (821, 851, 848, 992),    # the keep's tall barred windows
                 (640, 678, 651, 700), (650, 714, 664, 762), (676, 708, 702, 798), (869, 733, 906, 764)],
        'blade': [(0, 530, 445, 830),                           # the spike rows (the walls' blades)
                  (296, 596, 445, 640),                         # the short spike strip under the hooked blade
                  (250, 0, 385, 365), (330, 380, 445, 600),     # the blade finials and the hooked blade
                  (845, 0, 1024, 255), (838, 250, 1024, 290)],  # the crest and the tower crowns' blades
    }
    mask_hints = {
        'stone': [(0, 0, 4 * 1024, 4 * 1024)],
    }
