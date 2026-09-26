"""Dwarven wall end (DwarvenWallCliffCap, model DBWallNE): the piece that ends a wall run where it
meets a cliff. EA's model is two wall-segment bays end to end: bay A (y -19..19) takes the next
segment's slot and meets it at y = +19 with the segments' half buttress; bay B (y -57..-19) runs on
into the cliff and ends in a plain cut at y = -57. Its buttresses reach down to z -53 for the
falling ground at the cliff's foot.

The segments' profile runs on unchanged (coping, chevron parapet, corbel table, plinth, banners;
the constants are the segment's own, so the joint at y = +19 is exact), and the cut end gets a
stepped terminal block on the walkway, over both parapets, with a gilded point: the end of the
wall seen from the field. Nothing reaches past EA's footprint (x -8.34..8.3, y -57..19).

DBWALLNE hangs under a bone rotated by (-0.5, 0.5, 0.5, -0.5): mesh-local = (-y, z, -x) of the
world. `world_space = True`: every number here is in WORLD axes (z up, the model's origin as the
game places it), read off the imported model's matrix_world.

EA's cap in world axes (per face, s = +-1): wall body |x| 6.0, z 0..53.01; rune band |x| 8.0,
z 43.97..51.07, full length; relief niches recessed to |x| 4.0 about y = 0 and y = -38 (|dy| <=
5.38, jambs to 6.62); stepped buttresses (|x| 7.3 / 8.3) over y 10.5..19 (the joint's half
buttress) and -27.5..-10.5 (the full one between the bays), z -53..33.3/34.3 ramping to 41 at
y = +-19; the -57 end plain (no buttress)."""
from sagekit.building import Building

from ..style import DwarvenStyle
from ..wall_segment.building import (BANNER, CORBEL, CORBEL_U, COPING, COPING_TAGS, COPING_X, PLINTH, PLINTH_TAGS,
                                     WALL_X, BAND)

JOINT_Y = 19.0                    # meets the neighbouring segment's end (its y = -19)
END_Y = -57.0                     # the cut end, into the cliff
BAYS = (0.0, -38.0)               # niche centres
# plinth runs between the buttresses' outer layers (|x| 8.3), which bury its ends; bay B's runs
# out to the cut end (0.1 short of it: its end cap then lies inside the wall body for |x| < 6)
PLINTH_RUNS = [(-11.4, 11.4, False), (END_Y + 0.1, -26.6, True)]
# corbels: the segment's five about each niche; bay B's plain run to the end gets two more
CORBEL_YS = [BAYS[0] + u for u in CORBEL_U] + [BAYS[1] + u for u in CORBEL_U] + [BAYS[1] - 12.6, BAYS[1] - 16.8]
# banners beside each niche, between its jamb and the buttress (or, bay B's end side, the plain run)
BANNER_YS = [BAYS[0] + BANNER[0], BAYS[0] - BANNER[0], BAYS[1] + BANNER[0], BAYS[1] - BANNER[0]]
# terminal block at the cut end: tiers (half width x, inset from the block's y range, z0, z1, side
# tags [end, +x, walk, -x]); the block stands 0.25 in from the cut and 0.25 behind the coping face
# (|x| 8.2) so no face shares a plane with it; the first tier starts buried in the walkway /
# coping (52.9); then a gilded point
T0, T1 = END_Y + 0.25, END_Y + 10.25
END_TIERS = [
    (7.95, 0.0, 52.9, 61.0, "stoneB"),
    (7.35, 0.6, 61.0, 63.6, ["tri", "tri", "stoneA", "tri"]),
    (6.0, 1.9, 63.6, 66.6, "stoneA"),
    (4.4, 3.1, 66.6, 68.4, "stoneA"),
]
END_POINT = 72.4                  # limit: -53 + 106.02 x 1.2 = 74.2
PARAPET_Y0 = T1 - 0.3             # the chevrons start buried 0.3 in the terminal block
COPING_Y0 = END_Y + 0.1           # the coping's end cap 0.1 short of the cut: where it crosses the rune
                                  # band and the wall it lies inside them, not on their end face


class WallEnd(Building):
    style = DwarvenStyle()
    source = "DBWallNE"
    target = "DBWALLNE"
    world_space = True
    sheet = None                                                # the faction atlas DBFortress1
    own_textures = {"DBFortress1.tga": "DBFortressN.tga"}       # taken: B C E F G H J K M P Q R S V W
    # our own house-colour model's Draw module gets a tag of its own (see wall_segment)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallNE"
    views = {
        "rts": ((0, -19, 30), 300, 48, -24, 50),
        "close": ((0, -19, 34), 215, 20, -18, 45),
        "end": ((0, -48, 44), 120, 28, -62, 45),
        "joint": ((0, 12, 40), 110, 30, 40, 45),
        "ingame": ((0, -19, 26), 560, 53, -62, 50),
    }

    def variants(self, install):
        """The framework's variants, less EA's swaps to sheets the game does not have: the cliff
        cap's snowy construction swaps to `DBFortress_Snow.tga` (EA's typo for DBFortress1_Snow;
        no archive has it). Without a swap of ours our body keeps its own sheet in that state. And
        one variant per sheet: the INI spells the snow sheet both `DBFortress1_Snow` and `_snow`
        (the INI swaps match either spelling)."""
        from sagekit.formats.textures import compiled_path
        out, seen = {}, set()
        for ea, mine in super().variants(install).items():
            if ea.lower() in seen or install.owner(compiled_path(ea, ".dds")) is None:
                continue
            seen.add(ea.lower())
            out[ea] = mine
        return out

    def design(self, kit):
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft, sweep
        solids = []
        t = V((0, 1, 0))
        for s in (1, -1):
            n = V((s, 0, 0))
            # 1. coping the whole length (its end cap at the cut); chevrons from the terminal block
            path = [(s * COPING_X, COPING_Y0), (s * COPING_X, JOINT_Y)]
            solids += sweep(path, COPING, COPING_TAGS, center=(0, -19))[0]
            solids += kit.chevron_parapet(V((s * COPING_X, PARAPET_Y0, 0)), t, n, JOINT_Y - PARAPET_Y0)
            # 2. battered plinth in each bay
            for y0, y1, cap in PLINTH_RUNS:
                path = [(s * WALL_X, y0), (s * WALL_X, y1)]
                solids += sweep(path, PLINTH, PLINTH_TAGS, cap_start=cap, cap_end=False, center=(0, -19))[0]
            # 3. corbel table under the rune band
            z0, dep, hw = CORBEL
            for u in CORBEL_YS:
                def ring(y):
                    return [V((s * WALL_X, y, z0)), V((s * (WALL_X + dep), y, BAND[0])), V((s * WALL_X, y, BAND[0]))]
                solids.append(loft([ring(u - hw), ring(u + hw)], [["stoneB", None, None]],
                                   cap0=("stoneB", True), cap1=("stoneB", True)))
            # 4. banners beside the niches
            _, z_top, width, length = BANNER
            for u in BANNER_YS:
                solids += kit.banner(V((s * WALL_X, 0, 0)), t, n, u, z_top, width, length, d=0.05)
        # 5. the terminal block at the cut end
        def rect(hx, e, z):
            return box_rings((-hx, hx), (T0 + e, T1 - e), z, 0)
        for hx, e, z0, z1, tag in END_TIERS:
            solids.append(loft([rect(hx, e, z0), rect(hx, e, z1)], [tag], cap0=("top", False), cap1=("top", True)))
        hx, e, _, z1, _ = END_TIERS[-1]
        apex = V((0, (T0 + T1) / 2, END_POINT))
        solids.append(loft([rect(hx, e, z1), [apex] * 4], ["trim"], cap0=("top", False), cap1=("top", False)))
        return solids

    def emphasis(self, c, n):
        if c.z > 50:
            return 1.4                        # parapet, coping, terminal: what the RTS camera sees
        return 1.0
