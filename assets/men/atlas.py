"""GBFortress1 (512): where the new faces sample EA's painted Gondor stone and motifs.

Plain ashlar, the cornice and string-course bands, EA's corbel arcade (the little arches under the
wall walks, reused on the lantern drums), the dome's slate, the square slate tiles (spirelets),
the slit and arched windows. The painted regions (steel, gilt, enamel, iron, relief, cloth) take
their grain from plain stone and are repainted by the style's TagRamps (style.py)."""
from sagekit.atlas import Atlas, Region

PLAIN = (338, 350, 414, 440)


class MenAtlas(Atlas):
    texture = 'GBFortress1.tga'
    normal = 'GBFortress1_NRM.tga'
    size = 512
    density = 3.0
    ground_sat = (.25, .40)
    regions = {                                                   # order matters: face tags index it
        'stoneA': Region(PLAIN),
        'stoneB': Region((20, 372, 196, 450)),
        'top': Region((6, 283, 208, 296), Region.BAND),
        'course': Region((6, 301, 208, 314), Region.BAND),
        'trim': Region(PLAIN),
        'gilt': Region(PLAIN),
        'enamel': Region(PLAIN),
        'cloth': Region(PLAIN),
        'relief': Region(PLAIN),
        'roof': Region((357, 29, 398, 65)),
        'iron': Region(PLAIN),
        'arcade': Region((22, 322, 215, 357), Region.BAND, su=5.5),  # EA's corbel arcade, an arch every 3 units
        'slate': Region((424, 4, 480, 33)),                           # square slate tiles
        'slit': Region((432, 97, 445, 157), Region.STRETCH),          # a tall slit window
        'window': Region((435, 240, 482, 310), Region.STRETCH),       # round-arched window between columns
    }
    painted = ('trim', 'gilt', 'enamel', 'cloth', 'relief', 'iron')
    mask_hints = {
        'stone': [(4 * 338, 4 * 350, 4 * 425, 4 * 477), (4 * 20, 4 * 372, 4 * 196, 4 * 450)],
        'tiles': [(4 * 350, 4 * 12, 4 * 406, 4 * 74), (4 * 422, 4 * 2, 4 * 482, 4 * 35)],
        'grille': [(4 * 284, 4 * 206, 4 * 317, 4 * 286), (4 * 370, 4 * 117, 4 * 401, 4 * 148)],
    }
