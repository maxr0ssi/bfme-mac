"""Angmar fortress wall hub (AngmarWallHubSmallExpansion; model KBHTow): EA's expansion hub kept
whole - the wall hub's octagonal tower (the same mesh in model space) and the stub of wall running
from it to the citadel - and dressed as the wall hub (shapes_walls.hub: merlons on the parapet,
icicles under its overhang, ice drifts on the diagonal faces, EA's horn pair frozen from its tips
down, the cold brazier in the roof's middle, "coldflame") with the stub carrying the walls' run:
Carn Dum merlons on both its top edges, a corbel with icicles under them either side of EA's
buttress. No banners.

EA's facts (HUBTOWER mesh coordinates = model, identity bone; measured 2026-10-01, ray casts): the
tower as angmar/wall_hub's in model space (faces 20.3..20.8 from the axis, parapet 21.7 at
z 54.5..61.5, roof 62.4, the horn pair over the +y corners to z 96, the third over -y); the stub
along x from -42.35 into the hub's -x face (x -20.3): faces at y ~+10.1 / -10.4, its top z 44.6
with the walk at 39.6 (|y| < 6), a buttress at x -28 proud to |y| 11.8. ICEWALL (Ice Walls,
18 triangles, EXFortressIce): a shell 0.5 outside the shaft and the stub (x -42.7..21, |y| 21.3)
to z 33.04: the ice drifts stand beyond it, their feet through it. The Ice Walls sheet gets our
own copy (KBFortressM_Ice). Lifecycle models in its Draw module: KBHTow_A, KBHTow_D1, KBHTow_D2,
KBHTow_D3, kkbhtow_a. House colour: none.
"""
from sagekit.building import Building

from ..style import AngmarStyle

# the cold brazier in the roof's middle (shapes_walls.HUB_BRAZIER: z 62.4 + 0.62 of its 11), model space
HUB_FIRE = [(0.0, 0.0, 69.2, "coldflame")]

STUB = (-42.2, -20.6, 44.6)          # x0, x1 (the hub's face), top
STUB_FACE = {1: 10.1, -1: 10.4}
BUTTRESS = (-30.8, -25.2)


class FortressWallHub(Building):
    style = AngmarStyle()
    source = "KBHTow"
    target = "HUBTOWER"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressM.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCFortressWallHub"
    bake_hidden = ("ICEWALL",)        # the Ice Walls shell: shown in game with its upgrade, out of the bakes
    house_tags = ()
    fire_points = HUB_FIRE
    views = {
        "rts": ((-7.3, -5.0, 48.1), 288, 50, -38, 50),
        "close": ((-7.3, -5.0, 48.1), 170, 24, -30, 45),
        "ingame": ((-7.3, -5.0, 48.1), 654, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from ..shapes_walls import corbel, hub, merlon_us, merlons
        out = hub(kit, ground=0.05)
        x0, x1, top = STUB
        for s in (1, -1):
            a, t, n = V((0, s * STUB_FACE[s], 0)), V((1, 0, 0)), V((0, s, 0))
            out += merlons(kit, a, t, n, merlon_us(x0, x1, skip=[BUTTRESS]), top)
            for u0, u1 in ((x0, BUTTRESS[0]), (BUTTRESS[1], x1)):
                out += corbel(kit, a, t, n, u0, u1, top - 1.9, out=1.3, seed=u0 * s)
        return kit.retag(out)
