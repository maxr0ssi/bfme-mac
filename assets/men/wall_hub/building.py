"""Men wall hub (MenWallHubSmall, ArnorWallHubSmall; model GBWallRmprtN): EA's hexagonal tower
where wall segments meet, kept whole - the ashlar body with its painted corbel arcade, the drum
with its slit windows, the slate dome - and crowned as the citadel's towers are (dome.py, the
shared Gondor tower top):

- a flush parapet round the rim: a black enamel band with silver stars (StarBand) and square
  merlons with capstones, between
- six corbelled bartizans on the corners, slit windows, steel-banded cornices, slate spirelets;
- on the drum: pilasters up its corners and a round-arched window frame (voussoirs, keystone,
  sill) on every face; a steel eave band;
- on the dome: steel ribs up its six edges and faces, a lantern cupola, a steel mast, a gilt orb
  and a spike (EA's stone spike is cleared: the lantern stands where it was).

No banners: hubs repeat along every wall.

EA's hub (OBJECT03, mesh coordinates; the mesh hangs on a bone at z 80.79, turned 60 degrees
about z, so the ground is at mesh z -80.72): a regular hexagon with corners on the x axis (corner
radius 23.44, faces 20.3 from the axis) to z -31.64, a sloped roof in to the drum (corner radius
17.85) at -27.39, the drum to -11.84, an eave lip (18.61), the dome's rings (corner radius, z)
17.81 -11.75, 13.08 -4.24, 7.63 -0.28, 1.36 1.81 and the spike to 17.35. Segments run into any
face (their crown 7.45 either side of the face's middle): nothing new passes a face's plane, and
the bartizans stand clear of the middle 15.8 of every face. The footprint is EA's (x +-23.44,
y +-20.3).

The pieces are static methods so men/wall_hub_upgradeable and men/fortress_wall_hub (EA's
GBGFWHub: the same mesh) reuse them.
"""
from sagekit.building import Building
from sagekit.clear import Box

from ..style import MenStyle

BONE_Z = 80.794                  # the mesh hangs this high: model z = mesh z + BONE_Z
FACE = 20.3                      # the body's faces from the axis (apothem)
RIM = -31.64                     # the body's top (model 49.15; the walls' top is 49.5)
PARAPET = (RIM, -28.3)           # the parapet ring (model 49.15..52.5)
BAND = (-31.1, -29.0)            # its black enamel band (silver stars)
MERLONS = dict(w=2.2, gap=1.6, h=2.6, cap=0.55)
MERLON_TRIM = 4.4                # merlons kept this far from the corners (the bartizans)
BARTIZAN = (20.6, -35.6, 2.05, 7.2, 5.6)   # centre radius along the corners, corbel foot, r, h, spire
DRUM = (15.46, -27.39, -11.84)   # apothem, foot, eave
EAVE = (16.1, -11.8)
DOME = [(-11.7, 15.42), (-4.24, 11.33), (-0.28, 6.61)]
LANTERN = (0.55, 3.9, 6.6)       # z0 (where the dome's corner radius is about 4.7), r, top
FINIAL = (13.2, 29.5)            # orb, tip (model 110.3: +12.4 %)
WINDOW = (-24.6, -16.3, 1.5)     # sill, crown, half width on the drum faces


class WallHub(Building):
    style = MenStyle()
    source = "GBWallRmprtN"
    target = "OBJECT03"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressE.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallHub"
    house_tags = ()                 # no banners: hubs repeat along every wall
    clear = [Box((-2.0, -2.0, 2.4), (2.0, 2.0, 18.0))]          # EA's stone spike (the lantern stands there)
    views = {
        "rts": ((0.0, 0.0, 49.1), 230, 50, -38, 50),              # model space (z up from the ground)
        "close": ((0.0, 0.0, 62.0), 125, 24, -30, 45),
        "ingame": ((0.0, 0.0, 49.1), 580, 53, -62, 50),
    }

    def design(self, kit):
        return self.rim(kit) + self.drum(kit) + self.dome(kit)

    @staticmethod
    def section():
        from ..dome import Section
        return Section(0.0, 0.0, k=6, phase=0.0)

    @classmethod
    def rim(cls, kit):
        """The flush parapet with its enamel band and merlons, and the six corner bartizans."""
        from .. import dome as D
        sec = cls.section()
        out = D.parapet(kit, sec, FACE, *PARAPET, d_in=-2.4, d_out=-0.05, band=(*BAND, "enamel"), merlon=MERLONS,
                        trim=MERLON_TRIM)
        R, z0, r, h, spire = BARTIZAN
        out += D.bartizans(kit, sec, R, z0, r=r, h=h, spire=spire)
        return out

    @classmethod
    def drum(cls, kit):
        """Pilasters up the drum's corners and a window frame on every face."""
        from .. import dome as D
        sec = cls.section()
        half, z0, z1 = DRUM
        out = D.pilasters(sec, half, z0 - 0.3, z1 - 0.6, w=0.75, d=(-0.6, 0.75))
        out += D.window_frames(kit, sec, half, *WINDOW[:2], WINDOW[2], d=(0.0, 0.65))
        return out

    @classmethod
    def dome(cls, kit):
        """Steel ribs, a lantern cupola, a steel mast, a gilt orb and a spike."""
        from .. import dome as D
        return D.crown(kit, cls.section(), EAVE, DOME, lantern=LANTERN, finial=FINIAL)

    def decals(self):
        from ..paint import men_layers
        from ..wall_segment.paintwall import wall_layers
        return [men_layers()[2](zrange=BAND, pitch=3.0, r=0.8),       # silver stars on the rim's band
                wall_layers()()]                                       # EA's joints crisp on the white stone

    def emphasis(self, c, n):
        if c.z > RIM - 4:
            return 1.35                       # the crown: what the RTS camera sees
        return 1.0
