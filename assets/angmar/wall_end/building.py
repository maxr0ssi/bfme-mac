"""Angmar wall end (AngmarWallCliffCap; model Dwarf): EA's cliff cap kept whole - two segments'
worth of curtain (y -57..19) with its ribs and curved horn pairs at y 0 and -38, its foot carried
down into the cliff - and given the frozen wall of every Angmar wall piece (shapes_walls.run):
Carn Dum merlons along both top edges at the walls' common pitch (the joint at y 19 keeps a
segment's beat), a corbel with icicles just under the walk between the ribs, ice drifts up the
foot in the four bays. No peak, no fire, no banners (as the segments).

EA's facts (DWARF mesh coordinates = model, identity bone; measured 2026-10-01, ray casts): the
segment's profile 8.5 lower - faces at x +8.29 / -8.39, the top at z 44.6, the walk's channels
at 39.1 - from the cliff foot (z -43.71) up; ribs |y - rib| < 3 at y 0 and -38 proud to |x| 10.3,
their horn pairs to z 73.49; buttresses at y -55, -19 and 18 to |x| 10.1; footprint x -10.46..10.35,
y -57..19 (y 19 meets a segment). ICEWALL (Ice Walls, 8 triangles): a box shell at |x| 8.84 from
z -43.9 to 33.04 (y -57.5..19.4): the ice drifts stand between it and the footprint, their feet
through it, as EA's ribs are. The Ice Walls sheet gets our own copy (KBFortressK_Ice).
Lifecycle models in its Draw module: Dwarf_A, Dwarf_D1, Dwarf_D2, Dwarf_D3. House colour: none.
"""
from sagekit.building import Building

from ..style import AngmarStyle


class WallEnd(Building):
    style = AngmarStyle()
    source = "Dwarf"
    target = "DWARF"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressK.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallEnd"
    bake_hidden = ("ICEWALL",)        # the Ice Walls shell: shown in game with its upgrade, out of the bakes
    house_tags = ()                 # no banners: as the segments
    views = {
        "rts": ((-0.1, -19.0, 14.9), 311, 50, -38, 50),
        "close": ((-0.1, -19.0, 14.9), 184, 24, -30, 45),
        "ingame": ((-0.1, -19.0, 14.9), 706, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_walls import run
        return kit.retag(run(kit, -57.0, 19.0, top=44.6, ribs=(0.0, -38.0), ground=-0.06,
                             bays=(-48.0, -28.5, -9.5, 10.5)))
