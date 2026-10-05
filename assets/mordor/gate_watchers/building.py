"""Mordor gate watchers (MordorGateWatchersExpansion): EA's gate and its three-headed Watcher kept whole; the
Watchers wake: witch-light in their six eyes (the one green accent), barbed teeth in the gate's arch,
fire baskets on its wall (watchers.py).

EA's GWatchers (objects MordorGateWatchersExpansion; role hall_expansion): body GWATCHERS, 1271
triangles, painted from MBFortress.tga + MBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In GWATCHERS mesh coordinates: x -65.75..-3.10, y -17.37..17.37, z -0.39..59.05.
Other meshes (EA's, untouched): BIB 92 (MBFortress.tga).
Lifecycle models in its Draw module: GWatchers_A, GWatchers_D2, GWatchers_D3.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure mordor/gate_watchers` -> work/measure.json.

EA's facts (measured 2026-09-30, work/measure.json and the model's vertices), in the expansion's own
frame (its pad turns +X outward, the gate's -X end against the citadel): the gate wall along x (faces
y +-7.52, z 0..32, x -65.75..-30.49, a taller end at x -65.75..-55 to z 57), its arch (x
-62.75..-30.75, to z 24); the Watcher on its plinth, three identical vulture heads a quarter turn apart
round the axis (-20.5, 0) facing +X, +Y and -Y (skull 8.5 out at z 59, beak tip 17.4 out at z 55, the
eye socket 9.3 out and 3.05 to each side at z 56..57.3); EA's base plate BIB (x -42.3..-5.6, |y| <
15.1, z 0..9.8), untouched. Mirror-symmetric in y.
"""
from sagekit.building import Building

from ..style import MordorStyle


# Real fire: (x, y, z, kind) in the target's mesh coordinates, from the design (the kit's fire log)
FIRE_POINTS = [(-48.0, 0.0, 37.3, 'brazier'), (-36.5, 0.0, 37.3, 'brazier')]


class GateWatchers(Building):
    style = MordorStyle()
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): the two braziers a torch flame each. 6.0 live (was 11.9).
    fire_points = [(-48.0, 0.0, 37.3, 'torch'), (-36.5, 0.0, 37.3, 'torch')]
    source = "GWatchers"
    target = "GWATCHERS"
    sheet = "MBFortress.tga"
    sheet_normal = "MBFortress_NRM.tga"
    own_textures = {"MBFortress.tga": "MBFortresF.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the unwrap overlapped (0.15%): seams at EA's islands and 8-degree turns
    HOUSE_DRAW = "ModuleTag_Draw_HCGateWatchers"
    views = {
        "rts": ((-34.4, -0.0, 29.3), 205, 50, -38, 50),
        "close": ((-34.4, -0.0, 29.3), 121, 24, -30, 45),
        "ingame": ((-34.4, -0.0, 29.3), 465, 53, -62, 50),
        "heads": ((-18.0, 0.0, 52.0), 60, 18, -40, 45),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged

        from . import watchers
        return logged(kit, lambda k: k.retag(watchers.build(k)))
