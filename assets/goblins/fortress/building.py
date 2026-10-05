"""The Goblin citadel (WildFortressCitadel, WildFortress): EA's body kept whole - the four plated
spire towers with their horn-scaled hoods and glowing eyes, the black-draped curtain walls, the
dragon's head over the gate and the stone tongue of its ramp - and made a Goblin warlord's hall in
blood, iron and bone: the spires crowned with iron hoops, great horns and bleached tusks, iron
spikes to z 136 each with a skull driven onto it, a gibbet cage off each front spire and a flayed
hide off each back one (crown.py); the walls crowned with a leaning palisade of sharpened stakes
with skulls on them, a horned-skull totem over each wall's middle buttress, crimson hides daubed
with white war paint hung down the walls (this module); the gate framed by two great tusks, bone
fangs along the tongue, skull piles, impaled skeletons, fire bowls and two ragged banners
(gate.py). Three house-colour banners in all.

WBFORTRESS mesh coordinates (identity bone frame). EA's facts, measured (work/measure.json and
the sections in crown.py and gate.py): x -65.01..70.79, y -64.97..65.00, z 0..116.86; the curtain
walls' outer faces at |c| 43.4..45.3 (the drapes), their tops an outer lip at |c| 44.2 (z 56.5)
over a walk at z 55.2 reaching in to |c| 30; each wall's middle buttress rises to a horn at
|c| 47..52, z 63.3 (the -X, +Y and -Y walls); the courtyard (the throne upgrade WBFGThrone,
x -35..40, |y| <= 25, z 0..173.5, and the fire drake's perch P1 at z 74.8) stays clear; the razor
spines upgrade (WBFRSpin) rings the base outside r 70; EYES (the glowing eyes) stays EA's.
"""
from sagekit.building import Building
from sagekit.taxonomy import Tier

from ..style import GoblinStyle

WALL, LIP, WALK = 44.2, 45.3, 55.2          # the walls' top lip, their outer face (for hangings), the walk
# (anchor, along, out, [(u0, u1) palisade runs]) of the side and back walls
WALLS = [((0, -WALL, 0), (1, 0, 0), (0, -1, 0)), ((0, WALL, 0), (-1, 0, 0), (0, 1, 0)),
         ((-WALL, 0, 0), (0, -1, 0), (-1, 0, 0))]
RUNS = [(-30.5, -5.2), (5.2, 30.5)]
# the hangings on each wall (the same order as WALLS): (u, kind); "banner" is house colour
HANGINGS = [((-17.0, "hand"), (17.0, "banner")), ((-17.0, "claw"), (17.0, "eye")), ((-17.0, "eye"), (17.0, "fangs"))]
HIDE = (53.5, 9.0, 17.5)                    # top, width, length
TOTEM = (40.0, 15.5, 4.3)                   # |c| of its foot, height, skull size
# The game's fire (sagekit/fire.py): the coals of the two fire bowls on the front walk either side
# of the dragon's head (gate.py: kit.brazier at (39.5, +-27, 55.2), h 3.2). EA's citadel burns
# nowhere near them (its smoke is on the fire-arrow upgrade's spire tops, its embers on the throne).
FIRE_POINTS = [(39.5, 27.0, 58.7, 'brazier'), (39.5, -27.0, 58.7, 'brazier')]


class Fortress(Building):
    style = GoblinStyle()
    source = "WBFortress"
    target = "WBFORTRESS"
    tier = Tier.HERO
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): the gate's two braziers a torch flame each. 6.0 live (was 11.9).
    fire_points = [(39.5, 27.0, 58.7, 'torch'), (39.5, -27.0, 58.7, 'torch')]
    sheet = "WBFortress.tga"
    sheet_normal = "WBFortress_NRM.tga"
    own_textures = {"WBFortress.tga": "WBFortresH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                      # EA's own layout overlapped (0.73%): seams at its islands and 8-degree turns
    views = {
        "rts": ((2.9, 0.0, 62.0), 520, 50, -38, 50),
        "close": ((2.9, 0.0, 64.0), 310, 24, -30, 45),
        "gate": ((52.0, 0.0, 34.0), 175, 12, -14, 45),
        "crown": ((44.2, -44.2, 96.0), 125, 18, -40, 45),
        "ingame": ((2.9, 0.0, 58.4), 1107, 53, -62, 50),
    }

    def design(self, kit):
        from . import crown, gate
        out = []
        for c in crown.TOWERS:
            out += crown.build(kit, c)
        out += self._walls(kit)
        out += gate.build(kit)
        return out

    @staticmethod
    def _walls(kit):
        """The palisade crowns, the totems and the hangings of the side and back walls."""
        from mathutils import Vector as V
        out = []
        for w, ((a, t, n), hangings) in enumerate(zip(WALLS, HANGINGS)):
            a, t, n = V(a), V(t), V(n)
            for i, (u0, u1) in enumerate(RUNS):
                out += kit.palisade(a, t, n, u0, u1, WALK, 8.0, d=-1.5, pitch=3.4, r=0.8, lean=0.22,
                                    skulls=(4,) if i == w % 2 else (), skull=2.6, seed=w * 2 + i)
            foot, height, s = TOTEM
            out += kit.totem(n * foot + V((0, 0, WALK - 1.0)), height + 1.0, s, facing=n, skulls=0)
            face = n * LIP
            for u, kind in hangings:
                top, width, length = HIDE
                if kind == "banner":
                    out += kit.banner(face, t, n, u, top - 1.0, width - 1.5, length + 2.0, d=1.6, mark="hand")
                else:
                    out += kit.hide_panel(face, t, n, u, top, width, length, d=0.4, mark=kind)
        return out

    def decals(self):
        from ..paint import goblin_layers
        from . import crown, gate
        anchors = [g for c in crown.TOWERS for g in crown.gore_anchors(c)] + gate.gore_anchors()
        return [goblin_layers()["Gore"](anchors)]

    def emphasis(self, c, n):
        if c.z > 66:
            return 1.3                        # the spire crowns: horns, hoops, skulls, cages
        if c.x > 44 and abs(c.y) < 36:
            return 1.3                        # the gate front
        return 1.0
