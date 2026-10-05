"""Angmar barracks (AngmarBarracks), pass 2 "the thrall-master's gantry": EA's hall kept whole; across
its front, over the way out, stands the thrall-master's gantry, as tall as the eaves: at each end a
rimed stone plinth and an A-frame of two heavy iron-banded timber legs, a cross-tie and a knee brace;
over them one heavy beam, iron-strapped, rimed along its top and hung with icicles; from iron arms
reaching out of its front, on chains, two great iron cages, each with a captive frozen inside a
column of ice crystals. Cold-fire braziers (claws of iron prongs out of black stone shards) stand on
stone plinths before the A-frames' feet ("coldflame"). EA's six roof spikes are frozen from about
60 % of their height to the point (the family's frozen tips: assets/angmar/shapes_walls.py freeze).
Pass 1 hung the gallows along the +X side: too small against the hall at RTS.
Kit: assets/angmar/shapes_army.py.

EA's KBHall (objects AngmarBarracks; role barracks): body BASE, 918 triangles, painted from
KBHall.tga + KBHall_Normal.tga (DXT5, cut-out alpha: our texture is DXT5).
In BASE mesh coordinates: x -42.75..42.75, y -56.30..48.72, z -0.00..92.69.
Other meshes (EA's, untouched): V2 642 (the level-3 tower at the back, y 27..53, to z 123); V1 488 (the
level-2 horns: the corners (+-42, -37), (+-42, 48), the sides (+-52, 6), the front (-27, -51), (19, -50));
DARKDUNEDAIN 444 (KUDarkDune.tga); N_WINDOW 16 (GBNightWIndows.tga); DOOR_LEFT, DOOR_RIGHT 11 each.
Lifecycle models in its Draw module: KBHall_A, KBHall_D1, KBHall_D2, KBHall_D3.
House colour: KBHCHall. The doors are a Draw of their own (KBHallDoors_CL).

EA's facts (measured 2026-10-01 from the model's own vertices): a long hall along Y, its front (the
porch and door) at -Y; units come out at (0, -9) and rally at (0, -75). The side walls at x +-27 to
z 30, the roof sloping from the ridge (z 71) to the eaves; three buttress-spikes a side (at x 34 they
stand y -22..-16, 4..10, 29..35; to z 77..87); the plinth's steps at z 7 (x +-37) and z 4 (to x
+-42.75), from y -33 to 46. The six roof spikes (loose parts, 34 triangles each) rise from z 40.8 at
x +-16..33 to their points at (+-17.3, -19.6, 83.3), (+-16.3, 7.6, 92.7), (+-17.3, 31.4, 83.3). EA's
normal map KBHall_Normal exists only as a DDS (kbhall_normal.dds; kbhall_nrm.tga is another file):
the extract step reads it through `normal_member` (sagekit/formats/textures.py).
"""
from sagekit.building import Building

from ..style import AngmarStyle


# the thrall-master's gantry across the front, over the way out (units come out at (0, -9), rally at
# (0, -75)): the A-frames at x +-30 on the ground before the plinth (the porch spans |x| < 13 to y -43),
# between the level-2 horns (V1: the front pair at x +-16..23, y -55..-48, to z 28.5; the corners at
# x +-38.5..45.6, y -41..-34); the beams' underside at z 33 (the eaves at z 30, the porch roof to z 36
# at y -38), clear over the front horns' points; two great cages [(along the beam, chain drop, cage
# height)] hung off iron arms out of the beam's front, over the way out; cold braziers on plinths before the A-frames' feet
GANTRY = (0.0, -44.0, 0.0)
SPAN, HEIGHT = 60.0, 33.0
CAGES = [(-8.5, 2.0, 18.0), (8.5, 4.5, 15.5)]
BRAZIERS = [(-31.0, 8.8), (31.0, 8.8)]        # (along the beam, out from it toward -Y)
# EA's six roof spikes (the buttresses' horns), frozen from about 60 % of their height to the point:
# (centres up the spike, measured from the model's own sections, radii of the casing)
SPIKES = [
    [(-25.4, -18.8, 59.9), (-23.7, -18.8, 66.3), (-21.7, -18.8, 72.7), (-19.3, -18.8, 78.2), (-17.3, -19.6, 83.3)],
    [(-25.1, 6.6, 64.1), (-23.4, 6.9, 71.9), (-21.4, 6.6, 79.7), (-18.7, 6.8, 86.5), (-16.3, 7.6, 92.7)],
    [(-25.4, 32.1, 59.9), (-23.7, 32.1, 66.3), (-21.7, 32.1, 72.7), (-19.3, 32.1, 78.2), (-17.3, 31.4, 83.3)],
]
SPIKES += [[(-x, y, z) for x, y, z in path] for path in SPIKES]
SPIKE_R = {83.3: [2.9, 2.4, 1.8, 1.2, 0.5], 92.7: [3.1, 2.5, 1.9, 1.3, 0.5]}

# real fire (the game's particle systems on bones of KBHall_FX), from the design's log
FIRE_POINTS = [(-31.0, -52.8, 8.9, 'coldflame'), (31.0, -52.8, 8.9, 'coldflame')]   # the braziers


class Barracks(Building):
    style = AngmarStyle()
    source = "KBHall"
    target = "BASE"
    sheet = "KBHall.tga"
    sheet_normal = "KBHall_Normal.tga"
    own_textures = {"KBHall.tga": "KBHalH.tga",      # free in EA's files and every recipe (sagekit/names.py)
                    "KBHall_Normal.tga": "KBHalH_Normal.tga"}    # EA named its normal map off the _NRM pattern
    views = {
        "rts": ((0.0, -3.8, 46.9), 361, 50, -38, 50),
        "close": ((0.0, -3.8, 46.9), 213, 24, -30, 45),
        "ingame": ((0.0, -3.8, 46.9), 821, 53, -62, 50),
    }

    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): the two braziers a small cold flame each. 6.0 live (was 14.4).
    fire_points = [(-31.0, -52.8, 8.9, 'coldtorch'), (31.0, -52.8, 8.9, 'coldtorch')]
    bake_hidden = ("V1", "V2", "N_WINDOW")      # level 1: the level-up meshes are drawn later

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        return logged(kit, lambda k: k.retag(self._pieces(k)))

    @staticmethod
    def _pieces(kit):
        from .. import shapes_army as A
        from ..shapes_walls import freeze
        A.floor(0.0)                            # EA's ground (BASE z min)
        out = A.thrall_gantry(kit, GANTRY, (1, 0), SPAN, HEIGHT, CAGES, post=4.6, splay=5.0, braziers=BRAZIERS,
                                reach=5.0)
        for i, path in enumerate(SPIKES):
            out += freeze(kit, path, SPIKE_R[path[-1][2]], seed=1.0 + i * 1.3, crystals=3)
        return out
