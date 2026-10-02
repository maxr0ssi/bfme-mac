"""Mordor fortress fire arrows (MordorFortressCitadel): EA's clawed fire-pod on its eight legs over the
gatehouse, kept whole and made one of the citadel's crowns in small: six jagged, hooked spikes rise
from inside the pod's rim, between EA's twelve, and close over a bed of embers and a real fire; a
hooked barb off every leg.

EA's MBFFArrows (objects MordorFortressCitadel; role fortress_upgrade): body MBFFARROWS, 376
triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In MBFFARROWS mesh coordinates: x 32.60..51.58, y -9.49..9.49, z 59.96..89.84.
Other meshes (EA's, untouched): FLAMES 8 (EXFireTorchSeq.tga); FIREGLOW 4 (PG02.tga).
Lifecycle models in its Draw module: MBFFArrows_A, MBFFArrows_D1, MBFFArrows_D2, MBFFArrows_D3.
House colour: MBHCFortress.
EA's body measured: `python3 -m sagekit measure mordor/fortress_fire_arrows` ->
work/measure.json.

EA's facts (measured 2026-09-30, work/measure.json and the model's vertices): the pod's axis at
(42.1, 0.0) (EA's bone GLOWBONE01 at (43.2, 0.05, 80.3), where EA's SmokeDwfFort starts); eight legs
from the gatehouse roof (z 60, r 7.2..10.5 round (43.1, 0.1), at 0, +-50, +-97, +-140, 180 degrees)
to the pod's belly (z 72..76, r 3..6); the pod's rim at z 80.6..81.1 (r 3..6.6), a bed at z 80.8,
twelve spikes from the rim (z 83, r 5.2..7.2) leaning in to z 89.8 (r 2.3..4.4) at -180, -154,
-127, -99, -69, -36, -1, 35, 69, 100, 128, 155 degrees. EA's flame cards FLAMES (two crossed
planes, x 34.1..52.1, |y| < 9.2, z 77..95) and FIREGLOW (a plane at x 44.5, z 70..101) are kept in
game and left out of renders (bake_hidden). Footprint x 32.6..51.58, |y| < 9.49; the citadel's
frontispiece is at x 57.3, its parapet spikes at |y| > 14.5: clear.
"""
from sagekit.building import Building

from ..style import MordorStyle


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in MBFFARROWS mesh
# coordinates, collected from the design (the kit's fire log, printed as FIRE_POINTS in the geometry log)
FIRE_POINTS = [(42.1, 0.0, 82.0, 'brazier')]


class FortressFireArrows(Building):
    style = MordorStyle()
    fire_points = FIRE_POINTS
    bake_hidden = ("FLAMES", "FIREGLOW")        # EA's flame cards: kept in game, left out of bakes and renders
    source = "MBFFArrows"
    target = "MBFFARROWS"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresB.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    # EA remodelled the really damaged pieces: cut, 13% open backs (sagekit/lifecycle.py `fill`)
    lifecycle = {"MBFFArrows_D2": {"fill": True}}
    parts = ("ModuleTag_DrawFireArrows",)
    views = {
        "rts": ((42.1, -0.0, 76.0), 120, 50, -38, 50),       # EA's view, drawn back to show the whole pod
        "close": ((42.1, -0.0, 79.0), 80, 18, -30, 45),
        "ingame": ((42.1, -0.0, 74.9), 201, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged

        from . import pod
        return logged(kit, lambda k: k.retag(pod.build(k)))
