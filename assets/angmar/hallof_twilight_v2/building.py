"""Angmar Hall of Twilight, level 3's piece (V2 of KBTemple, with its rune glow: shown at level 3):
the crown's three horns (9.43 higher than at level 1) and the three great horns rising from the
dais's sides to z 107.45 frozen at the tips (assets/angmar/hallof_twilight/horns.py: the walls
group's `freeze`), so the Hall reads the same as at levels 1 and 2. EA's V2 stays whole inside the
ice; its three small horns from the dais (to z 46.1) stay EA's, the menhirs standing close by.

The chain's last link: chained on angmar/hallof_twilight_v1 (`base`), it ships KBTemple and its
derived models for the whole chain (hallof_twilight -> _top -> _v1 -> _v2; rebuild in that order
after changing any link). EA's V2 (1753 triangles): x -66.5..69.0, y -60.5..65.6, z -3.5..107.5.
Per upgrade level: no cloth, no night lights, no fire.
"""
from sagekit.building import Building

from ..hallof_twilight.levels import HIDDEN, VIEWS
from ..style import AngmarStyle


class HallofTwilightV2(Building):
    style = AngmarStyle()
    source = "KBTemple"
    target = "V2"
    base = "angmar/hallof_twilight_v1"
    sheet = "KBTemple.tga"
    sheet_normal = "KBTemple_NRM.tga"
    own_textures = {"KBTemple.tga": "KBTemplY.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    house_tags = ()                 # shown per upgrade level; the house model is always drawn
    bake_hidden = HIDDEN[3]
    views = VIEWS

    def design(self, kit):
        from ..hallof_twilight.horns import frozen
        return frozen(kit, "V2")
