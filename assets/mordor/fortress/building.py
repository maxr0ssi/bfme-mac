"""The Mordor citadel (MordorFortressCitadel, MordorFortress), pass 7 "a claw round the witch-fire":
EA's body kept whole and made the Dark Tower's. Inside every tower's crown a cluster of small
jagged, hooked spikes rises out of the ring round a green witch-fire, the back tower's a little
larger (crown.py); barbed portcullis teeth under the Lidless Eye, steel spikes along the parapet,
broad lava welling from under the wall feet and round the courtyard, lava seams, impaling stakes
at the ramp, an orc scaffold (walls.py); dark lancets in the tower flutes (on every tower the pair
facing the camera kept in the Morgul witch-light), heavy chains slung between the crowns (towers.py); a forge with
its flue, fire baskets, a crane swinging a cage over the wall, ash heaps on the walks (yard.py).

EA's MBFortress (objects MordorFortressCitadel, MordorFortress; role fortress): body MBFORTRESS,
4882 triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our
texture is DXT5). In MBFORTRESS mesh coordinates (identity bone): x -56.51..112.99,
y -57.26..57.26, z -0.00..140.21. Other meshes (EA's, untouched): MBFDPYRES 992 (the pyres);
MBFDPF 32 (EXFireTorchSeq.tga) and MBFDPFG 16 (PG02.tga), the pyres' flame cards.
Lifecycle models in its Draw module: MBFortress_A, MBFortress_D2, MBFortress_D3.
House colour: MBHCFortress (one banner, HC_BANNER01, x 84..88, y 10..27, down the ramp's side).

EA's facts (measured 2026-09-30, work/measure.json and the model's own vertices):
- The curtain: a square, its outer faces at 52.8 on the ground battered to 51.8 at z 45, the
  parapet to z 70, iron spikes along the foot (48.6..52.8, z 0..24.5); the walk at z 51 from
  48.1 in to 32.1; the courtyard floor at z 1 inside the inner faces at 29.04 (the +-X ones to
  z 69, the +-Y ones to z 43, battered 2.6 degrees). Mirror-symmetric in y.
- Four towers on the corners, axes (+-41.75, +-42.5): a base to z 77 (r 11..15), a star shaft of
  eight knife ribs at 0, 45, .. degrees (r 14 at z 77 to r 9 at z 115) with V flutes between them
  (floors at 22.5 + 45k degrees, r 7.6 at z 74.8 to r 6.0 at z 104.8), a crown flaring to r 13
  at z 119.5, its walk at z 121.1, its rim and six spike heads to z 139.2..140.2.
- The pyres (MBFDPYRES) on the four crowns, z 120.5..149.9; their flame cards fill a box +- 14.2
  round each tower's axis, z 132.8..168.
- The gatehouse along +X (|y| < 12, x 27.9..57, z 0..60, its roof at z 60): a door recess to the
  courtyard at x 27.94 (|y| < 6, z 42.4) and one outside at x 56.9 (|y| < 7.4, z 45); the outer
  arch at x 64.1 (jambs |y| 8.5 to z 24.6, head to z 50.9); the frontispiece at x 57.3 (|y| <
  12.9, its point at z 73, side horns to z 82); the ramp on at z 1 to x 84, down to x 113;
  two standards at x 85, |y| 13..16, to z 56.
- The sheet: 1024, DXT5 with cut-out alpha (the blade and spike rows), damaged MBFortress_D,
  snow MBFortress_snow; nearly all the body painted from four parts: the spiked and fluted wall
  plate (245..615, 615..1024), the towers' shafts and crowns (838..945, 250..635), the inner walls
  (485..720, 180..520) and the walks' cratered rock (50..178, 292..418).

Kept clear (the upgrades' own vertices, 2026-09-30): the Gorgoroth spire (MBFEWEye, |x| < 19.15,
|y| < 23.3, to z 174.7, the courtyard's middle); the magma cauldrons (MBFMCauld: on the -X walk
x -50.1..-31.3, y -35.3..-3.6 and x -39.4..-32.6, y 3.6..22, z 51..98.9; a base up the -X inner
face x -44.2..-23.4, |y| < 8.9, z 0..66; spouts on the outer faces at +-(20.4..27.3), z 25.3..37.3);
the fire arrows over the gatehouse (MBFFArrows, x 32.6..51.6, |y| < 9.5, z 60..89.8); the lava
moat (MBFLavaMoat, outside, z 0..16.9); the pyres' flame cards (above); the doors and the ramp.
No night meshes. The back crown's spikes take the height to z 150 (+7.0 %): max_z_growth 0.08.
"""
from sagekit.building import Building
from sagekit.taxonomy import Tier

from ..style import MordorStyle


# Where real fire and smoke go (the game's particle systems on bones of MBFortress_FX): (x, y, z,
# kind) in MBFORTRESS mesh coordinates. Collected from the design (kit.fire records every point
# while a kit's `fire_log` is a list: design() prints FIRE_POINTS into work/logs/*geometry.log); run
# again after moving a fire. 19 points, 29 particle systems in each state that shows our body.
# The crowns burn green: "witchfire" (our SagekitWitchFire, EA's furnaceFire in Morgul green, and
# SagekitWitchSmoke, a modest dark plume; sagekit/fire_systems.py), the back tower a second green
# "witchflame". The lava, the forge and the fire baskets stay orange (EA's systems); the forge's
# flue carries EA's heavy dark plume alone ("plume": SmokeBuildingLarge).
FIRE_POINTS = [
    (-40.2, 41.0, 135.0, 'witchfire'), (-43.2, 44.0, 138.0, 'witchflame'),             # the back crown
    (-40.2, -44.0, 134.5, 'witchfire'), (43.2, -44.0, 134.5, 'witchfire'), (43.2, 41.0, 134.5, 'witchfire'),
    (-31.0, -53.8, 0.4, 'embers'), (31.0, -53.8, 0.4, 'embers'), (54.3, -35.0, 0.4, 'embers'),
    (-26.4, 26.4, 1.4, 'embers'), (26.4, -26.4, 1.4, 'embers'),                         # the lava channels
    (-12.0, -54.0, 1.0, 'smoke'), (54.3, -25.0, 1.0, 'smoke'),                          # smoke off the lava
    (0.0, 40.5, 53.8, 'hearth'), (12.3, 44.4, 97.0, 'chimney'), (12.3, 44.4, 101.0, 'plume'),  # the forge, its flue
    (-19.0, 34.6, 56.5, 'brazier'), (22.0, 34.6, 56.5, 'brazier'), (-20.0, -34.6, 56.5, 'brazier'),
    (17.0, -34.6, 56.5, 'brazier'),                                                     # the fire baskets
]


class Fortress(Building):
    style = MordorStyle()
    source = "MBFortress"
    target = "MBFORTRESS"
    tier = Tier.HERO
    fire_points = FIRE_POINTS
    max_z_growth = 0.08                 # the back crown's spikes to z 150 (+7.0 %): a claw inside EA's crown
    # EA's pyres and their flame cards: kept in game, left out of bakes and review renders. The game hides all
    # three until the Doom Pyres upgrade (EA's SubObjectsUpgrade ModuleTag_HidePyres / _ShowPyres), so the
    # renders show the crowns as they stand before it: our spikes and the green fire only
    bake_hidden = ("MBFDPF", "MBFDPFG", "MBFDPYRES")
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((28.2, -0.0, 80.0), 546, 50, -38, 50),         # EA's view raised 10: the crowns' tips in frame
        "close": ((28.2, -0.0, 96.0), 360, 24, -30, 45),
        "board": ((20.0, 0.0, 72.0), 540, 50, -38, 50),
        "tower": ((0.0, 0.0, 115.0), 200, 30, -38, 50),
        "ingame": ((28.2, -0.0, 70.1), 1240, 53, -62, 50),
        "crown": ((-36.0, 37.0, 135.0), 230, 22, -38, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS

        from . import crown, towers, walls, yard
        return logged(kit, lambda k: k.retag(crown.build(k) + towers.build(k) + walls.build(k) + yard.build(k)))
