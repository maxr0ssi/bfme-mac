"""The Ivory Tower (UPGRADE_IVORY_TOWER, Draw ModuleTag_IvoryTowerDraw of MenFortressCitadel): EA's
slender tower kept whole - the hexagonal base with its corner buttresses and pointed arches, the
middle storey with its round-arched windows and fleur-de-lis corner blocks, the panelled upper
shaft with its corner columns, the flared cornice, the belfry of tracery windows and its ribbed
spire - and crowned the way the citadel crowns its four towers (citadel_motifs.py): a
machicolated gallery round the upper shaft's top (corbels, a black band of silver stars, a
parapet of square merlons), six corbelled bartizans with slate spirelets at the shaft's corners,
so the belfry rises out of a ring of spires, pinnacles with steel orbs on the middle storey's six
corner blocks, steel ribs up the spire's edges and the citadel's finial - steel mast, gilt orb,
ringed spike - over it, the tallest point of the fortress. The middle storey's painted windows get
stone sills and voussoir hoods with keystones; a black band of silver stars under a cornice rings
the base's top, and pinnacles stand on its six corner buttresses.

EA's GBFITOWER (402 triangles, drawn at the fortress's origin; mesh = fortress coordinates, the
tower's axis at (0, 0)): the base z 11.58..66.98, a hexagon of apothem 13.57 (faces at -30, 30,
90, ... degrees) with triangular corner buttresses to r 16.9 (0, 60, ...); the middle storey
83.9..116.5, faces at 30 + 60k (apothem 12.6..13.0), its corner blocks (0 + 60k, to r 12.86)
notched on top at 116.5..122.8; the upper shaft 114.5..143.7 turned 30 degrees (faces at 0 + 60k,
apothem 9.84, central panels |u| <= 2.9) with corner columns at 30 + 60k (r 10.3..10.8); the
flared cornice 143.7..151.1 (r 8.0..8.65); the belfry 151.1..167.8 (corners at 30 + 60k, r 6.2);
the spire 167.8 (r 6.2), 173.3 (r 3.5 at 30 + 60k) to its point at 177.86. The footprint is x
-16.9..16.73, |y| <= 14.38 (the bartizans centre at r 11.9 so they stay inside it); height
166.28, +20 % allowed: the finial ends at z 196 (+10.9 %, the citadel grew +10.6 %).
"""
import math

from sagekit.building import Building

from ..style import MenStyle

SHAFT_A = 9.9                         # the upper shaft's apothem (faces at 0 + 60k), a hair out
GALLERY_S, GALLERY_Z = 0.85, 138.5    # the gallery's scale (1 = the citadel's) and its corbels' foot
BARTIZAN = dict(R=11.9, z0=135.8, r=1.6, h=7.8, spire=6.2)
PINNACLE = dict(R=11.45, z0=122.6, z1=125.2, half=0.85, spire=3.4)
SPIRE = [(167.8, 6.2), (173.3, 3.5), (177.86, 0.0)]      # (z, r) at the spire's edges (30 + 60k)
FINIAL = (176.9, 184.2, 196.0)                             # mast foot, orb, tip
BASE_A, BAND = 13.57, (63.2, 65.7)    # the base's apothem (faces at 30 + 60k) and its black star band
# the middle storey's six faces (angle, apothem) and their painted round-arched windows (|u| 3.0
# outside the frame, sill 87.6, crown 107.5): a sill and a hood of voussoirs with a keystone
MIDDLE = [(30, 12.55), (90, 13.0), (150, 13.57), (210, 12.69), (270, 12.99), (330, 13.57)]
HOOD = dict(inner=(3.25, 3.3, 104.2), outer=(3.95, 4.05, 104.2), sill=(87.1, 87.8))
BUTTRESS = dict(R=15.0, z0=66.9, z1=71.2, half=1.0, spire=4.6)     # pinnacles on the corner buttresses


class FortressIvoryTower(Building):
    style = MenStyle()
    source = "GBFITower"
    target = "GBFITOWER"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressL.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_IvoryTowerDraw",)
    tri_budget = 6000
    views = {
        "rts": ((0.0, 0.0, 100.0), 400, 50, -38, 50),
        "close": ((0.0, 0.0, 150.0), 120, 20, -30, 45),
        "crown": ((0.0, 0.0, 160.0), 70, 30, -30, 45),
        "ingame": ((0.0, 0.0, 94.7), 860, 53, -62, 50),
    }

    def design(self, kit):
        from . import citadel_motifs as M
        out = []
        path = M.polygon(0.0, 0.0, SHAFT_A, 6, phase=math.pi / 6)      # corners at 30 + 60k: faces at 0 + 60k
        gal, _ = M.gallery(kit, path, (0.0, 0.0), GALLERY_Z, s=GALLERY_S)
        out += gal
        for k in range(6):
            a = math.radians(30 + 60 * k)
            b = BARTIZAN
            out += kit.bartizan(b["R"] * math.cos(a), b["R"] * math.sin(a), b["z0"], r=b["r"], h=b["h"],
                                spire=b["spire"], facing=a)
        for k in range(6):
            a = math.radians(60 * k)
            p = PINNACLE
            out += kit.pinnacle(p["R"] * math.cos(a), p["R"] * math.sin(a), p["z0"], p["z1"], half=p["half"], spire=p["spire"])
        out += self._base_band(M)
        out += self._windows(M)
        for k in range(6):
            a = math.radians(60 * k)
            p = BUTTRESS
            out += kit.pinnacle(p["R"] * math.cos(a), p["R"] * math.sin(a), p["z0"], p["z1"], half=p["half"], spire=p["spire"])
        rings = [[(r * math.cos(math.radians(30 + 60 * k)), r * math.sin(math.radians(30 + 60 * k)), z) for k in range(6)]
                 for z, r in SPIRE[:-1]] + [[(0.0, 0.0, SPIRE[-1][0] - 0.4)] * 6]
        out += M.spire_ribs(kit, 0.0, 0.0, rings)
        out += M.finial(kit, 0.0, 0.0, FINIAL[0], FINIAL[1], FINIAL[2], collar=(1.25, 175.6, 177.4))
        return out

    @staticmethod
    def _windows(M):
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz
        out = []
        for ang, ap in MIDDLE:
            n = V((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
            t = V((-n.y, n.x, 0))
            a = n * ap
            out += M.voussoirs(a, t, n, HOOD["inner"], HOOD["outer"], -0.2, 0.55, count=7, key=(0.6, 108.9, 0.25))
            z0, z1 = HOOD["sill"]
            out.append(prism_uz(a, t, n, [(-3.3, z0), (3.3, z0), (3.3, z1), (-3.3, z1)], -0.2, 0.7,
                                ["stoneB", "stoneB", "top", "stoneB"], "course", "stoneB"))
        return out

    @staticmethod
    def _base_band(M):
        """A black band of silver stars under a moulded cornice round the base's top, between the
        corner buttresses (the sweep runs through them, buried)."""
        from sagekit.blender.geometry import sweep
        path = M.polygon(0.0, 0.0, BASE_A, 6, phase=0.0)
        z0, z1 = BAND
        band = [(-0.4, z0 - 0.5), (0.25, z0 - 0.5), (0.4, z0), (0.4, z1), (-0.4, z1)]
        out = sweep(path, band, ["stoneB", "course", "enamel", "top", None], center=(0, 0))[0]
        return out + M.cornice(path, z1, out=0.65, h=1.4, back=0.4, center=(0, 0))

    def decals(self):
        from .citadel_motifs import SLAB, star_band
        s, z0 = GALLERY_S, GALLERY_Z
        return [star_band((z0 + SLAB[1][1] * s, z0 + SLAB[3][1] * s), pitch=3.2 * s, r=0.95 * s),
                star_band((BAND[0] + 0.2, BAND[1] - 0.2), pitch=3.0, r=0.95)]

    def emphasis(self, c, n):
        return 1.35 if c.z > 112 else 1.0
