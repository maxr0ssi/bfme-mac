"""The Gondor sentry tower (GondorSentryTower): the keep's smaller sister, crowned the same way
(assets/men/keep/tower.py). EA's round shaft is kept whole - its six pilasters, the frieze and
the tiled dome - and gains the citadel's crown: a moulded lip under the frieze, a black band
of silver stars on it, a parapet of square merlons with a small pinnacle over each fold, six corbelled
bartizans with slate spirelets engaged on the pilasters, twelve steel ribs up the dome (now
slate, as the citadel's), a lantern cupola, a gilt orb and a steel spike. Lower down: string
courses collaring the pilasters, plinth blocks at the pilasters' feet, and a sill and pointed
hood with a gilt knob on each of the six windows. One house-colour banner. No corbels under the
frieze here (the keep has them): EA painted a winged helm on every face there (z 55.4..61.4),
and it stays in view.

EA's GBBtlTwrM.GBBTLTWRMINI01 (mesh = model coordinates): the keep's plan at r 13.47 (vertices at
0, 24, 36, 60, ... degrees) from z 5.51, pilasters proud to 14.48 from 10.0; the frieze proud to
14.47 from 61.39 up to the dome's lip at 65.49; the dome through 13.38 (70.8), 10.0 (76.05), 6.4
(79.54) to its point at 81.58. Windows (WINDOW_N01, kept clear) on the folds 0, 60, ...: 1.4
wide, 40.17 up to 48.83, pointed to 51.09. The footprint (the plinth, r 14.82 / 15.93 at the
pilasters) is |x| <= 14.82, |y| <= 15.84: the gallery's front stays within 1.33 of the shaft at
the folds facing x, the bartizans centre at r 14.0. Ships in place (also drawn, as an editor
state, on the base-defence plot)."""
from types import SimpleNamespace as Spec

from sagekit.building import Building

from ..keep.building import DOME_TILES
from ..style import MenStyle

SENTRY = Spec(R=13.47, out=1.2, frieze_d=0.8, band=(61.55, 65.49), parapet=67.2, par_d=0.45,
              corbel=(57.2, 59.0, 60.8), corbel_u=(), corbel_w=0.33, corbel_d=(0.6, 1.1), lip=0.45,
              merlon=(1.3, 0.95, 1.8), bartizan=(1.45, 14.0, 56.0, 10.0, 7.0),
              dome=[(65.49, 14.47), (70.8, 13.38), (76.05, 10.0), (79.54, 6.4), (81.58, 0.0)],
              lantern=(80.3, 2.5, 84.6), finial=(88.6, 96.3))
WINDOW = dict(half=0.72, z_sill=39.4, z_spring=48.83, z_crown=51.09, d=0.45, back=-0.55)
BANNER = (312, 37.0, 3.0, 15.5)     # face, top (under the sills), width, length


class SentryTower(Building):
    style = MenStyle()
    source = "GBBtlTwrM"
    target = "GBBTLTWRMINI01"
    sheet = "GBBtlTwrM.tga"
    sheet_normal = "GBBtlTwrM_NRM.tga"
    own_textures = {"GBBtlTwrM.tga": "GBBtlTwrH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((0.0, -0.0, 44.0), 215, 50, -38, 50),
        "close": ((0.0, -0.0, 46.0), 150, 24, -30, 45),
        "crown": ((0.0, 0.0, 74.0), 72, 20, -38, 45),
        "ingame": ((0.0, -0.0, 40.9), 461, 53, -62, 50),
    }

    @property
    def sheet_atlas(self):
        """EA's sheet with the dome's tiles hinted as tiles (the keep's layout): the palette's slate."""
        a = super().sheet_atlas
        a.mask_hints = {"tiles": DOME_TILES}
        return a

    def variants(self, install):
        """Arnor's really damaged GBBtlTwrM_D2 draws the body with the crack decal GBMTDecal.tga
        in place of its sheet's normal map. The derived model takes our variant of it, which W3D
        patches in place, so it needs a name as long as EA's: GBMTDecaH.tga (free in EA's files),
        not the taxonomy's GBBtlTwrHMTDecal.tga (a framework gap: own_variant_name assumes a
        variant named after the sheet)."""
        out = super().variants(install)
        for k in list(out):
            if k.lower() == "gbmtdecal.tga":
                out[k] = "GBMTDecaH.tga"
        return out

    def design(self, kit):
        from ..keep import tower
        s = SENTRY
        out = tower.gallery(kit, s)
        out += tower.bartizans(kit, s)
        out += tower.fold_pinnacles(kit, s, half=0.4, h=2.0, spire=2.2)
        out += tower.dome(kit, s, rib_angles=range(0, 360, 30), z_from=s.parapet)
        for z in (33.4, 54.6):
            out += tower.course(s.R, z, h=0.7, d=0.45, pil_d=1.4)
        out += tower.pilaster_bases(s.R, 3.9, 8.0, 1.45)
        for ang in range(0, 360, 60):
            out += tower.hood(*tower.fold(s.R, ang), **WINDOW)
        face, top, width, length = BANNER
        out += kit.banner(*tower.face(s.R, face), 0.0, top, width, length, d=0.8)
        return out

    def decals(self):
        from ..paint import men_layers
        z0, z1 = SENTRY.band
        return [men_layers()[2](zrange=(z0 - 0.1, z1 - 0.05), pitch=2.6, r=0.95)]

    def emphasis(self, c, n):
        return 1.4 if c.z > 55 else 1.0
