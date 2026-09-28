"""The Gondor keep (GondorKeep, the battle tower): EA's round tower kept whole - the 18-sided
shaft with its six pilasters, the twelve lancet windows of the upper storey, the frieze, the
ribbed slate dome and the gabled porch - and crowned like the citadel's towers (tower.py): a
machicolated gallery (corbels under the frieze, a black band of silver stars on it, a parapet
of square merlons), six corbelled bartizans with slate spirelets engaged on the pilasters, steel
ribs up the dome's folds, a lantern cupola, a gilt orb and a steel spike. The upper windows get
sills, colonnettes and pointed hoods with gilt knobs, between string courses that collar the
pilasters; the porch a voussoir archivolt, raking cornices, a black tympanum with the White Tree,
a winged-helm crest and two buttress pinnacles. Two house-colour banners hang on the pilasters
flanking the porch and White Tree shields on the other four, clear of EA's statue niches (painted
on every fold, z 30..46.6), which a string course under them frames.

EA's GBBtlTwrs.OBJ0 (mesh = model coordinates): shaft vertices at 0, 24, 36, 60, ... degrees
at r 18.34 from z 6.1; pilasters (24..36 + 60k) proud to 19.72 from z 11.1, their capitals
flaring to 21.18 at 90.7; windows (recessed to 16.4, 1.85 wide) at 12 + 60k and 48 + 60k from
63.36, springing at 74.81, crown 77.79 (N_WINDOW: panes 63.25..78.03, glow cards 53.9..87.6,
kept clear); the frieze proud to 19.71 from 90.73 to 95.25; the dome from r 18.42 at 95.25
through 16.43 (103.57), 13.09 (109.38), 8.71 (113.25) to its point at 116.02 (EA's stone ribs
on the pilaster lines, 2 proud). The plinth reaches r 20.18 (21.69 at the pilasters): the
footprint is x -20.18..26.85, |y| <= 21.57, so the gallery's front stays within 1.68 of the
shaft (the fold at 180 degrees) and the bartizans centre at r 19.2. The porch: a front x
23.61, |y| <= 8.11 from z 6.45; its door |y| <= 6.16 to 18.52, arched to 23.85; its gable from
25.95 at the corners to 30.62, the roof rising back to 35.64 at the tower; steps out to x 26.85.
"""
from types import SimpleNamespace as Spec

from sagekit.building import Building

from ..style import MenStyle

KEEP = Spec(R=18.34, out=1.68, frieze_d=1.1, band=(90.9, 95.25), parapet=97.2, par_d=0.55,
            corbel=(86.4, 88.25, 90.15), corbel_u=(-2.4, 0.0, 2.4), corbel_w=0.42, corbel_d=(0.8, 1.6),
            merlon=(1.7, 1.2, 2.3), bartizan=(1.9, 19.2, 84.0, 12.5, 9.0),
            dome=[(95.25, 18.42), (103.57, 16.43), (109.38, 13.09), (113.25, 8.71), (116.02, 0.0)],
            lantern=(114.3, 3.5, 120.4), finial=(124.6, 134.0))
WINDOWS = [a + b for a in range(0, 360, 60) for b in (12, 48)]
WINDOW = dict(half=0.95, z_sill=62.3, z_spring=74.81, z_crown=77.79)
PORCH_X, PORCH_Y, GABLE = 23.61, 8.11, (25.95, 30.62)
PILASTER = 19.72
BANNERS = (30, 330)                  # the pilasters flanking the porch
BANNER = (58.4, 3.0, 17.5)           # top (under the string course), width, length
SHIELDS = (90, 150, 210, 270)        # the other pilasters
SHIELD = (44.0, 1.65, 6.4)           # z of the point, half-width, height


# EA's slate dome panel on GBBtlTwr (upscale pixels, y down): a tapering strip from its eave (y
# 1080, x 808..1306) to its point (1057, 2040), hinted as tiles in steps so it takes the palette's
# slate like the citadel's domes (the colour rules alone made white stone of its pale blue-grey)
_PANEL = [(1075, 252), (1404, 205), (1604, 162), (1816, 106), (2045, 8)]    # (y, half-width about x 1057)


def _dome_tiles(step=40):
    out = []
    for y in range(1075, 2045, step):
        h = next(h0 + (h1 - h0) * (y - y0) / (y1 - y0) for (y0, h0), (y1, h1) in zip(_PANEL, _PANEL[1:]) if y0 <= y <= y1)
        out.append((round(1057 - h), y, round(1057 + h), min(y + step, 2048)))
    return out


DOME_TILES = _dome_tiles()


class Keep(Building):
    style = MenStyle()
    source = "GBBtlTwrs"
    target = "OBJ0"
    sheet = "GBBtlTwr.tga"
    sheet_normal = "GBBtlTwr_NRM.tga"
    own_textures = {"GBBtlTwr.tga": "GBBtlTwH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((3.3, -0.0, 62.0), 300, 50, -38, 50),
        "close": ((3.3, -0.0, 64.0), 215, 24, -30, 45),
        "crown": ((0.0, 0.0, 106.0), 100, 20, -38, 45),
        "porch": ((22.0, 0.0, 20.0), 62, 12, -24, 45),
        "ingame": ((3.3, -0.0, 58.2), 661, 53, -62, 50),
    }

    @property
    def sheet_atlas(self):
        a = super().sheet_atlas
        a.mask_hints = {"tiles": DOME_TILES}
        return a

    def design(self, kit):
        from . import tower
        s = KEEP
        out = tower.gallery(kit, s)
        out += tower.bartizans(kit, s)
        out += tower.dome(kit, s, rib_angles=range(0, 360, 60))
        for z in (27.6, 59.8, 80.9):
            out += tower.course(s.R, z, pil_d=1.75)
        out += tower.pilaster_bases(s.R, 4.3, 9.0, 1.98)
        out += tower.fold_pinnacles(kit, s)
        for ang in WINDOWS:
            out += tower.hood(*tower.face(s.R, ang), **WINDOW)
        out += self._porch(kit)
        for ang in BANNERS:
            out += kit.banner(*tower.pilaster(PILASTER, ang), 0.0, *BANNER, d=0.7)
        for ang in SHIELDS:
            out += tower.shield(kit, *tower.pilaster(PILASTER, ang), 0.0, *SHIELD)
        return out

    @staticmethod
    def _porch(kit):
        """The porch front (x = 23.61): a voussoir archivolt round EA's door arch, a black tympanum
        with the gilt star, raking cornices, a winged-helm crest on the apex and a buttress pier
        with a pinnacle at each front corner."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz
        A, T, N = V((PORCH_X, 0, 0)), V((0, 1, 0)), V((1, 0, 0))
        z0, apex = GABLE
        out = kit.voussoirs(A, T, N, (6.25, 5.4, 18.52), (7.95, 7.0, 18.52), -0.2, 0.75, count=9, key=(0.8, 26.4, 0.35))
        out.append(prism_uz(A, T, N, [(-7.2, z0 + 0.35), (7.2, z0 + 0.35), (0.0, apex - 0.3)], 0.0, 0.14,
                            ["stoneB"] * 3, "enamel", None))
        out += kit.white_tree(A, T, N, 0.0, 26.65, 3.1, 0.3, r=0.12)
        for e in (-1, 1):
            poly = [(0.0, apex), (e * PORCH_Y, z0), (e * (PORCH_Y + 0.9), z0 - 0.15), (0.0, apex + 0.95)]
            out.append(prism_uz(A, T, N, poly, -0.4, 0.95, ["stoneB", "stoneB", "slate", None], "course", "stoneB"))
            out += kit.pinnacle(PORCH_X, e * PORCH_Y, 4.0, 26.4, half=0.85, spire=3.2)
            out.append(prism_uz(A, T, N, [(e * PORCH_Y - 1.05, 16.6), (e * PORCH_Y + 1.05, 16.6), (e * PORCH_Y + 1.05, 17.5),
                                          (e * PORCH_Y - 1.05, 17.5)], -1.05, 1.05, ["stoneB", "stoneB", "top", "stoneB"],
                                "course", "stoneB"))
        out += kit.winged_crest(A, T, N, 0.0, apex + 0.2, -0.6, 0.5, s=0.72)
        return out

    def decals(self):
        from ..paint import men_layers
        z0, z1 = KEEP.band
        return [men_layers()[2](zrange=(z0 - 0.1, z1 - 0.05), pitch=3.0, r=1.1)]

    def emphasis(self, c, n):
        if c.z > 84:
            return 1.4                        # the crown, dome and lantern
        if c.x > 21 and c.z < 36:
            return 1.3                        # the porch
        return 1.0
