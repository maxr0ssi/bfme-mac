"""Men forge (GondorForge): EA's body kept whole - the gabled hall with its corner piers and
parapet gables, the hearth and its chimney on the yard front, the forge bed where the smith
works, the weapon platform - and dressed like the citadel.

EA's GBBlkSmith_SKN, body GBBLKSMITH (483 triangles), painted from GBBlkSmithNew.tga (DXT5, own
copy GBBlkSmithNeH.tga); new faces sample the Men atlas (GBFortress1). Model coordinates are the
mesh's. What EA's body is, measured:

    hall    x -27.4..27.4, y 13.1 (the yard front) .. 35.8, the eaves at 35.7, the roof rising
            1.25 per unit to its ridge at y 24.45, z 48.6; the gable parapets (x 23.4..27.4 each
            side) rise above it to their apexes at (+-25.24, 24.34, 50.5); the corner piers
            x +-(23.2..28.24), y 9.8..13.3 and 35.7..39.2, to 40.4 under EA's finials (to 47.4)
    front   the door at x 13.3 (half 6.75, jambs 15, crown 21.5); little windows at z 28.4-31
            over x 6.6, 13.5, 20.3 and -15.9 (EA's night quads)
    east    the gable end x 27.39: a door at y 25 (half 5.5, jambs 15.5, crown 21), three
            windows over it at z 27.5-30.5 (y 18.85, 24.65, 30.15)
    hearth  the block x -16.85..4.58 standing out to y 7.38, its top at about 22; the fire's
            opening x -13.35..0.65 up to 18.5 (EA's fire plane FIREPLANE01 behind it, x -13.2..-1,
            y 7.6..13.3, z 6.7..28.6), a hood over the forge bed x -8.5..-3.5 out to y -4.4; the
            chimney x -10.9..-1.4, y 7.4..17.7 to 50.9, its cap from 52 to 55.25; smoke
            emitters at z 48 just outside its four faces (CHIMNEY, CHIMNEY01-03)
    levels  V1 (level 2) sets towers round the four corner piers (x +-23..32, y 9..20 and
            32..43, to 47, capped to 52) and yard walls; V2 (level 3) a belfry from the roof
            behind the ridge (x -8.3..9, y 23.7..41.1, from 48.3)

What stands on it here (no cloth: EA's house banner GBHCBlkSmith is the forge's one):

    chimney steel bands, a sable star band, a corbelled cornice under the cap (the smoke
            emitters' band kept clear), a gilt knob on the cap, a White Tree roundel on its front
    roof    a steel ridge roll with cresting and gilt knobs (stopping short of V2's belfry), two
            slate dormers with arched windows on the yard slope
    front   a voussoir archivolt round the door, surrounds round EA's windows, a sable frieze of
            gilt stars and a dentilled cornice along the eaves, a cornice on the hearth's top
    gables  pinnacles on the parapets' apexes; on the east (and west) gable an archivolt round
            the door, surrounds round the windows, a string course, and EA's painted shield
            raised as a steel-framed sable shield with the White Tree
    piers   moulded caps with gilt orbs round EA's finials (inside V1's towers at level 2)
"""
from sagekit.building import Building

from ..style import MenStyle

FRONT_Y, EAVE = 13.11, 35.7
DOOR = (13.3, 6.75, 15.0, 6.5)                  # centre x, half, springing, rise
WINDOWS = [(6.62, 1.36), (13.53, 1.81), (20.33, 1.36), (-15.94, 1.35)]     # front: centre x, half
GABLE_X, GABLE_DOOR = 27.39, (25.0, 5.5, 15.5, 5.5)
SHIELD = (24.4, 36.4, 3.3, 8.2)                 # EA's painted shield in the gable: u, point z, half, height
GABLE_WINDOWS = [(18.85, 1.35), (24.65, 1.65), (30.15, 1.35)]
CHIMNEY = (-10.9, -1.4, 7.4, 17.7, 50.9)        # x0, x1, y0, y1, top
CAP_TOP = (-6.24, 12.59, 55.25)
PIERS = [(23.2, 28.24, 9.8, 13.3), (23.2, 28.24, 35.67, 39.19)]
RIDGE_Z, RIDGE_Y = 48.6, 24.45
NOT_BAKED = ("RUSAM01", "SWORD STAND-IN", "N_WINDOW", "V1", "V2", "FIREPLANE01")


def front(z=0.0):
    """(a, t, n) on the hall's yard front: u = x."""
    from mathutils import Vector as V
    return V((0, FRONT_Y, 0)), V((1, 0, 0)), V((0, -1, 0))


def east():
    """(a, t, n) on the east gable end: u = y."""
    from mathutils import Vector as V
    return V((GABLE_X, 0, 0)), V((0, 1, 0)), V((1, 0, 0))


class Forge(Building):
    style = MenStyle()
    source = "GBBlkSmith_SKN"
    target = "GBBLKSMITH"
    sheet = "GBBlkSmithNew.tga"
    sheet_normal = "GBBlkSmithNew_NRM.tga"
    own_textures = {"GBBlkSmithNew.tga": "GBBlkSmithNeH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    bake_hidden = NOT_BAKED
    views = {
        "rts": ((-0.0, 0.1, 27.6), 244, 50, -38, 50),
        "close": ((2.0, 10.0, 30.0), 150, 26, -36, 45),
        "gable": ((27.0, 24.0, 30.0), 90, 14, -10, 45),
        "hearth": ((-6.0, 8.0, 30.0), 90, 18, -70, 45),
        "ingame": ((-0.0, 0.1, 27.6), 555, 53, -62, 50),
    }

    def design(self, kit):
        from ..stable.pieces import drop_loose, mirrored
        drop_loose(self.target)                 # EA's four loose vertices (the checks allow none)
        gable = self._gable(kit)
        return (self._chimney(kit) + self._roof(kit) + self._front(kit) + self._hearth(kit) + gable
                + mirrored(gable, x0=0.0) + self._piers(kit) + mirrored(self._piers(kit), x0=0.0))

    # ------------------------------------------------------------------ the chimney
    @staticmethod
    def _chimney(kit):
        """Bands round the stack's three yard-side faces (its back runs into the roof), a sable
        star band, a corbelled cornice from 49.6 under the cap (the emitters at 48 stay clear), a
        roundel on the front, a gilt knob on the cap."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import sweep

        from ..motifs import corbel_table, knob, roundel, star_frieze
        x0, x1, y0, y1, _ = CHIMNEY
        path = [(x0, y1), (x0, y0), (x1, y0), (x1, y1)]
        c = ((x0 + x1) / 2, (y0 + y1) / 2)
        out = []
        for z0, z1, d, tag in ((36.0, 36.9, 0.55, "course"), (44.0, 45.0, 0.45, "trim"), (49.6, 50.9, 0.9, "course")):
            prof = [(-0.3, z0), (d, z0), (d, z1), (-0.3, z1)]
            out += sweep(path, prof, ["stoneB", tag, "top", None], center=c)[0]
        fa, ft, fn = V((0, y0, 0)), V((1, 0, 0)), V((0, -1, 0))
        out += star_frieze(kit, fa, ft, fn, x0 + 0.2, x1 - 0.2, 41.6, h=1.6, d1=0.4, count=3)
        out += corbel_table(kit, fa, ft, fn, x0 + 0.6, x1 - 0.6, 48.9, pitch=2.4, w=0.4, d1=0.4, d2=0.8, h=0.35)
        out += roundel(kit, fa, ft, fn, c[0], 30.4, 2.9, d=0.3)
        cx, cy, cz = CAP_TOP
        out += knob(cx, cy, cz - 0.6, cz + 5.2, r=0.75)
        return out

    # ------------------------------------------------------------------ the roof
    @staticmethod
    def _roof(kit):
        """The ridge roll stops at x +-9.6 (V2's belfry stands over the middle at level 3) and at
        the parapets; dormers at x -19 and 17 (clear of the chimney, the door's windows and the
        smoke emitter at (-15, 19, 36.9)): fronts at y 14.0, backs buried at y 20.4."""
        from ..motifs import ridge
        from ..stable.pieces import dormer
        out = []
        for xa, xb in ((-23.0, -9.8), (9.8, 23.0)):
            out += ridge((xa, RIDGE_Y, RIDGE_Z), (xb, RIDGE_Y, RIDGE_Z), r=0.32, cresting=2.1, spike=1.6)
        a, t, n = front()
        for u in (-19.0, 17.0):
            out += dormer(kit, a, t, n, u, -0.9, 36.5, 40.1, 2.2, 2.0, -7.3)
        return out

    # ------------------------------------------------------------------ the yard front
    @staticmethod
    def _front(kit):
        from ..motifs import star_frieze, window_surround
        from ..stable.pieces import archivolt, cornice
        a, t, n = front()
        out = archivolt(kit, a, t, n, *DOOR)
        for u, h in WINDOWS:
            out += window_surround(kit, a, t, n, u, h, 28.4, 30.8, rise=0, w=0.45, d=0.4, sill=True)
        for u0, u1 in ((-23.0, -11.3), (-1.0, 23.0)):
            out += star_frieze(kit, a, t, n, u0, u1, 31.85, h=1.35, d1=0.45, pitch=2.8)
            out += cornice(a, t, n, u0, u1, 33.2, depth=1.3, pitch=1.0)      # its top under the eave (35.7)
        return out

    @staticmethod
    def _hearth(kit):
        """A moulded cornice along the hearth block's top (its face y 7.38; the chimney runs up
        through it), clear of the hood over the forge bed (x -8.5..-3.5)."""
        from mathutils import Vector as V

        from ..motifs import course
        a, t, n = V((0, 7.38, 0)), V((1, 0, 0)), V((0, -1, 0))
        out = []
        for u0, u1 in ((-16.85, -9.0), (-3.0, 4.58)):
            out += course(a, t, n, u0, u1, 20.6, h=0.9, d=0.7)
        return out

    # ------------------------------------------------------------------ the gable ends
    @staticmethod
    def _gable(kit):
        """The east gable end (the west one is its mirror): an archivolt round the door, surrounds
        round the windows, a string course at the eaves, a shield over EA's painted one and the apex pinnacle."""
        from ..motifs import course, window_surround
        from ..stable.pieces import archivolt
        a, t, n = east()
        out = archivolt(kit, a, t, n, *GABLE_DOOR, d=0.5)          # its keystone inside x 28.24 (EA's piers)
        for u, h in GABLE_WINDOWS:
            out += window_surround(kit, a, t, n, u, h, 27.6, 29.9, rise=h * 0.4, w=0.45, d=0.4)
        out += course(a, t, n, 13.4, 35.6, 34.8, h=0.8, d=0.6)
        out += kit.shield(a, t, n, SHIELD[0], SHIELD[1], SHIELD[2], SHIELD[3], d=-0.5)    # over EA's painted one
        out += kit.pinnacle(25.4, 24.35, 50.2, 52.0, half=1.0, spire=3.8)
        return out

    @staticmethod
    def _piers(kit):
        """Moulded caps round the east piers' tops (flush with the footprint's edges), EA's finials
        standing out of them, gilt orbs on the outer corners."""
        from ..motifs import box, knob
        out = []
        for x0, x1, y0, y1 in PIERS:            # the caps stay inside EA's footprint (x 28.24, y 39.19)
            front = y0 < 20
            out.append(box(x0 - 0.45, x1 - 0.05, y0 - 0.45 if front else y0 - 0.45, y1 + 0.45 if front else y1 - 0.05,
                           39.3, 40.5, "course"))
            cy = y0 + 0.75 if y0 < 20 else y1 - 0.75
            out += knob(x1 - 0.75, cy, 40.4, 43.4, r=0.45)
        return out

    @property
    def sheet_atlas(self):
        from ..prodkit import with_tiles
        return with_tiles(super().sheet_atlas, [(0, 0, 184, 224)])     # EA's slate roof stays slate

    def decals(self):
        from ..stable.pieces import KeepFire         # the forge bed's coals, the hearth's glow and the planks stay EA's
        return [KeepFire(((-15.5, -22.0, -1.0), (2.5, 12.0, 30.0)), hue=(0.0, 62.0), sat=(0.22, 0.36), val=(0.06, 0.16)),
                KeepFire(((-30.0, -40.0, -1.0), (30.0, 40.0, 60.0)), hue=(12.0, 48.0), sat=(0.3, 0.44), val=(0.14, 0.26)),
                KeepFire(((-30.0, -40.0, -1.0), (30.0, -26.0, 15.0)), hue=(12.0, 48.0), sat=(0.16, 0.28), val=(0.08, 0.18))]   # planks

    def variants(self, install):
        from ..levels import with_damaged      # EA's damaged forge (D1-D3) draws GBBlkSmithN_D
        from ..prodkit import same_length_variants     # ... as GBBlkSmithH_D (W3D renames in place)
        return same_length_variants(self, install, with_damaged(self, super().variants(install), "GBBlkSmithN_D.tga"))

    def emphasis(self, c, n):
        if c.z > 30:
            return 1.35                       # the chimney, roof, cornice and gable heads
        return 1.0
