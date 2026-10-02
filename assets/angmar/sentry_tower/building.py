"""Angmar sentry tower (AngmarSentryTower), pass 1: EA's hexagonal tower kept whole and crowned as the
citadel is crowned, small: three forged iron tines with frozen tips rise from its flat roof between
EA's horns, round a cairn of black stone and ice with the cold fire burning out of its crater.

EA's KBBtlTwr (objects AngmarSentryTower, a ChildObject of AngmarSentryTower_Independent in the same
file; role tower): body BASE, 1527 triangles, painted from KBBtlTwr.tga + KBBtlTwr_Nrm.tga (DXT1).
In BASE mesh coordinates: x -28.15..25.11, y -30.92..32.06, z -0.08..128.53.
Other meshes (EA's, untouched): N_WINDOW 4 (GBNightWIndows.tga; x 10..18, y -15..-1, z 15..34).
Lifecycle models in its Draw module: KBBtlTwr_A, KBBtlTwr_D1, KBBtlTwr_D2, KBBtlTwr_D3.
House colour: KBHCBtlTwr. EA's body measured: `python3 -m sagekit measure angmar/sentry_tower`.

EA's facts (measured 2026-10-01, ray casts on the model):
- A hexagonal shaft, the faces at r 15.8..16.8 (normals at 0, 60, .. degrees), from the ground to a
  flat roof at z 85.96 open to the sky (r <= 14 across it): nothing stands on it.
- Six blades hug the hexagon's corners: three tall horns at 90, 210 and 330 degrees (r ~20, z 42 to
  122.9..128.5) and three shorter blades at 30, 150 and 270 degrees (r ~20, z 74.6 to ~110).
- Arrow bones ARROW01..12 in the walls' windows at z 45.2 and 67.8 (r 12..18); the doorway and steps
  on the -X side at the foot. The garrison shoots from the windows; the roof is no firing position.
"""
from sagekit.building import Building

from ..style import AngmarStyle

# Real fire: (x, y, z, kind) in BASE mesh coordinates, from the design (kit.fire's log in work/logs/*geometry.log)
FIRE_POINTS = [(0.0, 0.0, 93.6, 'coldfire')]

ROOF = 85.96
# three tines on the hexagon's short-blade corners (EA's tall horns stand on the other three): (deg, r)
TINES = [(30.0, 8.0), (150.0, 8.0), (270.0, 8.0)]
H, W = 36.0, 5.2


def crown(kit):
    from ..shapes_addons import cairn, tine_crown
    out = tine_crown(kit, (0.0, 0.0), ROOF, TINES, H, W, seed=1.0)
    out += cairn(kit, (0.0, 0.0, ROOF), 3.6, 8.0, kind="coldfire", seed=2.0)
    return out


class SentryTower(Building):
    style = AngmarStyle()
    fire_points = FIRE_POINTS
    source = "KBBtlTwr"
    target = "BASE"
    sheet = "KBBtlTwr.tga"
    sheet_normal = "KBBtlTwr_Nrm.tga"
    own_textures = {"KBBtlTwr.tga": "KBBtlTwH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    lifecycle = {"KBBtlTwr_D3": {"backs": (0.13, "the collapse's first frames: the cut blades' and spikes' "
                                              "inner faces, 12.2% past EA's; the RTS renders show no hole and "
                                              "every piece is under the ground at its end")}}
    views = {
        "rts": ((-1.5, 0.6, 64.2), 336, 50, -38, 50),
        "close": ((0.0, 0.0, 100.0), 130, 42, -38, 45),          # the crown
        "ingame": ((-1.5, 0.6, 64.2), 764, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        return logged(kit, lambda k: k.retag(crown(k)))
