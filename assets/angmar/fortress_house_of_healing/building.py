"""Angmar House of Lamentation (AngmarFortressCitadel, EA's tag ModuleTag_HouseOfHealingDraw), pass 1:
EA's house over the citadel's gate kept whole, and its story told: on the wing's roofs either side of
its drum stand thralls frozen into pillars of ice, their heads and arms raised in lament breaking out
of the crystal (the bold mass); on the drum's top a cairn of black stone and ice with the cold fire
burning out of its crater, the house's lament-fire.

EA's KBFHoLa (objects AngmarFortressCitadel; role fortress_upgrade): body KBFHOLA, 754 triangles,
painted from KBFortressX.tga + KBFortressX_NRM.tga (DXT1).
In KBFHOLA mesh coordinates (the citadel's): x 34.17..71.90, y -42.80..43.71, z 40.38..138.73.
Other meshes (EA's, untouched): N_WINDOW 18 (GBNightWIndows.tga; x 42.3..67.3, y -29.7..12.5,
z 55.8..95.2).
Lifecycle models in its Draw module: KBFHoLa_A, KBFHoLa_D1, KBFHoLa_D2.
House colour: KBHCFortress.
EA's body measured: `python3 -m sagekit measure angmar/fortress_house_of_healing` ->
work/measure.json.

EA's facts (measured 2026-10-01, ray casts and loose parts of the model):
- Shown with UPGRADE_HOUSE_OF_HEALING on the citadel, in its coordinates: it sits on the curtain
  over the gate (+X). A round drum (r 12.8 round (55, 0)) rises from the gate's top (z 40.4) to a
  flat top at z 103.5 (x 42..68, |y| <= 12, small merlons round its rim at z 90..107); a curved wing
  (its front faces at r 67.6) runs round both sides of the drum to |y| 43, roofed at z 78 (x 44..64,
  |y| 14..43, sloping down to z 70 toward the well), EA's own icicle drips under its windows.
- Horns: two on the drum's top at (50, +-10) to z 126, one tall at the front (x 59..72, y +-5) to
  z 138.7, two on the wing roofs at (54, +-29) to z 97. EA's mist (HouseofLamentationsMist) plays at
  the object's origin in another Draw (ModuleTag_DrawHoLFX).
- The citadel's +X tine (fortress/crown.py, r 38..42 on the gate's axis, frozen from z ~93 to its
  point at z 120) stands against the drum's back (x 40.7..44, z 90..120): EA's body and that tine
  cross (295 faces); new faces here keep x >= 47 above z 85.
"""
from sagekit.building import Building

from ..style import AngmarStyle

# Real fire: (x, y, z, kind) in KBFHOLA mesh coordinates, from the design (kit.fire's log)
FIRE_POINTS = [(55.0, 0.0, 113.0, 'coldfire')]

TOP, WING = 103.5, 78.0
PYRE = (55.0, 0.0, TOP)
# the frozen thralls on the wing roofs: (x, y, facing degrees, height)
CAPTIVES = [(55.5, 21.5, 20.0, 17.0), (53.5, 35.5, 40.0, 15.0), (55.5, -21.5, -20.0, 17.0), (53.5, -35.5, -40.0, 15.0)]


def lament(kit):
    import math

    from ..shapes_addons import cairn, frozen_captive
    out = cairn(kit, PYRE, 4.6, 10.0, kind="coldfire", seed=3.0, n=10, rim=5)
    for i, (x, y, deg, h) in enumerate(CAPTIVES):
        a = math.radians(deg)
        out += frozen_captive(kit, (x, y, WING), (math.cos(a), math.sin(a)), h=h, seed=i * 1.9)
    return out


class FortressHouseOfHealing(Building):
    style = AngmarStyle()
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): one small cold flame on the drum. 3.0 live (was 12.3).
    fire_points = [(55.0, 0.0, 113.0, 'coldtorch')]
    source = "KBFHoLa"
    target = "KBFHOLA"
    sheet = "KBFortressX.tga"
    sheet_normal = "KBFortressX_NRM.tga"
    own_textures = {"KBFortressX.tga": "KBFortressN.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_HouseOfHealingDraw",)
    views = {
        "rts": ((53.0, 0.5, 89.6), 300, 50, -38, 50),
        "close": ((55.0, 0.0, 92.0), 150, 35, -30, 45),
        "ingame": ((53.0, 0.5, 89.6), 682, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        return logged(kit, lambda k: k.retag(lament(k)))
