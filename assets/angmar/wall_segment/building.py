"""Angmar wall segment (AngmarWallSegmentSmall, AngmarWallPosternGateSmall; model KBWallN): EA's
curtain kept whole - the flat faces, the walk's two channels, the middle rib with its curved horn
pair, the little brackets - and given the frozen wall every Angmar wall piece shares
(assets/angmar/shapes_walls.py):

- the battlement: six Carn Dum merlons along each face's top edge (stone teeth rising to an
  off-centre point, left and right in turn, their slopes rimed), at the walls' common pitch, a half
  pitch in from each end, none over EA's rib;
- a corbelled string course just under the walk on both faces, a rime crust along its front and
  icicles hanging under it;
- ice crystals growing up the foot in each bay, leaning along the face (a black stone shard
  among them).

No peak, no fire, no banners: segments repeat many times along a wall (the hubs, towers and gate
carry those). Everything stays inside EA's footprint (x -10.47..10.34, the rib's width; y +-19) and
nothing but the corbel's run reaches the ends, so a neighbour, a hub or the gate meets it and a
stretched segment still joins. Both faces alike.

EA's facts (KBWALL01 mesh coordinates = model, identity bone; measured 2026-10-01, ray casts): the
faces at x +8.29 / -8.39 from the ground (-0.06) to the top at z 53.1, the walk two channels at
z 47.6 (|x| 2..3.5); the rib |y| < 3 proud to |x| 10.2 to the top, its two curved horns at x +-3.5
to z 81.9; small brackets at y +-12, z 36 (|x| 9.9). ICEWALL (Ice Walls upgrade, 8 triangles,
EXFortressIce): a box shell 0.5 outside the faces (|x| 8.85, y -19.3..19.4) to z 33.04; the ice
crystals stand in the 1.5 between it and the footprint, their buried feet through it, as EA's own
rib is. The Ice Walls sheet KBFortressB_Ice gets our own copy (KBFortressD_Ice) by the same swap.
Lifecycle models in its Draw module: KBWallN_A, KBWallN_CUR, KBWallN_D1, KBWallN_D2, KBWallN_D3.
House colour: none (no cloth).
"""
from sagekit.building import Building

from ..style import AngmarStyle


class WallSegment(Building):
    style = AngmarStyle()
    source = "KBWallN"
    target = "KBWALL01"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressD.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallSegment"
    bake_hidden = ("ICEWALL",)        # the Ice Walls shell: shown in game with its upgrade, out of the bakes
    house_tags = ()                 # no banners: segments repeat many times along a wall
    views = {
        "rts": ((-0.1, -0.0, 40.9), 204, 50, -38, 50),
        "close": ((-0.1, -0.0, 40.9), 121, 24, -30, 45),
        "ingame": ((-0.1, -0.0, 40.9), 464, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_walls import run
        return kit.retag(run(kit, -19.0, 19.0, bays=(-11.2, 11.2)))

