"""Mordor haradrim palace (MordorHaradrimPalace), pass 2: EA's great cross-shaped tent kept whole, in
Mordor's black and fire with the Harad twist (Max: "cool like it go for it"): on the peak a crown of
eight ivory tusks round a great fire bowl on a stepped basalt plinth (the family motif); on the
ground either side of the -Y door a stepped plinth, a fire bowl and six ivory tusks round it; the
Harad sun in brass on war-paint plates under the gables and over the door; two banners of the
player's colour with the sun and serpent on the X arm's -Y eave; real fire in EA's bonfire
(palace.py).

EA's MBHrdPlc_SKN (objects MordorHaradrimPalace; role other): body MBHRDPLC, 1106 triangles (rigid,
on the root), painted from MBHrdPlc.tga + MBHrdPlc_NRM.tga (DXT1). In MBHRDPLC mesh coordinates:
x -34.43..34.41, y -41.94..38.16, z -3.83..47.20. Skeleton MBHrdPlc_SKL (idle animations IDLA..C:
the lancer). Other meshes (EA's, untouched): BANNER_HARAD01 736 (Haradrim_Banr.tga); V2A 426 and
V1 340 (MBHrdPlc.tga: the upgrade pieces, V1 the tusk ring at level 2, V2A the tower and poles at
level 3, EA's SubObjectsUpgrades); MUHARALNCR 308 (skinned, the lancer) and LANCE 152; BONFIRE 207
(PCampFire.tga) and FIRE 8 (EXFireSeq.tga, its flame card: left out of our bakes, kept in game).
Bones ARROW_01..08 (the arm ends), TENTCTRL, FIRE, BONFIRE. Lifecycle models in its Draw module:
MBHrdPlc_A, MBHrdPlc_D1, MBHrdPlc_D2, MBHrdPlc_D3. House colour: MBHCHrdPlc (HC_BANNER01, its
pole at (17.2, -19.7), to z 69). EA's body measured: `python3 -m sagekit measure
mordor/haradrim_palace`.
"""
from sagekit.building import Building

from ..style import MordorStyle


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in the target's
# coordinates, collected from the design (kit.fire records them while the kit's `fire_log` is a list:
# design() prints FIRE_POINTS into work/logs/*geometry.log); run again after moving a fire.
FIRE_POINTS = [
    (0.0, 0.0, 52.9, 'furnace'), (0.0, 0.0, 55.5, 'plume'), (-11.0, -36.1, 11.1, 'furnace'),
    (-11.0, -36.1, 13.8, 'smoke'), (11.0, -36.1, 11.1, 'furnace'), (11.0, -36.1, 13.8, 'smoke'),
    (21.5, -28.0, 2.0, 'hearth')
]


class HaradrimPalace(Building):
    style = MordorStyle()
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): the roof's fire a brazier. 6.0 live (was 54.5).
    fire_points = [(0.0, 0.0, 52.9, 'brazier')]
    source = "MBHrdPlc_SKN"
    target = "MBHRDPLC"
    sheet = "MBHrdPlc.tga"
    sheet_normal = "MBHrdPlc_NRM.tga"
    max_z_growth = 0.45                     # the crown's tusks to z 64 (+41 %); EA's own level 3 tower reaches z 79
    # EA's bonfire flame card, and the pieces the game shows only from level 2 (V1, the tusk ring) and 3 (V2A
    # the tower, the banner, the lancer; EA's SubObjectsUpgrades): kept in game, left out of the bakes and the
    # renders, so they show the palace as it is built (level 1)
    facet_islands = 8                       # the unwrap overlapped (0.24%): seams at EA's islands and 8-degree turns
    bake_hidden = ("FIRE", "V1", "V2A", "BANNER_HARAD01", "MUHARALNCR", "LANCE")
    own_textures = {"MBHrdPlc.tga": "MBHrdPlH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    lifecycle = {"MBHrdPlc_A": {"fill": True}}     # EA's build model is a remodel, not a cut (sagekit/lifecycle.py)
    views = {
        "rts": ((-0.0, -1.9, 21.7), 258, 50, -38, 50),
        "close": ((-0.0, -1.9, 21.7), 152, 24, -30, 45),
        "ingame": ((-0.0, -1.9, 21.7), 586, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS

        from . import palace
        return logged(kit, lambda k: k.retag(palace.build(k)))
