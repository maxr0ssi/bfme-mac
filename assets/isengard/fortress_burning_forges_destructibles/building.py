"""Isengard fortress burning forges destructibles (IsengardFortressCitadel): the forge tower (folder
renamed from EA's tag spelling, ModuleTag_DrawBurningForgesDescrutbiles). EA's body kept whole; EA's
round stack carried on as the citadel's needle chimney to z 138, a beacon, a forge, a molten
chute, fins and vents, real fire (forge.py).

EA's IBFBForgB (objects IsengardFortressCitadel; role fortress_upgrade): body IBFBFORGES, 971
triangles, painted from IBFortress.tga + IBFortress_NRM.tga (DXT5, cut-out alpha: our texture is
DXT5).
In IBFBFORGES mesh coordinates: x -70.40..-19.33, y -29.45..25.43, z -0.00..124.03.
Other meshes (EA's, untouched): P1 2.
Lifecycle models in its Draw module: IBFBForgB_A, IBFBForgB_D2, IBFBForgB_D3.
House colour: IBHCFortress.
EA's body measured: `python3 -m sagekit measure isengard/fortress_burning_forges_destructibles` ->
work/measure.json.

Nearest Dwarven recipe: assets/dwarves/fortress_statues (the same role; start from its shapes).
"""
from sagekit.building import Building

from ..style import IsengardStyle


# Real fire (the game's particle systems on bones, docs/ART.md "Fire"): (x, y, z, kind) in the target's
# coordinates, collected from the design (kit.flames / kit.fire record them when the kit has a
# `fire_log` list); run again after moving a fire.
FIRE_POINTS = [
    (-37.7, -13.0, 133.8, 'chimney'), (-43.0, 0.0, 115.6, 'brazier'), (-54.0, -12.5, 64.4, 'hearth'),
    (-48.5, -15.5, 65.3, 'embers'), (-28.4, 9.4, 41.8, 'crucible')
]


class FortressBurningForgesDescrutbiles(Building):
    style = IsengardStyle()
    fire_points = FIRE_POINTS
    source = "IBFBForgB"
    target = "IBFBFORGES"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresM.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the unwrap overlapped (0.02%): seams at EA's islands and 8-degree turns
    parts = ("ModuleTag_DrawBurningForgesDescrutbiles",)
    views = {
        "rts": ((-44.9, -2.0, 62.0), 319, 50, -38, 50),
        "close": ((-42.0, -5.0, 80.0), 150, 30, -30, 45),
        "ingame": ((-44.9, -2.0, 62.0), 725, 53, -62, 50),
    }

    def design(self, kit):
        from . import forge
        return forge.build(kit)
