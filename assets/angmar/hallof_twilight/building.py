"""Angmar Hall of Twilight (AngmarHallofTwilight), pass 2 "the sorcerers' ring": EA's dais and shrine
kept whole; five broad menhirs (13 across, 9.5 deep, 34..39 tall) stand round the dais's rim on the
ground, each leaning a little out, its top cut on a slant and rimed, one great rune glowing down its
outer face, ice crystals at its foot; on the dais before the shrine (front-right, toward the RTS
camera) a sorcerers' altar: a broad step of dressed stone, a black stone block with three columns of
cold runes, a rimed top slab and a crater of ice and black stone shards with the cold fire burning out
of it ("coldfire"). Pass 1's stones were thin (6.4 by 3.4) and lost at RTS. EA's horns are frozen on
the level pieces (TOP_1, V1, V2: each at its own height, not on BASE) by the chained recipes
hallof_twilight_top, _v1 and _v2 (horns.py).
Kit: assets/angmar/shapes_army.py.

EA's KBTemple (objects AngmarHallofTwilight; role barracks): body BASE, 784 triangles, painted
from KBTemple.tga + KBTemple_NRM.tga (DXT1).
In BASE mesh coordinates: x -59.31..57.20, y -65.15..53.81, z -11.19..43.76.
Other meshes (EA's, untouched): the level pieces (SubObjectsUpgrade): level 1 shows TOP_1 474 (the
shrine's roof and its three horns, z 44..79) and ROCKS_1 202; level 2 V1 1499 (hides TOP_1 and
ROCKS_1); level 3 V2 1753 and RUNEGLOWV2 204 (EXTemple_Runes.tga; hides V1, TOP_1, ROCKS_1); N_WINDOW 4.
Our design is on BASE, shown at every level; the level pieces are the chained recipes' (horns.py).
Lifecycle models in its Draw module: KBTemple_A, KBTemple_D1, KBTemple_D2, KBTemple_D3.
House colour: KBHCTemple. EA's own sorcery: AngTempleWhirl / AngTempleMist (and _V2) at FXBONE.
"""
import math

from sagekit.building import Building

from ..style import AngmarStyle


# EA's dais: a round platform (r 30 round (0, -6), top z 4) under the shrine (a ring of uprights at r ~12 and
# the front block (0, -23) to z 38 under the roof; the roof itself is a level piece: TOP_1 at level 1, V1
# at 2, V2 at 3, with ROCKS_1 at level 1 only); the sorcerers leave by the front ramp (|x| < 10, y < -28;
# rally (0, -90)). BASE shows at every level, so all of ours stands clear of every level piece: V1's and
# V2's great horns spring from the dais at r 8..24 on the +-X sides (0, +-30, 180, +-150 degrees), their
# clumps reach in at -150, -30 and 60..120; the roof hangs over r 13..22 from z 40 up (measured
# 2026-10-01 from the model's own vertices)
DAIS, FLOOR = (0.0, -6.0), 4.0
ALTAR = (-55.0, 23.0)                     # (degrees round the dais, r): front-right, toward the RTS camera
# the menhirs: (degrees, r, height), 13 broad and 9.5 deep, standing on the ground at the dais's rim (it
# cuts into them); their corners clear the level pieces by 1.8..3.9 below z 44
STONES = [(0.0, 28.5, 37.0), (180.0, 28.5, 35.0), (-125.0, 28.0, 39.0), (45.0, 28.5, 34.0), (135.0, 28.5, 36.0)]

# real fire (the game's particle systems on bones of KBTemple_FX), from the design's log
FIRE_POINTS = [(13.2, -24.8, 16.1, 'coldfire')]         # out of the altar's crater


class HallofTwilight(Building):
    style = AngmarStyle()
    source = "KBTemple"
    target = "BASE"
    sheet = "KBTemple.tga"
    sheet_normal = "KBTemple_NRM.tga"
    own_textures = {"KBTemple.tga": "KBTemplH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((-1.1, -5.7, 16.3), 386, 50, -38, 50),
        "close": ((-1.1, -5.7, 16.3), 228, 24, -30, 45),
        "ingame": ((-1.1, -5.7, 16.3), 877, 53, -62, 50),
    }

    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": an identity building, at most 20 live
    # particles): the altar's cold fire without its plume. 7.2 live (was 12.3).
    fire_points = [(13.2, -24.8, 16.1, 'coldflame')]
    # level 1 in the bakes and review renders: the level pieces V1 and V2 (and V2's rune glow) are drawn later
    bake_hidden = ("V1", "V2", "RUNEGLOWV2", "N_WINDOW")

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        return logged(kit, lambda k: k.retag(self._pieces(k)))

    @staticmethod
    def _pieces(kit):
        from .. import shapes_army as A
        A.floor(-11.19)                         # EA's lowest (BASE z min)
        cx, cy = DAIS
        at = lambda deg, r: (cx + r * math.cos(math.radians(deg)), cy + r * math.sin(math.radians(deg)), FLOOR)  # noqa
        out = A.altar(kit, at(*ALTAR), (math.cos(math.radians(ALTAR[0])), math.sin(math.radians(ALTAR[0]))), s=1.0,
                      seed=1.0)
        for i, (deg, r, h) in enumerate(STONES):
            a = math.radians(deg)
            p = at(deg, r)
            out += A.rune_stone(kit, (p[0], p[1], 0.0), (math.cos(a), math.sin(a)), 13.0, 9.5, h, lean=0.05, seed=i * 1.3,
                                runed="great")
        return out
