"""Angmar fortress spikes (AngmarFortressSpikes), pass 1: EA's ring of iron spikes round the citadel's
feet kept whole and frozen, as the citadel's crown is frozen: every tall spike cased in ice from
half its height to its point under a ragged frost line, rime on the last stretch, crystals growing
out of the casing (the bold mass: a moat of frozen points; EA's upgrade slows the enemy round the
citadel with a chill aura, SpikeMoatModifier).

EA's KBFSpike (objects AngmarFortressSpikes; role fortress_addon): body KBFSPIKES, 1326
triangles, painted from KBFortressX.tga + KBFortressX_NRM.tga (DXT1).
In KBFSPIKES mesh coordinates: x -93.99..100.88, y -91.19..91.19, z 0.58..46.23.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/fortress_spikes` -> work/measure.json.

EA's facts (measured 2026-10-01, the model's loose parts):
- An object of its own (ObjectCreationUpgrade on Upgrade_AngmarFortressSpikes spawns it at the
  citadel, slaved to it), drawn round the citadel in its coordinates: 26 clumps at r 80..108 all
  round but the gate's ramp (|deg| < 19), each a stone foot (z 0.6..4.9, 12..17 across) with one to
  three curved spikes on it: 7 to z 39.8, 16 to z 33.5 (6 of them with a thin point standing on
  them to z 46.2), 12 pairs of halves to z 22.7..23.4, small flat fins round them.
- The citadel's ice clusters (fortress/walls.py: r 80 at 24, 66, 114, .. degrees; r 99 on the
  diagonals) and frost fissures (r 77..79) stand among EA's clumps at the wall feet: EA's spikes
  cross them (1009 faces), as they cross EA's own plinth.
- The tall spikes' sections are read from EA's mesh at design time (shapes_addons.frozen_spikes),
  so each casing follows its own spike.
"""
from sagekit.building import Building

from ..style import AngmarStyle

# Real fire: none (the moat's chill is EA's aura; the citadel's cold fire burns in its crown)
FIRE_POINTS = []


def frost(kit):
    from ..shapes_addons import frozen_spikes
    out, frozen = frozen_spikes(kit, "KBFSPIKES", minz=30.0, frost=0.55, seed=1.0)
    print("FROZEN_SPIKES", len(frozen))
    return out


class FortressSpikes(Building):
    style = AngmarStyle()
    fire_points = FIRE_POINTS
    source = "KBFSpike"
    target = "KBFSPIKES"
    sheet = "KBFortressX.tga"
    sheet_normal = "KBFortressX_NRM.tga"
    own_textures = {"KBFortressX.tga": "KBFortressQ.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the unwrap overlapped (0.12%): seams at EA's islands and 8-degree turns
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressSpikes"
    views = {
        "rts": ((3.4, -0.0, 23.4), 596, 50, -38, 50),
        "close": ((10.0, -85.0, 18.0), 120, 30, -60, 45),         # the clumps at the -Y wall foot
        "ingame": ((3.4, -0.0, 23.4), 1354, 53, -62, 50),
    }

    def design(self, kit):
        return kit.retag(frost(kit))
