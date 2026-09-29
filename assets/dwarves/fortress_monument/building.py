"""The fortress's monument (UPGRADE_FORTRESS_MONUMENT, Draw ModuleTag_MightyCatapultTowerDraw of
DwarvenFortressCitadel): the central keep that carries the Mighty Catapult, crowned.

The crown: EA's drum (the catapult's seat) gets a corbelled rune belt round its foot, a big
Erebor-blue banner on each of its six faces between the stone ribs, a bronze cornice at the rim
with a stepped merlon (triangle frieze) over each banner, and a gilded stepped spire (rune collar,
shaft, ring, needle to z 183) on each of the six ribs - the fortress's highest point. Lower down,
a rune belt rings the shaft under the statue cornice, and four long banners hang from it over the
shaft's medallion panels.

EA's model (mesh DBFGCAP; its bone lifts it by -1.58, so mesh z = world z + 1.58): a square shaft
(±17.23) with corner buttresses to z 84.6, a medallion panel on each face (outer face |x| or |y|
15.12, 22.4 wide, z 66.7..95.9), a pointed cornice at z 100..108, a pair of Atlas statues on each
face (z 108..135.4), and the drum: a 12-gon (apothem 16.15, faces toward 0, 30, 60... degrees) on
a corbel from z 135.5, to its parapet at 158..161.4 round the catapult floor (z 152.7, radius
13.53; the catapult spawns at world z 155 and turns within radius ~14.3). Six pointed ribs stand
on the faces toward 0, 60, ... degrees (outer face at radial 18.73, ±4.33 wide, ridge z 162.93)
and set the bounding box; the six faces between them are clear. Nothing new comes inside radius
15.6 above the rim, so the catapult turns freely; everything stays inside EA's footprint. All
measurements in DBFGCAP mesh coordinates, taken from the original model."""
import math

from sagekit.building import Building

from ..style import DwarvenStyle


AP = 16.15                                    # the drum's apothem (a 12-gon, faces at 0, 30, 60, ... degrees)
FACES = [math.radians(30 + 60 * k) for k in range(6)]      # the drum faces between the ribs
RIBS = [math.radians(60 * k) for k in range(6)]


def ring12(ap, z):
    """12-gon like the drum (vertices at 15, 45, ... degrees), apothem ap, at height z."""
    from mathutils import Vector as V
    r = ap / math.cos(math.radians(15))
    return [V((r * math.cos(math.radians(15 + 30 * k)), r * math.sin(math.radians(15 + 30 * k)), z)) for k in range(12)]


def axes(ang):
    """(outward normal, tangent) of a face or rib at angle ang (radians)."""
    from mathutils import Vector as V
    return V((math.cos(ang), math.sin(ang), 0)), V((-math.sin(ang), math.cos(ang), 0))


class FortressMonument(Building):
    style = DwarvenStyle()
    source = "DBFGCap"
    target = "DBFGCAP"
    sheet = None                                                # the faction atlas DBFortress1
    own_textures = {"DBFortress1.tga": "DBFortressM.tga"}
    parts = ("ModuleTag_MightyCatapultTowerDraw",)
    bake_hidden = ("P1",)
    tri_budget = 5000
    facet_islands = True        # EA's Atlas statues fold over themselves unwrapped uncut
    views = {
        "rts": ((0, 0, 110), 300, 50, -38, 50),
        "close": ((0, 0, 148), 95, 22, -30, 45),
        "ingame": ((0, 0, 90), 800, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft, prism_uz
        O = V((0, 0, 0))
        out = []

        # 1. the corbelled rune belt round the drum's foot (the ribs run through it)
        rings = [ring12(15.4, 135.8), ring12(16.9, 136.8), ring12(16.9, 137.4), ring12(16.6, 137.4), ring12(16.6, 140.6),
                 ring12(16.9, 140.6), ring12(16.9, 141.3), ring12(16.0, 141.3)]
        out.append(loft(rings, ["stoneB", "trim", "top", "rune", "trim", "trim", "top"],
                        cap0=("stoneB", True), cap1=("top", True)))

        # 2. a banner on each drum face between the ribs, from under the rim cornice to the belt
        for f in FACES:
            n, t = axes(f)
            out += kit.banner(O, t, n, 0.0, 156.6, 7.4, 14.3, d=AP + 0.06)

        # 3. the rim: a bronze cornice (open over the catapult floor) and a stepped merlon with the
        #    triangle frieze over each banner
        rings = [ring12(16.1, 157.4), ring12(16.9, 158.0), ring12(16.9, 158.8), ring12(15.6, 158.8), ring12(15.6, 157.6)]
        out.append(loft(rings, ["trim", "trim", "top", "trim"], cap0=("trim", False), cap1=("trim", False)))
        for f in FACES:
            n, t = axes(f)
            out.append(prism_uz(O, t, n, [(-3.6, 158.8), (3.6, 158.8), (3.6, 162.4), (-3.6, 162.4)], 16.0, 17.3,
                                [None, "stoneB", "top", "stoneB"], "tri", "stoneB"))
            out.append(prism_uz(O, t, n, [(-2.6, 162.4), (2.6, 162.4), (2.6, 163.4), (-2.6, 163.4)], 16.2, 17.0,
                                [None, "trim", "trim", "trim"], "trim", "trim"))
            out.append(prism_uz(O, t, n, [(-2.6, 163.4), (2.6, 163.4), (0.0, 166.4)], 16.2, 17.0,
                                [None, "top", "top"], "stoneA", "stoneA"))

        # 4. a gilded stepped spire on each rib (a collar over the rib's ridge, a rune ring, a
        #    shaft, a ring, a needle): the fortress's highest point
        for r in RIBS:
            n, t = axes(r)
            out.append(prism_uz(O, t, n, [(-2.5, 160.2), (2.5, 160.2), (2.5, 163.6), (-2.5, 163.6)], 14.6, 18.3,
                                [None, "trim", "top", "trim"], "trim", "trim"))
            out.append(prism_uz(O, t, n, [(-2.0, 163.6), (2.0, 163.6), (2.0, 164.6), (-2.0, 164.6)], 15.0, 17.9,
                                [None, "rune", "top", "rune"], "rune", "rune"))

            def sq(h0, h1, z, n=n, t=t):        # square ring about radial 16.45: lateral ±h0, radial ±h1
                return [n * (16.45 + dr) + t * du + V((0, 0, z)) for du, dr in ((-h0, -h1), (h0, -h1), (h0, h1), (-h0, h1))]
            out.append(loft([sq(1.4, 1.2, 164.6), sq(1.4, 1.2, 171.0), sq(1.7, 1.5, 171.0), sq(1.7, 1.5, 172.0),
                             sq(1.2, 1.0, 172.0), [n * 16.45 + V((0, 0, 183.0))] * 4],
                            ["trim", "top", "trim", "top", "trim"], cap0=("trim", False), cap1=("trim", False)))

        # 5. the shaft's rune belt under the statue cornice
        def B(h, z, ch):
            return box_rings((-h, h), (-h, h), z, ch)
        rings = [B(15.0, 94.6, 3.0), B(15.7, 95.2, 3.2), B(15.7, 95.9, 3.2), B(15.45, 95.9, 3.1), B(15.45, 99.4, 3.1),
                 B(15.7, 99.4, 3.2), B(15.7, 100.1, 3.2), B(14.8, 100.1, 2.9)]
        out.append(loft(rings, ["stoneB", "trim", "top", ["rune" if k % 2 == 0 else "trim" for k in range(8)], "trim",
                                "trim", "top"], cap0=("stoneB", False), cap1=("top", True)))

        # 6. four long banners from the belt over the medallion panels (faces at 15.12)
        for ang in (0, 90, 180, 270):
            a = math.radians(ang)
            n, t = V((math.cos(a), math.sin(a), 0)), V((-math.sin(a), math.cos(a), 0))
            out += kit.banner(O, t, n, 0.0, 93.8, 8.4, 22.0, d=15.18)
        return out

    def emphasis(self, c, n):
        return 1.4 if c.z > 130 else (1.15 if c.z > 90 else 1.0)
