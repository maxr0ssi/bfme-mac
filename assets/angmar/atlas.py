"""KBFortress (1024): Angmar's master sheet for the citadel, and where its materials are.

EA painted Carn Dum as a northern hold of grey stone and timber: cool blue-grey dressed blocks
with iron-framed arrow slits and rust running from the joints (the lower half), a smooth slab
plinth along the bottom, dark timber with white frost in its grain (the top left: gables and
the great arched window), warm plank walls, scale shingles with an oily violet-green sheen (top
right), a reddish beam with iron brackets, small plank brackets in the wall. Two more master
sheets carry the rest of the faction (atlas_sheets.py): KBFortressB (walls, towers, gate, the
sanctum) and KBFortressX (the House of Lamentation, the spikes, the kennel).

    materials   {material: [(x0, y0, x1, y1)]} in the sheet's pixels (y down), first listed wins
                (AngmarRecolour, paint.py): slit (the dark insides of the arrow slits: a palette's
                "slit" ramp lights them, darkest texel brightest; lighter texels fall through),
                iron (the beam's brackets), planks (warm boards, the beam, the wall brackets),
                roof (the scale shingles), timber (the dark frost-grained wood: its white frost
                lines are the top of the timber ramp, rime), stone (the rest: blocks and plinth).
                Rust is found by colour on stone and iron (saturated orange), not by rect.
    mask_hints  one "stone" hint over the whole upscale: the stock masks stay out of the way.

Regions for new faces (the kit, assets/angmar/shapes*.py): stone (two block fields), slab (the
plinth), timber, planks, roof, slit, rock (the plinth's slab, stretched: the shards of black
stone), and the painted materials, each repainted by a TagRamp of the style (style.py): iron (the
dark grained timber stretched over each face: the crown's tines, forged iron), steel (the white
frost line: the tines' edges), trim, cloth (the player's colour), flame and ember (cold glow),
ice and rime (the slab stretched: crystal, never masonry), chain, soot. The rects were read by eye
on the flat sheet (2026-10-01) and checked on the citadel's first builds (a tiled bracket plate on
the tines read as rows of rivets: now stretched timber)."""
from sagekit.atlas import Atlas, Region

BLOCKS = (420, 852, 760, 940)               # plain blocks under the lower slits
BEAM = (781, 450, 866, 740)                 # the reddish beam with iron brackets
GRAIN = (428, 40, 500, 420)                 # dark frost-grained timber beside the frost line
FROST = (396, 40, 414, 420)                 # the white frost line down it
SLAB = (180, 958, 410, 1016)                # the plinth's smooth cracked slab, between its rust runs
SLITS = [(96, 598, 118, 692), (386, 598, 408, 664), (742, 598, 764, 664),          # the upper slits
         (300, 768, 324, 848), (394, 768, 418, 848), (480, 768, 504, 848), (575, 768, 599, 848),
         (655, 768, 679, 848), (755, 768, 779, 848),                                   # the lower slits
         (888, 512, 900, 550), (932, 512, 944, 550)]                                   # the tower's pair


class AngmarAtlas(Atlas):
    texture = 'KBFortress.tga'
    normal = 'KBFortress_NRM.tga'
    size = 1024
    density = 6.0                           # 1024 px over the same building sizes as the 512 sheets' 3.0
    ground_sat = (.6, .8)                   # no enamel band ground: the blue-grey is the stone itself
    regions = {                                                   # order matters: face tags index it
        'stoneA': Region(BLOCKS),
        'stoneB': Region((600, 470, 780, 600)),                    # the upper wall's blocks
        'slab': Region((0, 950, 1024, 1024)),                      # the plinth
        'timber': Region((350, 0, 505, 440)),                      # frost-grained dark boards
        'planks': Region((520, 150, 815, 340)),
        'roof': Region((830, 0, 1020, 245)),                       # the scale shingles
        'iron': Region(GRAIN, Region.STRETCH),                     # dark grained timber, one strip per face: forged
                                                                   # iron by its TagRamp (a tiled bracket read as tiles)
        'slit': Region(SLITS[3]),
        'cloth': Region(BLOCKS),
        'trim': Region((829, 485, 866, 520)),
        'flame': Region(SLAB, Region.STRETCH),
        'ice': Region(SLAB, Region.STRETCH),               # smooth cracked slab: crystal, never masonry
        'chain': Region((829, 485, 866, 520)),
        # the kit's (assets/angmar/shapes*.py, 2026-10-01): the steel edges of the crown's tines and
        # spikes, rime (white frost crusts), cold glow in fissures (ember), raw stone (rock: the plinth's
        # slab), sooted iron; each painted by its TagRamp (style.py) but rock (recoloured as stone). The
        # new faces' iron, steel, ice, glow and rock are stretched, one motif per face (first build:
        # tiled brackets and blocks read as tiles on the crown's tines and the shards)
        'steel': Region(FROST, Region.STRETCH),                    # the white frost line down the dark timber
        'rime': Region(SLAB, Region.STRETCH),
        'ember': Region(SLAB, Region.STRETCH),
        'rock': Region(SLAB, Region.STRETCH),
        'soot': Region((829, 485, 866, 520)),
    }
    painted = ('cloth', 'trim', 'flame', 'ice', 'chain', 'steel', 'rime', 'ember', 'soot')
    materials = {
        'slit': SLITS,
        'iron': [(829, 485, 866, 520), (829, 640, 866, 676)],                # the beam's brackets
        'planks': [(512, 145, 822, 345), (822, 250, 1024, 450), BEAM,
                   (304, 610, 334, 637), (464, 610, 496, 637), (667, 610, 698, 637),    # wall brackets
                   (402, 710, 433, 741), (464, 710, 496, 741), (579, 710, 611, 741), (641, 710, 672, 741)],
        'roof': [(512, 0, 822, 145), (822, 0, 1024, 250)],
        'timber': [(0, 0, 512, 450), (512, 345, 822, 450), (0, 450, 75, 592), (960, 450, 1024, 700)],
        'stone': [(0, 0, 1024, 1024)],
    }
    mask_hints = {
        'stone': [(0, 0, 4 * 1024, 4 * 1024)],
    }
