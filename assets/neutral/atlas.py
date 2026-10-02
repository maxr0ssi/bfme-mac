"""NBInn (512): the neutral master sheet, and where its materials are.

EA painted the Inn as a wilderland timber hall: olive-grey weatherboards (top left), a pale and a
dark log beam under them, a pale squared post, fieldstone (top right), the inn's own painted
signboard (a wolf's head on a plank), a small framed window, blue-grey board walls with leaded
and pointed windows (bottom left), dark planking between two posts, wooden shingles (bottom
right), a mossy log, a steel cylinder and an amber lamp pane. Every neutral building's new faces
are mapped here (the Outpost, signal fire and lairs paint their bodies from sheets of their own).

Regions for new faces: the materials above, and the painted ones each repainted by a TagRamp of
the style (style.py): cloth (faded madder), brass, iron, glow (lamp light). The capture dress of
each faction (assets/neutral/dress.py) has tags of its own, `<dress>_<role>`: the faction's
material on a texture of the same kind (its stone on the fieldstone, its metal on the steel
cylinder), repainted in that faction's own ramp; its cloth goes to the house-colour model."""
from sagekit.atlas import Atlas, Region

BOARDS = (8, 8, 380, 198)               # olive-grey weatherboards
STONE = (420, 4, 510, 108)              # fieldstone
PLANKS = (276, 276, 358, 364)           # dark planking between the posts
METAL = (402, 260, 446, 306)            # the steel cylinder
PALE = (393, 4, 415, 148)               # the pale squared post
GLOW = (454, 266, 465, 304)             # the amber lamp pane

# the capture dress: one prefix per faction (sagekit/capture.py DRESS) and the roles a faction's
# kit tags fall into (dress.py ROLE), each on a region of the same kind of texture
DRESS_PREFIXES = ("dw", "el", "mn", "is", "mo", "gb", "an")
DRESS_ROLES = {"stone": Region(STONE), "gilt": Region(METAL, Region.STRETCH), "metal": Region(METAL, Region.STRETCH),
               "wood": Region(PLANKS), "bone": Region(PALE, Region.STRETCH), "glow": Region(GLOW, Region.STRETCH),
               "cloth": Region(BOARDS)}


# the lairs' story pieces (after the dress's tags, so theirs keep their indices): the kits' rock,
# hoard gold, bone, embers and web, each repainted by its TagRamp (style.py)
LAIR = {"rock": Region(STONE), "gold": Region(METAL, Region.STRETCH), "bone": Region(PALE, Region.STRETCH),
        "ember": Region(GLOW, Region.STRETCH), "web": Region(PALE, Region.STRETCH)}


class NeutralAtlas(Atlas):
    texture = "NBInn.tga"
    normal = "NBInn_NRM.tga"
    size = 512
    density = 3.0
    ground_sat = (.6, .8)               # no enamel band ground on this sheet: its blue-grey boards are wood
    regions = dict({                                              # order matters: face tags index it
        "stoneA": Region(STONE),                                  # the kit's default faces: fieldstone
        "stoneB": Region(STONE),
        "top": Region(STONE),
        "boards": Region(BOARDS),
        "beam": Region((4, 215, 386, 237), Region.BAND, su=3.0),  # the pale log beam
        "log": Region((4, 247, 392, 269), Region.BAND, su=3.0),   # the dark log beam
        "post": Region(PALE, Region.STRETCH),
        "planks": Region(PLANKS),
        "slate": Region((56, 282, 82, 504)),                      # blue-grey boards between the windows
        "shingle": Region((234, 380, 470, 508)),
        "moss": Region((404, 240, 470, 250), Region.BAND, su=3.0),   # the mossy log
        "sign": Region((420, 118, 472, 150), Region.STRETCH),     # EA's painted signboard (a wolf's head)
        "window": Region((394, 162, 448, 206), Region.STRETCH),   # a small framed window
        "lattice": Region((2, 296, 44, 500), Region.STRETCH),     # the leaded window
        "metal": Region(METAL, Region.STRETCH),
        "cloth": Region(PLANKS),                                  # painted: faded madder (style.py)
        "brass": Region(METAL, Region.STRETCH),                   # painted: lamp frames, sign irons
        "iron": Region(METAL, Region.STRETCH),                    # painted: straps, hinges, brackets
        "glow": Region(GLOW, Region.STRETCH),                     # painted: lamp light
    }, **{"%s_%s" % (p, role): r for p in DRESS_PREFIXES for role, r in DRESS_ROLES.items()}, **LAIR)
    painted = ("cloth", "brass", "iron", "glow") + tuple(
        "%s_%s" % (p, role) for p in DRESS_PREFIXES for role in DRESS_ROLES) + tuple(LAIR)
    mask_hints = {
        "stone": [(0, 0, 2048, 2048)],  # no stock metal or wood from colour alone (EA's colours are kept)
    }
