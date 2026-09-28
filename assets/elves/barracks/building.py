"""Elves barracks (ElvenBarracks): EA's hall of warriors kept whole - a long timber hall with a
pointed (lancet-section) slate roof and a carved crest fin along its ridge, glazed tracery gables
with a carved porch at each end, a yard walled by a palisade with obelisk posts, weapon racks
along the hall front and a great mallorn growing up through the roof - crowned the citadel's way
in silver and gold:

- the ridge's crest fin gets a silver cap along its two waves, and a gilt leaf finial on each
  wave's peak;
- the hall front gets six lancet windows (EA's lattice glass in silver frames on silver sills,
  flat work where EA's racks lean on the wall) and a leaf banner on each corner pier (the two
  banners);
- each porch gets a crystal lantern on each of its two pedestals, and a tall crystal lantern hangs
  from each gable's swan-neck horn where EA hung its night lantern;
- the yard's two obelisks get gilt leaf finials.

The cloth takes the player's colour: EA's house-colour model NBHCElvnBarx is Arnor's too, so the
house step ships an own copy, EBHCElvnBarx, shown by the Elven barracks only.
EA's tree (V1, V1A) and the level-3 crown (V2) stay EA's.

All numbers are NBELVNBARXA coordinates (the mesh sits at the model's origin), measured on EA's
model; the building faces -y (the yard) and +x (the east porch), towards the camera:
  hall      walls x -53.0..28.6, y -9.68..24.15; front: plinth y -10.15 up to z 12.3, boards
            y -9.68 up to z 23.6, eave cornice y -11.44 over z 23.3..26.4; corner piers
            x -54.5..-51.2 and 26.8..30.2 (front y -10.56, z 11.8..24); roof (y, z) (-5.3, 41.6)
            (-1.2, 46.0) (2.8, 49.2) (7.2, 51.2); the ridge's crest fin (y 6.3..8.1) in two waves,
            its top edge (x, z) (-51.6, 51.8) (-32.6, 54.0) (-14.0, 51.8) and (-10.4, 51.8) (8.2,
            54.0) (27.3, 51.8), a spike to 54.0 at x -12.2 between them
  porches   pedestals x 28.3..33.0 (west: -57.4..-52.7), y -1.1..0.3 and 14.1..15.6, top z 8.3; the
            porch arch's jambs from z 13.2; the door y 1.3..13.2, apex z 22.5
  yard      front wall y -48.2..-43.7 (coping top z 13.1) x -54.7..3.8, a mid post at x -25.4;
            west wall x -54.7..-51.2 to the hall; east stub x -0.2..3.8, y -47.9..-34.6; obelisks
            (-52.29, -45.74) to z 27.94 and (1.46, -45.49) to z 28.42
  props     EA's racks stand against the front wall at x -3..25.5, y -26..-9.4 (lances to z 38):
            only flat work (d <= 0.7) there; V2 (the level-3 crown) sits over y >= 12.3, z >= 55.9
Footprint x -66.29..41.93, y -50.74..30.24 unchanged; height 60.1 (+20 % allowed: top 70.4)."""
from sagekit.building import Building

from ..style import ElvenStyle

FRONT_Y = -9.68
BAYS = [-44.7 + 13.0 * k for k in range(6)]            # window axes along the front
RIDGE_Y = 7.2
CREST = [[(-51.6, 51.8), (-32.6, 54.0), (-14.0, 51.8)], [(-10.4, 51.8), (8.2, 54.0), (27.3, 51.8)]]
PEDESTALS = [(32.0, -0.4), (32.0, 14.85), (-56.4, -0.4), (-56.4, 14.85)]
OBELISKS = [(-52.29, -45.74, 27.94), (1.46, -45.49, 28.42)]
# EA's night lanterns (N_WINDOW) hang from the horns at x 37.2..42.9 and -67.4..-62.0, y 4.1..10.4,
# z 22.1..32.9: ours hang there (the west one moved in to stay inside the footprint)
HORN_LANTERNS = [(40.0, 7.25, 32.7), (-64.8, 7.25, 32.9)]
HORN_H, HORN_R, HORN_ROD = 6.4, 1.3, 1.6
PEDESTAL_H, PEDESTAL_R = 4.4, 0.62


class Barracks(Building):
    style = ElvenStyle()
    source = "NBElvnBarx_SKN"
    target = "NBELVNBARXA"
    own_model = "EBElvnBarx_SKN"            # men draws NBElvnBarx_SKN too (sagekit/ownership.py)
    sheet = "nbelvnbarx.tga"
    sheet_normal = "nbelvnbarx_nrm.tga"
    own_textures = {"nbelvnbarx.tga": "nbelvnbarH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    tri_budget = 15000
    # the warrior line and his gear stand at the origin in the rest pose; the night meshes are light
    bake_hidden = ("LINE05", "WARRIOR", "LINE02", "BOW", "BOWQUIV01", "QUIVER01", "N_WINDOW", "N_GLOW", "PLANE01")
    views = {
        "rts": ((-12.2, -10.2, 28.6), 325, 50, -38, 50),
        "close": ((-12.2, -10.2, 28.6), 192, 24, -30, 45),
        "ingame": ((-12.2, -10.2, 28.6), 740, 53, -62, 50),
        "front": ((-12.0, -12.0, 16.0), 110, 12, -80, 45),
        "porch": ((30.0, 5.0, 12.0), 70, 15, -20, 45),
    }

    def design(self, kit):
        s = []
        s += self._crest(kit)                   # 1. the ridge: silver cap, gilt finials
        s += self._front(kit)                   # 2. lancet windows, two banners
        s += self._porches(kit)                 # 3. pedestal and horn lanterns
        s += self._obelisks(kit)                # 4. finials on the yard's obelisks
        return s

    def cache_ops(self, variants=None, derived=()):
        """Recipe-side workaround (sagekit/building.py cache_ops, 2026-09-26): our normal map's copy
        for the D1 state, nbelvnbarH_D_NRM, is registered like EA's NBElvnBarx_D_NRM, which no
        asset.dat files (EA's D1 names a map the game never shipped), so the cache step fails.
        Register it like EA's nbelvnbarx_nrm.tga instead, the map it is a copy of."""
        from sagekit.workspace import Workspace
        ea = {k.lower() for k in Workspace(self).normal_variants}
        like = self.sheet_atlas.normal.lower()
        return [("texture", op[1], like, None, None) if op[0] == "texture" and op[2] in ea else op
                for op in super().cache_ops(variants, derived)]

    # ------------------------------------------------------------------ 1. the ridge
    @staticmethod
    def _crest(kit):
        """A silver cap riding the crest fin's top edge (its underside sunk in the fin, wider than it),
        and a gilt leaf finial on each wave's peak."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        a, t, n = V((0, RIDGE_Y, 0)), V((1, 0, 0)), V((0, -1, 0))
        out = []
        for wave in CREST:
            for i, ((xa, za), (xb, zb)) in enumerate(zip(wave, wave[1:])):
                q = [(xa, za - 0.4), (xb, zb - 0.4), (xb, zb + 0.4), (xa, za + 0.4)]
                tags = [None, "trim" if i == len(wave) - 2 else None, "trim", "trim" if i == 0 else None]
                out.append(prism_uz(a, t, n, q, -1.15, 1.15, tags, "trim", "trim"))
            x, z = wave[1]
            out += kit.leaf_finial(x, RIDGE_Y, z + 0.3, 5.6, 2.0)
        return out

    # ------------------------------------------------------------------ 2. the hall front
    @staticmethod
    def _front(kit):
        from mathutils import Vector as V
        from .motifs import lancet_window
        a, t, n = V((0, FRONT_Y, 0)), V((1, 0, 0)), V((0, -1, 0))
        out = []
        for u in BAYS:
            out += lancet_window(kit, a, t, n, u, 2.6, 13.8, 18.4, 21.3, w=0.65, d=0.45, finial=False)
        pier = V((0, -10.56, 0))
        for u in (-52.85, 28.5):
            out += kit.leaf_banner(pier, t, n, u, 22.4, 2.6, 9.6, d=0.25, free=True)     # the pier is no solid block
        return out

    # ------------------------------------------------------------------ 3. porches
    @staticmethod
    def _porches(kit):
        from .motifs import hanging_lantern
        out = []
        for x, y in PEDESTALS:
            out += kit.crystal_lantern(x, y, 8.25, h=PEDESTAL_H, r=PEDESTAL_R)
        for x, y, z in HORN_LANTERNS:
            out += hanging_lantern(kit, x, y, z, h=HORN_H, r=HORN_R, rod=HORN_ROD)
        return out

    # ------------------------------------------------------------------ 4. the yard
    @staticmethod
    def _obelisks(kit):
        out = []
        for x, y, z in OBELISKS:
            out += kit.leaf_finial(x, y, z - 0.35, 4.2, 1.4)
        return out

    @staticmethod
    def night_lights(kit):
        """Starlight where EA's night lanterns glowed (our horn lanterns), the porch lanterns and five of the six
        lancet windows of the hall front (panes without halos: a halo would drape over the sills); not
        the last window, behind the bows of EA's rack (a bow crosses it, and its pane would face the bow)."""
        from sagekit.nightlights import Light
        from .motifs import crystal_light, hanging_base, lantern_glow
        out = [crystal_light(x, y, hanging_base(z, HORN_H, HORN_ROD), HORN_H, HORN_R, "horn %+.0f" % x)
               for x, y, z in HORN_LANTERNS]
        out += [lantern_glow(x, y, hanging_base(z, HORN_H, HORN_ROD), HORN_H, "horn %+.0f" % x)   # EA's glow
                for x, y, z in HORN_LANTERNS]                                                    # cards' place
        out += [crystal_light(x, y, 8.25, PEDESTAL_H, PEDESTAL_R, "porch %+.0f %+.0f" % (x, y), halo=False)
                for x, y in PEDESTALS if x > 0]
        return out + [Light.arch((0, FRONT_Y, 0), (1, 0, 0), (0, -1, 0), u, 2.2, 14.1, 18.4, 20.6, halo=False, reach=1.5,
                             name="front %+.0f" % u) for u in BAYS[:-1]]

    def emphasis(self, c, n):
        if c.z > 50:
            return 1.4                          # the ridge's cap and finials
        if c.y < -9 and 10 < c.z < 24:
            return 1.3                          # the front windows
        return 1.0
