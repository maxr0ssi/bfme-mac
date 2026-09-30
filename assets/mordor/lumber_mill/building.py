"""Mordor lumber mill (MordorLumberMill): stub from `sagekit new mordor`.

EA's MBLumMill_SKN (objects MordorLumberMill; role economy): body LUMBERMILL, 1204 triangles,
painted from MBLumberMill.tga + MBLumberMill_NRM.tga (DXT1).
In LUMBERMILL mesh coordinates: x -66.93..53.07, y -56.71..57.42, z -4.40..45.61.
Target ambiguous: V2 (385 triangles) could be the body too (the rule takes a normal-mapped mesh
standing on the ground, then the largest); set `target` to the mesh the design redesigns.
Other meshes (EA's, untouched): V2 385 (MBLumberMill.tga, MBLumberMill_NRM.tga); ORCN 264
(MUOrcWarr.tga); ORC 264 (MUOrcWarr.tga); N_WINDOW 80 (WBCave.tga, WBCave_NRM.tga); OBJECT04 24
(MBLumberMill.tga, MBLumberMill_NRM.tga); OBJECT06 24 (MBLumberMill.tga, MBLumberMill_NRM.tga);
OBJECT05 24 (MBLumberMill.tga, MBLumberMill_NRM.tga); OBJECT02 24 (MBLumberMill.tga,
MBLumberMill_NRM.tga).
Lifecycle models in its Draw module: MBLumMill_A, MBLumMill_D1, MBLumMill_D2.
House colour: MBHCLumberMill.
Other factions draw MBLumMill_A, MBLumMill_D1, MBLumMill_D2, MBLumMill_SKN too (goblins,
isengard): it ships as its own copy, own_model MBLumMill2_SKN.
MBHCLumberMill is drawn by another faction too: the house step ships an own copy
(Building.own_house_copy).
Its sheet is drawn by goblins, isengard too: our own texture is pinned in own_textures.
EA's body measured: `python3 -m sagekit measure mordor/lumber_mill` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/hearth (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import MordorStyle


class LumberMill(Building):
    style = MordorStyle()
    source = "MBLumMill_SKN"
    target = "LUMBERMILL"
    own_model = "MBLumMill2_SKN"            # goblins, isengard draws MBLumMill_SKN too (sagekit/ownership.py)
    sheet = "MBLumberMill.tga"
    sheet_normal = "MBLumberMill_NRM.tga"
    own_textures = {"MBLumberMill.tga": "MBLumberMilB.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-6.9, 0.4, 20.6), 381, 50, -38, 50),
        "close": ((-6.9, 0.4, 20.6), 225, 24, -30, 45),
        "ingame": ((-6.9, 0.4, 20.6), 865, 53, -62, 50),
    }

    def design(self, kit):
        return []
