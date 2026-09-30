"""Mordor battle tower (MordorBattleTower), pass 1: EA's star-shafted tower kept whole, crowned with the
citadel's claw: eight jagged spikes rising from inside the roof's dish and leaning in round a jagged fire
bowl with orange fire and dark smoke; the Lidless Eye in the head's valley; lava welling out from the
foot (tower.py).

EA's MBSentry (objects MordorBattleTower; role tower): body CYLINDER01, 680 triangles, painted from
DolGolGate.tga + DolGolGate_NRM.tga (DXT1). In CYLINDER01 mesh coordinates (on the root, 0.1 off
the axis): x -15.31..15.56, y -15.30..15.57, z -0.08..122.77. No other meshes. Bones ARROW_01..16
(the archers, r 7..8.3, z 89.2 and 91.7). Lifecycle models in its Draw module: MBSentry_A,
MBSentry_D1, MBSentry_D2, MBSentry_D3. House colour: MBHCSentry (HC_BANNER01, x -21..-10,
y -19.5..-7.6, to z 73.7). Its sheet is drawn by angmar too: our own texture is pinned in
own_textures. EA's body measured: `python3 -m sagekit measure mordor/battle_tower`.
"""
from sagekit.building import Building

from ..style import MordorStyle


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in the target's
# coordinates, collected from the design (kit.fire records them while the kit's `fire_log` is a list:
# design() prints FIRE_POINTS into work/logs/*geometry.log); run again after moving a fire.
FIRE_POINTS = [
    (0.1, 0.1, 122.3, 'furnace'), (0.1, 0.1, 125.0, 'smoke'), (10.7, -10.5, 0.4, 'embers'),
    (10.7, 10.7, 0.4, 'embers'), (-10.5, -10.5, 0.4, 'embers'), (-10.5, 10.7, 0.4, 'embers')
]


class BattleTower(Building):
    style = MordorStyle()
    fire_points = FIRE_POINTS
    source = "MBSentry"
    target = "CYLINDER01"
    sheet = "DolGolGate.tga"
    sheet_normal = "DolGolGate_NRM.tga"
    own_textures = {"DolGolGate.tga": "DolGolGatH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((0.0, 0.0, 61.3), 287, 50, -38, 50),
        "close": ((0.0, 0.0, 105.0), 120, 24, -30, 45),        # the crown
        "ingame": ((0.0, 0.0, 61.3), 652, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS

        from . import tower
        return logged(kit, lambda k: k.retag(tower.build(k)))
