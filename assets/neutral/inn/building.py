"""The Inn (Inn, InnSecond): EA's wayside inn, kept whole and told as a story at the RTS camera, and
dressed in the look of whoever captures it (sagekit/capture.py).

EA's NBInn_SKN: body NBINN, 1,880 triangles on NBInn.tga + NBInn_NRM.tga (512, DXT1); a U of
timber buildings round a yard opening to -y (where units leave: UnitCreatePoint (5.9, 20.1),
rally (-0.1, -80)): the tall hall with a round balcony tower (x -62..-6), the gatehouse block at
the back (the gate at y 19.7, x -2.5..12), the stable wing on a 16-unit podium (x 29..71), a well.
The townsfolk (two skinned meshes) and the well's water (MESH01) stay EA's.

Ours (body): a broad three-flue fieldstone chimney through the hall's roof, smoking; a sign gallows at the yard
mouth carrying EA's own painted wolf's-head board, big, with a lamp; a faded madder awning over the
gate; a shingled stable lean-to against the podium with stalls and a hay rack; an open hearth in the
yard with a spit and a kettle, burning (EA's fire); barrels by the hall. The yard's middle, x -2..14,
stays clear for the units leaving the gate.

Capture dress (dress.py): per faction two banners (the hall's gable, the gatehouse dormer) or a
shield or plaque, and the hall's and stable wing's ridges crowned in the faction's manner: Dwarven
stepped stone crest with blue-steel caps on a gold rune band, Elven leaf finials and crystal
lanterns, Gondor's white merlons and pinnacles, Isengard's iron straps and spikes with the Hand
shield on braces, Mordor's black spikes, ember braziers and the Eye plaque, a Goblin bone fence
with crimson rags and skulls on the porch and a horned skull on the gable, Angmar's frozen tine
pair cased in ice and a cold-fire lantern."""
from sagekit.building import Building
from sagekit.capture import Capturable

from ..style import NeutralStyle

FRONT = ((0, -28.1, 0), (1, 0, 0), (0, -1, 0))          # the hall's gable face (looking -y)
GATE = ((0, 19.7, 0), (1, 0, 0), (0, -1, 0))            # the gate wall at the back of the yard
POST = (24.5, -24.5)                                     # the sign gallows
SPOTS = dict(banner=FRONT + (-41.9, 93.0, 12.0, 25.0, 1.2),              # the hall's gable, over the balcony
             banner2=GATE + (2.0, 55.0, 8.0, 13.0, 0.6),                  # the gatehouse dormer, over the awning
             ridges=[((-41.9, -31.7), (-41.9, 11.2), 103.6, 0.785),     # the hall's ridge (its roof's pitch)
                     ((50.9, -31.7), (50.9, 10.1), 67.45, 1.26)],       # the stable wing's
             porch=((-23.0, -31.0), (-9.0, -31.0)))                       # in front of the yard's left side


class Inn(Capturable, Building):
    style = NeutralStyle()
    source = "NBInn_SKN"
    target = "NBINN"
    sheet = "NBInn.tga"
    sheet_normal = "NBInn_NRM.tga"
    own_textures = {"NBInn.tga": "NBInH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    lifecycle = {"GBGenRubble": {"skip": "EA's generic rubble pile after the collapse (six factions' camp keeps draw "
                                         "it): none of our body is in it"}}
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): the yard's open hearth a coal glow. 3.0 live (was 20.3).
    fire_points = [(-14.0, -12.0, 0.6, 'coals')]
    views = {
        "rts": ((-1.4, -2.1, 51.8), 507, 50, -68, 50),        # the front (-y, where units leave) to the camera
        "close": ((-1.4, -12.0, 45.0), 300, 24, -58, 45),
        "ingame": ((-1.4, -2.1, 51.8), 1153, 53, -62, 50),
    }

    def body(self, kit):
        out = kit.stack(-18.0, -4.0, 11.0, 6.5, 72.0, 116.0, pots=3)        # a broad three-flue stack
        out += kit.gallows_sign(POST + (0,), (-1, 0, 0), 38.0, 18.0, 14.0, 10.0)
        a, t, n = GATE
        out += kit.awning(a, t, n, -6.0, 15.0, 39.6, 37.2, 5.0)
        out += kit.lean_to(29.3, 21.5, -17.0, 8.0, 15.8, 11.5)
        out += kit.hearth(-14.0, -12.0, 4.2)
        for x, y in ((-21.0, -24.0), (-21.0, -20.6), (-17.8, -23.6)):
            out += kit.barrel(x, y)
        return out

    def dress(self, kit):
        from ..dress import Spots, dress           # (Blender side: the factions' kits)
        return dress(Spots(**SPOTS))
