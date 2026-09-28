"""The Elven battle tower (ElvenBattleTower, elvenbattletower.ini): EA's slender tower keeps its
battered stone foot with the porch and ramp, its shaft of tall lattice windows between white corner
piers, and its head of four pointed gables with their horns. What made it read squat - the bulging
fish-scale cupola in the middle of the gables - is now the foot of a tall Elven spire: a concave
slate needle with swan-neck eaves rising from inside the ring of gables, a gold collar
between gilt beads a third of the way up, a gilt leaf finial on a gilt mast flying a long leaf
pennant in the player's colour. Round the foot, a moulded silver coping on the stone's top edge
and a knotwork band a little lower (both break for the porch), and a crystal lantern on a
swan-neck bracket either side of the two camera-facing faces.

All numbers are EBBBATTLETWR mesh coordinates (= model; one bone, upright). The mesh also holds five
tiny markers 55 units out on the axes (the footprint is theirs: x -57.8..46.2, y -55.7..58.7).
The tower itself: the foot is an octagon (axis faces battered 0.17, apothem 18.8 at the ground,
13.7 at its top edge z 32.9; short chamfers on the diagonals) round S (-0.645, 1.49); the shaft is
square, faces at 10.8 from S, with corner piers on the diagonals out to 17 from z 32.9 to 78; the
head (z 80.8..103.3) has its four gables on the axes round H (-0.06, 1.25), feet at radius 21-23,
horns out to 25.6 at z 109.2. The cupola rises from z 103.3 (radius 15.4 on the diagonals) through
10.6 at 110 and 1.5 at 120 to its tip at 131.55: the spire (radius 16.4 at its eaves, 15.2 at the
middle of a side) holds it everywhere. The archer bones (3..14) stand at z 88.5-93.3 in the gables'
windows: nothing is added below z 103 in the head.

The snow tower (ElvenBattleTowerSnow, an ObjectReskin) draws EBBbattleTwrS: EA's very body on the
snow sheet. It is not in the family the pipeline finds (EBBbattleTwr_*), so drawn_models adds it and
it is derived like the damaged state (our body, our _Snow sheet).
"""
import math

from sagekit.building import Building

from ..style import ElvenStyle

S = (-0.645, 1.49)          # foot and shaft centre
H = (-0.3, 1.4)             # the spire's axis (EA's cupola tip is at (-0.56, 1.56))
FOOT_Z = 32.9               # the stone foot's top edge
SPIRE = dict(r=16.4, z=103.3, h=42.0, phase=0.0)   # corners on the axes (the gables) and diagonals
SNOW = "EBBbattleTwrS"
# the tips of the four gables' horns (EA's vertices: the horn curls up and out to z 109.3)
HORNS = [(0.15, -25.45), (26.7, 1.4), (0.15, 27.9), (-26.7, 1.4)]
HORN_Z = 109.3


def foot_apothem(z):
    """The battered foot's axis faces: distance from S at height z (planes offsets 19.81 / 18.87 /
    17.4 with normals tilted 0.17 up, averaged)."""
    return 18.8 - 0.1735 * z


def foot_path(z, chamfer=0.42):
    """The foot's outline at z: axis faces at foot_apothem(z) with diagonal chamfers (a fraction of
    the half side), from the +x face's -y corner round -y, -x, +y to its +y corner: the porch fills
    the +x face between them."""
    A = foot_apothem(z)
    c = A * chamfer
    pts = [(A, -(A - c)), (A - c, -A), (-(A - c), -A), (-A, -(A - c)), (-A, A - c), (-(A - c), A), (A - c, A), (A, A - c)]
    return [(S[0] + x, S[1] + y) for x, y in pts]


def spire_ribs(cx, cy, z, r, h, pw, upturn, phase=0.0, k=8, steps=6, size=0.3):
    """Silver ribs up a swept_roof needle's k corners (its eave ring at z, radius r, height h, sweep
    power pw, corners turned up by `upturn` fading over the first third), riding on the faces: a
    square section lofted from the eave to near the tip (as the citadel's flèche, fortress/spire.py)."""
    from mathutils import Vector as V
    from sagekit.blender.geometry import loft
    out = []
    for i in range(k):
        ang = phase + 2 * math.pi * i / k
        c, s_ = math.cos(ang), math.sin(ang)
        rings = []
        for j in range(steps + 1):
            s = j / steps * 0.94
            rr = r * (1 - s) ** pw + 0.12
            zz = z + h * s + upturn * max(0.0, 1 - 3 * s)
            p = V((cx + rr * c, cy + rr * s_, zz))
            rad, tan = V((c, s_, 0)), V((-s_, c, 0))
            rings.append([p - tan * size, p - tan * size + rad * size * 1.4, p + tan * size + rad * size * 1.4,
                          p + tan * size])
        out.append(loft(rings, ["trim"] * steps, cap0=("trim", False), cap1=("trim", True)))
    return out


class BattleTower(Building):
    style = ElvenStyle()
    source = "EBBbattleTwr"
    target = "EBBBATTLETWR"
    sheet = "EBBbattleTwr.tga"
    sheet_normal = "EBBbattleTwr_NRM.tga"
    own_textures = {"EBBbattleTwr.tga": "EBBbattleTwH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((0.0, 1.5, 72.0), 330, 50, -38, 50),
        "close": ((0.0, 1.5, 120.0), 120, 24, -30, 45),
        "ingame": ((0.0, 1.5, 72.0), 900, 53, -62, 50),
        "foot": ((6.0, 1.5, 22.0), 110, 22, -30, 45),
    }

    def drawn_models(self, install):
        """EA's models plus the snow tower's (see the module notes)."""
        out = super().drawn_models(install)
        if install.has_model(SNOW) and SNOW.lower() not in {m.lower() for m in out}:
            out.append(SNOW)
        return out

    def design(self, kit):
        s = []
        s += self._spire(kit)                   # 1. the spire over EA's cupola, collar, mast, pennant
        s += self._foot(kit)                    # 2. coping and knotwork band round the stone foot
        s += self._lanterns(kit)                # 3. crystal lanterns on the camera-facing faces
        for x, y in HORNS:                      # 4. gilt leaf finials on the gables' horns
            s += kit.leaf_finial(x, y, HORN_Z - 0.3, 4.2, 1.3)
        return s

    # ------------------------------------------------------------------ 1. spire
    @staticmethod
    def _spire(kit):
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        from ..shapes import ring, turned
        cx, cy = H
        r, z, h = SPIRE["r"], SPIRE["z"], SPIRE["h"]
        out = kit.swept_roof(cx, cy, r, z, h, k=8, per_side=3, upturn=1.3, lip=0.4, sweep_pow=1.7, finial=False,
                             phase=SPIRE["phase"])
        top = z + 0.4 + h

        def spire_r(zz):                        # the needle's corner radius at height zz
            return r * max(0.0, 1 - (zz - z - 0.4) / h) ** 1.7

        # a gold collar a third of the way up: a moulded gilt band between beads, over silver ribs
        z0 = z + 0.4 + 0.3 * h
        rr = spire_r(z0)

        def R(e, zz):
            return ring(cx, cy, e, zz, 8, phase=SPIRE["phase"])
        rings = [R(rr - 0.8, z0 - 0.3), R(rr + 0.55, z0 - 0.3), R(rr + 0.75, z0 + 0.05), R(rr + 0.45, z0 + 0.4),
                 R(spire_r(z0 + 2.0) + 0.45, z0 + 2.0), R(spire_r(z0 + 2.0) + 0.75, z0 + 2.35),
                 R(spire_r(z0 + 2.7) + 0.5, z0 + 2.7), R(spire_r(z0 + 2.7) - 0.8, z0 + 2.7)]
        out.append(loft(rings, [None, "gilt", "gilt", "gilt", "gilt", "gilt", "gilt"], cap0=("gilt", False),
                        cap1=("gilt", False)))
        out += spire_ribs(cx, cy, z + 0.4, r, h, 1.7, 1.3, phase=SPIRE["phase"])
        # the mast: a gilt collar on the needle's tip, a slender gilt pole, a leaf finial
        mast = top + 6.2
        out.append(turned(cx, cy, [(0.9, top - 2.2), (0.55, top - 0.6), (0.3, top + 0.4)], ["gilt", "gilt"], k=8,
                          cap0=("gilt", False), cap1=("gilt", True)))
        out.append(turned(cx, cy, [(0.26, top), (0.18, mast)], ["gilt"], k=8, cap0=("gilt", False), cap1=("gilt", True)))
        out += kit.leaf_finial(cx, cy, mast - 0.1, 3.6, 1.2)
        # the pennant flies across the RTS camera's view (camera from azimuth -38)
        t = V((math.sin(math.radians(38)), math.cos(math.radians(38)), 0))
        n = V((t.y, -t.x, 0))
        out += kit.pennant(V((cx, cy, 0)), t, n, 0.15, mast - 0.6, 15.0, 3.0)
        return out

    # ------------------------------------------------------------------ 2. foot
    @staticmethod
    def _foot(kit):
        """A moulded silver coping on the foot's top edge (its top 0.25 over the ledge, overhanging
        0.9) and a knotwork band between gilt beads at z 27.4..28.8, both open over the porch."""
        out = []
        out += kit.coping_run(foot_path(FOOT_Z - 0.8), FOOT_Z + 0.25, d_out=0.9, d_in=-2.4, center=S)
        out += kit.filigree_band(foot_path(28.1), 27.4, 28.8, d=0.3, center=S)
        return out

    # ------------------------------------------------------------------ 3. lanterns
    @staticmethod
    def _lanterns(kit):
        """A crystal lantern on a gilt swan-neck bracket at each end of the -y and -x faces of the
        foot, just under the band (the brackets start inside the battered face)."""
        from mathutils import Vector as V
        out = []
        z = 21.0
        A = foot_apothem(z) - 0.4
        for n in (V((0, -1, 0)), V((-1, 0, 0))):
            t = V((-n.y, n.x, 0))
            a = V((S[0] + n.x * A, S[1] + n.y * A, 0))
            for u in (-7.2, 7.2):
                out += kit.hung_lantern(a, t, n, u, z, reach=2.6, h=3.0)
        return out

    # ------------------------------------------------------------------ night
    @staticmethod
    def night_lights(kit):
        """EA's four lattice windows of the shaft (between the corner piers) and the porch door."""
        from sagekit.nightlights import Light
        out = []
        for n in ((1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0)):
            if n == (1, 0, 0):
                continue                        # the +x shaft face: see the porch below
            a = (S[0] + n[0] * 10.8, S[1] + n[1] * 10.8, 0.0)
            t = (-n[1], n[0], 0.0)
            out.append(Light.rect(a, t, n, -8.0, 8.0, 36.0, 74.0, reach=3.0, name="shaft %s" % (n,)))
        out.append(Light.rect((S[0] + 10.8, S[1], 0.0), (0, 1, 0), (1, 0, 0), -8.0, 8.0, 48.0, 74.0, reach=3.0,
                              name="shaft +x"))
        out.append(Light.arch((12.0, S[1], 0.0), (0, 1, 0), (1, 0, 0), 0.0, 2.6, 7.6, 13.5, 17.0, kind="door", reach=9.0,
                              name="porch door"))
        return out

    def emphasis(self, c, n):
        if c.z > 103.0:
            return 1.4                          # the spire, the RTS camera's favourite
        return 1.2 if c.z < 36.0 else 1.0
