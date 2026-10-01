"""The Isengard citadel (IsengardFortressCitadel, IsengardFortress), pass 2 "Orthanc's forge":
EA's body kept whole - the 16-sided curtain, the wedge towers with their arcaded faces and spiked
points, the gatehouse, the pit of the courtyard - and made Saruman's war-works. The back tower is
wrapped from the ground into a foundry of faceted black stone with silver arrises, a great White
Hand on its courtyard face, a crane arm with a crucible, a bellows house and the great stack
(foundry.py); two more stacks on the side walks; forges, a gantry, Uruk shield racks, pipework
and fire grates on the walks; felled Fangorn, the Isen's flume and water wheel driving gears, and
scaffolding round a half-built siege ladder outside (yard.py); spikes and two heavy banners
(walls.py).

EA's facts (IBFORTRESS mesh coordinates, identity bone; work/measure.json): x -74.16..84.76,
y -74.16..74.16, z -0.06..91.41, mirror-symmetric in y. Kept clear: the courtyard, where the
upgrades stand (the wizard's tower IBFWTower at the centre, r 21.8, to z 175.7; the excavations
to r 54, z 12..91.8; the burning forges over the -X wall, x -70..-19, |y| < 29, z 0..124); the
orcfire munitions' cauldrons on the four tower tops ((+-37.4, +-37.7), z 80.2..93.7, fire to 110);
the gate opening (x > 73, |y| < 11, z < 43). IBFORTRESSB (48 triangles) stays EA's.

Shape preview only: no bake, paint or build yet.
"""
import os

from sagekit.building import Building
from sagekit.taxonomy import Tier

from ..style import IsengardStyle


# Where real fire goes, for the fire job (the game's particle systems on bones, ParticleSysBone):
# (x, y, z, kind) in IBFORTRESS mesh coordinates, the point the flame rises from - a chimney's
# throat, a furnace's mouth, a hearth's bed, a crucible's brim, a brazier's embers, a grate's pit.
# Kinds: chimney, furnace, hearth, crucible, brazier, grate. Collected from the design (every
# kit.flames / kit.fire_grate call records its point when the kit has a `fire_log` list); run
# again after moving a fire.
FIRE_POINTS = [
    (-60.6, 60.6, 99.5, 'chimney'), (0.0, -61.5, 97.5, 'chimney'), (0.0, 61.5, 97.5, 'chimney'),
    (-10.0, 57.5, 49.6, 'furnace'), (0.0, -53.6, 49.5, 'furnace'), (-24.5, 57.2, 50.9, 'hearth'),
    (12.7, 59.7, 51.1, 'hearth'), (1.3, 41.1, 76.8, 'crucible'), (15.1, 55.5, 50.7, 'crucible'),
    (15.4, -58.5, 56.5, 'crucible'), (-18.3, -53.1, 52.0, 'brazier'), (3.9, 56.1, 52.0, 'brazier'),
    (18.3, -53.1, 52.0, 'brazier'), (51.3, -22.9, 52.0, 'brazier'), (53.0, 18.8, 52.0, 'brazier'),
    (-68.5, 46.5, 1.2, 'grate'), (-47.0, 68.0, 1.2, 'grate'), (-18.4, 51.2, 1.2, 'grate'),
    (14.1, -58.8, 49.0, 'grate'), (56.2, -21.0, 49.0, 'grate')
]


# The tweak options (tweaks.py, 2026-09-30): Max picked D2 (no needle stacks, no tall pair, Orthanc
# horns on the corner towers and a horned crown on EA's tower point); ISENGARD_CITADEL=A|B|C|D previews
# another, ISENGARD_CITADEL=OLD the design before. Their fire points, from the design's fire log (shapes_industry.logged):
# the installed points without the three needle stacks' chimneys, a crucible on the -Y walk, and
# what stands where the side stacks stood.
_KEPT = [p for p in FIRE_POINTS if p[3] != "chimney"] + [(-4.4, -63.2, 50.9, 'crucible')]
_HEARTH = {sy: (0.0, sy * 61.5, 51.3, 'hearth') for sy in (1, -1)}
CITADEL_FIRE = {
    "A": _KEPT + [_HEARTH[1], _HEARTH[-1]],
    "B": _KEPT + [(0.0, 61.5, 95.2, 'chimney'), _HEARTH[-1]],
    "C": _KEPT + [_HEARTH[1], _HEARTH[-1]],
    "D": _KEPT + [_HEARTH[1], _HEARTH[-1]],                     # the pair had no fire points
    "D2": _KEPT + [_HEARTH[1], _HEARTH[-1], (-56.6, 56.8, 94.3, 'brazier')],     # the point crown's fire-pot
}


CITADEL = "D2"


def option():
    o = os.environ.get("ISENGARD_CITADEL", CITADEL).upper()
    return "" if o == "OLD" else o


def fire_points():
    """The installed design's points, or the ISENGARD_CITADEL option's."""
    return CITADEL_FIRE.get(option(), FIRE_POINTS)


class Fortress(Building):
    style = IsengardStyle()
    source = "IBFortress"
    target = "IBFORTRESS"
    tier = Tier.HERO
    fire_points = fire_points()
    max_z_growth = 0.35                 # D2's tower crown to z 109 (+19 %; the old great stack reached 118): EA's citadel is low (91.4)
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((5.3, -0.0, 45.7), 519, 50, -38, 50),
        "close": ((5.3, -0.0, 45.7), 307, 24, -30, 45),
        "keep": ((-38.0, 38.0, 58.0), 240, 24, -38, 50),
        "ingame": ((5.3, -0.0, 45.7), 1179, 53, -62, 50),
    }

    def design(self, kit):
        from . import foundry, tweaks, walls, yard
        opt = option()
        if opt in ("A", "B", "C", "D", "D2"):                # a tweak option's shape preview (tweaks.py)
            from ..shapes_industry import logged
            return logged(kit, lambda k: tweaks.design(k, opt))
        return foundry.build(kit) + walls.build(kit) + yard.build(kit)

    def emphasis(self, c, n):
        if c.z > 70:
            return 1.3                        # the foundry's top and the stacks
        return 1.0
