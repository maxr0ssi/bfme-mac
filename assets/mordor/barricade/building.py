"""Mordor barricade (MordorBarricade), pass 1: EA's L of blocks and keep kept whole, armed with barbed
steel and set in lava: open lava along the foot of every front and a moat before the gate, glowing
cracks up the walls, the portcullis' barbed teeth in the gate, barbed stakes, steel spikes along every
roof's lip, a claw of spikes rising inside the keep's parapet, the Lidless Eye, two fire baskets
(defences.py).

EA's MBBarcade (objects MordorBarricade; role bunker): body MBBARCADE, 923 triangles, painted from
MBBarcade.tga + MBBarcade_NRM.tga (DXT1). In MBBARCADE mesh coordinates (identity bone): x
-45.32..47.70, y -35.83..35.83, z -0.10..78.71. No other meshes. Bones ARCHER_01..04 (the archers on
the roofs). Lifecycle models in its Draw module: MBBarcade_A, MBBarcade_D1, MBBarcade_D2,
MBBarcade_D3. House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's
house_template); the design adds no cloth. EA's body measured: `python3 -m sagekit measure
mordor/barricade`.
"""
from sagekit.building import Building

from ..style import MordorStyle


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in the target's
# coordinates, collected from the design (kit.fire records them while the kit's `fire_log` is a list:
# design() prints FIRE_POINTS into work/logs/*geometry.log); run again after moving a fire.
FIRE_POINTS = [
    (-24.0, -30.4, 0.4, 'embers'), (4.0, -30.4, 0.4, 'embers'), (30.0, -34.1, 0.4, 'embers'),
    (45.6, -16.0, 0.4, 'embers'), (42.6, 20.0, 0.4, 'embers'), (-10.0, -30.6, 0.8, 'smoke'),
    (45.6, -24.0, 0.8, 'smoke'), (-33.0, -24.0, 39.6, 'brazier'), (35.5, 28.0, 48.3, 'brazier')
]


class Barricade(Building):
    style = MordorStyle()
    fire_points = FIRE_POINTS
    source = "MBBarcade"
    target = "MBBARCADE"
    sheet = "MBBarcade.tga"
    sheet_normal = "MBBarcade_NRM.tga"
    own_textures = {"MBBarcade.tga": "MBBarcadH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    # EA remodelled the really damaged pieces: cut, 3.4% open backs (sagekit/lifecycle.py `fill`)
    lifecycle = {"MBBarcade_D2": {"fill": True}}
    HOUSE_DRAW = "ModuleTag_Draw_HCBarricade"
    views = {
        "rts": ((1.2, -0.0, 39.3), 311, 50, -38, 50),
        "close": ((1.2, -0.0, 39.3), 184, 24, -30, 45),
        "ingame": ((1.2, -0.0, 39.3), 707, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS

        from . import defences
        return logged(kit, lambda k: k.retag(defences.build(k)))
