"""Angmar wall hub (AngmarWallHubSmall; model KBWallHubN): EA's octagonal hub kept whole - the
shaft, the corbelled parapet, the flat roof, its horn pair over the +y corners, the third horn
leaning out over -y and the two small hooks - and given the walls' frozen top (shapes_walls.hub,
shared with angmar/fortress_wall_hub):

- Carn Dum merlons on the parapet of every face, as the segments' (none where EA's horns stand);
- icicles under the parapet's overhang all round, a rime crust along it;
- ice drifts up the shaft's four diagonal faces (the faces on the axes stay clear for the walls
  run into them);
- in the roof's middle, between EA's horns, a sorcerer's cold brazier: a claw of five iron prongs
  out of black stone shards, the cold fire burning in it ("coldflame"): the hub's fire.

No new peak: EA's three horns are the hub's crown; the frozen tines stand on the wall tower.
No banners (hubs repeat along every wall).

EA's facts (measured 2026-10-01, ray casts in model space): the mesh WALL HUB hangs on a bone
turned 90.5 degrees about z and moved (0.06, -5.06, 48.1) (model = R mesh + T, FRAME below): the
design is built in model space and turned into the mesh's frame. In model space: the octagonal
shaft's faces 20.3 (x), 20.7 (y) and ~20.8 (diagonals) from the axis, from the ground (z 0.07) to
53.5; the parapet corbelled out to 21.7 (z 54.5..61.5), chamfered to 20.5 at the roof (z 62.4);
the horn pair over the +y corners at (+-15, 8) to z 96, the third horn from (0, -11) leaning out
over -y (its point at y -32) to z 95, two small hooks at (+-27, 16), z 75; footprint x +-27.9,
y -32.9..22.8. No Ice Walls mesh on this model; the Ice Walls sheet gets our own copy
(KBFortressC_Ice). Lifecycle models in its Draw module: KBWalHubN_A, KBWalHubN_D3, KBWallHubN_D1,
KBWallHubN_D2. House colour: none.
"""
from sagekit.building import Building

from ..style import AngmarStyle

# the cold brazier in the roof's middle (shapes_walls.HUB_BRAZIER: z 62.4 + 0.62 of its 11), model space
HUB_FIRE = [(0.0, 0.0, 69.2, "coldflame")]

# WALL HUB's bone (sagekit.formats.w3dframes.mesh_frames): model = R mesh + T
FRAME = (((-0.008777, -0.999961, 0.0), (0.999961, -0.008777, 0.0), (0.0, 0.0, 1.0)), (0.0604, -5.0563, 48.098))


class WallHub(Building):
    style = AngmarStyle()
    source = "KBWallHubN"
    target = "WALL HUB"
    sheet = "KBFortressB.tga"
    sheet_normal = "KBFortressB_NRM.tga"
    own_textures = {"KBFortressB.tga": "KBFortressC.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallHub"
    house_tags = ()                 # no banners: hubs repeat along every wall
    fire_points = HUB_FIRE         # model space
    views = {
        "rts": ((-0.1, -5.0, 48.1), 272, 50, -38, 50),
        "close": ((-0.1, -5.0, 48.1), 161, 24, -30, 45),
        "ingame": ((-0.1, -5.0, 48.1), 618, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_walls import framed, hub
        return kit.retag(framed(hub(kit, ground=0.07), FRAME))
