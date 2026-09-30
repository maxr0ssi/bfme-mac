"""Mordor orc pit (MordorOrcPit), pass 2 "the jaws of the pit": EA's crater of rock kept whole and
made the citadel's: a claw of jagged hooked spikes rises from INSIDE the crater's rim and closes over
the pit, open toward the front where the orcs climb out; shelves of glowing coals ring the pit's
foot with real orange forge fire, a dark plume rises out of it; lava seams run down the front
slopes into open lava at the mound's foot; a war drum, a whip post, impaling stakes, ash and bones.

    claw        fourteen spikes (the citadel's Horn: knife-edged, steel outer edge, teeth hooking up,
                a lava seam up the tall ones) every 24 degrees from the inner wall at r 25 round the
                pit's axis (-5, 7), leaning in to tips at r 11.5..14.5, z 39.2 (tall) and 34.5; a gap
                of 48 degrees round 298: the orcs' way out over the rim toward the rally point
                (10, -75); two chains between the tall spikes at the back, meat hooks on one
    forges      seven basalt shelves heaped with coals on the inner wall's foot (z 15.6..16.2, over
                EA's mud floor), four "forge" fires on them; a heavy dark plume ("plume") over the pit
    lava        seams down the front slopes (250, 315, 20 degrees) into an open lava channel and a
                lava pool at the mound's foot, clear of the orcs' way out; embers and a thin smoke
    yard        a war drum and a whip post at the front corner, impaling stakes either side of the
                orcs' way out, an ash heap (-X) and a bone heap (-X+Y)

EA's MBOrcpit_SKN (object MordorOrcPit; role barracks): body ORCPIT, 257 triangles, painted from
MBBStone.tga + MBBStone_NRM.tga (DXT1). In ORCPIT mesh coordinates (identity bone): x -58.92..55.38,
y -41.92..56.72, z 0.00..32.83. Other meshes (EA's, untouched): V2 1512 (MU_Banr_A.tga, the level 3
banners on poles at (-18, 57), (57, -8), (-36, -42), to z 80); ORC 264; V1HIDE00..02 (level 1 mud)
and V1A..V1D (level 2, the pit's floor at z 13..15 and mud heaps in it); ORCPIT01 (rim posts at
(10.8, 35.7), (-35.5, 33.7), (-15, -31.5), (43, 23) and a beam); ORCPIT02 (rock slabs at the foot);
N_WINDOW / N_FIRE (night torch posts at (31, 51), (31.5, -33), (-68, 13)).
Lifecycle models in its Draw module: MBOrcpit_A, MBOrcpit_D1, MBOrcpit_D2, MBOrcpit_D3.
House colour: MBHCOrcpit, drawn by Isengard's tavern too: Mordor's own copy MBHCOrcpit2.

EA's facts (measured 2026-09-30, work/measure.json and the preview stage's own vertices): a ring of
rock round an open pit on the axis (-5, 7): the inner wall from r 20 (ground) to the rim, r 26..32
at z 20..32 (the heads (-16.7, 33.1) z 32.6 and (-5.7, -23.4) z 30.8), the outer slope down to the
ground at r 40..50. The orcs come up out of the pit (ORC at the origin) and rally at (10, -75)
(QueueProductionExitUpdate): the rim toward -Y stays open. Height limit +20 %: z 39.4.
"""
from sagekit.building import Building

from ..style import MordorStyle

AXIS = (-5.0, 7.0)                          # the pit's axis
# the claw: (degrees round the axis, the inner wall's height at r 24 there, tall)
# the claw: (degrees round the axis, the inner wall's height at r 25 there, tall); none at 298 (the way out)
SPIKES = [(322.0, 21.8, True), (346.0, 16.2, False), (10.0, 17.9, True), (34.0, 13.8, False), (58.0, 16.9, True),
          (82.0, 19.7, False), (106.0, 23.8, True), (130.0, 16.2, False), (154.0, 9.9, True), (178.0, 10.4, False),
          (202.0, 14.0, True), (226.0, 7.5, False), (250.0, 12.8, True), (274.0, 19.2, False)]
TIP = {True: (11.5, 39.2, 2.5), False: (14.5, 34.5, 1.9)}   # (tip r, tip z, section scale)
# the pit's forges: ember shelves on the inner wall's foot, (degrees, r, top z); a forge fire over each
SHELVES = [(28.0, 20.5, 15.8), (64.0, 19.5, 16.0), (100.0, 19.5, 16.2), (136.0, 20.5, 15.8), (172.0, 20.5, 15.8),
           (208.0, 20.5, 15.6), (244.0, 20.5, 15.6)]
FORGES = [28.0, 100.0, 172.0, 244.0]
CHAINS = [((10.0, 32.0), (58.0, 32.0), 0), ((58.0, 32.0), (106.0, 33.0), 2)]    # ((deg, z), (deg, z), hooks)
# lava seams down the front slopes: (degrees, [(r, surface z)])
SEAMS = [(250.0, [(28.5, 23.7), (33.0, 24.9), (37.5, 21.8), (42.0, 18.0), (45.0, 12.8), (46.5, 10.3), (48.0, 6.5),
                  (49.5, 0.8)]),
         (315.0, [(25.5, 24.2), (30.0, 20.8), (34.5, 15.1), (39.0, 10.3), (42.0, 6.9), (45.0, 3.2), (46.5, 1.3)]),
         (20.0, [(27.0, 21.6), (33.0, 20.2), (37.5, 17.2), (42.0, 13.9), (45.0, 11.0), (48.0, 6.6), (51.0, 0.4)])]
CHANNELS = [[(300.0, 46.0), (312.0, 46.5), (322.0, 46.0)]]
POOL = (-33.0, -33.0, 0.0)
DRUM = ((44.0, -30.0, 0.55), (0.8, 0.6, 0.0))
WHIP = (38.5, -38.0, 0.65)
STAKES = [((-14.0, -37.5, 0.95), (-0.35, -0.3, 1.0)), ((19.0, -35.0, 0.95), (0.35, -0.3, 1.0)),
          ((24.0, -30.5, 0.95), (0.45, -0.1, 1.0))]
ASH = (-53.0, -22.0, 0.1)
BONES = (-49.0, 42.0, 0.2)

# real fire and smoke (the game's particle systems on bones of the rig), from the design's log
FIRE_POINTS = [
    (9.6, 14.7, 15.8, 'forge'), (-7.9, 23.2, 15.8, 'forge'), (-21.3, 9.3, 15.8, 'forge'), (-12.2, -7.8, 15.8, 'forge'),
    (-5.0, 7.0, 30.0, 'plume'), (-33.0, -33.0, 0.6, 'embers'), (26.1, -27.6, 0.4, 'embers'), (22.0, -30.2, 1.0, 'smoke')
]


class OrcPit(Building):
    style = MordorStyle()
    source = "MBOrcpit_SKN"
    target = "ORCPIT"
    sheet = "MBBStone.tga"
    sheet_normal = "MBBStone_NRM.tga"
    own_textures = {"MBBStone.tga": "MBBStonH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    facet_islands = 8                       # the unwrap overlapped (0.73%): seams at EA's islands and 8-degree turns
    # EA's night torch cards, the level 3 banners and the orc: out of the bakes and review renders
    bake_hidden = ("N_FIRE", "N_WINDOW", "V2", "ORC")
    fire_points = FIRE_POINTS
    views = {
        "rts": ((-1.8, 7.4, 16.4), 340, 50, -38, 50),
        "close": ((-1.8, 7.4, 16.4), 201, 24, -30, 45),
        "ingame": ((-1.8, 7.4, 16.4), 773, 53, -62, 50),
    }

    def design(self, kit):
        from assets.isengard.shapes_industry import logged      # prints the design's FIRE_POINTS
        from assets.men.stable.pieces import drop_loose
        drop_loose(self.target)                 # EA's eight loose vertices (the checks allow none on the target)
        return logged(kit, lambda k: k.retag(self._pieces(k)))

    @staticmethod
    def _pieces(kit):
        import math

        from mathutils import Vector as V

        from .. import shapes_production as P
        cx, cy = AXIS

        def at(deg, r, z=0.0):
            a = math.radians(deg)
            return V((cx + r * math.cos(a), cy + r * math.sin(a), z))
        out = []
        for deg, z, tall in SPIKES:                              # the claw round the pit
            r1, zt, s = TIP[tall]
            out += P.spike(kit, AXIS, deg, 25.0, z - 1.5, r1, zt - (z - 1.5), s, tall)
        for (d0, z0), (d1, z1), hooks in CHAINS:                 # chains slung between the tall spikes, hooks on one
            solids, _ = kit.hung_chain(at(d0, 21.0, z0), at(d1, 21.0, z1), 5.0, link=2.2, w=0.8, th=0.3, segs=5, hooks=hooks)
            out += solids
        for deg, r, z in SHELVES:                                # the forges' ember shelves round the pit's foot
            out += P.ember_shelf(kit, AXIS, deg, r, z, seed=deg * 0.01)
        for deg in FORGES:
            kit.fire(at(deg, 16.5, 15.8), "forge")
        kit.fire(V((cx, cy, 30.0)), "plume")                      # the pit's heavy dark smoke
        for deg, pts in SEAMS:                                   # lava down the front slopes
            out += P.slope_crack(kit, [at(deg + (1.5 if i % 2 else -1.5) * (i > 0), r, z + 0.05)
                                       for i, (r, z) in enumerate(pts)], w=1.8)
        for run in CHANNELS:                                     # open lava at the foot
            out += kit.lava_channel([at(d, r) for d, r in run], w=2.2, kerb=0.6, h=1.0, seed=run[0][0] * 0.01,
                                    sides=(1,), pitch=5.0)
        out += kit.lava_pool(V(POOL), 3.2, seed=1.0)
        kit.fire(V(POOL) + V((0, 0, 0.6)), "embers")
        kit.fire(at(312.0, 46.5, 0.4), "embers")
        kit.fire(at(306.0, 46.0, 1.0), "smoke")
        c, t = DRUM
        out += kit.war_drum(V(c), V(t), r=3.2, w=3.8)
        out += P.whip_post(kit, WHIP, 10.0, seed=1.0)
        for i, (c, d) in enumerate(STAKES):
            out += kit.stake(V(c), V(d), 12.0, r=0.6, barbs=1, seed=i + 2.0)
        out += kit.ash_heap(V(ASH), 3.4, 2.6, seed=3)
        out += P.bone_heap(kit, BONES, 3.0, seed=1.0)
        return out
