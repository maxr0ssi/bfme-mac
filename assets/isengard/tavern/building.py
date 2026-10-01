"""The Isengard tavern (IsengardTavern; EA's Dunland hall, "Clan Steading" on its button), pass 2
"the hall of the White Hand": EA's hall kept whole - the long steep roof down to the ground, the
crossed logs at its gable ends, the log buttresses, the door in the +X gable - and claimed by
Saruman. A dorsal crest of seven layered knife fins runs the ridge, rising to the middle (z 76), a pair of iron blades crosses over each gable's
apex (the hall's horns), two lozenge needle stacks rise through the roof's -Y slope, and the
White Hand on a shield hangs in the +X gable over the door. Real fire in the stacks (EA's own
chimney smoke has no bone in the model, so it rises from the object's origin; its torches FX01,
FX02 at (42, +-26, 32) stay).

Pass 3 (the citadel's recipe, 2026-09-29): the hall of the White Hand flanked: two matching blades out of the roof slopes
either side of the dorsal crest in the RTS view (z 28 to 77.5, the White Hand in pointed-arch
slots, chains to the crest's tall fin); the two stacks became one great chimney behind the crest
on the view's axis.

Pass 4 (2026-09-30, "the furnace towers look a lil stupid", Max): the chimney, the pair and its
chains went. Crude orc hides pegged with iron on the -Y slope the camera sees, and a cook-fire with
a spit at the -X end (the chimney's fire).

Player-built: slot 6 of IsengardPorterCommandSet builds it (Command_ConstructIsengardTavern), so
it is a building like the others, not a captured map building.

EA's facts (BUILDING on an identity bone): x -42.9..42.9, y -33.7..36.8, z -8.5..63.5 (1848
triangles). The ridge along x at y -2, z 56..60, the gable apexes at x -30 and 25 (the crossed
logs to z 64); the roof falls to z 20..35 at y +-25..33. Kept clear: the door and the units' way
out (made at (14.9, -0.1), rallying to (100, -0.1): x > 15, |y| < 12 below z 30); the level-ups
(V1 hide walls along both sides, x -36..26, |y| 19..50, to z 32; V2 banners, x -45..36, to z 48;
V3 stakes flanking the door, x 25..53, |y| 10..27, to z 27); the torch posts (TORCHES, x 39..43,
|y| 21..27). Its sheets (ibwildbuilding.tga, _d, _snow, _nrm) are TGA files, not DDS: the extract
step reads them (sagekit/formats/textures.py sheet_member, tga_to_dds), the snow swap included.
Height limit +20 %: z 77.9.
"""
from sagekit.building import Building

from ..style import IsengardStyle

FIRE_POINTS = [
    (-38.5, -9.0, 1.0, 'hearth')
]

RIDGE = ((-28.0, -2.0, 58.5), (22.0, -2.0, 58.0))
FINS = [6.0, 9.5, 13.0, 17.5, 13.0, 9.5, 6.0]         # the dorsal crest's fins, tops above the ridge
APEXES = [(25.0, -2.0, 56.0), (-30.5, -2.0, 57.0)]
# pass 4 (2026-09-30): the chimney and the pair went; crude orc hides pegged on the -Y slope
# (EA's roof there: z 56 at y -4 falling to 38.6 at y -16), a cook-fire at the -X end
HIDES = [((-18.0, -4.6, 55.6), 12.5, 17.0, 0.3), ((-3.0, -4.2, 56.2), 11.0, 18.5, 1.9), ((11.5, -4.8, 55.3), 12.0, 16.0, 3.1)]
COOK = ((-38.5, -9.0), (0.0, 1.0))
HAND = (27.5, -2.0, 34.0)                         # the shield's foot on the +X gable


class Tavern(Building):
    style = IsengardStyle()
    source = "ibwildbld_skn"
    target = "BUILDING"
    sheet = "ibwildbuilding.tga"
    sheet_normal = "ibwildbuilding_NRM.tga"
    own_textures = {"ibwildbuilding.tga": "ibwildbuildinH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    fire_points = FIRE_POINTS
    views = {
        "rts": ((0.0, 1.6, 27.5), 291, 50, -38, 50),
        "close": ((0.0, 0.0, 30.0), 190, 24, -30, 45),
        "ingame": ((0.0, 1.6, 27.5), 662, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_industry import logged
        return logged(kit, self._pieces)

    def _pieces(self, kit):
        from mathutils import Vector as V

        from .. import shapes_industry_big as B
        p, q = RIDGE
        out = B.ridge_fins(kit, V(p), V(q), FINS, w=1.4)
        for x, y, z in APEXES:                        # crossed iron blades over each gable's apex
            for s in (-1, 1):
                a = V((x, y + s * 2.5, z - 4.0))
                b = V((x, y - s * 7.5, z + 15.0))
                out.append(kit.beam(a, b, 0.9, "iron", 0.0))
                out.append(kit.beam(a + V((0.6, 0, 0)), b + V((0.6, 0, 0)) - (b - a) * 0.3, 0.35, "trim", 0.0))
        from .. import shapes_trades as T
        down = V((0.0, -0.568, -0.823))               # down the -Y slope (EA's roof, probed)
        for (x0, y0, z0), w, length, seed in HIDES:   # crude hides pegged on the slope the camera sees
            out += T.roof_hide(kit, V((x0, y0, z0)), (1, 0, 0), down, w, length, seed=seed)
        (fx, fy), t = COOK
        out += T.spit_fire(kit, V((fx, fy, 0.0)), t, 2.8)
        x, y, z = HAND
        out += kit.shield(V((x, y, 0)), V((0, 1, 0)), V((1, 0, 0)), 0.0, z, 15.0, d=0.0)
        for s in (-1, 1):                             # hung on chains from the apex
            out += kit.chain(V((x + 0.3, y + s * 3.4, z + 14.6)), V((x - 1.0, y + s * 1.2, z + 20.0)), link=1.3)
        return out
