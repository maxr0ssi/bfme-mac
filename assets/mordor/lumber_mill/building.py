"""Mordor lumber mill (MordorLumberMill; EA's MBLumMill_SKN, shipped as our own MBLumMill2_SKN), pass
2 "the charcoal pit": EA's yard kept whole - the lean-to shed of spiked posts and its log stacks, the
chopping stumps, the great log on its X sawhorses, the fire pit, the slab floor - and made the
citadel's: a big claw of hooked spikes rises from inside the fire pit's stone ring and closes over
its real orange fire and dark plume (the orcs burn the felled wood to charcoal for the forges); a
great saw hangs from a tall gantry across the great log; a ramp of felled trunks rises beside it;
steel spikes crest the shed's front beam.

    claw        six spikes (the citadel's Horn, s 2.5 / 2.0) from the pit's ring at r 12 round (20,
                32.7), leaning in to tips at r 6..7.5, z 42 (tall) and 33; set between the planes of
                EA's flame card (FIRE01: four crossed planes at 9, 28, 95 and 124 degrees, +-9.4
                wide, z 3.5..30.4)
    fire        "furnace" over the pit's coals among the spikes, a heavy dark plume over it
    saw         a gantry of charred A-frames (to z 40, 25 across) over the great log's middle (23,
                -1), a steel blade with hooked teeth hung on chains, bitten into the log
    logs        log_ramp at (38, -38): five courses of trunks, three skids leaning up onto it, stakes
    shed        steel spikes leaning out along the front beam (x -24, z 40)
    yard        a charcoal heap, a fire basket, a whip post by the stumps, a lava pool by the pit

Ownership: the Goblins and Isengard draw MBLumMill_* too; the redesign ships as MBLumMill2_SKN (own
model), on our own sheet MBLumberMilB.tga, with our own house copy MBHCLumMill2.

EA's MBLumMill_SKN (object MordorLumberMill; role economy): body LUMBERMILL, 1204 triangles, painted
from MBLumberMill.tga + MBLumberMill_NRM.tga (DXT1). In LUMBERMILL mesh coordinates (identity bone):
x -66.93..53.07, y -56.71..57.42, z -4.40..45.61. Other meshes (EA's, untouched): V2 385 (the
level-up watchtower, x -56.5..-21.6, y -51.2..-16.3, to z 81.4); ORC, ORCN 264; N_WINDOW 80 and
N_FIRE 16 (night torch posts at (-8, -51) and (-1, 47)); FIRE01 8 (EA's flame card in the pit);
OBJECT01..06 (the loose logs and chips). Lifecycle models in its Draw module: MBLumMill_A (a
remodel, not a cut: lifecycle fill, as the Goblins' and Isengard's), MBLumMill_D1, MBLumMill_D2.
House colour: MBHCLumberMill.

EA's facts (measured 2026-09-30, work/measure.json and the preview stage): the slab floor at z -3.1
under the terrain; the shed on the -X side under its front beam (x -24.5, y -29..53, z 34..40), its
roof falling to z 19 at x -55; the great log from (-1, -18) to (47, 16), z 5..16.4; the fire pit a
stone ring round (20, 32.7): coals heaped to z 5 in the middle, a trough at r 8 (z 2), the ring's
crest at r 12..13 (z 6..8), the ground at r 18. Kept clear: the stumps where the orcs chop (x
-35..-5, y -53..-19), the level-up tower (V2), the torch posts. Height limit +20 %: z 55.6.
"""
from sagekit.building import Building

from ..style import MordorStyle

PIT = (20.0, 32.7)
# the claw: (degrees, the ring's crest height there, tall)
SPIKES = [(61.3, 8.0, True), (109.6, 7.6, False), (156.9, 6.8, True), (241.3, 6.1, True), (289.6, 6.0, False),
          (336.9, 5.5, True)]
TIP = {True: (6.0, 42.0, 2.5), False: (7.5, 33.0, 2.0)}   # (tip r, tip z, section scale)
SAW = ((23.0, -1.0), (0.81, 0.58), 16.4)                 # the log's middle, its axis, its top z
BEAM = ((-24.0, -29.0), (-22.0, 53.0), 40.0)
HEAP = (16.0, -48.0)
BASKET = (46.0, -12.0)
RAMP = ((38.0, -38.0), (0.0, -1.0), 18.0, 1.9, 5)    # the log pile: centre, rising along, log length, r, courses
WHIP = (-10.0, -45.0)
POOL = (38.0, 45.0)

# real fire and smoke (the game's particle systems on bones of the rig), from the design's log
FIRE_POINTS = [
    (20.0, 32.7, 6.0, 'furnace'), (20.5, 32.2, 22.0, 'plume'), (46.0, -12.0, 5.3, 'brazier'), (38.0, 45.0, 0.6, 'embers')
]


class LumberMill(Building):
    style = MordorStyle()
    source = "MBLumMill_SKN"
    target = "LUMBERMILL"
    own_model = "MBLumMill2_SKN"            # goblins, isengard draws MBLumMill_SKN too (sagekit/ownership.py)
    sheet = "MBLumberMill.tga"
    sheet_normal = "MBLumberMill_NRM.tga"
    own_textures = {"MBLumberMill.tga": "MBLumberMilB.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # EA's unwrap overlaps (the Goblins' and Isengard's mills): seams at its islands
    bake_hidden = ("V2", "N_WINDOW", "N_FIRE", "FIRE01", "ORC", "ORCN")
    lifecycle = {"MBLumMill_A": {"fill": True}}     # EA's build model is a remodel, not a cut (sagekit/lifecycle.py)
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): none: an economy building. 0.0 live (was 23.6).
    fire_points = []
    views = {
        "rts": ((-6.9, 0.4, 20.6), 381, 50, -38, 50),
        "close": ((-6.9, 0.4, 20.6), 225, 24, -30, 45),
        "ingame": ((-6.9, 0.4, 20.6), 865, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        return logged(kit, lambda k: k.retag(self._pieces(k)))

    @staticmethod
    def _pieces(kit):
        from mathutils import Vector as V

        from .. import shapes_production as P
        out = []
        for deg, z, tall in SPIKES:                              # the claw round the charcoal pit
            r1, zt, s = TIP[tall]
            out += P.spike(kit, PIT, deg, 12.0, z - 1.5, r1, zt - (z - 1.5), s, tall)
        kit.fire(V((PIT[0], PIT[1], 6.0)), "furnace")
        kit.fire(V((PIT[0] + 0.5, PIT[1] - 0.5, 22.0)), "plume")
        (sx, sy), t, top = SAW
        out += P.great_saw(kit, (sx, sy, 0.0), t, top, span=12.5, h=40.0, blade=9.5)
        (x0, y0), (x1, y1), z = BEAM
        a, t = V((x0, y0, 0)), V((x1 - x0, y1 - y0, 0))
        L = t.length
        t.normalize()
        out += kit.spike_row(a, t, V((t.y, -t.x, 0)), 2.0, L - 2.0, z + 0.3, 5.5, 13, lean=0.5, r=0.5, tag="steel")
        out += kit.ash_heap(V((HEAP[0], HEAP[1], 0.05)), 4.2, 3.2, seed=2)
        from .. import shapes_production_big as PB
        (lx, ly), t, L, r, rows = RAMP
        out += PB.log_ramp(kit, (lx, ly, 0.0), t, L, r, rows, seed=1.0)
        out += kit.fire_basket(V((BASKET[0], BASKET[1], 0.0)), 1.7, 5.0)
        out += P.whip_post(kit, (WHIP[0], WHIP[1], 0.65), 10.0, seed=2.0)
        out += kit.lava_pool(V((POOL[0], POOL[1], 0.0)), 3.4, seed=2.0)
        kit.fire(V((POOL[0], POOL[1], 0.6)), "embers")
        return out
