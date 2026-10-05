"""Angmar catapult works (AngmarCatapultExpansion), pass 2 "the frozen works": EA's troll-sling tower
kept whole; round its top on the faces the RTS camera sees, two frozen timber hoardings: plank
galleries on raking struts with loopholes, a shingled lean-to up to the parapet, rime on the eaves and
icicles under them. At the foot on the camera's diagonal a frozen timber gantry (A-frame trestles under
a heavy rimed beam) hangs two ice boulders in iron slings over a heaped crib of big ice boulders; on
the other diagonal a second pile and beside it the freezing pit, a kerb of black stone round a grate
of cold fire ("coldflame"); more ice ammunition in a crib on the platform, clear of the troll.
Kit: assets/angmar/shapes_army.py.

EA's KBTrollSlingTo (objects AngmarCatapultExpansion; role catapult_tower): body KBTROLLSLINGTOW,
397 triangles, painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our
texture is DXT5).
In KBTROLLSLINGTOW mesh coordinates: x -41.84..43.08, y -39.25..39.18, z -0.02..61.85.
Other meshes (EA's, untouched): ICEWALL 24 (EXFortressIce.tga, EXIceRefraction01.tga).
Lifecycle models in its Draw module: KBTrlSgTw_A, KBTrlSgTw_D1, KBTrlSgTw_D2, KBTrlSgTw_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).

EA's facts (measured 2026-10-01 from the model's own vertices): a round tower (its face r 28..31 at
z 47..56), the platform floor at z 49 inside a parapet ring (r 22..28, to z 53), blades on the parapet
and buttresses at 0 and +-80 degrees (to r 35), a wall stub to -X (x -42..-20, |y| < 11, z 48). The
Ice Walls shell (ICEWALL) is a skirt at r 34..40 to z 33. The troll (AngmarTrollSlingFortress) is
spawned on the platform at (4.4, -0.5, 48.2).
"""
import math

from sagekit.building import Building

from ..style import AngmarStyle


# EA's tower: round (r ~30 round the origin), its platform floor at z 49 inside a parapet ring (r 22..28,
# z 53), the wall stub to -X (x -42..-20, |y| < 11, z 48), buttress fins at +-Y and +X; the Ice Walls shell
# (ICEWALL) a skirt at r 34..40 to z 33. The troll (AngmarTrollSlingFortress) stands on the platform at
# (4.4, -0.5, 48.2): its middle stays clear. The diagonals are free ground inside the footprint.
HOIST = -40.0                             # the works on the diagonal the RTS camera faces (seen broadside)
HEAP = (-80.0, 17.0)                      # the ice ammunition on the platform: (degrees, r), 16 from the troll
PLATFORM = 49.0
# on the other diagonal (+X+Y, beyond the Ice Walls skirt): the great pile of ice boulders in its crib and
# beside it the freezing pit, a kerb of black stone round a grate of cold fire: (degrees, r)
PILE = (34.0, 42.0)
PIT = (55.0, 41.0)
# frozen timber hoardings round the top, between EA's fins (at 0 and +-80 degrees the parapet's blades
# stand to r 35 and the buttresses below them): (from, to degrees); the tower's face there at r 28..31
HOARDS = [(-68.0, -12.0), (12.0, 68.0)]


# real fire (the game's particle systems on bones of KBTrollSlingTo_FX), from the design's log
FIRE_POINTS = [(23.5, 33.6, 2.0, 'coldflame')]          # the freezing pit by the pile


class Catapult(Building):
    style = AngmarStyle()
    source = "KBTrollSlingTo"
    target = "KBTROLLSLINGTOW"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressL.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    lifecycle = {"KBTrlSgTw_D3": {"backs": (0.11, "the collapse's first frames: slivers of the pilasters' "
                                               "insides, 10.6% past EA's; the RTS renders show no hole and "
                                               "every piece is under the ground at its end")}}
    HOUSE_DRAW = "ModuleTag_Draw_HCCatapult"
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): none. 0.0 live (was 7.2).
    fire_points = []
    views = {
        "rts": ((0.6, -0.0, 30.9), 288, 50, -38, 50),
        "close": ((0.6, -0.0, 30.9), 170, 24, -30, 45),
        "ingame": ((0.6, -0.0, 30.9), 656, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS (none here)
        return logged(kit, lambda k: k.retag(self._pieces(k)))

    @staticmethod
    def _pieces(kit):
        from .. import shapes_army as A
        A.floor(0.0)                            # EA's ground (KBTROLLSLINGTOW z min)
        o = (math.cos(math.radians(HOIST)), math.sin(math.radians(HOIST)))
        at = lambda deg, r, z: (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)), z)  # noqa: E731
        t = (-o[1], o[0])
        out = A.gantry(kit, at(HOIST, 41.0, 0.0), t, 14.0, 23.0, [(-3.5, 11.0), (3.5, 7.0)], post=3.0, splay=3.0,
                       seed=1.0)
        out += A.boulder_heap(kit, at(HOIST, 41.0, 0.0), o, 12.0, 8.0, s=6.4, n=11, seed=2.0)
        deg, r = PILE                           # the great pile of ice boulders, and the pit where they freeze
        out += A.boulder_heap(kit, at(deg, r, 0.0), (math.cos(math.radians(deg)), math.sin(math.radians(deg))), 10.0,
                              8.0, s=6.4, n=11, seed=7.0)
        deg, r = PIT
        out += A.fire_pit(kit, at(deg, r, 0.0), 3.2, 2.6, seed=2.0)
        for a0, a1 in HOARDS:
            out += A.hoarding(kit, (0.0, 0.0), a0, a1, 29.0, 35.5, 45.0, 53.5, 58.5, seed=a0)
        deg, r = HEAP
        out += A.boulder_heap(kit, at(deg, r, PLATFORM), (math.cos(math.radians(deg)), math.sin(math.radians(deg))),
                              10.0, 7.0, s=4.0, n=7, seed=5.0)
        return out
