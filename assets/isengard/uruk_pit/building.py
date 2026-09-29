"""Isengard uruk pit (IsengardUrukPit): stub from `sagekit new isengard`.

EA's IBUrukPit_SKN (objects IsengardUrukPit; role barracks): body IBURUKPIT_NEW, 1087 triangles,
painted from iburukpit.tga + iburukpit_nrm.tga (DXT1).
In IBURUKPIT_NEW mesh coordinates: x -48.86..72.79, y -41.51..53.08, z -0.47..64.92.
Target ambiguous: V2 (792 triangles) could be the body too (the rule takes a normal-mapped mesh
standing on the ground, then the largest); set `target` to the mesh the design redesigns.
Other meshes (EA's, untouched): V2 792 (iburukpit.tga, iburukpit_nrm.tga); UILURTZ02 452
(uilurtz_a.tga); PM_ORC 384 (MUOrcWarr_c.tga); N_WINDOW 120 (wbcave.tga, wbcave_nrm.tga); HOOK 96
(MUOrcWarr_c.tga); N_FIRE 24 (exfiretorchseq.tga).
Lifecycle models in its Draw module: IBUrukPit_A, IBUrukPit_D1, IBUrukPit_D2, IBUrukPit_D3.
House colour: IBHCUrukPit.
EA's body measured: `python3 -m sagekit measure isengard/uruk_pit` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/barracks (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


class UrukPit(Building):
    style = IsengardStyle()
    source = "IBUrukPit_SKN"
    target = "IBURUKPIT_NEW"
    sheet = "iburukpit.tga"
    sheet_normal = "iburukpit_nrm.tga"
    own_textures = {"iburukpit.tga": "iburukpiH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((12.0, 5.8, 32.2), 368, 50, -38, 50),
        "close": ((12.0, 5.8, 32.2), 218, 24, -30, 45),
        "ingame": ((12.0, 5.8, 32.2), 837, 53, -62, 50),
    }

    def design(self, kit):
        return []
