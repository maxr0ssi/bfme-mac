"""Angmar den (AngmarDen), pass 2 "the den's mouth": EA's rock and pen kept whole; the cave the wargs
come out of (on the rock's +X side) becomes the mouth of a great frozen warg skull, 53.5 long: its
cranium rising out of the rock over the cave, a rimed crest and ice crystals on the crown, flaring
cheekbones, brow ridges over dark sockets with frost crystals in them, the snout out over the yard
with long ice fangs, a dark nose; the lower jaw dropped to the ground, its two halves apart so the
wargs walk out between them; the cold fire glows low in its throat ("coldflame"). A cluster of ice
and black stone shards stands outside the pen wall. Pass 1 set a smaller skull on the rock over the
pen: too small at RTS. Kit: assets/angmar/shapes_army.py.

EA's KBDen (objects AngmarDen; role barracks): body BASE, 2256 triangles, painted from KBDen.tga
+ KBDen_NRM.tga (DXT1).
In BASE mesh coordinates: x -64.92..63.64, y -67.13..69.70, z -1.48..80.15.
Other meshes (EA's, untouched): BROWNWOLF01 594 (the warg in the pen, (0, -38)); V1 323 (level 2: a
roof over the orc's platform, x -34..-8, y -24..2, z 47..64, and spikes on the +X side); OBJDEFAULT 308
(the orc on the platform, (-20, -22, 34)); DUMMYMAN 305 (the dummy he dangles, (-18, -37)); V2 298
(level 3: the watch tower on the rock at (-15, 35), z 52..126); STICK 12; ROPE 8.
Lifecycle models in its Draw module: KBDen_A, KBDen_D1, KBDen_D2, KBDen_D3.
House colour: KBHCDen.

EA's facts (measured 2026-10-01 from the model's own vertices): a great rock (to z 80) behind a round
pen (its centre (2, -30), its wall r 37..40 on the -Y side, to z 18, spikes on it to z 30); the rock's
front face over the pen rises from z 22 at y 2 to z 43 at y 12; the cave's glow at FX_CAVEGLOW
(20, 40, 16) (EA's AngDenGlow and AngDenMist); units come out at (2, 40) and rally at (100, 45).
"""
from sagekit.building import Building

from ..style import AngmarStyle


# the den's mouth: a great frozen warg skull over the cave's mouth on the rock's +X side, where the wargs
# come out (UnitCreatePoint (2, 40), rally (100, 45)): EA's cave runs in under an overhang of rock (its
# underside from z 6 at y 15 to z 32 at y 40..50, x 22..41), the yard before it open (x 31..45, y 20..47,
# z 0). The occiput sunk in the rock (its top z 64..79 there), the cranium on the overhang, the snout
# out over the yard (the nose at x 61, z 38: EA's footprint to 63.6), the jaw dropped to the ground with
# its two halves apart so the wargs walk out between them; clear of the level-2 spikes (V1: x 47..68
# at y -2..9 and y 61..69) and the level-3 tower on the rock (V2: (-15, 35), z 52 up)
SKULL = (8.0, 36.5, 44.0)
LOOK = (1.0, 0.03)
LENGTH, PITCH, GAPE, JAW = 53.5, 0.12, 0.66, 0.85
THROAT = (37.0, 37.0, 3.0)                # the cold fire low in its throat, under the palate

# ice clusters outside the pen wall (the pen's centre (2, -30), its wall at r 37..40 on the -Y side)
ICE = [(43.7, -49.4, 5.0, 16.0)]

# real fire (the game's particle systems on bones of KBDen_FX), from the design's log
FIRE_POINTS = [(18.1, -10.4, 19.3, 'coldflame')]        # in the skull's maw


class Den(Building):
    style = AngmarStyle()
    source = "KBDen"
    target = "BASE"
    sheet = "KBDen.tga"
    sheet_normal = "KBDen_NRM.tga"
    own_textures = {"KBDen.tga": "KBDeH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-0.6, 1.3, 39.3), 450, 50, -38, 50),
        "close": ((-0.6, 1.3, 39.3), 266, 24, -30, 45),
        "ingame": ((-0.6, 1.3, 39.3), 1024, 53, -62, 50),
        "skull": ((40.0, 37.0, 26.0), 150, 12, -60, 45),          # the skull close
        "cave": ((32.0, 34.0, 14.0), 170, 28, -15, 45),           # the cave mouth (+X)
    }

    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): none. 0.0 live (was 7.2).
    fire_points = []
    bake_hidden = ("V1", "V2")                  # level 1: the level-up meshes are drawn later
    facet_islands = 8                       # the unwrap overlapped: seams at EA's islands and 8-degree turns

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        return logged(kit, lambda k: k.retag(self._pieces(k)))

    @staticmethod
    def _pieces(kit):
        from .. import shapes_army as A
        A.floor(-1.48)                          # EA's ground (BASE z min)
        out = A.warg_skull(kit, SKULL, LOOK, LENGTH, pitch=PITCH, gape=GAPE, seed=1.0, jaw=JAW, chin=0.17,
                           throat=THROAT)
        for i, (x, y, r, h) in enumerate(ICE):
            out += kit.ice_cluster((x, y, 0.0), r, h, n=7, seed=30.0 + i, lean=0.55, thick=0.2, stone="rock",
                                   floor=-1.4)
        return out
