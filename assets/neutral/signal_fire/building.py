"""Neutral signal fire (SignalFire, SignalFireSecond): stub from `sagekit new neutral`.

EA's NBSigFire (objects SignalFire, SignalFireSecond; role other): body MOUNTIAN, 300 triangles,
painted from NBSifFirMount.tga + NBSigFirMount_NRM.tga (DXT1).
In MOUNTIAN mesh coordinates: x -25.88..66.67, y -94.48..2.94, z -2.20..83.29.
Other meshes (EA's, untouched): COLUMN 448 (NBSigFireTower.tga, NBSigFire_NRM.tga); FIREBOX 80
(NBSigFireTower.tga, NBSigFire_NRM.tga); STAIRS 46 (NBSigFireStair_NRM.tga, NBSigFireStairs.tga);
FIREWOOD 26 (NBSigFireTowGlow.tga, NBSigFireTower.tga).
Lifecycle models in its Draw module: GBGenRubble, NBSigFire_A, NBSigFire_D1, NBSigFire_D2,
NBSigFire_D3, NBSigFire_R.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
GBGenRubble (EA's generic rubble pile; six factions' camp keeps draw it) is a lifecycle skip.
Its bone is turned (115 degrees about z, moved): world_space, every number in world axes.

Ours (body): two great stacks of split firewood, the beacon's fuel, at the mountain's foot and a
warden's timber lookout with a shingled roof by the stair foot. Our parts stay under 102 (the
mountain's height limit; EA's column rises to 129). Capture dress (dress.py): banners on the
lookout's boarded front and side (EA's column is not our mesh: a banner's open back there would face
the sky in the checks), the column's foot on its -y and +x sides crowned in the holder's manner (no
porch: no ground for a Goblin fence on the mountain).
EA's body measured: `python3 -m sagekit measure neutral/signal_fire` -> work/measure.json.

No Dwarven recipe plays this role.
"""
from sagekit.building import Building
from sagekit.capture import Capturable

from ..style import NeutralStyle

SPOTS = dict(banner=((0, -43.6, 0), (1, 0, 0), (0, -1, 0), -14.0, 16.0, 7.0, 9.0, 0.6),     # the lookout's front boards
             banner2=((-8.4, 0, 0), (0, 1, 0), (1, 0, 0), -40.0, 16.0, 6.0, 9.0, 0.6),    # its side boards
             ridges=[((-12.0, -14.8), (12.0, -14.8), 85.1, 0.0), ((14.8, -12.0), (14.8, 12.0), 85.1, 0.0)],
             porch=None, ceiling=102.0)          # the column's foot, just outside its faces; the body's height limit


class SignalFire(Capturable, Building):
    style = NeutralStyle()
    source = "NBSigFire"
    target = "MOUNTIAN"
    world_space = True
    facet_islands = 20                  # the mountain's smooth rock unwraps onto itself otherwise
    sheet = "NBSifFirMount.tga"
    sheet_normal = "NBSigFirMount_NRM.tga"
    own_textures = {"NBSifFirMount.tga": "NBSifFirMounH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    lifecycle = {"GBGenRubble": {"skip": "EA's generic rubble pile after the collapse (six factions' camp keeps draw "
                                         "it): none of our body is in it"}}
    views = {
        "rts": ((-1.3, -5.0, 52.0), 360, 50, -62, 50),
        "close": ((-4.0, -12.0, 50.0), 260, 28, -58, 45),
        "ingame": ((-1.3, -5.0, 42.6), 754, 53, -62, 50),
    }

    def body(self, kit):
        out = kit.log_stack((-27.0, -31.0), (0.9, -0.45, 0), 16.0, 1.5, rows=4)     # the beacon's fuel, at its foot
        out += kit.log_stack((23.0, -37.0), (0.95, 0.3, 0), 14.0, 1.5, rows=3)
        out += kit.platform((-14.0, -40.0), (1, 0, 0), 10.0, 7.0, 9.0)               # the warden's lookout over the stair foot
        out.append(kit.box(-19.0, -9.0, -43.6, -43.0, 9.0, 16.6, "planks|v", ("planks", True), ("beam", True)))
        out.append(kit.box(-9.0, -8.4, -43.0, -35.0, 9.0, 16.6, "planks|v", ("planks", True), ("beam", True)))
        return out

    def dress(self, kit):
        from ..dress import Spots, dress           # (Blender side: the factions' kits)
        return dress(Spots(**SPOTS))
