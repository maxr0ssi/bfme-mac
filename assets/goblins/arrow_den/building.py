"""The Goblin arrow den (WildArrowDenExpansion): EA's watch-pod kept whole - the plated octagonal
stalk, the flared bowl, the dark ring of glowing eyes the arrows fly from, the spiked octagonal
roof, the brace down to the ground at the back - and made a bone-clasped lookout in blood, iron and
bone: four great ribs rise out of a skirt of black rock to grip the stalk (pad.py, shared by every
expansion), riveted iron bands round the stalk and the brace, a skull on a spike out of the stalk,
a ring of bone fangs and hanging skulls under the bowl, iron spikes round the roof and an iron spike
out of its middle with a skull driven onto it (the citadel spires' mark), a skull on the brace's
post, bone spikes along its beam, a gibbet cage hung under it, and one ragged house-colour banner on
the brace.

EA's facts (WBFARRDEN mesh coordinates, measured; work/measure.json): WBFADen, 499 triangles on
WBFortress.tga (own copy WBFortresX.tga); x -45.52..24.77, |y| <= 24.97, z 0..89.33. The stalk is
an octagon about (-0.4, 0) with its corners on the axes and diagonals (corner radius 2.55 + 0.141 z),
a keel toward the brace; the bowl flares from r 10 at z 51 to the rim, r 22 at z 72.5; the eye
ring (EYES, r 12.9 about (-0.3, 0, 77.5), z 72.5..82.5) and the eight arrow bones at r 11.8, z 76.8
look out through the posts between the rim and the roof deck (z 87.4, r ~13; a boss to 89.3):
nothing new stands between r 11 and 25 from z 71 to 87. The brace: a post x -45.5..-38 (|y| < 2.5)
to z 53.2 and a beam from it to the stalk at z 36..50. Lifecycle: WBFADen_A (construction), _D2,
_D3. House colour: none of EA's; our own from the style's template (HOUSE_DRAW).
"""
from sagekit.building import Building

from ..style import GoblinStyle

STALK = (-0.4, 0.0)
SPIKE_TOP, SKULL_Z, SKULL_S = 106.0, 99.0, 4.6          # the roof's iron spike and its skull
POST = (-41.5, 0.0, 53.2)                               # the brace's post top
CAGE = (-26.0, 0.0, 35.5)                               # hung under the beam
BANNER = (-40.6, 49.0, 6.8, 20.0)                       # on the post's -y face: x, top, width, length
PILE = (8.5, -3.5)


def stalk_r(z):
    """The stalk's corner radius at height z."""
    return 2.55 + 0.141 * z


class ArrowDen(Building):
    style = GoblinStyle()
    source = "WBFADen"
    target = "WBFARRDEN"
    sheet = "WBFortress.tga"
    sheet_normal = "WBFortress_NRM.tga"
    own_textures = {"WBFortress.tga": "WBFortresX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the Goblin kit's unwrap overlaps a little: seams at EA's islands and 8-degree turns
    HOUSE_DRAW = "ModuleTag_Draw_HCArrowDen"
    views = {
        "rts": ((-10.4, 0.0, 48.0), 273, 50, -38, 50),
        "close": ((-10.4, 0.0, 50.0), 200, 20, -38, 45),
        "ingame": ((-10.4, 0.0, 44.7), 621, 53, -62, 50),
    }

    def design(self, kit):
        return self._pad(kit) + self._stalk(kit) + self._head(kit) + self._brace(kit)

    @staticmethod
    def _pad(kit):
        import math

        from . import pad
        box = (-45.5, 24.7, -24.9, 24.9)
        out = pad.skirt(kit, pad.ring(STALK, 4.6, 9, 0.2), STALK, r=2.8, h=2.6, pitch=2.8, out=0.8, seed=3, box=box)
        out += pad.skirt(kit, [(-44.0, 2.4), (-39.0, 2.4), (-39.0, -2.4), (-44.0, -2.4)], (-41.5, 0.0), r=2.2, h=2.0,
                         pitch=2.6, out=0.6, seed=5, box=box)
        z = 30.0
        out += pad.clasp(kit, STALK, 4, 13.5, stalk_r(z) - 0.5, z, r=1.8, bow=5.0, phase=math.pi / 4)
        for i in range(4):                      # a rock at each rib's foot
            a = math.pi / 4 + math.pi / 2 * i
            out += pad.rock(kit, (STALK[0] + 13.5 * math.cos(a), STALK[1] + 13.5 * math.sin(a)), 3.0, 3.0, seed=11 + i)
        out += kit.skull_pile(kit.V((PILE[0], PILE[1], 0.0)), 3.2, 3, 2.2, seed=2, face=(1, -0.6, 0))
        return out

    @staticmethod
    def _stalk(kit):
        import math
        V = kit.V
        out = []
        for z in (16.0, 40.0):
            out += kit.hoop(STALK, z, stalk_r(z) + 0.05, h=1.8, th=0.7, inner=1.4, phase=0.0)
        # a skull on an iron spike out of the stalk's front
        a = 0.0                                 # between the front ribs (+-45 degrees)
        d = V((math.cos(a), math.sin(a), 0.3)).normalized()
        base = V((STALK[0], STALK[1], 32.0)) + V((d.x, d.y, 0)) * (stalk_r(32.0) * 0.92 - 0.6)
        out += kit.spike(base, d, 8.0, 0.5, k=4, tip="gore")
        out += kit.skull(base + d * 4.4 + V((0, 0, 0.3)), V((d.x, d.y, 0)), 3.2, detail=1)
        return out

    @staticmethod
    def _head(kit):
        import math
        V, Z = kit.V, kit.Z
        c = V((STALK[0], STALK[1], 0))
        out = kit.hoop(STALK, 48.0, stalk_r(48.0) + 0.1, h=2.0, th=0.8, inner=1.5, phase=0.0)
        # bone fangs round the bowl's underside, below the eye ring, and skulls hung between them
        for i in range(16):
            a = 2 * math.pi * (i + 0.5) / 16
            rad = V((math.cos(a), math.sin(a), 0))
            base = c + rad * 19.3 + Z * 70.3
            length = 6.5 if i % 2 else 4.5
            out += kit.spike(base, rad * 0.35 - Z, length, 0.75, tag="bone", k=4, sink=0.8)
        for i in range(4):
            a = math.pi / 4 + math.pi / 2 * i - math.radians(20)
            rad = V((math.cos(a), math.sin(a), 0))
            top = c + rad * 18.8 + Z * 68.6
            out += kit.chain(top, top - Z * 3.2)
            out += kit.skull(top - Z * 4.6 + rad * 0.3, rad, 2.2, detail=0)
        # four great horns and four iron spikes round the roof deck, and the spike out of its middle with a skull on it
        out += kit.horn_crown(c, 86.6, 11.6, 4, 17.0, 1.9, rise=0.85, lean=0.45, phase=math.pi / 8, k=6, n=5)
        for i in range(1, 8, 2):
            a = 2 * math.pi * (i + 0.5) / 8
            rad = V((math.cos(a), math.sin(a), 0))
            out += kit.spike(c + rad * 11.2 + Z * 87.4, rad * 0.4 + Z, 6.5, 0.65, k=4, tip="gore")
        top = V((STALK[0], STALK[1], SPIKE_TOP))
        out.append(kit.tube([c + Z * 87.8, c + Z * 92.0, c + Z * SKULL_Z, top], [2.2, 1.7, 1.25, 0.0], "iron", k=6,
                            cap0="iron", cap1=None))
        out.append(kit.tube([c + Z * 88.4, c + Z * 90.2], [3.0, 2.7], "iron", k=8, cap0="iron", cap1="iron"))
        out += kit.skull(c + Z * SKULL_Z, V((1, -0.5, 0)), SKULL_S, detail=2)
        return out

    @staticmethod
    def _brace(kit):
        V = kit.V
        out = []
        x, y, z = POST
        out += kit.skull_on_spike(V((x, y, z - 1.0)), 6.5, 3.0, facing=(1, -0.6, 0))
        for i, bx in enumerate((-33.0, -26.5, -20.0)):
            out += kit.spike(V((bx, 0.0, 49.2 - 0.1 * i)), V((0.12, 0, 1)), 5.5 - 0.6 * i, 0.7, tag="bone", k=4)
        cx, cy, cz = CAGE
        out += kit.cage(V((cx, cy, cz - 2.0)), 7.0, 2.2, facing=(1, -0.7, 0), chain=2.0)
        bxu, top, w, length = BANNER
        out += kit.banner(V((0, -2.9, 0)), V((1, 0, 0)), V((0, -1, 0)), bxu, top, w, length, d=1.5, mark="eye")
        return out

    def decals(self):
        from ..paint import goblin_layers
        c = STALK
        anchors = [(c[0] + 0.5, c[1] - 0.3, SKULL_Z - 1.5, 2.0, 8.0), (POST[0], POST[1], POST[2] + 4.0, 1.8, 6.0),
                   (PILE[0], PILE[1], 0.8, 2.6, 2.0), (9.6, 0.0, 31.5, 2.0, 8.0)]
        return [goblin_layers()["Gore"](anchors)]

    def emphasis(self, c, n):
        return 1.3 if c.z > 45 else 1.0
