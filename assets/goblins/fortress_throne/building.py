"""The Goblin throne (WildFortressCitadel, upgrade UPGRADE_FORTRESS_MONUMENT: the dragon's nest):
EA's rearing wyrm on its flared nest kept whole - sculpt, crest, wings, the forelegs gripping the
bowl, the niche the fire drake idles in - and made the citadel's centrepiece, the Goblins' chained
war idol in blood, iron and bone (palette E): great crimson horns and a spiked iron crown, bone
fangs and tusks with blood on them, a spiked iron collar with a skull on a chain at the throat,
bleached spikes down the crest, spurs on the wing tips, the wrists shackled and chained to the
nest, bone talons (dragon.py); an iron band round the nest's waist, great tusks rising from the
bowl's rim like a ribcage, fire bowls on brackets, a horned troll skull nailed over the front,
skull piles and bones round the foot (nest.py). No banner: the citadel carries three.

EA's facts (sagekit measure; work/measure.json): WBFGThrone, body WBFGTHRONE, 854 triangles on
WBFortress.tga (own copy WBFortresC.tga), not skinned; x -35.09..40.30, |y| <= 25.15, z 0..173.5;
EA's bones B_DRAKE (12.83, 0, 74.47: the fire drake's perch, WUFireDrk_SKN attaches there),
FXMOUTH (16, 0, 146.4), FXEYE01/02 (20.3, +-7, 154.4) and the mesh P1 (the bowl, z 74.8) stay
clear. Lifecycle: WBFGThrone_A (construction, animated), _D2, _D3 (collapsing, animated).
House colour: none of its own (WBHCFGThrone would carry an add-on banner; there is none).
"""
from sagekit.building import Building

from ..style import GoblinStyle

# The game's fire (sagekit/fire.py): the coals of the two fire bowls on iron brackets out of the
# nest's flare (nest.py: BRAZIER, the bowl at (0.8, +-20.9), kit.brazier h 2.6 from z 55.6). EA's
# own fire is the drake's glow on B_DRAKE (12.8, 0, 74.5) and the head's FXMOUTH/FXEYE: clear.
FIRE_POINTS = [(0.8, 20.9, 58.5, 'brazier'), (0.8, -20.9, 58.5, 'brazier')]


class FortressThrone(Building):
    style = GoblinStyle()
    source = "WBFGThrone"
    target = "WBFGTHRONE"
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): none (the citadel's gate braziers burn). 0.0 live (was 11.9).
    fire_points = []
    sheet = "WBFortress.tga"
    sheet_normal = "WBFortress_NRM.tga"
    own_textures = {"WBFortress.tga": "WBFortresC.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                      # EA's own layout overlaps (1.42%), as on the citadel
    parts = ("ModuleTag_IvoryTowerDraw",)
    views = {
        "rts": ((2.6, 0.0, 86.8), 431, 50, -38, 50),
        "close": ((2.6, 0.0, 92.0), 330, 18, -38, 45),
        "head": ((6.0, 0.0, 150.0), 105, 14, -42, 45),
        "nest": ((6.0, 0.0, 60.0), 150, 28, -30, 45),
        "ingame": ((2.6, 0.0, 86.8), 979, 53, -62, 50),
    }

    def design(self, kit):
        from . import dragon, nest
        return dragon.build(kit) + nest.build(kit)

    def decals(self):
        from ..paint import goblin_layers
        from . import dragon, nest
        return [goblin_layers()["Gore"](dragon.gore_anchors() + nest.gore_anchors())]

    def emphasis(self, c, n):
        if c.z > 125:
            return 1.3                        # the head, horns, crown and collar: what reads from the camera
        return 1.0
