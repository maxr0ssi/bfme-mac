"""Angmar battle tower (AngmarBattleTowerExpansion), pass 1: EA's tower kept whole, its lantern crowned
small as the citadel is crowned: three forged iron tines with frozen tips rise from the lantern's
roof between EA's three horns, round a cairn of black stone and ice with the cold fire burning out
of its crater (a beacon of cold fire over the archers' ring).

EA's KBArrowTower (objects AngmarBattleTowerExpansion; role tower_expansion): body ARROWTOWER, 1168
triangles, painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In ARROWTOWER mesh coordinates: x -41.86..17.37, y -19.08..18.70, z 0.54..126.59.
Other meshes (EA's, untouched): ICEWALL 18 (EXFortressIce.tga, EXIceRefraction01.tga; x -42.7..12,
z 0..33, the Ice Walls upgrade).
Lifecycle models in its Draw module: KBArwTow_A, KBArwTow_D1, KBArwTow_D2, KBArwTow_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure angmar/battle_tower` -> work/measure.json.

EA's facts (measured 2026-10-01, ray casts on the model):
- An expansion on the citadel's pads (EA's base file bases\\fortress_angmar: the sides at 110 from
  the citadel, the corners at (+-77, +-77), each turned so local -X faces the citadel). The round
  tower (r 13..15 round (-3, 0)) stands outside; a walled wing (its floor at z 40.2, walls to 45..60)
  runs back along -X to x -41.9, into the curtain on the side pads and into the bastion on the corner
  pads (so nothing new goes on the wing).
- The top: a flared parapet bowl (z 62.5..68.7, r 13..17) round the archers' ring (floor z 65.1);
  ARROW01..04 at z 73.1..73.2, r ~12 from the tower's axis. In the middle a lantern (r 9..13, hollow
  below) roofed at z ~86..88 (r ~8), three horns rising off its rim: two at (-8, +-6.5) to z 112 and
  126.6, one at (2, 0) to z 122; small blades round the rim at z 81..93.5.
"""
from sagekit.building import Building

from ..style import AngmarStyle

# Real fire: (x, y, z, kind) in ARROWTOWER mesh coordinates, from the design (kit.fire's log)
FIRE_POINTS = [(-3.0, 0.0, 92.2, 'coldfire')]

LANTERN = (-3.0, 0.0)
ROOF = 86.0
# three tines in the gaps between EA's horns (at about 0, +-128 degrees round the lantern's axis): (deg, r)
TINES = [(64.0, 5.8), (-64.0, 5.8), (180.0, 6.0)]
H, W = 30.0, 3.9


def crown(kit):
    from ..shapes_addons import cairn, tine_crown
    out = tine_crown(kit, LANTERN, ROOF, TINES, H, W, seed=4.0)
    out += cairn(kit, (LANTERN[0], LANTERN[1], ROOF + 0.5), 2.6, 6.0, kind="coldfire", seed=5.0, n=7, rim=4)
    return out


class BattleTower(Building):
    style = AngmarStyle()
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): one small cold flame in the crown's lantern. 3.0 live (was 12.3).
    fire_points = [(-3.0, 0.0, 92.2, 'coldtorch')]
    source = "KBArrowTower"
    target = "ARROWTOWER"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    # EA remodelled the really damaged tower: cut, 23% open backs (sagekit/lifecycle.py `fill`)
    lifecycle = {"KBArwTow_D2": {"fill": True}}
    # EA's damaged tower is its healthy one with four more triangles (box within 0.7): cut along it,
    # 23% open backs against EA's 13%; it carries our body whole instead
    also_derived = ("KBArwTow_D1",)
    HOUSE_DRAW = "ModuleTag_Draw_HCBattleTower"
    views = {
        "rts": ((-12.2, -0.2, 63.6), 317, 50, -38, 50),
        "close": ((-3.0, 0.0, 95.0), 110, 42, -38, 45),          # the crown on the lantern
        "ingame": ((-12.2, -0.2, 63.6), 722, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        return logged(kit, lambda k: k.retag(crown(k)))
