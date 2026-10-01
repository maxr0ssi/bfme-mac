"""Angmar sanctum (AngmarFortressCitadel, ModuleTag_SanctumDraw), pass 1: EA's sorcerer's tower kept
whole, rising out of the citadel's cairn in the heart of the crown, and frozen by its own sorcery: a
collar of ice crystals bursts up between the six fins over its skirt, round its waist under the
crown, level with the frozen tips of the citadel's tines round it: six blooms, each a crater of
crystal, the cold fire burning in every other one (the bold mass). Its foot stands in the citadel's
cairn; nothing new goes there (a collar of shards tried in pass 1 only added to the cairn's
crossing and is hidden by the curtain at the RTS view).

EA's KBFSanctum (objects AngmarFortressCitadel; role fortress_upgrade): body KBFSANCTUM, 1452
triangles, painted from KBFortressB.tga + KBFortressB_NRM.tga (DXT5, cut-out alpha: our texture
is DXT5).
In KBFSANCTUM mesh coordinates (the citadel's): x -19.09..19.09, y -20.33..20.33, z 0.00..175.38.
Lifecycle models in its Draw module: KBFSanctum_A, KBFSanctum_D1, KBFSanctum_D2, KBFSanctum_D3.
House colour: KBHCFortress.
EA's body measured: `python3 -m sagekit measure angmar/fortress_sanctum` -> work/measure.json.

EA's facts (measured 2026-10-01, ray casts and loose parts of the model):
- Shown with UPGRADE_IVORY_TOWER in the middle of the citadel's well, six-fold: a plinth (r 17.3,
  z 0..12), a shaft (r 15.9, z 13..78) with six ribs (r 18.1, at 0, 60, .. degrees, z 42..74); a
  skirt roof sloping from r 20 at z 78 to r 11.6 at z 98, its six ridge blades at 30, 90, ..
  degrees; six fins (r 15.5, z 97.5..114.6), a ledge (z 98), a drum (r 11.6, z 115..118); the
  crown: a dome to z 131 inside six horns, three to z 175.4 and three to z 153.8.
- Bones EYEBONE (0, 0, 173.9) and EYEBONE01 (0, 0, 147.7): EA's AngSanctumCharge systems while it
  fires (UNPACKING) and its weapon's launch bone. Kept clear (nothing new above z 118).
- The citadel's cairn (fortress/crown.py: r 17 round (0, 0, 9.9), to z ~64) and its cold fire
  (0, 0, 51.9) are where the shaft stands: EA's body and the cairn cross (180 faces).
"""
from sagekit.building import Building

from ..style import AngmarStyle

# Real fire: (x, y, z, kind) in KBFSANCTUM mesh coordinates, from the design (kit.fire's log)
FIRE_POINTS = [(13.1, 0.0, 101.9, 'coldflame'), (-6.5, 11.3, 101.9, 'coldflame'), (-6.5, -11.3, 101.9, 'coldflame')]

# the ice blooms on the ledge over the skirt (z 98, between the fins at 30, 90, .. degrees): (deg, r, z)
BLOOMS = [(60.0 * i, 12.2, 98.0) for i in range(6)]


def blooms(kit):
    import math

    from mathutils import Vector as V
    out = []
    for i, (deg, r, z) in enumerate(BLOOMS):
        a = math.radians(deg)
        e = V((math.cos(a), math.sin(a), 0))
        c = V((0, 0, z)) + e * r
        up = (V((0, 0, 1)) + e * 0.22).normalized()        # up between the fins, leaning out a little
        big = i % 2 == 0
        out += kit.ice_cluster(c, 3.0, 20.0 if big else 15.0, n=9, up=up, seed=10.0 + i * 3.1, lean=0.3, thick=0.2,
                               hollow=2)
        if big:
            kit.fire(c + up * 4.0, "coldflame")
    return out


class FortressSanctum(Building):
    style = AngmarStyle()
    fire_points = FIRE_POINTS
    source = "KBFSanctum"
    target = "KBFSANCTUM"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressP.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the unwrap overlapped (0.06%): seams at EA's islands and 8-degree turns
    parts = ("ModuleTag_SanctumDraw",)
    views = {
        "rts": ((0.0, -0.0, 87.7), 405, 50, -38, 50),
        "close": ((0.0, 0.0, 95.0), 150, 35, -38, 45),
        "ingame": ((0.0, -0.0, 87.7), 920, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        return logged(kit, lambda k: k.retag(blooms(k)))
