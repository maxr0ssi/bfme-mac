"""Mordor slaughter house (MordorSlaughterHouse), pass 2 "the smoke-house": EA's butchery kept whole
- the hide-roofed hall on its stilts, the slatted decks, the ramp, the turning hook wheel with its
meat - and made the citadel's: a jagged basalt smoke stack rises from the ground at the yard's
front, its mouth opening into a claw of hooked spikes round a real orange fire and a heavy dark
plume; beside it a great smoke-rack of charred timber hangs two rows of meat hooks and carcasses;
butcher blocks, bone heaps, a lava runnel, a gibbet off the gable.

    stack       claw_stack at (25, -60): r 6.5 at its foot, battered, iron bands, ember slits and a
                lava seam, its mouth at z 56, seven spikes to z 73; "chimney" fire and a "plume"
    rack        smoke_rack from (24, -15) to (24, -46): two A-frames to z 26, a top bar and two
                lower bars of hooks with heavy dark carcasses (the new mass at the RTS camera)
    yard        butcher blocks with steel cleavers, two bone heaps round spikes, a lava runnel to the
                stack's foot ("embers")
    hall        a gibbet cage off the ridge's -Y horned end; steel spikes along the +X deck's edge,
                two fire baskets on it (pass 1's bowl on the ridge is gone: perched, it read stuck on)

EA's MBSltrHs_SKN (object MordorSlaughterHouse; role economy): body MBSLTRHS, 832 triangles, painted
from MBSltrHs.tga + MBSltrHs_NRM.tga (DXT1). In MBSLTRHS mesh coordinates (identity bone): x
-53.42..37.54, y -71.42..51.34, z -3.36..63.67. Other meshes (EA's, untouched): V2 794 (the level-up
watch tower with its ladder over the -Y platform, x -56.7..3.2, y -75.8..-35.5, to z 92.2);
HOOKWHEEL 512 (animated: its post at (21, 6), arms r 17 at z 40..60); ORCPORTER, ORCPORTER_STR 258;
RHYNOE_STR 228 (x 3..14, y -71.7..-34.7); N_WINDOW 120 and N_FIRE 24 (night torch posts); MEAT07..10
on the wheel. Lifecycle models in its Draw module: MBSltrHs_A, MBSltrHs_D1, MBSltrHs_D2, MBSltrHs_D3.
House colour: MBHCSltrHs.

EA's facts (measured 2026-09-30, work/measure.json and the preview stage): the hall x -45..-15,
y -10..45, its ridge along y at x -30 from z 56.3 (y 15) up to the horned ends z 61..63.7; eaves at
z 45..46; the lean-to over the deck (x -10..0) at z 33..35; decks at z 20.6 (x -10..0) and z 18.8
(x 5..30, y 22..43); the ramp up from the -Y platform (x -35..-20, y -40..-15, z 3..16); the
platform under the tower (x -43..-12, y -71..-40, z 16..24); the yard slab at z -3.4 (x 0..35, y
-70..20) lies under the terrain (z 0). Kept clear: the wheel's sweep (r 18 round (21, 6)), the tower (V2), the rhino, the ramp.
Height limit +20 %: z 77.
"""
from sagekit.building import Building

from ..style import MordorStyle

GROUND = 0.0                                # the terrain (EA's yard slab at -3.4 lies under it)
STACK = ((25.0, -60.0), 6.5, 56.0, 17.0)                # (x, y), foot r, mouth z, claw H
RACK = ((24.0, -15.0), (24.0, -46.0), 26.0)              # the smoke-rack gantry: its two A-frames' feet, height
BLOCKS = [((10.0, -24.0), (0.0, 1.0)), ((34.0, -30.0), (1.0, 0.3))]
BONES = [(33.0, -8.0), (-4.0, -62.0)]
SEAM = [(34.0, -20.0), (34.5, -36.0), (32.5, -48.0), (29.0, -53.5)]
GIBBET = ((-30.0, -12.0), 54.0)
DECK_SPIKES = ((30.5, 23.0), (30.5, 43.0), 18.8, 7)
BASKETS = [(27.0, 40.0, 18.8), (7.0, 25.0, 18.8)]      # fire baskets on the +X deck

# real fire and smoke (the game's particle systems on bones of the rig), from the design's log
FIRE_POINTS = [
    (25.0, -60.0, 56.2, 'chimney'), (25.0, -60.0, 67.9, 'plume'), (34.4, -34.0, 0.4, 'embers'), (27.0, 40.0, 23.9, 'brazier'),
    (7.0, 25.0, 23.9, 'brazier')
]


class SlaughterHouse(Building):
    style = MordorStyle()
    source = "MBSltrHs_SKN"
    target = "MBSLTRHS"
    sheet = "MBSltrHs.tga"
    sheet_normal = "MBSltrHs_NRM.tga"
    own_textures = {"MBSltrHs.tga": "MBSltrHH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    bake_hidden = ("N_FIRE", "N_WINDOW", "V2", "ORCPORTER", "ORCPORTER_STR", "RHYNOE_STR")
    fire_points = FIRE_POINTS
    views = {
        "rts": ((-7.9, -10.0, 30.2), 367, 50, -38, 50),
        "close": ((-7.9, -10.0, 30.2), 217, 24, -30, 45),
        "ingame": ((-7.9, -10.0, 30.2), 834, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        return logged(kit, lambda k: k.retag(self._pieces(k)))

    @staticmethod
    def _pieces(kit):
        from mathutils import Vector as V

        from .. import shapes_production as P
        from .. import shapes_production_big as PB
        (sx, sy), r, z1, H = STACK                           # the smoke stack, grounded, its mouth clawed
        out = PB.claw_stack(kit, (sx, sy), r, z1, H, n=7, s=1.7, kind="chimney", smoke="plume", seed=1.0)
        p, q, h = RACK                                       # the smoke-rack of carcasses
        out += PB.smoke_rack(kit, (p[0], p[1], GROUND), (q[0], q[1], GROUND), h, rows=2, hooks=5, seed=0.5)
        for c, t in BLOCKS:
            out += P.butcher_block(kit, (c[0], c[1], GROUND + 0.35), t, 1.4)
        for i, (x, y) in enumerate(BONES):
            out += P.bone_heap(kit, (x, y, GROUND + 0.3), 3.2, seed=i * 1.7)
        out += kit.lava_channel([(x, y, GROUND) for x, y in SEAM], w=1.1, kerb=0.6, h=0.8, seed=0.4, pitch=3.5)
        kit.fire(V((34.4, -34.0, GROUND + 0.4)), "embers")
        (gx, gy), gz = GIBBET
        out += kit.gibbet(V((gx, gy, 0)), (0, -1), gz, reach=6.0, drop=4.0, h=7.0, w=2.0)
        (x0, y0), (x1, y1), z, k = DECK_SPIKES
        out += kit.spike_row(V((x0, y0, 0)), V((0, 1, 0)), V((1, 0, 0)), 0.0, y1 - y0, z, 4.5, k, lean=0.35, r=0.45,
                             tag="steel")
        for c in BASKETS:
            out += kit.fire_basket(V(c), 1.7, 4.8)
        return out
