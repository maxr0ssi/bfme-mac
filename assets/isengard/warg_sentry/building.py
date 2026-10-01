"""Isengard warg sentry (IsengardWargSentry): EA's den kept whole, its middle clear for the wargs;
a palisade on its back rim round a Hand standard, heaps of gnawed bones and chain stakes at its
ends (pass 4, 2026-09-30: pass 3's blade pair there went), warg posts and chains, stakes, a fire
pit and braziers (kennel.py).

EA's IBWargSent (objects IsengardWargSentry; role tower): body IBWARGSENT, 3013 triangles,
painted from IBWargSent.tga + IBWargSent_NRM.tga (DXT5).
In IBWARGSENT mesh coordinates: x -57.74..64.42, y -59.58..65.16, z -0.31..32.74.
Other meshes (EA's, untouched): N_WINDOW 80 (WBCave.tga, WBCave_NRM.tga); N_FIRE 16
(EXFireTorchSeq.tga).
Lifecycle models in its Draw module: IBWargSent_A, IBWargSent_D1, IBWargSent_D2, IBWargSent_D3.
House colour: IBHCWargSent.
EA's body measured: `python3 -m sagekit measure isengard/warg_sentry` -> work/measure.json.

Nearest Dwarven recipe: assets/dwarves/sentry_tower (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in the target's
# coordinates, collected from the design (kit.flames / kit.fire record them when the kit has a
# `fire_log` list); run again after moving a fire.
FIRE_POINTS = [
    (40.0, -30.0, 8.5, 'brazier'), (46.0, -14.0, 8.5, 'brazier'), (-30.0, -34.0, 1.2, 'grate'),
    (-15.9, 39.4, 6.9, 'brazier'), (-41.9, 7.4, 6.9, 'brazier')
]


class WargSentry(Building):
    style = IsengardStyle()
    fire_points = FIRE_POINTS
    source = "IBWargSent"
    target = "IBWARGSENT"
    sheet = "IBWargSent.tga"
    sheet_normal = "IBWargSent_NRM.tga"
    own_textures = {"IBWargSent.tga": "IBWargSenH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((3.3, 2.8, 16.2), 391, 50, -38, 50),
        "close": ((3.3, 2.8, 16.2), 231, 24, -30, 45),
        "ingame": ((3.3, 2.8, 16.2), 888, 53, -62, 50),
    }

    def design(self, kit):
        from . import kennel
        return kennel.build(kit)
