"""Isengard fortress wizards tower (IsengardFortressCitadel): Orthanc. EA's octagonal tower kept whole,
four many-sided piers on its diagonals opening into horns at the summit, ember windows, a door
with the White Hand, Saruman's balcony, the Hand high on three faces, braziers (orthanc.py).

EA's IBFWTower (objects IsengardFortressCitadel; role fortress_upgrade): body IBFWTOWER, 1572
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFWTOWER mesh coordinates: x -21.79..21.79, y -21.79..21.79, z -0.00..175.69.
Lifecycle models in its Draw module: IBFWTower_A, IBFWTower_D1, IBFWTower_D2, IBFWTower_D3.
House colour: IBHCFortress.
EA's body measured: `python3 -m sagekit measure isengard/fortress_wizards_tower` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_monument (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in the target's
# coordinates, collected from the design (kit.flames / kit.fire record them when the kit has a
# `fire_log` list); run again after moving a fire.
FIRE_POINTS = [
    (13.8, 13.8, 79.2, 'brazier'), (-13.8, 13.8, 79.2, 'brazier'), (-13.8, -13.8, 79.2, 'brazier'),
    (13.8, -13.8, 79.2, 'brazier'), (14.0, -3.4, 97.5, 'brazier'), (14.0, 3.4, 97.5, 'brazier')
]


class FortressWizardsTower(Building):
    style = IsengardStyle()
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): the upper pair a torch flame each. 6.0 live (was 35.8).
    fire_points = [(14.0, -3.4, 97.5, 'torch'), (14.0, 3.4, 97.5, 'torch')]
    source = "IBFWTower"
    target = "IBFWTOWER"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresN.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawWizardsTower",)
    footprint_margin = 1.0              # the doorway's frame on the battered +X face (collision is the INI's)
    views = {
        "rts": ((0.0, 0.0, 100.0), 460, 50, -38, 50),
        "close": ((0.0, 0.0, 160.0), 215, 26, -30, 45),
        "foot": ((0.0, 0.0, 45.0), 190, 20, -30, 45),
        "ingame": ((0.0, 0.0, 100.0), 931, 53, -62, 50),
    }

    def design(self, kit):
        from . import orthanc
        return orthanc.build(kit)
