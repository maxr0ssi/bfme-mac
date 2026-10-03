"""Neutral ruined tower (RuinedTower): stub from `sagekit new neutral`.

EA's RuinTwr (objects RuinedTower; role tower): body RUIN TOWER, 1568 triangles, painted from
RuinTwr1.tga, no normal map (DXT1).
In RUIN TOWER mesh coordinates: x -22.13..38.98, y -20.59..23.08, z -1.47..107.77.
Other meshes (EA's, untouched): HOUSE COLOR 258 (GU_Banr_house.tga); WINDOW_N01 50 (GBNight.tga).
Lifecycle models in its Draw module: RuinTwr_D, RuinTwr_D2.
House colour: none of EA's (HOUSE_DRAW: a model of our own, from the style's house_template).
EA's body measured: `python3 -m sagekit measure neutral/ruined_tower` -> work/measure.json.

Its bone is turned 180 degrees about z: world_space, every number in world axes.

Ours (body, no capture dress): the broken top stays open (a roof over it was rejected: the ruin has
to read as a ruin). Squatters camp on the old floor instead: a fire ring with a cookpot on a tripod,
barrels, a charred roof beam fallen against the wall, and a lantern on a pole.
No dress: the tower changes hands by garrison (HordeGarrisonContain, AllowNeutralInside), and when
the garrison leaves it goes back to its old owner while an upgrade module cannot be undone, so a
holder's dress would stay on a tower nobody holds. EA's own house-colour banner (HOUSE COLOR,
ALWAYS_SHOW_HOUSE_COLOR) already shows who is inside.
"""
from sagekit.building import Building

from ..style import NeutralStyle


class RuinedTower(Building):
    style = NeutralStyle()
    source = "RuinTwr"
    target = "RUIN TOWER"
    world_space = True
    facet_islands = 20                  # the broken masonry's smooth shells unwrap onto themselves otherwise
    sheet = "RuinTwr1.tga"
    sheet_normal = None
    own_textures = {"RuinTwr1.tga": "RuinTwrH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    house_tags = ()
    views = {
        "rts": ((-8.5, -1.2, 53.2), 300, 50, -62, 50),
        "close": ((-4.0, -2.0, 70.0), 190, 26, -55, 45),
        "ingame": ((-8.5, -1.2, 53.2), 664, 53, -62, 50),
    }

    def design(self, kit):
        import math
        V, Z, z = kit.V, kit.Z, 85.7                             # the old floor, open to the sky
        out = []
        cx, cy, r = 2.5, 3.0, 2.6                               # fire ring, ash bed, cookpot on a tripod
        for i in range(8):
            a = 2 * math.pi * i / 8
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            out.append(kit.box(x - 0.7, x + 0.7, y - 0.7, y + 0.7, z - 0.03, z + 0.8 + 0.25 * (i % 2), "stoneA",
                               ("stoneA", False), ("top", True)))
        out.append(kit.turned(cx, cy, [(r - 0.5, z), (r - 0.8, z + 0.3)], ["log"], 8, cap0=("log", False), cap1=("iron", True)))
        top = V((cx, cy, z + 5.2))
        for a in (90, 210, 330):
            foot = V((cx + 3.4 * math.cos(math.radians(a)), cy + 3.4 * math.sin(math.radians(a)), z))
            out.append(kit.beam(foot, top + Z * 0.4, 0.2, "post"))
        out.append(kit.beam(top, top - Z * 1.8, 0.08, "iron"))
        out.append(kit.turned(cx, cy, [(0.5, z + 1.9), (1.1, z + 2.3), (1.15, z + 3.0), (0.9, z + 3.4)], ["iron"] * 3, 8,
                              cap0=("iron", True), cap1=("iron", True)))
        out += kit.barrel(-6.5, -3.5, z, 1.4, 3.2)
        out += kit.barrel(-4.0, -6.8, z, 1.3, 3.0)
        out.append(kit.beam(V((-8.0, 6.5, z + 0.6)), V((7.5, -8.5, 99.6)), 0.85, "log|a"))      # the old roof's ridge, charred
        out.append(kit.post(6.0, -1.5, z, z + 8.5, 0.35))                                        # lantern pole and arm
        out.append(kit.beam(V((6.0, -1.5, z + 8.0)), V((4.2, -1.5, z + 8.0)), 0.18, "post"))
        out += kit.lantern((4.4, -1.5, z + 7.8), 1.0, 0.8)
        return out
