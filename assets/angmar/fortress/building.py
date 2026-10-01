"""The Angmar citadel (AngmarFortressCitadel, AngmarFortress), pass 5 "four frozen tines, clear of
the upgrades": EA's body kept whole and made Carn Dum's. Out of the courtyard well rises the
Witch-king's crown in iron: four forged tines on the building's axes to z 120, each with a raised
spine, steel edges, barbs, riveted bands above the walk and a rune groove glowing cold blue, their
points frozen - cased in ice under a ragged frost line, rime toward the points, crystals growing
out, icicles off the barbs; EA's bastion windows look out between them; they rise from a ring cairn
of black stone and ice round the middle of the well, the cold fire burning in a crater on each
diagonal between them (crown.py). Ice-crystal clusters grow from the ground beyond the walls (a
great one on each side of the gate's ramp, smaller ones in the gaps between the upgrades) and on
the parapet, icicles hang under a rime crust along the curtain's lip, cold glow wells out of
fissures beside the ramp (walls.py); sorcerers' braziers of cold fire on the walk, iron gibbets off
the -Y wall towers, icicles off the gate's lintel, two banners in the player's colour (yard.py).
Pass 3 had eight tines (four tall, four short): too busy with EA's horns at RTS (Max: "reduce a few
horns but keep some ... just 4 more detailed ones?", "ice cold tips, like frozen style"). Pass 4
(Max: "pass 4 is great") crossed EA's own upgrade models: the House of Lamentation's drum met the +X
tine's frozen point, the sanctum stood in the heart's cairn with the cold fire inside it, the
Spikes' clumps stood among the wall-foot ice, a battle tower on the S or N pad crossed the banners.
Pass 5 keeps the look and clears them all (crown.py and walls.py name what each keeps clear of).
Kit: assets/angmar/shapes*.py. Reviews: build/assets/angmar/_review/citadel_v1..v5.jpg.

EA's KBFortress (objects AngmarFortressCitadel, AngmarFortress; role fortress): body KBFORTRESS,
4652 triangles, painted from KBFortress.tga + KBFortress_NRM.tga (DXT1).
In KBFORTRESS mesh coordinates: x -83.12..107.64, y -83.26..83.12, z -0.72..143.55.
Other meshes (EA's, untouched): ICEWALL 715 (EXFortressIce.tga, EXIceRefraction01.tga);
ICEMUNITIONS04 164 (PFrozenPond01_env.tga, SoWolf_Ice2.tga); ICEMUNITIONS03 164
(PFrozenPond01_env.tga, SoWolf_Ice2.tga); ICEMUNITIONS01 164 (PFrozenPond01_env.tga,
SoWolf_Ice2.tga); ICEMUNITIONS02 148 (PFrozenPond01_env.tga, SoWolf_Ice2.tga); ICEMUNMIST_04 136
(EXIceRefraction01.tga); ICEMUNMIST_03 136 (EXIceRefraction01.tga); ICEMUNMIST_01 136
(EXIceRefraction01.tga).
Lifecycle models in its Draw module: KBFortres_D1, KBFortres_D2, KBFortres_D3, KBFortress_A.
House colour: KBHCFortress.
EA's body measured: `python3 -m sagekit measure angmar/fortress` -> work/measure.json.

EA's facts (measured 2026-10-01, work/measure.json and the model's own vertices):
- A ring citadel, nearly four-fold symmetric: the curtain's outer hull an octagon of radius ~83
  (x -83.1..107.6 with the gate ramp, y -83.3..83.1), battered faces leaning in from z ~11 to
  z 38; the plinth top at z 1.6; the wall walk at z 51.85 (x and y within +-67.5), its parapet
  roof at z 56.8; the courtyard a deep round well inside the ring.
- Four keep spires round the middle at (+-31.4, +-31.4) to z 143.3 (the tallest heads), four great
  curved horns on the ring's diagonals at (+-56, +-56) to z 105.5..106.4; small spikes along the
  parapet at (+-62, +-15) and (+-15, +-62) to z ~77.
- The gate along +X: a spike over it at (68.6, 0) to z 98.4 with a pair at (68.6, +-13.7) to
  z 92.4; the ramp out to x 107.6 (|y| < 28).
- The sheet: 1024, DXT1 (no cut-out alpha); damaged KBFortress_D1, snow KBFortress_Snow, and the
  Ice Walls upgrade's KBFortress_Ice (+ KBFortressNRM_Ice), swapped in by INI. Painted from the
  stone blocks and slits (the lower half), the frost-grained timber (the horns and spires), the
  plank walk round the ring and the scale shingles (atlas.py).
- Not the body (effect meshes, shown by upgrades and hidden in the palette renders): ICEWALL
  (Ice Walls: an ice crust over the whole curtain to z 59.8, EXFortressIce), ICEMUNITIONS01..04
  and ICEMUNMIST_01..04 (Ice Munitions: horns of ice on bones, PFrozenPond01_env, SoWolf_Ice2,
  EXIceRefraction01). Keep both clear of new faces and out of the bake (bake_hidden), with N_WINDOW
  82 (night windows) and MBFDPF 64 (EA's BLUE torch flame cards, EXFireTorchSeqBlue, round the ring
  at z 91.5..129.4: Angmar's fire is already cold blue in EA's art).
- The doors are a Draw of their own (KBFDoor_CLS, AngmarFortressCitadel); the citadel also draws
  the Dwarven bib DBFortress_Bib (sheet GBWall_Bib, drawn by the Dwarves, Men and Elves too): never
  recolour it in place.

Nearest Dwarven recipe: assets/dwarves/fortress (the same role; start from its shapes).
"""
from sagekit.building import Building
from sagekit.taxonomy import Tier

from ..style import AngmarStyle

# Where real fire goes (the game's particle systems on bones of KBFortress_FX): (x, y, z, kind) in
# KBFORTRESS mesh coordinates, collected from the design (design() prints FIRE_POINTS into
# work/logs/*geometry.log); run again after moving a fire. 8 points, 10 particle systems in each state
# that shows our body (as pass 4's 9 points). All cold: "coldfire" (our SagekitColdFire, EA's furnaceFire
# ice-blue to white, and SagekitColdSmoke, a modest blue-black plume; sagekit/fire_systems.py) out of the
# NE and SW craters of the ring cairn, "coldflame" (the fire alone) out of the SE and NW ones and in each
# sorcerer's brazier on the walk. The craters stand at r 29, outside the sanctum (r <= 20.3) when it is
# built in the middle of the well.
FIRE_POINTS = [
    (20.5, 20.5, 51.5, 'coldfire'), (-20.5, 20.5, 51.5, 'coldflame'), (-20.5, -20.5, 51.5, 'coldfire'),
    (20.5, -20.5, 51.5, 'coldflame'),                                                  # the ring's craters
    (27.7, -52.1, 57.1, 'coldflame'), (-27.7, -52.1, 57.1, 'coldflame'), (27.7, 52.1, 57.1, 'coldflame'),
    (-52.1, 27.7, 57.1, 'coldflame'),                                                  # the braziers
]


class Fortress(Building):
    style = AngmarStyle()
    source = "KBFortress"
    target = "KBFORTRESS"
    tier = Tier.HERO
    sheet = "KBFortress.tga"
    sheet_normal = "KBFortress_NRM.tga"
    own_textures = {"KBFortress.tga": "KBFortresH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((12.3, -0.1, 71.4), 641, 50, -38, 50),
        "close": ((12.3, -0.1, 71.4), 379, 24, -30, 45),
        "ingame": ((12.3, -0.1, 71.4), 1457, 53, -62, 50),
        "board": ((12.0, 0.0, 62.0), 560, 50, -38, 50),          # the palette options (style.palette_views)
        "keep": ((0.0, 0.0, 96.0), 270, 28, -38, 50),            # the keep's four spires and the walls behind
        "crown": ((0.0, 0.0, 80.0), 300, 42, -38, 50),            # the crown in the well
    }
    fire_points = FIRE_POINTS

    # EA's Ice Walls and Ice Munitions meshes and the Banners upgrade's blue torch cards: kept in game,
    # left out of bakes and review renders (the game shows them only with their upgrades)
    bake_hidden = ("MBFDPF", "ICEWALL", "ICEMUNITIONS01", "ICEMUNITIONS02", "ICEMUNITIONS03", "ICEMUNITIONS04",
                   "ICEMUNMIST_01", "ICEMUNMIST_02", "ICEMUNMIST_03", "ICEMUNMIST_04")

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS

        from . import crown, walls, yard
        return logged(kit, lambda k: k.retag(crown.build(k) + walls.build(k) + yard.build(k)))
