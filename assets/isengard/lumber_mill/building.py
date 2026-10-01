"""The Isengard lumber mill (IsengardLumberMill; EA's Mordor mill MBLumMill_SKN, shipped as our own
IBLumMill_SKN), pass 2 "Fangorn's end": EA's yard kept whole - the lean-to shed and its log
stacks, the chopping stumps, the great log on its sawhorses, the fire pit, the slab floor - and
made the place where Saruman's orcs fell and burn the forest for the furnaces:

Pass 3 (the citadel's recipe, 2026-09-29): Fangorn's end, stacked: the pair of charcoal kilns lowered to feet (z 14) with a
great blade-spire stack out of each (to z 47.5, crowns of blades, ember slits, glowing mouths),
mirrored either side of the banner: the citadel's pair.

Pass 4 (2026-09-30, "the furnace towers look a lil stupid", Max): both spire stacks, the second
kiln and the blade crane went. The mill's own work instead: a felled giant of Fangorn across the
front yard (root plate, broken limbs, iron dogs, a chain) with the great frame saw in its trunk, its
limbs burning on a slash pyre beside it; one charcoal kiln, its own throat alight; an iron gantry
over the crib of felled Fangorn with a trunk slung from it.

    kilns      a pair of steep square charcoal kilns on the +X-Y front, a corner to the camera,
               iron bands, a blade out of each corner, pointed ember vents, glowing throats
    crane      a lozenge iron mast to z 55 on the +X side, a laced jib over the logs, a trunk
               slung from its head
    logs       a crib of felled Fangorn in five crossed courses under the jib, iron stakes
    shed       a crest of iron blades along the front beam
    saw        a great frame saw over a trunk on trestles in the -Y yard
    banner     one heavy banner on an iron frame between the kilns
    fire       the kilns' throats, EA's fire pit, two braziers

    shed       a crest of iron blades along the front beam (the new outline over the yard)
    kilns      a pair of faceted black charcoal kilns on the +X-Y front, ember vents, a crown
               of blades round each glowing throat
    saw        a great frame saw over a trunk on trestles in the -Y yard
    hoist      an iron gantry over the great log's +X end, a trunk slung from its trolley
    logs       felled Fangorn stacked between iron stakes by the fire pit
    banner     one heavy banner on an iron frame between the kilns
    fire       the kilns' throats, EA's fire pit, two braziers

Ownership: Goblins and Mordor draw MBLumMill_* too; the redesign ships as IBLumMill_SKN (own
model), on our own sheet MBLumberMilX.tga, with our own house copy of MBHCLumberMill.

EA's facts (LUMBERMILL on an identity bone): x -66.9..53.1, y -56.7..57.4, z -4.4..45.6 (1204
triangles); the floor at z -3; the shed under its front beam (x -24, y -31..56, z 34..40), its
roof falling to z 19 at x -61; the great log from (5, -18) to (47, 17), z 5..16, on sawhorses;
the fire pit (FIRE01, EA's card) at (20, 33). The orcs work the stumps (x -35..-5, y -53..-19)
and the log: the yard between them stays clear. The level-up watchtower (V2, x -57..-22,
y -51..-16, to z 81) takes the -X-Y corner; EA's night torch posts (N_WINDOW) at (-8, -51) and
(-1, 47). Height limit +20 %: z 55.6.
"""
from sagekit.building import Building

from ..style import IsengardStyle

FIRE_POINTS = [
    (41.0, -21.0, 14.4, 'chimney'), (12.0, -31.0, -2.0, 'hearth'), (49.0, -36.0, 1.7, 'brazier'),
    (-2.0, -40.0, 1.7, 'brazier'), (20.0, 33.0, 2.0, 'hearth')
]

FLOOR = -3.0
BEAM = ((-24.0, -29.0, 40.0), (-22.0, 53.0, 40.0))      # the shed's front beam, its ends at the top
KILNS = [((41.0, -21.0), 10.0, 20.0)]           # the charcoal kiln right of the banner
GIANT = ((8.0, -48.5, FLOOR + 2.6), (28.0, -32.5, FLOOR + 2.0), 2.6)   # root plate, sawn end, radius
SAW = ((19.5, -39.3), 19.0)                     # the frame saw over the giant: foot centre, height
PYRE = ((12.0, -31.0), 3.4)                     # its limbs burning beside it
HOIST = ((41.5, 34.0), (1.0, 0.0), 18.0, 24.0, 9.0)          # gantry centre, t, span, height, drop
LOGS = ((42.5, 34.0), (1.0, 0.0), 16.0, 2.2, 5)               # a crib of felled Fangorn under the crane's jib
BANNER = ((38.0, -35.0), (-0.62, -0.79))
BRAZIERS = [(49.0, -36.0), (-2.0, -40.0)]


class LumberMill(Building):
    style = IsengardStyle()
    source = "MBLumMill_SKN"
    target = "LUMBERMILL"
    own_model = "IBLumMill_SKN"            # goblins, mordor draws MBLumMill_SKN too (sagekit/ownership.py)
    sheet = "MBLumberMill.tga"
    facet_islands = 8                       # the unwrap overlapped a little: seams at EA's islands and 8-degree turns
    sheet_normal = "MBLumberMill_NRM.tga"
    own_textures = {"MBLumberMill.tga": "MBLumberMilX.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    fire_points = FIRE_POINTS
    lifecycle = {"MBLumMill_A": {"fill": True}}     # EA's build model is a remodel, not a cut (sagekit/lifecycle.py)
    views = {
        "rts": ((-6.9, 0.4, 20.6), 381, 50, -38, 50),
        "close": ((0.0, 0.0, 18.0), 225, 24, -30, 45),
        "ingame": ((-6.9, 0.4, 20.6), 865, 53, -62, 50),
    }

    def design(self, kit):
        from ..shapes_industry import logged
        return logged(kit, self._pieces)

    def _pieces(self, kit):
        from mathutils import Vector as V

        from .. import shapes_industry as I
        from .. import shapes_industry_big as B
        from .. import shapes_trades as T
        (p, q) = BEAM
        p0, q0, r = GIANT                                # a felled giant of Fangorn across the front yard
        out = T.fangorn_trunk(kit, V(p0), V(q0), r, seed=0.7)
        out += I.roof_crest(kit, V(p), V(q), 11, 11.0, w=0.45, d=2.2)
        for (kx, ky), r, h in KILNS:                    # the charcoal kilns, their own throats alight
            out += B.pyramid_kiln(kit, V((kx, ky, FLOOR)), r, h, rot=-83.0)
        (sx, sy), h = SAW                               # the great saw in the giant's trunk
        p, q, r = GIANT
        d = (V(q) - V(p)).normalized()
        out += T.trunk_saw(kit, V((sx, sy, FLOOR)), (d.x, d.y), FLOOR + 2 * r, h, w=r + 1.6)
        (yx, yy), r = PYRE
        out += T.slash_pyre(kit, V((yx, yy, FLOOR)), r, seed=1.3)
        (gx, gy), t, span, h, drop = HOIST              # an iron gantry over the crib, a trunk slung from it
        out += T.pit_gantry(kit, V((gx, gy, FLOOR)), t, span, h, drop=drop, log=(13.0, 1.5))
        (lx, ly), t, length, r, layers = LOGS
        out += B.log_crib(kit, V((lx, ly, FLOOR)), t, length, r, layers)
        (bx, by), t = BANNER
        out += I.banner_frame(kit, V((bx, by, FLOOR)), t, 8.0, 17.0)
        for x, y in BRAZIERS:
            out += kit.brazier(V((x, y, FLOOR)), 1.6, 4.6)
        kit.fire(V((20.0, 33.0, 2.0)), "hearth")                # EA's fire pit: its card stays, our flames join it
        return out
