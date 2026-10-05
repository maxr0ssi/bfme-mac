"""Mordor mumakil pen (MordorMumakilPen), pass 2: EA's pit, decks, rails and berms kept whole, and the
door's measured swing (mumakil_pen_02) kept clear. Over the open end a great arch of crossed ivory
tusks on stepped basalt plinths, a fire bowl at its crown, the Harad sun under it and chains
hanging; ivory tusk claws round fire bowls on the berms; spiked howdahs with canopies of the
player's colour on the decks; two sun-and-serpent banners on the -Y rail; lava along the -Y berm's
foot (pen.py).

EA's MBMumkpen (objects MordorMumakilPen; role stable): body MUMAKILPEN, 1472 triangles, painted from
MBMumkPen.tga + MBMumkPen_NRM.tga (DXT1). In MUMAKILPEN mesh coordinates (identity bone): x
-58.81..50.62, y -46.24..46.97, z -3.02..66.62. Other meshes (EA's, untouched): V1 506
(MBMumkPen_V1.tga), BANNERS 384 (Haradrim_Banr.tga), N_WINDOW 120 and N_FIRE 24 (the night lights),
V2 99. The door is a model of its own in a Draw of its own (ModuleTag_02: MBMumkpenDSCL shut,
MBMumkpenDOP open, MBMumkpen_DROCD its animation): a lid over the pit hinged at x -41.5, z 50.3.
Lifecycle models in its Draw module: MBMUMKPEN_D1, MBMumkPen_D2, MBMumkPen_D3, MBMumkpen_A. House
colour: MBHCMumkPen (HC_BANNER01, its pole at (29.8, 22.3), to z 74.9). EA's body measured:
`python3 -m sagekit measure mordor/mumakil_pen`.
"""
from sagekit.building import Building

from ..style import MordorStyle


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in the target's
# coordinates, collected from the design (kit.fire records them while the kit's `fire_log` is a list:
# design() prints FIRE_POINTS into work/logs/*geometry.log); run again after moving a fire.
FIRE_POINTS = [
    (7.0, -38.6, 34.1, 'furnace'), (7.0, -38.6, 36.8, 'smoke'), (7.0, 38.6, 34.1, 'furnace'),
    (7.0, 38.6, 36.8, 'smoke'), (45.8, -33.0, 12.3, 'furnace'), (45.8, -33.0, 15.0, 'smoke'),
    (45.8, 33.0, 12.3, 'furnace'), (45.8, 33.0, 15.0, 'smoke'), (45.8, 0.0, 78.5, 'furnace'),
    (45.8, 0.0, 81.0, 'plume'), (-26.0, -44.8, 0.4, 'embers'), (12.0, -44.8, 0.4, 'embers')
]
# The fire budget (2026-10-04, docs/ART.md "Fire budget": at most 60 live particles): every bowl keeps
# its flame, the crown's its sparks and plume; two of the four side bowls (one per side) keep their
# smoke. 59.5 live (was 253).
FIRE_POINTS = [
    (7.0, -38.6, 34.1, 'flame'), (7.0, -38.6, 36.8, 'smoke'), (7.0, 38.6, 34.1, 'flame'),
    (45.8, -33.0, 12.3, 'flame'), (45.8, 33.0, 12.3, 'flame'), (45.8, 33.0, 15.0, 'smoke'),
    (45.8, 0.0, 78.5, 'furnace'), (45.8, 0.0, 81.0, 'plume'), (-26.0, -44.8, 0.4, 'embers'),
    (12.0, -44.8, 0.4, 'embers')
]


class MumakilPen(Building):
    style = MordorStyle()
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): the top's fire a brazier. 6.0 live (was 59.5).
    fire_points = [(45.8, 0.0, 78.5, 'brazier')]
    source = "MBMumkpen"
    target = "MUMAKILPEN"
    sheet = "MBMumkPen.tga"
    sheet_normal = "MBMumkPen_NRM.tga"
    # the pieces the game shows only from level 2 (V1) and 3 (V2, BANNERS; EA's SubObjectsUpgrades): kept in
    # game, left out of the bakes and the renders, so they show the pen as it is built (level 1)
    bake_hidden = ("V1", "V2", "BANNERS")
    max_z_growth = 0.25                 # the tusk arch's crown fire over the open end to z 86 (+23 %)
    own_textures = {"MBMumkPen.tga": "MBMumkPeH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    lifecycle = dict.fromkeys(("MBMumkpen_DRA", "MBMumkpen_DROCD", "MBMumkpenDOP", "MBMumkpenDSCL"), {
        "skip": "the pen's gate: a separate piece in a Draw of its own (ModuleTag_02) that EA opens, closes and "
                "drops; never on the healthy body"})
    lifecycle["MBMumkPen_D3"] = {"skip": "the collapse cuts our stockade and tusk arch open: 17.6-26.3% past EA's "
                                         "(filled or cut), over the checks' 10%; EA's collapse stays until the "
                                         "cut caps what it opens"}
    views = {
        "rts": ((-4.1, 0.4, 31.8), 351, 50, -38, 50),
        "close": ((-4.1, 0.4, 31.8), 208, 24, -30, 45),
        "ingame": ((-4.1, 0.4, 31.8), 799, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS

        from . import pen
        return logged(kit, lambda k: k.retag(pen.build(k)))
