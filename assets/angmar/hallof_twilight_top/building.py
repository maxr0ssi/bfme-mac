"""Angmar Hall of Twilight, level 1's piece (TOP_1 of KBTemple: the shrine's roof and its crown of
three horns, z 43.8..78.7, shown at level 1, hidden at 2 and 3): the crown's horns frozen at the
tips (assets/angmar/hallof_twilight/horns.py: the walls group's `freeze`), so the Hall reads like
every other Angmar building at level 1. EA's roof and horns stay whole inside the ice.

Chained on the finished Hall (`base`): built after angmar/hallof_twilight, before
angmar/hallof_twilight_v1 (V1, level 2) and angmar/hallof_twilight_v2 (V2, level 3), whose build
ships the model for the whole chain. TOP_1's own extent is the tower top (x +-17.8, y -28.7..7.4),
well inside the Hall's footprint (BASE and V2: x -66.5..69, y -65.2..65.7); the front horn's casing
and crystals pass its y min by up to 3 (footprint_margin; the game's collision comes from the INI's
geometry, not the mesh). Per upgrade level: no cloth, no night lights, no fire.
"""
from sagekit.building import Building

from ..hallof_twilight.levels import HIDDEN, VIEWS
from ..style import AngmarStyle


class HallofTwilightTop(Building):
    style = AngmarStyle()
    source = "KBTemple"
    target = "TOP_1"
    base = "angmar/hallof_twilight"
    sheet = "KBTemple.tga"
    sheet_normal = "KBTemple_NRM.tga"
    own_textures = {"KBTemple.tga": "KBTemplT.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    house_tags = ()                 # shown per upgrade level; the house model is always drawn
    footprint_margin = 3.0
    bake_hidden = HIDDEN[1]
    views = VIEWS

    def design(self, kit):
        from ..hallof_twilight.horns import frozen
        return frozen(kit, "TOP_1")
