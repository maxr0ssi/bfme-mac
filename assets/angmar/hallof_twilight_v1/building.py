"""Angmar Hall of Twilight, level 2's piece (V1 of KBTemple: shown at level 2, hidden at 3): the
crown's three horns (4.32 higher than at level 1) and the three great horns rising from the dais's
sides to z 86 frozen at the tips (assets/angmar/hallof_twilight/horns.py: the walls group's
`freeze`), so the Hall reads the same as at level 1. EA's V1 stays whole inside the ice.

Chained on angmar/hallof_twilight_top (`base`, level 1's piece), before angmar/hallof_twilight_v2.
EA's V1 (1499 triangles): x -65.44..64.90, y -59.54..64.55, z -24.30..86.04; the menhirs of the
Hall's own design (BASE) stand under z 39, the great horns' casings start over z 42.8 (their
ragged frost line). Per upgrade level: no cloth, no night lights, no fire.
"""
from sagekit.building import Building

from ..hallof_twilight.levels import HIDDEN, VIEWS
from ..style import AngmarStyle


class HallofTwilightV1(Building):
    style = AngmarStyle()
    source = "KBTemple"
    target = "V1"
    base = "angmar/hallof_twilight_top"
    sheet = "KBTemple.tga"
    sheet_normal = "KBTemple_NRM.tga"
    own_textures = {"KBTemple.tga": "KBTemplX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    house_tags = ()                 # shown per upgrade level; the house model is always drawn
    bake_hidden = HIDDEN[2]
    views = VIEWS

    def design(self, kit):
        from ..hallof_twilight.horns import frozen
        return frozen(kit, "V1")
