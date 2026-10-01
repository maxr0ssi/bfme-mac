"""Angmar kennel (AngmarKennelExpansion), pass 1 "the warg-tusk arch": EA's kennel kept whole; before
its gate two great warg tusks rise from rimed black stone footings either side of the wolves' way out
and curve in to cross over the gate, one a little in front of the other, an iron band riveted where
they cross; teeth of ice along their inner edges. No fire. Kit: assets/angmar/shapes_army.py.

EA's KBFKennel (objects AngmarKennelExpansion; role hall_expansion): body KBFKENNEL, 645
triangles, painted from KBFortressX.tga + KBFortressX_NRM.tga (DXT1).
In KBFKENNEL mesh coordinates: x -37.09..37.09, y -32.11..32.11, z -34.15..34.15 (the mesh hangs on its
bone at (-3.3, -1.0, 34.07): the ground is z -34.07). EA's body carries four loose vertices (dropped).
Other meshes (EA's, untouched): ICEWALL 28 (EXFortressIce.tga, EXIceRefraction01.tga).
Lifecycle models in its Draw module: KBFKennel_A, KBFKennel_D1, KBFKennel_D2, KBFKennel_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).

EA's facts (measured 2026-10-01 from the model's own vertices; heights above the ground): a half-round
kennel with its gate at +X: the portcullis at x 23..24, |y| < 8, to 21; a wolf pelt over it out to
x 33, to 45; claws at the front corners (x 34..37, |y| 15..19, to 17); horns at +-Y to 68; a wall
stub to -X (x -33..-3, |y| < 10, to 39). The wolves (AngmarDireWolf_Slaved) spawn inside and rally to
(70, 0). The Ice Walls shell (ICEWALL) stands round the gate at x 25..28.5.
"""
from sagekit.building import Building

from ..style import AngmarStyle


# KBFKENNEL hangs on its bone at (-3.3, -1.0, 34.07): in mesh coordinates the ground is z -34.07
Z0 = -34.07
# the warg-jaw arch before the gate (+X, the wolves' way out to the rally point (70, 0)): EA's portcullis at
# x 23..24 (|y| < 8, to 21 above the ground), the wolf pelt over it to x 33, z 45 above the ground, the
# front claws at x 34..37, |y| 15..19; the Ice Walls shell (ICEWALL) round the gate at x 25..28.5: the feet
# stand in front of it at x 32.4, |y| 11, the bones crossing over the pelt at ~56 above the ground
ARCH = (32.4, 0.0)
SPAN, HEIGHT = 22.0, 56.0


class Kennel(Building):
    style = AngmarStyle()
    source = "KBFKennel"
    target = "KBFKENNEL"
    sheet = "KBFortressX.tga"
    sheet_normal = "KBFortressX_NRM.tga"
    own_textures = {"KBFortressX.tga": "KBFortressR.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCKennel"
    facet_islands = 8                       # the unwrap overlapped: seams at EA's islands and 8-degree turns
    views = {
        "rts": ((-3.3, -1.0, 34.1), 263, 50, -38, 50),
        "close": ((-3.3, -1.0, 34.1), 155, 24, -30, 45),
        "ingame": ((-3.3, -1.0, 34.1), 598, 53, -62, 50),
        "gate": ((25.0, -1.0, 26.0), 130, 15, -20, 45),            # the jaw arch before the gate
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS (none here)
        from assets.men.stable.pieces import drop_loose
        drop_loose(self.target)                 # EA's four loose vertices (the checks allow none on the target)
        return logged(kit, lambda k: k.retag(self._pieces(k)))

    @staticmethod
    def _pieces(kit):
        from .. import shapes_army as A
        A.floor(Z0 - 0.08)                      # EA's ground (KBFKENNEL z min)
        return A.jaw_arch(kit, (ARCH[0], ARCH[1], Z0), (1, 0), SPAN, HEIGHT, r=2.0, teeth=7, seed=2.0, ice=False)
