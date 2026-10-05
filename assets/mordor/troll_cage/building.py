"""Mordor troll cage (MordorTrollCage), pass 2 "the iron claw": EA's pen kept whole - the ring of
sharpened stakes round the troll, the log-roofed house with its great door, the corner posts - and
made the citadel's: eleven heavy hooked iron claws rise from inside the palisade and close over the
troll, chained to a spiked iron boss over the pen's middle, a fire pit burning under them; steel
spikes along the roof's edge over the door; lava at the pen's foot, fire baskets by the door.

    claw        eleven hooked iron bars (r 1.8 / 1.45) from inside the palisade (r 27 round (-27,
                -2)), up its inner face and in over the pen to steel points at z 54..59, two barbs
                each; heavy chains from their tips to a spiked boss at z 52 (the troll stands to z 37)
    fire        a fire pit in the pen's west end (-43, -2), clear of the troll: "forge" and a
                "plume" under the claw (pass 1's roof bowl is gone: one claw is enough)
    roof        steel spikes leaning out along the roof's -Y edge (z 43) over the great door
    lava        an open lava channel round the pen's south-west foot (r 40..41.5), embers and smoke
    door        fire baskets either side of the door, clear of its sweep (x 16..51)

EA's MBTrollPit_SKN (object MordorTrollCage; role stable): body MBTROLLPIT, 1064 triangles, painted
from MBTrollPit.tga + MBTrollPit_NRM.tga (DXT1). In MBTROLLPIT mesh coordinates: x -44.39..84.08,
y -46.15..48.36, z -2.18..57.59; its bone is moved (-18.48, -2.14, 0.24), so the recipe works in
world axes (world_space): x -62.87..65.60, y -48.28..46.22, z -1.94..57.83. Other meshes (EA's,
untouched): V2 1218 (the level 3 banners on poles at (-2.6, 40.3), (65.8, -15.2), (-36, -42.4), to
z 105); TROLL_MESH 536 (the troll in the pen, x -31..-14, to z 37); ORC 264; CHAIN 212 (the troll's
chain); N_WINDOW 120, N_FIRE 24; CYLINDER01. The door (troll_cage_02, MBTrollPit_DSCL: x 16.2..51.4,
y -18.9..-15.8, z 6.8..47.3, animated) and the chains (troll_cage_module_tag_03) stay EA's and clear.
Lifecycle models in its Draw module: MBTrollPit_A, MBTrollPit_D1, MBTrollPit_D2, MBTrollPit_D3.
House colour: MBHCTrollPit.

EA's facts (measured 2026-09-30, work/measure.json and the preview stage, world axes): the pen's
floor at z 0.8 inside a ring of stakes round (-27, -2) (r 27..33, their tips at z 30..38), the house
east of it (x 0..62, y -15..37) under a flat log roof at z 42..44, its corner posts to z 48..57.
The trolls are made at (34, -45) and rally at (34, -93): the door's side (-Y of the house) stays
clear for x 12..56. Height limit +20 %: z 69.8.
"""
from sagekit.building import Building

from ..style import MordorStyle

PEN = (-27.0, -2.0)
BARS = [62.0 + 23.6 * i for i in range(11)]           # degrees round the pen's middle, 62..298
PIT = (-43.0, -2.0, 1.3)                              # the fire pit under the claw, west of the troll
BOSS = 52.0
EDGE = ((6.0, -15.6), (60.0, -15.6), 43.0, 12)        # the roof's -Y edge over the door, spikes
CHANNEL = [(215.0, 40.0), (240.0, 41.0), (265.0, 41.5), (288.0, 40.0)]
BASKETS = [(9.0, -27.0), (58.0, -27.0)]

# real fire and smoke (the game's particle systems on bones of the rig), from the design's log
FIRE_POINTS = [
    (-43.0, -2.0, 2.0, 'forge'), (-43.0, -2.0, 7.4, 'plume'), (-47.5, -37.5, 0.4, 'embers'), (-25.6, -43.3, 1.0, 'smoke'),
    (9.0, -27.0, 5.5, 'brazier'), (58.0, -27.0, 5.5, 'brazier')
]


class TrollCage(Building):
    style = MordorStyle()
    source = "MBTrollPit_SKN"
    target = "MBTROLLPIT"
    sheet = "MBTrollPit.tga"
    sheet_normal = "MBTrollPit_NRM.tga"
    own_textures = {"MBTrollPit.tga": "MBTrollPiH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    # EA remodelled the damaged cage: cut, 16-19% open backs (sagekit/lifecycle.py `fill`)
    lifecycle = {"MBTrollPit_D1": {"fill": True}, "MBTrollPit_D2": {"fill": True},
                 # the rubble too (cut: 14.7%); filled, 10.3% past EA's mid-collapse, no hole in the RTS renders
                 "MBTrollPit_D3": {"fill": True, "backs": (0.11, "mid-collapse, the stakes' cut ends: 10.3% "
                                                                "past EA's; no hole in the RTS renders")}}
    parts = ("ModuleTag_Draw",)
    world_space = True                  # the body's bone is moved (-18.5, -2.1, 0.2): design and fire share world axes
    facet_islands = 8                       # the unwrap overlapped (0.26%): seams at EA's islands and 8-degree turns
    bake_hidden = ("V2", "N_WINDOW", "N_FIRE", "TROLL_MESH", "ORC")
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): none. 0.0 live (was 30.8).
    fire_points = []
    views = {
        "rts": ((1.4, -1.0, 27.9), 375, 50, -38, 50),
        "close": ((1.4, -1.0, 27.9), 221, 24, -30, 45),
        "ingame": ((1.4, -1.0, 27.9), 852, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        return logged(kit, lambda k: k.retag(self._pieces(k)))

    @staticmethod
    def _pieces(kit):
        import math

        from mathutils import Vector as V

        from .. import shapes_production as P
        cx, cy = PEN

        def at(deg, r, z=0.0):
            a = math.radians(deg)
            return V((cx + r * math.cos(a), cy + r * math.sin(a), z))
        out = []
        boss = V((cx, cy, BOSS))
        for i, deg in enumerate(BARS):                          # the iron claw over the pen
            tall = i % 2 == 0
            out += P.claw_bar(kit, at(deg, 27.0, 16.0), boss, rise=38.0, tip=(12.0 if tall else 14.5),
                              ztip=(59.0 if tall else 54.0), r=1.8 if tall else 1.45)
            tip = at(deg, 12.0 if tall else 14.5, 59.0 if tall else 54.0)
            solids, _ = kit.hung_chain(tip - V((0, 0, 1.5)), boss + (tip - boss).normalized() * 1.6, 2.5, link=1.8,
                                       w=0.7, th=0.26, segs=3)
            out += solids
        out += P.boss(kit, boss, 2.4)
        out += P.fire_pit(kit, PIT, 3.8, kind="forge", smoke="plume", spit=False, seed=0.4)   # fire under the claw
        (x0, y0), (x1, y1), z, k = EDGE
        out += kit.spike_row(V((x0, y0, 0)), V((1, 0, 0)), V((0, -1, 0)), 0.0, x1 - x0, z + 0.4, 5.0, k, lean=0.5,
                             r=0.5, tag="steel")
        out += kit.lava_channel([at(d, r) for d, r in CHANNEL], w=2.0, kerb=0.6, h=1.0, seed=0.3, sides=(1,), pitch=5.0)
        kit.fire(at(240.0, 41.0, 0.4), "embers")
        kit.fire(at(272.0, 41.3, 1.0), "smoke")
        for x, y in BASKETS:
            out += kit.fire_basket(V((x, y, 0.0)), 1.8, 5.2)
        return out
