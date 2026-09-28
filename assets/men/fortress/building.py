"""The Gondor citadel (MenFortressCitadel, MenFortress): EA's body kept whole - the four domed
towers with their belfries, the curtain walls with their corbel arcades, the sunken courtyard and
the gate - and crowned the way of Minas Tirith: machicolated galleries with square merlons and
corner bartizans round every tower top (crown.py), steel-ribbed domes under lantern cupolas, gilt
orbs and tall steel spikes; crenellated parapets on the curtain walls with pinnacles over EA's
buttresses; a gatehouse front of pilasters, a voussoir archivolt with its keystone, portcullis
teeth, a black frieze with the seven stars and a pediment with the White Tree under a winged
crest (gate.py). Four house-colour banners on the front towers, White Tree shields on the back.

Coordinates are GBFORTRESS's mesh frame (identity). EA's towers stand at (+-39.88, +-39.8), shafts
half 13.05 (outer faces x, y = +-52.93, +-52.85), curtain walls' outer faces at +-49.01 up to
the corbelled walk (overhang to 50.9 at z 48, walk top 49.5 over 47.4..50.2 for |along| <= 20.8,
then a step up to z 54). EA's side and back walls carry buttresses at |along| 11..15.2. The
upgrades drawn at the same origin: the Ivory Tower (centre, |x|, |y| <= 17), the healing house
(x 28.7..48.8, |y| <= 28.5, from the walk), the oil works (outlets on the walls at |along|
19.5..26.4, z 26..38.9; cauldrons on the back walk), the flame hardware on the middle of every
outward tower face (z 59.8..73.5, 7 out), the banner upgrade's pennants (GBFFLAG, from the tower
poles at z 105..112) and the doors (gate.py)."""
import math

from sagekit.building import Building
from sagekit.taxonomy import Tier

from ..style import MenStyle

TOWERS = [(x, y) for x in (39.88, -39.88) for y in (39.8, -39.8)]
FACE = 13.05
WALL, RUN, PIN_U = 49.01, 20.6, 13.1         # curtain walls' outer face, parapet half-run, pinnacles
# (anchor, along, out) of the side and back curtain walls
WALLS = [((0, WALL, 0), (1, 0, 0), (0, 1, 0)), ((0, -WALL, 0), (1, 0, 0), (0, -1, 0)),
         ((-WALL, 0, 0), (0, 1, 0), (-1, 0, 0))]
BANNER = (57.6, 6.8, 24.5)                    # z_top (under the flame hardware), width, length
SHIELD = (41.5, 5.2, 14.8)                    # z of the point, half-width, height


class Fortress(Building):
    style = MenStyle()
    source = 'GBFortress'
    target = 'GBFORTRESS'
    own_model = 'GBFortress2'
    own_textures = {'GBFortress1.tga': 'GBFortressH.tga'}
    parts = ('ModuleTag_MainDraw', 'ModuleTag_01')
    tier = Tier.HERO
    bake_hidden = ('GBFFLAG', 'FIREGLOW', 'FLAMES', 'GBFFLAMING')
    views = {'rts': ((0, 0, 65), 480, 50, -38, 50),
             'close': ((3, 0, 68), 350, 25, -32, 45),
             'gate': ((52, 0, 36), 160, 12, -12, 45),
             'crown': ((39.88, -39.8, 92), 115, 20, -38, 45),
             'ingame': ((0, 0, 45), 1000, 53, -62, 50)}

    def house_shared(self, install, model):
        # Arnor's fortress draws GBHCFortress too (sagekit.ownership counts Arnor as Men): our banners
        # hang on our own body (GBFortress2), so they go to an own copy, GBHCFortress2
        return True

    def design(self, kit):
        from . import crown, gate
        out = []
        for cx, cy in TOWERS:
            out += crown.build(kit, cx, cy)
        out += self._parapets(kit)
        out += gate.build(kit)
        out += self._heraldry(kit)
        return out

    @staticmethod
    def _parapets(kit):
        """Crenellated parapets on the side and back walls' outer edge, a string course under them,
        and a pinnacle over each of EA's buttresses."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz
        out = []
        for a, t, n in (map(V, w) for w in WALLS):
            out.append(prism_uz(a, t, n, [(-RUN, 48.0), (RUN, 48.0), (RUN, 51.8), (-RUN, 51.8)], 0.2, 1.9,
                                [None, "stoneB", "top", "stoneB"], "stoneA", "stoneA"))
            out.append(prism_uz(a, t, n, [(-RUN, 47.6), (RUN, 47.6), (RUN, 48.5), (-RUN, 48.5)], 1.8, 2.3,
                                ["stoneB", "stoneB", "top", "stoneB"], "course", None))
            for u0, u1 in ((-RUN, -PIN_U - 1.45), (-PIN_U + 1.45, PIN_U - 1.45), (PIN_U + 1.45, RUN)):
                out += kit.merlons(a, t, n, u0, u1, 51.8, 0.3, 1.9, w=2.4, gap=1.8, h=3.0)
            for u in (-PIN_U, PIN_U):
                c = a + t * u + n * 1.05
                out += kit.pinnacle(c.x, c.y, 48.0, 57.0, half=1.2, spire=4.6)
        return out

    @staticmethod
    def _heraldry(kit):
        """House-colour banners on the front towers' outward faces, hung under the flame upgrade's
        hardware; White Tree shields on the back towers' outward faces."""
        from mathutils import Vector as V
        out = []
        for cx, cy in TOWERS:
            sx, sy = math.copysign(1, cx), math.copysign(1, cy)
            faces = [(V((cx + sx * FACE, cy, 0)), V((0, 1, 0)), V((sx, 0, 0))),
                     (V((cx, cy + sy * FACE, 0)), V((1, 0, 0)), V((0, sy, 0)))]
            for a, t, n in faces:
                if cx > 0:
                    out += kit.banner(a, t, n, 0.0, *BANNER)
                else:
                    z, half, height = SHIELD
                    out += kit.shield(a, t, n, 0.0, z, half, height)
        return out

    def decals(self):
        from ..paint import men_layers
        return [men_layers()[2]()]                 # silver stars on the towers' black gallery bands

    def emphasis(self, c, n):
        if c.z > 70:
            return 1.35                       # tower crowns, domes, lanterns
        if c.x > 53 and abs(c.y) < 22:
            return 1.35                       # the gatehouse front
        return 1.0
